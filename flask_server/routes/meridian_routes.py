# Stdlib
import os
import uuid
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Third-party
import pandas as pd
from flask import Blueprint, current_app, jsonify, render_template, request, send_file, session

# Local
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from app.analysis_frameworks.meridian_framework import MeridianFramework, MERIDIAN_AVAILABLE
except ImportError:
    MERIDIAN_AVAILABLE = False
    MeridianFramework = None

logger = logging.getLogger(__name__)

meridian_bp = Blueprint("meridian", __name__)

# Jobs de treino em memória (suficiente para dev; produção usaria Redis)
_training_jobs: Dict[str, Dict[str, Any]] = {}
# Resultados armazenados por job_id
_job_results: Dict[str, Any] = {}
# Modelos treinados por job_id (em memória, não serializáveis facilmente)
_trained_models: Dict[str, Any] = {}


def _load_dataframe_from_session() -> Optional[pd.DataFrame]:
    """Carrega o DataFrame da sessão (via CSV em disco, como outros blueprints)."""
    dataset_id = session.get("dataset_id")
    if not dataset_id:
        return None
    csv_path = PROJECT_ROOT / "data" / "uploads" / f"{dataset_id}.csv"
    if not csv_path.exists():
        return None
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Erro ao carregar DataFrame: {e}")
        return None


def _check_meridian_available():
    """Retorna erro JSON se Meridian não está disponível."""
    if not MERIDIAN_AVAILABLE:
        return jsonify({
            "error": "Meridian não está instalado. Execute: pip install google-meridian[schema] tensorflow tensorflow-probability"
        }), 503
    return None


@meridian_bp.route("/", methods=["GET"])
def meridian_index():
    """Página principal do Media Mix Modeling."""
    return render_template("meridian/index.html",
                           meridian_available=MERIDIAN_AVAILABLE)


@meridian_bp.route("/detect-columns", methods=["POST"])
def detect_columns():
    """Detecta colunas do DataFrame para mapeamento MMM."""
    err = _check_meridian_available()
    if err:
        return err

    df = _load_dataframe_from_session()
    if df is None:
        return jsonify({"error": "Nenhum dataset carregado na sessão."}), 400

    try:
        fw = MeridianFramework()
        detected = fw.detect_columns(df)
        return jsonify({
            "success": True,
            "detected": detected,
            "columns": list(df.columns),
            "numeric_columns": list(df.select_dtypes(include="number").columns),
        })
    except Exception as e:
        logger.exception("Erro ao detectar colunas")
        return jsonify({"error": f"Erro ao detectar colunas: {str(e)}"}), 500


@meridian_bp.route("/validate", methods=["POST"])
def validate_mapping():
    """Valida o mapeamento de colunas para MMM."""
    err = _check_meridian_available()
    if err:
        return err

    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON inválido."}), 400

    df = _load_dataframe_from_session()
    if df is None:
        return jsonify({"error": "Nenhum dataset carregado na sessão."}), 400

    column_mapping = data.get("column_mapping", {})

    try:
        fw = MeridianFramework()
        result = fw.validate_data(df, column_mapping)
        return jsonify({
            "valid": result["valid"],
            "errors": result["errors"],
            "warnings": result["warnings"],
        })
    except Exception as e:
        logger.exception("Erro ao validar mapeamento")
        return jsonify({"error": f"Erro na validação: {str(e)}"}), 500


def _run_training(job_id: str, df: pd.DataFrame, column_mapping: Dict,
                  model_config: Dict, train_params: Dict):
    """Executa treino em thread separada e atualiza _training_jobs."""
    job = _training_jobs[job_id]
    try:
        job["status"] = "running"
        job["progress"] = 10
        job["message"] = "Construindo dados de entrada..."

        fw = MeridianFramework()
        input_data = fw.build_input_data(df, column_mapping)

        job["progress"] = 30
        job["message"] = "Configurando modelo..."

        mmm = fw.configure_model(input_data, model_config)

        job["progress"] = 40
        job["message"] = "Treinando modelo (MCMC — pode demorar vários minutos)..."

        mmm, metadata = fw.train(
            mmm,
            n_chains=train_params.get("n_chains", 4),
            n_adapt=train_params.get("n_adapt", 1000),
            n_burnin=train_params.get("n_burnin", 500),
            n_keep=train_params.get("n_keep", 500),
        )

        job["progress"] = 80
        job["message"] = "Executando diagnóstico de convergência..."

        health = fw.run_health_check(mmm)

        job["progress"] = 90
        job["message"] = "Gerando resultados..."

        results = fw.generate_results(mmm)

        _trained_models[job_id] = {"mmm": mmm, "fw": fw}
        _job_results[job_id] = {
            "results": results,
            "health": health,
            "metadata": metadata,
            "column_mapping": column_mapping,
        }

        job["status"] = "done"
        job["progress"] = 100
        job["message"] = f"Treino concluído em {metadata.get('tempo_segundos', 0):.0f}s"

    except Exception as e:
        logger.exception(f"Erro no treino do job {job_id}")
        job["status"] = "error"
        job["message"] = f"Erro durante o treino: {str(e)}"
        job["progress"] = 0


@meridian_bp.route("/train", methods=["POST"])
def start_training():
    """Inicia o treino assíncrono do modelo MMM."""
    err = _check_meridian_available()
    if err:
        return err

    df = _load_dataframe_from_session()
    if df is None:
        return jsonify({"error": "Nenhum dataset carregado na sessão."}), 400

    data = request.get_json() or {}
    column_mapping = data.get("column_mapping", {})
    model_config = {
        "roi_mu": data.get("roi_mu", float(os.getenv("MERIDIAN_ROI_MU", "0.2"))),
        "roi_sigma": data.get("roi_sigma", float(os.getenv("MERIDIAN_ROI_SIGMA", "0.9"))),
    }
    train_params = {
        "n_chains": data.get("n_chains", int(os.getenv("MERIDIAN_N_CHAINS", "4"))),
        "n_adapt": data.get("n_adapt", int(os.getenv("MERIDIAN_N_ADAPT", "1000"))),
        "n_burnin": data.get("n_burnin", int(os.getenv("MERIDIAN_N_BURNIN", "500"))),
        "n_keep": data.get("n_keep", int(os.getenv("MERIDIAN_N_KEEP", "500"))),
    }

    job_id = str(uuid.uuid4())
    _training_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": "Iniciando treino...",
        "created_at": datetime.now().isoformat(),
    }

    # Copia o DataFrame para a thread (evita race condition)
    df_copy = df.copy()
    thread = threading.Thread(
        target=_run_training,
        args=(job_id, df_copy, column_mapping, model_config, train_params),
        daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id, "status": "running"}), 202


@meridian_bp.route("/status/<job_id>", methods=["GET"])
def training_status(job_id: str):
    """Retorna o status atual de um job de treino."""
    if job_id not in _training_jobs:
        return jsonify({"error": "Job não encontrado."}), 404

    job = _training_jobs[job_id]
    return jsonify({
        "status": job["status"],
        "progress": job["progress"],
        "message": job["message"],
        "created_at": job.get("created_at"),
    })


@meridian_bp.route("/results/<job_id>", methods=["GET"])
def get_results(job_id: str):
    """Retorna os resultados completos de um job de treino concluído."""
    if job_id not in _training_jobs:
        return jsonify({"error": "Job não encontrado."}), 404

    if _training_jobs[job_id]["status"] != "done":
        return jsonify({
            "error": "Treino ainda não concluído.",
            "status": _training_jobs[job_id]["status"],
        }), 400

    if job_id not in _job_results:
        return jsonify({"error": "Resultados não disponíveis."}), 404

    results_data = _job_results[job_id]

    return jsonify({
        "success": True,
        "results": results_data["results"],
        "health": results_data["health"],
        "metadata": results_data["metadata"],
    })


@meridian_bp.route("/optimize", methods=["POST"])
def optimize_budget():
    """Executa otimização de budget."""
    err = _check_meridian_available()
    if err:
        return err

    data = request.get_json() or {}
    job_id = data.get("job_id")
    total_budget = data.get("total_budget", 0)
    constraints = data.get("constraints", {})

    if not job_id or job_id not in _trained_models:
        return jsonify({"error": "Modelo não encontrado. Treine o modelo primeiro."}), 400

    try:
        mmm = _trained_models[job_id]["mmm"]
        fw = _trained_models[job_id]["fw"]
        opt_results = fw.run_optimization(mmm, total_budget, constraints)
        return jsonify({"success": True, "optimization": opt_results})
    except Exception as e:
        logger.exception("Erro na otimização")
        return jsonify({"error": f"Erro na otimização: {str(e)}"}), 500


@meridian_bp.route("/report/<job_id>", methods=["GET"])
def generate_report(job_id: str):
    """Gera e retorna o relatório HTML do MMM."""
    err = _check_meridian_available()
    if err:
        return err

    if job_id not in _job_results:
        return jsonify({"error": "Resultados não encontrados. Treine o modelo primeiro."}), 404

    results_data = _job_results[job_id]

    try:
        fw = _trained_models.get(job_id, {}).get("fw") or MeridianFramework()
        results = results_data["results"]
        metadata = results_data["metadata"]

        charts = fw.generate_charts(results)
        html_content = fw.generate_html_report(results, charts, None, metadata)

        published_dir = Path(current_app.config["PUBLISHED_REPORTS_DIR"])
        published_dir.mkdir(parents=True, exist_ok=True)
        report_path = published_dir / f"mmm_{job_id}.html"
        report_path.write_text(html_content, encoding="utf-8")

        download = request.args.get("download", "false").lower() == "true"
        if download:
            return send_file(
                str(report_path),
                as_attachment=True,
                download_name=f"mmm_report_{job_id[:8]}.html",
                mimetype="text/html"
            )
        else:
            return html_content, 200, {"Content-Type": "text/html; charset=utf-8"}

    except Exception as e:
        logger.exception("Erro ao gerar relatório")
        return jsonify({"error": f"Erro ao gerar relatório: {str(e)}"}), 500
