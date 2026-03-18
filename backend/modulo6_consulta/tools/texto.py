"""
Ferramenta de busca por texto livre nos fragmentos.
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta


@register_tool(
    name="buscar_texto_livre",
    description=(
        "Busca fragmentos de memória por correspondência de texto no resumo. "
        "Use como ferramenta de fallback quando outras buscas (por tópico, entidade ou período) "
        "não forem suficientes ou quando o usuário usar termos genéricos."
    ),
    parameters={
        "termo": {
            "type": "string",
            "description": "Palavra ou frase a buscar nos resumos dos fragmentos",
        }
    },
)
def buscar_texto_livre(termo: str, usuario_id: int) -> List[Dict[str, Any]]:
    """Busca fragmentos cujo resumo contenha o termo informado (ILIKE)."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, resumo, criado_em, sentimento, importance_score
                FROM fragmentos
                WHERE resumo ILIKE %s
                  AND usuario_id = %s
                ORDER BY importance_score DESC, criado_em DESC
                LIMIT %s
                """,
                (f"%{termo}%", usuario_id, _LIMIT),
            )
            columns = ["id", "resumo", "criado_em", "sentimento", "importance_score"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
                if r["importance_score"] is not None:
                    r["importance_score"] = float(r["importance_score"])
            logger.debug(f"buscar_texto_livre('{termo}') → {len(result)} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ buscar_texto_livre failed: {e}")
        return []
