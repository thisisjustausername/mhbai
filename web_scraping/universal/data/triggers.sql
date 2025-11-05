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


CREATE OR REPLACE FUNCTION add_search_string()
    RETURNS TRIGGER AS
$$
BEGIN
    IF (NEW.uni_url, NEW.name, NEW.degree) IS NOT DISTINCT FROM (OLD.uni_url, OLD.name, OLD.degree) OR
       NEW.search_string IS NOT NULL THEN
        RETURN NEW; -- no changes, do nothing
    END IF;

    NEW.search_string := RTRIM(CONCAT('page:', NEW.uni_url, ' filetype:pdf modulhandbuch ', NEW.name, ' ', COALESCE(
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


CREATE OR REPLACE TRIGGER check_inserted_vals_trigger
    BEFORE INSERT
    ON universal_mhbs
    FOR EACH ROW
EXECUTE FUNCTION check_inserted_vals();



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
    ON universal_mhbs
    FOR EACH ROW
EXECUTE FUNCTION add_university();