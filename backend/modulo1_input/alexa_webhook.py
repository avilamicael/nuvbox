from flask import Flask, request, jsonify
from queue import Queue
from datetime import datetime
from modulo3_armazenamento.storage_worker import TextItem
from modulo1_input.text_webhook import register_text_webhook
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)


def create_alexa_app(text_queue: Queue) -> Flask:
    """
    Create Flask app for Alexa webhook.

    Args:
        text_queue: Queue to push TextItem objects for storage

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint."""
        return jsonify({"status": "ok", "service": "cerebro-alexa-webhook"}), 200

    @app.route("/webhook/alexa", methods=["POST"])
    def alexa_webhook():
        """
        Receive transcribed text from Alexa Cloud.

        Request body (JSON):
        {
            "text": "o que é um qubit",
            "session_id": "amzn1.ask.account.XXXXX",
            "timestamp": "2026-03-17T15:30:45Z"
        }

        Security:
        - Validates X-Alexa-Secret header against ALEXA_WEBHOOK_SECRET
        """
        # Validate secret header
        secret = request.headers.get("X-Alexa-Secret", "")
        if secret != settings.flask.webhook_secret:
            logger.warning(
                f"❌ Unauthorized webhook attempt (bad secret from {request.remote_addr})"
            )
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            text = data.get("text", "").strip()
            session_id = data.get("session_id", "")
            timestamp_str = data.get("timestamp", "")

            if not text:
                logger.warning("❌ Empty text in Alexa webhook")
                return jsonify({"error": "empty text"}), 400

            # Parse timestamp
            try:
                transcribed_at = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                transcribed_at = datetime.now()

            # Create TextItem and queue for storage
            text_item = TextItem(
                text=text,
                source="alexa",
                transcribed_at=transcribed_at,
                audio_duration_ms=None,  # Alexa doesn't provide duration
                whisper_model=None,  # Alexa uses its own transcription
                language=settings.whisper.language,
                alexa_session_id=session_id,
                metadata={"webhook_ip": request.remote_addr},
            )

            try:
                text_queue.put_nowait(text_item)
                logger.info(f"✅ Queued Alexa text (session={session_id}, len={len(text)})")
                return jsonify({"status": "ok", "session_id": session_id}), 200
            except:  # Queue.Full
                logger.error("❌ Text queue full, rejecting Alexa webhook")
                return jsonify({"error": "queue_full"}), 503

        except Exception as e:
            logger.error(f"❌ Alexa webhook error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500

    # Register generic text webhook for all other sources (Windows, ESP32, etc.)
    register_text_webhook(app, text_queue)

    return app
