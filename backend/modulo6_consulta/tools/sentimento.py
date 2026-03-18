"""
Ferramenta de consulta por sentimento dos fragmentos.
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta

_SENTIMENTOS_VALIDOS = {"positivo", "negativo", "neutro", "misto"}


@register_tool(
    name="buscar_por_sentimento",
    description=(
        "Busca fragmentos de memória filtrados pelo sentimento predominante. "
        "Use quando o usuário perguntar sobre memórias positivas, negativas, animadas, "
        "frustrantes, neutras ou mistas. "
        "Valores aceitos: 'positivo', 'negativo', 'neutro', 'misto'."
    ),
    parameters={
        "sentimento": {
            "type": "string",
            "enum": ["positivo", "negativo", "neutro", "misto"],
            "description": "Sentimento a filtrar: 'positivo', 'negativo', 'neutro' ou 'misto'",
        }
    },
)
def buscar_por_sentimento(sentimento: str, usuario_id: int) -> List[Dict[str, Any]]:
    """Busca fragmentos com o sentimento informado, ordenados por importance_score."""
    if sentimento not in _SENTIMENTOS_VALIDOS:
        logger.warning(f"Sentimento inválido '{sentimento}', usando 'neutro'")
        sentimento = "neutro"

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, resumo, criado_em, sentimento, importance_score
                FROM fragmentos
                WHERE sentimento = %s
                  AND usuario_id = %s
                ORDER BY importance_score DESC, criado_em DESC
                LIMIT %s
                """,
                (sentimento, usuario_id, _LIMIT),
            )
            columns = ["id", "resumo", "criado_em", "sentimento", "importance_score"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
                if r["importance_score"] is not None:
                    r["importance_score"] = float(r["importance_score"])
            logger.debug(f"buscar_por_sentimento('{sentimento}') → {len(result)} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ buscar_por_sentimento failed: {e}")
        return []
