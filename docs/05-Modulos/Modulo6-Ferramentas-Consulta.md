---
title: Módulo 6 - Ferramentas de Consulta
description: Catálogo de todas as ferramentas de busca disponíveis no query agent do M6, com exemplos de perguntas suportadas e lacunas identificadas
tags: [modulo6, consulta, ferramentas, tool-calling, query, catalogo]
aliases:
  - Ferramentas de Consulta
  - Catálogo M6
---

# 🛠️ Módulo 6 — Ferramentas de Consulta

Catálogo de todas as ferramentas registradas no query agent (`modulo6_consulta/tools/`).
Cada ferramenta é um `@register_tool` que o LLM pode invocar via tool calling.

> **Como adicionar uma nova ferramenta:** crie um arquivo em `modulo6_consulta/tools/`, registre com `@register_tool`, e documente aqui.

---

## Ferramentas Implementadas

| Ferramenta              | Parâmetros                                                                          | O que faz                                                                                      |
| ----------------------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `buscar_por_entidade`   | `nome: str`                                                                         | Busca fragmentos vinculados a entidades (pessoa, empresa, projeto, lugar) por nome (ILIKE)     |
| `buscar_por_topico`     | `topico: str`                                                                       | Busca fragmentos vinculados a tópicos pelo caminho hierárquico (ILIKE)                         |
| `listar_topicos`        | —                                                                                   | Lista os 30 tópicos mais frequentes do usuário, ordenados por frequência                       |
| `buscar_por_periodo`    | `inicio: str (ISO 8601)` · `fim: str (ISO 8601)`                                    | Busca fragmentos por intervalo de tempo. O LLM converte "esta semana", "ontem" etc. para ISO   |
| `buscar_texto_livre`    | `termo: str`                                                                        | ILIKE no campo `resumo`. Fallback genérico. Ordenado por `importance_score DESC`               |
| `listar_action_items`   | `status: "pendente" \| "concluido" \| "cancelado"`                                  | Lista tarefas extraídas pelo M4 filtradas por status, com resumo do fragmento de origem        |
| `buscar_por_sentimento` | `sentimento: "positivo" \| "negativo" \| "neutro" \| "misto"`                       | Busca fragmentos pelo sentimento predominante. Ordenado por `importance_score DESC`            |
| `buscar_por_importancia`| `minimo: float` · `inicio?: str (ISO)` · `fim?: str (ISO)`                          | Fragmentos com `importance_score >= minimo`. Aceita período opcional                           |
| `buscar_topico_periodo` | `topico: str` · `inicio: str (ISO 8601)` · `fim: str (ISO 8601)`                   | Busca combinada: tópico + intervalo de datas na mesma query                                    |
| `buscar_transcricao`    | `termo: str`                                                                        | ILIKE no texto bruto da transcrição (antes do M4). Retorna trecho de até 300 chars             |
| `contar_mencoes`        | `termo: str`                                                                        | COUNT simples via ILIKE no resumo. Retorna `{ termo, total_mencoes }`                          |
| `contar_ocorrencias`    | `termo: str` · `inicio?: str (ISO)` · `fim?: str (ISO)`                             | COUNT robusto via 3 fontes (entidade + tópico + texto), deduplificado por ID de fragmento      |
| `resumo_estatistico`    | `inicio?: str (ISO)` · `fim?: str (ISO)`                                            | Agrega: total, score médio/máximo, distribuição por sentimento, top 5 tópicos do período       |

---

## Retorno por Ferramenta

| Ferramenta              | Campos retornados                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------ |
| `buscar_por_entidade`   | `id` · `resumo` · `criado_em` · `entidade_nome` · `entidade_tipo` · `contexto`             |
| `buscar_por_topico`     | `id` · `resumo` · `criado_em` · `sentimento` · `topico_caminho`                            |
| `listar_topicos`        | `id` · `caminho` · `frequencia` · `ultima_mencao_em`                                       |
| `buscar_por_periodo`    | `id` · `resumo` · `criado_em` · `sentimento` · `importance_score`                          |
| `buscar_texto_livre`    | `id` · `resumo` · `criado_em` · `sentimento` · `importance_score`                          |
| `listar_action_items`   | `id` · `texto` · `status` · `criado_em` · `fragmento_resumo` · `fragmento_criado_em`       |
| `buscar_por_sentimento` | `id` · `resumo` · `criado_em` · `sentimento` · `importance_score`                          |
| `buscar_por_importancia`| `id` · `resumo` · `criado_em` · `sentimento` · `importance_score`                          |
| `buscar_topico_periodo` | `id` · `resumo` · `criado_em` · `sentimento` · `importance_score` · `topico_caminho`       |
| `buscar_transcricao`    | `id` · `resumo` · `criado_em` · `importance_score` · `trecho_transcricao` (máx 300 chars)  |
| `contar_mencoes`        | `termo` · `total_mencoes`                                                                                                     |
| `contar_ocorrencias`    | `termo` · `total_unicos` · `por_entidade` · `por_topico` · `por_texto` · `periodo?`                                           |
| `resumo_estatistico`    | `total_fragmentos` · `score_medio` · `score_maximo` · `por_sentimento` · `top_topicos`                                        |

---

## Exemplos de Perguntas por Ferramenta

| Ferramenta              | Exemplos de perguntas                                                                                                   |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `buscar_por_entidade`   | "O que eu falei sobre o João?" · "Memórias que mencionam a Anthropic" · "O que discuti sobre o Cerebro?"                |
| `buscar_por_topico`     | "O que eu falei sobre saúde?" · "Memórias sobre Trabalho > Reuniões" · "O que tenho registrado de finanças?"            |
| `listar_topicos`        | "Sobre o que eu mais falo?" · "Quais são meus tópicos principais?" · "O que domina minhas conversas?"                   |
| `buscar_por_periodo`    | "O que eu falei esta semana?" · "Memórias de ontem" · "O que registrei em março?" · "O que houve na quarta?"            |
| `buscar_texto_livre`    | "Busca por 'reunião de sprint'" · "O que eu disse sobre 'comprar apartamento'?" · _(termo genérico qualquer)_           |
| `listar_action_items`   | "Quais são minhas tarefas pendentes?" · "O que eu já concluí?" · "O que eu preciso fazer?"                              |
| `buscar_por_sentimento` | "O que me deixou animado?" · "Momentos de frustração desta semana" · "Memórias negativas do mês"                        |
| `buscar_por_importancia`| "O que foi mais importante essa semana?" · "Minhas memórias críticas" · "O que teve score acima de 0.8?"                |
| `buscar_topico_periodo` | "O que falei sobre saúde em fevereiro?" · "Reuniões desta semana" · "Assuntos de trabalho no mês passado"               |
| `buscar_transcricao`    | "Eu disse exatamente a palavra 'deploy'" · "Busca pela frase 'preciso ligar'" · _(termos exatos não no resumo)_         |
| `contar_mencoes`        | "Quantas vezes falei sobre o Cerebro?" · "Com que frequência menciono reunião?"                                         |
| `contar_ocorrencias`    | "Quantos cigarros fumei essa semana?" · "Quantas reuniões tive em março?" · "Quantas vezes citei o João este mês?"      |
| `resumo_estatistico`    | "Me dá um resumo da semana" · "Como foi meu balanço de março?" · "Qual meu score médio de importância este mês?"        |

---

## Lacunas Identificadas

Consultas que o sistema **ainda não suporta** nativamente. Candidatas a novas ferramentas:

| Tipo de Consulta      | Exemplo                                                | Ferramenta Necessária      |
| --------------------- | ------------------------------------------------------ | -------------------------- |
| Relacionamentos       | "O que João e o projeto Cerebro têm em comum?"         | `buscar_relacao_entidades` |
| Fragmentos sem tópico | "O que ainda não foi categorizado?"                    | `buscar_sem_topico`        |
| Recorrência           | "Sobre o que eu falo toda semana?"                     | `buscar_recorrente`        |

---

## Contagem Robusta — `contar_ocorrencias` vs `contar_mencoes`

Existem duas funções de contagem com propósitos diferentes:

| | `contar_mencoes` | `contar_ocorrencias` |
| --- | --- | --- |
| **Fonte** | Apenas `resumo` (texto livre) | Entidade + Tópico + Resumo |
| **Deduplicação** | Não necessária (fonte única) | Sim — UNION por `fragmento_id` |
| **Precisão** | Depende do wording do resumo | Alta — usa dados estruturados |
| **Cobertura** | Média — pode perder variações | Alta — captura mesmo sem nome exato |
| **Custo SQL** | Baixo | Médio (3 queries + UNION) |
| **Quando usar** | Buscas genéricas e rápidas | Contagens que precisam ser confiáveis |

### Por que `contar_ocorrencias` é mais confiável?

O M4 pode **não extrair a entidade** em situações como:
- Você disse "fumei mais um" sem mencionar "cigarro"
- Variações fonéticas/coloquiais que o Whisper transcreveu diferente
- Fragmento com `importance_score` baixo foi `skipped` pelo M4

Nesse caso, o termo só aparece no `resumo` (fonte 3), e seria perdido pela contagem via entidade.

A função busca pelas **3 fontes independentemente** e faz `UNION` dos IDs para garantir que cada fragmento seja contado **no máximo uma vez**, mesmo que apareça nas 3 fontes simultaneamente.

### Interpretando o retorno

```json
{
  "termo": "cigarro",
  "total_unicos": 14,
  "por_entidade": 11,
  "por_topico": 10,
  "por_texto": 13
}
```

- `total_unicos: 14` → contagem final a usar na resposta
- `por_entidade < por_texto` → o M4 não extraiu a entidade em ~3 fragmentos (cobertura 78%)
- `por_topico ≈ por_entidade` → tópico e entidade estão bem alinhados

---

## Notas de Comportamento do Agente

- **MAX_ROUNDS:** configurado em `settings.modulo6.max_rounds` — o agente tem no máximo N rodadas de tool calling antes de ser forçado a sintetizar
- **Coleta de fragmentos:** o agente coleta automaticamente todos os resultados com campo `resumo` como `fragmentos` na resposta
- **Fallback:** se o loop esgotar sem `finish_reason == "stop"`, retorna a mensagem de fallback padrão
- **Idioma:** o system prompt força resposta sempre em PT-BR

---

## Relacionado

- [[Modulo6-Consulta|Módulo 6 — Visão Geral]]
- [[Modulo5-Schema-SQL|Módulo 5 — Schema SQL]] _(tabelas consultadas pelas ferramentas)_
- [[Modulo4-Processamento-IA|Módulo 4 — Processamento IA]] _(gera os dados que as ferramentas buscam)_
