CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY,
    event_key VARCHAR(128) UNIQUE NOT NULL,
    event_id VARCHAR(64),
    event_type VARCHAR(64) NOT NULL,
    routing_key VARCHAR(128),
    zone VARCHAR(64),
    user_id VARCHAR(64),
    amount NUMERIC(14, 2),
    status VARCHAR(32),
    risk_category VARCHAR(16),
    event_timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_analytics_events_event_type ON analytics_events (event_type);
CREATE INDEX IF NOT EXISTS ix_analytics_events_event_timestamp ON analytics_events (event_timestamp);
CREATE INDEX IF NOT EXISTS ix_analytics_events_zone ON analytics_events (zone);
CREATE INDEX IF NOT EXISTS ix_analytics_events_user_id ON analytics_events (user_id);

CREATE TABLE IF NOT EXISTS analytics_metrics (
    id UUID PRIMARY KEY,
    metric_type VARCHAR(64) NOT NULL,
    value NUMERIC(14, 4) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    zone VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_analytics_metrics_type_time_zone
    ON analytics_metrics (metric_type, timestamp, zone);

CREATE TABLE IF NOT EXISTS aggregated_stats (
    id UUID PRIMARY KEY,
    metric_name VARCHAR(64) UNIQUE NOT NULL,
    value NUMERIC(14, 4) NOT NULL,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
