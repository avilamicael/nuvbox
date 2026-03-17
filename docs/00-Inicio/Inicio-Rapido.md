---
title: Início Rápido - 5 Minutos
tags: [rapido, setup, guia, instalacao]
aliases: [Início Rápido, Quick Start]
---

# ⚡ Início Rápido - 5 Minutos

Configuração completa do zero até rodando. Sem complexidade.

## 📋 Pré-requisitos (1 minuto)

Instale **Docker**:
- **Mac/Windows**: https://www.docker.com/products/docker-desktop
- **Linux**: `curl -fsSL https://get.docker.com | sh`

Verifique:
```bash
docker --version
docker-compose --version
```

## 🚀 4 Passos (4 minutos)

### 1️⃣ Preparar (1 minuto)
```bash
cd /home/micael/nuvbox
cp .env.example .env
```

### 2️⃣ Configurar (2 minutos)
```bash
nano .env
```

**Edite apenas estas 2 linhas:**

```env
# Linha 2
DB_PASSWORD=sua_senha_forte_aqui

# Linha 19
ALEXA_WEBHOOK_SECRET=sua_chave_secreta_aqui
```

Salve: `Ctrl+X` → `Y` → `Enter`

### 3️⃣ Iniciar (1 minuto)
```bash
docker-compose up -d
sleep 10
```

### 4️⃣ Verificar (menos de 1 minuto)
```bash
docker-compose logs backend
```

Procure por:
```
✅ JARVIS BACKEND RODANDO
🎤 Microfone: escutando fala
📊 Banco de dados: armazenando transcrições
```

## ✅ Sucesso!

Sistema está rodando. Pronto para usar.

## 🧪 Testar

### Teste de Microfone
```bash
# Fale 3 segundos no seu microfone
# Depois execute:
docker-compose logs backend | grep "Transcribed"
```

### Teste de Banco de Dados
```bash
docker-compose exec postgres psql -U jarvis -d jarvis_db \
  -c "SELECT COUNT(*) FROM transcricoes;"
```

## 🛑 Parar

```bash
docker-compose down
```

Dados são preservados.

## 🆘 Problemas?

### PostgreSQL não inicia
```bash
docker-compose down
docker-compose up -d
sleep 10
docker-compose logs
```

### Microfone não encontrado
```bash
docker-compose run --rm backend \
  python -c "import sounddevice as sd; print(sd.query_devices())"
```

Encontre seu dispositivo, mude `MIC_DEVICE_ID` em `.env`, reinicie.

### Mais ajuda
→ Veja [[Erros-Comuns|Erros Comuns]]
→ Execute `./scripts/healthcheck.sh`

## 📖 Próximas Leituras

- [[Arquitetura-Geral|Entender Arquitetura]] (desenvolvimento)
- [[Implantacao-Clientes|Implantar em Clientes]] (produção)
- [[Variaveis-Ambiente|Configuração Completa]] (referência)

## 📚 Índice

- [[00-Comece-Aqui|← Comece Aqui]]
- [[INDEX|↑ Índice Completo]]

---

**Tudo pronto!** 🎉

Seus próximos passos:
1. Entender como funciona: [[Arquitetura-Geral|Arquitetura]]
2. Para clientes: [[Implantacao-Clientes|Implantação]]
3. Precisa de ajuda: [[Erros-Comuns|Troubleshooting]]

---

#rapido #setup #guia #instalacao #jarvis
