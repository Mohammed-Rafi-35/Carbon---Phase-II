-- Carbon Platform cluster bootstrap for schema-isolated microservices.
-- Run this once on the target PostgreSQL cluster with a privileged role.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS identity;
CREATE SCHEMA IF NOT EXISTS policy;
CREATE SCHEMA IF NOT EXISTS claims;
CREATE SCHEMA IF NOT EXISTS fraud;
CREATE SCHEMA IF NOT EXISTS payout;
CREATE SCHEMA IF NOT EXISTS notification;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS trigger;
CREATE SCHEMA IF NOT EXISTS ai_risk;

-- Optional least-privilege role layout (uncomment and adjust passwords for managed deployments).
-- CREATE ROLE identity_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE policy_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE claims_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE fraud_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE payout_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE notification_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE analytics_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE trigger_service LOGIN PASSWORD 'replace-me';
-- CREATE ROLE ai_risk_service LOGIN PASSWORD 'replace-me';

-- GRANT USAGE ON SCHEMA identity TO identity_service;
-- GRANT USAGE ON SCHEMA policy TO policy_service;
-- GRANT USAGE ON SCHEMA claims TO claims_service;
-- GRANT USAGE ON SCHEMA fraud TO fraud_service;
-- GRANT USAGE ON SCHEMA payout TO payout_service;
-- GRANT USAGE ON SCHEMA notification TO notification_service;
-- GRANT USAGE ON SCHEMA analytics TO analytics_service;
-- GRANT USAGE ON SCHEMA trigger TO trigger_service;
-- GRANT USAGE ON SCHEMA ai_risk TO ai_risk_service;

-- ALTER ROLE identity_service IN DATABASE postgres SET search_path TO identity, public;
-- ALTER ROLE policy_service IN DATABASE postgres SET search_path TO policy, public;
-- ALTER ROLE claims_service IN DATABASE postgres SET search_path TO claims, public;
-- ALTER ROLE fraud_service IN DATABASE postgres SET search_path TO fraud, public;
-- ALTER ROLE payout_service IN DATABASE postgres SET search_path TO payout, public;
-- ALTER ROLE notification_service IN DATABASE postgres SET search_path TO notification, public;
-- ALTER ROLE analytics_service IN DATABASE postgres SET search_path TO analytics, public;
-- ALTER ROLE trigger_service IN DATABASE postgres SET search_path TO trigger, public;
-- ALTER ROLE ai_risk_service IN DATABASE postgres SET search_path TO ai_risk, public;
