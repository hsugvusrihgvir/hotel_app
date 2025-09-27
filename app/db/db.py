import psycopg2
from psycopg2 import sql, errors

import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
from app.log.log import HotelLog



class HotelDB:
    def __init__(self):
        self.conn = None
        self.cur = None

        self.log = HotelLog()

        load_dotenv(encoding='utf-8')

        self.DB_NAME = "hotel_db" # имя бд
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASS = os.getenv("DB_PASS")
        self.DB_HOST = os.getenv("DB_HOST")
        self.DB_PORT = os.getenv("DB_PORT")

    # преобразует ошибки в понятный человеку язык
    def _friendly_db_error(self, e: Exception):
        if isinstance(e, errors.UniqueViolation):
            return "Нарушение уникальности: запись с такими уникальными данными уже существует (UNIQUE)."
        if isinstance(e, errors.NotNullViolation):
            return "Нарушение NOT NULL: заполните все обязательные поля."
        if isinstance(e, errors.CheckViolation):
            return "Нарушение CHECK: проверьте правила (например, датa выезда > даты заезда; вместимость > 0; не более 10 удобств)."
        if isinstance(e, errors.ForeignKeyViolation):
            return "Нарушение внешнего ключа: связанный объект не существует (проверьте клиента/номер)."
        if isinstance(e, errors.InvalidTextRepresentation):
            return "Ошибка типов: неверный формат значения (например, ENUM или DATE)."
        if isinstance(e, errors.NumericValueOutOfRange):
            return "Ошибка диапазона чисел: значение слишком велико/мало."
        if isinstance(e, errors.StringDataRightTruncation):
            return "Строка слишком длинная для этого поля."
        if isinstance(e, psycopg2.OperationalError):
            return "Ошибка подключения к базе: проверьте хост/порт/логин/пароль и наличие базы данных."
        if isinstance(e, psycopg2.DataError):
            return "Ошибка данных: значение не соответствует ожидаемому типу."

        return f"Ошибка БД: {str(e)}"

    def create(self): # создание схемы
        self.log.addInfo("Проверка подключения к БД...")
        if not self.conn or not self.cur: # проверяем подключение
            raise RuntimeError("Нет подключения к БД. Проверьте хост/порт/логин/пароль и наличие базы данных.")
        schema_path = Path(__file__).with_name("schema.sql")
        try:
            self.log.addInfo("Создание схемы БД...")
            with open(schema_path, "r", encoding="utf-8") as f:
                sql = f.read() # из файла
            self.cur.execute(sql)
            self.conn.commit() # выполняем
            self.log.addInfo("Схема БД создана")
            return "OK"
        except Exception as e:
            self.conn.rollback()
            self.log.addError(e)
            raise RuntimeError(f"Ошибка при создании схемы: {self._friendly_db_error(e)}")

    def connect(self): # подключение к бд
        try:
            self.log.addInfo(f"Подключение к БД {self.DB_NAME}...")
            self.conn = psycopg2.connect(
                dbname=self.DB_NAME,
                user=self.DB_USER,
                password=self.DB_PASS,
                host=self.DB_HOST,
                port=self.DB_PORT,
            )
            self.cur = self.conn.cursor()
            self.cur.execute("SET client_encoding TO 'UTF8';")
        except Exception as e:
            self.log.addError(e)
            raise RuntimeError(f"Ошибка подключения к БД: {self._friendly_db_error(e)}")


    def pr_table(self, title): # проверяет есть ли таблица
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        self.cur.execute("""  
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = %s
                    );
                """, (title,))
        exists = self.cur.fetchone()[0]
        return bool(exists)

    def close(self): # закрыть соединение
        self.log.addInfo(f"Закрытие подключения к БД...")
        if self.cur is not None:
            self.cur.close()
            self.cur = None
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        self.log.addInfo(f"Подключение к БД закрыто")

    # записывает данные клиента из интерфейса
    def enterDataClient(self, dct): # передается словарь с данными
        self.log.addInfo(f"Записываются данные клиента...")
        try:
            _ = self.pr_table("clients") # проверяем, что таблица есть
        except Exception as e:
            raise RuntimeError(e)
        if not _:
            raise RuntimeError("Таблицы не существует, создайте схему")
        s = """
                        INSERT INTO clients (last_name, first_name, patronymic, passport, comment, is_regular, registered)
                        VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """
        try:
            self.cur.execute(s, (dct["last_name"], dct["first_name"], dct["patronymic"], dct["passport"], dct["comment"], dct["is_regular"], dct["registered"]))
            self.conn.commit() # фиксируем
            self.log.addInfo(f"Данные добавлены")
        except Exception as e:
            self.conn.rollback()
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Ошибка при вставке: " + self._friendly_db_error(e))

    # записывает данные о номере
    def enterDataRooms(self, dct):
        self.log.addInfo(f"Записываются данные номера...")
        try:
            _ = self.pr_table("rooms")
        except Exception as e:
            self.log.addError(str(e))
            raise RuntimeError(self._friendly_db_error(e))
        if not _:
            raise RuntimeError("Таблицы не существует, создайте схему")

        amenities = dct.get("amenities", [])

        if len(amenities) > 10:
            raise RuntimeError("Слишком много удобств: максимум 10.")

        sql = """
               INSERT INTO rooms (room_number, capacity, comfort, price, amenities)
               VALUES (%s, %s, %s, %s, %s)
           """
        params = (
            dct['room_number'],
            dct['capacity'],
            dct['comfort'],
            dct['price'],
            amenities
        )
        try:
            self.cur.execute(sql, params)
            self.conn.commit()
            self.log.addInfo(f"Данные номера записаны")
        except Exception as e:
            self.conn.rollback()
            self.log.addError(str(e) + '\n\t' + sql + '\n')
            raise RuntimeError("Ошибка при вставке: " + self._friendly_db_error(e))

    # записывает данные о заселении
    def enterDataStays(self, dct):
        self.log.addInfo(f"Записываются данные бронирования...")
        try:
            _ = self.pr_table("stays")
        except Exception as e:
            raise RuntimeError(e)
        if not _:
            raise RuntimeError("Таблицы не существует, создайте схему")

        # проверка существования клиента
        s = "SELECT id FROM clients WHERE id = %s;"
        try:
            self.cur.execute(s, (dct["client_id"],))
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Ошибка при проверке существования клиента")
        if not self.cur.fetchone():
            raise RuntimeError(f"Нарушение внешнего ключа (клиента с id={dct['client_id']} не существует)")

        # проверка существования комнаты
        s = "SELECT id FROM rooms WHERE id = %s;"
        try:
            self.cur.execute(s, (dct["room_id"],))
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Ошибка при проверке существования номера")
        if not self.cur.fetchone():
            raise RuntimeError(f"Нарушение внешнего ключа (номера с id={dct['room_id']} не существует)")

        s = """
                INSERT INTO stays (client_id, room_id, check_in, check_out, is_paid, note, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
        try:
            self.cur.execute(s, (dct["client_id"], dct["room_id"], dct["check_in"], dct["check_out"], dct["is_paid"], dct["note"], dct["status"]))
            self.conn.commit()  # фиксируем
            self.log.addInfo(f"Данные бронирования записаны")
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Ошибка при вставке: " + self._friendly_db_error(e))


    def find_clients(self):
        s = """
            SELECT id, first_name, last_name, passport
            FROM clients
            ORDER BY last_name, first_name;
        """
        try:
            self.cur.execute(s)
            rows = self.cur.fetchall()
            out = []
            for c in rows:
                cid = c["id"] if isinstance(c, dict) else c[0]
                fn = c["first_name"] if isinstance(c, dict) else c[1]
                ln = c["last_name"] if isinstance(c, dict) else c[2]
                pp = c["passport"] if isinstance(c, dict) else c[3]
                out.append({"id": cid, "label": f"{ln} {fn} (паспорт {pp})"})
            return out
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Ошибка при поиске клиентов:" + self._friendly_db_error(e))

    def find_rooms(self):
        s ="""
            SELECT id, room_number, comfort, capacity
            FROM rooms
            ORDER BY room_number;
        """
        try:
            self.cur.execute(s)
            rows = self.cur.fetchall()
            out = []
            for r in rows:
                rid = r["id"] if isinstance(r, dict) else r[0]
                rn = r["room_number"] if isinstance(r, dict) else r[1]
                cm = r["comfort"] if isinstance(r, dict) else r[2]
                cp = r["capacity"] if isinstance(r, dict) else r[3]
                out.append({"id": rid, "label": f"Комната {rn} ({cm}, {cp} мест)"})
            return out
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Ошибка при поиске комнат: " + self._friendly_db_error(e))

    def room_exists(self, room_number):
        s = "SELECT EXISTS(SELECT 1 FROM rooms WHERE room_number = %s)"

        try:
            self.cur.execute(s, (room_number,))
            return self.cur.fetchone()[0]
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Ошибка при проверке существования комнат: " + self._friendly_db_error(e))

    # загрузка данных с сортировкой и без
    def load_data(self, filters_param):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        try:
            #база
            query = """
                SELECT 
                    s.id, 
                    c.last_name || ' ' || c.first_name || ' ' || COALESCE(c.patronymic, '') AS client, 
                    r.room_number, 
                    r.comfort, 
                    s.check_in, 
                    s.check_out, 
                    CASE WHEN s.is_paid THEN 'Да' ELSE 'Нет' END AS paid, 
                    CASE WHEN s.status  THEN 'Активно' ELSE 'Завершено' END AS status 
                FROM stays s 
                JOIN clients c ON s.client_id = c.id 
                JOIN rooms r  ON s.room_id   = r.id 
            """

            # соответствие столбцов
            column_mapping = {
                "ID": "s.id",
                "Клиент": "client",
                "Номер": "r.room_number",
                "Комфорт": "r.comfort",
                "Заезд": "s.check_in",
                "Выезд": "s.check_out",
                "Оплата": "paid",
                "Статус": "status"
            }

            # фильтр по столбцам
            if isinstance(filters_param, dict) and filters_param['use_sort']:
                selected_column = filters_param['sort_column']
                selected_sort = filters_param['sort_order']
            else:
                selected_column = "ID"
                selected_sort = "по возрастанию"

            sort_direction = "DESC" if selected_sort == "по убыванию" else "ASC"
            sort_column = column_mapping.get(selected_column, "s.id")

            # список условий WHERE
            where_conditions = []

            # фильтр по дате
            if isinstance(filters_param, dict) and filters_param['use_date']:
                date_from = filters_param.get('date_from')
                date_to = filters_param.get('date_to')
                # фильтруем брони, которые пересекаются с указанным периодом
                where_conditions.append(f"""
                            (
                                (s.check_in BETWEEN '{date_from}' AND '{date_to}') OR
                                (s.check_out BETWEEN '{date_from}' AND '{date_to}') OR
                                (s.check_in <= '{date_to}' AND s.check_out >= '{date_from}')
                            )
                            """)

            # фильтр по комфорту номера
            if isinstance(filters_param, dict) and filters_param['use_comfort']:
                comfort_filter = filters_param['comfort_level']
                where_conditions.append(f"r.comfort = '{comfort_filter}'")

            # фильтр по отплате
            if isinstance(filters_param, dict) and filters_param['use_paid']:
                case_paid = filters_param['is_paid']
                where_conditions.append(f"s.is_paid = '{case_paid}'")

            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            query += f" ORDER BY {sort_column} {sort_direction}"

            self.cur.execute(query)  # выполняем
            rows = self.cur.fetchall()  # забираем данные
            return rows  # список кортежей
        except Exception as e:
            self.log.addError("Ошибка при загрузке данных из БД: " + str(e))
            raise RuntimeError("Ошибка при загрузке данных из БД: " + self._friendly_db_error(e))
