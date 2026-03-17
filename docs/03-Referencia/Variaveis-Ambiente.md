---
title: Variáveis de Ambiente
tags: [configuracao, .env, variaveis, referencia]
aliases: [.env Reference, Configuração]
---

# ⚙️ Variáveis de Ambiente - Referência Completa

Documentação de cada variável em `.env`.

## 📋 Estrutura

Copie `.env.example` para `.env` e edite:
```bash
cp .env.example .env
nano .env
```

## 🗄️ Banco de Dados

### `DB_USER`
- **Tipo**: string
- **Padrão**: `jarvis`
- **Descrição**: Usuário PostgreSQL
- **Produção**: Pode manter ou mudar

### `DB_PASSWORD`
- **Tipo**: string
- **Padrão**: `jarvis_secure_password`
- **Descrição**: Senha PostgreSQL
- **⚠️ Segurança**: MUDE EM PRODUÇÃO!
- **Exemplo**: `sua_senha_forte_aqui`

### `DB_NAME`
- **Tipo**: string
- **Padrão**: `jarvis_db`
- **Descrição**: Nome do banco de dados
- **Produção**: Pode manter

## 🎤 Microfone

### `MIC_DEVICE_ID`
- **Tipo**: número inteiro
- **Padrão**: `0` (padrão)
- **Descrição**: ID do dispositivo de áudio
- **Como descobrir**:
  ```bash
  docker-compose run --rm backend \
    python -c "import sounddevice as sd; print(sd.query_devices())"
  ```
- **Exemplo**: `0` ou `2` (depende do seu setup)

### `MIC_SAMPLE_RATE`
- **Tipo**: número (Hz)
- **Padrão**: `16000`
- **Descrição**: Taxa de amostragem
- **Nota**: Whisper espera 16kHz
- **Não mude**: Deixe no padrão

### `MIC_CHUNK_SIZE`
- **Tipo**: número (amostras)
- **Padrão**: `512`
- **Descrição**: Tamanho do chunk de áudio
- **Nota**: Afeta latência vs CPU
- **Não mude**: Deixe no padrão

## 🤖 Whisper

### `WHISPER_MODEL`
- **Tipo**: string
- **Opções**: `tiny`, `base`, `small`, `medium`, `large`
- **Padrão**: `small`
- **Descrição**: Tamanho do modelo
- **Trade-off**:
  | Modelo | Speed | Qualidade | Tamanho |
  |--------|-------|-----------|---------|
  | tiny   | ⚡⚡⚡  | ⭐       | 40MB    |
  | base   | ⚡⚡   | ⭐⭐     | 140MB   |
  | small  | ⚡    | ⭐⭐⭐   | 460MB   |
  | medium | 🐢    | ⭐⭐⭐⭐ | 1.5GB   |
  | large  | 🐢🐢   | ⭐⭐⭐⭐⭐ | 2.9GB   |

### `WHISPER_LANGUAGE`
- **Tipo**: string (código ISO 639-1)
- **Padrão**: `pt` (português)
- **Opções comuns**: `pt`, `en`, `es`, `fr`, deixe em branco para auto-detectar
- **Descrição**: Idioma para transcrição

## 🎙️ Voice Activity Detection (VAD)

### `VAD_SILENCE_DURATION_MS`
- **Tipo**: número (milissegundos)
- **Padrão**: `500`
- **Descrição**: Tempo de silêncio para terminar enunciado
- **Ajustar se**:
  - Muito baixo (ex: 200): Corta fala rápida
  - Muito alto (ex: 1000): Demora para processar

### `VAD_MIN_SPEECH_DURATION_MS`
- **Tipo**: número (milissegundos)
- **Padrão**: `300`
- **Descrição**: Tempo mínimo para considerar fala
- **Ajustar se**:
  - Muito baixo: Detecção de ruído
  - Muito alto: Perde falas curtas

## 🌐 Flask/Alexa

### `ALEXA_WEBHOOK_SECRET`
- **Tipo**: string
- **Padrão**: `change_me_before_ngrok`
- **Descrição**: Secret para validação de webhook Alexa
- **⚠️ Segurança**: MUDE ANTES DE EXPOR!
- **Como usar**:
  ```bash
  curl -X POST http://localhost:5001/webhook/alexa \
    -H "X-Alexa-Secret: sua_chave_aqui" \
    -d '{"text":"teste",...}'
  ```

## 📝 Logging

### `LOG_LEVEL`
- **Tipo**: string
- **Opções**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Padrão**: `INFO`
- **Descrição**: Nível de verbosidade
- **Usar**:
  - `DEBUG`: Desenvolvimento (muito detalhado)
  - `INFO`: Produção (normal)
  - `WARNING`: Somente avisos
  - `ERROR`: Somente erros

### `LOG_DIR`
- **Tipo**: path
- **Padrão**: `/app/logs`
- **Descrição**: Diretório de logs
- **Docker**: Não mude
- **Local**: Pode mudar para `logs/` local

## 🐳 Docker Interno

### `FLASK_HOST`
- **Tipo**: string
- **Padrão**: `0.0.0.0`
- **Descrição**: Host para Flask bind
- **Produção**: Deixe como está (reverse proxy trata)

### `FLASK_PORT`
- **Tipo**: número
- **Padrão**: `5001`
- **Descrição**: Porta Flask
- **Mudar se**: Conflita com outra aplicação

## 📊 Filas

### `RAW_AUDIO_QUEUE_MAX_SIZE`
- **Tipo**: número
- **Padrão**: `100`
- **Descrição**: Tamanho máximo da fila de áudio bruto
- **Ajustar se**: Muitos "queue full" errors

### `TEXT_QUEUE_MAX_SIZE`
- **Tipo**: número
- **Padrão**: `100`
- **Descrição**: Tamanho máximo da fila de texto
- **Ajustar se**: Muitos "queue full" errors

---

## 🔄 Exemplo Completo

```env
# Banco de dados
DB_USER=jarvis
DB_PASSWORD=minha_senha_forte_123!
DB_NAME=jarvis_db

# Microfone
MIC_DEVICE_ID=0
MIC_SAMPLE_RATE=16000
MIC_CHUNK_SIZE=512

# Whisper
WHISPER_MODEL=small
WHISPER_LANGUAGE=pt

# VAD
VAD_SILENCE_DURATION_MS=500
VAD_MIN_SPEECH_DURATION_MS=300

# Alexa
ALEXA_WEBHOOK_SECRET=meu_secret_alexa_123

# Logging
LOG_LEVEL=INFO

# Internas
LOG_DIR=/app/logs
```

---

## 💡 Dicas

### Para Desenvolvimento
```env
LOG_LEVEL=DEBUG
WHISPER_MODEL=tiny  # Mais rápido
```

### Para Produção
```env
LOG_LEVEL=INFO
WHISPER_MODEL=small  # Melhor custo-benefício
DB_PASSWORD=senhaForte123!@#
ALEXA_WEBHOOK_SECRET=secretoAleatorio123!@#
```

### Para Performance
```env
WHISPER_MODEL=base    # Mais rápido que small
VAD_SILENCE_DURATION_MS=300  # Mais responsivo
```

---

## 🔗 Ver Também

- [[Implantacao-Clientes|Implantação para Clientes]]
- [[Diagnostico|Diagnóstico]]
- [[Configuracao|Sistema de Configuração]]
- [[INDEX|Índice]]

---

#configuracao #variaveis #.env #referencia #ambiente
