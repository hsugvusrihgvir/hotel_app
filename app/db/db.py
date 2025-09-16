import psycopg2

import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path


class HotelDB:
    def __init__(self):
        self.conn = None
        self.cur = None

    def create(self):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")
        schema_path = Path(__file__).with_name("schema.sql")
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                sql = f.read()
            print(sql)
            self.cur.execute(sql)
            self.conn.commit()
            return "OK"
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Ошибка при создании схемы: {e}")

    def connect(self):
        try:
            load_dotenv()

            DB_NAME = "hotel_db"
            DB_USER = os.getenv("DB_USER") # из .env, подставьте туда свои данные
            DB_PASS = os.getenv("DB_PASS")
            DB_HOST = os.getenv("DB_HOST")
            DB_PORT = os.getenv("DB_PORT")

            # подключение
            self.conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT
            )
            self.cur = self.conn.cursor()
            print("Подключение успешно")
        except Exception as e:
            raise RuntimeError(f"Ошибка подключения к БД: {e}")

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
        if self.cur is not None:
            self.cur.close()
            self.cur = None
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    # записывает данные клиента из интерфейса
    def enterDataClient(self, lastName, firstName, patronymic, passport, comment=None, is_regular=False, registered=None):
        try:
            _ = self.pr_table("clients") # проверяем, что таблица есть
        except Exception as e:
            raise RuntimeError(e)
        if not _:
            raise RuntimeError("Таблицы не существует, создайте схему")

        if registered is None: # время регистрации
            registered = datetime.now()

        try:
            self.cur.execute("""
                INSERT INTO clients (last_name, first_name, patronymic, passport, comment, is_regular, registered)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (lastName, firstName, patronymic, passport, comment, is_regular, registered))
            self.conn.commit() # фиксируем
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError("Ошибка при вставке (убедитесь, что схема создана):", e)

    # записывает данные о номере
    def enterDataRooms(self, room_number, capacity, comfort, price):
        try:
            _ = self.pr_table("rooms")
        except Exception as e:
            raise RuntimeError(e)
        if not _:
            raise RuntimeError("Таблицы не существует, создайте схему")

        try:
            self.cur.execute("""
                INSERT INTO rooms (room_number, capacity, comfort, price)
                VALUES (%s, %s, %s, %s);
            """, (room_number, capacity, comfort, price))
            self.conn.commit()  # фиксируем
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError("Ошибка при вставке (убедитесь, что схема создана):", e)

    # записывает данные о заселении/бронировании
    def enterDataStays(self, client_id, room_id, check_in, check_out, is_paid=False, note=None, status=True):


        try:
            _ = self.pr_table("stays")
        except Exception as e:
            raise RuntimeError(e)
        if not _:
            raise RuntimeError("Таблицы не существует, создайте схему")

        # проверка существования клиента
        self.cur.execute("SELECT id FROM clients WHERE id = %s;", (client_id,))
        if not self.cur.fetchone():
            raise RuntimeError(f"Клиента с id={client_id} не существует")

        # проверка существования комнаты
        self.cur.execute("SELECT id FROM rooms WHERE id = %s;", (room_id,))
        if not self.cur.fetchone():
            raise RuntimeError(f"Комнаты с id={room_id} не существует")

        try:
            self.cur.execute("""
                INSERT INTO stays (client_id, room_id, check_in, check_out, is_paid, note, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, (client_id, room_id, check_in, check_out, is_paid, note, status))
            self.conn.commit()  # фиксируем
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError("Ошибка при вставке (убедитесь, что схема создана):", e)

