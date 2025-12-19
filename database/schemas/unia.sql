-- Copyright (c) 2025 Leon Gattermeyer

-- This file is part of mhbai.

-- Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.--
-- Description: create schema, tables and triggers for university of augsburg
-- STATUS: VERSION 1.0
-- FileID: Da-sc-0001


-- create schema for university of augsburg

CREATE schema IF NOT EXISTS unia
AUTHORIZATION gatterle;


-- create tables

CREATE TABLE IF NOT EXISTS unia.mhbs (
    id SERIAL PRIMARY KEY,
    web_url TEXT NOT NULL UNIQUE, 
    folder TEXT NOT NULL, 
    pdf_name TEXT,
    title TEXT);

CREATE TABLE IF NOT EXISTS unia.modules (
    id SERIAL PRIMARY KEY,
    module_code TEXT UNIQUE NOT NULL, 
    content TEXT, 
    goals TEXT, 
    title TEXT NOT NULL, 
    ects INTEGER
    );

CREATE TABLE IF NOT EXISTS unia.mhbs_modules_link (
    id SERIAL PRIMARY KEY,
    mhb_id INTEGER REFERENCES unia.mhbs(id) ON DELETE CASCADE,
    module_id INTEGER REFERENCES unia.modules(id) ON DELETE CASCADE,
    pages JSONB, 
    UNIQUE (mhb_id, module_id)
    );

-- create table for ai extracted module information
CREATE TABLE IF NOT EXISTS unia.modules_ai_extracted (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    module_code TEXT UNIQUE NOT NULL,
    ects INTEGER,
    lecturer TEXT,
    contents JSONB, 
    goals JSONB, 
    requirements JSONB, 
    expense JSONB,
    success_requirements JSONB,
    weekly_hours INTEGER,
    recommended_semester INTEGER,
    exams JSONB, 
    module_parts JSONB
)