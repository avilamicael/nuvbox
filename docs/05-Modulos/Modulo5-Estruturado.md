---
tags: [modulo5, estruturado, schema, entity-resolver, action-items]
---

# Módulo 5 — Armazenamento Estruturado

## Visão Geral

O M5 solidifica o schema do banco de dados e adiciona inteligência de desambiguação de entidades. Ele se integra ao [[Modulo4-Processamento-IA|Módulo 4]] sem substituí-lo — o BatchWorker continua sendo o orquestrador, agora com mais contexto.

**Dois objetivos:**

1. **Solidificar o schema** — adicionar campos que o M4 já extraía mas descartava (`sentimento`, `tem_decisao`, `tem_pergunta`, `action_items`), corrigir dimensão do embedding, adicionar `status` e `descricao` em entidades/tópicos
2. **Workflow de desambiguação** — antes do LLM rodar, injetar entidades/tópicos existentes no prompt; após resposta, usar `EntityResolver` para decidir criar nova vs. reutilizar existente vs. marcar como pendente para revisão

---

## Arquivos do Módulo

| Arquivo | Responsabilidade |
|---|---|
| `backend/modulo5_estruturado/__init__.py` | Exports: `EntityResolver`, `ResolveResult` |
| `backend/modulo5_estruturado/schema_migration.sql` | ALTERs + CREATE TABLE action_items |
| `backend/modulo5_estruturado/entity_resolver.py` | Fuzzy match + decisão ativo/pendente/novo |
| `backend/modulo5_estruturado/db_queries.py` | fetch_existing_entities, fetch_existing_topics, save_action_items, update_entity_status |

**Arquivos modificados pelo M5:**

| Arquivo | O que mudou |
|---|---|
| `backend/modulo4_processamento/db_queries.py` | `save_fragment()` recebe `sentimento`, `tem_decisao`, `tem_pergunta` |
| `backend/modulo4_processamento/batch_worker.py` | Usa `EntityResolver`, salva `action_items`, passa campos M5 |
| `backend/modulo4_processamento/prompt_builder.py` | `build_system_prompt()` aceita entidades/tópicos; novos métodos `build_entity_context()`, `build_topic_context()` |
| `backend/entrypoint.sh` | Aplica `modulo5_estruturado/schema_migration.sql` |

---

## Fluxo de Desambiguação

```
BatchWorker._process_batch()
  │
  ├─ 1. m5_db.fetch_existing_entities(limit=100)
  ├─ 2. m5_db.fetch_existing_topics(limit=50)
  │
  ├─ 3. prompt_builder.build_system_prompt(existing_entities, existing_topics)
  │       └─ Injeta seção "ENTIDADES CONHECIDAS" + "TÓPICOS EXISTENTES" no prompt
  │
  ├─ 4. openai_client.call_with_retry(...)
  │
  └─ _process_result()
       │
       ├─ db_queries.save_fragment(..., sentimento, tem_decisao, tem_pergunta)
       │
       ├─ m5_db.save_action_items(fragmento_id, action_items)
       │
       ├─ db_queries.upsert_topico(...)  [sem mudança]
       │
       └─ Para cada entidade:
            EntityResolver.resolve(nome, tipo)
              ├─ status='ativo'    → reutilizar id existente (match exato)
              ├─ status='pendente' → reutilizar id + marcar para revisão (fuzzy)
              └─ status='novo'     → criar nova entidade
```

---

## EntityResolver

Localização: `backend/modulo5_estruturado/entity_resolver.py`

**Algoritmo:**
1. **Match exato**: `nome_normalizado` + `tipo` → `status='ativo'`
2. **Fuzzy match**: `difflib.SequenceMatcher` com threshold=0.85 → `status='pendente'`
3. **Sem match**: retorna `entidade_id=None`, `status='novo'`

```python
resolver = EntityResolver(existing_entities)
result = resolver.resolve("Juliana", "pessoa")
# result.entidade_id = 1
# result.status = 'ativo'
# result.matched_nome = 'Juliana'
# result.score = 1.0
```

**`ResolveResult`** (dataclass):
- `entidade_id`: `int | None` — None = criar nova
- `status`: `'ativo' | 'pendente' | 'novo'`
- `matched_nome`: nome da entidade no banco que fez match
- `score`: float 0.0–1.0

---

## Tabelas Novas / Alteradas

### `action_items` (nova)
```sql
id            BIGSERIAL PRIMARY KEY
fragmento_id  BIGINT REFERENCES fragmentos(id) ON DELETE CASCADE
texto         TEXT NOT NULL
status        VARCHAR(20) DEFAULT 'pendente'   -- pendente | concluido | cancelado
atualizado_por VARCHAR(20) DEFAULT 'manual'    -- manual | llm
criado_em     TIMESTAMPTZ DEFAULT NOW()
usuario_id    INTEGER DEFAULT 1
```

### `fragmentos` (novos campos)
```sql
sentimento    VARCHAR(20)          -- positivo | negativo | neutro | misto
tem_decisao   BOOLEAN DEFAULT FALSE
tem_pergunta  BOOLEAN DEFAULT FALSE
usuario_id    INTEGER DEFAULT 1
embedding     VECTOR(384)          -- corrigido de 1536 → 384 (MiniLM local, M7)
```

### `entidades` (novos campos)
```sql
descricao     TEXT
status        VARCHAR(20) DEFAULT 'ativo'   -- ativo | pendente | ambiguo
usuario_id    INTEGER DEFAULT 1
```

### `topicos` (novos campos)
```sql
descricao     TEXT
status        VARCHAR(20) DEFAULT 'ativo'
usuario_id    INTEGER DEFAULT 1
```

---

## Decisões de Design

**Por que `difflib` em vez de `rapidfuzz`?**
— `difflib` é stdlib, sem dependência extra. Para o volume atual (~centenas de entidades), é suficiente. Migrar para `rapidfuzz` é trivial se o dataset crescer.

**Por que `status='pendente'` em vez de merge automático no fuzzy?**
— Merge automático poderia colapsar entidades distintas (ex: duas "Julianas"). O status pendente é uma fila de revisão humana sem bloquear o pipeline.

**Por que a dimensão do embedding mudou de 1536 para 384?**
— O M7 usará `sentence-transformers` com modelo MiniLM local (384 dims), não a OpenAI Embeddings API (1536 dims). Correção feita agora antes de popular dados reais.

**Por que `usuario_id DEFAULT 1`?**
— Sistema ainda é single-user. O campo está presente para facilitar a migração para multi-tenant no futuro sem reescrever schema.

---

## Verificação

```sql
-- Fragmentos com todos os campos preenchidos
SELECT id, resumo, sentimento, tem_decisao, tem_pergunta
FROM fragmentos LIMIT 5;

-- Action items salvos
SELECT ai.texto, ai.status, f.resumo
FROM action_items ai JOIN fragmentos f ON f.id = ai.fragmento_id
LIMIT 10;

-- Entidades com status
SELECT nome, tipo, status, descricao
FROM entidades ORDER BY frequencia DESC LIMIT 20;

-- Tópicos com status
SELECT caminho, status FROM topicos ORDER BY frequencia DESC LIMIT 20;
```
