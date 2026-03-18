"""
Database queries for Módulo 5 — Armazenamento Estruturado.

Responsável por:
1. Buscar entidades e tópicos existentes (para contexto do LLM)
2. Salvar action_items
3. Atualizar status de entidades (ativo/pendente/ambiguo)
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from utils import setup_logger

logger = setup_logger(__name__)


class M5DBQueriesError(Exception):
    """Base exception for M5 DB query errors."""
    pass


def fetch_existing_entities(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch most-referenced active entities for LLM context injection.

    Args:
        limit: Max number to return (ordered by frequency desc)

    Returns:
        List of dicts: {id, nome, nome_normalizado, tipo, descricao}
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, nome, nome_normalizado, tipo, descricao
                FROM entidades
                WHERE status = 'ativo'
                ORDER BY frequencia DESC
                LIMIT %s
                """,
                (limit,)
            )
            columns = ["id", "nome", "nome_normalizado", "tipo", "descricao"]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        logger.error(f"❌ fetch_existing_entities failed: {e}")
        raise M5DBQueriesError(f"fetch_existing_entities failed: {e}")


def fetch_existing_topics(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch most-referenced active topics for LLM context injection.

    Args:
        limit: Max number to return (ordered by frequency desc)

    Returns:
        List of dicts: {id, caminho, frequencia}
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, caminho, frequencia
                FROM topicos
                WHERE status = 'ativo'
                ORDER BY frequencia DESC
                LIMIT %s
                """,
                (limit,)
            )
            columns = ["id", "caminho", "frequencia"]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        logger.error(f"❌ fetch_existing_topics failed: {e}")
        raise M5DBQueriesError(f"fetch_existing_topics failed: {e}")


def save_action_items(fragmento_id: int, action_items: List[str]) -> int:
    """
    Persist action items linked to a fragment.

    Args:
        fragmento_id: ID of the parent fragment
        action_items: List of action item text strings

    Returns:
        Number of items actually saved
    """
    if not action_items:
        return 0

    items_to_save = [t.strip() for t in action_items if t and t.strip()]
    if not items_to_save:
        return 0

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for texto in items_to_save:
                cursor.execute(
                    """
                    INSERT INTO action_items
                    (fragmento_id, texto, status, atualizado_por, criado_em)
                    VALUES (%s, %s, 'pendente', 'llm', NOW())
                    """,
                    (fragmento_id, texto)
                )
            conn.commit()
            logger.debug(f"Saved {len(items_to_save)} action items for fragmento {fragmento_id}")
            return len(items_to_save)

    except Exception as e:
        logger.error(f"❌ save_action_items failed: {e}")
        raise M5DBQueriesError(f"save_action_items failed: {e}")


def update_entity_status(entidade_id: int, status: str) -> None:
    """
    Update entity status for disambiguation workflow.

    Args:
        entidade_id: Entity ID to update
        status: One of 'ativo', 'pendente', 'ambiguo'
    """
    valid_statuses = {"ativo", "pendente", "ambiguo"}
    if status not in valid_statuses:
        raise M5DBQueriesError(
            f"Invalid status '{status}', must be one of {valid_statuses}"
        )

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE entidades SET status = %s WHERE id = %s",
                (status, entidade_id)
            )
            conn.commit()
            logger.debug(f"Updated entity {entidade_id} status → {status}")

    except Exception as e:
        logger.error(f"❌ update_entity_status failed: {e}")
        raise M5DBQueriesError(f"update_entity_status failed: {e}")
