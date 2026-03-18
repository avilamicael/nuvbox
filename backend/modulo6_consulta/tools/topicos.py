"""
Ferramentas de consulta por tópico.
"""

from typing import List, Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

_LIMIT = settings.modulo6.max_fragmentos_por_ferramenta


@register_tool(
    name="buscar_por_topico",
    description=(
        "Busca fragmentos de memória relacionados a um tópico específico. "
        "Use quando o usuário menciona um assunto, área ou tema (ex: 'Cerebro', 'trabalho', 'saúde')."
    ),
    parameters={
        "topico": {
            "type": "string",
            "description": "Nome ou parte do caminho do tópico a buscar (ex: 'Cerebro', 'Trabalho > Reuniões')",
        }
    },
)
def buscar_por_topico(topico: str, usuario_id: int) -> List[Dict[str, Any]]:
    """Busca fragmentos vinculados a tópicos que correspondam ao termo informado."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT
                    f.id,
                    f.resumo,
                    f.criado_em,
                    f.sentimento,
                    t.caminho AS topico_caminho
                FROM fragmentos f
                JOIN fragmento_topico ft ON ft.fragmento_id = f.id
                JOIN topicos t ON t.id = ft.topico_id
                WHERE t.caminho ILIKE %s
                  AND f.usuario_id = %s
                ORDER BY f.criado_em DESC
                LIMIT %s
                """,
                (f"%{topico}%", usuario_id, _LIMIT),
            )
            columns = ["id", "resumo", "criado_em", "sentimento", "topico_caminho"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["criado_em"]:
                    r["criado_em"] = r["criado_em"].isoformat()
            logger.debug(f"buscar_por_topico('{topico}') → {len(result)} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ buscar_por_topico failed: {e}")
        return []


@register_tool(
    name="listar_topicos",
    description=(
        "Lista os tópicos mais frequentes do usuário, ordenados por frequência. "
        "Use quando o usuário quer saber sobre quais assuntos falou mais."
    ),
    parameters={},
)
def listar_topicos(usuario_id: int) -> List[Dict[str, Any]]:
    """Retorna os 30 tópicos mais frequentes do usuário."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, caminho, frequencia, ultima_mencao_em
                FROM topicos
                WHERE usuario_id = %s AND status = 'ativo'
                ORDER BY frequencia DESC
                LIMIT 30
                """,
                (usuario_id,),
            )
            columns = ["id", "caminho", "frequencia", "ultima_mencao_em"]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            for r in result:
                if r["ultima_mencao_em"]:
                    r["ultima_mencao_em"] = r["ultima_mencao_em"].isoformat()
            logger.debug(f"listar_topicos() → {len(result)} tópicos")
            return result
    except Exception as e:
        logger.error(f"❌ listar_topicos failed: {e}")
        return []
