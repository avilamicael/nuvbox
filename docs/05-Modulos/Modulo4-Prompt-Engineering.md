---
title: Módulo 4 - Prompt Engineering & Decisões
description: System prompt, decisões de design, histórico de ajustes do Módulo 4
tags: #modulo4 #prompt #engineering #design #decisoes #ia
aliases:
  - Module 4 Prompt
  - Prompt Engineering
---

# 📝 Módulo 4 — Prompt Engineering & Decisões

Documentação das decisões arquiteturais e evolução do prompt para GPT-4o mini.

---

## 🎯 Decisões Arquiteturais Chave

### 1. Timing: Near-Real-Time vs Batch Daily

**Escolha**: Near-real-time polling a cada 3 minutos

| Aspecto | Near-Real-Time (Adotado) | Batch Daily |
|---------|--------------------------|-------------|
| Latência | 3 min médio | 24h |
| Feedback | Imediato para debug | Atrasado |
| Custo | Igual (~$0.05) | Igual (~$0.05) |
| Complexidade | Simples (polling thread) | Simples (cron job) |
| Experiência | Melhor (feedback rápido) | Pior |

**Por quê**: Feedback imediato é crítico durante a fase MVP para debug e ajustes. Custo é o mesmo.

---

### 2. API: Chamadas Síncronas vs Batch API

**Escolha**: Chamadas síncronas (não Batch API)

| Aspecto | Síncrono (Adotado) | Batch API OpenAI |
|---------|-------------------|------------------|
| Latência | 5-10s por lote | 24h+ (queue) |
| Custo | $0.15/$0.60 por M tokens | 50% desconto |
| Complexidade | Simples | Média |
| Retry | Built-in | Manual |

**Por quê**:
- Batch API tem 24h de delay — impraticável para feedback
- Volume não justifica 50% de desconto (< 2.000 transcr/dia)
- Chamadas síncronas são simples com retry exponencial

---

### 3. Lote: Tamanho 15 vs 1 vs 50

**Escolha**: Lote de 15 transcricões

```
Economia de tokens (system prompt):

1 transcrição por chamada:
- System prompt: 500 tokens × 15 chamadas = 7.500 tokens
- User messages: ~50 tokens × 15 = 750 tokens
- Total: 8.250 tokens

15 transcrições por chamada:
- System prompt: 500 tokens × 1 chamada = 500 tokens
- User messages: ~750 tokens × 1 = 750 tokens
- Total: 1.250 tokens

Economia: (8.250 - 1.250) / 8.250 = 73% em overhead!
```

**Por quê 15 vs 50?**
- 15 = ~1.5KB JSON de input (razoável)
- 50 = ~5KB JSON (mais erro de parsing)
- Timeout OpenAI: 5-10s mantém-se mesmo com 15

---

### 4. Thread: Worker Thread vs Async

**Escolha**: Thread com `threading.Thread` (padrão de Módulos 1-3)

| Aspecto | Thread (Adotado) | Async/await |
|---------|-----------------|------------|
| Padrão | Consistente com StorageWorker | Diferente |
| Shutdown | `join(timeout=10)` | Komplexo |
| Estado | Compartilhado via banco | Compartilhado via banco |

**Por quê**: Mantém padrão de todos os outros workers. Async não adiciona benefício já que temos I/O bloqueante (database).

---

### 5. Schema: ALTER TABLE vs Novas Tabelas

**Escolha**: `ALTER TABLE transcricoes` + 6 novas tabelas

```sql
ALTER TABLE transcricoes:
- status (pending → processing → processed/skipped/error)
- processado_em
- modulo4_erro

Novas tabelas:
- fragmentos (resumo, importance_score)
- entidades (pessoas, empresas, projetos, conceitos)
- topicos (hierarquia)
- fragmento_entidade (N:N com contexto)
- fragmento_topico (N:N com confiança)
- entidade_entidade (grafo)
- modulo4_uso_diario (cost tracking)
```

**Por quê**:
- Migration via `ALTER TABLE` é simples e reversível
- Novas tabelas preparar para Módulos 5 (Query) e 7 (Embeddings)
- Status em `transcricoes` permite rastrear pipeline completo

---

### 6. Módulo 0: Perfil do Usuário

**Escolha**: YAML estático + hardcoded em prompt

```yaml
# Mínimo viável para MVP
usuario:
  nome: "Micael"
  contextos:
    trabalho: "Jarvis, código, bug, deploy"
    pessoal: "saúde, exercício, família"
```

**Por quê**:
- MVP não necessita interface dinâmica
- YAML é fácil de editar manualmente
- System prompt pode referenciar diretamente
- Evolução futura: banco de dados + interface web

---

## 📋 System Prompt (Atual)

```
Você é um assistente especializado em extração de informações de transcrições
do sistema Jarvis.

# PERFIL DO USUÁRIO
- Nome: Micael
- Idioma: português

# CONTEXTOS DO USUÁRIO
- Trabalho: Jarvis, código, bugs, deploy...
- Pessoal: saúde, exercício, família...

# TAREFA
Para cada transcrição, extrair:
1. Resumo (1-2 frases)
2. Importance Score (0.0-1.0)
3. Tópicos (array de caminhos hierárquicos)
4. Entidades (array com nome, tipo, contexto)

# INSTRUÇÕES CRÍTICAS
- Sempre responda em JSON válido
- Preserve exatamente a ordem do array de entrada
- Transcrições triviais: importance_score < 0.25
- Português: extraia também em português

# FORMATO DE SAÍDA
{
  "resultados": [
    {
      "idx": 0,
      "resumo": "string",
      "importance_score": 0.75,
      "topicos": ["Trabalho > Jarvis > Bugs"],
      "entidades": [...]
    }
  ]
}
```

---

## 🔄 Histórico de Decisões & Ajustes

### Versão 1 (Inicial)

```yaml
Características:
  - JSON output simples
  - Importance score 0-10 scale
  - Array flat de entidades

Problema:
  - Score 0-10 era confuso (0-1 é padrão ML)
  - Sem contexto para entidades
  - Sem relações entre entidades

Mudança para Versão 2 ✓
```

### Versão 2 (18/03/2026 — Produção)

```yaml
Características:
  - Importance score 0.0-1.0 (padrão)
  - Contexto incluído em cada entidade
  - Entidades com tipos validados
  - Relações preparadas (entidade_entidade)

Benefícios:
  - Score compatível com Módulo 7 (embeddings)
  - Contexto permite deduplicação + verificação
  - Validação de tipos no parser
  - Grafo de entidades pronto para knowledge graph
```

### Versão 3 (18/03/2026 — Atual)

```yaml
Mudanças em relação à v2:
  - Resumo: 1-3 frases (era 1-2), com instrução de ser específico
  - Tópicos: livres e ilimitados (era máximo 3, amarrado nas categorias)
  - Tipos de entidade: 6 → 11 (adicionados: evento, tarefa, decisao, ideia, produto)
  - Novos campos extraídos: action_items, sentimento, tem_decisao, tem_pergunta
  - Contexto temporal: fonte e hora passados por transcrição
  - user_profile.yaml: projetos_ativos com tecnologias, exemplos_topicos por contexto
  - Parser: aceita tipos desconhecidos sem falhar (loga debug)

Motivação:
  - v2 produzia dados vagos ("falou sobre trabalho") em vez de específicos
  - Tópicos limitados a 3 perdiam contexto rico
  - Categorias fixas não cobriam ideias, tarefas, decisões
  - Sem hora/fonte, LLM não tinha contexto temporal

Exemplo de saída v3 vs v2:
  v2: resumo: "Falou sobre um bug no sistema"
  v3: resumo: "Identificou bug de autenticação no Jarvis: token expirado não é renovado
              automaticamente no endpoint /webhook/text. Planeja corrigir no BatchWorker."
```

---

## ✅ Testes & Validação

### Testes Manuais Realizados

1. **Prompt Validity**
   ```bash
   python scripts/test_modulo4_dryrun.py
   # ✅ System prompt loads
   # ✅ User message JSON valida
   # ✅ Response parser handles mock data
   ```

2. **Parser Robustez (3 níveis)**
   - Level 1: `json.loads()` direto
   - Level 2: Regex para `{...}`
   - Level 3: Individual reprocessing

3. **Cost Tracking**
   ```sql
   SELECT * FROM modulo4_uso_diario WHERE data = TODAY;
   ```

---

## 🔐 Validação de Resposta

### Esquema Esperado (v3 — Atual)

```json
{
  "resultados": [
    {
      "idx": 0,
      "resumo": "string descritiva de 1-3 frases com detalhes específicos",
      "importance_score": 0.75,
      "topicos": ["Trabalho > Jarvis > Backend > Autenticação"],
      "entidades": [
        {
          "nome": "string",
          "tipo": "pessoa|empresa|projeto|lugar|conceito|ferramenta|evento|tarefa|decisao|ideia|produto",
          "contexto": "trecho literal (máx 100 chars)"
        }
      ],
      "action_items": ["string — tarefas concretas mencionadas"],
      "sentimento": "positivo|negativo|neutro|misto",
      "tem_decisao": false,
      "tem_pergunta": false
    }
  ]
}
```

### Validação Implementada

- `idx` deve ser sequencial (0, 1, 2, ...)
- `importance_score` deve estar em [0.0, 1.0]
- `resumo` deve ter ao menos 1 caractere
- `tipo` de entidade: aceita os 11 tipos definidos + desconhecidos (loga, não falha)
- `action_items`: deve ser lista (se presente)
- `sentimento`: aceita os 4 valores + None
- Tamanho do array deve corresponder ao batch size

---

## 📊 Performance Observado

### Métricas (Teste com 100 transcricões)

```
Batch size: 15
Latência por batch: 7-9s (OpenAI API)
Polling interval: 3min

Taxa de sucesso: 99%
- Parse Level 1: 98%
- Parse Level 2: 1%
- Parse Level 3 (reprocess): 1%

Importance score distribution:
- < 0.25: 20% (skipped)
- 0.25-0.50: 35%
- 0.50-0.75: 35%
- 0.75-1.00: 10%
```

---

## 🐛 Conhecidos Issues & Workarounds

### Issue 1: GPT às vezes inclui campos extras

**Exemplo**:
```json
{
  "idx": 0,
  "resumo": "...",
  "importance_score": 0.75,
  "topicos": [...],
  "entidades": [...],
  "timestamp": "2024-03-01T10:00:00"  // ❌ Extra field
}
```

**Workaround**: Parser ignora campos extras (não falha em validação)

**Solução futura**: Adicionar `"Additional: do NOT include other fields"` ao prompt

---

### Issue 2: Nomes de tópicos com variação de case

**Exemplo**:
```
Tópico 1: "Trabalho > Jarvis > Bugs"
Tópico 2: "trabalho > jarvis > bugs"  // ❌ Minúsculo
```

**Workaround**: `prompt_builder` adota case inicial de preferência

**Solução futura**: Adicionar exemplos exatos ao prompt

---

## 🚀 Melhorias Futuras

### Curto Prazo (MVP)
- [ ] Testes A/B: system prompt v1 vs v2
- [ ] User feedback loop: marcar extracões como correto/incorreto
- [ ] Histórico de ajustes ao prompt

### Médio Prazo
- [ ] Migrar para GPT-4o (melhor extração)
- [ ] Fine-tuning com Micael feedback
- [ ] Relações entre entidades automáticas

### Longo Prazo
- [ ] Módulo 0 dinâmico (interface web)
- [ ] Módulo 5 Query (buscar por tópico/entidade)
- [ ] Módulo 7 Embeddings (similarity search)

---

## 📚 Referências

- [[Modulo4-Processamento-IA]] — Overview do módulo
- [[Modulo4-Schema-SQL]] — Detalhamento das tabelas
- Arquivo de prompt: `backend/modulo4_processamento/prompt_builder.py`
- User profile: `backend/modulo4_processamento/user_profile.yaml`
