"""
LLM Client wrapper — compatível com OpenAI, Groq, e qualquer API OpenAI-compatible.

Groq usa a mesma interface da OpenAI SDK, só muda base_url e api_key.
Suporta: Groq, OpenAI, Anthropic (via compatible endpoint), Google Vertex, etc.
"""

import time
from typing import Tuple
from openai import OpenAI, RateLimitError, APIError, AuthenticationError
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)


class OpenAIClientError(Exception):
    pass


class OpenAIClient:
    """
    Wrapper OpenAI-compatible com retry exponencial.

    Funciona com:
    - Groq:      base_url=https://api.groq.com/openai/v1
    - OpenAI:    base_url=None (padrão)
    - Qualquer API compatível com a interface OpenAI
    """

    def __init__(self):
        if not settings.llm.api_key:
            raise OpenAIClientError("LLM_API_KEY não configurada no .env")

        # base_url=None usa o default da OpenAI
        base_url = settings.llm.base_url or None

        self.client = OpenAI(
            api_key=settings.llm.api_key,
            base_url=base_url,
        )
        self.model = settings.llm.model
        self.provider = settings.llm.provider
        self.max_retries = settings.modulo4.max_retries

        logger.info(f"✅ LLM Client inicializado: provider={self.provider}, model={self.model}")

    def call_with_retry(self, system_prompt: str, user_message: str) -> Tuple[str, int, int]:
        """
        Chama a API com retry exponencial (1s, 2s, 4s).

        Returns:
            (response_text, input_tokens, output_tokens)

        Raises:
            OpenAIClientError: se todas as tentativas falharem
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0,
                )

                response_text = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                logger.debug(
                    f"✅ {self.provider} call OK | "
                    f"input={input_tokens} output={output_tokens} tokens"
                )
                return response_text, input_tokens, output_tokens

            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(
                    f"⚠️  Rate limit {self.provider} "
                    f"(tentativa {attempt + 1}/{self.max_retries}). "
                    f"Aguardando {wait_time}s..."
                )
                time.sleep(wait_time)

            except APIError as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(
                    f"⚠️  API error {self.provider} "
                    f"(tentativa {attempt + 1}/{self.max_retries}): {e}. "
                    f"Aguardando {wait_time}s..."
                )
                time.sleep(wait_time)

            except AuthenticationError as e:
                raise OpenAIClientError(f"Autenticação falhou ({self.provider}): {e}")

            except Exception as e:
                raise OpenAIClientError(f"Erro inesperado ({self.provider}): {e}")

        raise OpenAIClientError(
            f"Falhou após {self.max_retries} tentativas ({self.provider}). "
            f"Último erro: {last_error}"
        )

    def chat_with_tools(self, messages: list, tools: list) -> object:
        """
        Faz uma chamada chat completion com tool calling (function calling).

        Args:
            messages: Lista de mensagens no formato OpenAI [{"role": ..., "content": ...}]
            tools: Lista de tools no formato OpenAI (get_all_tools())

        Returns:
            Objeto choice completo (com .message, .finish_reason, .message.tool_calls)

        Raises:
            OpenAIClientError: se todas as tentativas falharem
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                    temperature=0,
                )
                choice = response.choices[0]
                logger.debug(
                    f"✅ {self.provider} tool-call OK | "
                    f"finish_reason={choice.finish_reason} | "
                    f"tokens={response.usage.prompt_tokens}+{response.usage.completion_tokens}"
                )
                return choice

            except RateLimitError as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(
                    f"⚠️  Rate limit {self.provider} "
                    f"(tentativa {attempt + 1}/{self.max_retries}). "
                    f"Aguardando {wait_time}s..."
                )
                time.sleep(wait_time)

            except APIError as e:
                last_error = e
                wait_time = 2 ** attempt
                logger.warning(
                    f"⚠️  API error {self.provider} "
                    f"(tentativa {attempt + 1}/{self.max_retries}): {e}. "
                    f"Aguardando {wait_time}s..."
                )
                time.sleep(wait_time)

            except AuthenticationError as e:
                raise OpenAIClientError(f"Autenticação falhou ({self.provider}): {e}")

            except Exception as e:
                raise OpenAIClientError(f"Erro inesperado ({self.provider}): {e}")

        raise OpenAIClientError(
            f"chat_with_tools falhou após {self.max_retries} tentativas ({self.provider}). "
            f"Último erro: {last_error}"
        )

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calcula custo usando preços configurados no .env (Groq = 0.0)."""
        input_cost = (input_tokens / 1_000_000) * settings.llm.cost_input_per_1m
        output_cost = (output_tokens / 1_000_000) * settings.llm.cost_output_per_1m
        return input_cost + output_cost
