---
title: Módulo 6 - Interface de Consulta
description: Query engine com tool calling, registry extensível e adaptadores de canal (web, WhatsApp, Alexa)
tags: [modulo6, consulta, query, tool-calling, channels, registry, cerebro]
aliases:
  - Módulo 6
  - Interface de Consulta
  - Query Interface
---

# 🔍 Módulo 6 — Interface de Consulta

O Módulo 6 é a camada que permite ao usuário **recuperar memória** do sistema Jarvis via linguagem natural. Ele conecta os dados estruturados do [[Modulo5-Estruturado|M5]] e os embeddings do [[Modulo7-Semantico|M7]] a qualquer interface de entrada — web, WhatsApp, Alexa, ou o que vier depois.

**Dois princípios de design:**
1. **Canal-agnóstico**: o core não sabe se a pergunta veio do WhatsApp ou da Alexa
2. **Ferramentas extensíveis**: adicionar uma nova capacidade de busca não exige tocar no agente

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                     CANAIS (Adapters)                       │
│                                                             │
│   Web Chat ──┐                                              │
│   WhatsApp ──┤──► QueryRequest(pergunta, usuario_id)        │
│   Alexa    ──┘                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   QUERY AGENT (Core)                        │
│                                                             │
│   1. Recebe QueryRequest                                    │
│   2. Chama get_all_tools() → schemas das ferramentas        │
│   3. Manda pergunta + tools para LLM (OpenAI)              │
│   4. LLM responde: "chamar buscar_por_topico(..."           │
│   5. registry.dispatch(nome, args) → executa a query        │
│   6. Manda resultado de volta para LLM                      │
│   7. LLM sintetiza resposta final em PT-BR                  │
│   8. Retorna QueryResponse(resposta, fragmentos)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  TOOL REGISTRY                              │
│                                                             │
│   _schemas    → JSONs no formato OpenAI function calling    │
│   _functions  → funções Python reais                        │
│                                                             │
│   get_all_tools()       → lista de schemas                  │
│   dispatch(nome, args)  → executa a função pelo nome        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  TOOLS (Ferramentas)                        │
│                                                             │
│   topicos.py    buscar_por_topico, listar_topicos           │
│   entidades.py  buscar_por_entidade                         │
│   temporal.py   buscar_por_periodo                          │
│   tarefas.py    listar_action_items                         │
│   texto.py      buscar_texto_livre                          │
│   semantica.py  buscar_semanticamente  ← ativado no M7     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    PostgreSQL (M5 schema)
```

---

## 📁 Estrutura de Arquivos

```
backend/modulo6_consulta/
├── __init__.py               # Exports: QueryAgent, QueryRequest, QueryResponse
├── registry.py               # @register_tool, get_all_tools(), dispatch()
├── query_agent.py            # Agentic loop: pergunta → LLM+tools → resposta
├── tools/
│   ├── __init__.py           # Importa todos os módulos para ativar o @register_tool
│   ├── topicos.py            # buscar_por_topico, listar_topicos
│   ├── entidades.py          # buscar_por_entidade
│   ├── temporal.py           # buscar_por_periodo
│   ├── tarefas.py            # listar_action_items
│   ├── texto.py              # buscar_texto_livre (ILIKE em resumo)
│   └── semantica.py          # buscar_semanticamente (pgvector, ativado no M7)
└── channels/
    ├── __init__.py
    ├── web.py                # FastAPI: POST /consulta
    ├── whatsapp.py           # Webhook Twilio/Meta (futuro)
    └── alexa.py              # Skill Lambda handler (futuro)
```

---

## 🔧 registry.py — Esboço

O registry mantém dois dicionários internos e expõe três operações públicas.

**Estrutura interna:**
```python
_schemas    = {}   # nome → JSON schema (formato OpenAI function calling)
_functions  = {}   # nome → callable Python

def register_tool(name, description, parameters):
    # Decorator que popula _schemas e _functions
    # Uso: @register_tool(name="...", description="...", parameters={...})

def get_all_tools() -> list:
    # Retorna lista de todos os _schemas
    # Entra no campo "tools=" da chamada OpenAI

def dispatch(nome: str, args: dict, usuario_id: int) -> any:
    # Executa _functions[nome](**args, usuario_id=usuario_id)
    # Levanta ToolNotFoundError se nome não existe
```

**Por que dois dicionários separados?**
— O schema vai para a OpenAI (JSON puro, sem código). A função fica em Python. Separar evita serializar código acidentalmente e permite testar schemas independentemente das queries.

**Como uma ferramenta é registrada:**
```python
# tools/topicos.py
@register_tool(
    name="buscar_por_topico",
    description="Busca fragmentos de memória relacionados a um tópico específico",
    parameters={
        "topico": {
            "type": "string",
            "description": "O tópico a buscar, ex: 'Trabalho > Jarvis'"
        }
    }
)
def buscar_por_topico(topico: str, usuario_id: int) -> list[dict]:
    # SELECT fragmentos JOIN fragmento_topico JOIN topicos
    # WHERE topicos.caminho ILIKE %topico% AND usuario_id = ?
    ...
```

---

## 🤖 query_agent.py — Esboço

O agente executa um **agentic loop** de no máximo `MAX_ROUNDS` rodadas (default: 5).

**Contrato público:**
```python
class QueryRequest:
    pergunta: str
    usuario_id: int

class QueryResponse:
    resposta: str           # Resposta em linguagem natural para o usuário
    fragmentos: list        # Fragmentos usados (para web mostrar as fontes)
    ferramentas_usadas: list  # Quais tools foram chamadas (para debug/log)

def run(request: QueryRequest) -> QueryResponse:
    ...
```

**Fluxo interno do loop:**
```
Rodada 1 — LLM recebe a pergunta + schemas de todas as ferramentas
  Se LLM retorna texto → resposta final (fim)
  Se LLM retorna tool_call → vai para Rodada 2

Rodada 2 — Execução da ferramenta
  registry.dispatch(nome, args, usuario_id)
  Resultado adicionado ao histórico de mensagens como "tool result"
  Vai para Rodada 3

Rodada 3 — LLM recebe o resultado da ferramenta
  Se LLM retorna texto → resposta final (fim)
  Se LLM pede outra ferramenta → continua o loop
  ...

Rodada MAX — Forçar síntese
  Se atingiu o limite, mandar mensagem de sistema: "sintetize com o que tem"
```

**O agente não conhece os canais.** Recebe `QueryRequest`, devolve `QueryResponse`. Ponto.

---

## 📡 channels/ — Esboço

Cada canal tem responsabilidade única: **traduzir o mundo externo para QueryRequest e vice-versa**.

### web.py (MVP)
```
POST /consulta
  Body: { "pergunta": "o que ficou pendente da reunião de terça?" }
  Response: { "resposta": "...", "fragmentos": [...] }
```
Monta `QueryRequest`, chama `query_agent.run()`, serializa `QueryResponse` para JSON.

### whatsapp.py (futuro)
```
POST /webhook/whatsapp (Twilio ou Meta Cloud API)
  Extrai texto da mensagem recebida
  Monta QueryRequest
  Chama query_agent.run()
  Trunca resposta para 1600 chars se necessário
  POST de volta para a API do WhatsApp
```

### alexa.py (futuro)
```
Lambda handler (AWS)
  Extrai utterance do JSON da Alexa
  Monta QueryRequest
  Chama query_agent.run()
  Envolve resposta em SSML para síntese de voz
  Retorna no formato Alexa response JSON
```

---

## 🛠️ Ferramentas Planejadas

| Ferramenta | Arquivo | Descrição | Depende de |
|---|---|---|---|
| `buscar_por_topico` | `tools/topicos.py` | Fragmentos por tópico hierárquico | M5 |
| `listar_topicos` | `tools/topicos.py` | Lista tópicos existentes do usuário | M5 |
| `buscar_por_entidade` | `tools/entidades.py` | Fragmentos mencionando pessoa/projeto/empresa | M5 |
| `buscar_por_periodo` | `tools/temporal.py` | Fragmentos entre duas datas | M5 |
| `listar_action_items` | `tools/tarefas.py` | Tarefas pendentes/concluídas | M5 |
| `buscar_texto_livre` | `tools/texto.py` | ILIKE em resumo e palavras-chave | M5 |
| `buscar_semanticamente` | `tools/semantica.py` | pgvector similarity search | **M7** |

> **Nota:** `buscar_semanticamente` será implementada no M7. O arquivo existe mas a função retorna `NotImplementedError` até lá. O decorator `@register_tool` é adicionado apenas quando o M7 estiver ativo para não confundir a LLM com uma ferramenta que não funciona.

---

## ➕ Como Adicionar uma Nova Ferramenta

1. Criar (ou abrir) um arquivo em `tools/`
2. Decorar a função com `@register_tool`
3. Importar o módulo em `tools/__init__.py`

**Nenhum outro arquivo precisa ser alterado.** O `query_agent.py` chama `get_all_tools()` dinamicamente — a nova ferramenta aparece automaticamente no próximo request.

```python
# Exemplo: tools/reunioes.py
@register_tool(
    name="buscar_reunioes",
    description="Busca fragmentos de reuniões num período",
    parameters={
        "periodo": {"type": "string", "description": "ex: 'esta semana', 'março'"}
    }
)
def buscar_reunioes(periodo: str, usuario_id: int) -> list[dict]:
    ...
```

---

## ➕ Como Adicionar um Novo Canal

1. Criar `channels/novo_canal.py`
2. Implementar o handler específico do canal
3. Montar `QueryRequest`, chamar `query_agent.run()`, formatar `QueryResponse`

**O `query_agent.py`, o `registry.py` e todas as ferramentas não mudam.**

---

## 🔄 Decisões de Design

**Por que não LangChain?**
— O projeto já tem um padrão de módulos Python simples sem frameworks pesados. LangChain adicionaria ~50 abstrações para um loop de 5 rodadas que são ~50 linhas de código. Difícil de debugar quando a LLM faz algo inesperado.

**Por que não text-to-SQL direto?**
— LLM gera SQL errado com frequência (esquece `usuario_id`, usa colunas erradas). Com tool calling, cada query é uma função Python revisada por humano — o LLM só escolhe qual chamar e com quais parâmetros.

**Por que `usuario_id` é injetado pelo agente e não pela LLM?**
— Segurança. O usuário autenticado não pode manipular qual `usuario_id` será usado nas queries. O canal autentica o usuário, passa para `QueryRequest`, o agente injeta em cada `dispatch()`. A LLM nunca vê ou controla o `usuario_id`.

**Por que `ferramentas_usadas` em `QueryResponse`?**
— Para logging e futura UI de "como cheguei nessa resposta". Útil para debug quando a LLM escolher a ferramenta errada.

---

## 📊 Fluxo Completo — Exemplo

```
Usuário (web): "o que ficou pendente da semana passada?"

QueryRequest(pergunta="o que ficou pendente da semana passada?", usuario_id=1)

Rodada 1:
  LLM recebe: pergunta + 6 ferramentas disponíveis
  LLM responde: tool_call → listar_action_items(status="pendente")

Rodada 2 (execução):
  dispatch("listar_action_items", {"status": "pendente"}, usuario_id=1)
  → SELECT action_items WHERE status='pendente' AND usuario_id=1
  → [{"texto": "Revisar PR do Jarvis", "criado_em": "2026-03-15"}, ...]

Rodada 3 (síntese):
  LLM recebe os resultados
  LLM responde: "Você tem 3 itens pendentes da semana passada:
    1. Revisar PR do Jarvis (criado em 15/03)
    ..."

QueryResponse(
  resposta="Você tem 3 itens pendentes...",
  fragmentos=[...],
  ferramentas_usadas=["listar_action_items"]
)
```

---

## ⚙️ Variáveis de Ambiente

```bash
MODULO6_MAX_ROUNDS=5          # Máximo de rodadas do agentic loop
MODULO6_MODEL=gpt-4o-mini     # Modelo para síntese (pode ser diferente do M4)
MODULO6_MAX_FRAGMENTOS=20     # Limite de fragmentos retornados por ferramenta
```

---

## 🚀 Próximas Etapas

- **MVP**: Implementar `registry.py` + `query_agent.py` + ferramentas M5 + `channels/web.py`
- **M7**: Adicionar `tools/semantica.py` com `buscar_semanticamente` via pgvector
- **Futuro**: `channels/whatsapp.py` (Twilio ou Meta Cloud API)
- **Futuro**: `channels/alexa.py` (AWS Lambda + Alexa Skills Kit)

---

## 📚 Referências

- [[Modulo5-Estruturado]] — Schema das tabelas consultadas pelas ferramentas
- [[Modulo7-Semantico]] — Embeddings e pgvector usados por `buscar_semanticamente`
- [[Modulo4-Processamento-IA]] — Como os fragmentos foram criados
