-- Schema for Jarvis Transcription Storage (Módulo 3)

CREATE TABLE IF NOT EXISTS transcricoes (
    id              BIGSERIAL PRIMARY KEY,
    texto           TEXT        NOT NULL,
    fonte           VARCHAR(50) NOT NULL,        -- 'mic_usb', 'alexa'
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    duracao_ms      INTEGER,                     -- NULL para Alexa
    modelo_whisper  VARCHAR(50),                 -- NULL para Alexa (ex: 'small')
    idioma          VARCHAR(10),                 -- ex: 'pt', 'en'
    sessao_id       VARCHAR(200),                -- session_id da Alexa, NULL para mic
    metadados       JSONB,                       -- extensível para Módulos 4-7
    criado_em_idx   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transcricoes_fonte
    ON transcricoes (fonte);

CREATE INDEX IF NOT EXISTS idx_transcricoes_criado_em
    ON transcricoes (criado_em DESC);

CREATE INDEX IF NOT EXISTS idx_transcricoes_sessao_id
    ON transcricoes (sessao_id) WHERE sessao_id IS NOT NULL;
