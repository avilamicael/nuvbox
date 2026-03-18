---
name: Changelog — Backend (Mar 2026)
description: Histórico de mudanças estruturais e features implementadas
---

# Changelog — Backend Cerebro (Março 2026)

## [Modulo 5] ✅ 18/03/2026

### Adicionado
- **Módulo 5** (`backend/modulo5_estruturado/`): Armazenamento estruturado com desambiguação de entidades
- **EntityResolver** (`entity_resolver.py`): Match exato + fuzzy (difflib, threshold=0.85) para evitar entidades duplicatas — retorna status `ativo`, `pendente` ou `novo`
- **M5 DB queries** (`db_queries.py`): `fetch_existing_entities()`, `fetch_existing_topics()`, `save_action_items()`, `update_entity_status()`
- **Schema migration** (`schema_migration.sql`): novos campos + tabela `action_items`
- **Tabela `action_items`**: Tarefas extraídas pelo LLM com status `pendente|concluido|cancelado`

### Alterado
- **`save_fragment()`** (`modulo4/db_queries.py`): Agora aceita e persiste `sentimento`, `tem_decisao`, `tem_pergunta`
- **`BatchWorker._process_batch()`**: Busca entidades/tópicos existentes antes de chamar o LLM e injeta no prompt
- **`BatchWorker._process_result()`**: Usa `EntityResolver` para desambiguação; salva `action_items` após fragmento; passa campos M5 para `save_fragment()`
- **`PromptBuilder.build_system_prompt()`**: Aceita `existing_entities` e `existing_topics`; injeta seções "ENTIDADES CONHECIDAS" e "TÓPICOS EXISTENTES" no prompt
- **`entrypoint.sh`**: Aplica `modulo5_estruturado/schema_migration.sql` na inicialização

### Schema Mudanças
- **`fragmentos`**: Adicionados `sentimento`, `tem_decisao`, `tem_pergunta`, `usuario_id`; embedding corrigido de `VECTOR(1536)` → `VECTOR(384)` (MiniLM local, M7)
- **`entidades`**: Adicionados `descricao`, `status` (ativo/pendente/ambiguo), `usuario_id`
- **`topicos`**: Adicionados `descricao`, `status`, `usuario_id`
- **`action_items`** (nova tabela): `id`, `fragmento_id`, `texto`, `status`, `atualizado_por`, `criado_em`, `usuario_id`

---

## [Modulo 4] ✅ 18/03/2026

### Adicionado
- **BatchWorker** (`modulo4_processamento/batch_worker.py`): Thread que faz polling a cada 3min das transcrições pendentes, processa em lotes de 15 com LLM
- **OpenAI SDK v1.x wrapper** (`openai_client.py`): Suporta Groq + OpenAI com retry exponencial
- **Prompt builder** (`prompt_builder.py`): Carrega `user_profile.yaml` e constrói system prompt contextualizado
- **Response parser** (`response_parser.py`): Parse JSON com 3 níveis de fallback + validação de schema
- **Cost tracker** (`cost_tracker.py`): Rastreamento de custo diário + enforcement de limite
- **DB queries** (`db_queries.py`): Todas as operações SQL (fetch, insert, update) do Módulo 4
- **Schema migration** (`schema_migration.sql`): ALTER TABLE transcricoes + 7 novas tabelas (fragmentos, entidades, topicos, etc.)
- **User profile** (`user_profile.yaml`): Perfil estático do usuário para contexto LLM
- **Env vars**: `LLM_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`, `LLM_PROVIDER`, `MODULO4_*`
- **Config dataclass**: `LLMSettings` (era `OpenAISettings`) com `base_url`, `provider`, custo

### Removido
- **MicrophoneSource** (modulo1_input/mic_source.py): Backend não mais captura áudio localmente
- **TranscriptionWorker** (modulo2_transcricao/transcription_worker.py): Whisper agora roda no cliente (Pinky)
- **raw_audio_queue**: Pipeline reduzido (webhook text → text_queue → StorageWorker)
- Código de inicialização desses workers em `main.py`

### Alterado
- **main.py**: Removidas 50+ linhas de setup local (mic capture, transcription). Adicionado BatchWorker init
- **config.py**: Renomeado `OpenAISettings` → `LLMSettings`; adicionado suporte a `base_url` e `provider`
- **entrypoint.sh**: Aplicação de `schema_migration.sql` após `schema.sql`
- **requirements.txt**: `openai` atualizado para `>=1.52.0` (fix para compatibilidade httpx)
- **docker-compose.yml**: Adicionadas todas env vars de Módulo 4
- **Backend entrypoint**: Webhook agora é única entrada de dados

### Bug Fixes
- ✅ OpenAI SDK v1.3.9 → v1.52.0 (fixo conflito `proxies` com httpx)
- ✅ Response parser: resumo mínimo reduzido de 5 para 1 caractere (transcrições curtas)
- ✅ CEREBRO_SECRET não era injetado no container (env var não presente no docker-compose.yml)
- ✅ pg_isready sem `-d $DB_NAME` falhava (entrypoint.sh e docker-compose.yml healthcheck)

### Schema Mudanças
- **transcricoes**: Adicionadas colunas `status` (pending/processing/processed/error), `processado_em`, `modulo4_erro`
- **Novas tabelas**:
  - `fragmentos`: Resumos + importance_score processados
  - `entidades`: Pessoas, empresas, projetos (com deduplicação case-insensitive)
  - `topicos`: Hierarquia de tópicos (com `pai_id` self-FK)
  - `fragmento_entidade`, `fragmento_topico`: N:N com metadata
  - `entidade_entidade`: Grafo de relações (para Módulo 7)
  - `modulo4_uso_diario`: Tracking de custo diário

---

## [Pinky App] ✅ 18/03/2026

### Alterado
- **http-sender.ts**: Header `X-Jarvis-Secret` → `X-Cerebro-Secret`
- **SettingsForm.tsx**: Label "Secret (X-Jarvis-Secret)" → "Secret (X-Cerebro-Secret)"

### Mantido para compatibilidade
- **backend/modulo1_input/text_webhook.py**: Aceita ambos `X-Jarvis-Secret` e `X-Cerebro-Secret` (fallback)

---

## [Infraestrutura] ✅ 18/03/2026

### Renomeação: Segurança Genérica
- **ALEXA_WEBHOOK_SECRET** → **CEREBRO_SECRET** (mais genérico, não exclusivo da Alexa)
- Atualizado em: `.env`, `.env.example`, `docker-compose.yml`, `backend/config.py`, `backend/main.py`, comentários

### Documentação
- ✅ `Modulo4-Implementacao.md`: Arquitetura, dois layers (raw vs tratado), configuração
- ✅ `CLEANUP-TODO.md`: Arquivos órfãos para remover (modulo1/2 local)
- ✅ `CHANGELOG-Backend.md`: Este arquivo

---

## Arquitetura Atual

```
┌─────────────────────┐
│  Cliente (Pinky)    │
│  ou Alexa           │
└──────────┬──────────┘
           │ POST /webhook/text
           ↓
┌──────────────────────────────────────┐
│ Backend Flask                        │
├──────────────────────────────────────┤
│ Módulo 1: text_webhook               │
│  └─ Validação (X-Cerebro-Secret)     │
│  └─ → text_queue                     │
│                                      │
│ Módulo 3: StorageWorker              │
│  └─ Consome text_queue               │
│  └─ → INSERT transcricoes (pending)  │
│                                      │
│ Módulo 4: BatchWorker (polling 3min) │
│  └─ Fetch 15 transcricoes pending    │
│  └─ Chama LLM (Groq)                 │
│  └─ → INSERT fragmentos, entidades   │
│  └─ → UPDATE transcricoes (processed)│
│                                      │
│ PostgreSQL                           │
│  ├─ transcricoes (raw)               │
│  ├─ fragmentos (tratados)            │
│  ├─ entidades, topicos, links        │
│  └─ modulo4_uso_diario               │
└──────────────────────────────────────┘
```

---

## Performance & Custo

| Métrica | Valor |
|---|---|
| Batch size | 15 transcrições |
| Polling interval | 3 minutos (configurável) |
| Retry exponencial | 3 tentativas (1s, 2s, 4s) |
| Custo (Groq) | $0.00 (free tier) |
| Custo (OpenAI) | ~$0.06/dia (500 transcrições) |
| Economy vs 1-by-1 | ~73% tokens economizados (prompt reutilizado) |

---

## Próximos Passos

1. **Módulo 5**: Relações entre entidades (entidade_entidade population)
2. **Módulo 6**: UI de query (web interface para buscar por topic/entidade)
3. **Módulo 7**: Embeddings + similarity search (pgvector + sentence-transformers)
4. **Admin**: Interface para gerenciar providers LLM, user profile, reprocessamento

---

**Maintainer**: Cerebro Backend
**Last Updated**: 2026-03-18
