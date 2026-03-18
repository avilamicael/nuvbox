"""
Ferramenta de consulta por entidade (pessoa, empresa, projeto, etc.).
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta


@register_tool(
    name="buscar_por_entidade",
    description=(
        "Busca fragmentos de memória que mencionam uma entidade específica "
        "(pessoa, empresa, projeto, lugar ou conceito). "
        "Use quando o usuário perguntar sobre alguém ou algo pelo nome."
    ),
    parameters={
        "nome": {
            "type": "string",
            "description": "Nome (ou parte do nome) da entidade a buscar (ex: 'João', 'Anthropic', 'Cerebro')",
        }
    },
)
def buscar_por_entidade(nome: str, usuario_id: int) -> List[Dict[str, Any]]:
    """Busca fragmentos vinculados a entidades que correspondam ao nome informado."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    f.id,
                    f.resumo,
                    f.criado_em,
                    e.nome AS entidade_nome,
                    e.tipo AS entidade_tipo,
                    fe.contexto
                FROM fragmentos f
                JOIN fragmento_entidade fe ON fe.fragmento_id = f.id
                JOIN entidades e ON e.id = fe.entidade_id
                WHERE e.nome ILIKE %s
                  AND f.usuario_id = %s
                ORDER BY f.criado_em DESC
                LIMIT %s
                """,
                (f"%{nome}%", usuario_id, _LIMIT),
            )
            columns = ["id", "resumo", "criado_em", "entidade_nome", "entidade_tipo", "contexto"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
            logger.debug(f"buscar_por_entidade('{nome}') → {len(result)} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ buscar_por_entidade failed: {e}")
        return []
