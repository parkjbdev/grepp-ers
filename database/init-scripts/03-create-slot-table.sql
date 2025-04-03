CREATE TABLE slots
(
    id         SERIAL PRIMARY KEY NOT NULL,
    time_range TSTZRANGE          NOT NULL,
    EXCLUDE USING gist (time_range WITH &&)
);