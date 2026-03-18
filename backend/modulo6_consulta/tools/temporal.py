"""
Ferramenta de consulta por período de tempo.
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta


@register_tool(
    name="buscar_por_periodo",
    description=(
        "Busca fragmentos de memória registrados dentro de um período de tempo. "
        "Use quando o usuário mencionar datas ou períodos (ex: 'esta semana', 'ontem', 'em março'). "
        "Converta os períodos para datas ISO antes de chamar."
    ),
    parameters={
        "inicio": {
            "type": "string",
            "description": "Data/hora de início no formato ISO 8601 (ex: '2026-03-11T00:00:00')",
        },
        "fim": {
            "type": "string",
            "description": "Data/hora de fim no formato ISO 8601 (ex: '2026-03-18T23:59:59')",
        },
    },
)
def buscar_por_periodo(inicio: str, fim: str, usuario_id: int) -> List[Dict[str, Any]]:
    """Busca fragmentos criados entre as datas inicio e fim."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, resumo, criado_em, sentimento, importance_score
                FROM fragmentos
                WHERE criado_em BETWEEN %s AND %s
                  AND usuario_id = %s
                ORDER BY criado_em DESC
                LIMIT %s
                """,
                (inicio, fim, usuario_id, _LIMIT),
            )
            columns = ["id", "resumo", "criado_em", "sentimento", "importance_score"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
                if r["importance_score"] is not None:
                    r["importance_score"] = float(r["importance_score"])
            logger.debug(f"buscar_por_periodo('{inicio}' → '{fim}') → {len(result)} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ buscar_por_periodo failed: {e}")
        return []
