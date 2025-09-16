DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'comfort_enum') THEN
        CREATE TYPE comfort_enum AS ENUM ('standard', 'semi_lux', 'lux');
    END IF;
END
$$ LANGUAGE plpgsql;


CREATE TABLE IF NOT EXISTS clients (
  id SERIAL PRIMARY KEY,
  last_name VARCHAR(40) NOT NULL,
  first_name VARCHAR(40) NOT NULL,
  patronymic VARCHAR(40),
  passport VARCHAR(11) UNIQUE NOT NULL,
  comment TEXT,
  is_regular BOOLEAN NOT NULL DEFAULT FALSE,
  registered TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rooms (
  id SERIAL PRIMARY KEY,
  room_number INT UNIQUE NOT NULL,
  capacity INT NOT NULL CHECK (capacity > 0),
  comfort comfort_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS stays (
  id SERIAL PRIMARY KEY,
  client_id INT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  room_id INT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  check_in DATE NOT NULL,
  check_out DATE NOT NULL,
  CONSTRAINT ck_dates CHECK (check_out > check_in)
);