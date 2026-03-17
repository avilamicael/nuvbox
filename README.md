# 🎙️ Cerebro Backend v1.0

**Sistema completo de transcrição de voz** com Docker, Whisper e PostgreSQL.

> **Documentação completa em `docs/`** — [Acesse aqui](docs/INDEX.md)

## 🚀 Início Rápido

```bash
cp .env.example .env
nano .env                  # Edite: DB_PASSWORD + ALEXA_WEBHOOK_SECRET
docker-compose up -d
```

Sistema rodando em segundos. Documentação em `docs/INDEX.md`.

## 📚 Documentação

Toda a documentação está em **formato Obsidian** em `docs/`:

- **[INDEX.md](docs/INDEX.md)** — Ponto de partida
- **[Comece Aqui](docs/00-Inicio/00-Comece-Aqui.md)** — O que é o sistema
- **[Início Rápido](docs/00-Inicio/Inicio-Rapido.md)** — Setup em 5 minutos
- **[Arquitetura](docs/01-Arquitetura/Arquitetura-Geral.md)** — Como funciona
- **[Implantar](docs/02-Implantacao/Implantacao-Clientes.md)** — Para clientes
- **[Referência](docs/03-Referencia/)** — Variáveis, comandos
- **[Troubleshooting](docs/04-Troubleshooting/Erros-Comuns.md)** — Problemas

## 📁 Estrutura

```
nuvbox/
├── backend/                ← Aplicação Python
│   ├── main.py             ← Ponto de entrada
│   ├── config.py           ← Configurações
│   ├── requirements.txt     ← Dependências
│   └── modulo[1-3]/         ← Componentes
├── docs/                   ← 📚 Documentação Obsidian
│   ├── INDEX.md            ← Comece aqui!
│   ├── 00-Inicio/
│   ├── 01-Arquitetura/
│   ├── 02-Implantacao/
│   ├── 03-Referencia/
│   └── 04-Troubleshooting/
├── scripts/                ← Ferramentas
│   ├── healthcheck.sh
│   └── test_alexa.sh
├── docker-compose.yml      ← Orquestração
├── .env.example            ← Configuração template
├── CLAUDE.md               ← Instruções do projeto
└── Makefile                ← Atalhos de dev
```

## 🎯 O que você recebeu

✅ **Backend Python** — 12 módulos, 2.500+ linhas
✅ **Docker** — Production-ready com compose
✅ **Configuração** — Tudo em `.env`
✅ **Documentação** — 9 guias completos em Obsidian
✅ **Ferramentas** — Makefile, healthcheck, teste Alexa

## 💻 Comandos Úteis

```bash
# Docker
docker-compose up -d       # Iniciar
docker-compose down        # Parar
docker-compose logs -f     # Ver logs

# Makefile
make up                    # Iniciar
make logs                  # Ver logs
make test-db               # Testar banco
make healthcheck.sh        # Verificação

# Scripts
./scripts/healthcheck.sh   # Saúde do sistema
./scripts/test_alexa.sh    # Webhook Alexa
```

## 📚 Próximos Passos

1. **Ler documentação**: Abra [`docs/INDEX.md`](docs/INDEX.md)
2. **Começar rápido**: [`docs/00-Inicio/Inicio-Rapido.md`](docs/00-Inicio/Inicio-Rapido.md)
3. **Entender arquitetura**: [`docs/01-Arquitetura/Arquitetura-Geral.md`](docs/01-Arquitetura/Arquitetura-Geral.md)
4. **Implantar clientes**: [`docs/02-Implantacao/Implantacao-Clientes.md`](docs/02-Implantacao/Implantacao-Clientes.md)

## 📖 Documentação no Obsidian

Para melhor experiência:
1. Abra **Obsidian**
2. Abra pasta: `docs/`
3. Comece em `INDEX.md`
4. Use wikilinks `[[file]]` para navegar
5. Filtre por tags `#tag`

## 🔑 Características

- 🎤 Captura de áudio (USB + Alexa)
- 🤖 Transcrição com Whisper (local, offline)
- 💾 Armazenamento PostgreSQL (indexado)
- 🐳 Docker production-ready
- ⚙️ Configuração 100% em `.env`
- 🔐 Sem telemetria, sem nuvem

## 📞 Suporte

**Para dúvidas**, veja:
- **[Erros Comuns](docs/04-Troubleshooting/Erros-Comuns.md)**
- **[Diagnóstico](docs/04-Troubleshooting/)** (em breve)
- **[FAQ](docs/04-Troubleshooting/)** (em breve)

---

**Status**: 🟢 Pronto para Produção
**Versão**: 1.0
**Idioma**: Português BR
**Próximo**: Módulos 4-7 (IA, Grafo, Query, Semântica)

[→ Ir para Documentação](docs/INDEX.md)
