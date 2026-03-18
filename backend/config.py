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
class LLMSettings:
    api_key: str
    model: str
    base_url: str       # None = OpenAI default | Groq = https://api.groq.com/openai/v1
    provider: str       # 'openai' | 'groq' | 'anthropic' | 'google'
    # Pricing por 1M tokens (para cost tracking)
    cost_input_per_1m: float
    cost_output_per_1m: float


@dataclass
class Modulo4Settings:
    batch_size: int
    poll_interval_seconds: int
    importance_threshold: float
    daily_cost_limit_usd: float
    max_retries: int
    dry_run: bool


@dataclass
class Modulo6Settings:
    max_rounds: int
    max_fragmentos_por_ferramenta: int


@dataclass
class Settings:
    db: DBSettings
    mic: MicSettings
    whisper: WhisperSettings
    vad: VADSettings
    flask: FlaskSettings
    queues: QueueSettings
    llm: LLMSettings
    modulo4: Modulo4Settings
    modulo6: Modulo6Settings
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
            webhook_secret=os.getenv("CEREBRO_SECRET", "change_me_before_ngrok"),
        ),
        queues=QueueSettings(
            raw_audio_max_size=int(os.getenv("RAW_AUDIO_QUEUE_MAX_SIZE", "100")),
            text_max_size=int(os.getenv("TEXT_QUEUE_MAX_SIZE", "100")),
        ),
        llm=LLMSettings(
            api_key=os.getenv("LLM_API_KEY", ""),
            model=os.getenv("LLM_MODEL", "llama-3.1-8b-instant"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
            provider=os.getenv("LLM_PROVIDER", "groq"),
            # Groq é grátis (free tier), custo = 0. OpenAI: input 0.15, output 0.60 por 1M tokens
            cost_input_per_1m=float(os.getenv("LLM_COST_INPUT_PER_1M", "0.0")),
            cost_output_per_1m=float(os.getenv("LLM_COST_OUTPUT_PER_1M", "0.0")),
        ),
        modulo4=Modulo4Settings(
            batch_size=int(os.getenv("MODULO4_BATCH_SIZE", "15")),
            poll_interval_seconds=int(os.getenv("MODULO4_POLL_INTERVAL_SECONDS", "180")),
            importance_threshold=float(os.getenv("MODULO4_IMPORTANCE_THRESHOLD", "0.25")),
            daily_cost_limit_usd=float(os.getenv("MODULO4_DAILY_COST_LIMIT_USD", "2.00")),
            max_retries=int(os.getenv("MODULO4_MAX_RETRIES", "3")),
            dry_run=os.getenv("MODULO4_DRY_RUN", "false").lower() in ("true", "1", "yes"),
        ),
        modulo6=Modulo6Settings(
            max_rounds=int(os.getenv("MODULO6_MAX_ROUNDS", "5")),
            max_fragmentos_por_ferramenta=int(os.getenv("MODULO6_MAX_FRAGMENTOS", "8")),
        ),
        log_dir=os.getenv("LOG_DIR", "logs"),
        log_level=os.getenv("LOG_LEVEL", "DEBUG"),
    )


# Global settings instance
settings = load_settings()
