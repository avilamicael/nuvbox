---
name: Módulo 4 — Implementação Concluída
description: Resumo das mudanças, arquitetura e camadas de dados (raw vs tratado)
type: documentation
tags: [modulo4, ia-processing, batch-worker, openai-sdk, groq]
---

# Módulo 4 — Implementação Concluída (18/03/2026)

## Visão Geral

**Módulo 4** processa transcrições brutas (Módulo 3) usando LLM (GPT-4o mini via Groq) para extrair:
- Resumo em 1-2 frases
- Importance score (0-1)
- Tópicos hierárquicos
- Entidades nomeadas (pessoas, empresas, projetos, conceitos)

Roda como **BatchWorker** (thread contínua) que faz polling a cada 3 minutos.

---

## Arquitetura de Duas Camadas

### Camada 1: Dados Brutos — `transcricoes` (Módulo 3)
```sql
CREATE TABLE transcricoes (
  id SERIAL PRIMARY KEY,
  text TEXT NOT NULL,                    -- Texto exato enviado pelo cliente
  source VARCHAR(100) NOT NULL,          -- windows_mic, alexa, esp32, etc.
  transcribed_at TIMESTAMPTZ NOT NULL,
  audio_duration_ms INT,
  whisper_model VARCHAR(50),
  language VARCHAR(10) DEFAULT 'pt',
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  status VARCHAR(20) DEFAULT 'pending',  -- pending → processing → processed/error
  processado_em TIMESTAMPTZ,
  modulo4_erro TEXT                      -- Log de erro se falhou
);
```

**Responsabilidade**: Armazenar áudio transcrito conforme chega. Sem processamento.

---

### Camada 2: Dados Tratados — `fragmentos` (Módulo 4)
```sql
CREATE TABLE fragmentos (
  id SERIAL PRIMARY KEY,
  transcricao_id INT NOT NULL REFERENCES transcricoes(id),
  resumo TEXT NOT NULL,                  -- 1-2 frases extraídas por LLM
  importance_score NUMERIC(3,2),         -- 0.00–1.00 (Módulo 4 decide)
  tokens_input INT,
  tokens_output INT,
  custo_usd NUMERIC(10,8),
  modelo_usado VARCHAR(50),              -- llama-3.1-8b-instant, gpt-4o-mini, etc.
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Responsabilidade**: Armazenar análise estruturada. Cada fragmento = uma transcrição processada.

---

## Fluxo de Processamento

```
1. Cliente (Pinky/Alexa)
   ↓ POST /webhook/text
2. StorageWorker (Módulo 3)
   ↓ INSERT transcricoes (status='pending')
3. BatchWorker (Módulo 4) — polling a cada 3min
   ├─ Fetch 15 transcricoes com status='pending'
   ├─ Marca como 'processing'
   ├─ Carrega user_profile.yaml (contexto do usuário)
   ├─ Constrói system prompt + batch user message
   ├─ Chama LLM (Groq/OpenAI via base_url)
   ├─ Parse JSON com 3 níveis de fallback
   ├─ Salva em fragmentos, entidades, topicos
   ├─ Atualiza status='processed'
   └─ Log custo em modulo4_uso_diario
```

---

## Arquivos Implementados

### Core Módulo 4
| Arquivo | Propósito |
|---|---|
| `modulo4_processamento/__init__.py` | Lazy import de BatchWorker |
| `modulo4_processamento/batch_worker.py` | Orquestrador principal (polling + chain de processamento) |
| `modulo4_processamento/openai_client.py` | Wrapper OpenAI SDK v1.x com retry exponencial (funciona com Groq via base_url) |
| `modulo4_processamento/prompt_builder.py` | Carrega user_profile.yaml, monta system + user prompts |
| `modulo4_processamento/response_parser.py` | Parse JSON com 3 níveis fallback + validação de schema |
| `modulo4_processamento/cost_tracker.py` | Rastreamento de custo diário + enforcement de limite |
| `modulo4_processamento/db_queries.py` | Todas as queries SQL (fetch_pending, save_fragment, upsert_entidade, etc.) |
| `modulo4_processamento/schema_migration.sql` | ALTER TABLE transcricoes + 7 novas tabelas |
| `modulo4_processamento/user_profile.yaml` | Perfil estático do usuário (Módulo 0 MVP) |

### Configuração
| Arquivo | Mudança |
|---|---|
| `config.py` | Adicionado `LLMSettings` (era `OpenAISettings`) com `base_url`, `provider`, custo |
| `.env` / `.env.example` | Adicionadas vars: `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `MODULO4_*` |
| `requirements.txt` | `openai>=1.52.0` (fixo para compatibilidade com httpx) |
| `docker-compose.yml` | Adicionadas todas as env vars do Módulo 4 |

### Integração
| Arquivo | Mudança |
|---|---|
| `main.py` | Removidas captura local (MicrophoneSource, TranscriptionWorker, raw_audio_queue). Adicionado BatchWorker init |
| `backend/entrypoint.sh` | Aplicação de schema_migration.sql após schema.sql |

---

## Configuração (Variáveis de Ambiente)

### Provider (Groq recomendado)
```bash
LLM_API_KEY=gsk_...                          # Groq: console.groq.com
LLM_MODEL=llama-3.1-8b-instant               # ou llama-3.3-70b-versatile, gemma2-9b-it
LLM_BASE_URL=https://api.groq.com/openai/v1  # Groq é OpenAI-compatible
LLM_PROVIDER=groq
LLM_COST_INPUT_PER_1M=0.0                    # Groq = free
LLM_COST_OUTPUT_PER_1M=0.0
```

### Alternativa: OpenAI (pago)
```bash
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=                                # Vazio = usa default OpenAI
LLM_PROVIDER=openai
LLM_COST_INPUT_PER_1M=0.15
LLM_COST_OUTPUT_PER_1M=0.60
```

### Batch Processing
```bash
MODULO4_BATCH_SIZE=15                 # Transcrições por lote (↑ economiza tokens de prompt)
MODULO4_POLL_INTERVAL_SECONDS=180     # 3 minutos (reduz para testes)
MODULO4_IMPORTANCE_THRESHOLD=0.25     # Descarta se < 0.25
MODULO4_DAILY_COST_LIMIT_USD=2.00     # $2/dia (para Groq free)
MODULO4_MAX_RETRIES=3                 # Retry exponencial na API
MODULO4_DRY_RUN=false                 # true = nada salva no banco
```

---

## OpenAI SDK v1.x + Groq

### Por que v1.52.0+?
Versões antigas (`1.3.9`) têm conflito com `httpx` moderno — SDK tenta passar `proxies=` que a versão instalada não suporta.

### Como funciona com Groq?
```python
from openai import OpenAI

client = OpenAI(
    api_key="gsk_...",
    base_url="https://api.groq.com/openai/v1"  # Override endpoint
)

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[...],
    temperature=0
)
```

Groq expõe API **100% compatível** com OpenAI — mesmo método, mesmo campo de resposta, sem mudanças adicionais.

---

## Response Parsing — 3 Níveis de Fallback

Se LLM retorna JSON malformado:

1. **Nível 1**: `json.loads()` direto → se falhar
2. **Nível 2**: Regex para extrair bloco `{...}` com `"resultados"` → se falhar
3. **Nível 3**: Marca batch para reprocessamento individual (1-by-1) → isolado problema

Exemplo de saída esperada:
```json
{
  "resultados": [
    {
      "idx": 0,
      "resumo": "Discussão sobre implementação do Módulo 4",
      "importance_score": 0.8,
      "topicos": ["Trabalho > Cerebro > Backend"],
      "entidades": [
        {
          "nome": "Cerebro",
          "tipo": "projeto",
          "contexto": "...trecho..."
        }
      ]
    }
  ]
}
```

---

## Verificação — Dados no Banco

```bash
# Fragmentos processados
docker exec cerebro-postgres psql -U cerebro -d cerebro_db \
  -c "SELECT id, resumo, importance_score FROM fragmentos ORDER BY id DESC LIMIT 10;"

# Entidades extraídas
docker exec cerebro-postgres psql -U cerebro -d cerebro_db \
  -c "SELECT nome, tipo FROM entidades ORDER BY id DESC LIMIT 20;"

# Tópicos
docker exec cerebro-postgres psql -U cerebro -d cerebro_db \
  -c "SELECT nome FROM topicos LIMIT 10;"

# Custo diário
docker exec cerebro-postgres psql -U cerebro -d cerebro_db \
  -c "SELECT data, custo_total, num_fragmentos FROM modulo4_uso_diario;"

# Status de transcrições (qual está pending, processado, erro)
docker exec cerebro-postgres psql -U cerebro -d cerebro_db \
  -c "SELECT id, source, status, processado_em FROM transcricoes ORDER BY id DESC LIMIT 20;"
```

---

## Decisões de Design

| Decisão | Motivo |
|---|---|
| **Polling vs WebSocket** | Simples, sem overhead de conexão; 3min é aceitável para MVP |
| **Batch de 15** | Economiza ~73% de tokens vs processar 1-by-1 (prompt system reutilizado) |
| **Groq como default** | Free tier, OpenAI-compatible, modelo rápido (8B) |
| **Sem providers no banco** | MVP: env vars bastam; interface admin vem no futuro |
| **User profile estático** | YAML simples; upgrade para DB quando houver UI de edição |
| **Sem embeddings ainda** | Deferred to Módulo 7 (pgvector não instalado); tabela `fragmentos` pronta para `embedding VECTOR(1536)` |

---

## Notas para o Futuro

- [ ] **Módulo 7**: Adicionar coluna `embedding VECTOR(1536)` em `fragmentos`; popular com sentence-transformers
- [ ] **Admin UI**: Migrar LLM providers para tabela `llm_providers` quando houver Django Admin
- [ ] **Reprocessamento**: Implementar UI para marcar fragmentos como `status='pending'` novamente
- [ ] **Alertas**: Se custo diário ultrapassa limite, enviar notificação

---

**Status**: ✅ Implementado e testando
**Responsável**: Modulo 4 BatchWorker (thread contínua)
**Próximo**: Módulo 5 (relações entre entidades), Módulo 7 (embeddings)
