CREATE TABLE users
(
    id         SERIAL PRIMARY KEY,
    username   VARCHAR(50)                                        NOT NULL UNIQUE,
    password   TEXT                                               NOT NULL,
    admin      BOOLEAN                  DEFAULT FALSE             NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
