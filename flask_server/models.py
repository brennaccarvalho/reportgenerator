"""
Modelos SQLAlchemy — tabelas no PostgreSQL.

Tabelas criadas:
    datasets  → cada arquivo importado pelo usuário
    reports   → cada relatório publicado (referencia um dataset)
"""
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _new_uuid() -> str:
    """Gera um UUID v4 como string."""
    return str(uuid.uuid4())


class Dataset(db.Model):
    """
    Representa um dataset importado.

    Armazena metadados do arquivo (nome, origem, dimensões)
    e o caminho do CSV limpo salvo em disco.
    """
    __tablename__ = "datasets"

    id = db.Column(db.String(36), primary_key=True, default=_new_uuid)
    name = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(50), nullable=False)      # 'csv' | 'xlsx'
    source_name = db.Column(db.String(255))                # nome original do arquivo
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    n_rows = db.Column(db.Integer)
    n_cols = db.Column(db.Integer)
    columns_meta = db.Column(db.JSON)                      # perfil de cada coluna
    storage_path = db.Column(db.String(500))               # CSV limpo em disco

    # Relacionamento: um dataset pode ter vários relatórios
    reports = db.relationship("Report", backref="dataset", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "source": self.source,
            "source_name": self.source_name,
            "uploaded_at": self.uploaded_at.isoformat(),
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
        }


class Report(db.Model):
    """
    Representa um relatório publicado.

    Referencia o dataset de origem e armazena o caminho
    do arquivo HTML gerado em disco.
    """
    __tablename__ = "reports"

    id = db.Column(db.String(36), primary_key=True, default=_new_uuid)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    framework = db.Column(db.String(50), nullable=False)
    dataset_id = db.Column(db.String(36), db.ForeignKey("datasets.id"), nullable=True)
    source = db.Column(db.String(50))
    source_name = db.Column(db.String(255))
    path = db.Column(db.String(500))    # HTML do relatório em disco
    n_rows = db.Column(db.Integer)
    n_cols = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "framework": self.framework,
            "dataset_id": self.dataset_id,
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
        }
