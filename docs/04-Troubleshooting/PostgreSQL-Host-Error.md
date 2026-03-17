---
title: Erro de Conexão PostgreSQL - localhost vs postgres
description: Solução para erro "localhost:5432 - no response" em Docker
tags: #docker #postgresql #troubleshooting #network
aliases:
---

# Erro PostgreSQL "localhost:5432 - no response"

## Problema

Ao executar `docker-compose up`, o container `jarvis-backend` falha repetidamente com:
```
localhost:5432 - no response
Attempt 1/30...
localhost:5432 - no response
...
❌ PostgreSQL failed to start
```

O PostgreSQL está rodando e saudável, mas o backend não consegue conectar.

## Causa

O arquivo `.env` no diretório `./backend/` contém:
```bash
DB_HOST=localhost
```

Quando o entrypoint.sh monta esse arquivo como volume em `/app/.env` dentro do container e o sourca:
```bash
if [ -f /app/.env ]; then
    source /app/.env
fi
```

Ele sobrescreve a variável de ambiente `DB_HOST` que vem do docker-compose, mudando de `postgres` (nome do serviço) para `localhost` (que não existe dentro da rede Docker).

## Solução

### Opção 1: Remover o arquivo `.env` do backend (recomendado para Docker)

```bash
rm ./backend/.env
docker-compose down
docker-compose up -d
```

A docker-compose.yml já passa todas as variáveis necessárias via ambiente. O arquivo `.env` do raiz é usado apenas para desenvolvimento local.

### Opção 2: Corrigir o arquivo `.env` do backend

Se você estiver desenvolvendo localmente (fora de Docker), atualize o arquivo:
```bash
# ./backend/.env
DB_HOST=postgres      # ← Mude de "localhost" para "postgres"
                      # (ou use localhost se rodar Python diretamente na máquina host)
```

### Opção 3: Adicionar volume exclusão na docker-compose

Se quiser manter o arquivo `.env` no backend para desenvolvimento local, exclua-o do mount em Docker:
```yaml
services:
  backend:
    volumes:
      - ./backend:/app
      - ./logs:/app/logs
      - /dev/snd:/dev/snd
      - /dev/null:/app/.env   # ← Excluir o arquivo do mount
```

## Diferença: localhost vs postgres

| Contexto | Host | Motivo |
|----------|------|--------|
| **Dentro de Docker** | `postgres` | Nome do serviço na rede Docker (jarvis-network) |
| **Local (máquina host)** | `localhost` | Conexão TCP/IP via porta 5432 publicada |
| **Dentro de um container Python rodando localmente** | `localhost` | Precisa conectar via port forwarding ou bridge |

## Prevenção

1. **Nunca commitar `.env` no git** (já está em `.gitignore` e `.dockerignore`)
2. **Usar `.env.example` como referência** com comentários sobre Docker/Local
3. **Volume mount do backend deve ser lido-only** para valores como `DB_HOST` críticos:
   ```yaml
   volumes:
     - ./backend:/app:ro  # Read-only (com exceções para logs)
     - ./logs:/app/logs   # Logs com escrita
   ```

## Verificação

Confirme que o container pode resolver o hostname:
```bash
docker exec jarvis-backend pg_isready -h postgres -p 5432 -U jarvis
# Esperado: postgres:5432 - accepting connections
```

---
**Tags**: #docker #postgresql #networking #container
