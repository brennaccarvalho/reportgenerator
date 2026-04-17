"""
Ponto de entrada do servidor Flask.

Executa com:
    python run_flask.py

Ou via Docker Compose:
    docker compose up flask
"""
import sys
import os

# Garante que a raiz do projeto está no PYTHONPATH
# para que 'from app.services...' funcione corretamente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask_server import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",   # aceita conexões externas (necessário no Docker)
        port=5000,
        debug=True,
    )
