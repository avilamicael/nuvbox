"""
Prompt builder for Módulo 4 batch processing.

Responsável por:
1. Carregar perfil do usuário do user_profile.yaml
2. Construir system prompt com instruções de extração
3. Construir user message com lote de transcrições em JSON
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from utils import setup_logger

logger = setup_logger(__name__)


class PromptBuilderError(Exception):
    """Base exception for prompt builder errors."""
    pass


class PromptBuilder:
    """
    Builds system and user prompts for GPT-4o mini batch processing.
    """

    def __init__(self, user_profile_path: str = None):
        """
        Initialize with user profile YAML.

        Args:
            user_profile_path: Path to user_profile.yaml
                              Defaults to modulo4_processamento/user_profile.yaml
        """
        if user_profile_path is None:
            # Assume this module is at backend/modulo4_processamento/
            user_profile_path = Path(__file__).parent / "user_profile.yaml"

        try:
            with open(user_profile_path, "r", encoding="utf-8") as f:
                self.user_profile = yaml.safe_load(f)
            logger.debug(f"✅ Loaded user profile from {user_profile_path}")
        except FileNotFoundError:
            raise PromptBuilderError(f"User profile not found: {user_profile_path}")
        except yaml.YAMLError as e:
            raise PromptBuilderError(f"Invalid YAML in user profile: {e}")

    def build_system_prompt(self) -> str:
        """
        Build the system prompt with extraction rules and user context.

        Returns:
            System prompt string in Portuguese
        """
        contextos = self._format_contextos()
        entidade_tipos = ", ".join(self.user_profile.get("entidade_tipos", []))

        return f"""Você é um assistente especializado em extração de informações de transcrições de áudio do sistema Jarvis.

# PERFIL DO USUÁRIO
- Nome: {self.user_profile.get('usuario', {}).get('nome', 'Usuário')}
- Idioma: {self.user_profile.get('usuario', {}).get('idioma', 'português')}

# CONTEXTOS DO USUÁRIO
{contextos}

# TAREFA
Você receberá um JSON com um array de transcrições. Para cada transcrição, você deve extrair:

1. **Resumo**: Uma ou duas frases capturando a essência
2. **Importance Score**: Número de 0.0 a 1.00
   - < 0.25: Descartado automaticamente
   - 0.25-0.50: Importante, armazenar
   - 0.50-0.75: Muito importante
   - 0.75-1.00: Crítico (relacionado a vida/trabalho principal)

3. **Tópicos**: Array de caminhos hierárquicos
   - Formato: "Categoria > Subcategoria > Tópico"
   - Exemplos válidos: "Trabalho > Jarvis > Bugs", "Pessoal > Saúde > Exercício"
   - Máximo 3 tópicos por transcrição

4. **Entidades**: Array de objetos com:
   - nome: Nome da entidade (pessoa, empresa, projeto, lugar, conceito)
   - tipo: Um de: {entidade_tipos}
   - contexto: Trecho onde foi mencionada

# INSTRUÇÕES CRÍTICAS

- Sempre responda em JSON válido
- Preserve exactamente a ordem do array de entrada
- Use nome_normalizado com lowercase para deduplicação futura
- Se a transcrição for trivial, defina importance_score < 0.25
- Transcrições em português: extraia tópicos e entidades em português também
- Nunca adicione campos extras à resposta

# FORMATO DE SAÍDA

Responda com este JSON exatamente:
{{
  "resultados": [
    {{
      "idx": 0,
      "resumo": "string de 1-2 frases",
      "importance_score": 0.75,
      "topicos": ["Trabalho > Jarvis > Bugs"],
      "entidades": [
        {{
          "nome": "PostgreSQL",
          "tipo": "ferramenta",
          "contexto": "trecho onde foi mencionada"
        }}
      ]
    }}
  ]
}}

Responda APENAS com o JSON, sem explicações adicionais."""

    def build_user_message(
        self,
        transcricoes: List[Dict[str, Any]]
    ) -> str:
        """
        Build the user message with batch of transcriptions.

        Args:
            transcricoes: List of dicts with 'id' and 'texto' keys

        Returns:
            User message as JSON string
        """
        batch = [
            {
                "idx": i,
                "id": t.get("id"),
                "texto": t.get("texto")
            }
            for i, t in enumerate(transcricoes)
        ]

        user_msg = {
            "quantidade": len(batch),
            "transcricoes": batch
        }

        return json.dumps(user_msg, ensure_ascii=False, indent=2)

    def _format_contextos(self) -> str:
        """Format user contextos for inclusion in system prompt."""
        contextos = self.user_profile.get("contextos", {})
        if not contextos:
            return "Nenhum contexto definido."

        lines = []
        for ctx_name, ctx_data in contextos.items():
            descricao = ctx_data.get("descricao", "")
            palavras = ", ".join(ctx_data.get("palavras_chave", []))
            lines.append(f"- **{ctx_name.capitalize()}**: {descricao}")
            if palavras:
                lines.append(f"  Palavras-chave: {palavras}")

        return "\n".join(lines)


def build_full_prompt(
    transcricoes: List[Dict[str, Any]],
    user_profile_path: str = None
) -> tuple:
    """
    Convenience function to build both system and user prompts.

    Args:
        transcricoes: List of transcription dicts
        user_profile_path: Path to user profile YAML

    Returns:
        Tuple of (system_prompt, user_message)
    """
    builder = PromptBuilder(user_profile_path)
    system_prompt = builder.build_system_prompt()
    user_message = builder.build_user_message(transcricoes)
    return system_prompt, user_message
