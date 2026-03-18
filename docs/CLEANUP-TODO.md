---
name: Cleanup — Arquivos Não Utilizados
description: Scripts e módulos removidos quando backend mudou para arquitetura webhook-only
---

# Cleanup — Arquivos Não Utilizados

**Data**: 18/03/2026
**Razão**: Backend agora é webhook-only (Pinky, Alexa enviam áudio transcrito). Captura local foi removida.

## Arquivos para Remover

### Módulo 1 — Captura Local (Não Utilizado)
```
backend/modulo1_input/base_source.py        # Base class para fontes de áudio locais
backend/modulo1_input/mic_source.py         # MicrophoneSource (sounddevice + Silero VAD)
```

**Por quê?** Backend não mais captura áudio. Clientes (Pinky, Alexa) enviam já transcrito.

### Módulo 2 — Transcrição Local (Não Utilizado)
```
backend/modulo2_transcricao/transcription_worker.py   # TranscriptionWorker (Whisper)
backend/modulo2_transcricao/whisper_engine.py         # WhisperEngine wrapper
```

**Por quê?** Whisper roda no cliente (Pinky Windows app). Backend recebe texto pronto.

---

## Referências Removidas

- `main.py`: Removidas linhas de inicialização do `MicrophoneSource`, `TranscriptionWorker`, `raw_audio_queue`
- Imports em `modulo1_input/__init__.py`: Mantidas referências para compatibilidade (não causam erro se não usadas)
- Imports em `modulo2_transcricao/__init__.py`: Idem

---

## Status Atual

### ✅ Ativos
- `modulo1_input/text_webhook.py` — Recebe transcrições via POST
- `modulo1_input/alexa_webhook.py` — Suporta webhook legado Alexa
- `modulo3_armazenamento/` — StorageWorker, DB
- `modulo4_processamento/` — BatchWorker, LLM processing
- `scripts/test_modulo4_dryrun.py` — Teste de Module 4

### ⚠️ Órfãos (Importáveis mas não utilizados)
- `backend/modulo1_input/base_source.py`
- `backend/modulo1_input/mic_source.py`
- `backend/modulo2_transcricao/transcription_worker.py`
- `backend/modulo2_transcricao/whisper_engine.py`

---

## Ação Recomendada

**Fase 1** (agora): Deixar como está — pode ser referência histórica

**Fase 2** (quando estável): Remover se temos certeza que nenhum cliente legado usa captura local

```bash
# Remover depois de confirmar 100% que não é necessário:
rm backend/modulo1_input/{base_source,mic_source}.py
rm backend/modulo2_transcricao/{transcription_worker,whisper_engine}.py

# Limpar imports nos __init__.py
# (editar modulo1_input/__init__.py e modulo2_transcricao/__init__.py)
```

---

## Nota

Se no futuro precisar de captura local novamente (ex: ESP32 com Whisper local), os arquivos podem ser recuperados do git history.
