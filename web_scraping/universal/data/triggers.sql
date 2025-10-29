CREATE OR REPLACE FUNCTION check_inserted_vals()
RETURNS TRIGGER AS $$
DECLARE vals TEXT[3] := ARRAY[NEW.name, NEW.university, NEW.degree, NEW.city]; -- NEW.uni_url removed since added after fetching base data
BEGIN
    IF (SELECT COUNT(*) FROM unnest(vals) AS col WHERE col IS NOT NULL) > 0 AND (SELECT COUNT(*) FROM unnest(vals) AS col WHERE col IS NULL) > 0 THEN
        RAISE EXCEPTION 'If one of title, uni_url, or search_string is provided, all three must be provided.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER check_inserted_vals_trigger
BEFORE INSERT ON universal_mhbs
FOR EACH ROW
EXECUTE FUNCTION check_inserted_vals();


CREATE OR REPLACE FUNCTION add_university()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO universities (name, city)
    VALUES (NEW.university, NEW.city)
    ON CONFLICT (name, city) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER add_university_trigger
AFTER INSERT ON universal_mhbs
FOR EACH ROW
EXECUTE FUNCTION add_university();