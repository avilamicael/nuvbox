#!/usr/bin/env python3
"""
Test script for Module 4 - Dry run without actual OpenAI API calls.

Usage:
    python scripts/test_modulo4_dryrun.py

This script:
1. Loads the user profile
2. Builds system and user prompts
3. Creates sample transcriptions for testing
4. Prints the prompts for inspection
5. Parses a mock response to validate the parser
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from modulo4_processamento.prompt_builder import PromptBuilder
from modulo4_processamento.response_parser import ResponseParser


def main():
    print("=" * 80)
    print("🧪 MÓDULO 4 — DRY RUN TEST")
    print("=" * 80)
    print()

    # 1. Load user profile
    print("1️⃣  Loading user profile...")
    try:
        builder = PromptBuilder()
        print("   ✅ User profile loaded successfully")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return 1

    print()

    # 2. Build system prompt
    print("2️⃣  Building system prompt...")
    system_prompt = builder.build_system_prompt()
    system_prompt_lines = system_prompt.split("\n")
    print(f"   ✅ System prompt ({len(system_prompt)} chars):")
    print("   " + "-" * 76)
    for line in system_prompt_lines[:15]:  # First 15 lines
        print(f"   {line}")
    if len(system_prompt_lines) > 15:
        remaining = len(system_prompt_lines) - 15
        print(f"   ... ({remaining} more lines)")
    print("   " + "-" * 76)

    print()

    # 3. Create sample transcriptions
    print("3️⃣  Creating sample transcriptions...")
    sample_transcricoes = [
        {
            "id": 1001,
            "texto": "Hoje tive uma reunião com o time do Cerebro para discutir os bugs no PostgreSQL. "
                     "Precisamos refatorar o módulo de armazenamento antes do deploy na próxima semana."
        },
        {
            "id": 1002,
            "texto": "Fui ao médico hoje, tenho que melhorar a minha alimentação e fazer mais exercício. "
                     "Vou começar a ir na academia de novo."
        },
        {
            "id": 1003,
            "texto": "Aprendi um novo conceito de machine learning chamado prompt engineering. "
                     "Vou estudar mais sobre transformers no fim de semana."
        },
    ]

    user_message = builder.build_user_message(sample_transcricoes)
    print(f"   ✅ Built user message with {len(sample_transcricoes)} transcriptions")
    print()
    print("   User message (JSON):")
    print("   " + "-" * 76)
    for line in user_message.split("\n")[:20]:
        print(f"   {line}")
    print("   " + "-" * 76)

    print()

    # 4. Parse mock response
    print("4️⃣  Testing response parser with mock output...")

    mock_response = {
        "resultados": [
            {
                "idx": 0,
                "resumo": "Reunião com time para discutir bugs no PostgreSQL antes do deploy.",
                "importance_score": 0.85,
                "topicos": ["Trabalho > Cerebro > Bugs", "Trabalho > Cerebro > Deploy"],
                "entidades": [
                    {
                        "nome": "PostgreSQL",
                        "tipo": "ferramenta",
                        "contexto": "bugs no PostgreSQL"
                    },
                    {
                        "nome": "Cerebro",
                        "tipo": "projeto",
                        "contexto": "reunião com o time do Cerebro"
                    }
                ]
            },
            {
                "idx": 1,
                "resumo": "Visita ao médico com recomendações de exercício e melhor alimentação.",
                "importance_score": 0.35,
                "topicos": ["Pessoal > Saúde"],
                "entidades": [
                    {
                        "nome": "Academia",
                        "tipo": "lugar",
                        "contexto": "vai voltar na academia"
                    }
                ]
            },
            {
                "idx": 2,
                "resumo": "Aprendizado sobre prompt engineering e transformers em machine learning.",
                "importance_score": 0.55,
                "topicos": ["Estudos > Machine Learning > Transformers"],
                "entidades": [
                    {
                        "nome": "Transformers",
                        "tipo": "conceito",
                        "contexto": "novo conceito de transformers"
                    },
                    {
                        "nome": "Prompt Engineering",
                        "tipo": "conceito",
                        "contexto": "conceito de prompt engineering"
                    }
                ]
            }
        ]
    }

    mock_response_text = json.dumps(mock_response, ensure_ascii=False, indent=2)

    try:
        parsed = ResponseParser.parse_response(mock_response_text, len(sample_transcricoes))
        print("   ✅ Response parsed successfully (Level 1: Direct json.loads)")
        print()
        print("   Parsed results:")
        for result in parsed["resultados"]:
            normalized = ResponseParser.normalize_result(result)
            print()
            print(f"   📝 Result {result['idx']}:")
            print(f"      Resumo: {normalized['resumo']}")
            print(f"      Importance: {normalized['importance_score']}")
            print(f"      Tópicos: {normalized['topicos']}")
            print(f"      Entidades: {len(normalized['entidades'])} encontradas")
            for ent in normalized['entidades']:
                print(f"        - {ent['nome']} ({ent['tipo']})")

    except Exception as e:
        print(f"   ❌ Parse error: {e}")
        return 1

    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Set OPENAI_API_KEY in .env")
    print("2. Set MODULO4_DRY_RUN=true in .env to test without DB insertion")
    print("3. Run: docker-compose up")
    print("4. Check logs for batch processing output")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
