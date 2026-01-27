CREATE OR REPLACE FUNCTION set_uuid_hash()
RETURNS trigger AS $$
BEGIN
    NEW.user_uuid := gen_random_uuid();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_session_id()
RETURNS trigger AS $$
BEGIN
    IF OLD.session_id IS NULL
    THEN
        NEW.session_id := gen_random_uuid();
    ELSE
        NEW.session_id := OLD.session_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_reset_code()
RETURNS trigger AS $$
BEGIN
    IF OLD.reset_code IS NULL
    THEN
        NEW.reset_code := gen_random_uuid();
    ELSE
        NEW.reset_code := OLD.reset_code;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_user_constants()
RETURNS trigger AS $$
BEGIN
    IF NEW.user_uuid != OLD.user_uuid AND OLD.user_uuid IS NOT NULL
    THEN
        RAISE EXCEPTION 'user_uuid is constant and cannot be changed after being initialized';
    END IF;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE TRIGGER set_uuid_hash_trigger
    BEFORE INSERT ON unia.users -- only on insert
    FOR EACH ROW EXECUTE FUNCTION set_uuid_hash();

CREATE OR REPLACE TRIGGER check_user_constants
    BEFORE UPDATE ON unia.users -- only on updates
    FOR EACH ROW EXECUTE FUNCTION check_user_constants();

CREATE OR REPLACE TRIGGER set_session_id_trigger
    BEFORE INSERT OR UPDATE ON unia.sessions
    FOR EACH ROW EXECUTE FUNCTION set_session_id();

CREATE OR REPLACE TRIGGER set_reset_code_trigger
    BEFORE INSERT ON unia.verification_codes
    FOR EACH ROW EXECUTE FUNCTION set_reset_code();
