DROP SCHEMA public CASCADE;
CREATE SCHEMA public;


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
  comfort comfort_enum NOT NULL,
  price NUMERIC(10,2) NOT NULL CHECK (price > 0),
  amenities TEXT[] DEFAULT '{}' CHECK (cardinality(amenities) <= 10)
);

CREATE TABLE IF NOT EXISTS stays (
  id SERIAL PRIMARY KEY,
  client_id INT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  room_id INT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  check_in DATE NOT NULL,
  check_out DATE NOT NULL,
  is_paid BOOLEAN NOT NULL DEFAULT false,
  note TEXT,
  status BOOLEAN NOT NULL DEFAULT true,
  CONSTRAINT ck_dates CHECK (check_out > check_in)
);

-- Базовые клиенты
INSERT INTO clients (last_name, first_name, patronymic, passport, comment, is_regular)
VALUES
  ('Иванов', 'Алексей', 'Петрович', '1234 567890', 'VIP клиент', true),
  ('Смирнова', 'Елена', NULL, '9876 543210', 'Просит этаж пониже', false);

-- Комнаты
INSERT INTO rooms (room_number, capacity, comfort, price, amenities)
VALUES
  (101, 2, 'standard', 3000.00, ARRAY['Wi-Fi', 'Телевизор']),
  (202, 3, 'lux', 8500.00, ARRAY['Wi-Fi', 'Мини-бар', 'Кондиционер']),
  (303, 1, 'semi_lux', 5200.00, ARRAY['Wi-Fi']);

-- Проживания
INSERT INTO stays (client_id, room_id, check_in, check_out, is_paid, note)
VALUES
  (1, 1, (CURRENT_DATE - INTERVAL '2 days')::date, (CURRENT_DATE + INTERVAL '3 days')::date, true, 'Оплата по безналу'),
  (2, 2, CURRENT_DATE, (CURRENT_DATE + INTERVAL '1 week')::date, false, 'Ожидается предоплата');
