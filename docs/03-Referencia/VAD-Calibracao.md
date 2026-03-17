---
title: VAD - Calibração e Debug
description: Como calibrar o Voice Activity Detection para capturar frases completas sem cortar nas pausas
tags: #vad #calibracao #debug #silero #microfone #qualidade
aliases:
  - VAD Calibração
  - Debug Transcrição
---

# 🎚️ VAD — Calibração e Debug

O **Silero VAD** decide quando uma frase começa e termina. Se ele cortar cedo demais, você perde partes da fala.

---

## 🔍 Como Identificar o Problema

### Sinal de que o VAD está cortando rápido demais

No banco de dados, frases que deveriam ser uma só aparecem como registros separados:

```
ID 3: "Eu preciso falar com Renato da Futura, pra gente ver isso sobre a questão."
ID 4: "e verificar com Renato para ver a nossa proposta..."
       ↑ começa com letra minúscula — é claramente continuação da frase anterior
```

Use o comando de debug para ver:
```bash
make db-debug    # Texto completo + duração em ms
make db-full     # Último registro completo
make db-full N=5 # Últimos 5 registros completos
```

---

## ⚙️ Variáveis de Controle (no `.env`)

### `VAD_SILENCE_DURATION_MS`
Tempo de silêncio (em ms) que o VAD espera antes de considerar que a fala terminou.

| Valor | Comportamento |
|-------|--------------|
| `300` | Muito sensível — corta nas mínimas pausas |
| `500` | Padrão — bom para fala fluida sem pausas |
| `1000` | Tolerante — aguarda pausas normais de pensamento |
| `1500` | **Recomendado para vícios de linguagem** — aguarda pausas longas |
| `2000` | Muito tolerante — pode juntar frases separadas |
| `3000+` | Excessivo — atrasa muito o envio |

### `VAD_MIN_SPEECH_DURATION_MS`
Tempo mínimo (em ms) de fala para não ser descartado como ruído.

| Valor | Comportamento |
|-------|--------------|
| `100` | Captura até sons curtos (pode pegar ruídos) |
| `300` | **Padrão** — ignora sons breves |
| `500` | Conservador — ignora falas curtas |

---

## 🎯 Configurações Recomendadas

### Para vícios de linguagem / pausas para pensar
```env
VAD_SILENCE_DURATION_MS=1500
VAD_MIN_SPEECH_DURATION_MS=300
```

### Para fala rápida e fluida
```env
VAD_SILENCE_DURATION_MS=500
VAD_MIN_SPEECH_DURATION_MS=200
```

### Para ambiente com ruído
```env
VAD_SILENCE_DURATION_MS=800
VAD_MIN_SPEECH_DURATION_MS=500
```

### Para gravar reuniões / múltiplas pessoas
```env
VAD_SILENCE_DURATION_MS=2000
VAD_MIN_SPEECH_DURATION_MS=300
```

---

## 🔄 Aplicar Mudança

Após editar o `.env`, **reinicie o script Windows** (Ctrl+C e rodar de novo):

```powershell
# Parar com Ctrl+C, depois:
python clients\windows_mic_sender.py
```

O script relê o `.env` a cada inicialização.

---

## 📊 Debugar com Comandos Make

```bash
# Ver texto completo + duração de cada registro
make db-debug

# Ver texto do último registro
make db-full

# Ver texto dos últimos 5 registros
make db-full N=5

# Ver preview rápido (80 chars)
make db-recent
```

### O que observar no `make db-debug`

| Campo | O que indica |
|-------|-------------|
| `chars` | Tamanho do texto — muito pequeno pode ser frase cortada |
| `duracao_ms` | Duração do áudio — ex: 4500ms = 4.5s de fala |
| `texto` | Começa com minúscula? Provavelmente é continuação de outra frase |

---

## 🧪 Metodologia de Calibração

1. Grave uma frase longa com pausa no meio
2. Rode `make db-debug`
3. Se apareceu como 2 registros → aumente `VAD_SILENCE_DURATION_MS` em +500ms
4. Repita até frases ficarem em 1 registro só
5. Se estiver juntando frases que são separadas → diminua em -200ms

---

## 💡 Dicas

- **Pausas de 1-2 segundos**: Use `VAD_SILENCE_DURATION_MS=1500`
- **"Éhhh...", "Hmm..."**: São fala, não silêncio — o VAD captura corretamente
- **Ruído de fundo constante**: Pode fazer VAD nunca detectar silêncio → use valor menor
- **Transcrição atrasada**: Normal — Whisper processa após a fala terminar. Com `VAD_SILENCE_DURATION_MS=1500` o delay aumenta ~1s, mas a qualidade melhora

---

**Tags**: #vad #calibracao #debug #silero #qualidade #microfone
