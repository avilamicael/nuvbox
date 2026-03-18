"""
Ferramenta de consulta por importance_score dos fragmentos.
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta


@register_tool(
    name="buscar_por_importancia",
    description=(
        "Busca os fragmentos de memória mais importantes, acima de um score mínimo. "
        "Use quando o usuário perguntar sobre memórias relevantes, importantes ou marcantes. "
        "O importance_score vai de 0.0 a 1.0. "
        "Guia: 0.5 = relevante, 0.7 = importante, 0.85 = muito importante, 0.95 = crítico. "
        "Opcionalmente filtra por período (inicio/fim em ISO 8601)."
    ),
    parameters={
        "minimo": {
            "type": "number",
            "description": "Score mínimo de importância (0.0 a 1.0). Ex: 0.7 para 'importante'",
        },
        "inicio": {
            "type": "string",
            "description": "Data/hora de início no formato ISO 8601 (opcional)",
        },
        "fim": {
            "type": "string",
            "description": "Data/hora de fim no formato ISO 8601 (opcional)",
        },
    },
)
def buscar_por_importancia(
    minimo: float,
    usuario_id: int,
    inicio: str = None,
    fim: str = None,
) -> List[Dict[str, Any]]:
    """Busca fragmentos com importance_score >= minimo, opcionalmente dentro de um período."""
    minimo = max(0.0, min(1.0, float(minimo)))

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            if inicio and fim:
                cursor.execute(
                    """
                    SELECT id, resumo, criado_em, sentimento, importance_score
                    FROM fragmentos
                    WHERE importance_score >= %s
                      AND criado_em BETWEEN %s AND %s
                      AND usuario_id = %s
                    ORDER BY importance_score DESC, criado_em DESC
                    LIMIT %s
                    """,
                    (minimo, inicio, fim, usuario_id, _LIMIT),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, resumo, criado_em, sentimento, importance_score
                    FROM fragmentos
                    WHERE importance_score >= %s
                      AND usuario_id = %s
                    ORDER BY importance_score DESC, criado_em DESC
                    LIMIT %s
                    """,
                    (minimo, usuario_id, _LIMIT),
                )

            columns = ["id", "resumo", "criado_em", "sentimento", "importance_score"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
                if r["importance_score"] is not None:
                    r["importance_score"] = float(r["importance_score"])
            logger.debug(f"buscar_por_importancia(minimo={minimo}) → {len(result)} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ buscar_por_importancia failed: {e}")
        return []
