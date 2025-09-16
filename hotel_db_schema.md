![[Pasted image 20250913171025.png]]
## comfort_enum
Перечисление уровней комфортности номера.  
Возможные значения: standard, semi_lux, lux.

---

## clients
Хранит информацию о клиентах гостиницы.  

- id SERIAL PRIMARY KEY 
- last_name VARCHAR(40) NOT NULL (фамилия клиента)  
- first_name VARCHAR(40) NOT NULL (имя клиента)  
- patronymic VARCHAR(40) (отчество клиента, может быть NULL)  
- passport VARCHAR(11) UNIQUE NOT NULL (паспортные данные, уникальные для каждого клиента)  
- comment TEXT (дополнительный комментарий о клиенте)  
- is_regular BOOLEAN NOT NULL DEFAULT false (является ли клиент постоянным)  
- registered TIMESTAMP NOT NULL (дата и время регистрации клиента в системе)

---

## rooms
Хранит информацию о номерах гостиницы.  

- id SERIAL PRIMARY KEY 
- room_number INT UNIQUE NOT NULL (номер комнаты в гостинице)  
- capacity INT NOT NULL CHECK (capacity > 0) (вместимость номера, количество мест)  
- comfort comfort_enum NOT NULL (уровень комфортности: стандарт, полулюкс, люкс)  
- price NUMERIC(10,2) NOT NULL CHECK (price > 0) (стоимость проживания за сутки)

---
## stays
Хранит информацию о заселениях и бронированиях.  

- client_id INT NOT NULL FOREIGN KEY → clients(id) (клиент, который заселяется или бронирует)  
- room_id INT NOT NULL FOREIGN KEY → rooms(id) (номер, в который заселяется клиент)  
- check_in DATE NOT NULL (дата заселения)  
- check_out DATE NOT NULL(дата выезда)  
- is_paid BOOLEAN NOT NULL DEFAULT false (статус: активно = true, завершено = false)  
- note TEXT (примечание) 
- status BOOLEAN NOT NULL DEFAULT true (статус: активно = true, завершено = false)  
