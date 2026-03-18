"""
Query Agent — Módulo 6.

Recebe uma pergunta em linguagem natural e usa tool calling para buscar
no banco de dados do Jarvis, sintetizando uma resposta em PT-BR.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any

import modulo6_consulta.tools  # noqa: F401 — ativa todos os @register_tool
from modulo6_consulta.registry import get_all_tools, dispatch, M6RegistryError
from modulo4_processamento.openai_client import OpenAIClient, OpenAIClientError
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

MAX_ROUNDS = settings.modulo6.max_rounds

SYSTEM_PROMPT = """\
Você é o Jarvis, um assistente de segunda memória pessoal.
Você tem acesso às memórias do usuário através de ferramentas de busca no banco de dados.

Instruções:
- Responda SEMPRE em português brasileiro.
- Use as ferramentas disponíveis para buscar informações antes de responder.
- Se uma ferramenta não retornar resultados, tente outra abordagem ou informe que não há dados.
- Seja conciso e direto. Cite datas quando relevante.
- Nunca invente informações — use apenas o que as ferramentas retornarem.
- Se não encontrar nada relevante, diga claramente que não há memórias sobre esse assunto.
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

    tools = get_all_tools()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
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
            for tool_call in message.tool_calls:
                nome = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                if nome not in ferramentas_usadas:
                    ferramentas_usadas.append(nome)

                try:
                    resultado = dispatch(nome, args, request.usuario_id)
                except M6RegistryError as e:
                    resultado = {"erro": str(e)}
                    logger.warning(f"⚠️  Tool dispatch error: {e}")

                # Coletar fragmentos retornados (listas de dicts com 'resumo')
                if isinstance(resultado, list):
                    for item in resultado:
                        if isinstance(item, dict) and "resumo" in item:
                            fragmentos_coletados.append(item)

                # Adicionar resultado da tool ao histórico
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(resultado, ensure_ascii=False, default=str),
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
