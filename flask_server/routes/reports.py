"""
Rotas de relatórios publicados.

GET  /reports              → lista todos os relatórios
GET  /reports/<id>         → exibe um relatório
GET  /reports/<id>/raw     → serve o HTML puro (usado em iframe)
GET  /reports/<id>/download → download do HTML
DELETE /api/reports/<id>   → remove relatório (chamado via JS fetch)
"""
import os
from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, jsonify, send_file, abort, Response,
)

from flask_server.models import db, Report

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
def reports_list():
    """Lista todos os relatórios ordenados do mais recente para o mais antigo."""
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template(
        "reports.html",
        current_step="reports",
        current_step_num=6,
        dataset_info=None,
        reports=reports,
    )


@reports_bp.route("/reports/<report_id>")
def report_detail(report_id):
    """Página de detalhe do relatório com iframe embutido."""
    report = Report.query.get_or_404(report_id)
    return render_template(
        "report_view.html",
        current_step="reports",
        current_step_num=6,
        dataset_info=None,
        report=report,
        has_file=bool(report.path and os.path.exists(report.path)),
    )


@reports_bp.route("/reports/<report_id>/raw")
def report_raw(report_id):
    """Serve o HTML bruto do relatório (carregado no iframe)."""
    report = Report.query.get_or_404(report_id)
    if not report.path or not os.path.exists(report.path):
        abort(404)
    with open(report.path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content, mimetype="text/html")


@reports_bp.route("/reports/<report_id>/download")
def download_report(report_id):
    """Download do arquivo HTML do relatório."""
    report = Report.query.get_or_404(report_id)
    if not report.path or not os.path.exists(report.path):
        abort(404)
    return send_file(
        report.path,
        as_attachment=True,
        download_name=f"{report.name}.html",
        mimetype="text/html",
    )


@reports_bp.route("/api/reports/<report_id>", methods=["DELETE"])
def delete_report(report_id):
    """Remove relatório do banco e do disco. Chamado via fetch() no frontend."""
    report = Report.query.get_or_404(report_id)

    # Remove arquivo em disco se existir
    if report.path and os.path.exists(report.path):
        os.remove(report.path)

    db.session.delete(report)
    db.session.commit()
    return jsonify({"ok": True, "message": "Relatório removido."})
