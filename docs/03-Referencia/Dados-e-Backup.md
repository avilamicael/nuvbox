---
title: Dados e Backup
description: Onde estão os dados, como acessar, backup e migração para VPS
tags: #dados #backup #postgresql #vps #migration
aliases:
  - Estrutura de Dados
  - Backup de Dados
---

# Dados e Backup

## 📁 Localização dos Dados

Os dados do Jarvis são salvos em **`./data/postgres/`** (raiz do projeto):

```
nuvbox/
├── data/
│   └── postgres/          ← ✅ TODOS OS DADOS AQUI
│       ├── base/
│       ├── global/
│       ├── pg_wal/
│       ├── postgresql.conf
│       └── ... (arquivos do PostgreSQL)
├── backend/
├── frontend/
├── docker-compose.yml
└── ...
```

### Por que aqui?

- **Fácil Backup**: Pasta local na raiz, não em volume Docker oculto
- **Portável**: Copie `data/` inteira para migrar para VPS
- **Versionável**: Caso queira, pode fazer snapshot antes de mudanças
- **Controle Total**: Você governa os dados, não o Docker

---

## 📊 Estrutura de Dados

### Banco de Dados: PostgreSQL

```sql
Database: jarvis_db
User: jarvis
Host: postgres (dentro de Docker)
Port: 5432

Tabela Principal: transcricoes
├── id (BIGSERIAL PRIMARY KEY)
├── texto (TEXT) - Transcrição
├── fonte (VARCHAR) - 'alexa' | 'mic_usb'
├── criado_em (TIMESTAMP) - Data/hora da transcrição
├── duracao_ms (INTEGER) - Duração em ms (NULL para Alexa)
├── modelo_whisper (VARCHAR) - Qual modelo Whisper foi usado
├── idioma (VARCHAR) - Idioma detectado
├── sessao_id (VARCHAR) - ID da sessão Alexa
└── metadados (JSONB) - Dados extras para Módulos 4-7
```

### Índices

```sql
idx_transcricoes_fonte      → Buscar por fonte (mic_usb, alexa)
idx_transcricoes_criado_em  → Buscar por data
idx_transcricoes_sessao_id  → Buscar por sessão Alexa
```

---

## 🔍 Como Acessar os Dados

### Opção 1: Via psql (CLI)

```bash
# Conectar ao banco
docker exec jarvis-postgres psql -U jarvis -d jarvis_db

# Dentro do psql:
jarvis_db=# SELECT COUNT(*) FROM transcricoes;
jarvis_db=# SELECT id, fonte, texto, criado_em FROM transcricoes ORDER BY id DESC LIMIT 10;
jarvis_db=# SELECT * FROM transcricoes WHERE fonte='alexa';
```

### Opção 2: Via Python

```python
import psycopg2

conn = psycopg2.connect(
    dbname="jarvis_db",
    user="jarvis",
    password="sua_senha",
    host="localhost",
    port=5432
)

cursor = conn.cursor()
cursor.execute("SELECT id, texto, fonte, criado_em FROM transcricoes ORDER BY id DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()
```

### Opção 3: Via Docker (sem instalar psql localmente)

```bash
# Listar todas as transcrições
docker exec jarvis-postgres psql -U jarvis -d jarvis_db \
  -c "SELECT id, fonte, LEFT(texto, 80) as preview FROM transcricoes ORDER BY id DESC;"

# Contar por fonte
docker exec jarvis-postgres psql -U jarvis -d jarvis_db \
  -c "SELECT fonte, COUNT(*) as total FROM transcricoes GROUP BY fonte;"

# Exportar para CSV
docker exec jarvis-postgres psql -U jarvis -d jarvis_db \
  -c "COPY (SELECT * FROM transcricoes ORDER BY id DESC) TO STDOUT WITH CSV HEADER;" > transcricoes.csv
```

---

## 💾 Backup

### Backup Manual (Full)

```bash
# Backup completo do PostgreSQL
docker exec jarvis-postgres pg_dump -U jarvis -d jarvis_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar de um backup
docker exec -i jarvis-postgres psql -U jarvis -d jarvis_db < backup_20260317_165000.sql
```

### Backup da Pasta data/

```bash
# Backup da pasta inteira (para migração)
tar -czf jarvis_dados_backup_$(date +%Y%m%d).tar.gz ./data/postgres/

# Restaurar
tar -xzf jarvis_dados_backup_20260317.tar.gz
```

### Backup Automático (Cron)

Adicione ao `crontab`:

```bash
# Daily backup at 2 AM
0 2 * * * cd /home/micael/nuvbox && docker exec jarvis-postgres pg_dump -U jarvis -d jarvis_db > backups/backup_$(date +\%Y\%m\%d).sql
```

---

## 🚀 Migração para VPS

### Passo 1: Backup Local

```bash
cd /home/micael/nuvbox

# Backup do banco
docker exec jarvis-postgres pg_dump -U jarvis -d jarvis_db > backup_vps.sql

# Backup da pasta data (alternativa)
tar -czf jarvis_data.tar.gz ./data/postgres/
```

### Passo 2: Enviar para VPS

```bash
# Via SCP
scp backup_vps.sql user@seu-vps.com:/home/user/nuvbox/
scp jarvis_data.tar.gz user@seu-vps.com:/home/user/nuvbox/

# Ou via SFTP/rsync
rsync -avz ./data/postgres/ user@seu-vps.com:/home/user/nuvbox/data/postgres/
```

### Passo 3: Restaurar na VPS

```bash
# Via SQL dump
docker exec -i jarvis-postgres psql -U jarvis -d jarvis_db < backup_vps.sql

# Ou via pasta completa
tar -xzf jarvis_data.tar.gz
docker-compose down
docker-compose up -d
```

---

## 📈 Monitoramento

### Tamanho do Banco

```bash
# Tamanho total
docker exec jarvis-postgres psql -U jarvis -d jarvis_db \
  -c "SELECT pg_size_pretty(pg_database_size('jarvis_db')) as tamanho;"

# Por tabela
docker exec jarvis-postgres psql -U jarvis -d jarvis_db \
  -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as tamanho FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

### Número de Registros

```bash
docker exec jarvis-postgres psql -U jarvis -d jarvis_db \
  -c "SELECT fonte, COUNT(*) as quantidade FROM transcricoes GROUP BY fonte ORDER BY quantidade DESC;"
```

### Últimas Transcrições

```bash
docker exec jarvis-postgres psql -U jarvis -d jarvis_db \
  -c "SELECT id, fonte, criado_em, LEFT(texto, 100) as texto FROM transcricoes ORDER BY id DESC LIMIT 10;"
```

---

## ⚙️ Variáveis de Conexão

```ini
# .env ou docker-compose.yml
DB_HOST=postgres          # (docker) ou localhost (local)
DB_PORT=5432
DB_USER=jarvis
DB_PASSWORD=sua_senha
DB_NAME=jarvis_db
```

Para desenvolvimento **fora do Docker**:
```bash
export DB_HOST=localhost
python backend/main.py
```

---

## 🛡️ Segurança

### Não Committar Dados

```bash
# Já está ignorado em .gitignore:
data/
postgres_data/
.env
```

### Controle de Acesso

```bash
# Permissões da pasta
chmod 700 ./data/postgres/    # Só o owner (postgres) pode acessar
```

### Backup da .env

```bash
# Manter cópia segura da senha (NÃO NO GIT)
cp .env backup/.env.seguro
chmod 600 backup/.env.seguro
```

---

**Tags**: #dados #postgresql #backup #vps #segurança
