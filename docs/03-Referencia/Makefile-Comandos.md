---
title: Makefile - Comandos Úteis
description: Referência rápida de comandos do Makefile para gerenciar o Cerebro
tags: #makefile #comandos #docker #database
aliases:
  - Comandos Make
  - Make Commands
---

# Makefile - Comandos Úteis

Um **Makefile** simplifica a execução de tarefas repetitivas. Em vez de digitar comandos longos, use `make comando`.

## Menu de Ajuda

```bash
make help
```

Mostra todos os comandos disponíveis com descrição.

---

## 🐳 Containers (Docker)

### Iniciar

```bash
make up
```
Inicia PostgreSQL + backend em background. Aguarda 2 segundos e mostra status.

**Output esperado:**
```
✅ Services starting...
NAME              IMAGE           STATUS
cerebro-postgres   postgres:15     Up 2 seconds (healthy)
cerebro-backend    nuvbox-backend  Up 2 seconds
```

### Parar

```bash
make down
```
Para todos os containers.

### Ver Logs

```bash
# Backend logs (em tempo real)
make logs

# PostgreSQL logs
make logs-postgres
```

---

## 📊 Banco de Dados & Dados

### Ver Tamanho do Banco

```bash
make db-size
```

**Output:**
```
Database size...
 tamanho
----------
 7615 kB
```

### Últimas Transcrições

```bash
make db-recent
```

Mostra os 10 últimos registros com preview do texto.

**Output:**
```
 id |         preview         | fonte |           criado_em
----+-------------------------+-------+-------------------------------
  1 | dados em pasta data/    | alexa | 2026-03-17 16:57:53.537863+00
```

### Estatísticas

```bash
make db-stats
```

Mostra contagem, primeira e última transcrição por fonte.

**Output:**
```
 fonte | count |           first_at            |            last_at
-------+-------+-------------------------------+-------------------------------
 alexa |     1 | 2026-03-17 16:57:53.537863+00 | 2026-03-17 16:57:53.537863+00
```

### Acessar PostgreSQL Direto

```bash
make shell-db
```

Abre shell `psql` para queries customizadas.

**Exemplos de queries dentro do shell:**
```sql
-- Ver todas as tabelas
\dt

-- Contar registros
SELECT COUNT(*) FROM transcricoes;

-- Ver últimos registros
SELECT * FROM transcricoes ORDER BY id DESC LIMIT 5;

-- Sair
\q
```

### Backup do Banco

```bash
make db-backup
```

Cria arquivo `backup_YYYYMMDD_HHMMSS.sql` com dump do banco.

```bash
# Restaurar de um backup
docker-compose exec -i postgres psql -U cerebro -d cerebro_db < backup_20260317_165900.sql
```

---

## 🧪 Testes

### Testar Microphone

```bash
make test
```

Lista todos os dispositivos de áudio disponíveis.

### Testar Webhook Alexa

```bash
make webhook-test
```

Envia um POST request ao webhook e mostra resposta.

**Output:**
```json
{
  "session_id": "make-test",
  "status": "ok"
}
```

---

## 🧹 Limpeza

### Limpar Logs Temporários

```bash
make clean
```

Remove arquivos de log em `logs/` e backups SQL antigos.

### Reset do Banco (Dados apenas)

```bash
make db-reset
```

⚠️ **CUIDADO**: Deleta TODOS os registros da tabela `transcricoes`.

Pede confirmação: `Are you sure? (type 'yes'): `

### Reset Completo

```bash
make reset
```

⚠️ **MUITO CUIDADO**:
- Para containers
- Remove volumes Docker
- Deleta logs
- Deleta backups antigos

Também pede confirmação.

---

## 📝 Exemplos de Uso

### Cenário 1: Começar o Dia

```bash
make up              # Inicia tudo
make db-stats        # Verifica quantas transcrições tem
make logs            # Vê os logs em tempo real
```

### Cenário 2: Verificar Dados

```bash
make db-size         # Quanto espaço está usando
make db-recent       # Últimas transcrições
make db-stats        # Estatísticas por fonte
```

### Cenário 3: Backup Antes de Atualizar

```bash
make db-backup       # Faz backup SQL
# Ou copiar a pasta toda:
cp -r ./data/postgres ./data/postgres.backup-2026-03-17
```

### Cenário 4: Testar Sistema

```bash
make webhook-test    # Envia webhook de teste
make db-recent       # Verifica se foi salvo
```

### Cenário 5: Migrar para VPS

```bash
make db-backup       # Cria SQL dump
# Enviar arquivo backup_*.sql para VPS e restaurar lá
```

---

## 🔧 Editando o Makefile

Todos os comandos estão em `/nuvbox/Makefile`:

```makefile
webhook-test:
	@echo "Testing Alexa webhook..."
	@curl -s -X POST http://localhost:5001/webhook/alexa \
		-H "Content-Type: application/json" \
		-H "X-Alexa-Secret: mude_antes_do_ngrok" \
		-d '{"text": "test webhook", "session_id": "make-test", "timestamp": "'$$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}' | jq .
```

**Importante**:
- Use **TABS** (não espaços) para indentar comandos no Makefile
- Adicione novo comando com `.PHONY: novo-comando`

---

## 📍 Onde Estão os Dados?

```
nuvbox/
└── data/
    └── postgres/        ← Aqui estão os dados!
        ├── base/        (tabelas e índices)
        ├── pg_wal/      (write-ahead logs)
        ├── global/      (configuração)
        └── ...
```

**Tamanho típico**: 7-50 MB (depende de quantas transcrições)

Para fazer backup da pasta toda:
```bash
tar -czf backup_data_$(date +%Y%m%d).tar.gz ./data/postgres/
```

---

**Tags**: #makefile #cli #docker #database #productivity
