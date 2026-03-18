"""
Query Agent — Módulo 6.

Recebe uma pergunta em linguagem natural e usa tool calling para buscar
no banco de dados do Cerebro, sintetizando uma resposta em PT-BR.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

import modulo6_consulta.tools  # noqa: F401 — ativa todos os @register_tool
from modulo6_consulta.registry import get_all_tools, get_tools_by_names, dispatch, M6RegistryError
from modulo4_processamento.openai_client import OpenAIClient, OpenAIClientError
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

MAX_ROUNDS = settings.modulo6.max_rounds
MAX_TOOL_CALLS_PER_ROUND = 5   # Proteção contra LLMs que geram dezenas de calls idênticas
MAX_TOOL_RESULT_CHARS = 1500   # Trunca resultado individual para não explodir o contexto

# ---------------------------------------------------------------------------
# Tool routing — seleciona 3-4 ferramentas relevantes por tipo de pergunta.
# Reduz drasticamente o contexto enviado ao LLM, melhorando velocidade e
# qualidade de resposta em modelos pequenos (llama, mistral, etc).
#
# Cada grupo tem ferramentas primárias + "buscar_texto_livre" sempre incluído
# como fallback universal. Se nenhum grupo casar, usa o conjunto padrão.
# ---------------------------------------------------------------------------

_ROUTING_RULES: List[Dict] = [
    {
        "keywords": ["quantos", "quantas", "vezes", "contabilizar", "contar", "frequência", "frequencia"],
        "tools": ["contar_ocorrencias", "contar_mencoes", "buscar_texto_livre"],
    },
    {
        "keywords": ["tarefa", "tarefas", "pendente", "pendências", "pendencias", "fazer", "concluí", "conclui", "ação", "ações", "action"],
        "tools": ["listar_action_items", "buscar_texto_livre"],
    },
    {
        "keywords": ["resumo", "balanço", "balanco", "visão geral", "visao geral", "estatística", "estatistica", "média", "media", "score"],
        "tools": ["resumo_estatistico", "listar_topicos", "buscar_texto_livre"],
    },
    {
        "keywords": ["animado", "triste", "frustrado", "positivo", "negativo", "neutro", "misto", "sentimento", "feliz", "chateado"],
        "tools": ["buscar_por_sentimento", "buscar_texto_livre"],
    },
    {
        "keywords": ["importante", "importância", "importancia", "relevante", "crítico", "critico", "marcante"],
        "tools": ["buscar_por_importancia", "buscar_texto_livre"],
    },
    {
        "keywords": ["semana", "ontem", "hoje", "mês", "mes", "janeiro", "fevereiro", "março", "marco",
                     "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
                     "período", "periodo", "data", "quando", "ano", "anual"],
        "tools": ["buscar_por_periodo", "buscar_topico_periodo", "buscar_texto_livre"],
    },
    {
        "keywords": ["assunto", "tópico", "topico", "tema", "sobre o que", "falo mais", "falar sobre"],
        "tools": ["buscar_por_topico", "listar_topicos", "buscar_texto_livre"],
    },
]

_DEFAULT_TOOLS = ["buscar_por_entidade", "buscar_por_topico", "buscar_texto_livre"]


def _select_tools(pergunta: str) -> list:
    """
    Seleciona ferramentas relevantes para a pergunta usando keyword matching.

    Estratégia:
    - Varre as regras em ordem; usa o primeiro grupo que der match.
    - Se nenhum grupo casar, usa _DEFAULT_TOOLS (entidade + tópico + texto livre).
    - buscar_texto_livre está sempre presente como fallback universal.

    Benefício: reduz de 13 para 2-4 ferramentas por chamada, diminuindo
    o contexto e a latência do LLM, especialmente em modelos pequenos.
    """
    p = pergunta.lower()
    for rule in _ROUTING_RULES:
        if any(kw in p for kw in rule["keywords"]):
            selected = rule["tools"]
            logger.info(f"🗺️  Tool routing → {selected} (match: {[kw for kw in rule['keywords'] if kw in p][:3]})")
            return get_tools_by_names(selected)

    logger.info(f"🗺️  Tool routing → {_DEFAULT_TOOLS} (default)")
    return get_tools_by_names(_DEFAULT_TOOLS)

def _build_system_prompt() -> str:
    from datetime import date
    hoje = date.today().strftime("%d/%m/%Y")
    return f"""\
Você é o Cerebro, um assistente de segunda memória pessoal.
Você tem acesso às memórias do usuário através de ferramentas de busca no banco de dados.

Data de hoje: {hoje}

Instruções gerais:
- Responda SEMPRE em português brasileiro.
- Use as ferramentas disponíveis para buscar informações antes de responder.
- Seja conciso e direto. Cite datas quando relevante.
- Nunca invente informações — use apenas o que as ferramentas retornarem.
- Se não encontrar nada relevante, diga claramente que não há memórias sobre esse assunto.

Instruções de busca:
- Use EXATAMENTE a grafia portuguesa que o usuário usou. NUNCA translitere nomes
  (ex: "Belinha" NÃO é "Beliña", "João" NÃO é "Joao", "café" NÃO é "cafe").
- Se buscar_por_entidade retornar vazio, tente buscar_texto_livre com o mesmo termo.
- Para contagens (quantas vezes, quantos), use contar_ocorrencias — ela busca por
  entidade, tópico E texto livre ao mesmo tempo, evitando perder registros.
- Não chame a mesma ferramenta com os mesmos argumentos mais de uma vez.
- Prefira 1-2 ferramentas bem escolhidas a chamar muitas ferramentas diferentes.
- Quando uma pessoa tiver nome simples (ex: "João"), tente buscar pelo primeiro nome
  E pelo nome completo se disponível. Use buscar_texto_livre como fallback.

Instruções sobre síntese e precisão:
- Reporte APENAS o que está explicitamente nos fragmentos retornados pelas ferramentas.
- NUNCA infira relacionamentos, cargos ou contextos que não estejam escritos nos dados.
- Pessoas com nomes parecidos (ex: "Luiz" e "Luís") são pessoas DIFERENTES — não as confunda.
- Se os dados forem insuficientes para responder completamente, diga o que sabe e
  informe que não há mais detalhes registrados — nunca complete com suposições.

REGRA CRÍTICA — isolamento de entidades:
- Um fragmento pode mencionar várias pessoas ao mesmo tempo. Isso NÃO significa que
  essas pessoas têm relação entre si.
- Exemplo ERRADO: fragmento diz "Márcio é meu padrasto e tenho irmãos Erick e Luiz".
  Conclusão errada: "Erick e Luiz são irmãos do Márcio". ERRADO — são irmãos do usuário.
- Ao responder sobre uma pessoa específica (ex: "quem é Márcio?"), reporte SOMENTE
  o que o fragmento diz SOBRE Márcio, ignorando outras pessoas citadas no mesmo fragmento.
- NUNCA atribua a uma pessoa informações que pertencem a outra pessoa no mesmo fragmento.

Instruções sobre datas:
- A data de hoje é {hoje}. Use isso como referência para calcular períodos.
- "esta semana" = segunda-feira até hoje. "este mês" = dia 1 até hoje.
- "já fumei" / "já falei" / "ao todo" / sem período especificado = NÃO passe inicio/fim.
  Omitir o período faz a busca em TODOS os registros, que é o correto nesses casos.
- Só passe inicio/fim quando o usuário especificar explicitamente um período de tempo.
"""


@dataclass
class QueryRequest:
    pergunta: str
    usuario_id: int


@dataclass
class QueryResponse:
    resposta: str
    fragmentos: List[Dict[str, Any]] = field(default_factory=list)
    ferramentas_usadas: List[str] = field(default_factory=list)


def run(request: QueryRequest) -> QueryResponse:
    """
    Executa o agente de consulta com loop de tool calling.

    Args:
        request: Pergunta do usuário + usuario_id

    Returns:
        QueryResponse com resposta sintetizada, fragmentos encontrados e ferramentas usadas
    """
    try:
        client = OpenAIClient()
    except OpenAIClientError as e:
        logger.error(f"❌ Falha ao inicializar LLM client: {e}")
        return QueryResponse(
            resposta="Desculpe, o serviço de IA não está disponível no momento.",
        )

    tools = _select_tools(request.pergunta)
    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": request.pergunta},
    ]

    fragmentos_coletados: List[Dict[str, Any]] = []
    ferramentas_usadas: List[str] = []

    for rodada in range(MAX_ROUNDS):
        logger.info(f"🤖 Query agent — rodada {rodada + 1}/{MAX_ROUNDS}")

        # Forçar síntese na última rodada
        if rodada == MAX_ROUNDS - 1:
            messages.append({
                "role": "system",
                "content": (
                    "Esta é sua última oportunidade. "
                    "Sintetize uma resposta final com base nos dados coletados até agora. "
                    "NÃO chame mais ferramentas."
                ),
            })

        try:
            choice = client.chat_with_tools(messages, tools if rodada < MAX_ROUNDS - 1 else [])
        except OpenAIClientError as e:
            logger.error(f"❌ LLM error na rodada {rodada + 1}: {e}")
            return QueryResponse(
                resposta="Desculpe, ocorreu um erro ao processar sua pergunta.",
                fragmentos=fragmentos_coletados,
                ferramentas_usadas=ferramentas_usadas,
            )

        finish_reason = choice.finish_reason
        message = choice.message

        # Adicionar resposta do assistente ao histórico
        messages.append(message)

        if finish_reason == "stop":
            resposta = message.content or ""
            logger.info(f"✅ Query agent finalizado após {rodada + 1} rodada(s)")
            return QueryResponse(
                resposta=resposta,
                fragmentos=fragmentos_coletados,
                ferramentas_usadas=ferramentas_usadas,
            )

        if finish_reason == "tool_calls" and message.tool_calls:
            chamadas_esta_rodada: set = set()  # Deduplicação por (nome, args)
            calls_executadas = 0

            for tool_call in message.tool_calls:
                nome = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                # Cap de tool calls por rodada
                if calls_executadas >= MAX_TOOL_CALLS_PER_ROUND:
                    logger.warning(
                        f"⚠️  Cap de {MAX_TOOL_CALLS_PER_ROUND} tool calls atingido na rodada "
                        f"{rodada + 1}. Ignorando: {nome}({args})"
                    )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"ignorado": "cap de chamadas por rodada atingido"}, ensure_ascii=False),
                    })
                    continue

                # Deduplicação: ignorar (nome, args) já chamados nesta rodada
                chave = (nome, json.dumps(args, sort_keys=True))
                if chave in chamadas_esta_rodada:
                    logger.warning(f"⚠️  Chamada duplicada ignorada: {nome}({args})")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps({"ignorado": "chamada duplicada nesta rodada"}, ensure_ascii=False),
                    })
                    continue

                chamadas_esta_rodada.add(chave)
                calls_executadas += 1

                if nome not in ferramentas_usadas:
                    ferramentas_usadas.append(nome)

                try:
                    resultado = dispatch(nome, args, request.usuario_id)
                except M6RegistryError as e:
                    resultado = {"erro": str(e)}
                    logger.warning(f"⚠️  Tool dispatch error: {e}")

                # Log resultado vazio para facilitar debug
                if isinstance(resultado, list) and len(resultado) == 0:
                    logger.warning(f"⚠️  {nome}({args}) → 0 resultados")
                elif isinstance(resultado, dict) and resultado.get("total_unicos") == 0:
                    logger.warning(f"⚠️  {nome}({args}) → total_unicos=0")
                else:
                    n = len(resultado) if isinstance(resultado, list) else "-"
                    logger.info(f"✅ {nome}({args}) → {n} resultado(s)")

                # Coletar fragmentos retornados (listas de dicts com 'resumo')
                if isinstance(resultado, list):
                    for item in resultado:
                        if isinstance(item, dict) and "resumo" in item:
                            fragmentos_coletados.append(item)

                # Truncar resultado para não explodir o contexto
                resultado_json = json.dumps(resultado, ensure_ascii=False, default=str)
                if len(resultado_json) > MAX_TOOL_RESULT_CHARS:
                    resultado_json = resultado_json[:MAX_TOOL_RESULT_CHARS] + "... [truncado]"
                    logger.warning(f"⚠️  Resultado de '{nome}' truncado para {MAX_TOOL_RESULT_CHARS} chars")

                # Adicionar resultado da tool ao histórico
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": resultado_json,
                })

            continue

        # Outro finish_reason (ex: length) — usar o conteúdo disponível
        resposta = message.content or "Não foi possível gerar uma resposta."
        logger.warning(f"⚠️  Query agent terminou com finish_reason='{finish_reason}'")
        return QueryResponse(
            resposta=resposta,
            fragmentos=fragmentos_coletados,
            ferramentas_usadas=ferramentas_usadas,
        )

    # Fallback se o loop terminar sem retornar
    return QueryResponse(
        resposta="Não foi possível sintetizar uma resposta após o número máximo de tentativas.",
        fragmentos=fragmentos_coletados,
        ferramentas_usadas=ferramentas_usadas,
    )
