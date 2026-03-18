"""
Ferramenta de busca combinada: tópico + período de tempo.
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
    name="buscar_topico_periodo",
    description=(
        "Busca fragmentos de memória que combinam um tópico específico E um período de tempo. "
        "Use quando o usuário mencionar tanto um assunto quanto uma data/período. "
        "Exemplo: 'o que eu falei sobre saúde em fevereiro?' ou 'reuniões desta semana'."
    ),
    parameters={
        "topico": {
            "type": "string",
            "description": "Nome ou parte do caminho do tópico (ex: 'saúde', 'Trabalho > Reuniões')",
        },
        "inicio": {
            "type": "string",
            "description": "Data/hora de início no formato ISO 8601 (ex: '2026-02-01T00:00:00')",
        },
        "fim": {
            "type": "string",
            "description": "Data/hora de fim no formato ISO 8601 (ex: '2026-02-28T23:59:59')",
        },
    },
)
def buscar_topico_periodo(
    topico: str,
    inicio: str,
    fim: str,
    usuario_id: int,
) -> List[Dict[str, Any]]:
    """Busca fragmentos vinculados a um tópico dentro de um intervalo de datas."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    f.id,
                    f.resumo,
                    f.criado_em,
                    f.sentimento,
                    f.importance_score,
                    t.caminho AS topico_caminho
                FROM fragmentos f
                JOIN fragmento_topico ft ON ft.fragmento_id = f.id
                JOIN topicos t ON t.id = ft.topico_id
                WHERE {ui('t.caminho')}
                  AND f.criado_em BETWEEN %s AND %s
                  AND f.usuario_id = %s
                ORDER BY f.criado_em DESC
                LIMIT %s
                """,
                (f"%{topico}%", inicio, fim, usuario_id, _LIMIT),
            )
            columns = ["id", "resumo", "criado_em", "sentimento", "importance_score", "topico_caminho"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
                if r["importance_score"] is not None:
                    r["importance_score"] = float(r["importance_score"])
            logger.debug(
                f"buscar_topico_periodo('{topico}', '{inicio}' → '{fim}') → {len(result)} fragmentos"
            )
            return result
    except Exception as e:
        logger.error(f"❌ buscar_topico_periodo failed: {e}")
        return []
