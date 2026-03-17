---
title: Erro PortAudio - sounddevice não encontra biblioteca
description: Solução para erro "OSError: PortAudio library not found" ao rodar Backend localmente
tags: #sounddevice #portaudio #microfone #troubleshooting #setup
aliases:
  - PortAudio Missing
  - sounddevice Error
---

# Erro: PortAudio library not found

## Problema

Ao rodar Backend Python localmente:

```
File "/home/micael/nuvbox/backend/modulo1_input/mic_source.py", line 12, in <module>
    import sounddevice as sd
  File "/home/micael/nuvbox/venv/lib/python3.10/site-packages/sounddevice.py", line 71, in <module>
    raise OSError('PortAudio library not found')
OSError: PortAudio library not found
```

## Causa

O pacote Python `sounddevice` precisa da **biblioteca C PortAudio** instalada no sistema operacional.

```
sounddevice (pacote Python pip)
        ↓
precisa de
        ↓
libportaudio2 (biblioteca C do sistema)
```

## Solução

### **Linux (Ubuntu/Debian)**

```bash
# Instalar a biblioteca PortAudio
sudo apt-get update
# ⚠️ Atenção: o pacote correto é portaudio19-dev, não libportaudio-dev
sudo apt-get install -y libportaudio2 portaudio19-dev

# Depois rodar Backend
DB_HOST=localhost python backend/main.py
```

### **macOS**

```bash
# Via Homebrew
brew install portaudio

# Depois
DB_HOST=localhost python backend/main.py
```

### **Windows**

PortAudio geralmente já está incluído. Se não funcionar:
1. Baixe em: http://www.portaudio.com/download.html
2. Instale o instalador
3. Reinicie o terminal e tente novamente

## Verificação

```bash
# Testar se instalou corretamente
python -c "import sounddevice; print('✅ sounddevice OK')"
```

**Esperado:**
```
✅ sounddevice OK
```

---

## Alternativa: Usar Docker para Tudo

Se não conseguir instalar PortAudio localmente, use Docker:

```bash
# Voltar a 100% Docker
make down
docker-compose up -d
make webhook-test  # Testar webhook Alexa
```

---

**Tags**: #sounddevice #portaudio #setup #microfone
