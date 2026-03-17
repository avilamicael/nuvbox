---
title: Módulo 1 - Input (Fontes de Entrada)
description: Arquitetura modular de fontes de entrada de áudio e texto do Jarvis
tags: #modulo1 #input #arquitetura #microfone #alexa #esp32 #wearable #modular
aliases:
  - Módulo 1
  - Input Sources
  - Fontes de Entrada
---

# 🎤 Módulo 1 — Input (Fontes de Entrada)

O Módulo 1 é responsável por **receber dados de qualquer fonte** e colocá-los no pipeline de processamento do Jarvis.

---

## 🏗️ Design Fundamental

O Módulo 1 é **intencionalmente modular**. O backend não se importa *de onde* veio o dado — só que ele chegou na fila certa no formato certo.

```
┌────────────────────────────────────────────────────────────────────┐
│                     MÓDULO 1 — INPUT                               │
│                                                                    │
│   FONTES EXTERNAS           ADAPTADORES          SAÍDA             │
│   ─────────────────         ──────────────        ───────────────  │
│   Windows Mic ──────────→ windows_mic_sender  → /webhook/text ──┐ │
│   Linux Mic ────────────→ MicrophoneSource    →  raw_audio_q  ──┤ │
│   Alexa Echo ───────────→ Alexa Cloud         → /webhook/alexa ─┤ │
│   ESP32 ────────────────→ ESP32 firmware      → /webhook/text ──┤ │
│   Colar/Wearable ───────→ BLE/MQTT firmware   → /webhook/text ──┤ │
│   Arquivo .mp3/.wav ────→ audio_file_source   →  raw_audio_q  ──┤ │
│   API externa ──────────→ http client         → /webhook/text ──┘ │
│                                                     │              │
│                                              ┌──────▼──────┐       │
│                                              │  text_queue │       │
│                                              └──────┬──────┘       │
└─────────────────────────────────────────────────────┼──────────────┘
                                                       │
                                                       ▼
                                                  Módulo 2
                                                (Transcrição /
                                                 Storage direto)
```

---

## 🔀 Dois Caminhos de Dados

### Caminho 1: Áudio bruto → Transcrição

Para fontes que capturam **áudio cru** (microfones):

```
Fonte de Áudio
     ↓ AudioChunk (float32, 16kHz)
raw_audio_queue
     ↓
TranscriptionWorker (Whisper)
     ↓ TextItem
text_queue
     ↓
StorageWorker → PostgreSQL
```

**Fontes que usam este caminho:**
- `MicrophoneSource` (Linux, USB mic)
- `WindowsMicSender` (script externo)
- `ESP32Source` (futuro)
- `AudioFileSender` (futuro - arquivos .mp3, .wav)

### Caminho 2: Texto já transcrito → Storage direto

Para fontes que já transcrevem **antes de enviar**:

```
Fonte de Texto
     ↓ TextItem (texto pronto)
text_queue (via webhook)
     ↓
StorageWorker → PostgreSQL
```

**Fontes que usam este caminho:**
- `Alexa` (Alexa Cloud já transcreve)
- `WindowsMicSender` (transcreve localmente com Whisper)
- `CollarSender` (futuro - Whisper embarcado)
- Qualquer API que envie texto direto

---

## 📦 Fontes Implementadas e Planejadas

### ✅ Implementadas

| Fonte | Arquivo | Como funciona | Status |
|-------|---------|---------------|--------|
| **Linux Mic** | `mic_source.py` | sounddevice + Silero VAD + Whisper | ✅ Pronto |
| **Alexa Webhook** | `alexa_webhook.py` | POST `/webhook/alexa` | ✅ Pronto |
| **Generic Text Webhook** | `text_webhook.py` | POST `/webhook/text` + `source` field | ✅ Pronto |

### 🔲 Planejadas (futuro)

| Fonte | Arquivo Futuro | Como vai funcionar | Fase |
|-------|---------------|-------------------|------|
| **Windows Mic** | `clients/windows_mic_sender.py` | Script externo: sounddevice → Whisper → POST | Fase 1 |
| **macOS Mic** | `clients/macos_mic_sender.py` | Igual Windows | Fase 1 |
| **Android App** | `clients/android/` | App Android: microfone → Whisper → POST | Fase 2 |
| **iOS App** | `clients/ios/` | App iOS: microfone → Whisper → POST | Fase 2 |
| **ESP32** | `clients/esp32/` | C++ firmware: mic → compressão → POST | Fase 3 |
| **Colar Wearable** | `clients/collar/` | BLE → ESP32 → POST ou MQTT | Fase 3 |
| **Arquivo de Áudio** | `clients/audio_file_sender.py` | .mp3/.wav → Whisper → POST | Fase 2 |

---

## 🧩 Como Adicionar uma Nova Fonte

Qualquer nova fonte de dado precisa apenas **enviar um POST** para o backend:

### Endpoint Genérico

```http
POST /webhook/text
Content-Type: application/json
X-Jarvis-Secret: {WEBHOOK_SECRET}

{
  "text": "o que você disse",
  "source": "windows_mic",     ← identifica a fonte
  "session_id": "opcional",
  "timestamp": "2026-03-17T14:00:00Z",
  "metadata": {                ← qualquer dado extra
    "device": "Microfone USB Samson",
    "whisper_model": "small",
    "language": "pt",
    "duration_ms": 3200
  }
}
```

**Fontes aceitas no campo `source`:**
- `windows_mic` — script rodando no Windows
- `linux_mic` — captura direta no Linux
- `alexa` — Alexa Cloud
- `esp32` — dispositivo ESP32
- `collar` — colar wearable
- `audio_file` — arquivo de áudio enviado
- `android_app` — app Android
- `ios_app` — app iOS
- qualquer string — extensível

### Regra Simples

> **Se você consegue fazer um POST HTTP com um JSON, você consegue adicionar uma nova fonte ao Jarvis.**

---

## 🗂️ Estrutura de Arquivos

```
backend/
└── modulo1_input/
    ├── __init__.py            # Exports públicos
    ├── base_source.py         # Classe abstrata AudioSource + AudioChunk
    ├── mic_source.py          # Linux: sounddevice + VAD (USB mic)
    ├── alexa_webhook.py       # Webhook específico Alexa
    └── text_webhook.py        # Webhook genérico (Windows, ESP32, etc.)

clients/                       # Scripts externos, rodando FORA do backend
├── windows_mic_sender.py      # Windows: captura mic + Whisper + envia
├── audio_file_sender.py       # Futuro: envia arquivo .mp3/.wav
└── esp32/                     # Futuro: firmware ESP32
    └── main.ino
```

---

## 🔐 Autenticação

Todas as fontes externas devem enviar o header de autenticação:

```
X-Jarvis-Secret: {WEBHOOK_SECRET}
```

O `WEBHOOK_SECRET` é configurado no `.env`:
```env
ALEXA_WEBHOOK_SECRET=mude_antes_de_usar
```

---

## 📋 Interface: AudioSource (para fontes de áudio local)

Para implementar uma **fonte de áudio local** (roda dentro do backend):

```python
from modulo1_input.base_source import AudioSource, AudioChunk

class MinhaFonteDeAudio(AudioSource):

    def __init__(self, audio_queue: Queue):
        self.audio_queue = audio_queue

    def start(self):
        # Iniciar captura
        pass

    def stop(self):
        # Parar captura
        pass

    def is_running(self) -> bool:
        return self._running

    def _emitir_chunk(self, audio_bytes: bytes):
        chunk = AudioChunk(
            audio_bytes=audio_bytes,
            source_id="minha_fonte",  # identificador único
            captured_at=datetime.now(),
            sample_rate=16000,
        )
        self.audio_queue.put_nowait(chunk)
```

---

## 🌐 Interface: Cliente HTTP (para fontes externas)

Para implementar uma **fonte externa** (roda fora do backend, em qualquer linguagem):

```python
import requests

def enviar_texto(texto: str, source: str, metadata: dict = None):
    response = requests.post(
        "http://seu-backend:5001/webhook/text",
        headers={
            "Content-Type": "application/json",
            "X-Jarvis-Secret": "seu-secret"
        },
        json={
            "text": texto,
            "source": source,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {}
        }
    )
    return response.json()

# Usar:
enviar_texto("olá jarvis", source="windows_mic", metadata={"duration_ms": 1500})
```

---

## 🗺️ Roadmap do Módulo 1

```
Fase 1 (AGORA)
├── ✅ Linux Mic (sounddevice)
├── ✅ Alexa Webhook
├── ✅ Generic Text Webhook
└── 🔲 Windows Mic Sender (clients/windows_mic_sender.py)

Fase 2 (próximas semanas)
├── 🔲 Audio File Sender (clients/audio_file_sender.py)
├── 🔲 Android App (clients/android/)
└── 🔲 iOS App (clients/ios/)

Fase 3 (futuro)
├── 🔲 ESP32 Firmware (clients/esp32/)
└── 🔲 Colar Wearable (clients/collar/)
```

---

**Tags**: #modulo1 #input #arquitetura #modular #microfone #esp32 #wearable #alexa
