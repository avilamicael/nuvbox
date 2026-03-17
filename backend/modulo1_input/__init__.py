from modulo1_input.base_source import AudioSource, AudioChunk
from modulo1_input.mic_source import MicrophoneSource
from modulo1_input.alexa_webhook import create_alexa_app
from modulo1_input.text_webhook import register_text_webhook

__all__ = [
    # Base classes — implement these to add a new local audio source
    "AudioSource",
    "AudioChunk",
    # Built-in local sources
    "MicrophoneSource",       # Linux: USB mic via sounddevice + Silero VAD
    # Webhook server — all external sources connect via HTTP
    "create_alexa_app",       # Creates Flask app with /webhook/alexa + /webhook/text
    "register_text_webhook",  # Registers /webhook/text on an existing Flask app
]
