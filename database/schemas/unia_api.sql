-- Description: create tables, types, check functions for database

-- SET DateStyle TO ISO, YMD;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- enum for user_role in table users
CREATE TYPE USER_ROLE AS ENUM ('admin', 'user');

CREATE SCHEMA IF NOT EXISTS unia;

-- table to save users
CREATE TABLE IF NOT EXISTS unia.users (
    id SERIAL PRIMARY KEY,
    user_role USER_ROLE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$' OR password_hash is NULL),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_uuid UUID UNIQUE NOT NULL, -- added for personal references, not as easy to guess as id
    last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    user_name TEXT NOT NULL,
    organization TEXT NOT NULL
);

-- table to save login sessions
CREATE TABLE IF NOT EXISTS unia.sessions (
    id SERIAL PRIMARY KEY,
    expiration_date TIMESTAMPTZ NOT NULL,
    user_id INTEGER REFERENCES unia.users(id) ON DELETE CASCADE NOT NULL,
    session_id UUID NOT NULL UNIQUE
);

-- table to save configuration settings
CREATE TABLE IF NOT EXISTS unia.configurations (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- set default configuration values
INSERT INTO unia.configurations (key, value) VALUES
('session_expiration_days', '30'),
('reset_code_expiration_minutes', '15');

CREATE TABLE IF NOT EXISTS unia.verification_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES unia.users(id) ON DELETE CASCADE,
    reset_code UUID UNIQUE NOT NULL,
    additional_data JSONB DEFAULT NULL, -- to store optional changes in users
    used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

/*
-- error table
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    error_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    raised_by INTEGER REFERENCES unia.error_logs(id), -- self reference for errors raised by error handling
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    raised_python TEXT,
    actions_taken BOOLEAN DEFAULT FALSE
);
*/
