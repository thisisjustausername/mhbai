CREATE TABLE IF NOT EXISTS universal_mhbs (
    id SERIAL PRIMARY KEY,
    stud_url TEXT NOT NULL UNIQUE,
    stud_title TEXT,
    name TEXT, 
    city TEXT, 
    university TEXT, 
    degree TEXT, 
    uni_url TEXT UNIQUE,
    search_string TEXT
);

CREATE TABLE IF NOT EXISTS universities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    website TEXT UNIQUE, --- technically also not UNIQUE for same reason as mhb_url, but might be changed before being used
    mhb_url TEXT, -- for now not unique since handling same university from different city separately UNIQUE,
    label_mhb_good BOOLEAN, 
    label_mhb_manually BOOLEAN DEFAULT FALSE,
    UNIQUE (name, city)
);