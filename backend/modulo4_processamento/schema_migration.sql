-- Schema Migration for Módulo 4 - AI Processing with GPT-4o mini
-- This migration:
-- 1. Extends transcricoes table with processing status
-- 2. Creates 6 new tables for structured memory (fragmentos, entidades, tópicos, etc.)
-- 3. Creates cost tracking table

-- ============================================================================
-- MIGRATION 1: Extend transcricoes table with processing status
-- ============================================================================

ALTER TABLE transcricoes
ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'pending';

ALTER TABLE transcricoes
ADD COLUMN IF NOT EXISTS processado_em TIMESTAMPTZ;

ALTER TABLE transcricoes
ADD COLUMN IF NOT EXISTS modulo4_erro TEXT;

-- Index for efficient polling of pending transcriptions
CREATE INDEX IF NOT EXISTS idx_transcricoes_status
    ON transcricoes (status) WHERE status = 'pending';

-- Index for finding stuck processing records
CREATE INDEX IF NOT EXISTS idx_transcricoes_processado_em
    ON transcricoes (processado_em DESC) WHERE status = 'processing';

-- ============================================================================
-- TABLE: fragmentos
-- The processed unit - one fragment per transcription (if importance >= threshold)
-- ============================================================================

CREATE TABLE IF NOT EXISTS fragmentos (
    id              BIGSERIAL PRIMARY KEY,
    transcricao_id  BIGINT NOT NULL UNIQUE REFERENCES transcricoes(id) ON DELETE CASCADE,

    -- Extracted by GPT-4o mini
    resumo          TEXT NOT NULL,                -- 1-2 sentence summary
    importance_score DECIMAL(3,2) NOT NULL,      -- 0.00 to 1.00

    -- Metadata
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tokens_input    INTEGER,                      -- For cost tracking
    tokens_output   INTEGER,                      -- For cost tracking
    model_used      VARCHAR(50)                   -- e.g., 'gpt-4o-mini'

    -- Future (Módulo 7): ALTER TABLE fragmentos ADD COLUMN embedding VECTOR(1536);
    -- Requer extensão pgvector: CREATE EXTENSION vector;
);

CREATE INDEX IF NOT EXISTS idx_fragmentos_transcricao_id
    ON fragmentos (transcricao_id);

CREATE INDEX IF NOT EXISTS idx_fragmentos_importance
    ON fragmentos (importance_score DESC);

-- ============================================================================
-- TABLE: entidades
-- Extracted entities: pessoas, empresas, projetos, conceitos, etc.
-- ============================================================================

CREATE TABLE IF NOT EXISTS entidades (
    id                  BIGSERIAL PRIMARY KEY,

    nome                VARCHAR(255) NOT NULL,     -- Raw name from LLM
    nome_normalizado    VARCHAR(255) NOT NULL,     -- Lowercase for deduplication
    tipo                VARCHAR(50) NOT NULL,      -- 'pessoa', 'empresa', 'projeto', 'lugar', 'conceito'

    -- Aggregation across fragments
    frequencia          INTEGER NOT NULL DEFAULT 1, -- How many fragments mention this?
    primeira_mencao_em  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ultima_mencao_em    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique index inclui variante para permitir homônimos com qualificador diferente
-- (ex: "Juliana (mãe)" e "Juliana (amiga)" como entidades distintas)
-- Substituído por idx_entidades_tipo_nome_variante no M6 schema_migration.sql

CREATE INDEX IF NOT EXISTS idx_entidades_frequencia
    ON entidades (frequencia DESC);

-- ============================================================================
-- TABLE: topicos (Hierarchical)
-- e.g., "Trabalho > Cerebro > Bugs"
-- ============================================================================

CREATE TABLE IF NOT EXISTS topicos (
    id          BIGSERIAL PRIMARY KEY,

    nome        VARCHAR(255) NOT NULL,     -- e.g., 'Bugs'
    caminho     TEXT NOT NULL,             -- e.g., 'Trabalho > Cerebro > Bugs'
    nivel       INTEGER NOT NULL,          -- 1 = root, 2 = child, etc.

    pai_id      BIGINT REFERENCES topicos(id) ON DELETE SET NULL,

    -- Aggregation
    frequencia  INTEGER NOT NULL DEFAULT 1,
    primeira_mencao_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    criado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_topicos_caminho
    ON topicos (caminho);

CREATE INDEX IF NOT EXISTS idx_topicos_pai_id
    ON topicos (pai_id);

CREATE INDEX IF NOT EXISTS idx_topicos_frequencia
    ON topicos (frequencia DESC);

-- ============================================================================
-- TABLE: fragmento_entidade (N:N relationship)
-- Links fragments to entities with context
-- ============================================================================

CREATE TABLE IF NOT EXISTS fragmento_entidade (
    id              BIGSERIAL PRIMARY KEY,

    fragmento_id    BIGINT NOT NULL REFERENCES fragmentos(id) ON DELETE CASCADE,
    entidade_id     BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,

    contexto        TEXT NOT NULL,         -- The snippet where entity was mentioned
    posicao_relativa VARCHAR(50),          -- 'inicio', 'meio', 'final'

    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fragmento_entidade_unique
    ON fragmento_entidade (fragmento_id, entidade_id);

CREATE INDEX IF NOT EXISTS idx_fragmento_entidade_entidade_id
    ON fragmento_entidade (entidade_id);

-- ============================================================================
-- TABLE: fragmento_topico (N:N relationship)
-- Links fragments to topics with confidence score
-- ============================================================================

CREATE TABLE IF NOT EXISTS fragmento_topico (
    id              BIGSERIAL PRIMARY KEY,

    fragmento_id    BIGINT NOT NULL REFERENCES fragmentos(id) ON DELETE CASCADE,
    topico_id       BIGINT NOT NULL REFERENCES topicos(id) ON DELETE CASCADE,

    confianca       DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00 - LLM confidence
    eh_principal    BOOLEAN NOT NULL DEFAULT FALSE,  -- Main topic for this fragment?

    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fragmento_topico_unique
    ON fragmento_topico (fragmento_id, topico_id);

CREATE INDEX IF NOT EXISTS idx_fragmento_topico_topico_id
    ON fragmento_topico (topico_id);

-- ============================================================================
-- TABLE: entidade_entidade (Graph of relationships)
-- Preparation for Módulo 7: Knowledge graph traversal
-- ============================================================================

CREATE TABLE IF NOT EXISTS entidade_entidade (
    id              BIGSERIAL PRIMARY KEY,

    entidade1_id    BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,
    entidade2_id    BIGINT NOT NULL REFERENCES entidades(id) ON DELETE CASCADE,

    tipo_relacao    VARCHAR(100) NOT NULL, -- 'trabalha_para', 'amigo_de', 'componente_de', etc.
    confianca       DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00
    frequencia      INTEGER NOT NULL DEFAULT 1,

    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_entidade_entidade_unique
    ON entidade_entidade (entidade1_id, entidade2_id, tipo_relacao);

CREATE INDEX IF NOT EXISTS idx_entidade_entidade_entidade2
    ON entidade_entidade (entidade2_id);

-- ============================================================================
-- TABLE: modulo4_uso_diario
-- Daily cost tracking and limits
-- ============================================================================

CREATE TABLE IF NOT EXISTS modulo4_uso_diario (
    id              BIGSERIAL PRIMARY KEY,

    data            DATE NOT NULL UNIQUE,
    tokens_input    BIGINT NOT NULL DEFAULT 0,
    tokens_output   BIGINT NOT NULL DEFAULT 0,
    custo_usd       DECIMAL(10,4) NOT NULL DEFAULT 0.0000,

    fragmentos_processados  INTEGER NOT NULL DEFAULT 0,
    fragmentos_skipped      INTEGER NOT NULL DEFAULT 0,  -- importance < threshold
    erros_count             INTEGER NOT NULL DEFAULT 0,

    atualizado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_modulo4_uso_diario_data
    ON modulo4_uso_diario (data DESC);
