"""
Prompt builder for Módulo 4 batch processing.

Responsável por:
1. Carregar perfil do usuário do user_profile.yaml
2. Construir system prompt com instruções de extração
3. Construir user message com lote de transcrições em JSON
"""

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from utils import setup_logger

logger = setup_logger(__name__)


class PromptBuilderError(Exception):
    pass


class PromptBuilder:

    def __init__(self, user_profile_path: str = None):
        if user_profile_path is None:
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
        usuario = self.user_profile.get("usuario", {})
        nome = usuario.get("nome", "Usuário")
        ocupacao = usuario.get("ocupacao", "")

        projetos_str = self._format_projetos()
        contextos_str = self._format_contextos()
        entidade_tipos_str = self._format_entidade_tipos()

        return f"""Você é um assistente especializado em extrair informações ricas e detalhadas de transcrições de áudio do sistema Jarvis.

# PERFIL DO USUÁRIO
- Nome: {nome}
- Ocupação: {ocupacao}

# PROJETOS ATIVOS
{projetos_str}

# CONTEXTOS E EXEMPLOS DE TÓPICOS
Os tópicos abaixo são exemplos — você deve criar tópicos novos livremente se o conteúdo não se encaixar nos exemplos.
{contextos_str}

# TAREFA
Você receberá um JSON com um array de transcrições de áudio. Para cada transcrição, extraia:

## 1. Resumo
- 1 a 3 frases capturando a essência completa
- Seja específico: mencione nomes, projetos, tecnologias se aparecerem
- Não generalize ("falou sobre trabalho") — detalhe ("discutiu bug de autenticação no Jarvis com token expirado")

## 2. Importance Score (0.00 a 1.00)
- 0.00–0.24: Trivial — saudações, ruído, frases sem conteúdo ("tá", "ah é", "ok")
- 0.25–0.49: Relevante — informação cotidiana com algum valor
- 0.50–0.74: Importante — decisões, planos, aprendizados, problemas
- 0.75–1.00: Crítico — decisões estratégicas, insights únicos, tarefas urgentes, descobertas

## 3. Tópicos
- Formato hierárquico: "Categoria > Subcategoria > Detalhe"
- Crie tópicos novos livremente se o conteúdo exigir — não se limite aos exemplos
- Use quantos tópicos forem necessários para cobrir o conteúdo
- Seja específico: prefira "Trabalho > Jarvis > Bug > Autenticação" a "Trabalho"

## 4. Entidades
Extraia TODAS as entidades mencionadas. Para cada uma:
- **nome**: Nome exato como aparece na transcrição
- **tipo**: Um dos tipos abaixo (ou outro se nenhum se encaixar):
{entidade_tipos_str}
- **contexto**: Trecho literal da transcrição onde foi mencionada (máx 100 chars)

## 5. Itens de Ação (action_items)
- Liste tarefas ou ações concretas mencionadas: "preciso fazer X", "tem que resolver Y", "lembrar de Z"
- Array de strings, pode ser vazio

## 6. Metadados Extras
- **sentimento**: "positivo", "negativo", "neutro", "misto"
- **tem_decisao**: true se uma decisão foi tomada
- **tem_pergunta**: true se há uma pergunta em aberto

# INSTRUÇÕES CRÍTICAS
- Responda APENAS com JSON válido, sem texto antes ou depois
- Preserve a ordem exata do array de entrada (idx começa em 0)
- Para transcrições triviais (score < 0.25): resumo curto, tópicos e entidades podem ser vazios
- Idioma de saída: português (mesmo que a transcrição tenha palavras em inglês)
- Seja rico em detalhes — dados vagos têm pouco valor como memória

# FORMATO DE SAÍDA

{{
  "resultados": [
    {{
      "idx": 0,
      "resumo": "string descritiva de 1-3 frases com detalhes específicos",
      "importance_score": 0.75,
      "topicos": [
        "Trabalho > Jarvis > Backend > Autenticação",
        "Trabalho > Infraestrutura > Docker"
      ],
      "entidades": [
        {{
          "nome": "Jarvis",
          "tipo": "projeto",
          "contexto": "trecho literal onde foi mencionada"
        }}
      ],
      "action_items": ["Resolver bug de token expirado no Jarvis"],
      "sentimento": "neutro",
      "tem_decisao": false,
      "tem_pergunta": false
    }}
  ]
}}"""

    def build_user_message(self, transcricoes: List[Dict[str, Any]]) -> str:
        batch = []
        for i, t in enumerate(transcricoes):
            item = {
                "idx": i,
                "id": t.get("id"),
                "texto": t.get("texto"),
            }
            # Enrich with metadata if available
            if t.get("fonte"):
                item["fonte"] = t["fonte"]
            if t.get("criado_em"):
                criado_em = t["criado_em"]
                if hasattr(criado_em, "strftime"):
                    item["hora"] = criado_em.strftime("%H:%M")
                    item["dia_semana"] = self._dia_semana(criado_em.weekday())
                else:
                    item["hora"] = str(criado_em)
            batch.append(item)

        return json.dumps(
            {"quantidade": len(batch), "transcricoes": batch},
            ensure_ascii=False,
            indent=2
        )

    def _format_projetos(self) -> str:
        projetos = self.user_profile.get("projetos_ativos", [])
        if not projetos:
            return "Nenhum projeto definido."
        lines = []
        for p in projetos:
            techs = ", ".join(p.get("tecnologias", []))
            lines.append(f"- **{p['nome']}**: {p.get('descricao', '')}")
            if techs:
                lines.append(f"  Tecnologias: {techs}")
        return "\n".join(lines)

    def _format_contextos(self) -> str:
        contextos = self.user_profile.get("contextos", {})
        if not contextos:
            return "Nenhum contexto definido."
        lines = []
        for ctx_name, ctx_data in contextos.items():
            lines.append(f"\n**{ctx_name.capitalize()}**: {ctx_data.get('descricao', '')}")
            exemplos = ctx_data.get("exemplos_topicos", [])
            if exemplos:
                lines.append("  Exemplos: " + " | ".join(exemplos[:4]))
        return "\n".join(lines)

    def _format_entidade_tipos(self) -> str:
        tipos = self.user_profile.get("entidade_tipos", [])
        if not tipos:
            return "  pessoa, empresa, projeto, lugar, conceito, ferramenta, evento, tarefa, decisao, ideia, produto"
        return "\n".join(f"  - {t}" for t in tipos)

    @staticmethod
    def _dia_semana(weekday: int) -> str:
        dias = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
        return dias[weekday] if 0 <= weekday <= 6 else ""


def build_full_prompt(
    transcricoes: List[Dict[str, Any]],
    user_profile_path: str = None
) -> tuple:
    builder = PromptBuilder(user_profile_path)
    system_prompt = builder.build_system_prompt()
    user_message = builder.build_user_message(transcricoes)
    return system_prompt, user_message
