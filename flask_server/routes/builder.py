"""
Rota /builder/<dataset_id> — configuração do relatório.

O usuário escolhe quais colunas incluir na análise.
Por padrão o framework usa todas as colunas; a seleção
aqui filtra o DataFrame antes de rodar o framework.
"""
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session,
)
import pandas as pd

from flask_server.models import Dataset

builder_bp = Blueprint("builder", __name__)


@builder_bp.route("/builder/<dataset_id>", methods=["GET"])
def builder_page(dataset_id):
    """Exibe os controles de seleção de colunas e nome do relatório."""
    dataset = Dataset.query.get_or_404(dataset_id)
    framework_id = session.get("framework_id")

    if not framework_id:
        flash("Selecione um framework antes de continuar.", "warning")
        return redirect(
            url_for("framework.framework_page", dataset_id=dataset_id)
        )

    try:
        df = pd.read_csv(dataset.storage_path)
    except Exception as e:
        flash(f"Erro ao carregar dataset: {e}", "error")
        return redirect(url_for("main.upload_page"))

    # Classifica colunas por tipo semântico
    num_cols = df.select_dtypes(include="number").columns.tolist()
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    cat_cols = df.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    # Tenta detectar datas em colunas string pelo conteúdo amostral
    detected_date_cols = []
    for col in list(cat_cols):
        sample = df[col].dropna().head(5).astype(str).tolist()
        if any(
            ("/" in v or "-" in v) and len(v) >= 8
            for v in sample
        ):
            detected_date_cols.append(col)
            cat_cols.remove(col)
    date_cols = date_cols + detected_date_cols

    dataset_info = {
        "id": dataset.id,
        "name": dataset.name,
        "n_rows": dataset.n_rows,
        "n_cols": dataset.n_cols,
        "framework": framework_id,
    }

    return render_template(
        "builder.html",
        current_step="builder",
        current_step_num=4,
        dataset_info=dataset_info,
        dataset=dataset,
        framework_id=framework_id,
        num_cols=num_cols,
        cat_cols=cat_cols,
        date_cols=date_cols,
    )


@builder_bp.route("/builder/<dataset_id>", methods=["POST"])
def build_report(dataset_id):
    """Salva a configuração na sessão e redireciona para o preview."""
    Dataset.query.get_or_404(dataset_id)
    framework_id = session.get("framework_id")

    if not framework_id:
        flash("Sessão expirada. Selecione o framework novamente.", "warning")
        return redirect(
            url_for("framework.framework_page", dataset_id=dataset_id)
        )

    report_name = (
        request.form.get("report_name", "").strip()
        or f"Relatório — {Dataset.query.get(dataset_id).name}"
    )

    # Salva colunas selecionadas na sessão (lista pode estar vazia = todas)
    selected_cols = request.form.getlist("selected_cols")

    session["dataset_id"] = dataset_id
    session["framework_id"] = framework_id
    session["report_name"] = report_name
    session["selected_cols"] = selected_cols

    return redirect(url_for("preview.preview_page"))
