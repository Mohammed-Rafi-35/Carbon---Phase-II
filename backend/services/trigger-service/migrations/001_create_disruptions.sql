CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS disruptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zone TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NULL,
    source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_disruptions_status ON disruptions(status);
CREATE INDEX IF NOT EXISTS ix_disruptions_zone_type_status ON disruptions(zone, type, status);
