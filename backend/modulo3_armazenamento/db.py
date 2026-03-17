import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Thread-safe connection pool
_connection_pool = None


def initialize_pool():
    """Create the connection pool (call once at startup)."""
    global _connection_pool
    try:
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            host=settings.db.host,
            port=settings.db.port,
            user=settings.db.user,
            password=settings.db.password,
            database=settings.db.name,
            connect_timeout=5,
        )
        logger.info("Connection pool initialized")
    except psycopg2.Error as e:
        logger.error(f"Failed to initialize connection pool: {e}")
        raise


def close_pool():
    """Close all connections in the pool (call at shutdown)."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        logger.info("Connection pool closed")


@contextmanager
def get_connection():
    """
    Context manager for getting a connection from the pool.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    if _connection_pool is None:
        raise RuntimeError("Connection pool not initialized. Call initialize_pool() first.")

    conn = _connection_pool.getconn()
    try:
        yield conn
    finally:
        _connection_pool.putconn(conn)


def insert_transcription(
    texto: str,
    fonte: str,
    duracao_ms: int = None,
    modelo_whisper: str = None,
    idioma: str = None,
    sessao_id: str = None,
    metadados: dict = None,
) -> int:
    """
    Insert a transcription record into the database.

    Args:
        texto: The transcribed text
        fonte: Source identifier ('mic_usb', 'alexa', etc.)
        duracao_ms: Audio duration in milliseconds (None for Alexa)
        modelo_whisper: Whisper model used (None for Alexa)
        idioma: Language code (e.g., 'pt', 'en')
        sessao_id: Alexa session ID (None for mic)
        metadados: JSON metadata for future modules

    Returns:
        The ID of the inserted row
    """
    import json

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            metadados_json = json.dumps(metadados) if metadados else None
            cursor.execute(
                """
                INSERT INTO transcricoes (texto, fonte, duracao_ms, modelo_whisper, idioma, sessao_id, metadados)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (texto, fonte, duracao_ms, modelo_whisper, idioma, sessao_id, metadados_json),
            )
            row_id = cursor.fetchone()[0]
            conn.commit()
            logger.debug(f"Inserted transcription ID {row_id} from source '{fonte}'")
            return row_id
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Failed to insert transcription: {e}")
            raise


def get_recent_transcriptions(limit: int = 10) -> list:
    """
    Fetch recent transcriptions for debugging/monitoring.

    Args:
        limit: Number of rows to return

    Returns:
        List of dictionaries with transcription data
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, texto, fonte, criado_em, duracao_ms, modelo_whisper, idioma, sessao_id
                FROM transcricoes
                ORDER BY criado_em DESC
                LIMIT %s
                """,
                (limit,),
            )
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        except psycopg2.Error as e:
            logger.error(f"Failed to fetch transcriptions: {e}")
            raise
