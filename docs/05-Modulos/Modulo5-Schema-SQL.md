---
tags: [modulo5, schema, sql, postgres]
---

# Módulo 5 — Schema SQL Completo

Schema aplicado por `backend/modulo5_estruturado/schema_migration.sql` via `entrypoint.sh`.

> Ver também: [[Modulo4-Schema-SQL]] para o schema base, [[Modulo5-Estruturado]] para decisões de design.

---

## Migration SQL

```sql
-- Módulo 5 — Armazenamento Estruturado
-- Schema migration: novos campos, tabela action_items, correção embedding

-- 1. Colunas faltantes em fragmentos
ALTER TABLE fragmentos
  ADD COLUMN IF NOT EXISTS sentimento VARCHAR(20),
  ADD COLUMN IF NOT EXISTS tem_decisao BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS tem_pergunta BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS usuario_id INTEGER DEFAULT 1;

-- 2. Corrigir dimensão do embedding (1536 → 384 para MiniLM local, M7)
ALTER TABLE fragmentos DROP COLUMN IF EXISTS embedding;
ALTER TABLE fragmentos ADD COLUMN IF NOT EXISTS embedding VECTOR(384);

-- 3. Entidades: descricao, status, usuario_id
ALTER TABLE entidades
  ADD COLUMN IF NOT EXISTS descricao TEXT,
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ativo',
  ADD COLUMN IF NOT EXISTS usuario_id INTEGER DEFAULT 1;

-- 4. Tópicos: descricao, status, usuario_id
ALTER TABLE topicos
  ADD COLUMN IF NOT EXISTS descricao TEXT,
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ativo',
  ADD COLUMN IF NOT EXISTS usuario_id INTEGER DEFAULT 1;

-- 5. Nova tabela action_items
CREATE TABLE IF NOT EXISTS action_items (
  id            BIGSERIAL PRIMARY KEY,
  fragmento_id  BIGINT NOT NULL REFERENCES fragmentos(id) ON DELETE CASCADE,
  texto         TEXT NOT NULL,
  status        VARCHAR(20) DEFAULT 'pendente',
  atualizado_por VARCHAR(20) DEFAULT 'manual',
  criado_em     TIMESTAMPTZ DEFAULT NOW(),
  usuario_id    INTEGER DEFAULT 1
);

-- Índices action_items
CREATE INDEX IF NOT EXISTS idx_action_items_fragmento ON action_items(fragmento_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
CREATE INDEX IF NOT EXISTS idx_action_items_usuario ON action_items(usuario_id);

-- Índices novos em fragmentos
CREATE INDEX IF NOT EXISTS idx_fragmentos_sentimento ON fragmentos(sentimento);
CREATE INDEX IF NOT EXISTS idx_fragmentos_tem_decisao ON fragmentos(tem_decisao) WHERE tem_decisao = TRUE;
CREATE INDEX IF NOT EXISTS idx_fragmentos_tem_pergunta ON fragmentos(tem_pergunta) WHERE tem_pergunta = TRUE;

-- Índices em entidades e tópicos
CREATE INDEX IF NOT EXISTS idx_entidades_status ON entidades(status);
CREATE INDEX IF NOT EXISTS idx_topicos_status ON topicos(status);
```

---

## Schema Completo M5 (state after migration)

### `fragmentos`
| Coluna | Tipo | Notas |
|---|---|---|
| id | BIGSERIAL PK | — |
| transcricao_id | BIGINT FK | → transcricoes |
| resumo | TEXT | Resumo 1–3 frases |
| importance_score | DECIMAL(4,2) | 0.00–1.00 |
| tokens_input | INTEGER | — |
| tokens_output | INTEGER | — |
| model_used | VARCHAR(50) | ex: gpt-4o-mini |
| sentimento | VARCHAR(20) | positivo\|negativo\|neutro\|misto *(M5)* |
| tem_decisao | BOOLEAN | default FALSE *(M5)* |
| tem_pergunta | BOOLEAN | default FALSE *(M5)* |
| usuario_id | INTEGER | default 1 *(M5)* |
| embedding | VECTOR(384) | MiniLM local, M7 *(M5, corrigido de 1536)* |
| criado_em | TIMESTAMPTZ | — |

### `action_items` *(nova — M5)*
| Coluna | Tipo | Notas |
|---|---|---|
| id | BIGSERIAL PK | — |
| fragmento_id | BIGINT FK | → fragmentos (CASCADE DELETE) |
| texto | TEXT | Tarefa extraída pelo LLM |
| status | VARCHAR(20) | pendente\|concluido\|cancelado |
| atualizado_por | VARCHAR(20) | manual\|llm |
| criado_em | TIMESTAMPTZ | — |
| usuario_id | INTEGER | default 1 |

### `entidades`
| Coluna | Tipo | Notas |
|---|---|---|
| id | BIGSERIAL PK | — |
| nome | VARCHAR(200) | Nome original |
| nome_normalizado | VARCHAR(200) | Lowercase, unique key (+ tipo) |
| tipo | VARCHAR(50) | pessoa, empresa, projeto, etc. |
| frequencia | INTEGER | Contagem de menções |
| ultima_mencao_em | TIMESTAMPTZ | — |
| descricao | TEXT | *(M5)* |
| status | VARCHAR(20) | ativo\|pendente\|ambiguo *(M5)* |
| usuario_id | INTEGER | default 1 *(M5)* |
| criado_em | TIMESTAMPTZ | — |

### `topicos`
| Coluna | Tipo | Notas |
|---|---|---|
| id | BIGSERIAL PK | — |
| nome | VARCHAR(200) | Último nível do caminho |
| caminho | TEXT UNIQUE | ex: "Trabalho > Cerebro > Bug" |
| nivel | INTEGER | Profundidade hierárquica |
| pai_id | BIGINT FK | Self-referencial |
| frequencia | INTEGER | Contagem de menções |
| ultima_mencao_em | TIMESTAMPTZ | — |
| descricao | TEXT | *(M5)* |
| status | VARCHAR(20) | ativo\|pendente\|ambiguo *(M5)* |
| usuario_id | INTEGER | default 1 *(M5)* |
| criado_em | TIMESTAMPTZ | — |

---

## Queries Úteis

```sql
-- Pendências de desambiguação (entidades para revisão)
SELECT id, nome, tipo, status, frequencia
FROM entidades
WHERE status = 'pendente'
ORDER BY frequencia DESC;

-- Action items em aberto
SELECT ai.id, ai.texto, ai.criado_em, f.resumo
FROM action_items ai
JOIN fragmentos f ON f.id = ai.fragmento_id
WHERE ai.status = 'pendente'
ORDER BY ai.criado_em DESC;

-- Fragmentos com decisões
SELECT id, resumo, sentimento, criado_em
FROM fragmentos
WHERE tem_decisao = TRUE
ORDER BY criado_em DESC
LIMIT 20;

-- Fragmentos com perguntas em aberto
SELECT id, resumo, criado_em
FROM fragmentos
WHERE tem_pergunta = TRUE
ORDER BY criado_em DESC
LIMIT 20;

-- Distribuição de sentimento
SELECT sentimento, COUNT(*) as total
FROM fragmentos
GROUP BY sentimento
ORDER BY total DESC;

-- Concluir um action item manualmente
UPDATE action_items
SET status = 'concluido', atualizado_por = 'manual'
WHERE id = <id>;

-- Resolver entidade pendente (marcar como ativa)
UPDATE entidades SET status = 'ativo' WHERE id = <id>;
```
