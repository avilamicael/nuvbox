-- Módulo 5 — Armazenamento Estruturado
-- Schema migration: novos campos, tabela action_items, correção embedding

-- 1. Colunas faltantes em fragmentos
ALTER TABLE fragmentos
  ADD COLUMN IF NOT EXISTS sentimento VARCHAR(20),
  ADD COLUMN IF NOT EXISTS tem_decisao BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS tem_pergunta BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS usuario_id INTEGER DEFAULT 1;

-- 2. Corrigir dimensão do embedding (1536 → 384 para MiniLM local, M7)
ALTER TABLE fragmentos DROP COLUMN IF EXISTS embedding;
ALTER TABLE fragmentos ADD COLUMN IF NOT EXISTS embedding VECTOR(384);

-- 3. Entidades: descricao, status, usuario_id
ALTER TABLE entidades
  ADD COLUMN IF NOT EXISTS descricao TEXT,
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ativo',
  ADD COLUMN IF NOT EXISTS usuario_id INTEGER DEFAULT 1;
-- Status possíveis: 'ativo' | 'pendente' | 'ambiguo'

-- 4. Tópicos: descricao, status, usuario_id, ultima_mencao_em
ALTER TABLE topicos
  ADD COLUMN IF NOT EXISTS descricao TEXT,
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ativo',
  ADD COLUMN IF NOT EXISTS usuario_id INTEGER DEFAULT 1,
  ADD COLUMN IF NOT EXISTS ultima_mencao_em TIMESTAMPTZ DEFAULT NOW();

-- 5. Nova tabela action_items
CREATE TABLE IF NOT EXISTS action_items (
  id            BIGSERIAL PRIMARY KEY,
  fragmento_id  BIGINT NOT NULL REFERENCES fragmentos(id) ON DELETE CASCADE,
  texto         TEXT NOT NULL,
  status        VARCHAR(20) DEFAULT 'pendente',   -- pendente | concluido | cancelado
  atualizado_por VARCHAR(20) DEFAULT 'manual',    -- manual | llm
  criado_em     TIMESTAMPTZ DEFAULT NOW(),
  usuario_id    INTEGER DEFAULT 1
);

-- Índices action_items
CREATE INDEX IF NOT EXISTS idx_action_items_fragmento ON action_items(fragmento_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
CREATE INDEX IF NOT EXISTS idx_action_items_usuario ON action_items(usuario_id);

-- Índices novos em fragmentos
CREATE INDEX IF NOT EXISTS idx_fragmentos_sentimento ON fragmentos(sentimento);
CREATE INDEX IF NOT EXISTS idx_fragmentos_tem_decisao ON fragmentos(tem_decisao) WHERE tem_decisao = TRUE;
CREATE INDEX IF NOT EXISTS idx_fragmentos_tem_pergunta ON fragmentos(tem_pergunta) WHERE tem_pergunta = TRUE;

-- Índices em entidades e tópicos
CREATE INDEX IF NOT EXISTS idx_entidades_status ON entidades(status);
CREATE INDEX IF NOT EXISTS idx_topicos_status ON topicos(status);
