-- AI Email Assistant Database Initialization
-- This script sets up the initial database structure

-- Create additional schemas if needed
CREATE SCHEMA IF NOT EXISTS ai_email;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE ai_email_assistant TO ai_email_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO ai_email_user;
GRANT ALL PRIVILEGES ON SCHEMA ai_email TO ai_email_user;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';