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

-- stores information about the mhb pdfs and creates a mapping between the unia website and the downloaded pdfs
-- id is the file_name in /pdfs, web_url is the url where the pdf was found, folder is the folder where the pdf is stored, pdf_name is the name of the pdf file, title is the title of the mhb
CREATE TABLE IF NOT EXISTS unia.mhbs (
    id SERIAL PRIMARY KEY, -- id is the file_name in /pdfs
    web_url TEXT NOT NULL UNIQUE,
    folder TEXT NOT NULL,
    pdf_name TEXT,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW());


-- stores regex extracted information about modules from the mhb pdfs
CREATE TABLE IF NOT EXISTS unia.modules (
    id SERIAL PRIMARY KEY, -- unique id for each module
    module_code TEXT NOT NULL,  -- module code of each module, not unique since for each module multiple versions exist
    content TEXT, -- extracted text from field "Inhalt"
    goals TEXT, -- extracted text from field "Lernziele"
    title TEXT NOT NULL, -- title of the module
    ects INTEGER, -- ects points of the module
    pages JSONB, -- pages in the mhb where the module is located
    mhb_id INTEGER REFERENCES unia.mhbs(id), -- reference to the mhb where the module is located in
    created_at TIMESTAMPTZ DEFAULT NOW()
    );


-- create table for ai extracted module information
-- every information in this table is extracted using ai
CREATE TABLE IF NOT EXISTS unia.modules_ai_extracted (
    id SERIAL PRIMARY KEY, -- unique id for each module version
    title TEXT, -- title of the module
    module_code TEXT NOT NULL, -- not unique since for each module multiple versions exist
    ects INTEGER, -- ects points of the module
    lecturer TEXT, -- lecturer of the module
    contents JSONB, -- content of the module (multiple paragraphs possible, similar to unia.modules.content)
    goals JSONB, -- goals of the module (multiple paragraphs possible, similar to unia.modules.goals)
    requirements JSONB, -- requirements of the module
    expense JSONB, -- expense of the module
    success_requirements JSONB, -- success requirements of the module
    weekly_hours INTEGER, -- weekly hours required for the module
    recommended_semester INTEGER, -- recommended semester for the module
    exams JSONB, -- exams related to the module
    module_parts JSONB, -- parts of the module
    raw_module_id INTEGER NOT NULL REFERENCES unia.modules_raw(id), -- reference to the raw module text from which this ai extracted module was created
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- create table for raw module texts used for ai extraction
-- this table is used to store the raw module texts before they are processed by ai
CREATE TABLE IF NOT EXISTS unia.modules_raw (
    id SERIAL PRIMARY KEY, -- unique id for each raw module text
    module_code TEXT NOT NULL, -- module code of the module (extracted using regex, not unique since for each module multiple versions exist)
    content TEXT, -- full raw module text used for ai extraction
    content_md5 TEXT GENERATED ALWAYS AS (md5(content)) STORED, -- md5 hash of the content to ensure uniqueness (using less storage space than content)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (module_code, content_md5) -- ensure that for each module code the same raw content is not stored multiple times
);


-- create backup-table for already ai extracted module information
-- this table is used to store the ai extracted module information, that was extracted using llama3:70b !!!
CREATE TABLE IF NOT EXISTS unia.modules_ai_extracted_backup (
    id SERIAL PRIMARY KEY, -- unique id for each module version
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


-- create relation table between mhbs and modules_raw
CREATE TABLE IF NOT EXISTS unia.mhbs_modules_raw_relation (
  id SERIAL PRIMARY KEY,
  mhb_id INTEGER REFERENCES(unia.mhbs.id),
  modules_raw_id INTEGER REFERENCES(unia.modules_raw.id),
  UNIQUE(mhb_id, modules_raw_id)
);


CREATE OR REPLACE FUNCTION insert_modules_raw_relation_func()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.module_code IS NULL AND NEW.content IS NULL THEN
        INSERT INTO unia.mhbs_modules_raw_relation (mhb_id, modules_raw_id)
        VALUES (NEW.mhb_id, NEW.modules_raw_id)
        RETURNING id INTO NEW.id;
        RETURN NEW.id;

    ELSIF NEW.mhb_id IS NULL AND NEW.modules_raw_id IS NULL THEN
        INSERT INTO unia.modules_raw (module_code, content)
        VALUES (NEW.module_code, NEW.content)
        ON CONFLICT (module_code, content_md5) DO NOTHING
        RETURNING id INTO NEW.id;
        RETURN NEW.id;

    ELSIF NEW.mhb_id IS NOT NULL AND NEW.modules_raw_id IS NOT NULL AND NEW.module_code IS NOT NULL AND NEW.content IS NOT NULL THEN
        INSERT INTO unia.modules_raw (module_code, content)
        VALUES (NEW.module_code, NEW.content)
        ON CONFLICT (module_code, content_md5) DO NOTHING
        RETURNING id INTO NEW.modules_raw_id;

        INSERT INTO unia.mhbs_modules_raw_relation (mhb_id, modules_raw_id)
        VALUES (NEW.mhb_id, NEW.modules_raw_id)
        RETURNING id INTO NEW.mhbs_modules_raw_relation_id;

        RETURN 
    END IF;
END
$$ LANGUAGE plpgsql;


CREATE OR REPLACE TRIGGER insert_mhbs_modules_raw_relation
INSTEAD OF INSERT ON unia.mhbs_modules_raw_relation
OR INSERT ON unia.modules_raw
EXECUTE FUNCTION insert_mhbs_modules_raw_relation_func();


/*
-- create mapping from url -> file_name -> number_name
CREATE TABLE IF NOT EXISTS unia.url_file_number_mapping (
    id SERIAL PRIMARY KEY,
    web_url TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL UNIQUE,
    number_name INTEGER NOT NULL UNIQUE
);
*/
