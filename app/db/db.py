# db.py — ядро работы с PostgreSQL
# короткие комментарии, чистая архитектура
import psycopg2
import psycopg2.extras
from psycopg2 import sql
from contextlib import contextmanager
from app.log.log import app_logger
from dotenv import load_dotenv, find_dotenv
import os



class Database:
    """слой PostgreSQL + автоматическая загрузка .env"""

    def __init__(self):
        load_dotenv(find_dotenv())

        self.conn_params = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "dbname": os.getenv("DB_NAME"),
        }

        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = False
            app_logger.info("DB connected")
        except Exception as e:
            app_logger.error(f"connection error: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            app_logger.info("DB closed")

    def get_tables(self):
        """возвращает список таблиц из public-схемы"""
        q = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        with self.cursor() as cur:
            cur.execute(q)
            return [r["table_name"] for r in cur.fetchall()]

    def get_table_columns(self, table_name: str):
        """
        Возвращает информацию о колонках таблицы:
        имя, тип, nullable, default, enum_values (если есть)
        """
        q = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                udt_name,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """

        with self.cursor() as cur:
            cur.execute(q, (table_name,))
            columns = cur.fetchall()

        # добавим enum значения, если нужно
        for col in columns:
            if self._is_enum(col["udt_name"]):
                col["enum_values"] = self._get_enum_values(col["udt_name"])
            else:
                col["enum_values"] = None

        return columns

    def _is_enum(self, type_name):
        q = """
            SELECT 1
            FROM pg_type
            WHERE typname = %s AND typtype = 'e';
        """
        with self.cursor() as cur:
            cur.execute(q, (type_name,))
            return cur.fetchone() is not None

    def _get_enum_values(self, type_name):
        q = """
            SELECT enumlabel
            FROM pg_enum
            JOIN pg_type ON pg_type.oid = enumtypid
            WHERE typname = %s
            ORDER BY enumsortorder;
        """
        with self.cursor() as cur:
            cur.execute(q, (type_name,))
            return [r["enumlabel"] for r in cur.fetchall()]

    def insert_row(self, table: str, data: dict):
        """
        Вставка строки в таблицу с безопасной параметризацией
        data = {"column1": value1, "column2": value2, ...}
        """
        from psycopg2 import sql

        columns = list(data.keys())
        values = [data[c] for c in columns]

        query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({placeholders})").format(
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(", ").join(sql.Placeholder() * len(columns)),
        )

        with self.cursor() as cur:
            cur.execute(query, values)

        app_logger.info(f"INSERT INTO {table}: {data}")

    @contextmanager
    def cursor(self):
        if self.conn is None:
            self.connect()
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
        except Exception as e:
            self.conn.rollback()
            raise
        else:
            self.conn.commit()
        finally:
            cur.close()

    def commit(self):
        """ручной коммит (дополнительно к автокоммиту в cursor())."""
        if getattr(self, "conn", None) is not None:
            self.conn.commit()
    # ---------------------------
    # DDL (CREATE / ALTER / DROP)
    # ---------------------------

    def execute_ddl(self, query: str):
        """выполнить DDL команду — создание схем/таблиц/типов"""
        with self.cursor() as cur:
            cur.execute(query)
        app_logger.info(f"DDL executed: {query[:80].replace(chr(10),' ')}")

    def alter_table(self, query: str):
        """выполнить ALTER TABLE (в UI формируется динамически)"""
        with self.cursor() as cur:
            cur.execute(query)
        app_logger.info(f"ALTER executed: {query[:80].replace(chr(10),' ')}")

    # ---------------------------
    # INSERT
    # ---------------------------

    def insert(self, table: str, data: dict):
        """
        параметризованный insert
        data = {"col": value, ...}
        """
        cols = list(data.keys())
        values = [data[c] for c in cols]

        q = sql.SQL("INSERT INTO {tbl} ({cols}) VALUES ({vals})") \
            .format(
                tbl=sql.Identifier(table),
                cols=sql.SQL(', ').join(map(sql.Identifier, cols)),
                vals=sql.SQL(', ').join(sql.Placeholder() * len(cols)),
            )

        with self.cursor() as cur:
            cur.execute(q, values)

        app_logger.info(f"INSERT into {table}: {data}")

    def get_custom_types(self):
        """возвращает список всех пользовательских типов public"""
        q = """
            SELECT typname
            FROM pg_type
            WHERE typnamespace = 'public'::regnamespace
              AND typtype IN ('e', 'c')
            ORDER BY typname;
        """
        with self.cursor() as cur:
            cur.execute(q)
            return [r['typname'] for r in cur.fetchall()]

    # ---------------------------
    # универсальный SELECT
    # используется и для фильтров, и для join, и для группировки
    # ---------------------------

    def select(self,
               table: str,
               columns="*",
               where=None,
               order=None,
               group=None,
               having=None,
               limit=None):
        """
        универсальный SELECT для UI-конструктора
        table — строка или sql.SQL (для subquery)
        columns — строка или список
        where — список sql.SQL условий
        order — [('col', 'ASC'), ...]
        group — список колонок
        """

        # колонки
        if isinstance(columns, list):
            col_sql = sql.SQL(', ').join(map(sql.Identifier, columns))
        else:
            col_sql = sql.SQL(columns)

        q = sql.SQL("SELECT {cols} FROM {tbl}").format(
            cols=col_sql,
            tbl=sql.Identifier(table) if isinstance(table, str) else table
        )

        # where
        if where:
            wh = sql.SQL(" AND ").join(where)
            q += sql.SQL(" WHERE ") + wh

        # group by
        if group:
            gr = sql.SQL(', ').join(map(sql.Identifier, group))
            q += sql.SQL(" GROUP BY ") + gr

        # having
        if having:
            q += sql.SQL(" HAVING ") + having

        # order
        if order:
            parts = [
                sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(dir))
                for c, dir in order
            ]
            q += sql.SQL(" ORDER BY ") + sql.SQL(', ').join(parts)

        if limit:
            q += sql.SQL(" LIMIT {}").format(sql.Literal(limit))

        with self.cursor() as cur:
            cur.execute(q)
            rows = cur.fetchall()
            return rows

    # ---------------------------
    # поиск LIKE / regex / SIMILAR TO
    # ---------------------------

    def text_search(self, table, column, pattern, mode="like"):
        """
        mode:
            like — '%abc%'
            regex — ~  ~*
            neg_regex — !~  !~*
            similar — SIMILAR TO
            not_similar — NOT SIMILAR TO
        """
        col = sql.Identifier(column)

        if mode == "like":
            cond = sql.SQL("{} LIKE {}").format(col, sql.Placeholder())
            value = f"%{pattern}%"

        elif mode == "regex":
            cond = sql.SQL("{} ~ {}").format(col, sql.Placeholder())
            value = pattern

        elif mode == "regex_i":
            cond = sql.SQL("{} ~* {}").format(col, sql.Placeholder())
            value = pattern

        elif mode == "not_regex":
            cond = sql.SQL("{} !~ {}").format(col, sql.Placeholder())
            value = pattern

        elif mode == "similar":
            cond = sql.SQL("{} SIMILAR TO {}").format(col, sql.Placeholder())
            value = pattern

        elif mode == "not_similar":
            cond = sql.SQL("{} NOT SIMILAR TO {}").format(col, sql.Placeholder())
            value = pattern

        else:
            raise ValueError("unknown search mode")

        q = sql.SQL("SELECT * FROM {tbl} WHERE ").format(tbl=sql.Identifier(table))
        q += cond

        with self.cursor() as cur:
            cur.execute(q, (value,))
            return cur.fetchall()

    # ---------------------------
    # JOIN-конструктор (INNER/LEFT/RIGHT/FULL)
    # ---------------------------

    def join(self, t1, t2, key1, key2, join_type="INNER"):
        """
        простой универсальный join
        join_type: INNER | LEFT | RIGHT | FULL
        """
        q = sql.SQL(
            "SELECT * FROM {t1} {jt} JOIN {t2} "
            "ON {t1}.{k1} = {t2}.{k2}"
        ).format(
            t1=sql.Identifier(t1),
            t2=sql.Identifier(t2),
            k1=sql.Identifier(key1),
            k2=sql.Identifier(key2),
            jt=sql.SQL(join_type)
        )

        with self.cursor() as cur:
            cur.execute(q)
            return cur.fetchall()

    # ---------------------------
    # CTE (WITH)
    # ---------------------------

    def cte(self, name, cte_query: str, main_query: str):
        """выполнить CTE (для будущего UI-конструктора)"""
        q = sql.SQL(f"WITH {name} AS ({cte_query}) {main_query}")

        with self.cursor() as cur:
            cur.execute(q)
            return cur.fetchall()

    # ---------------------------
    # VIEW / MATERIALIZED VIEW
    # ---------------------------

    def create_view(self, name, query):
        q = sql.SQL(f"CREATE OR REPLACE VIEW {name} AS {query}")
        self.execute_ddl(q.as_string(self.conn))

    def create_mat_view(self, name, query):
        q = sql.SQL(f"CREATE MATERIALIZED VIEW {name} AS {query}")
        self.execute_ddl(q.as_string(self.conn))

    def refresh_mat_view(self, name):
        q = sql.SQL(f"REFRESH MATERIALIZED VIEW {name}")
        self.execute_ddl(q.as_string(self.conn))

    def get_foreign_keys(self, table):
        q = """
            SELECT
                kcu.column_name AS column,
                ccu.table_name AS ref_table,
                ccu.column_name AS ref_column
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
            WHERE
                tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s;
        """

        with self.cursor() as cur:
            cur.execute(q, (table,))
            return cur.fetchall()

    def get_reference_values(self, table):
        """получить пары (id, строка-представление) для выпадающих списков FK."""
        # подбираем человекочитаемое представление в зависимости от таблицы
        if table == "clients":
            label_expr = "last_name || ' ' || first_name"
        elif table == "rooms":
            label_expr = "room_number::text || ' (' || comfort::text || ')'"
        else:
            # на всякий случай дефолт — просто id::text
            label_expr = "id::text"

        query = sql.SQL(
            "SELECT id, {label} AS label FROM {tbl} ORDER BY id LIMIT 100"
        ).format(
            label=sql.SQL(label_expr),
            tbl=sql.Identifier(table),
        )

        with self.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

        # cursor использует RealDictCursor → возвращаем список (id, label)
        return [(row["id"], row["label"]) for row in rows]
