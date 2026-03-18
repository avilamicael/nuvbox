from flask import Flask, request, jsonify
from queue import Queue
from datetime import datetime
from modulo3_armazenamento.storage_worker import TextItem
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

# Fontes conhecidas — apenas para logging/validação, não bloqueia novas fontes
KNOWN_SOURCES = {
    "windows_mic",
    "linux_mic",
    "macos_mic",
    "alexa",
    "esp32",
    "collar",
    "audio_file",
    "android_app",
    "ios_app",
}


def register_text_webhook(app: Flask, text_queue: Queue) -> None:
    """
    Register the generic /webhook/text endpoint on an existing Flask app.

    This endpoint accepts transcribed text from ANY external source:
    - Windows mic sender script
    - ESP32 device
    - Collar/wearable
    - Audio file upload
    - Any HTTP client

    Request body (JSON):
    {
        "text": "transcribed text",
        "source": "windows_mic",          # identifies the source
        "session_id": "optional-id",
        "timestamp": "2026-03-17T14:00:00Z",
        "metadata": {                      # optional, any extra data
            "device": "USB Microphone",
            "whisper_model": "small",
            "language": "pt",
            "duration_ms": 3200
        }
    }

    Security: X-Cerebro-Secret header required.
    """

    @app.route("/webhook/text", methods=["POST"])
    def text_webhook():
        # Validate secret header (aceita X-Jarvis-Secret ou X-Cerebro-Secret)
        secret = (
            request.headers.get("X-Jarvis-Secret")
            or request.headers.get("X-Cerebro-Secret")
            or ""
        )
        if secret != settings.flask.webhook_secret:
            logger.warning(
                f"❌ Unauthorized /webhook/text attempt from {request.remote_addr}"
            )
            return jsonify({"error": "unauthorized"}), 401

        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "empty body"}), 400

            text = data.get("text", "").strip()
            source = data.get("source", "unknown").strip()
            session_id = data.get("session_id", "")
            timestamp_str = data.get("timestamp", "")
            metadata = data.get("metadata", {})

            if not text:
                return jsonify({"error": "empty text"}), 400

            if source not in KNOWN_SOURCES:
                logger.warning(f"⚠️  Unknown source: '{source}' — accepting anyway")

            # Parse timestamp
            try:
                transcribed_at = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                transcribed_at = datetime.now()

            # Extract optional fields from metadata
            duration_ms = metadata.get("duration_ms")
            whisper_model = metadata.get("whisper_model")
            language = metadata.get("language", settings.whisper.language)

            text_item = TextItem(
                text=text,
                source=source,
                transcribed_at=transcribed_at,
                audio_duration_ms=duration_ms,
                whisper_model=whisper_model,
                language=language,
                alexa_session_id=session_id or None,
                metadata={
                    "webhook_ip": request.remote_addr,
                    **metadata,
                },
            )

            try:
                text_queue.put_nowait(text_item)
                logger.info(
                    f"✅ Queued text from '{source}' (len={len(text)}, session={session_id or '-'})"
                )
                return jsonify({"status": "ok", "source": source}), 200
            except Exception:
                logger.error("❌ Text queue full, rejecting webhook")
                return jsonify({"error": "queue_full"}), 503

        except Exception as e:
            logger.error(f"❌ /webhook/text error: {e}", exc_info=True)
            return jsonify({"error": "internal_error"}), 500
