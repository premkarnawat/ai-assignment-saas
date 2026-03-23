-- database/schema.sql
-- Full PostgreSQL schema for AI Assignment Generator

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ──────────────────────────────────────────────────────────
-- USERS
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            VARCHAR(255) UNIQUE NOT NULL,
    name             VARCHAR(255),
    avatar_url       VARCHAR(500),
    hashed_password  VARCHAR(255),
    provider         VARCHAR(50)  NOT NULL DEFAULT 'email',
    provider_id      VARCHAR(255),
    tier             VARCHAR(50)  NOT NULL DEFAULT 'free',
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_email ON users(email);

-- ──────────────────────────────────────────────────────────
-- ASSIGNMENTS
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assignments (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question           TEXT NOT NULL,
    subject            VARCHAR(255),
    grade_level        VARCHAR(50) DEFAULT 'college',
    handwriting_style  VARCHAR(50) DEFAULT 'casual',
    paper_type         VARCHAR(50) DEFAULT 'notebook',
    font_name          VARCHAR(100) DEFAULT 'Caveat',
    generated_answer   TEXT,
    sections_json      JSONB,
    has_diagram        BOOLEAN DEFAULT FALSE,
    has_math           BOOLEAN DEFAULT FALSE,
    pdf_url            VARCHAR(1000),
    thumbnail_url      VARCHAR(1000),
    page_count         INTEGER DEFAULT 0,
    status             VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message      TEXT,
    task_id            VARCHAR(255),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at       TIMESTAMPTZ
);

CREATE INDEX idx_assignments_user_id ON assignments(user_id);
CREATE INDEX idx_assignments_status  ON assignments(status);
CREATE INDEX idx_assignments_created ON assignments(created_at DESC);

-- ──────────────────────────────────────────────────────────
-- PAYMENTS
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_cents INTEGER NOT NULL,
    currency     VARCHAR(10) NOT NULL DEFAULT 'usd',
    provider     VARCHAR(50) NOT NULL,
    provider_id  VARCHAR(255) UNIQUE NOT NULL,
    status       VARCHAR(50) NOT NULL,
    plan         VARCHAR(50) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_payments_user_id ON payments(user_id);

-- ──────────────────────────────────────────────────────────
-- USAGE LOGS (rate limiting)
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usage_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action      VARCHAR(100) NOT NULL,
    usage_date  DATE NOT NULL DEFAULT CURRENT_DATE,
    count       INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_usage_user_date ON usage_logs(user_id, usage_date);

-- ──────────────────────────────────────────────────────────
-- HANDWRITING STYLE PRESETS
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS handwriting_styles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    font_name   VARCHAR(100) NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}',
    preview_url VARCHAR(500),
    is_pro      BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed default styles
INSERT INTO handwriting_styles (name, display_name, font_name, config_json, is_pro)
VALUES
  ('casual',    'Casual',          'Caveat',             '{"rotation": 0.025, "scale": 0.08}', FALSE),
  ('neat',      'Neat & Tidy',     'PatrickHand',        '{"rotation": 0.015, "scale": 0.05}', FALSE),
  ('indie',     'Indie',           'IndieFlower',        '{"rotation": 0.030, "scale": 0.10}', FALSE),
  ('architect', 'Architect',       'ArchitectsDaughter', '{"rotation": 0.020, "scale": 0.06}', TRUE)
ON CONFLICT (name) DO NOTHING;

-- ──────────────────────────────────────────────────────────
-- AUTO-UPDATE TRIGGER FOR users.updated_at
-- ──────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
