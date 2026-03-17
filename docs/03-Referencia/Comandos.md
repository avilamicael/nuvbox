---
title: Comandos Disponíveis
tags: [referencia, comandos, makefile, docker, cli]
aliases: [Makefile Commands, CLI]
---

# 🔧 Comandos Disponíveis

Referência rápida de todos os comandos disponíveis.

## 📦 Docker Compose

### Iniciar
```bash
# Iniciar em background
docker-compose up -d

# Iniciar com modo dev (hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Iniciar com logs visíveis
docker-compose up
```

### Parar
```bash
# Parar (dados preservados)
docker-compose down

# Parar e remover volumes (⚠️ DELETA TUDO)
docker-compose down -v

# Parar apenas backend
docker-compose stop backend
```

### Logs
```bash
# Ver logs do backend
docker-compose logs backend

# Seguir logs em tempo real
docker-compose logs -f backend

# Últimas 100 linhas
docker-compose logs backend --tail 100

# Todos os serviços
docker-compose logs -f
```

### Status
```bash
# Status dos containers
docker-compose ps

# Uso de recursos
docker stats

# Tamanho dos volumes
docker system df
```

---

## 🎯 Makefile (Atalhos)

### Básico
```bash
# Iniciar serviços
make up

# Parar serviços
make down

# Ver logs do backend
make logs

# Limpar logs locais
make clean
```

### Testes
```bash
# Listar dispositivos de áudio
make test

# Testar conexão com banco de dados
make test-db

# Ver estatísticas do banco
make db-stats

# Contar transcrições
make test-transcription
```

### Banco de Dados
```bash
# Fazer backup do banco
make db-backup

# Resetar banco (⚠️ DELETA TUDO)
make db-reset

# Acessar banco via psql
make shell-db
```

### Limpeza
```bash
# Remover logs
make clean

# Reset completo (⚠️ DELETA DADOS + LOGS)
make reset
```

### Shell
```bash
# Acessar container backend
make shell
```

---

## 🧪 Scripts

### Health Check
```bash
# Verificar saúde do sistema
./scripts/healthcheck.sh
```

**Mostra:**
- Status Docker
- Status containers
- Conexão com banco
- Dispositivos de áudio
- Logs recentes
- Estatísticas do banco

### Teste Alexa
```bash
# Testar webhook Alexa
./scripts/test_alexa.sh
```

**Faz:**
- Valida endpoint
- Envia texto teste
- Verifica se foi armazenado

---

## 🔍 Diagnóstico

### Verificar Aplicação
```bash
# Health endpoint
curl http://localhost:5001/health

# Ver último erro
docker-compose logs backend | tail -20
```

### Verificar Banco de Dados
```bash
# Conectar como cerebro
docker-compose exec postgres psql -U cerebro -d cerebro_db

# Ver número de transcrições
SELECT COUNT(*) FROM transcricoes;

# Ver últimas 5
SELECT id, fonte, LEFT(texto, 50), criado_em
FROM transcricoes ORDER BY id DESC LIMIT 5;
```

### Verificar Microfone
```bash
# Listar dispositivos
docker-compose run --rm backend \
  python -c "import sounddevice as sd; print(sd.query_devices())"

# Teste de áudio (local)
arecord -d 3 test.wav  # Linux
ffmpeg -f dshow -i audio="Microphone" -t 3 test.wav  # Windows
```

---

## 🚀 Desenvolvimento

### Editar Código
```bash
# Iniciar com hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -f

# Código em backend/ recarrega automaticamente
```

### Lint
```bash
# Verificar código Python
docker-compose run --rm backend python -m py_compile backend/*.py backend/**/*.py
```

---

## 🗑️ Limpeza

### Remover Dados Específicos
```bash
# Deletar transcrições antigas (30+ dias)
docker-compose exec postgres psql -U cerebro -d cerebro_db << EOF
DELETE FROM transcricoes WHERE criado_em < NOW() - INTERVAL '30 days';
VACUUM transcricoes;
EOF

# Resetar banco inteiro (⚠️)
docker-compose exec postgres psql -U cerebro -d cerebro_db -c "TRUNCATE transcricoes;"
```

### Limpeza do Docker
```bash
# Remover imagens não usadas
docker image prune

# Remover containers parados
docker container prune

# Remover volumes não usados
docker volume prune

# Limpeza total (⚠️)
docker system prune -a --volumes
```

---

## 📋 Cheat Sheet

| Tarefa | Comando |
|--------|---------|
| Iniciar | `docker-compose up -d` |
| Parar | `docker-compose down` |
| Logs | `docker-compose logs -f backend` |
| Status | `docker-compose ps` |
| Backup | `make db-backup` |
| Health | `./scripts/healthcheck.sh` |
| BD Query | `make shell-db` |
| Remover logs | `make clean` |

---

## 🔗 Ver Também

- [[Diagnostico|Diagnóstico]]
- [[Erros-Comuns|Erros Comuns]]
- [[INDEX|Índice]]

---

#referencia #comandos #makefile #docker #cli
