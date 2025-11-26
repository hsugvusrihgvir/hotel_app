import psycopg2
from psycopg2 import sql, errors
from psycopg2.extras import RealDictCursor

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

        self.DB_NAME = "hotel_db"  # имя бд
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
            return "Нарушение CHECK: проверьте правила (например, дата выезда > даты заезда; вместимость > 0; не более 10 удобств)."
        if isinstance(e, errors.ForeignKeyViolation):
            return "Нарушение внешнего ключа: связанная запись не существует."
        if isinstance(e, errors.InvalidTextRepresentation):
            return "Ошибка типов: неверный формат значения (например, ENUM или DATE)."
        if isinstance(e, errors.NumericValueOutOfRange):
            return "Число выходит за допустимый диапазон."
        if isinstance(e, errors.StringDataRightTruncation):
            return "Строка слишком длинная для этого поля."
        if isinstance(e, psycopg2.OperationalError):
            return "Ошибка подключения к БД."
        if isinstance(e, psycopg2.DataError):
            return "Ошибка данных: значение не соответствует типу."

        return f"Ошибка БД: {str(e)}"

    def create(self):  # создание схемы
        self.log.addInfo("Проверка подключения к БД...")
        if not self.conn or not self.cur:  # проверяем подключение
            raise RuntimeError("Нет подключения к БД. Проверьте настройки и наличие базы.")

        schema_path = Path(__file__).with_name("schema.sql")
        try:
            self.log.addInfo("Создание схемы БД...")
            with open(schema_path, "r", encoding="utf-8") as f:
                sql_text = f.read()
            self.cur.execute(sql_text)
            self.conn.commit()
            self.log.addInfo("Схема БД создана")
            return "OK"
        except Exception as e:
            self.conn.rollback()
            self.log.addError(e)
            raise RuntimeError("Ошибка при создании схемы: " + self._friendly_db_error(e))

    def connect(self):  # подключение к бд
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
            raise RuntimeError("Ошибка подключения к БД: " + self._friendly_db_error(e))

    def pr_table(self, title):  # проверяет есть ли таблица
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

    def close(self):  # закрыть соединение
        self.log.addInfo("Закрытие подключения к БД...")
        if self.cur is not None:
            self.cur.close()
            self.cur = None
        if self.conn is not None:
            self.conn.close()
            self.conn = None
        self.log.addInfo("Подключение к БД закрыто")

    # записывает данные клиента из интерфейса
    def enterDataClient(self, dct):  # передается словарь с данными
        self.log.addInfo("Записываются данные клиента...")
        try:
            _ = self.pr_table("clients")  # проверяем, что таблица есть
        except Exception as e:
            raise RuntimeError(e)
        if not _:
            raise RuntimeError("Таблицы clients не существует, создайте схему")

        s = """
            INSERT INTO clients (last_name, first_name, patronymic, passport, comment, is_regular, registered)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        try:
            self.cur.execute(
                s,
                (
                    dct["last_name"],
                    dct["first_name"],
                    dct["patronymic"],
                    dct["passport"],
                    dct["comment"],
                    dct["is_regular"],
                    dct["registered"],
                ),
            )
            self.conn.commit()
            self.log.addInfo("Данные клиента добавлены")
        except Exception as e:
            self.conn.rollback()
            self.log.addError(str(e) + "\n\t" + s + "\n")
            raise RuntimeError("Ошибка при вставке: " + self._friendly_db_error(e))

    # записывает данные о номере
    def enterDataRooms(self, dct):
        self.log.addInfo("Записываются данные номера...")
        try:
            _ = self.pr_table("rooms")
        except Exception as e:
            self.log.addError(str(e))
            raise RuntimeError(self._friendly_db_error(e))
        if not _:
            raise RuntimeError("Таблицы rooms не существует, создайте схему")

        amenities = dct.get("amenities", [])
        if len(amenities) > 10:
            raise RuntimeError("Слишком много удобств: максимум 10.")

        s = """
            INSERT INTO rooms (room_number, capacity, comfort, price, amenities)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            dct["room_number"],
            dct["capacity"],
            dct["comfort"],
            dct["price"],
            amenities,
        )
        try:
            self.cur.execute(s, params)
            self.conn.commit()
            self.log.addInfo("Данные номера записаны")
        except Exception as e:
            self.conn.rollback()
            self.log.addError(str(e) + "\n\t" + s + "\n")
            raise RuntimeError("Ошибка при вставке: " + self._friendly_db_error(e))

    # записывает данные о заселении
    def enterDataStays(self, dct):
        self.log.addInfo("Записываются данные бронирования...")
        try:
            _ = self.pr_table("stays")
        except Exception as e:
            raise RuntimeError(e)
        if not _:
            raise RuntimeError("Таблицы stays не существует, создайте схему")

        # проверка существования клиента
        s = "SELECT id FROM clients WHERE id = %s;"
        try:
            self.cur.execute(s, (dct["client_id"],))
        except Exception as e:
            self.log.addError(str(e) + "\n\t" + s + "\n")
            raise RuntimeError("Ошибка при проверке существования клиента")
        if not self.cur.fetchone():
            raise RuntimeError(f"Нарушение внешнего ключа (клиента с id={dct['client_id']} не существует)")

        # проверка существования комнаты
        s = "SELECT id FROM rooms WHERE id = %s;"
        try:
            self.cur.execute(s, (dct["room_id"],))
        except Exception as e:
            self.log.addError(str(e) + "\n\t" + s + "\n")
            raise RuntimeError("Ошибка при проверке существования номера")
        if not self.cur.fetchone():
            raise RuntimeError(f"Нарушение внешнего ключа (номера с id={dct['room_id']} не существует)")

        s = """
                INSERT INTO stays (client_id, room_id, check_in, check_out, is_paid, note, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
        try:
            self.cur.execute(
                s,
                (
                    dct["client_id"],
                    dct["room_id"],
                    dct["check_in"],
                    dct["check_out"],
                    dct["is_paid"],
                    dct["note"],
                    dct["status"],
                ),
            )
            self.conn.commit()
            self.log.addInfo("Данные бронирования записаны")
        except Exception as e:
            self.log.addError(str(e) + "\n\t" + s + "\n")
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
            self.log.addError(str(e) + "\n\t" + s + "\n")
            raise RuntimeError("Ошибка при поиске клиентов: " + self._friendly_db_error(e))

    def find_rooms(self):
        s = """
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
            self.log.addError(str(e) + "\n\t" + s + "\n")
            raise RuntimeError("Ошибка при поиске комнат: " + self._friendly_db_error(e))

    def room_exists(self, room_number):
        s = "SELECT EXISTS(SELECT 1 FROM rooms WHERE room_number = %s)"

        try:
            self.cur.execute(s, (room_number,))
            return self.cur.fetchone()[0]
        except Exception as e:
            self.log.addError(str(e) + "\n\t" + s + "\n")
            raise RuntimeError("Ошибка при проверке существования комнат: " + self._friendly_db_error(e))

        # загрузка данных с сортировкой и фильтрами (старое окно «Показать данные»)

    def load_data(self, filters_param):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        try:
            # 1. Пытаемся автоматически определить реальные связи stays.client_id / stays.room_id

            client_ref_table = "clients"
            client_ref_col = "id"
            room_ref_table = "rooms"
            room_ref_col = "id"

            try:
                # смотрим структуру stays и её внешние ключи
                cols_stays = self.get_table_columns("public", "stays")
                by_name = {c["name"]: c for c in cols_stays}

                # --- client_id ---
                if "client_id" in by_name and by_name["client_id"]["fk"]:
                    fk = by_name["client_id"]["fk"][0]
                    client_ref_table = fk["ref_table"]
                    client_ref_col = fk["ref_columns"][0]
                else:
                    # fk нет или он странный — смотрим PK таблицы clients (или того, что указано в client_ref_table)
                    try:
                        cols_clients = self.get_table_columns("public", client_ref_table)
                        pk_cols = [c["name"] for c in cols_clients if c.get("is_pk")]
                        if pk_cols:
                            client_ref_col = pk_cols[0]
                    except Exception as e2:
                        self.log.addError("Не удалось определить PK для clients: " + str(e2))

                # --- room_id ---
                if "room_id" in by_name and by_name["room_id"]["fk"]:
                    fk = by_name["room_id"]["fk"][0]
                    room_ref_table = fk["ref_table"]
                    room_ref_col = fk["ref_columns"][0]
                else:
                    # fk нет или он странный — ищем PK в rooms
                    try:
                        cols_rooms = self.get_table_columns("public", room_ref_table)
                        pk_cols = [c["name"] for c in cols_rooms if c.get("is_pk")]
                        if pk_cols:
                            room_ref_col = pk_cols[0]
                    except Exception as e2:
                        self.log.addError("Не удалось определить PK для rooms: " + str(e2))

            except Exception as e:
                # если вообще ничего не получилось — остаются дефолты (clients.id, rooms.id)
                self.log.addError(
                    "Не удалось автоматически определить внешние ключи для stays: " + str(e)
                )

            # 2. Базовый запрос с учётом найденных таблиц и полей
            query = f"""
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
                   JOIN "{client_ref_table}" c ON s.client_id = c."{client_ref_col}"
                   JOIN "{room_ref_table}"  r ON s.room_id   = r."{room_ref_col}"
               """

            # соответствие столбцов (для сортировки)
            column_mapping = {
                "ID": "s.id",
                "Клиент": "client",
                "Номер": "r.room_number",
                "Комфорт": "r.comfort",
                "Заезд": "s.check_in",
                "Выезд": "s.check_out",
                "Оплата": "paid",
                "Статус": "status",
            }

            # сортировка
            if isinstance(filters_param, dict) and filters_param.get("use_sort"):
                selected_column = filters_param.get("sort_column")
                selected_sort = filters_param.get("sort_order")
            else:
                selected_column = "ID"
                selected_sort = "по возрастанию"

            sort_direction = "DESC" if selected_sort == "по убыванию" else "ASC"
            sort_column = column_mapping.get(selected_column, "s.id")

            where_conditions = []

            # фильтр по дате
            if isinstance(filters_param, dict) and filters_param.get("use_date"):
                date_from = filters_param.get("date_from")
                date_to = filters_param.get("date_to")
                if date_from and date_to:
                    where_conditions.append(
                        f"""
                           (
                               (s.check_in BETWEEN '{date_from}' AND '{date_to}') OR
                               (s.check_out BETWEEN '{date_from}' AND '{date_to}') OR
                               (s.check_in <= '{date_to}' AND s.check_out >= '{date_from}')
                           )
                           """
                    )

            # фильтр по комфорту
            if isinstance(filters_param, dict) and filters_param.get("use_comfort"):
                comfort_filter = filters_param.get("comfort_level")
                if comfort_filter:
                    where_conditions.append(f"r.comfort = '{comfort_filter}'")

            # фильтр по оплате
            if isinstance(filters_param, dict) and filters_param.get("use_paid"):
                case_paid = filters_param.get("is_paid")
                if case_paid is not None:
                    where_conditions.append(f"s.is_paid = '{case_paid}'")

            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)

            query += f" ORDER BY {sort_column} {sort_direction}"

            self.cur.execute(query)
            rows = self.cur.fetchall()
            return rows

        except Exception as e:
            self.log.addError("Ошибка при загрузке данных из БД: " + str(e))
            raise RuntimeError("Ошибка при загрузке данных из БД: " + self._friendly_db_error(e))
    # ====== НОВОЕ ДЛЯ КР2 / КР3 ======

    # универсальный SELECT для разных окон
    def run_select(self, query, params=None):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")
        if params is None:
            params = ()
        try:
            self.log.addInfo(f"SELECT: {query}")
            self.cur.execute(query, params)
            rows = self.cur.fetchall()
            return rows
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + query + '\n')
            raise RuntimeError("Ошибка при выполнении SELECT: " + self._friendly_db_error(e))

    # безопасный ALTER TABLE (изменение структуры)
    def execute_alter(self, query, params=None):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")
        if params is None:
            params = ()
        try:
            self.log.addInfo(f"ALTER: {query}")
            self.cur.execute("BEGIN;")
            self.cur.execute(query, params)
            self.conn.commit()
            self.log.addInfo("ALTER выполнен")
        except Exception as e:
            try:
                self.conn.rollback()
            except Exception:
                pass
            self.log.addError(str(e) + '\n\t' + query + '\n')
            raise RuntimeError("Ошибка при изменении структуры БД: " + self._friendly_db_error(e))

    # список таблиц схемы public (для комбобоксов)
    def list_tables(self):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        s = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        try:
            self.cur.execute(s)
            rows = self.cur.fetchall()
            return [r[0] for r in rows]
        except Exception as e:
            self.log.addError(str(e) + '\n\t' + s + '\n')
            raise RuntimeError("Не удалось получить список таблиц: " + self._friendly_db_error(e))

    # обёртка над get_table_columns для схемы public
    def list_columns(self, table):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")
        return self.get_table_columns("public", table)

    # ф. возв. поля таблицы со всеми ограничениями
    def get_table_columns(self, schema: str, table: str):
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        # базовая инфа о столбцах
        q_columns = """
            SELECT
                c.column_name,
                c.is_nullable,
                c.data_type,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                c.column_default,
                c.collation_name,
                c.is_identity,
                c.identity_generation
            FROM information_schema.columns c
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position;
        """

        # ограничения PK/UNIQUE
        q_keys = """
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON kcu.table_schema = tc.table_schema
             AND kcu.table_name   = tc.table_name
             AND kcu.constraint_name = tc.constraint_name
            WHERE tc.table_schema = %s
              AND tc.table_name   = %s
              AND tc.constraint_type IN ('PRIMARY KEY','UNIQUE')
            ORDER BY tc.constraint_name, kcu.ordinal_position;
        """

        # внешние ключи
        q_fks = """
            SELECT
                tc.constraint_name,
                kcu.column_name            AS src_column,
                ccu.table_schema           AS ref_schema,
                ccu.table_name             AS ref_table,
                ccu.column_name            AS ref_column,
                rc.update_rule             AS on_update,
                rc.delete_rule             AS on_delete
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = tc.constraint_name
             AND kcu.table_schema    = tc.table_schema
             AND kcu.table_name      = tc.table_name
            JOIN information_schema.referential_constraints rc
              ON rc.constraint_name = tc.constraint_name
             AND rc.constraint_schema = tc.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = rc.unique_constraint_name
             AND ccu.constraint_schema = rc.unique_constraint_schema
            WHERE tc.table_schema = %s
              AND tc.table_name   = %s
              AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.constraint_name, kcu.ordinal_position;
        """

        # CHECK ограничения
        q_checks = """
            SELECT cc.check_clause
            FROM information_schema.table_constraints tc
            JOIN information_schema.check_constraints cc
              ON cc.constraint_name = tc.constraint_name
             AND cc.constraint_schema = tc.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name   = %s
              AND tc.constraint_type = 'CHECK'
            ORDER BY tc.constraint_name;
        """

        try:
            self.log.addInfo(f"Загрузка столбцов таблицы {table}...")

            cur = self.conn.cursor(cursor_factory=RealDictCursor)

            # загружаем поля
            cur.execute(q_columns, (schema, table))
            rows = cur.fetchall()

            cols = []
            for r in rows:
                identity = None
                if (r["is_identity"] or "").upper() == "YES":
                    identity = (r["identity_generation"] or "").upper() or None

                dtype = r["data_type"]
                if r["character_maximum_length"]:
                    dtype = f"{dtype}({r['character_maximum_length']})"
                elif r["numeric_precision"] is not None:
                    if r["numeric_scale"] is not None:
                        dtype = f"{dtype}({r['numeric_precision']},{r['numeric_scale']})"
                    else:
                        dtype = f"{dtype}({r['numeric_precision']})"

                cols.append(
                    {
                        "name": r["column_name"],
                        "type": dtype,
                        "not_null": (r["is_nullable"] == "NO"),
                        "default": r["column_default"],
                        "identity": identity,
                        "collation": r["collation_name"],
                        "length": r["character_maximum_length"],
                        "numeric_precision": r["numeric_precision"],
                        "numeric_scale": r["numeric_scale"],
                        "enum_labels": None,
                        "is_pk": False,
                        "unique_groups": [],
                        "fk": [],
                        "checks": [],
                    }
                )

            by_name = {c["name"]: c for c in cols}

            # PK/UNIQUE
            cur.execute(q_keys, (schema, table))
            key_rows = cur.fetchall()
            groups = {}
            for r in key_rows:
                k = r["constraint_name"]
                groups.setdefault(k, {"type": r["constraint_type"], "cols": []})
                groups[k]["cols"].append(r["column_name"])

            for g in groups.values():
                if g["type"] == "PRIMARY KEY":
                    for col in g["cols"]:
                        if col in by_name:
                            by_name[col]["is_pk"] = True
                elif g["type"] == "UNIQUE":
                    arr = list(g["cols"])
                    for col in g["cols"]:
                        if col in by_name:
                            by_name[col]["unique_groups"].append(arr)

            # FK
            cur.execute(q_fks, (schema, table))
            fk_rows = cur.fetchall()
            fk_map = {}
            for r in fk_rows:
                name = r["constraint_name"]
                ent = fk_map.setdefault(
                    name,
                    {
                        "name": name,
                        "columns": [],
                        "ref_schema": r["ref_schema"],
                        "ref_table": r["ref_table"],
                        "ref_columns": [],
                        "on_update": r["on_update"],
                        "on_delete": r["on_delete"],
                        "match": "SIMPLE",
                    },
                )
                ent["columns"].append(r["src_column"])
                ent["ref_columns"].append(r["ref_column"])

            for fk in fk_map.values():
                for col in fk["columns"]:
                    if col in by_name:
                        by_name[col]["fk"].append(fk)

            # CHECK
            cur.execute(q_checks, (schema, table))
            checks = [x["check_clause"] for x in cur.fetchall()]
            for c in cols:
                c["checks"] = checks

            cur.close()
            self.log.addInfo(f"Столбцов найдено: {len(cols)}")
            return cols

        except Exception as e:
            try:
                cur.close()
            except Exception:
                pass
            self.log.addError(f"Ошибка при получении столбцов {schema}.{table}: " + str(e))
            raise RuntimeError("Не удалось получить столбцы: " + self._friendly_db_error(e))

    # ====== СЛУЖЕБНОЕ ДЛЯ ОКНА ALTER TABLE И ТИПОВ ======

    def list_types(self):
        """
        Возвращает список допустимых типов данных для выбора в интерфейсе ALTER TABLE.
        Базовый набор + пользовательские ENUM из схемы public.
        """
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        # базовый набор типов, покрывающий предметную область
        base_types = [
            "integer",
            "bigint",
            "numeric(10,2)",
            "text",
            "varchar(50)",
            "boolean",
            "date",
            "timestamp",
        ]

        # пробуем подтянуть пользовательские ENUM-типы
        enum_sql = """
            SELECT t.typname
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typtype = 'e'
              AND n.nspname = 'public'
            ORDER BY t.typname;
        """

        enums = []
        try:
            cur = self.conn.cursor()
            cur.execute(enum_sql)
            enums = [row[0] for row in cur.fetchall()]
            cur.close()
        except Exception as e:
            # если не получилось — логируем и продолжаем с базовым списком
            self.log.addError("Не удалось получить ENUM-типы: " + str(e))

        # убираем дубликаты, сохраняем порядок
        seen = set()
        result = []
        for t in base_types + enums:
            if t not in seen:
                seen.add(t)
                result.append(t)

        self.log.addInfo(f"Доступные типы данных: {result}")
        return result

    def list_constraints_unique(self, table: str):
        """
        Список UNIQUE-ограничений таблицы.
        Формат для каждого элемента:
            { "name": <имя ограничения>, "column": <колонка> }
        """
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        sql_text = """
            SELECT
                tc.constraint_name,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON kcu.table_schema = tc.table_schema
             AND kcu.table_name   = tc.table_name
             AND kcu.constraint_name = tc.constraint_name
            WHERE tc.table_schema = 'public'
              AND tc.table_name   = %s
              AND tc.constraint_type = 'UNIQUE'
            ORDER BY tc.constraint_name, kcu.ordinal_position;
        """
        try:
            self.cur.execute(sql_text, (table,))
            rows = self.cur.fetchall()
            out = []
            for cname, col in rows:
                out.append({
                    "name": cname,
                    "column": col,
                })
            self.log.addInfo(f"UNIQUE-ограничения для {table}: {out}")
            return out
        except Exception as e:
            self.log.addError("Не удалось получить UNIQUE-ограничения: " + str(e))
            raise RuntimeError("Ошибка при получении UNIQUE-ограничений: " + self._friendly_db_error(e))

    def list_constraints_check(self, table: str):
        """
        Список CHECK-ограничений таблицы.
        Формат для каждого элемента:
            { "name": <имя>, "expression": <текст CHECK> }
        """
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        sql_text = """
            SELECT
                tc.constraint_name,
                cc.check_clause
            FROM information_schema.table_constraints tc
            JOIN information_schema.check_constraints cc
              ON cc.constraint_name = tc.constraint_name
             AND cc.constraint_schema = tc.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name   = %s
              AND tc.constraint_type = 'CHECK'
            ORDER BY tc.constraint_name;
        """
        try:
            self.cur.execute(sql_text, (table,))
            rows = self.cur.fetchall()
            out = []
            for cname, clause in rows:
                out.append({
                    "name": cname,
                    "expression": clause,
                })
            self.log.addInfo(f"CHECK-ограничения для {table}: {out}")
            return out
        except Exception as e:
            self.log.addError("Не удалось получить CHECK-ограничения: " + str(e))
            raise RuntimeError("Ошибка при получении CHECK-ограничений: " + self._friendly_db_error(e))

    def list_constraints_fk(self, table: str):
        """
        Список внешних ключей таблицы.
        Формат:
            {
                "name": <имя>,
                "column": <локальный столбец>,
                "ref_table": <таблица-ссылка>,
                "ref_column": <столбец-ссылка>
            }
        """
        if not self.conn or not self.cur:
            raise RuntimeError("Нет подключения к БД")

        sql_text = """
            SELECT
                tc.constraint_name,
                kcu.column_name            AS src_column,
                ccu.table_name             AS ref_table,
                ccu.column_name            AS ref_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON kcu.constraint_name = tc.constraint_name
             AND kcu.table_schema    = tc.table_schema
             AND kcu.table_name      = tc.table_name
            JOIN information_schema.referential_constraints rc
              ON rc.constraint_name = tc.constraint_name
             AND rc.constraint_schema = tc.table_schema
            JOIN information_schema.constraint_column_usage ccu
              ON ccu.constraint_name = rc.unique_constraint_name
             AND ccu.constraint_schema = rc.unique_constraint_schema
            WHERE tc.table_schema = 'public'
              AND tc.table_name   = %s
              AND tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.constraint_name, kcu.ordinal_position;
        """
        try:
            self.cur.execute(sql_text, (table,))
            rows = self.cur.fetchall()
            out = []
            for cname, src_col, ref_table, ref_col in rows:
                out.append({
                    "name": cname,
                    "column": src_col,
                    "ref_table": ref_table,
                    "ref_column": ref_col,
                })
            self.log.addInfo(f"FK-ограничения для {table}: {out}")
            return out
        except Exception as e:
            self.log.addError("Не удалось получить внешние ключи: " + str(e))
            raise RuntimeError("Ошибка при получении внешних ключей: " + self._friendly_db_error(e))
