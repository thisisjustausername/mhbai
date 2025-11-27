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
CREATE TABLE IF NOT EXISTS all_unis.universities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    website TEXT UNIQUE,
    type_of_institution TEXT, 
    logo_url TEXT,
    source_url TEXT, 
    UNIQUE (name, city, source_url)
);


CREATE TABLE IF NOT EXISTS all_unis.mhbs (
    id SERIAL PRIMARY KEY,
    web_id TEXT, 
    source_url TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL, 
    name TEXT NOT NULL, 
    university INT REFERENCES all_unis.universities(id) NOT NULL, 
    degree TEXT NOT NULL, 
    duration INT, 
    study_type TEXT[], 
    search_string TEXT
);


CREATE TABLE IF NOT EXISTS all_unis.prototyping_mhbs (
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

CREATE TABLE IF NOT EXISTS all_unis.prototyping_universities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    website TEXT UNIQUE, --- technically also not UNIQUE for same reason as mhb_url, but might be changed before being used
    mhb_url TEXT, -- for now not unique since handling same university from different city separately UNIQUE,
    label_mhb_good BOOLEAN, 
    label_mhb_manually BOOLEAN DEFAULT FALSE,
    UNIQUE (name, city)
);


-- create views

-- view combining mhbs and universities for easier inserts
CREATE OR REPLACE VIEW all_unis.mhbs_unis AS
    SELECT all_unis.mhbs.*, all_unis.universities.name AS university_name, all_unis.universities.city, all_unis.universities.type_of_institution
    FROM all_unis.mhbs
    JOIN all_unis.universities ON all_unis.mhbs.university = all_unis.universities.id;


-- create triggers

-- define insert into for mhbs_unis view
CREATE OR REPLACE FUNCTION mhbs_unis_insert()
RETURNS TRIGGER AS $$
DECLARE 
    uni_id INT;
    mhbs_row all_unis.mhbs%ROWTYPE;
BEGIN
    uni_id := NULL;

    -- Insert into all_unis.universities
    INSERT INTO all_unis.universities (name, city, source_url, type_of_institution)
    VALUES (NEW.university_name, NEW.city, NEW.source_url, NEW.type_of_institution)
    ON CONFLICT (name, city, source_url) DO NOTHING
    RETURNING id INTO uni_id;

    -- if insert did not happen, select existing id
    IF uni_id IS NULL THEN
        SELECT id 
        INTO uni_id 
        FROM all_unis.universities 
        WHERE name = NEW.university_name 
            AND city = NEW.city 
            AND source_url = NEW.source_url 
        LIMIT 1;
    END IF;

    -- build mhbs_row record
    mhbs_row := jsonb_populate_record(
        NULL::all_unis.mhbs, 
        to_jsonb(NEW)
        - 'university_name' 
        - 'city' 
        - 'type_of_institution'
        || jsonb_build_object('university', uni_id)
    );
    mhbs_row.id := nextval(pg_get_serial_sequence('all_unis.mhbs','id'));

    -- insert into all_unis.mhbs
    INSERT INTO all_unis.mhbs
    VALUES (mhbs_row.*);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER mhbs_unis_insert_trigger
INSTEAD OF INSERT ON all_unis.mhbs_unis
FOR EACH ROW
EXECUTE FUNCTION mhbs_unis_insert();


-- trigger to create search string before inserting or updating universal mhbs
CREATE OR REPLACE FUNCTION add_search_string()
    RETURNS TRIGGER AS
$$
BEGIN
    IF (NEW.university, NEW.name, NEW.degree) IS NOT DISTINCT FROM (OLD.university, OLD.name, OLD.degree) OR
       NEW.search_string IS NOT NULL THEN
        RETURN NEW; -- no changes, do nothing
    END IF;

    NEW.search_string := RTRIM(CONCAT('site:', (SELECT website FROM all_unis.universities WHERE id = NEW.university LIMIT 1), ' filetype:pdf modulhandbuch ', NEW.name, ' ', COALESCE(
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
    ON all_unis.mhbs
    FOR EACH ROW
EXECUTE FUNCTION add_search_string();

/*
-- trigger to check that if one of name, uni_url, or search_string is provided, all three are provided
CREATE OR REPLACE FUNCTION check_inserted_vals()
    RETURNS TRIGGER AS
$$
DECLARE
    vals TEXT[3] := ARRAY [NEW.name, NEW.university, NEW.degree];
BEGIN
    IF (SELECT COUNT(*) FROM unnest(vals) AS col WHERE col IS NOT NULL) > 0 AND
       (SELECT COUNT(*) FROM unnest(vals) AS col WHERE col IS NULL) > 0 THEN
        RAISE EXCEPTION 'If one of name, university, or degree is provided, all three must be provided.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_inserted_vals_trigger
    BEFORE INSERT
    ON all_unis.mhbs
    FOR EACH ROW
EXECUTE FUNCTION check_inserted_vals();
*/