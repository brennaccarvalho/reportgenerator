"""
Rotas principais: dashboard (/) e upload de arquivo (/upload).

Fluxo do upload:
  1. Usuário envia arquivo CSV ou XLSX via POST
  2. load_file() carrega o DataFrame
  3. clean_dataframe() limpa e normaliza os dados
  4. profile_dataframe() gera perfil das colunas
  5. Dataset é salvo no PostgreSQL + CSV limpo no disco
  6. Redireciona para /processing/<id>
"""
import os
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session, current_app,
)

from app.services.file_loader import load_file
from app.services.data_cleaner import clean_dataframe
from app.services.data_profiler import profile_dataframe
from flask_server.models import db, Dataset, Report

main_bp = Blueprint("main", __name__)


def _get_dataset_info():
    """Lê info do dataset ativo da sessão Flask."""
    dataset_id = session.get("dataset_id")
    if not dataset_id:
        return None
    dataset = Dataset.query.get(dataset_id)
    if not dataset:
        return None
    return {
        "id": dataset.id,
        "name": dataset.name,
        "n_rows": dataset.n_rows,
        "n_cols": dataset.n_cols,
        "framework": session.get("framework_id"),
    }


# ── Dashboard ─────────────────────────────────────────────────────

@main_bp.route("/")
def index():
    """Página inicial com estatísticas e relatórios recentes."""
    total_reports = Report.query.count()
    total_datasets = Dataset.query.count()
    recent_reports = (
        Report.query.order_by(Report.created_at.desc()).limit(5).all()
    )
    return render_template(
        "index.html",
        current_step="home",
        current_step_num=0,
        dataset_info=_get_dataset_info(),
        total_reports=total_reports,
        total_datasets=total_datasets,
        recent_reports=recent_reports,
    )


# ── Upload ────────────────────────────────────────────────────────

@main_bp.route("/upload", methods=["GET"])
def upload_page():
    """Exibe o formulário de upload."""
    return render_template(
        "upload.html",
        current_step="upload",
        current_step_num=1,
        dataset_info=_get_dataset_info(),
    )


@main_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Processa o arquivo enviado:
      - Valida e carrega com load_file()
      - Limpa com clean_dataframe()
      - Perfila com profile_dataframe()
      - Salva Dataset no PostgreSQL
      - Salva CSV limpo em data/uploads/<id>.csv
    """
    if "file" not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for("main.upload_page"))

    file = request.files["file"]
    if not file.filename:
        flash("Nome de arquivo inválido.", "error")
        return redirect(url_for("main.upload_page"))

    # 1. Carrega o arquivo
    try:
        file_bytes = file.read()
        df_raw, _ = load_file(file_bytes, file.filename)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("main.upload_page"))

    # 2. Limpa os dados automaticamente
    df_clean, transformations_log = clean_dataframe(df_raw)

    # 3. Gera perfil das colunas para armazenar no DB
    profile = profile_dataframe(df_clean, transformations_log)

    # 4. Cria registro no PostgreSQL
    ext = "xlsx" if file.filename.lower().endswith((".xlsx", ".xls")) else "csv"
    dataset = Dataset(
        name=file.filename,
        source=ext,
        source_name=file.filename,
        n_rows=len(df_clean),
        n_cols=len(df_clean.columns),
        columns_meta=profile["columns"],
    )
    db.session.add(dataset)
    db.session.flush()  # gera o ID sem commitar ainda

    # 5. Salva CSV limpo no disco
    storage_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], f"{dataset.id}.csv"
    )
    df_clean.to_csv(storage_path, index=False)
    dataset.storage_path = storage_path
    db.session.commit()

    # 6. Armazena na sessão e redireciona
    session["dataset_id"] = dataset.id
    session["framework_id"] = None
    session.pop("report_name", None)

    flash(
        f"'{file.filename}' carregado com sucesso: "
        f"{len(df_clean)} linhas, {len(df_clean.columns)} colunas.",
        "success",
    )
    return redirect(
        url_for("processing.processing_page", dataset_id=dataset.id)
    )
