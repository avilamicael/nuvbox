"""
Ferramenta de busca na transcrição bruta (texto original, antes do processamento pelo M4).
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from modulo6_consulta.tools._search import ui
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta


@register_tool(
    name="buscar_transcricao",
    description=(
        "Busca no texto original das transcrições (antes do processamento pelo M4). "
        "Use quando buscar por palavras exatas que podem não ter sido preservadas no resumo. "
        "Útil para termos técnicos, nomes próprios raros, ou citações diretas. "
        "Retorna fragmentos cujas transcrições de origem contenham o termo buscado."
    ),
    parameters={
        "termo": {
            "type": "string",
            "description": "Palavra ou frase a buscar no texto original da transcrição",
        }
    },
)
def buscar_transcricao(termo: str, usuario_id: int) -> List[Dict[str, Any]]:
    """Busca fragmentos cujas transcrições de origem contenham o termo (ILIKE no texto bruto)."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    f.id,
                    f.resumo,
                    f.criado_em,
                    f.importance_score,
                    LEFT(tr.texto, 300) AS trecho_transcricao
                FROM fragmentos f
                JOIN transcricoes tr ON tr.id = f.transcricao_id
                WHERE {ui('tr.texto')}
                  AND f.usuario_id = %s
                ORDER BY f.importance_score DESC, f.criado_em DESC
                LIMIT %s
                """,
                (f"%{termo}%", usuario_id, _LIMIT),
            )
            columns = ["id", "resumo", "criado_em", "importance_score", "trecho_transcricao"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
                if r["importance_score"] is not None:
                    r["importance_score"] = float(r["importance_score"])
            logger.debug(f"buscar_transcricao('{termo}') → {len(result)} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ buscar_transcricao failed: {e}")
        return []
