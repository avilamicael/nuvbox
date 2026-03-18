"""
Ferramenta de consulta por action items / tarefas.
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta


@register_tool(
    name="listar_action_items",
    description=(
        "Lista tarefas e action items registrados pelo sistema. "
        "Use quando o usuário perguntar sobre tarefas pendentes, concluídas ou canceladas."
    ),
    parameters={
        "status": {
            "type": "string",
            "enum": ["pendente", "concluido", "cancelado"],
            "description": "Filtro de status da tarefa: 'pendente', 'concluido' ou 'cancelado'",
        }
    },
)
def listar_action_items(status: str, usuario_id: int) -> List[Dict[str, Any]]:
    """Lista action items pelo status, com contexto do fragmento de origem."""
    valid_statuses = {"pendente", "concluido", "cancelado"}
    if status not in valid_statuses:
        logger.warning(f"Status inválido '{status}', usando 'pendente'")
        status = "pendente"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    ai.id,
                    ai.texto,
                    ai.status,
                    ai.criado_em,
                    f.resumo AS fragmento_resumo,
                    f.criado_em AS fragmento_criado_em
                FROM action_items ai
                JOIN fragmentos f ON f.id = ai.fragmento_id
                WHERE ai.status = %s
                  AND ai.usuario_id = %s
                ORDER BY ai.criado_em DESC
                LIMIT %s
                """,
                (status, usuario_id, _LIMIT),
            )
            columns = ["id", "texto", "status", "criado_em", "fragmento_resumo", "fragmento_criado_em"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
                if r["fragmento_criado_em"]:
                    r["fragmento_criado_em"] = r["fragmento_criado_em"].isoformat()
            logger.debug(f"listar_action_items(status='{status}') → {len(result)} itens")
            return result
    except Exception as e:
        logger.error(f"❌ listar_action_items failed: {e}")
        return []
