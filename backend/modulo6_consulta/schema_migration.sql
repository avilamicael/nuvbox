-- Módulo 6 — Interface de Consulta
-- Schema migration: tabela de correções de texto

-- Tabela de correções: mapeamentos "texto errado" → "texto correto"
-- Aplicadas no BatchWorker (M4) antes de enviar transcrições ao LLM
-- Exemplo: "prômitos" → "prompts", "djavarscript" → "JavaScript"
CREATE TABLE IF NOT EXISTS correcoes_texto (
    id          SERIAL PRIMARY KEY,
    texto_errado  TEXT NOT NULL,
    texto_correto TEXT NOT NULL,
    usuario_id  INTEGER NOT NULL DEFAULT 1,
    criado_em   TIMESTAMP DEFAULT NOW(),
    UNIQUE(usuario_id, texto_errado)
);

CREATE INDEX IF NOT EXISTS idx_correcoes_usuario ON correcoes_texto(usuario_id);

-- Status 'deletado' para soft delete de entidades e tópicos
-- Não requer ALTER TABLE pois o campo já é VARCHAR(20) sem constraint
-- Apenas documentando que os valores válidos agora incluem 'deletado':
-- entidades.status: 'ativo' | 'pendente' | 'ambiguo' | 'deletado'
-- topicos.status:   'ativo' | 'pendente' | 'deletado'
