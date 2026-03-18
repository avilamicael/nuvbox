---
title: Módulo 4 - Processamento IA (GPT-4o mini)
description: Extração de entidades, tópicos e importância de transcrições usando GPT-4o mini
tags: #modulo4 #ia #gpt4 #processamento #entidades #topicos #cerebro
aliases:
  - Módulo 4
  - Processamento IA
  - AI Processing
---

# 🤖 Módulo 4 — Processamento IA com GPT-4o mini

O Módulo 4 transforma transcrições brutas em **memória estruturada e consultável**. Para cada transcrição, extrai:
- **Resumo**: 1-2 frases capturando a essência
- **Importance Score**: 0.0-1.0 indicando relevância
- **Tópicos**: Hierarquia (ex: "Trabalho > Cerebro > Bugs")
- **Entidades**: Pessoas, empresas, projetos, lugares, conceitos

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────────┐
│            MÓDULO 3 - STORAGE (Banco)                │
│                                                      │
│  transcricoes (status='pending')                     │
│    ├── id: 1001                                      │
│    ├── texto: "Reunião do Cerebro sobre bugs..."     │
│    └── status: 'pending'                             │
└──────────────────┬───────────────────────────────────┘
                   │ (Polling a cada 3 min)
                   ▼
┌──────────────────────────────────────────────────────┐
│        MÓDULO 4 - BATCH WORKER (Orquestração)        │
│                                                      │
│  1. Fetch 15 transcrições pendentes                  │
│  2. Build system + user prompts                      │
│  3. POST to OpenAI API (GPT-4o mini)                 │
│  4. Parse resposta JSON (3 níveis fallback)          │
│  5. Save fragments + entities + topics               │
│  6. Track cost & enforce limits                      │
└──────────────────┬───────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────┐
│       MÓDULO 4 - TABELAS (Memória Estruturada)       │
│                                                      │
│  fragmentos (resumos + importance)                   │
│  entidades (pessoa, empresa, projeto, conceito)      │
│  topicos (hierarquia: Trabalho > Cerebro > Bugs)     │
│  fragmento_entidade (N:N com contexto)               │
│  fragmento_topico (N:N com confiança)                │
│  entidade_entidade (grafo de relacionamentos)        │
│  modulo4_uso_diario (custo + estatísticas)           │
└──────────────────────────────────────────────────────┘
                   │
                   ▼ (Future)
        ┌──────────────────────────┐
        │  MÓDULO 5 - Query       │
        │  MÓDULO 7 - Embeddings  │
        └──────────────────────────┘
```

---

## 📊 Fluxo Completo de uma Transcrição

```
transcricoes.status:

'pending' ──→ 'processing' ──→ 'processed' ✅
                           └─→ 'skipped' (importance < 0.25)
                           └─→ 'error' ❌
```

**Exemplo**:
1. Usuário fala: "Reunião do Cerebro sobre bugs no PostgreSQL"
2. Módulo 2 salva em `transcricoes` com `status='pending'`
3. BatchWorker polling detecta novo registro
4. GPT-4o mini extrai:
   - Resumo: "Reunião com time para discutir bugs no PostgreSQL"
   - Importance: 0.85 (alto - relacionado a projeto principal)
   - Tópicos: ["Trabalho > Cerebro > Bugs"]
   - Entidades: [PostgreSQL (ferramenta), Cerebro (projeto)]
5. BatchWorker insere em `fragmentos`, `entidades`, `topicos`, links
6. Atualiza `transcricoes.status = 'processed'`

---

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# OpenAI API
OPENAI_API_KEY=sk-...           # Sua chave API OpenAI
OPENAI_MODEL=gpt-4o-mini        # Modelo (gpt-4o-mini | gpt-4o)

# Module 4 Behavior
MODULO4_BATCH_SIZE=15           # Transcrições por lote
MODULO4_POLL_INTERVAL_SECONDS=180  # Polling interval (3 min)
MODULO4_IMPORTANCE_THRESHOLD=0.25  # Score mínimo para salvar

# Cost Control
MODULO4_DAILY_COST_LIMIT_USD=2.00  # Limite diário ($)
MODULO4_MAX_RETRIES=3           # Tentativas com backoff

# Testing
MODULO4_DRY_RUN=false           # true = não insere no banco
```

### User Profile (Módulo 0)

Arquivo: `backend/modulo4_processamento/user_profile.yaml`

```yaml
usuario:
  nome: "Micael"
  idioma: "português"

contextos:
  trabalho:
    descricao: "Projetos de software, desenvolvimento"
    palavras_chave:
      - "Cerebro"
      - "código"
      - "bug"

  pessoal:
    descricao: "Vida pessoal, saúde, lazer"
    palavras_chave:
      - "saúde"
      - "exercício"

entidade_tipos:
  - "pessoa"
  - "empresa"
  - "projeto"
  - "lugar"
  - "conceito"
  - "ferramenta"
```

---

## 💰 Custo Estimado

**GPT-4o mini pricing** (data: 2024):
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Estimativas diárias**:

| Volume | Custo/dia | Custo/mês |
|--------|-----------|-----------|
| 100 transcricões | ~$0.012 | ~$0.36 |
| 500 transcricões | ~$0.058 | ~$1.74 |
| 2.000 transcricões | ~$0.227 | ~$6.81 |

**Por quê lote de 15?**
- 15 transcrições em uma chamada = ~73% economia em system prompt overhead
- Vs 15 chamadas individuais (reprocessa system prompt cada vez)

---

## 🔍 Extração de Dados

### Exemplo de Entrada

```json
{
  "quantidade": 3,
  "transcricoes": [
    {
      "idx": 0,
      "id": 1001,
      "texto": "Hoje tive reunião com time do Cerebro para discutir bugs..."
    },
    {
      "idx": 1,
      "id": 1002,
      "texto": "Fui ao médico, preciso fazer mais exercício..."
    }
  ]
}
```

### Exemplo de Saída

```json
{
  "resultados": [
    {
      "idx": 0,
      "resumo": "Reunião com team Cerebro para discussão de bugs críticos.",
      "importance_score": 0.85,
      "topicos": [
        "Trabalho > Cerebro > Bugs",
        "Trabalho > Cerebro > Deploy"
      ],
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
      "resumo": "Visita ao médico com recomendação de exercício físico.",
      "importance_score": 0.32,
      "topicos": ["Pessoal > Saúde"],
      "entidades": [
        {
          "nome": "Exercício",
          "tipo": "conceito",
          "contexto": "preciso fazer mais exercício"
        }
      ]
    }
  ]
}
```

---

## 🗄️ Schema SQL

### Tabela: fragmentos

Unidade processada (uma por transcrição com importance >= threshold).

```sql
CREATE TABLE fragmentos (
    id              BIGSERIAL PRIMARY KEY,
    transcricao_id  BIGINT NOT NULL UNIQUE,  -- 1:1 com transcricoes
    resumo          TEXT NOT NULL,           -- 1-2 frases
    importance_score DECIMAL(3,2) NOT NULL,  -- 0.00-1.00
    criado_em       TIMESTAMPTZ NOT NULL,
    tokens_input    INTEGER,
    tokens_output   INTEGER,
    model_used      VARCHAR(50),             -- e.g., 'gpt-4o-mini'
    embedding       VECTOR(1536)             -- Vazio até Módulo 7
);
```

### Tabela: entidades

Pessoas, empresas, projetos, conceitos, etc.

```sql
CREATE TABLE entidades (
    id                  BIGSERIAL PRIMARY KEY,
    nome                VARCHAR(255) NOT NULL,
    nome_normalizado    VARCHAR(255) NOT NULL,  -- Lowercase para dedup
    tipo                VARCHAR(50) NOT NULL,   -- pessoa | empresa | projeto | lugar | conceito | ferramenta
    frequencia          INTEGER NOT NULL DEFAULT 1,  -- Quantas vezes mencionada?
    primeira_mencao_em  TIMESTAMPTZ,
    ultima_mencao_em    TIMESTAMPTZ
);

UNIQUE(tipo, nome_normalizado);  -- Deduplication by type + name
```

### Tabela: topicos (Hierarquia)

```sql
CREATE TABLE topicos (
    id          BIGSERIAL PRIMARY KEY,
    nome        VARCHAR(255),               -- e.g., 'Bugs'
    caminho     TEXT NOT NULL UNIQUE,       -- e.g., 'Trabalho > Cerebro > Bugs'
    nivel       INTEGER NOT NULL,           -- 1=root, 2=child, etc.
    pai_id      BIGINT REFERENCES topicos,  -- Self-FK para hierarquia
    frequencia  INTEGER NOT NULL DEFAULT 1
);
```

### Relacionamentos (N:N)

```sql
fragmento_entidade (fragmento → entidades com contexto)
fragmento_topico (fragmento → topicos com confiança)
entidade_entidade (grafo de relacionamentos: A trabalha_para B)
```

### Cost Tracking

```sql
CREATE TABLE modulo4_uso_diario (
    id                      BIGSERIAL PRIMARY KEY,
    data                    DATE NOT NULL UNIQUE,
    tokens_input            BIGINT NOT NULL DEFAULT 0,
    tokens_output           BIGINT NOT NULL DEFAULT 0,
    custo_usd               DECIMAL(10,4) NOT NULL DEFAULT 0.0,
    fragmentos_processados  INTEGER NOT NULL DEFAULT 0,
    fragmentos_skipped      INTEGER NOT NULL DEFAULT 0,
    erros_count             INTEGER NOT NULL DEFAULT 0
);
```

---

## 🧪 Testando (Dry Run)

```bash
# 1. Sem DB insertion - só testa prompt + parsing
export MODULO4_DRY_RUN=true

# 2. Com teste de prompt (sem OpenAI)
python scripts/test_modulo4_dryrun.py

# 3. Real deployment
docker-compose up
docker-compose logs -f backend  # Ver logs do BatchWorker
```

---

## 🚨 Proteções

### Anti-Reprocessamento Duplo

No startup, BatchWorker reseta transcrições presas em `status='processing'` > 10 min:

```python
db_queries.reset_stuck_processing(timeout_minutes=10)
```

### Limite de Custo Diário

Antes de cada request OpenAI:

```python
if not cost_tracker.check_and_log_cost(...):
    # Cost limit exceeded - mark batch as error
    logger.error("Daily limit ($2.00) exceeded")
    return
```

### Retry Exponencial

3 tentativas com backoff em rate limit / API errors:
- Attempt 1: 1s espera
- Attempt 2: 2s espera
- Attempt 3: 4s espera

Não tenta retry em: Authentication, parsing errors.

### Parser com 3 Níveis de Fallback

1. **Level 1**: `json.loads()` direto
2. **Level 2**: Regex para extrair bloco `{...}`
3. **Level 3**: Marca batch inteira como erro, individual reprocessing em próximo ciclo

---

## 📈 Monitoring

### Logs Esperados

```
BatchWorker started
✅ BatchWorker initialized
Processing batch of 15 transcriptions...
✅ OpenAI call succeeded | input=1200 output=450 tokens
✅ Level 1 parse: Direct json.loads() succeeded
✅ Cost logged: $0.0009 (daily total: $0.0023/$2.00)
Processed: fragmento_id=42, topicos=2, entidades=3
✅ Batch processed: 12 saved, 3 skipped
```

### Queries Úteis

```sql
-- Custo diário
SELECT data, custo_usd, fragmentos_processados FROM modulo4_uso_diario ORDER BY data DESC;

-- Entidades mais frequentes
SELECT nome, tipo, frequencia FROM entidades ORDER BY frequencia DESC LIMIT 20;

-- Tópicos mais mencionados
SELECT caminho, frequencia FROM topicos ORDER BY frequencia DESC LIMIT 10;

-- Erros recentes
SELECT id, texto, modulo4_erro FROM transcricoes WHERE status = 'error' ORDER BY criado_em DESC LIMIT 10;
```

---

## 🔄 Próximas Etapas

- **Módulo 5 (Structured Storage)**: Query interface para buscar fragmentos por tópico/entidade
- **Módulo 7 (Semantic Memory)**: Embeddings + similarity search com pgvector

---

## 📚 Referências

- [[Modulo4-Prompt-Engineering]] — System prompt + decisões
- [[Modulo4-Schema-SQL]] — Detalhamento das tabelas
- [[Modulo1-Input]] — Entrada de dados
- [[Modulo3-Armazenamento]] — Storage de transcrições brutas
