---
title: Módulo 4 - Schema SQL
description: Detalhamento completo das tabelas de Módulo 4 com justificativas de design
tags: #modulo4 #schema #sql #database #design
aliases:
  - Module 4 Schema
  - Schema SQL
---

# 🗄️ Módulo 4 — Schema SQL Detalhado

Documentação completa das tabelas, índices e relacionamentos do Módulo 4.

---

## 📋 Visão Geral das Tabelas

```
transcricoes (existente, modificado)
    ↓ (1:1)
fragmentos (NOVO)
    ├── N:M → entidades (via fragmento_entidade)
    ├── N:M → topicos (via fragmento_topico)
    └── 1:M ← entidade_entidade

entidades (NOVO)
    ├── (self) → entidade_entidade
    └── N:M ← fragmento_entidade

topicos (NOVO)
    ├── (self FK) → pai_id (hierarquia)
    └── N:M ← fragmento_topico

modulo4_uso_diario (NOVO)
    └── Aggregação de custo por data
```

---

## 📝 Modificações em Tabelas Existentes

### ALTER TABLE transcricoes

Adicionamos 3 colunas para rastrear processamento:

```sql
ALTER TABLE transcricoes
ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'pending';

ALTER TABLE transcricoes
ADD COLUMN IF NOT EXISTS processado_em TIMESTAMPTZ;

ALTER TABLE transcricoes
ADD COLUMN IF NOT EXISTS modulo4_erro TEXT;
```

| Coluna | Tipo | Descrição | Valores |
|--------|------|-----------|---------|
| `status` | VARCHAR(20) | Estado do processamento | `pending`, `processing`, `processed`, `skipped`, `error` |
| `processado_em` | TIMESTAMPTZ | Timestamp de processamento | NULL até processado |
| `modulo4_erro` | TEXT | Mensagem de erro (se houve) | NULL se success; ex: "importance < 0.25" |

**Máquina de Estados**:
```
pending → processing → processed ✅
              ↓
           skipped (importance < 0.25)
              ↓
            error (falha de parsing)
```

**Índices Adicionados**:
```sql
CREATE INDEX idx_transcricoes_status
  ON transcricoes (status) WHERE status = 'pending';
  -- Para polling rápido do BatchWorker

CREATE INDEX idx_transcricoes_processado_em
  ON transcricoes (processado_em DESC)
  WHERE status = 'processing';
  -- Para detectar records presos em processing
```

---

## 🆕 Tabela: fragmentos

**Propósito**: Unidade processada = resumo + importance score de UMA transcrição

**Diagrama**:
```
transcricoes (1)
    ↓
fragmentos (1)
    ├── resumo: "Reunião com time sobre bugs"
    ├── importance_score: 0.85
    ├── tokens_input: 250
    ├── tokens_output: 120
    └── embedding: NULL (vazio até Módulo 7)
```

```sql
CREATE TABLE fragmentos (
    id              BIGSERIAL PRIMARY KEY,
    transcricao_id  BIGINT NOT NULL UNIQUE,
    resumo          TEXT NOT NULL,
    importance_score DECIMAL(3,2) NOT NULL,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tokens_input    INTEGER,
    tokens_output   INTEGER,
    model_used      VARCHAR(50),
    embedding       VECTOR(1536)
);
```

| Coluna | Tipo | Descrição | Notas |
|--------|------|-----------|-------|
| `id` | BIGSERIAL | PK | Auto-increment |
| `transcricao_id` | BIGINT | FK para transcricoes | UNIQUE (1:1) |
| `resumo` | TEXT | 1-2 frases | Extraído por GPT-4o mini |
| `importance_score` | DECIMAL(3,2) | 0.00 a 1.00 | > 0.25 para ser salvo |
| `tokens_input` | INTEGER | Tokens usados | Para custo |
| `tokens_output` | INTEGER | Tokens gerados | Para custo |
| `model_used` | VARCHAR(50) | e.g., 'gpt-4o-mini' | Auditoria |
| `embedding` | VECTOR(1536) | Vetor de embedding | Vazio; preenchido por Módulo 7 |

**Índices**:
```sql
CREATE INDEX idx_fragmentos_transcricao_id
  ON fragmentos (transcricao_id);

CREATE INDEX idx_fragmentos_importance
  ON fragmentos (importance_score DESC);
  -- Para buscar "mais importantes"
```

**Exemplo de Dados**:
```sql
INSERT INTO fragmentos VALUES
  (1, 1001, 'Reunião com time sobre bugs no PostgreSQL', 0.85, NOW(), 250, 120, 'gpt-4o-mini', NULL);
```

**Por quê DECIMAL(3,2)?**
- Precision: 3 dígitos totais
- Scale: 2 casas decimais
- Range: 0.00 a 99.99 (nós usamos 0.00-1.00)
- Alternativa: FLOAT (menos preciso para moeda/scoring)

---

## 🆕 Tabela: entidades

**Propósito**: Deduplicação de nomes (pessoas, empresas, projetos, etc.)

**Diagrama**:
```
entidades (múltiplas):
  ├─ nome: "PostgreSQL" (raw)
  ├─ nome_normalizado: "postgresql" (lowercase)
  ├─ tipo: "ferramenta"
  ├─ frequencia: 15 (quantas vezes mencionada)
  └─ ... relacionamento com fragmentos via N:M
```

```sql
CREATE TABLE entidades (
    id                  BIGSERIAL PRIMARY KEY,
    nome                VARCHAR(255) NOT NULL,
    nome_normalizado    VARCHAR(255) NOT NULL,
    tipo                VARCHAR(50) NOT NULL,
    frequencia          INTEGER NOT NULL DEFAULT 1,
    primeira_mencao_em  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultima_mencao_em    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_entidades_tipo_normalizado
  ON entidades (tipo, nome_normalizado);
```

| Coluna | Tipo | Descrição | Notas |
|--------|------|-----------|-------|
| `nome` | VARCHAR(255) | Nome raw | Ex: "PostgreSQL", "João Silva" |
| `nome_normalizado` | VARCHAR(255) | Lowercase | Para deduplicação |
| `tipo` | VARCHAR(50) | Tipo de entidade | `pessoa`, `empresa`, `projeto`, `lugar`, `conceito`, `ferramenta` |
| `frequencia` | INTEGER | Contagem | Incrementada cada vez mencionada |
| `primeira_mencao_em` | TIMESTAMPTZ | Primeira vez | Para timeline |
| `ultima_mencao_em` | TIMESTAMPTZ | Última vez | Para relevância recente |

**Exemplo**:
```sql
INSERT INTO entidades VALUES
  (1, 'PostgreSQL', 'postgresql', 'ferramenta', 5, NOW(), NOW(), NOW()),
  (2, 'Cerebro', 'Cerebro', 'projeto', 20, NOW(), NOW(), NOW()),
  (3, 'João Silva', 'joão silva', 'pessoa', 3, NOW(), NOW(), NOW());
```

**Lógica de Upsert**:
```python
# Se (tipo, nome_normalizado) já existe:
UPDATE entidades SET frequencia = frequencia + 1 ...

# Caso contrário:
INSERT INTO entidades VALUES ...
```

**Por quê armazenar `nome` E `nome_normalizado`?**
- `nome`: Preserva case original (mais legível em UI)
- `nome_normalizado`: Deduplicação insensível a case (postgresql = PostgreSQL = POSTGRESQL)

---

## 🆕 Tabela: topicos (Hierarquia)

**Propósito**: Organização em árvore (ex: "Trabalho > Cerebro > Bugs")

**Diagrama**:
```
Trabalho (id=1, nivel=1, pai_id=NULL)
  └── Cerebro (id=2, nivel=2, pai_id=1)
       ├── Bugs (id=3, nivel=3, pai_id=2)
       └── Deploy (id=4, nivel=3, pai_id=2)

Pessoal (id=5, nivel=1, pai_id=NULL)
  └── Saúde (id=6, nivel=2, pai_id=5)
       └── Exercício (id=7, nivel=3, pai_id=6)
```

```sql
CREATE TABLE topicos (
    id          BIGSERIAL PRIMARY KEY,
    nome        VARCHAR(255) NOT NULL,
    caminho     TEXT NOT NULL UNIQUE,
    nivel       INTEGER NOT NULL,
    pai_id      BIGINT REFERENCES topicos(id) ON DELETE SET NULL,
    frequencia  INTEGER NOT NULL DEFAULT 1,
    primeira_mencao_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_topicos_caminho
  ON topicos (caminho);
CREATE INDEX idx_topicos_pai_id
  ON topicos (pai_id);
```

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `nome` | VARCHAR(255) | Parte final | "Bugs" |
| `caminho` | TEXT | Path completo | "Trabalho > Cerebro > Bugs" |
| `nivel` | INTEGER | Profundidade | 1 (root), 2, 3... |
| `pai_id` | BIGINT | Self FK | id do tópico pai |
| `frequencia` | INTEGER | Contagem | Quantas vezes mencionado |

**Exemplo**:
```sql
INSERT INTO topicos (nome, caminho, nivel, pai_id) VALUES
  ('Trabalho', 'Trabalho', 1, NULL),
  ('Cerebro', 'Trabalho > Cerebro', 2, 1),
  ('Bugs', 'Trabalho > Cerebro > Bugs', 3, 2);
```

**Queries Úteis**:
```sql
-- Árvore completa
SELECT * FROM topicos WHERE nivel = 1 ORDER BY nome;

-- Subtópicos de "Cerebro"
SELECT * FROM topicos WHERE caminho LIKE 'Trabalho > Cerebro%';

-- Tópicos mais frequentes
SELECT caminho, frequencia FROM topicos ORDER BY frequencia DESC;
```

---

## 🆕 Tabela: fragmento_entidade (N:M com contexto)

**Propósito**: Ligar fragmentos a entidades com o contexto de onde foram mencionadas

**Diagrama**:
```
fragmento (id=42) ──┐
                    ├─→ fragmento_entidade
                    │   ├─ contexto: "bugs no PostgreSQL"
                    │   └─ posicao_relativa: "meio"
                    │
entidade (id=1, PostgreSQL) ──┘
```

```sql
CREATE TABLE fragmento_entidade (
    id              BIGSERIAL PRIMARY KEY,
    fragmento_id    BIGINT NOT NULL REFERENCES fragmentos(id) ON DELETE CASCADE,
    entidade_id     BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    contexto        TEXT NOT NULL,
    posicao_relativa VARCHAR(50),
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_fragmento_entidade_unique
  ON fragmento_entidade (fragmento_id, entidade_id);
```

| Coluna | Tipo | Descrição | Notas |
|--------|------|-----------|-------|
| `fragmento_id` | BIGINT | FK | Cascata delete |
| `entidade_id` | BIGINT | FK | Cascata delete |
| `contexto` | TEXT | Trecho | "bugs no PostgreSQL" |
| `posicao_relativa` | VARCHAR(50) | Onde mencionada | `inicio`, `meio`, `final` |

**Exemplo**:
```sql
INSERT INTO fragmento_entidade VALUES
  (1, 42, 1, 'bugs no PostgreSQL', 'meio'),
  (2, 42, 2, 'reunião com o time do Cerebro', 'inicio');
```

**Por quê `UNIQUE(fragmento_id, entidade_id)`?**
- Evita duplicação
- Mas permite múltiplas menções da mesma entidade em fragmentos diferentes

---

## 🆕 Tabela: fragmento_topico (N:M com confiança)

**Propósito**: Ligar fragmentos a tópicos com score de confiança

```sql
CREATE TABLE fragmento_topico (
    id              BIGSERIAL PRIMARY KEY,
    fragmento_id    BIGINT NOT NULL REFERENCES fragmentos(id) ON DELETE CASCADE,
    topico_id       BIGINT NOT NULL REFERENCES topicos(id) ON DELETE CASCADE,
    confianca       DECIMAL(3,2) NOT NULL,
    eh_principal    BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_fragmento_topico_unique
  ON fragmento_topico (fragmento_id, topico_id);
```

| Coluna | Tipo | Descrição | Notas |
|--------|------|-----------|-------|
| `confianca` | DECIMAL(3,2) | Score 0.0-1.0 | LLM confidence |
| `eh_principal` | BOOLEAN | É o tópico principal? | Primeiro na lista = true |

**Exemplo**:
```sql
INSERT INTO fragmento_topico VALUES
  (1, 42, 2, 1.0, true),   -- Trabalho > Cerebro > Bugs (principal)
  (2, 42, 3, 0.7, false);  -- Trabalho > Cerebro > Deploy (secundário)
```

---

## 🆕 Tabela: entidade_entidade (Grafo de Relacionamentos)

**Propósito**: Preparar para Módulo 7 (Knowledge Graph)

**Diagrama**:
```
João Silva (pessoa)
    ├── trabalha_para → Cerebro (projeto)
    └── amigo_de → Maria Silva (pessoa)

Cerebro (projeto)
    ├── usa → PostgreSQL (ferramenta)
    └── usa → Python (ferramenta)
```

```sql
CREATE TABLE entidade_entidade (
    id              BIGSERIAL PRIMARY KEY,
    entidade1_id    BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    entidade2_id    BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    tipo_relacao    VARCHAR(100) NOT NULL,
    confianca       DECIMAL(3,2) NOT NULL,
    frequencia      INTEGER NOT NULL DEFAULT 1,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_entidade_entidade_unique
  ON entidade_entidade (entidade1_id, entidade2_id, tipo_relacao);
```

| Coluna | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| `tipo_relacao` | VARCHAR(100) | Tipo de relação | `trabalha_para`, `amigo_de`, `usa`, `componente_de` |
| `confianca` | DECIMAL(3,2) | Score 0.0-1.0 | LLM confidence na relação |
| `frequencia` | INTEGER | Vezes mencionada | Para Módulo 7 ranking |

**Exemplo**:
```sql
INSERT INTO entidade_entidade VALUES
  (1, 3, 2, 'trabalha_para', 1.0, 5),  -- João trabalha para Cerebro
  (2, 2, 1, 'usa', 0.95, 3);            -- Cerebro usa PostgreSQL
```

**Future Use** (Módulo 7):
```python
# Buscar "João trabalha para quem?"
SELECT e2.nome FROM entidade_entidade
  WHERE entidade1_id = 3 AND tipo_relacao = 'trabalha_para';

# Buscar "Quem trabalha para Cerebro?"
SELECT e1.nome FROM entidade_entidade
  WHERE entidade2_id = 2 AND tipo_relacao = 'trabalha_para';
```

---

## 🆕 Tabela: modulo4_uso_diario (Cost Tracking)

**Propósito**: Rastrear custo diário + estatísticas

```sql
CREATE TABLE modulo4_uso_diario (
    id                      BIGSERIAL PRIMARY KEY,
    data                    DATE NOT NULL UNIQUE,
    tokens_input            BIGINT NOT NULL DEFAULT 0,
    tokens_output           BIGINT NOT NULL DEFAULT 0,
    custo_usd               DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
    fragmentos_processados  INTEGER NOT NULL DEFAULT 0,
    fragmentos_skipped      INTEGER NOT NULL DEFAULT 0,
    erros_count             INTEGER NOT NULL DEFAULT 0,
    atualizado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_modulo4_uso_diario_data
  ON modulo4_uso_diario (data DESC);
```

| Coluna | Tipo | Descrição | Notas |
|--------|------|-----------|-------|
| `data` | DATE | Data da coleta | UNIQUE |
| `tokens_input` | BIGINT | Total de input tokens | Para cálculo de custo |
| `tokens_output` | BIGINT | Total de output tokens | Para cálculo de custo |
| `custo_usd` | DECIMAL(10,4) | Custo em USD | Até $9999.9999 |
| `fragmentos_processados` | INTEGER | Salvos | importance >= 0.25 |
| `fragmentos_skipped` | INTEGER | Descartados | importance < 0.25 |
| `erros_count` | INTEGER | Erros | Parse failures |

**Exemplo**:
```sql
INSERT INTO modulo4_uso_diario VALUES
  (1, '2024-03-17', 5000, 1800, 0.0024, 15, 3, 0, NOW());
```

**Cálculo de Custo**:
```
input_cost = (tokens_input / 1_000_000) * 0.15
output_cost = (tokens_output / 1_000_000) * 0.60
total_cost = input_cost + output_cost

Exemplo:
  5000 input tokens: (5000/1M)*0.15 = $0.00075
  1800 output tokens: (1800/1M)*0.60 = $0.00108
  Total: $0.00183 ≈ $0.0018
```

---

## 📊 Relações de Chaves Estrangeiras

```sql
fragmentos.transcricao_id
  → REFERENCES transcricoes(id) ON DELETE CASCADE
  -- Se transcrição for deletada, fragmento também

fragmento_entidade.fragmento_id
  → REFERENCES fragmentos(id) ON DELETE CASCADE
  -- Se fragmento deletado, link também

fragmento_entidade.entidade_id
  → REFERENCES entidades(id) ON DELETE CASCADE
  -- Se entidade deletada, link também

topicos.pai_id
  → REFERENCES topicos(id) ON DELETE SET NULL
  -- Se pai deletado, filho não é deletado (orfanato)

fragmento_topico.*
  → ON DELETE CASCADE
  -- Se fragmento ou tópico deletado, link vai embora

entidade_entidade.entidade1/2_id
  → ON DELETE CASCADE
  -- Se entidade deletada, relacionamentos também
```

---

## 🔍 Queries Úteis

### Performance & Monitoring

```sql
-- Custo diário
SELECT data, custo_usd, fragmentos_processados, fragmentos_skipped
FROM modulo4_uso_diario
ORDER BY data DESC LIMIT 30;

-- Top entidades por frequência
SELECT tipo, nome, frequencia
FROM entidades
ORDER BY frequencia DESC LIMIT 20;

-- Tópicos mais mencionados
SELECT caminho, frequencia
FROM topicos
ORDER BY frequencia DESC LIMIT 20;

-- Fragmentos com maior importance
SELECT f.id, f.resumo, f.importance_score, t.texto
FROM fragmentos f
JOIN transcricoes t ON f.transcricao_id = t.id
ORDER BY f.importance_score DESC LIMIT 10;

-- Erros recentes
SELECT id, texto, status, modulo4_erro
FROM transcricoes
WHERE status IN ('error', 'skipped')
ORDER BY processado_em DESC LIMIT 20;
```

### Exploração de Dados

```sql
-- Entidades mencionadas em tópico "Cerebro"
SELECT DISTINCT e.nome, e.tipo, COUNT(*) as vezes
FROM entidades e
JOIN fragmento_entidade fe ON e.id = fe.entidade_id
JOIN fragmentos f ON fe.fragmento_id = f.id
JOIN fragmento_topico ft ON f.id = ft.fragmento_id
JOIN topicos t ON ft.topico_id = t.id
WHERE t.caminho LIKE 'Trabalho > Cerebro%'
GROUP BY e.id, e.nome, e.tipo
ORDER BY vezes DESC;

-- Grafo de relacionamentos para uma entidade
SELECT e2.nome, e2.tipo, ee.tipo_relacao, ee.confianca
FROM entidade_entidade ee
JOIN entidades e2 ON ee.entidade2_id = e2.id
WHERE ee.entidade1_id = (SELECT id FROM entidades WHERE nome = 'Cerebro')
ORDER BY ee.confianca DESC;
```

---

## 📚 Referências

- [[Modulo4-Processamento-IA]] — Overview do módulo
- [[Modulo4-Prompt-Engineering]] — Decisões e prompt
- `backend/modulo4_processamento/schema_migration.sql` — SQL bruteforça
