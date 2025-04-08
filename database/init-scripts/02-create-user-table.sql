CREATE TABLE users
(
    id         SERIAL PRIMARY KEY,
    username   VARCHAR(50)                                        NOT NULL UNIQUE,
    password   TEXT                                               NOT NULL,
    admin      BOOLEAN                  DEFAULT FALSE             NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- TODO: REMOVE THIS AFTER TESTING
-- Test Admin
INSERT INTO users (username, password, admin)
VALUES ('admin', '$argon2id$v=19$m=65536,t=3,p=4$zmxfD0y7SqFVHtQEIuNDXg$vJmxTwkDpEpQ4SPj2L6GRwozxnB0O9sngkkr1akNFic',
        TRUE);

-- Test User
INSERT INTO users (username, password, admin)
VALUES ('user', '$argon2id$v=19$m=65536,t=3,p=4$zmxfD0y7SqFVHtQEIuNDXg$vJmxTwkDpEpQ4SPj2L6GRwozxnB0O9sngkkr1akNFic',
        TRUE);
