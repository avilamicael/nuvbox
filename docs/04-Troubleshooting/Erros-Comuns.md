---
title: Erros Comuns e Soluções
tags: [troubleshooting, erros, solucoes, faq]
aliases: [Erros, Problemas Comuns]
---

# ❌ Erros Comuns e Soluções

Lista de problemas frequentes e como resolvê-los.

## 🗂️ Por Categoria

## 🐘 PostgreSQL / Banco de Dados

### "connection refused: 127.0.0.1:5432"
**Problema**: Backend não consegue conectar no PostgreSQL

**Soluções**:
```bash
# 1. Verificar se postgres está rodando
docker-compose ps | grep postgres

# 2. Se não está rodando:
docker-compose restart postgres
sleep 10

# 3. Verificar logs do postgres
docker-compose logs postgres

# 4. Se ainda não funciona:
docker-compose down
docker-compose up -d
```

### "PostgreSQL is unhealthy"
**Problema**: Container postgres parou ou está corrompido

**Solução**:
```bash
# Remover volume (⚠️ DELETA DADOS)
docker-compose down -v

# Recria banco
docker-compose up -d
```

### "Disco cheio" / ENOSPC
**Problema**: Sem espaço em disco

**Solução**:
```bash
# Ver tamanho
df -h
docker system df

# Deletar transcrições antigas
docker-compose exec postgres psql -U cerebro -d cerebro_db << EOF
DELETE FROM transcricoes WHERE criado_em < NOW() - INTERVAL '30 days';
VACUUM transcricoes;
EOF

# Aumentar espaço em disco (VM/nuvem)
```

---

## 🎤 Microfone / Áudio

### "No audio devices found"
**Problema**: Microfone não está sendo detectado

**Causa possível**: Errado `MIC_DEVICE_ID` em `.env`

**Solução**:
```bash
# Listar dispositivos
docker-compose run --rm backend \
  python -c "import sounddevice as sd; print(sd.query_devices())"

# Encontre seu microfone (procure por "Microphone" ou "Input")
# Note o número (ex: 0, 1, 2, etc)

# Edit .env
nano .env
# Mude: MIC_DEVICE_ID=0  → MIC_DEVICE_ID=<seu_numero>

# Reinicie
docker-compose restart backend
```

### "sounddevice: portaudio.so not found"
**Problema**: Libportaudio não instalada

**Solução**: Não deve acontecer em Docker, mas se acontecer:
```bash
docker-compose build --no-cache
docker-compose up -d
```

### "Sem som no microfone"
**Problema**: Sistema roda mas não detecta áudio

**Verificação**:
```bash
# Teste manual de áudio (Linux)
arecord -d 3 test.wav
play test.wav

# Verificar níveis (Linux)
alsamixer

# Verificar se o docker consegue acessar /dev/snd
docker-compose run --rm backend ls -la /dev/snd
```

---

## 🤖 Whisper / Transcrição

### "Failed to download model"
**Problema**: Whisper não conseguiu baixar o modelo

**Causas**: Sem internet, sem espaço em disco, firewall

**Solução**:
```bash
# Verificar internet
ping 8.8.8.8

# Verificar espaço
df -h

# Reintentar
docker-compose restart backend
docker-compose logs -f backend  # Aguarde download

# Se timeout, tente modelo menor:
nano .env
# Mude: WHISPER_MODEL=small → WHISPER_MODEL=tiny
docker-compose restart backend
```

### "Transcrição muito lenta"
**Problema**: Demora muito para transcrever

**Esperado?**:
- tiny: 1-2s por 10s áudio
- base: 2-3s
- small: 4-6s (padrão)
- medium: 15-20s
- large: 30s+ (precisa GPU)

**Solução** - Usar modelo menor:
```bash
nano .env
# WHISPER_MODEL=tiny  # Mais rápido
docker-compose restart backend
```

### "Queue full, dropping transcription"
**Problema**: Fila cheio, transcrições perdidas

**Causa**: Sistema não consegue processar rápido o suficiente

**Solução**:
```bash
# Usar modelo menor
nano .env
WHISPER_MODEL=tiny
docker-compose restart backend

# Ou aumentar tamanho da fila
nano config.py
# RAW_AUDIO_QUEUE_MAX_SIZE=200  # era 100
# TEXT_QUEUE_MAX_SIZE=200
```

---

## 🐳 Docker

### "Cannot connect to Docker daemon"
**Problema**: Docker não está rodando

**Solução**:
```bash
# Mac/Windows: Abra Docker Desktop
# Linux: Inicie o serviço
sudo systemctl start docker

# Verifique
docker ps
```

### "Permission denied while trying to connect"
**Problema**: Usuário sem permissão para Docker (Linux)

**Solução**:
```bash
# Adicione user ao grupo docker
sudo usermod -aG docker $USER

# Aplique novo grupo (sem fazer logout)
newgrp docker

# Teste
docker ps
```

### "Build failed"
**Problema**: Dockerfile não compilou

**Solução**:
```bash
# Rebuild sem cache
docker-compose build --no-cache

# Se falhar, ver erro completo
docker-compose build --no-cache 2>&1 | tail -100
```

---

## 🔧 Geral / Altro

### "Command 'docker-compose' not found"
**Problema**: docker-compose não instalado

**Solução**:
- **Mac/Windows**: Use Docker Desktop (inclui compose)
- **Linux**: `sudo apt install docker-compose` ou `pip install docker-compose`

### "Port 5001 already in use"
**Problema**: Outra aplicação está usando porta 5001

**Solução**:
```bash
# Encontrar o processo
lsof -i :5001
netstat -tlnp | grep 5001

# Opção A: Matar processo
kill -9 <PID>

# Opção B: Usar porta diferente
nano .env
FLASK_PORT=5002
docker-compose down
docker-compose up -d
```

### "Too many open files"
**Problema**: Limite de arquivo aberto excedido

**Solução** (Linux):
```bash
# Ver limite
ulimit -n

# Aumentar
ulimit -n 4096

# Permanente: Editar /etc/security/limits.conf
```

---

## 📋 Checklist de Diagnóstico

Se nenhuma solução acima funciona, execute:

```bash
# 1. Health check
./scripts/healthcheck.sh > debug_health.txt 2>&1

# 2. Status dos containers
docker-compose ps > debug_ps.txt

# 3. Logs do backend
docker-compose logs backend > debug_backend.log

# 4. Logs do postgres
docker-compose logs postgres > debug_postgres.log

# 5. Informações do sistema
docker system info > debug_docker.txt
df -h >> debug_docker.txt

# 6. Variáveis de env
cat .env > debug_env.txt

# Envie esses arquivos para suporte
```

---

## 🔗 Ver Também

- [[Diagnostico|Diagnóstico Avançado]]
- [[Comandos|Comandos]]
- [[FAQ|FAQ]]
- [[Implantacao-Clientes|Implantação]]

---

**Não encontrou seu problema?** → [[Diagnostico|Leia Diagnóstico]]

---

#troubleshooting #erros #solucoes #faq
