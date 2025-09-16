import psycopg2

import os
from dotenv import load_dotenv


class HotelDB:
    def __init__(self):
        self.conn = None
        self.cur = None

    def create(self):
        with open("schema.sql", "r", encoding="utf-8") as f:
            sql = f.read()

            self.cur.execute(sql)
        print("Схема создана")

    def connect(self):
        load_dotenv()

        DB_NAME = "hotel_db"
        DB_USER = os.getenv("DB_USER")
        DB_PASS = os.getenv("DB_PASS")
        DB_HOST = os.getenv("DB_HOST")
        DB_PORT = os.getenv("DB_PORT")

        # Подключение
        self.conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        self.cur = self.conn.cursor()
        print("Подключение успешно")


    def enterDataClient(self):
        pass

    def enterDataRooms(self):
        pass

    def enterDataStays(self):
        pass

