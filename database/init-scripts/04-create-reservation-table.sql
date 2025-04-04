CREATE TABLE reservations
(
    id           SERIAL PRIMARY KEY                                 NOT NULL,
    slot_id      INTEGER                                            NOT NULL
        CONSTRAINT "reservations__slots.id_fk" REFERENCES slots (id),
    user_id      INTEGER                                            NOT NULL
        CONSTRAINT "reservations__users.id_fk" REFERENCES users (id),
    amount       INTEGER                  DEFAULT 0                 NOT NULL CHECK (amount >= 0 AND amount <= 50000),
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
    slot_count INTEGER;
    dummy      INTEGER;
BEGIN
    IF (NEW.confirmed = TRUE AND OLD.confirmed = FALSE) THEN
        NEW.confirmed_at = CURRENT_TIMESTAMP;
    ELSIF (NEW.confirmed = FALSE AND OLD.confirmed = TRUE) THEN
        NEW.confirmed_at = NULL;
    END IF;

    -- admin
    -- 컨펌됐거나, 이미 컨펌된 상태에서 amount가 변경된 경우
    IF (NEW.confirmed = TRUE AND (OLD.confirmed = FALSE OR NEW.amount != OLD.amount)) THEN
        -- lock rows with same slot_id
        SELECT 1
        INTO dummy
        FROM reservations
        WHERE slot_id = NEW.slot_id
        ORDER BY id FOR UPDATE;

        -- slot_count = count reserved population
        SELECT COALESCE(SUM(amount), 0)
        INTO slot_count
        FROM reservations
        WHERE slot_id = NEW.slot_id
          AND confirmed = TRUE
          AND id != OLD.id;

        IF (slot_count + NEW.amount > 50000) THEN
            RAISE EXCEPTION 'SlotLimitExceeded' USING DETAIL = 'Slot population limit 50000 exceeded';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_confirmedtime
    BEFORE UPDATE
    ON reservations
    FOR EACH ROW
EXECUTE FUNCTION update_confirmed_col();

-- reservations table TRIGGER: check slot limit on insert
CREATE OR REPLACE FUNCTION check_slot_limit_on_insert()
    RETURNS TRIGGER AS
$$
DECLARE
    slot_count INTEGER;
    dummy      INTEGER;
BEGIN
    -- lock rows with same slot_id
    SELECT 1
    INTO dummy
    FROM reservations
    WHERE slot_id = NEW.slot_id
    ORDER BY id FOR UPDATE;

    -- slot_count = count reserved population
    SELECT COALESCE(SUM(amount), 0)
    INTO slot_count
    FROM reservations
    WHERE slot_id = NEW.slot_id
      AND confirmed = TRUE;

    -- check if adding new reservation would exceed the limit
    IF (slot_count + NEW.amount > 50000) THEN
        RAISE EXCEPTION 'SlotLimitExceeded' USING DETAIL = 'Slot population limit 50000 exceeded';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_slot_limit_before_insert
    BEFORE INSERT
    ON reservations
    FOR EACH ROW
EXECUTE FUNCTION check_slot_limit_on_insert();