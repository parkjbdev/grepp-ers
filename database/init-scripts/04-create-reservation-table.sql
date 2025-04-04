CREATE TABLE reservations
(
    id           SERIAL PRIMARY KEY                                 NOT NULL,
    slot_id      INTEGER                                            NOT NULL
        CONSTRAINT "reservations__slots.id_fk" REFERENCES slots (id),
    user_id      INTEGER                                            NOT NULL
        CONSTRAINT "reservations__users.id_fk" REFERENCES users (id),
    amount        INTEGER                  DEFAULT 0                 NOT NULL CHECK (amount >= 0),
    confirmed    bool                     DEFAULT FALSE             NOT NULL,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE                           NULL,
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- reservations table TRIGGER: update modification
CREATE OR REPLACE FUNCTION update_modified_col()
    RETURNS TRIGGER AS
$$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_updatedtime
    BEFORE UPDATE
    ON reservations
    FOR EACH ROW
EXECUTE FUNCTION update_modified_col();

-- reservations table TRIGGER: confirm reservation
CREATE OR REPLACE FUNCTION update_confirmed_col()
    RETURNS TRIGGER AS
$$
DECLARE
    slot_count INTEGER; -- Declare the variable here
BEGIN
    IF (NEW.confirmed = OLD.confirmed) THEN
        RETURN NEW;
    END IF;

    IF (NEW.confirmed = TRUE) THEN
        -- count reserved population
        SELECT COALESCE(SUM(amount), 0)
        INTO slot_count
        FROM reservations
        WHERE slot_id = OLD.slot_id
          AND confirmed = TRUE;
        IF (slot_count + OLD.amount > 50000) THEN
            RAISE EXCEPTION 'SlotLimitExceeded' USING DETAIL = 'Slot population limit 50000 exceeded';
        END IF;

        NEW.confirmed_at = CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_confirmedtime
    BEFORE UPDATE
    ON reservations
    FOR EACH ROW
EXECUTE FUNCTION update_confirmed_col();