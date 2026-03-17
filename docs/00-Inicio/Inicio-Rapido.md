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

### Teste de Webhook (qualquer SO)
```bash
make webhook-test
# Ou:
curl -s -X POST http://localhost:5001/webhook/text \
  -H "Content-Type: application/json" \
  -H "X-Jarvis-Secret: mude_antes_do_ngrok" \
  -d '{"text":"teste","source":"manual","timestamp":"2026-01-01T00:00:00Z"}'
```

### Ver registros salvos
```bash
make db-recent
```

---

## 🎤 Captura de Microfone

> O Docker **não tem acesso** ao microfone da máquina. Para capturar áudio, use o script cliente.

### No Windows (PowerShell — fora do WSL2)

```powershell
# 1. Instalar dependências (apenas 1ª vez)
pip install sounddevice numpy requests silero-vad python-dotenv
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
pip install openai-whisper

# 2. Ir para a pasta do projeto
cd C:\Users\SeuUsuario\nuvbox

# 3. Listar microfones disponíveis
python clients\windows_mic_sender.py --list-devices

# 4. Rodar (lê configurações do .env automaticamente)
python clients\windows_mic_sender.py
```

O script usa as variáveis do `.env`:
```env
BACKEND_URL=http://localhost:5001   # onde está o backend
CLIENT_SOURCE_ID=windows_mic        # como esta máquina aparece no banco
```

### No Linux (sem Docker)

```bash
# Terminal 1: PostgreSQL em Docker + Backend local
docker-compose up -d postgres
DB_HOST=localhost python backend/main.py

# O microfone USB é capturado diretamente
```

> Ver [[Windows-Mic-Sender-Setup|Setup Completo Windows]] e [[Deployment-Docker-vs-Local|Docker vs Local]] para mais detalhes.

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
