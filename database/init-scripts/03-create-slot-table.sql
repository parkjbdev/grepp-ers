CREATE TABLE slots
(
    id         SERIAL PRIMARY KEY NOT NULL,
    time_range TSTZRANGE          NOT NULL,
    EXCLUDE USING gist (time_range WITH &&)
);

-- GRANT PERMISSIONS
ALTER TABLE slots
    OWNER TO greppers;

GRANT ALL PRIVILEGES ON slots TO "greppers";
