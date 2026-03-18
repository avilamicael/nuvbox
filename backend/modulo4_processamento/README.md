# 🤖 Módulo 4 — Processamento IA com GPT-4o mini

Extração de entidades, tópicos e importância de transcrições usando OpenAI GPT-4o mini.

## 📁 Estrutura de Arquivos

```
modulo4_processamento/
├── __init__.py                  # Export: BatchWorker
├── batch_worker.py              # Thread principal — polling loop + orquestração
├── openai_client.py             # Wrapper OpenAI SDK com retry exponencial (3x)
├── prompt_builder.py            # Constrói system prompt + user message do lote
├── response_parser.py           # Parse + validação JSON com 3 níveis de fallback
├── db_queries.py                # Todas as queries SQL do Módulo 4
├── cost_tracker.py              # Controle de custo diário
├── schema_migration.sql         # ALTER TABLE transcricoes + novas tabelas
├── user_profile.yaml            # Perfil do usuário (Módulo 0 mínimo)
└── README.md                    # Este arquivo
```

## 🚀 Início Rápido

### 1. Instalar Dependências

```bash
pip install -r ../requirements.txt
```

### 2. Configurar Variáveis de Ambiente

```bash
# Copy e editar .env
cp ../.env.example .env

# Adicionar:
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
MODULO4_BATCH_SIZE=15
MODULO4_POLL_INTERVAL_SECONDS=180
MODULO4_IMPORTANCE_THRESHOLD=0.25
MODULO4_DAILY_COST_LIMIT_USD=2.00
MODULO4_DRY_RUN=false
```

### 3. Testar (Dry Run)

```bash
# Sem OpenAI API, apenas validação de prompt + parser
python scripts/test_modulo4_dryrun.py
```

### 4. Deploy

```bash
# Com Docker
docker-compose up

# Ou localmente (com PostgreSQL rodando)
python backend/main.py
```

## 📊 Fluxo de Dados

```
transcricoes (status='pending')
    ↓ (BatchWorker polling a cada 3 min)
OpenAI GPT-4o mini API
    ↓ (extrai: resumo, importance, tópicos, entidades)
Response Parser (3 níveis de fallback)
    ↓
fragmentos + entidades + topicos + links
    ↓
modulo4_uso_diario (cost tracking)
```

## 🔑 Componentes Principais

### batch_worker.py

**Responsabilidade**: Orquestração principal

- Polling para transcricoes com `status='pending'`
- Batch de 15 transcrições
- Chamada OpenAI com retry exponencial
- Parse JSON com fallback
- Persistência em banco de dados
- Tracking de custo diário

**Thread Pattern**:
```python
while not is_shutdown_requested():
    pending = db_queries.fetch_pending_transcriptions(batch_size=15)
    if pending:
        response = openai_client.call_with_retry(...)
        parsed = ResponseParser.parse_response(...)
        for result in parsed['resultados']:
            save_fragment(result)
    time.sleep(180)  # 3 minutos
```

### openai_client.py

**Responsabilidade**: Abstração OpenAI API

- Inicialização com API key
- Chamadas síncronas com retry (exponential backoff)
- Cálculo de custo (input + output tokens)
- Tratamento de erros específicos

**Preços GPT-4o mini**:
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

### prompt_builder.py

**Responsabilidade**: Construção de prompts

- Carregamento YAML do perfil de usuário
- System prompt com contextos do usuário
- User message com lote em JSON

**Exemplo de Entrada**:
```json
{
  "quantidade": 3,
  "transcricoes": [
    {"idx": 0, "id": 1001, "texto": "Reunião do Cerebro..."},
    {"idx": 1, "id": 1002, "texto": "Fui ao médico..."},
    {"idx": 2, "id": 1003, "texto": "Aprendi machine learning..."}
  ]
}
```

### response_parser.py

**Responsabilidade**: Parse + validação JSON com fallback

**3 Níveis de Fallback**:
1. `json.loads()` direto
2. Regex para extrair bloco `{...}`
3. Marca batch como erro (individual reprocessing próximo ciclo)

**Validação**:
- Índices sequenciais
- Importance score em [0.0, 1.0]
- Tipos de entidade validados
- Contexto não vazio

### db_queries.py

**Responsabilidade**: Todas as queries SQL

Funções principais:
- `fetch_pending_transcriptions()` — Buscar pendentes
- `mark_processing()` / `mark_processed()` / `mark_skipped()` / `mark_error()` — Status
- `save_fragment()` — Inserir fragmento
- `upsert_entidade()` — Deduplicação de entidades
- `upsert_topico()` — Tópicos hierárquicos
- `save_fragmento_entidade()` / `save_fragmento_topico()` — Relacionamentos

### cost_tracker.py

**Responsabilidade**: Controle de custo diário

- `check_and_log_cost()` — Valida limite + persiste em BD
- `get_daily_usage()` — Consulta stats do dia

**Limite Padrão**: $2.00/dia (ajustável em .env)

### schema_migration.sql

**Responsabilidade**: Alterações no schema

**ALTER TABLE transcricoes**:
- `status` (pending → processing → processed/skipped/error)
- `processado_em` (timestamp)
- `modulo4_erro` (mensagem de erro)

**Novas Tabelas**:
- `fragmentos` — Resumos + importance scores
- `entidades` — Pessoas, empresas, projetos, conceitos
- `topicos` — Hierarquia (ex: "Trabalho > Cerebro > Bugs")
- `fragmento_entidade` — N:M com contexto
- `fragmento_topico` — N:M com confiança
- `entidade_entidade` — Grafo de relacionamentos
- `modulo4_uso_diario` — Cost tracking

### user_profile.yaml

**Responsabilidade**: Perfil estático do usuário (Módulo 0)

```yaml
usuario:
  nome: "Micael"

contextos:
  trabalho:
    palavras_chave: ["Cerebro", "código", "bug", ...]

entidade_tipos:
  - "pessoa"
  - "empresa"
  - "projeto"
  - ...
```

## 📈 Monitoring

### Logs Esperados

```
BatchWorker started
✅ BatchWorker initialized
Processing batch of 15 transcriptions...
✅ OpenAI call succeeded | input=1200 output=450 tokens
✅ Level 1 parse: Direct json.loads() succeeded
Processed: fragmento_id=42, topicos=2, entidades=3
✅ Batch processed: 12 saved, 3 skipped
```

### Queries Úteis

```sql
-- Custo diário
SELECT data, custo_usd FROM modulo4_uso_diario ORDER BY data DESC LIMIT 7;

-- Entidades mais frequentes
SELECT nome, tipo, frequencia FROM entidades ORDER BY frequencia DESC LIMIT 20;

-- Erros recentes
SELECT id, texto, modulo4_erro FROM transcricoes
WHERE status = 'error' ORDER BY processado_em DESC LIMIT 10;
```

## ⚙️ Configuração Avançada

### Variáveis de Ambiente

| Var | Padrão | Descrição |
|-----|--------|-----------|
| `OPENAI_API_KEY` | (required) | Chave API OpenAI |
| `OPENAI_MODEL` | gpt-4o-mini | Modelo (gpt-4o-mini, gpt-4o) |
| `MODULO4_BATCH_SIZE` | 15 | Transcrições por lote |
| `MODULO4_POLL_INTERVAL_SECONDS` | 180 | Polling interval (3 min) |
| `MODULO4_IMPORTANCE_THRESHOLD` | 0.25 | Score mínimo para salvar |
| `MODULO4_DAILY_COST_LIMIT_USD` | 2.00 | Limite diário ($) |
| `MODULO4_MAX_RETRIES` | 3 | Tentativas com backoff |
| `MODULO4_DRY_RUN` | false | true = sem INSERT no banco |

### Customização de Perfil

Editar `user_profile.yaml` para ajustar:
- Nome do usuário
- Contextos (trabalho, pessoal, estudos, etc.)
- Tipos de entidade
- Boosts de importância específicos

## 🔐 Proteções Implementadas

1. **Anti-Reprocessamento Duplo**: Reset de records presos em `processing` > 10 min
2. **Limite de Custo**: Bloqueia se `projected_cost > $2.00/dia`
3. **Retry Exponencial**: 3 tentativas com backoff em RateLimit/API errors
4. **Parser Robusto**: 3 níveis de fallback para JSON parsing
5. **Graceful Shutdown**: `join(timeout=10)` para requests OpenAI

## 📚 Documentação Completa

- [[Modulo4-Processamento-IA]] — Overview do módulo
- [[Modulo4-Prompt-Engineering]] — Decisões + histórico
- [[Modulo4-Schema-SQL]] — Detalhamento de tabelas
- `scripts/test_modulo4_dryrun.py` — Teste sem OpenAI API
- `scripts/sample_transcricoes.txt` — Dados de teste

## 🚀 Próximas Etapas

- Módulo 5: Query interface para buscar por tópico/entidade
- Módulo 7: Embeddings + similarity search com pgvector
- Fine-tuning do prompt baseado em feedback
- Interface web para editar user_profile.yaml

## 🆘 Troubleshooting

### "No module named 'openai'"

```bash
pip install openai==1.3.9 PyYAML==6.0.1
```

### "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY=sk-...
```

### "Cost limit exceeded"

Aumentar `MODULO4_DAILY_COST_LIMIT_USD` em .env

### "Batch parsing failed (Level 2)"

Transcrições individuais serão reprocessadas no próximo ciclo (Level 3 fallback)

---

**Status**: ✅ MVP Completo — Pronto para Produção

Data: 2024-03-17
