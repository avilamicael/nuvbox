---
title: Setup - Windows Mic Sender
description: Como instalar e rodar o script de captura de microfone no Windows
tags: #windows #microfone #setup #cliente #instalacao
aliases:
  - Windows Setup
  - Mic Sender Windows
---

# 🪟 Setup: Windows Mic Sender

Script que roda no **Windows nativo** (fora do WSL2/Docker), captura o microfone, transcreve com Whisper e envia para o backend Cerebro.

---

## ⚠️ Pré-requisitos

### Python 3.10, 3.11 ou 3.12

> **Python 3.14 NÃO é suportado** — muitos pacotes ainda não têm builds para versões tão novas.

Verificar versão:
```powershell
python --version
```

Se for 3.13 ou 3.14, instale o Python 3.11 em:
- https://www.python.org/downloads/release/python-3119/
- Escolha "Windows installer (64-bit)"
- Marque "Add python.exe to PATH" durante a instalação

---

## 📂 Passo 1: Navegar até a pasta do projeto

O script fica em `clients/windows_mic_sender.py` dentro da pasta do projeto.

```powershell
# Navegar até o projeto (ajuste o caminho se necessário)
cd C:\Users\Usuario\nuvbox

# Confirmar que está no lugar certo
ls clients\
# Deve mostrar: windows_mic_sender.py
```

> **Erro comum:** Rodar o script de `C:\Users\Usuario` em vez de `C:\Users\Usuario\nuvbox`

---

## ⚙️ Passo 2: Configurar o .env

Toda configuração fica no `.env` da **raiz do projeto**. O script lê automaticamente de lá.

Abrir `.env` e ajustar as variáveis do cliente Windows:

```env
# URL do backend — localhost funciona se backend roda no WSL2 da mesma máquina
BACKEND_URL=http://localhost:5001

# Secret — deve ser igual ao ALEXA_WEBHOOK_SECRET no servidor
ALEXA_WEBHOOK_SECRET=mude_antes_do_ngrok

# ID desta máquina (aparece no banco no campo "fonte")
CLIENT_SOURCE_ID=windows_mic

# Microfone — rodar --list-devices para descobrir o ID
MIC_DEVICE_ID=0

# Whisper
WHISPER_MODEL=small      # tiny=rápido, small=equilibrado, medium=preciso
WHISPER_LANGUAGE=pt
```

> Nenhuma variável fica hardcoded no código. Toda mudança é feita só no `.env`.

---

## 📦 Passo 3: Instalar dependências

> **Erro comum:** `--index-url` substitui o PyPI inteiro → `sounddevice` não encontrado.
> **Correto:** usar `--extra-index-url` que *adiciona* o index do PyTorch sem substituir o PyPI.

```powershell
# Pacotes do PyPI
pip install sounddevice numpy requests silero-vad python-dotenv

# PyTorch CPU (precisa de index separado, mas não substitui o PyPI)
pip install torch --extra-index-url https://download.pytorch.org/whl/cpu

# Whisper
pip install openai-whisper
```

---

## 🧪 Passo 3: Verificar instalação

```powershell
# Listar dispositivos de áudio
python clients\windows_mic_sender.py --list-devices
```

**Output esperado:**
```
🎤 Dispositivos de áudio disponíveis:
   0 Microfone (Realtek(R) Audio), MME (2 in, 0 out)
   1 CABLE Output (VB-Audio Virtual ...), MME (2 in, 0 out)
   ...
```

---

## 🚀 Passo 4: Rodar

### Backend WSL2 rodando localmente

```powershell
# Backend em WSL2 rodando em localhost:5001
python clients\windows_mic_sender.py
```

### Backend em VPS (IP externo)

```powershell
python clients\windows_mic_sender.py --backend http://192.168.1.100:5001
```

### Opções avançadas

```powershell
# Ver todos os parâmetros
python clients\windows_mic_sender.py --help

# Escolher microfone específico (device ID da lista)
python clients\windows_mic_sender.py --device 1

# Usar modelo menor (mais rápido, menos preciso)
python clients\windows_mic_sender.py --model tiny

# Modelo maior (mais preciso, mais lento)
python clients\windows_mic_sender.py --model medium

# Mudar idioma
python clients\windows_mic_sender.py --language en
```

---

## 🔧 Troubleshooting

### `sounddevice` não encontrado

```
ERROR: No matching distribution found for sounddevice
```

**Causa:** `--index-url` substitui o índice PyPI inteiro.
**Solução:** Instalar separado sem `--index-url`:
```powershell
pip install sounddevice
```

### Arquivo não encontrado

```
can't open file 'C:\Users\Usuario\clients\windows_mic_sender.py'
```

**Causa:** Você está na pasta errada.
**Solução:**
```powershell
cd C:\Users\Usuario\nuvbox
python clients\windows_mic_sender.py
```

### Python 3.14 - pacotes não instalam

```
ERROR: Could not find a version that satisfies the requirement ...
```

**Causa:** Python 3.14 é muito novo, poucos pacotes têm wheels.
**Solução:** Instalar Python 3.11:
- Baixar em https://www.python.org/downloads/release/python-3119/
- Usar `py -3.11 clients\windows_mic_sender.py`

### Backend não conecta

```
❌ Não conseguiu conectar em http://localhost:5001
```

**Causas:**
1. Backend não está rodando — rodar `DB_HOST=localhost python backend/main.py` no WSL2
2. URL errada — conferir o IP/porta no `.env`
3. Firewall bloqueando — permitir porta 5001

### Secret inválido

```
❌ Backend retornou 401: {"error":"unauthorized"}
```

**Solução:** Passar o secret correto:
```powershell
python clients\windows_mic_sender.py --secret mude_antes_do_ngrok
```

---

## 🗂️ Onde fica o áudio capturado?

O script **não salva áudio em disco**. O fluxo é:
```
Microfone Windows → VAD (silêncio/fala) → Whisper (transcrição) → POST /webhook/text → PostgreSQL
```

Apenas o **texto transcrito** fica salvo no banco. Verificar:
```powershell
# Via WSL2
make db-recent
```

---

## 📋 Ver Também

- [[Deployment-Docker-vs-Local|Opções de Deployment]] — Quando usar Docker vs local
- [[Modulo1-Input|Módulo 1 - Input]] — Arquitetura de fontes de entrada
- [[Variaveis-Ambiente|Variáveis de Ambiente]] — Configuração do secret

---

**Tags**: #windows #microfone #setup #cliente #troubleshooting
