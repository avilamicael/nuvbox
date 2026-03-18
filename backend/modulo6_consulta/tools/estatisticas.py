"""
Ferramentas de estatísticas e contagem sobre os fragmentos.

Funções disponíveis:
  - contar_mencoes        : COUNT simples via ILIKE no resumo
  - contar_ocorrencias    : COUNT robusto via 3 fontes (entidade + tópico + texto), deduplica por ID
  - resumo_estatistico    : Agregação geral com sentimento, score médio e top tópicos
"""

from typing import Dict, Any
from modulo3_armazenamento.db import get_connection
from modulo6_consulta.registry import register_tool
from modulo6_consulta.tools._search import ui
from utils import setup_logger

logger = setup_logger(__name__)


@register_tool(
    name="contar_mencoes",
    description=(
        "Conta quantas vezes um termo aparece nos resumos dos fragmentos. "
        "Use quando o usuário perguntar sobre frequência ou recorrência de um assunto. "
        "Exemplos: 'quantas vezes falei sobre X?', 'com que frequência menciono Y?'."
    ),
    parameters={
        "termo": {
            "type": "string",
            "description": "Palavra ou frase a contar nos resumos dos fragmentos",
        }
    },
)
def contar_mencoes(termo: str, usuario_id: int) -> Dict[str, Any]:
    """Conta fragmentos cujo resumo contenha o termo informado."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM fragmentos
                WHERE {ui('resumo')}
                  AND usuario_id = %s
                """,
                (f"%{termo}%", usuario_id),
            )
            total = cursor.fetchone()[0]
            logger.debug(f"contar_mencoes('{termo}') → {total}")
            return {"termo": termo, "total_mencoes": total}
    except Exception as e:
        logger.error(f"❌ contar_mencoes failed: {e}")
        return {"termo": termo, "total_mencoes": 0, "erro": str(e)}


@register_tool(
    name="contar_ocorrencias",
    description=(
        "Conta ocorrências de um termo buscando nas 3 fontes disponíveis: "
        "(1) entidade estruturada extraída pelo M4, "
        "(2) tópico hierárquico vinculado ao fragmento, "
        "(3) texto livre no resumo do fragmento. "
        "Os resultados são deduplificados por ID de fragmento para evitar dupla contagem. "
        "Retorna o total único e a contagem por fonte para diagnóstico de qualidade do M4. "
        "Use quando o usuário quiser saber quantas vezes algo aconteceu (ex: 'quantos cigarros fumei?', "
        "'quantas reuniões tive essa semana?'). Aceita filtro opcional de período."
    ),
    parameters={
        "termo": {
            "type": "string",
            "description": (
                "Termo a contar. Será buscado como nome de entidade, como tópico e como texto livre. "
                "Ex: 'cigarro', 'reunião', 'café'"
            ),
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
def contar_ocorrencias(
    termo: str,
    usuario_id: int,
    inicio: str = None,
    fim: str = None,
) -> Dict[str, Any]:
    """
    Conta fragmentos relacionados a um termo usando 3 fontes independentes,
    deduplificando por fragmento_id para evitar dupla contagem.

    Fontes consultadas:
      1. fragmento_entidade → entidades (via nome ILIKE)
      2. fragmento_topico   → topicos   (via caminho ILIKE)
      3. fragmentos.resumo              (via ILIKE direto)

    O total_unicos é o COUNT do UNION das 3 fontes — cada fragmento contado uma só vez,
    independente de quantas fontes o identificaram.

    O retorno inclui contagem por fonte para que o LLM possa informar ao usuário
    a qualidade da classificação do M4 (ex: se por_entidade << por_texto, o M4
    pode estar falhando na extração de entidades para esse termo).
    """
    periodo_filter = "AND f.criado_em BETWEEN %s AND %s" if (inicio and fim) else ""
    periodo_params = [inicio, fim] if (inicio and fim) else []

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Fonte 1: via entidade estruturada
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT f.id)
                FROM fragmentos f
                JOIN fragmento_entidade fe ON fe.fragmento_id = f.id
                JOIN entidades e ON e.id = fe.entidade_id
                WHERE {ui('e.nome')}
                  AND f.usuario_id = %s
                  {periodo_filter}
                """,
                [f"%{termo}%", usuario_id] + periodo_params,
            )
            por_entidade = cursor.fetchone()[0]

            # Fonte 2: via tópico estruturado
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT f.id)
                FROM fragmentos f
                JOIN fragmento_topico ft ON ft.fragmento_id = f.id
                JOIN topicos t ON t.id = ft.topico_id
                WHERE {ui('t.caminho')}
                  AND f.usuario_id = %s
                  {periodo_filter}
                """,
                [f"%{termo}%", usuario_id] + periodo_params,
            )
            por_topico = cursor.fetchone()[0]

            # Fonte 3: via texto livre no resumo
            cursor.execute(
                f"""
                SELECT COUNT(DISTINCT id)
                FROM fragmentos f
                WHERE {ui('resumo')}
                  AND usuario_id = %s
                  {periodo_filter.replace('f.criado_em', 'criado_em')}
                """,
                [f"%{termo}%", usuario_id] + periodo_params,
            )
            por_texto = cursor.fetchone()[0]

            # Total único: UNION das 3 fontes, deduplificado por fragmento_id
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT f.id
                    FROM fragmentos f
                    JOIN fragmento_entidade fe ON fe.fragmento_id = f.id
                    JOIN entidades e ON e.id = fe.entidade_id
                    WHERE {ui('e.nome')} AND f.usuario_id = %s {periodo_filter}

                    UNION

                    SELECT DISTINCT f.id
                    FROM fragmentos f
                    JOIN fragmento_topico ft ON ft.fragmento_id = f.id
                    JOIN topicos t ON t.id = ft.topico_id
                    WHERE {ui('t.caminho')} AND f.usuario_id = %s {periodo_filter}

                    UNION

                    SELECT DISTINCT id
                    FROM fragmentos f
                    WHERE {ui('resumo')} AND usuario_id = %s
                    {periodo_filter.replace('f.criado_em', 'criado_em')}
                ) sub
                """,
                (
                    [f"%{termo}%", usuario_id] + periodo_params +
                    [f"%{termo}%", usuario_id] + periodo_params +
                    [f"%{termo}%", usuario_id] + periodo_params
                ),
            )
            total_unicos = cursor.fetchone()[0]

            result = {
                "termo": termo,
                "total_unicos": total_unicos,
                "por_entidade": por_entidade,
                "por_topico": por_topico,
                "por_texto": por_texto,
            }
            if inicio and fim:
                result["periodo"] = {"inicio": inicio, "fim": fim}

            logger.debug(
                f"contar_ocorrencias('{termo}') → "
                f"total={total_unicos} (entidade={por_entidade}, topico={por_topico}, texto={por_texto})"
            )
            return result

    except Exception as e:
        logger.error(f"❌ contar_ocorrencias failed: {e}")
        return {"termo": termo, "total_unicos": 0, "erro": str(e)}


@register_tool(
    name="resumo_estatistico",
    description=(
        "Gera um resumo estatístico dos fragmentos: total, distribuição por sentimento, "
        "score médio de importância e tópicos mais frequentes. "
        "Use quando o usuário pedir uma visão geral, um balanço ou um resumo do período. "
        "Opcionalmente filtra por período (inicio/fim em ISO 8601)."
    ),
    parameters={
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
def resumo_estatistico(
    usuario_id: int,
    inicio: str = None,
    fim: str = None,
) -> Dict[str, Any]:
    """Agrega estatísticas dos fragmentos, com ou sem filtro de período."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            periodo_filter = "AND criado_em BETWEEN %s AND %s" if (inicio and fim) else ""
            params_base = [usuario_id]
            if inicio and fim:
                params_base = [inicio, fim, usuario_id]

            # Total e score médio
            cursor.execute(
                f"""
                SELECT
                    COUNT(*)                        AS total_fragmentos,
                    ROUND(AVG(importance_score)::numeric, 2) AS score_medio,
                    ROUND(MAX(importance_score)::numeric, 2) AS score_maximo
                FROM fragmentos
                WHERE usuario_id = %s
                {periodo_filter}
                """,
                ([usuario_id] + ([inicio, fim] if inicio and fim else []))
                if not (inicio and fim)
                else ([inicio, fim, usuario_id]),
            )
            row = cursor.fetchone()
            total, score_medio, score_maximo = row if row else (0, None, None)

            # Distribuição por sentimento
            cursor.execute(
                f"""
                SELECT sentimento, COUNT(*) AS qtd
                FROM fragmentos
                WHERE usuario_id = %s
                {periodo_filter}
                GROUP BY sentimento
                ORDER BY qtd DESC
                """,
                ([usuario_id] + ([inicio, fim] if inicio and fim else []))
                if not (inicio and fim)
                else ([inicio, fim, usuario_id]),
            )
            sentimentos = {row[0]: row[1] for row in cursor.fetchall()}

            # Top 5 tópicos mais frequentes no período
            cursor.execute(
                f"""
                SELECT t.caminho, COUNT(*) AS qtd
                FROM fragmento_topico ft
                JOIN topicos t ON t.id = ft.topico_id
                JOIN fragmentos f ON f.id = ft.fragmento_id
                WHERE f.usuario_id = %s
                {periodo_filter.replace('criado_em', 'f.criado_em')}
                GROUP BY t.caminho
                ORDER BY qtd DESC
                LIMIT 5
                """,
                ([usuario_id] + ([inicio, fim] if inicio and fim else []))
                if not (inicio and fim)
                else ([inicio, fim, usuario_id]),
            )
            top_topicos = [{"topico": r[0], "mencoes": r[1]} for r in cursor.fetchall()]

            result = {
                "total_fragmentos": total,
                "score_medio": float(score_medio) if score_medio is not None else None,
                "score_maximo": float(score_maximo) if score_maximo is not None else None,
                "por_sentimento": sentimentos,
                "top_topicos": top_topicos,
            }
            if inicio and fim:
                result["periodo"] = {"inicio": inicio, "fim": fim}

            logger.debug(f"resumo_estatistico() → {total} fragmentos")
            return result
    except Exception as e:
        logger.error(f"❌ resumo_estatistico failed: {e}")
        return {"erro": str(e)}
