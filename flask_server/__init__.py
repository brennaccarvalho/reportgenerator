"""
App factory do servidor Flask.

Usa o padrão Application Factory para facilitar testes
e múltiplas instâncias com configurações diferentes.
"""
import os
from flask import Flask
from .config import DevelopmentConfig, ProductionConfig
from .models import db


def create_app(config_class=None):
    """
    Cria e configura a aplicação Flask.

    Fluxo:
      1. Cria a instância Flask
      2. Aplica configuração (dev ou prod)
      3. Inicializa o SQLAlchemy (PostgreSQL)
      4. Cria as tabelas no banco se não existirem
      5. Registra os Blueprints (grupos de rotas)
    """
    app = Flask(
        __name__,
        template_folder="templates",
    )

    # ── Configuração ──────────────────────────────────────────────
    if config_class is None:
        env = os.environ.get("FLASK_ENV", "development")
        config_class = ProductionConfig if env == "production" else DevelopmentConfig
    app.config.from_object(config_class)

    # ── Extensões ─────────────────────────────────────────────────
    db.init_app(app)  # conecta SQLAlchemy ao app Flask

    # ── Inicialização do banco e pastas ───────────────────────────
    with app.app_context():
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        os.makedirs(app.config["PUBLISHED_REPORTS_DIR"], exist_ok=True)
        db.create_all()  # cria tabelas 'datasets' e 'reports' se não existirem

    # ── Blueprints (grupos de rotas) ──────────────────────────────
    from .routes.main import main_bp
    from .routes.processing import processing_bp
    from .routes.framework import framework_bp
    from .routes.builder import builder_bp
    from .routes.preview import preview_bp
    from .routes.reports import reports_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(processing_bp)
    app.register_blueprint(framework_bp)
    app.register_blueprint(builder_bp)
    app.register_blueprint(preview_bp)
    app.register_blueprint(reports_bp)

    try:
        from .routes.meridian_routes import meridian_bp
        app.register_blueprint(meridian_bp, url_prefix='/meridian')
    except ImportError:
        pass  # Meridian routes não disponíveis

    return app
