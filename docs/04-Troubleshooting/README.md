---
title: Troubleshooting e Diagnóstico
tags: [troubleshooting, problemas, solucoes, diagnostico]
---

# 🐛 Troubleshooting e Diagnóstico

Solução de problemas e guias de diagnóstico.

## 📖 Documentos

### [[Erros-Comuns|❌ Erros Comuns]]
**Problemas frequentes e soluções**
- PostgreSQL não inicia
- Microfone não encontrado
- Whisper muito lento
- Fila cheia
- Disco cheio

### [[Diagnostico|🔍 Diagnóstico]]
**Como investigar problemas**
- Health check
- Verificações de sistema
- Análise de logs
- Testes específicos

### [[FAQ|❓ FAQ]]
**Perguntas frequentes**
- Como funciona X?
- Posso mudar Y?
- Por que Z não funciona?

---

## 🆘 Início Rápido

### 1. Executar Health Check
```bash
./scripts/healthcheck.sh
```

### 2. Verificar Logs
```bash
docker-compose logs -f backend | tail -50
```

### 3. Procurar em Erros Comuns
→ [[Erros-Comuns|Erros Comuns]]

### 4. Seguir Diagnóstico
→ [[Diagnostico|Diagnóstico]]

---

## 🔗 Links Relacionados

- [[Comandos|Comandos]]
- [[Variaveis-Ambiente|Variáveis de Ambiente]]
- [[Implantacao-Clientes|Implantação]]
- [[INDEX|Índice]]

---

#troubleshooting #problemas #solucoes #diagnostico
