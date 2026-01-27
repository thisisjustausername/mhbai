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
    id SERIAL PRIMARY KEY, -- id is the file_name in /pdfs
    web_url TEXT NOT NULL UNIQUE,
    folder TEXT NOT NULL,
    pdf_name TEXT,
    title TEXT);

CREATE TABLE IF NOT EXISTS unia.modules (
    id SERIAL PRIMARY KEY,
    module_code TEXT NOT NULL,
    content TEXT,
    goals TEXT,
    title TEXT NOT NULL,
    ects INTEGER,
    pages JSONB,
    mhb_id INTEGER REFERENCES unia.mhbs(id)
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
    title TEXT,
    module_code TEXT NOT NULL, -- not unique since for each module multiple versions exist
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
    module_parts JSONB,
    raw_module_id INTEGER REFERENCES unia.modules_raw(id) NOT NULL
);

CREATE TABLE IF NOT EXISTS unia.modules_raw (
    id SERIAL PRIMARY KEY,
    module_code TEXT NOT NULL,
    content TEXT,
    content_md5 TEXT GENERATED ALWAYS AS (md5(content)) STORED,
    UNIQUE (module_code, content_md5)
);


-- create backup-table for already ai extracted module information
CREATE TABLE IF NOT EXISTS unia.modules_ai_extracted_backup (
    id SERIAL PRIMARY KEY,
    title TEXT,
    module_code TEXT NOT NULL, -- not unique since for each module multiple versions exist
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
);


CREATE TABLE IF NOT EXISTS unia.mhbs_to_modules_raw (
  id SERIAL PRIMARY KEY,
  mhb_id INTEGER REFERENCES(unia.mhbs.id),
  modules_raw_id INTEGER REFERENCES(unia.modules_raw.id)
);
/*
-- create mapping from url -> file_name -> number_name
CREATE TABLE IF NOT EXISTS unia.url_file_number_mapping (
    id SERIAL PRIMARY KEY,
    web_url TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL UNIQUE,
    number_name INTEGER NOT NULL UNIQUE
);
*/
