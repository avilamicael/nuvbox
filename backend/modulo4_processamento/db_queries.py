"""
Database queries for Módulo 4.

Responsável por:
1. Buscar transcrições pendentes
2. Salvar fragmentos, entidades, relacionamentos
3. Atualizar status de processamento
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from modulo3_armazenamento.db import get_connection
from utils import setup_logger

logger = setup_logger(__name__)


class DBQueriesError(Exception):
    """Base exception for DB query errors."""
    pass


def fetch_pending_transcriptions(limit: int) -> List[Dict[str, Any]]:
    """
    Fetch pending transcriptions for processing.

    Args:
        limit: Max number to fetch

    Returns:
        List of dicts with id, texto, criado_em
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, texto, criado_em, fonte
                FROM transcricoes
                WHERE status = 'pending'
                ORDER BY criado_em ASC
                LIMIT %s
                """,
                (limit,)
            )

            columns = ["id", "texto", "criado_em", "fonte"]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        logger.error(f"❌ Failed to fetch pending transcriptions: {e}")
        raise DBQueriesError(f"Fetch pending failed: {e}")


def reset_stuck_processing(timeout_minutes: int = 10) -> int:
    """
    Reset transcriptions stuck in 'processing' state for too long.

    Call this on BatchWorker startup to recover from crashes.

    Args:
        timeout_minutes: How long before marking as stuck

    Returns:
        Number of records reset
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            timeout = datetime.now() - timedelta(minutes=timeout_minutes)

            cursor.execute(
                """
                UPDATE transcricoes
                SET status = 'pending', modulo4_erro = NULL
                WHERE status = 'processing' AND processado_em < %s
                RETURNING id
                """,
                (timeout,)
            )

            count = cursor.rowcount
            conn.commit()

            if count > 0:
                logger.warning(f"⚠️  Reset {count} stuck processing records")

            return count

    except Exception as e:
        logger.error(f"❌ Failed to reset stuck processing: {e}")
        raise DBQueriesError(f"Reset stuck failed: {e}")


def mark_processing(transcricao_id: int) -> None:
    """Mark a transcription as being processed."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE transcricoes SET status = 'processing', processado_em = NOW() WHERE id = %s",
                (transcricao_id,)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Failed to mark processing: {e}")
        raise DBQueriesError(f"Mark processing failed: {e}")


def mark_processed(transcricao_id: int, fragmento_id: int = None) -> None:
    """Mark a transcription as successfully processed."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transcricoes
                SET status = 'processed', processado_em = NOW(), modulo4_erro = NULL
                WHERE id = %s
                """,
                (transcricao_id,)
            )
            conn.commit()
            logger.debug(f"Marked transcription {transcricao_id} as processed")
    except Exception as e:
        logger.error(f"❌ Failed to mark processed: {e}")
        raise DBQueriesError(f"Mark processed failed: {e}")


def mark_skipped(transcricao_id: int, reason: str = "importance < threshold") -> None:
    """Mark a transcription as skipped (not important enough)."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transcricoes
                SET status = 'skipped', processado_em = NOW(), modulo4_erro = %s
                WHERE id = %s
                """,
                (reason, transcricao_id)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Failed to mark skipped: {e}")
        raise DBQueriesError(f"Mark skipped failed: {e}")


def mark_error(transcricao_id: int, error_msg: str) -> None:
    """Mark a transcription as errored."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transcricoes
                SET status = 'error', processado_em = NOW(), modulo4_erro = %s
                WHERE id = %s
                """,
                (error_msg, transcricao_id)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Failed to mark error: {e}")
        raise DBQueriesError(f"Mark error failed: {e}")


def save_fragment(
    transcricao_id: int,
    resumo: str,
    importance_score: Decimal,
    input_tokens: int,
    output_tokens: int,
    model_used: str,
    sentimento: str = None,
    tem_decisao: bool = False,
    tem_pergunta: bool = False,
) -> int:
    """
    Save a fragment (processed transcription).

    Args:
        transcricao_id: ID of source transcription
        resumo: 1-2 sentence summary
        importance_score: 0.0-1.0 score
        input_tokens: Tokens used for input
        output_tokens: Tokens used for output
        model_used: Model name (e.g., 'gpt-4o-mini')
        sentimento: positivo|negativo|neutro|misto (M5)
        tem_decisao: True if a decision was made (M5)
        tem_pergunta: True if an open question exists (M5)

    Returns:
        ID of inserted fragment
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fragmentos
                (transcricao_id, resumo, importance_score, tokens_input, tokens_output,
                 model_used, sentimento, tem_decisao, tem_pergunta, criado_em)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (transcricao_id, resumo, importance_score, input_tokens, output_tokens,
                 model_used, sentimento, tem_decisao, tem_pergunta)
            )
            fragmento_id = cursor.fetchone()[0]
            conn.commit()
            return fragmento_id

    except Exception as e:
        logger.error(f"❌ Failed to save fragment: {e}")
        raise DBQueriesError(f"Save fragment failed: {e}")


def upsert_entidade(
    nome: str,
    nome_normalizado: str,
    tipo: str
) -> int:
    """
    Insert or update entity (deduplication by tipo + nome_normalizado).

    Args:
        nome: Raw entity name
        nome_normalizado: Lowercase version for deduplication
        tipo: Entity type

    Returns:
        ID of inserted/existing entity
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Try insert (will fail if exists)
            try:
                cursor.execute(
                    """
                    INSERT INTO entidades (nome, nome_normalizado, tipo, criado_em)
                    VALUES (%s, %s, %s, NOW())
                    RETURNING id
                    """,
                    (nome, nome_normalizado, tipo)
                )
                entidade_id = cursor.fetchone()[0]
                conn.commit()
                logger.debug(f"Created entity: {tipo}/{nome_normalizado} (id={entidade_id})")
                return entidade_id

            except Exception:
                # Already exists - fetch it and update frequency
                conn.rollback()
                cursor.execute(
                    """
                    UPDATE entidades
                    SET frequencia = frequencia + 1, ultima_mencao_em = NOW()
                    WHERE tipo = %s AND nome_normalizado = %s
                    RETURNING id
                    """,
                    (tipo, nome_normalizado)
                )
                entidade_id = cursor.fetchone()[0]
                conn.commit()
                logger.debug(f"Updated entity: {tipo}/{nome_normalizado} (id={entidade_id})")
                return entidade_id

    except Exception as e:
        logger.error(f"❌ Failed to upsert entity: {e}")
        raise DBQueriesError(f"Upsert entity failed: {e}")


def save_fragmento_entidade(
    fragmento_id: int,
    entidade_id: int,
    contexto: str,
    posicao_relativa: str = None
) -> int:
    """Link fragment to entity with context."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fragmento_entidade
                (fragmento_id, entidade_id, contexto, posicao_relativa, criado_em)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (fragmento_id, entidade_id, contexto, posicao_relativa)
            )
            link_id = cursor.fetchone()[0]
            conn.commit()
            return link_id

    except Exception as e:
        logger.error(f"❌ Failed to save fragmento_entidade link: {e}")
        raise DBQueriesError(f"Save link failed: {e}")


def upsert_topico(caminho: str) -> int:
    """
    Insert or get topic by hierarchical path.

    Args:
        caminho: e.g., "Trabalho > Cerebro > Bugs"

    Returns:
        ID of inserted/existing topic
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if exists
            cursor.execute(
                "SELECT id FROM topicos WHERE caminho = %s",
                (caminho,)
            )
            row = cursor.fetchone()
            if row:
                # Update frequency
                cursor.execute(
                    """
                    UPDATE topicos
                    SET frequencia = frequencia + 1, ultima_mencao_em = NOW()
                    WHERE caminho = %s
                    RETURNING id
                    """,
                    (caminho,)
                )
                topico_id = cursor.fetchone()[0]
                conn.commit()
                return topico_id

            # Insert new
            parts = [p.strip() for p in caminho.split(">")]
            nome = parts[-1]
            nivel = len(parts)
            pai_id = None

            # Try to find parent if nivel > 1
            if nivel > 1:
                caminho_pai = " > ".join(parts[:-1])
                cursor.execute(
                    "SELECT id FROM topicos WHERE caminho = %s",
                    (caminho_pai,)
                )
                pai_row = cursor.fetchone()
                if pai_row:
                    pai_id = pai_row[0]

            cursor.execute(
                """
                INSERT INTO topicos (nome, caminho, nivel, pai_id, criado_em)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (nome, caminho, nivel, pai_id)
            )
            topico_id = cursor.fetchone()[0]
            conn.commit()
            logger.debug(f"Created topic: {caminho} (id={topico_id})")
            return topico_id

    except Exception as e:
        logger.error(f"❌ Failed to upsert topic: {e}")
        raise DBQueriesError(f"Upsert topic failed: {e}")


def save_fragmento_topico(
    fragmento_id: int,
    topico_id: int,
    confianca: Decimal,
    eh_principal: bool = False
) -> int:
    """Link fragment to topic with confidence."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO fragmento_topico
                (fragmento_id, topico_id, confianca, eh_principal, criado_em)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (fragmento_id, topico_id, confianca, eh_principal)
            )
            link_id = cursor.fetchone()[0]
            conn.commit()
            return link_id

    except Exception as e:
        logger.error(f"❌ Failed to save fragmento_topico link: {e}")
        raise DBQueriesError(f"Save topic link failed: {e}")
