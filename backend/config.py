import os
from dotenv import load_dotenv
from dataclasses import dataclass

# Load .env file (if it exists)
load_dotenv()


@dataclass
class DBSettings:
    host: str
    port: int
    user: str
    password: str
    name: str

    @property
    def dsn(self) -> str:
        """PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class MicSettings:
    device_id: int
    sample_rate: int
    chunk_size: int


@dataclass
class WhisperSettings:
    model: str
    language: str


@dataclass
class VADSettings:
    silence_duration_ms: int
    min_speech_duration_ms: int


@dataclass
class FlaskSettings:
    host: str
    port: int
    webhook_secret: str


@dataclass
class QueueSettings:
    raw_audio_max_size: int
    text_max_size: int


@dataclass
class Settings:
    db: DBSettings
    mic: MicSettings
    whisper: WhisperSettings
    vad: VADSettings
    flask: FlaskSettings
    queues: QueueSettings
    log_dir: str
    log_level: str


def load_settings() -> Settings:
    """Load all settings from environment variables."""
    return Settings(
        db=DBSettings(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            user=os.getenv("DB_USER", "cerebro"),
            password=os.getenv("DB_PASSWORD", "cerebro"),
            name=os.getenv("DB_NAME", "cerebro_db"),
        ),
        mic=MicSettings(
            device_id=int(os.getenv("MIC_DEVICE_ID", "0")),
            sample_rate=int(os.getenv("MIC_SAMPLE_RATE", "16000")),
            chunk_size=int(os.getenv("MIC_CHUNK_SIZE", "512")),
        ),
        whisper=WhisperSettings(
            model=os.getenv("WHISPER_MODEL", "small"),
            language=os.getenv("WHISPER_LANGUAGE", "pt"),
        ),
        vad=VADSettings(
            silence_duration_ms=int(os.getenv("VAD_SILENCE_DURATION_MS", "500")),
            min_speech_duration_ms=int(os.getenv("VAD_MIN_SPEECH_DURATION_MS", "300")),
        ),
        flask=FlaskSettings(
            host=os.getenv("FLASK_HOST", "0.0.0.0"),
            port=int(os.getenv("FLASK_PORT", "5001")),
            webhook_secret=os.getenv("ALEXA_WEBHOOK_SECRET", "change_me_before_ngrok"),
        ),
        queues=QueueSettings(
            raw_audio_max_size=int(os.getenv("RAW_AUDIO_QUEUE_MAX_SIZE", "100")),
            text_max_size=int(os.getenv("TEXT_QUEUE_MAX_SIZE", "100")),
        ),
        log_dir=os.getenv("LOG_DIR", "logs"),
        log_level=os.getenv("LOG_LEVEL", "DEBUG"),
    )


# Global settings instance
settings = load_settings()
