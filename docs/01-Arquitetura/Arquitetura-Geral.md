---
title: Arquitetura Geral
tags: [arquitetura, design, sistema, overview]
aliases: [Visão Geral, Arquitetura]
---

# 🏗️ Arquitetura Geral do Jarvis Backend

Visão completa de como o sistema funciona e seus componentes principais.

## 📊 Componentes Principais

O sistema possui **3 módulos principais** + **base comum**:

```
┌─────────────────────────────────────────────────┐
│         Jarvis Backend v1.0                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  Módulo 1: Captura de Áudio                    │
│  ├─ USB Microfone (sounddevice)                │
│  ├─ Voice Activity Detection (Silero VAD)      │
│  └─ Alexa Webhook (Flask)                      │
│                                                 │
│  Módulo 2: Transcrição                         │
│  ├─ OpenAI Whisper (local)                     │
│  └─ Worker thread (CPU-bound)                  │
│                                                 │
│  Módulo 3: Armazenamento                       │
│  ├─ PostgreSQL connection pool                 │
│  ├─ Tabela transcricoes                        │
│  └─ Storage worker thread                      │
│                                                 │
│  Base Comum                                    │
│  ├─ Configuração (config.py)                   │
│  ├─ Logging (logger.py)                        │
│  ├─ Shutdown gracioso (shutdown.py)            │
│  └─ Orquestração (main.py)                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

## 🔄 Pipeline de Dados

```
ENTRADA                    PROCESSAMENTO            SAÍDA
─────────────────────────────────────────────────────────

Microfone 🎤              Silero VAD               [raw_audio_queue]
                          (detecção)               (fila 1)
                                                        │
                                                        ▼
                                        TranscriptionWorker
                                            (Whisper)       → [text_queue]
                                                            (fila 2)
                                                                 │
Alexa 🌐                  Validação                           ▼
(HTTP POST)  ────────────► Secret ────────►                  │
                                                   StorageWorker
                                                   (PostgreSQL)
                                                        │
                                                        ▼
                                                  PostgreSQL 💾
                                                  (transcricoes)
```

Veja [[Pipeline-Dados|Pipeline de Dados]] para detalhes.

## 🧵 Threading Model

O sistema usa **threading** para paralelismo:

```
┌─────────────────────────────────────┐
│ main.py (thread principal)          │
│ ├─ Inicia serviços                  │
│ ├─ Aguarda shutdown_event           │
│ └─ Limpa recursos                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ sounddevice (callback de áudio)     │
│ ├─ Captura em tempo real            │
│ ├─ Processa VAD                     │
│ └─ Emite AudioChunk                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ TranscriptionWorker (thread)        │
│ ├─ Consome AudioChunk               │
│ ├─ Processa Whisper                 │
│ └─ Produz TextItem                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ StorageWorker (thread)              │
│ ├─ Consome TextItem                 │
│ ├─ INSERT no banco                  │
│ └─ Log de sucesso/erro              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ FlaskThread (webhook Alexa)         │
│ ├─ HTTP GET /health                 │
│ ├─ HTTP POST /webhook/alexa         │
│ └─ Validação de secret              │
└─────────────────────────────────────┘
```

## ⚙️ Configuração

Tudo é configurado via **variáveis de ambiente** (`.env`):

```python
# config.py lê .env e cria Settings dataclass
settings = load_settings()

# Acessível em todo o código
from config import settings
sample_rate = settings.mic.sample_rate  # 16000
model = settings.whisper.model          # "small"
db_host = settings.db.host              # "localhost"
```

Veja [[Variaveis-Ambiente|Variáveis de Ambiente]].

## 🔐 Segurança

### O que é protegido?
- ✅ Senhas: Em `.env`, não em código
- ✅ Audio: Processado localmente
- ✅ Texto: Armazenado no seu banco
- ✅ Webhook Alexa: Validação por secret

### O que não é:
- ⚠️ Conexão BD: TCP local (seguro em Docker network)
- ⚠️ Flask: Sem autenticação (rede interna)

Veja [[Implantacao-Clientes|Implantação]] para produção.

## 🚀 Escalabilidade

### Design para crescimento
- **Filas**: Desacoplam componentes
- **Threading**: Workers paralelos
- **Connection pool**: Reutiliza conexões BD
- **JSONB metadados**: Extensível sem migrations

### Limitações atuais
- 1 TranscriptionWorker (CPU-bound)
- 5 conexões BD máximo
- 100 items por fila máximo

## 📈 Performance

### Latência Típica
```
Microfone → VAD:          ~100ms (real-time)
Acumulação:               ~500ms (configurável)
Whisper (small):          3-5s por 10s de áudio
Banco de dados:           <10ms (indexado)
─────────────────────────────────────────
Total fim-a-fim:          ~4-6s para 10s de áudio
```

### Throughput
```
Transcrições/dia:         ~1000 (típico)
Tamanho por registro:     ~1KB
Storage growth:           1GB / ~1M transcrições
```

## 🔄 Ciclo de Vida

1. **Boot** (main.py)
   - Inicializa logger
   - Registra signal handlers
   - Cria connection pool
   - Inicia workers

2. **Operação Normal**
   - Microfone capta áudio
   - VAD detecta fala
   - Workers processam
   - Banco armazena

3. **Shutdown**
   - SIGINT recebido
   - Drain de filas (30s timeout)
   - Encerramento gracioso
   - Limpeza de recursos

## 🔗 Ver Também

- [[Pipeline-Dados|Pipeline de Dados]] - Fluxo detalhado
- [[Modulos|Módulos]] - Cada componente
- [[Estrutura-Projeto|Estrutura do Projeto]] - Arquivos
- [[Configuracao|Configuração]] - System settings

---

**Próximas leituras:**
1. [[Pipeline-Dados|Pipeline de Dados]] (5 min)
2. [[Modulos|Módulos]] (15 min)
3. [[Estrutura-Projeto|Estrutura do Projeto]] (20 min)

---

#arquitetura #design #sistema #overview
