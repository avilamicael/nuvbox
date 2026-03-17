---
title: Arquitetura — Backend e Clientes
description: O que o backend faz hoje, como os clientes se conectam, e o caminho para um app desktop futuro
tags: [arquitetura, backend, clientes, desktop, modular]
aliases:
  - Papel do Backend
  - App Desktop
---

# 🏗️ Arquitetura — Backend e Clientes

---

## 🎯 O que o Backend faz hoje

O backend Cerebro tem **uma responsabilidade**: receber texto (ou áudio para transcrever) e salvar no banco de dados.

```
┌─────────────────────────────────────────────────────────┐
│                    BACKEND CEREBRO (Docker)                      │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │  /webhook   │    │  Transcrição │    │  PostgreSQL│  │
│  │  /text      │───▶│  Whisper     │───▶│  Storage   │  │
│  │  /alexa     │    │  (Módulo 2)  │    │  (Módulo 3)│  │
│  └─────────────┘    └──────────────┘    └────────────┘  │
│         ▲                  ▲                             │
│         │                  │                             │
│    Texto pronto       Áudio bruto                        │
│    (pula Whisper)   (captura Linux)                      │
└─────────────────────────────────────────────────────────┘
```

### Dois caminhos de entrada

**Caminho A — Texto já pronto** (via webhook):
- Qualquer dispositivo faz `POST /webhook/text` com `{"text": "...", "source": "..."}`
- Backend salva direto no banco, sem processar áudio
- Usado por: `windows_mic_sender.py` (que transcreve localmente no Windows), Alexa, ESP32, etc.

**Caminho B — Áudio bruto** (via microfone Linux):
- Backend captura áudio diretamente (só funciona Linux sem Docker, ou Docker com passthrough)
- Silero VAD detecta início/fim de fala
- Whisper transcreve o áudio
- Resultado salva no banco

---

## 🧩 Separação de responsabilidades

| Componente | Onde roda | Responsabilidade |
|---|---|---|
| **Backend** | Servidor (VPS, WSL2, Linux) | Receber, transcrever (opcional), armazenar |
| **windows_mic_sender.py** | Windows (nativo) | Capturar mic, transcrever com Whisper, enviar texto |
| **App desktop futuro** | Windows/Mac/Linux | Substituir windows_mic_sender com UI, tray icon, configurações |
| **Alexa Skill** | Nuvem Alexa | Capturar voz via Echo, enviar texto transcrito |
| **ESP32/Colar** | Hardware | Capturar áudio, enviar para `/webhook/text` |

**Regra simples**: O backend não precisa saber *quem* enviou o texto — só precisa de `{"text": "...", "source": "..."}`.

---

## 🔌 Como trocar o banco de dados

O banco é configurado 100% via `.env`. Não é preciso tocar no código.

### PostgreSQL local via Docker (padrão)
```env
DB_HOST=postgres
DB_PORT=5432
DB_USER=cerebro
DB_PASSWORD=sua_senha
DB_NAME=cerebro_db
```

### Supabase (PostgreSQL na nuvem)
```env
DB_HOST=db.xxxxxxxxxxxx.supabase.co
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=sua_senha_supabase
DB_NAME=postgres
```

> **Importante**: Ao usar banco externo, o schema ainda precisa ser aplicado. O entrypoint.sh faz isso automaticamente na inicialização — basta o banco existir e as credenciais estarem corretas.

### PostgreSQL em VPS
```env
DB_HOST=ip.da.vps.aqui
DB_PORT=5432
DB_USER=cerebro
DB_PASSWORD=sua_senha
DB_NAME=cerebro_db
```

---

## 🖥️ Caminho para o App Desktop

Hoje `windows_mic_sender.py` é um script simples. No futuro, pode virar um app completo — a interface muda, mas o **protocolo não muda**.

### O que o app desktop precisa fazer

```
1. Capturar áudio do microfone
2. Detectar início/fim de fala (VAD — Silero ou outro)
3. Transcrever localmente (Whisper) OU enviar áudio para o backend transcrever
4. Enviar POST /webhook/text com { text, source, timestamp }
```

Isso é só um cliente HTTP. Pode ser feito em qualquer linguagem.

### Opções de tecnologia para o app desktop

| Tecnologia | Plataformas | Prós | Contras |
|---|---|---|---|
| **Python + Tkinter** | Win/Mac/Linux | Simples, mesmo stack do backend | UI básica |
| **Python + PyQt6** | Win/Mac/Linux | UI moderna, tray icon | Maior bundle |
| **Electron + Node.js** | Win/Mac/Linux | Web technologies, tray icon fácil | Bundle grande (Node + Chrome) |
| **Tauri + Rust** | Win/Mac/Linux | Bundle pequeno, UI web | Rust learning curve |
| **Swift** | Mac only | Nativo, integração sistema | Só Mac |
| **C# WPF/WinUI** | Windows only | Nativo Windows | Só Windows |

**Recomendação pragmática**: Python + PyQt6 ou Tauri (se quiser UI bonita cross-platform).

### Interface mínima do app desktop

```
Tray icon:
  ● Gravando — clique para pausar
  ○ Pausado  — clique para gravar

Configurações (abre janela):
  Backend URL: [http://localhost:5001]
  Fonte:       [meu-notebook]
  Modelo VAD:  [silero | webrtcvad]
  [Salvar]
```

### O backend não muda

Quando o app desktop existir, o backend continua igual. O app só precisa fazer o mesmo POST que `windows_mic_sender.py` já faz.

---

## 📐 Diagrama Completo (presente + futuro)

```
                    ┌──────────────────────────────────────┐
                    │         BACKEND (sempre ligado)       │
PRESENTE:           │                                      │
                    │  /webhook/text ──▶ Storage           │
windows_mic.py ────▶│                                      │
Alexa          ────▶│  /webhook/alexa ─▶ Storage           │◀──── POST
                    │                                      │
                    │  mic Linux ──▶ VAD ──▶ Whisper ──▶   │
                    │                         Storage      │
                    └──────────────┬───────────────────────┘
                                   │
                              PostgreSQL
                         (local, Supabase, VPS)

FUTURO:
App Windows  ────▶ POST /webhook/text
App Mac      ────▶ POST /webhook/text    (mesmo endpoint, muda só quem chama)
App Linux    ────▶ POST /webhook/text
ESP32/Colar  ────▶ POST /webhook/text
```

---

## 🔑 Princípio de design

> **O backend é um receptor passivo.** Ele não busca dados — ele recebe. Qualquer dispositivo que possa fazer um POST HTTP pode ser uma fonte. Isso torna o sistema infinitamente extensível sem mudar o backend.

---

**Tags**: #arquitetura #backend #clientes #desktop #modular #webhook
