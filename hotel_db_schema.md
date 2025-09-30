## `comfort_enum`
Перечисление уровней комфортности номера.  
**Значения:** `standard`, `semi_lux`, `lux`.

---

## `clients`
Хранит информацию о клиентах гостиницы.  
- `id` `SERIAL PRIMARY KEY` — идентификатор клиента  
- `last_name` `VARCHAR(40) NOT NULL` — фамилия  
- `first_name` `VARCHAR(40) NOT NULL` — имя  
- `patronymic` `VARCHAR(40)` — отчество (может быть `NULL`)  
- `passport` `VARCHAR(11) UNIQUE NOT NULL` — паспорт (уникально)  
- `comment` `TEXT` — примечание  
- `is_regular` `BOOLEAN NOT NULL DEFAULT FALSE` — постоянный клиент?  
- `registered` `TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` — дата/время регистрации

---

## `rooms`
Хранит информацию о номерах.  
- `id` `SERIAL PRIMARY KEY` — идентификатор номера  
- `room_number` `INT UNIQUE NOT NULL` — номер комнаты  
- `capacity` `INT NOT NULL CHECK (capacity > 0)` — вместимость (кол-во мест)  
- `comfort` `comfort_enum NOT NULL` — комфорт (`standard|semi_lux|lux`)  
- `price` `NUMERIC(10,2) NOT NULL CHECK (price > 0)` — цена/сутки  
- `amenities` `TEXT[] DEFAULT '{}' CHECK (cardinality(amenities) <= 10)` — массив удобств (массив обязателен по ТЗ)

---

## `stays`
Хранит заселения и бронирования.  
- `id` `SERIAL PRIMARY KEY` — идентификатор записи  
- `client_id` `INT NOT NULL` `REFERENCES clients(id) ON DELETE CASCADE ON UPDATE CASCADE` — клиент  
- `room_id` `INT NOT NULL` `REFERENCES rooms(id) ON DELETE RESTRICT ON UPDATE CASCADE` — номер  
- `check_in` `DATE NOT NULL` — дата заезда  
- `check_out` `DATE NOT NULL` — дата выезда  
- `is_paid` `BOOLEAN NOT NULL DEFAULT FALSE` — **оплачено?** (`TRUE/FALSE`)  
- `note` `TEXT` — примечание  
- `status` `BOOLEAN NOT NULL DEFAULT TRUE` — статус брони/проживания (`TRUE` — активно, `FALSE` — завершено)  
- `ck_dates` `CHECK (check_out > check_in)` — защита от некорректных дат

> Обоснование политик FK:  
> — Для `client_id` используем `ON DELETE CASCADE`, чтобы при удалении клиента автоматически удалялись его бронирования.  
> — Для `room_id` — `ON DELETE RESTRICT`, чтобы **база не позволяла** удалить номер при наличии связанных заселений.