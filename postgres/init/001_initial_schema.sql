-- ============================================================
-- EsoterSystem — Esquema inicial PostgreSQL
-- Versión: 001
-- ============================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- búsqueda por similitud de texto
CREATE EXTENSION IF NOT EXISTS "unaccent";   -- búsqueda sin tildes

-- ============================================================
-- DOMINIO 1: CLIENTES (CRM Espiritual)
-- ============================================================

CREATE TABLE clients (
    id                      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name               VARCHAR(200)  NOT NULL,
    email                   VARCHAR(254)  UNIQUE,
    phone_number            VARCHAR(30),
    birth_date              DATE,
    birth_time              TIME,
    birth_place             VARCHAR(200),
    natal_chart             JSONB         DEFAULT '{}',
    current_emotional_state VARCHAR(100),
    trust_level             SMALLINT      DEFAULT 3 CHECK (trust_level BETWEEN 1 AND 5),
    recurring_topics        TEXT[]        DEFAULT '{}',
    intuitive_notes         TEXT,
    current_goals           TEXT,
    current_challenges      TEXT,
    active_plan             VARCHAR(30)   NOT NULL DEFAULT 'free'
                                CHECK (active_plan IN ('free','lectura_pago','mensual')),
    stripe_customer_id      VARCHAR(100)  UNIQUE,
    has_active_subscription BOOLEAN       NOT NULL DEFAULT false,
    timezone                VARCHAR(60)   NOT NULL DEFAULT 'UTC',
    language                VARCHAR(10)   NOT NULL DEFAULT 'es',
    created_at              TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ   NOT NULL DEFAULT now(),
    deleted_at              TIMESTAMPTZ
);

CREATE INDEX idx_clients_email        ON clients(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_clients_phone        ON clients(phone_number) WHERE deleted_at IS NULL;
CREATE INDEX idx_clients_stripe       ON clients(stripe_customer_id);
CREATE INDEX idx_clients_plan         ON clients(active_plan, has_active_subscription);
CREATE INDEX idx_clients_active       ON clients(created_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_clients_name_trgm    ON clients USING gin(full_name gin_trgm_ops);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE client_channels (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id        UUID        NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    channel          VARCHAR(30) NOT NULL
                        CHECK (channel IN ('whatsapp','instagram','facebook','tiktok','web','email')),
    external_id      VARCHAR(200) NOT NULL,
    channel_username VARCHAR(150),
    is_primary       BOOLEAN     NOT NULL DEFAULT false,
    is_active        BOOLEAN     NOT NULL DEFAULT true,
    opted_in_at      TIMESTAMPTZ,
    opted_out_at     TIMESTAMPTZ,
    metadata         JSONB       DEFAULT '{}',
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (channel, external_id)
);

CREATE INDEX idx_client_channels_lookup ON client_channels(channel, external_id);
CREATE INDEX idx_client_channels_client ON client_channels(client_id);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE client_relationships (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id_a       UUID        NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    client_id_b       UUID        NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL
                        CHECK (relationship_type IN ('pareja','ex_pareja','familiar','amigo','colega','otro')),
    description       TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (client_id_a <> client_id_b),
    UNIQUE (client_id_a, client_id_b)
);

-- ============================================================
-- DOMINIO 2: CONVERSACIONES Y MENSAJES
-- ============================================================

CREATE TABLE conversations (
    id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id                UUID        NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    channel                  VARCHAR(30) NOT NULL
                                CHECK (channel IN ('whatsapp','instagram','facebook','tiktok','web','email')),
    channel_conversation_id  VARCHAR(200),
    status                   VARCHAR(20) NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active','closed','archived')),
    started_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_message_at          TIMESTAMPTZ,
    closed_at                TIMESTAMPTZ,
    summary                  TEXT,
    context_snapshot         JSONB       DEFAULT '{}',
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_conversations_client  ON conversations(client_id, last_message_at DESC);
CREATE INDEX idx_conversations_active  ON conversations(status) WHERE status = 'active';
CREATE INDEX idx_conversations_channel ON conversations(channel, channel_conversation_id);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE messages (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID        NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    client_id           UUID        NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    role                VARCHAR(20) NOT NULL CHECK (role IN ('user','assistant','system','tool')),
    content             TEXT        NOT NULL,
    content_type        VARCHAR(30) NOT NULL DEFAULT 'text'
                            CHECK (content_type IN ('text','image','audio','video','document','template')),
    media_url           TEXT,
    llm_model           VARCHAR(100),
    agent_name          VARCHAR(100),
    tokens_input        INTEGER     CHECK (tokens_input >= 0),
    tokens_output       INTEGER     CHECK (tokens_output >= 0),
    latency_ms          INTEGER     CHECK (latency_ms >= 0),
    external_message_id VARCHAR(200),
    is_deleted          BOOLEAN     NOT NULL DEFAULT false,
    metadata            JSONB       DEFAULT '{}',
    sent_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, sent_at ASC);
CREATE INDEX idx_messages_client       ON messages(client_id, sent_at DESC);
CREATE INDEX idx_messages_agent        ON messages(agent_name) WHERE agent_name IS NOT NULL;

-- ============================================================
-- DOMINIO 3: SESIONES DE CONSULTA
-- ============================================================

-- (payments se define antes por la FK en sessions)

CREATE TABLE payments (
    id                       UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id                UUID          NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    stripe_payment_intent_id VARCHAR(100)  NOT NULL UNIQUE,
    stripe_charge_id         VARCHAR(100)  UNIQUE,
    amount_cents             INTEGER       NOT NULL CHECK (amount_cents > 0),
    currency                 VARCHAR(3)    NOT NULL DEFAULT 'eur',
    status                   VARCHAR(30)   NOT NULL
                                CHECK (status IN ('pending','requires_action','succeeded','failed','refunded','canceled')),
    payment_method_type      VARCHAR(50),
    description              TEXT,
    metadata                 JSONB         DEFAULT '{}',
    stripe_created_at        TIMESTAMPTZ,
    paid_at                  TIMESTAMPTZ,
    refunded_at              TIMESTAMPTZ,
    created_at               TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX idx_payments_client    ON payments(client_id, created_at DESC);
CREATE INDEX idx_payments_status    ON payments(status);
CREATE INDEX idx_payments_stripe_pi ON payments(stripe_payment_intent_id);

-- ─────────────────────────────────────────────────────────────

CREATE TABLE sessions (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id               UUID        NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    conversation_id         UUID        REFERENCES conversations(id) ON DELETE SET NULL,
    payment_id              UUID        REFERENCES payments(id) ON DELETE SET NULL,
    session_type            VARCHAR(30) NOT NULL
                                CHECK (session_type IN ('tarot','astrologia','numerologia','baraja_española','adivinacion','combinada')),
    is_free                 BOOLEAN     NOT NULL DEFAULT false,
    main_question           TEXT,
    cards_drawn             JSONB       DEFAULT '[]',
    interpretation          TEXT,
    perceived_energy        TEXT,
    next_steps              TEXT,
    esoteric_system_detail  JSONB       DEFAULT '{}',
    client_feedback         SMALLINT    CHECK (client_feedback BETWEEN 1 AND 5),
    conducted_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    duration_minutes        SMALLINT    CHECK (duration_minutes >= 0),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_client  ON sessions(client_id, conducted_at DESC);
CREATE INDEX idx_sessions_type    ON sessions(session_type);
CREATE INDEX idx_sessions_payment ON sessions(payment_id) WHERE payment_id IS NOT NULL;

-- ============================================================
-- DOMINIO 4: SUSCRIPCIONES
-- ============================================================

CREATE TABLE subscriptions (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id               UUID        NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    stripe_subscription_id  VARCHAR(100) NOT NULL UNIQUE,
    stripe_price_id         VARCHAR(100) NOT NULL,
    status                  VARCHAR(30) NOT NULL
                                CHECK (status IN ('trialing','active','past_due','canceled','unpaid','incomplete')),
    plan_name               VARCHAR(50) NOT NULL,
    amount_cents            INTEGER     NOT NULL CHECK (amount_cents > 0),
    currency                VARCHAR(3)  NOT NULL DEFAULT 'eur',
    current_period_start    TIMESTAMPTZ NOT NULL,
    current_period_end      TIMESTAMPTZ NOT NULL,
    trial_start             TIMESTAMPTZ,
    trial_end               TIMESTAMPTZ,
    canceled_at             TIMESTAMPTZ,
    cancel_at_period_end    BOOLEAN     NOT NULL DEFAULT false,
    metadata                JSONB       DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_subscriptions_client     ON subscriptions(client_id);
CREATE INDEX idx_subscriptions_active     ON subscriptions(status)
    WHERE status IN ('active','trialing','past_due');
CREATE INDEX idx_subscriptions_period_end ON subscriptions(current_period_end);

-- ============================================================
-- DOMINIO 5: MENSAJES DE SEGUIMIENTO (Agente Follower)
-- ============================================================

CREATE TABLE follow_up_messages (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id            UUID        NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    channel              VARCHAR(30) NOT NULL
                            CHECK (channel IN ('whatsapp','instagram','facebook','tiktok','web','email')),
    message_type         VARCHAR(30) NOT NULL
                            CHECK (message_type IN ('objetivo','desafio','afirmacion','recordatorio','check_in','ritual_sugerido')),
    content              TEXT        NOT NULL,
    status               VARCHAR(20) NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','scheduled','sent','delivered','read','failed')),
    scheduled_for        TIMESTAMPTZ NOT NULL,
    sent_at              TIMESTAMPTZ,
    delivered_at         TIMESTAMPTZ,
    read_at              TIMESTAMPTZ,
    failure_reason       TEXT,
    reference_session_id  UUID        REFERENCES sessions(id) ON DELETE SET NULL,
    source_chunk_id       UUID        REFERENCES knowledge_chunks_motivational(id) ON DELETE SET NULL,
    generated_by_agent    VARCHAR(100),
    llm_model             VARCHAR(100),
    metadata             JSONB       DEFAULT '{}',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_followup_pending ON follow_up_messages(status, scheduled_for ASC)
    WHERE status IN ('pending','scheduled');
CREATE INDEX idx_followup_client  ON follow_up_messages(client_id, created_at DESC);
CREATE INDEX idx_followup_channel ON follow_up_messages(channel, status);

-- ============================================================
-- DOMINIO 6: OBSERVACIONES DEL MONITOR
-- ============================================================

CREATE TABLE monitor_observations (
    id                       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    observation_type         VARCHAR(40) NOT NULL
                                CHECK (observation_type IN (
                                    'gap_conocimiento','solicitud_nueva','mejora_respuesta',
                                    'oportunidad_negocio','patron_cliente','alerta_tecnica'
                                )),
    priority                 VARCHAR(20) NOT NULL DEFAULT 'medium'
                                CHECK (priority IN ('low','medium','high','critical')),
    status                   VARCHAR(20) NOT NULL DEFAULT 'open'
                                CHECK (status IN ('open','in_review','resolved','dismissed')),
    title                    VARCHAR(300) NOT NULL,
    description              TEXT        NOT NULL,
    source_conversation_id   UUID        REFERENCES conversations(id) ON DELETE SET NULL,
    source_message_id        UUID        REFERENCES messages(id) ON DELETE SET NULL,
    source_client_id         UUID        REFERENCES clients(id) ON DELETE SET NULL,
    suggested_action         TEXT,
    resolution_notes         TEXT,
    detected_by_agent        VARCHAR(100),
    resolved_at              TIMESTAMPTZ,
    metadata                 JSONB       DEFAULT '{}',
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_monitor_open     ON monitor_observations(status, priority)
    WHERE status IN ('open','in_review');
CREATE INDEX idx_monitor_type     ON monitor_observations(observation_type);
CREATE INDEX idx_monitor_client   ON monitor_observations(source_client_id)
    WHERE source_client_id IS NOT NULL;

-- ============================================================
-- DOMINIO 7: BASE DE CONOCIMIENTO (RAG Registry)
-- ============================================================

CREATE TABLE knowledge_documents (
    id                 UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    title              VARCHAR(400) NOT NULL,
    source_filename    VARCHAR(500),
    source_url         TEXT,
    content_type       VARCHAR(20)  NOT NULL
                            CHECK (content_type IN ('text','audio','video','pdf','image')),
    esoteric_system    VARCHAR(50)
                            CHECK (esoteric_system IN (
                                'tarot','astrologia','numerologia','baraja_española',
                                'magia','chakras','flores_bach','general','otro'
                            )),
    language           VARCHAR(10)  NOT NULL DEFAULT 'es',
    processing_status  VARCHAR(30)  NOT NULL DEFAULT 'pending'
                            CHECK (processing_status IN (
                                'pending','processing','indexed','failed','outdated'
                            )),
    processing_error   TEXT,
    chunk_count        INTEGER      CHECK (chunk_count >= 0),
    motivational_chunk_count INTEGER CHECK (motivational_chunk_count >= 0),
    qdrant_collection  VARCHAR(200),
    qdrant_point_ids   JSONB        DEFAULT '[]',
    file_size_bytes    BIGINT       CHECK (file_size_bytes >= 0),
    file_hash          VARCHAR(64),
    tags               TEXT[]       DEFAULT '{}',
    description        TEXT,
    author             VARCHAR(200),
    published_date     DATE,
    indexed_at         TIMESTAMPTZ,
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at         TIMESTAMPTZ
);

-- ─────────────────────────────────────────────────────────────
-- Registro de chunks motivacionales detectados en los documentos
-- Estos son los fragmentos aptos para envío proactivo por el Follower
-- ─────────────────────────────────────────────────────────────

CREATE TABLE knowledge_chunks_motivational (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID        NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    qdrant_point_id     VARCHAR(200) NOT NULL,          -- ID del punto en Qdrant
    content_preview     TEXT        NOT NULL,           -- Primeros ~300 chars del chunk
    esoteric_system     VARCHAR(50)
                            CHECK (esoteric_system IN (
                                'tarot','astrologia','numerologia','baraja_española',
                                'magia','chakras','flores_bach','general','otro'
                            )),
    -- Temáticas a las que aplica este chunk (para matching con perfil del cliente)
    topics              TEXT[]      DEFAULT '{}',       -- amor, dinero, familia, trabajo, salud, espiritualidad...
    -- Estados emocionales para los que es relevante
    emotional_states    TEXT[]      DEFAULT '{}',       -- ansiedad, bloqueo, esperanza, duelo, transicion...
    -- Tipo de contenido motivacional
    motivational_type   VARCHAR(40) NOT NULL DEFAULT 'inspiracion'
                            CHECK (motivational_type IN (
                                'inspiracion',          -- frase o párrafo inspirador
                                'ensenanza',            -- enseñanza o concepto esotérico
                                'reflexion',            -- pregunta o reflexión profunda
                                'ritual_sugerido',      -- actividad o práctica concreta
                                'afirmacion',           -- afirmación para repetir
                                'prediccion_general'    -- extracto tipo predicción general
                            )),
    -- Nivel de profundidad (para ajustar al nivel del cliente)
    depth_level         SMALLINT    DEFAULT 2
                            CHECK (depth_level BETWEEN 1 AND 3),
    -- 1 = introductorio / 2 = intermedio / 3 = avanzado
    times_sent          INTEGER     NOT NULL DEFAULT 0, -- cuántas veces se ha enviado en total
    last_sent_at        TIMESTAMPTZ,                    -- última vez que se envió a alguien
    is_active           BOOLEAN     NOT NULL DEFAULT true,
    -- Detectado automáticamente por LLM o marcado manualmente
    detection_method    VARCHAR(20) NOT NULL DEFAULT 'auto'
                            CHECK (detection_method IN ('auto','manual')),
    detection_score     NUMERIC(4,3),                   -- confianza del clasificador (0.000-1.000)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_motivational_document ON knowledge_chunks_motivational(document_id);
CREATE INDEX idx_motivational_topics   ON knowledge_chunks_motivational USING gin(topics);
CREATE INDEX idx_motivational_emotions ON knowledge_chunks_motivational USING gin(emotional_states);
CREATE INDEX idx_motivational_type     ON knowledge_chunks_motivational(motivational_type)
    WHERE is_active = true;
CREATE INDEX idx_motivational_system   ON knowledge_chunks_motivational(esoteric_system)
    WHERE is_active = true;
CREATE INDEX idx_motivational_depth    ON knowledge_chunks_motivational(depth_level)
    WHERE is_active = true;

-- ─────────────────────────────────────────────────────────────
-- Historial de envíos motivacionales por cliente
-- Evita repetir el mismo chunk al mismo cliente
-- ─────────────────────────────────────────────────────────────

CREATE TABLE client_chunk_sent_log (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    UUID        NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    chunk_id     UUID        NOT NULL REFERENCES knowledge_chunks_motivational(id) ON DELETE CASCADE,
    sent_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    channel      VARCHAR(30) NOT NULL,
    reaction     VARCHAR(30),   -- positiva / negativa / neutral / sin_respuesta
    UNIQUE (client_id, chunk_id) -- un cliente no recibe el mismo chunk dos veces
);

CREATE INDEX idx_chunk_sent_client ON client_chunk_sent_log(client_id, sent_at DESC);
CREATE INDEX idx_chunk_sent_chunk  ON client_chunk_sent_log(chunk_id);

CREATE INDEX idx_knowledge_status ON knowledge_documents(processing_status)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_knowledge_system ON knowledge_documents(esoteric_system)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_knowledge_hash   ON knowledge_documents(file_hash)
    WHERE file_hash IS NOT NULL;
CREATE INDEX idx_knowledge_tags   ON knowledge_documents USING gin(tags);

-- ============================================================
-- DOMINIO 8: LOGS DE AGENTES
-- ============================================================

CREATE TABLE agent_logs (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name     VARCHAR(100) NOT NULL,
    action         VARCHAR(100) NOT NULL,
    llm_model      VARCHAR(100),
    tokens_input   INTEGER      CHECK (tokens_input >= 0),
    tokens_output  INTEGER      CHECK (tokens_output >= 0),
    tokens_total   INTEGER      GENERATED ALWAYS AS (
                       COALESCE(tokens_input, 0) + COALESCE(tokens_output, 0)
                   ) STORED,
    cost_usd       NUMERIC(10,6) CHECK (cost_usd >= 0),
    duration_ms    INTEGER      CHECK (duration_ms >= 0),
    status         VARCHAR(20)  NOT NULL
                        CHECK (status IN ('success','error','timeout','partial')),
    error_type     VARCHAR(100),
    error_message  TEXT,
    conversation_id UUID        REFERENCES conversations(id) ON DELETE SET NULL,
    client_id      UUID        REFERENCES clients(id) ON DELETE SET NULL,
    session_id     UUID        REFERENCES sessions(id) ON DELETE SET NULL,
    input_summary  TEXT,
    output_summary TEXT,
    metadata       JSONB        DEFAULT '{}',
    executed_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_agentlogs_agent    ON agent_logs(agent_name, executed_at DESC);
CREATE INDEX idx_agentlogs_conv     ON agent_logs(conversation_id)
    WHERE conversation_id IS NOT NULL;
CREATE INDEX idx_agentlogs_client   ON agent_logs(client_id)
    WHERE client_id IS NOT NULL;
CREATE INDEX idx_agentlogs_errors   ON agent_logs(status, executed_at DESC)
    WHERE status = 'error';
CREATE INDEX idx_agentlogs_cost     ON agent_logs(executed_at DESC, cost_usd);

-- ============================================================
-- FUNCIÓN: auto-actualizar updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers updated_at en todas las tablas con esa columna
CREATE TRIGGER trg_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_client_channels_updated_at
    BEFORE UPDATE ON client_channels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_messages_updated_at
    BEFORE UPDATE ON messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_followup_updated_at
    BEFORE UPDATE ON follow_up_messages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_monitor_updated_at
    BEFORE UPDATE ON monitor_observations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_knowledge_updated_at
    BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_motivational_updated_at
    BEFORE UPDATE ON knowledge_chunks_motivational
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
