CREATE TABLE users
(
    id         SERIAL PRIMARY KEY,
    username   VARCHAR(30)                                        NOT NULL UNIQUE,
    password   TEXT                                               NOT NULL,
    admin      BOOLEAN                  DEFAULT FALSE             NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- users TRIGGER: hash password on insert
CREATE OR REPLACE FUNCTION users_insert()
    RETURNS TRIGGER AS
$$
BEGIN
    NEW.password := crypt(NEW.password, gen_salt('bf'));
    RETURN NEW;
END;
$$
    LANGUAGE plpgsql;

CREATE TRIGGER hash_pw_on_insert
    BEFORE INSERT
    ON users
    FOR EACH ROW
EXECUTE FUNCTION users_insert();


-- users login function
-- usage: SELECT * FROM login('admin', 'secure_password');
CREATE OR REPLACE FUNCTION login(
    p_username VARCHAR(30),
    p_password TEXT
)
    RETURNS TABLE
            (
                id       INTEGER,
                username VARCHAR(30),
                admin    BOOLEAN
            )
AS
$$
BEGIN
    RETURN QUERY
        SELECT u.id, u.username, u.admin
        FROM users u
        WHERE u.username = p_username
          AND u.password = crypt(p_password, u.password);
END;
$$ LANGUAGE plpgsql;

--  CREATE TRIGGER select_with_hashed_password
--     BEFORE
