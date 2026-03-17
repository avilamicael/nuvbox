---
title: Documentação Cerebro Backend v1.0
tags: [documentacao, indice, cerebro, backend]
created: 2026-03-17
updated: 2026-03-17
---

# 📚 Documentação Cerebro Backend v1.0

Bem-vindo à documentação do **Cerebro Backend** - um sistema de transcrição de voz pronto para produção com Docker.

> **🚀 Novo?** Comece por [[00-Comece-Aqui|Comece Aqui]] ou [[Inicio-Rapido|Início Rápido]]

---

## 🗂️ Estrutura da Documentação

### 🚀 [[00-Inicio/README|Início]]
Guias para começar rápido, sem complexidade.
- [[00-Comece-Aqui|Comece Aqui]] - Ponto de partida (5 min)
- [[Inicio-Rapido|Início Rápido]] - Configuração em 5 minutos

### 🏗️ [[01-Arquitetura/README|Arquitetura]]
Documentação técnica completa e aprofundada.
- [[Arquitetura-Geral|Arquitetura Geral]] - Visão geral do sistema e threading model
- [[Modulo1-Input|Módulo 1 - Input]] - Fontes de entrada modulares (mic, Alexa, ESP32, colar...)
- [[Deployment-Docker-vs-Local|Docker vs Local vs VPS]] - Quando usar cada opção de deployment
- [[Arquitetura-Backend-e-Clientes|Backend e Clientes]] - Papel do backend, banco externo, app desktop futuro

### 🚀 [[02-Implantacao/README|Implantação]]
Guias para implantar em ambiente de produção e clientes.
- [[Implantacao-Clientes|Implantação para Clientes]] - Passo a passo completo
- [[Windows-Mic-Sender-Setup|Setup Windows Mic Sender]] - Captura de microfone no Windows

### 🔧 [[03-Referencia/README|Referência]]
Referência rápida de comandos, variáveis e APIs.
- [[Variaveis-Ambiente|Variáveis de Ambiente]] - .env completo (backend + cliente Windows)
- [[Makefile-Comandos|Makefile - Comandos]] - Atalhos de desenvolvimento
- [[Dados-e-Backup|Dados e Backup]] - Onde ficam os dados, backup, migração para VPS
- [[VAD-Calibracao|VAD - Calibração e Debug]] - Ajustar detecção de pausas na fala

### 🐛 [[04-Troubleshooting/README|Troubleshooting]]
Diagnóstico e solução de problemas.
- [[Erros-Comuns|Erros Comuns]] - Soluções rápidas
- [[PostgreSQL-Host-Error|PostgreSQL: localhost vs postgres]] - Erro de conexão Docker
- [[PortAudio-Missing|PortAudio não encontrado]] - Erro sounddevice no Linux/Windows

---

## 🎯 Comece Por Aqui

**Se você é...**

| Eu sou... | Leia |
|-----------|------|
| Novo no projeto | [[00-Comece-Aqui\|Comece Aqui]] |
| Quero testar em 5 min | [[Inicio-Rapido\|Início Rápido]] |
| Desenvolvedor / Arquitetura | [[Arquitetura-Geral\|Arquitetura Geral]] + [[Modulo1-Input\|Módulo 1]] |
| Usando microfone no Windows | [[Windows-Mic-Sender-Setup\|Setup Windows]] |
| Implantando para cliente | [[Implantacao-Clientes\|Implantação para Clientes]] |
| Escolhendo Docker vs Local | [[Deployment-Docker-vs-Local\|Docker vs Local vs VPS]] |
| Com problemas de conexão DB | [[PostgreSQL-Host-Error\|PostgreSQL Host Error]] |
| Preciso de referência | [[Variaveis-Ambiente\|Variáveis]] + [[Makefile-Comandos\|Makefile]] |
| Backup / migrar para VPS | [[Dados-e-Backup\|Dados e Backup]] |

---

## 📊 Informações Rápidas

### Tecnologia
- **Backend**: Python 3.11+
- **Container**: Docker + Docker Compose
- **Banco de Dados**: PostgreSQL 15
- **Transcrição**: OpenAI Whisper
- **VAD**: Silero VAD
- **Web**: Flask

### Arquitetura (Módulo 1 — Input modular)
```
Windows Mic  → windows_mic_sender.py → POST /webhook/text ─┐
Linux Mic    → MicrophoneSource      → raw_audio_queue     ├→ PostgreSQL
Alexa        → Alexa Cloud           → POST /webhook/alexa ┘
ESP32/Colar  → firmware              → POST /webhook/text  (futuro)
```

### Configuração Rápida
```bash
cp .env.example .env     # Criar config
nano .env                # Editar (2 campos)
docker-compose up -d     # Iniciar
```

### Arquivos Importantes
- `docker-compose.yml` - Orquestração
- `.env.example` - Configuração
- `backend/main.py` - Aplicação
- `backend/requirements.txt` - Dependências

---

## 🏷️ Tags Principais

- `#cerebro` - Sistema Cerebro
- `#backend` - Código backend
- `#docker` - Containerização
- `#configuracao` - Variáveis e setup
- `#produção` - Para ambiente produção
- `#desenvolvimento` - Para desenvolvedores
- `#cliente` - Para implantação em clientes
- `#troubleshooting` - Solução de problemas
- `#api` - Endpoints e APIs
- `#banco-dados` - PostgreSQL

---

## 🔗 Ligações Rápidas

- [[00-Comece-Aqui|Comece Aqui]] (seu ponto de partida)
- [[Comandos|Makefile Commands]] (atalhos de desenvolvimento)
- [[Variaveis-Ambiente|.env Reference]] (configuração)
- [[Erros-Comuns|Troubleshooting]] (problemas comuns)
- [[Implantacao-Clientes|Cliente Setup]] (para clientes)

---

## 📅 Versão e Status

- **Versão**: 1.0
- **Status**: 🟢 Pronto para Produção
- **Idioma**: Português Brasil
- **Data**: 17 de Março de 2026
- **Próximo**: Módulos 4-7 (IA, Grafo, Query, Semântica)

---

## 💡 Dicas para Navegar

### Em Obsidian
- Use `Ctrl+O` (ou `Cmd+O` no Mac) para abrir rápido
- Clique em tags para filtrar documentos
- Use backlinks para navegar
- Graph view mostra conexões entre documentos

### Buscar
- Use `Ctrl+F` para buscar neste documento
- Use Obsidian search para buscar em todos

---

## 🤝 Próximos Passos

1. **Começar**: Vá para [[00-Comece-Aqui|Comece Aqui]]
2. **Entender**: Leia [[Arquitetura-Geral|Arquitetura Geral]]
3. **Desenvolver**: Veja [[Estrutura-Projeto|Estrutura do Projeto]]
4. **Implantar**: Siga [[Implantacao-Clientes|Implantação para Clientes]]

---

**Última atualização**: 17 de março de 2026
**Manutentor**: Equipe Cerebro
