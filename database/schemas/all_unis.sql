-- Copyright (c) 2025 Leon Gattermeyer

-- This file is part of mhbai.

-- Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.--
-- Description: create schema, tables and triggers for all universities
-- STATUS: VERSION 1.0
-- FileID: Da-sc-0002


-- create schema for university of augsburg

CREATE schema IF NOT EXISTS all_unis
AUTHORIZATION gatterle;


-- create tables

CREATE TABLE IF NOT EXISTS all_unis.universal_mhbs (
    id SERIAL PRIMARY KEY,
    source_url TEXT NOT NULL UNIQUE,
    source_title TEXT,
    source TEXT, 
    name TEXT, 
    city TEXT, 
    university TEXT, 
    degree TEXT, 
    uni_url TEXT,
    search_string TEXT, 
    additional_info JSONB
);

CREATE TABLE IF NOT EXISTS all_unis.universities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    website TEXT UNIQUE, --- technically also not UNIQUE for same reason as mhb_url, but might be changed before being used
    mhb_url TEXT, -- for now not unique since handling same university from different city separately UNIQUE,
    label_mhb_good BOOLEAN, 
    label_mhb_manually BOOLEAN DEFAULT FALSE,
    UNIQUE (name, city)
);


-- create triggers

-- trigger to add university to universities table when inserting mhbs into universal_mhbs
CREATE OR REPLACE FUNCTION add_university()
    RETURNS TRIGGER AS
$$
BEGIN
    INSERT INTO universities (name, city)
    VALUES (NEW.university, NEW.city)
    ON CONFLICT (name, city) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER add_university_trigger
    BEFORE INSERT OR UPDATE
    ON all_unis.universal_mhbs
    FOR EACH ROW
EXECUTE FUNCTION add_university();


-- trigger to create search string before inserting or updating universal mhbs
CREATE OR REPLACE FUNCTION add_search_string()
    RETURNS TRIGGER AS
$$
BEGIN
    IF (NEW.uni_url, NEW.name, NEW.degree) IS NOT DISTINCT FROM (OLD.uni_url, OLD.name, OLD.degree) OR
       NEW.search_string IS NOT NULL THEN
        RETURN NEW; -- no changes, do nothing
    END IF;

    NEW.search_string := RTRIM(CONCAT('site:', NEW.uni_url, ' filetype:pdf modulhandbuch ', NEW.name, ' ', COALESCE(
                                                                                                                       CASE
                                                                                                                           WHEN NEW.degree IS NOT NULL AND NEW.degree ILIKE '%bachelor%'
                                                                                                                               THEN 'Bachelor'
                                                                                                                           WHEN NEW.degree IS NOT NULL AND NEW.degree ILIKE '%master%'
                                                                                                                               THEN 'Master'
                                                                                                                           ELSE NULL
                                                                                                                           END, '')
                                                                                                               /*
                                                                                                               (CASE 
                                                                                                                   WHEN OLD.degree IS NOT NULL
                                                                                                                       THEN OLD.degree
                                                                                                                   ELSE ''
                                                                                                                END)
                                                                                                                */
                                            )
                                );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER add_search_string_trigger
    BEFORE INSERT OR UPDATE
    ON all_unis.universal_mhbs
    FOR EACH ROW
EXECUTE FUNCTION add_search_string();


-- trigger to check that if one of name, uni_url, or search_string is provided, all three are provided
CREATE OR REPLACE FUNCTION check_inserted_vals()
    RETURNS TRIGGER AS
$$
DECLARE
    vals TEXT[3] := ARRAY [NEW.name, NEW.university, NEW.degree, NEW.city]; -- NEW.uni_url removed since added after fetching base data
BEGIN
    IF (SELECT COUNT(*) FROM unnest(vals) AS col WHERE col IS NOT NULL) > 0 AND
       (SELECT COUNT(*) FROM unnest(vals) AS col WHERE col IS NULL) > 0 THEN
        RAISE EXCEPTION 'If one of title, uni_url, or search_string is provided, all three must be provided.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_inserted_vals_trigger
    BEFORE INSERT
    ON all_unis.universal_mhbs
    FOR EACH ROW
EXECUTE FUNCTION check_inserted_vals();