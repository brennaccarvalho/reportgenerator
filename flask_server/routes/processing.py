"""
Rota /processing/<dataset_id> — exibe o perfil do dataset.

Mostra ao usuário:
  - Dimensões (linhas × colunas)
  - Tipo inferido de cada coluna (numérico, categórico, data, texto)
  - % de valores nulos por coluna
  - Transformações aplicadas na limpeza automática
  - Problemas detectados (colunas com muitos nulos, variância zero)
"""
from flask import (
    Blueprint, render_template, redirect,
    url_for, flash, session,
)
import pandas as pd

from app.services.data_profiler import profile_dataframe
from flask_server.models import Dataset

processing_bp = Blueprint("processing", __name__)


@processing_bp.route("/processing/<dataset_id>", methods=["GET"])
def processing_page(dataset_id):
    """Exibe o perfil detalhado do dataset importado."""
    dataset = Dataset.query.get_or_404(dataset_id)

    # Carrega o CSV limpo do disco
    try:
        df = pd.read_csv(dataset.storage_path)
    except Exception as e:
        flash(f"Erro ao carregar dataset: {e}", "error")
        return redirect(url_for("main.upload_page"))

    # Gera perfil completo
    profile = profile_dataframe(df)

    # Mantém dataset_id na sessão
    session["dataset_id"] = dataset_id

    dataset_info = {
        "id": dataset.id,
        "name": dataset.name,
        "n_rows": dataset.n_rows,
        "n_cols": dataset.n_cols,
        "framework": session.get("framework_id"),
    }

    return render_template(
        "processing.html",
        current_step="processing",
        current_step_num=2,
        dataset_info=dataset_info,
        dataset=dataset,
        profile=profile,
    )
