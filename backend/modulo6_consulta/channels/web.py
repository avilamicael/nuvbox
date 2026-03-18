"""
Canal HTTP para Módulo 6 — Interface de Consulta.

Expõe o endpoint POST /consulta para busca por linguagem natural.
Segue o mesmo padrão de autenticação do M1 (X-Cerebro-Secret / X-Jarvis-Secret).
"""

from flask import Flask, request, jsonify
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)


def register_consulta_routes(app: Flask) -> None:
    """
    Registra o endpoint /consulta em um Flask app existente.

    Args:
        app: Flask application instance

    Endpoint:
        POST /consulta
        Headers: X-Cerebro-Secret ou X-Jarvis-Secret
        Body: {"pergunta": "o que eu falei sobre o Cerebro esta semana?"}
        Response: {"resposta": "...", "fragmentos": [...], "ferramentas_usadas": [...]}
    """

    @app.route("/consulta", methods=["POST"])
    def consultar():
        # Importação local para evitar inicializar tools antes do pool de DB estar pronto
        from modulo6_consulta.query_agent import run, QueryRequest

        # Validar secret header (mesmo padrão do M1)
        secret = (
            request.headers.get("X-Jarvis-Secret")
            or request.headers.get("X-Cerebro-Secret")
            or ""
        )
        if secret != settings.flask.webhook_secret:
            logger.warning(
                f"❌ Unauthorized /consulta attempt from {request.remote_addr}"
            )
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            pergunta = data.get("pergunta", "").strip()
            if not pergunta:
                return jsonify({"error": "campo 'pergunta' obrigatório"}), 400

            # usuario_id fixo = 1 (MVP single-user)
            query_request = QueryRequest(
                pergunta=pergunta,
                usuario_id=1,
            )

            logger.info(f"🔍 /consulta: '{pergunta[:80]}{'...' if len(pergunta) > 80 else ''}'")
            response = run(query_request)

            return jsonify({
                "resposta": response.resposta,
                "fragmentos": response.fragmentos,
                "ferramentas_usadas": response.ferramentas_usadas,
            }), 200

        except Exception as e:
            logger.error(f"❌ /consulta error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500
