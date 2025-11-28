import psycopg2
import psycopg2.extras
from psycopg2 import sql
from contextlib import contextmanager
from app.log.log import app_logger
from dotenv import load_dotenv, find_dotenv
import os



class Database:
    def __init__(self):
        load_dotenv(find_dotenv())

        self.conn_params = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "dbname": os.getenv("DB_NAME"),
        } # данные

        self.conn = None

    # подключение
    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.conn.autocommit = False
            app_logger.info("DB connected")
        except Exception as e:
            app_logger.error(f"connection error: {e}")
            raise

    # закрыть подключение
    def close(self):
        if self.conn:
            self.conn.close()
            app_logger.info("DB closed")

    # список таблиц
    def get_tables(self):
        q = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """
        with self.cursor() as cur:
            cur.execute(q)
            return [r["table_name"] for r in cur.fetchall()]

    # список полей таблицы
    def get_table_columns(self, table_name: str):
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

        # добавим enum значения если нужно
        for col in columns:
            if self._is_enum(col["udt_name"]):
                col["enum_values"] = self._get_enum_values(col["udt_name"])
            else:
                col["enum_values"] = None

        return columns

    # проверка
    def _is_enum(self, type_name):
        q = """
            SELECT 1
            FROM pg_type
            WHERE typname = %s AND typtype = 'e';
        """
        with self.cursor() as cur:
            cur.execute(q, (type_name,))
            return cur.fetchone() is not None

    # значения enum
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

    # учное управление
    def commit(self):
        if getattr(self, "conn", None) is not None:
            self.conn.commit()

    # создание схем таблиц типов
    def execute_ddl(self, query: str):
        with self.cursor() as cur:
            cur.execute(query)
        app_logger.info(f"DDL executed: {query[:80].replace(chr(10),' ')}")

    def alter_table(self, query: str):
        with self.cursor() as cur:
            cur.execute(query)
        app_logger.info(f"ALTER executed: {query[:80].replace(chr(10),' ')}")

    def insert(self, table: str, data: dict):
        if not data:
            raise ValueError("insert() got empty data dict")

        columns = list(data.keys())
        values = [data[c] for c in columns]

        query = sql.SQL(
            "INSERT INTO {table} ({fields}) VALUES ({placeholders})"
        ).format(
            table=sql.Identifier(table),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(", ").join(sql.Placeholder() * len(columns)),
        )

        with self.cursor() as cur:
            cur.execute(query, values)

        app_logger.info(f"INSERT INTO {table}: {data}")

    # чтобы не переписывать
    def insert_row(self, table: str, data: dict):
        return self.insert(table, data)

    # все польз. типы
    def get_custom_types(self):
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

    # универсальный селект
    def select(self,
               table: str,
               columns="*",
               where=None,
               order=None,
               group=None,
               having=None,
               limit=None):

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

    def text_search(self, table, column, pattern, mode="like"):
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


    def join(self, t1, t2, key1, key2, join_type="INNER"):

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

    def cte(self, name, cte_query: str, main_query: str):
        """выполнить CTE (для будущего UI-конструктора)"""
        q = sql.SQL(f"WITH {name} AS ({cte_query}) {main_query}")

        with self.cursor() as cur:
            cur.execute(q)
            return cur.fetchall()

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

    def get_user_types(self):
        q = """
               SELECT
                   t.typname,
                   t.typtype,
                   n.nspname,
                   c.relkind
               FROM pg_type t
               JOIN pg_namespace n ON n.oid = t.typnamespace
               LEFT JOIN pg_class c ON c.oid = t.typrelid
               WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                 AND (
                       t.typtype = 'e'                      -- ENUM
                    OR (t.typtype = 'c' AND c.relkind = 'c') -- только настоящие COMPOSITE
                 )
               ORDER BY n.nspname, t.typname;
           """
        with self.cursor() as cur:
            cur.execute(q)
            rows = cur.fetchall()

        return [
            {"name": r["typname"], "kind": r["typtype"], "schema": r["nspname"]}
            for r in rows
        ]

    def get_enum_labels(self, type_name: str):

        return self._get_enum_values(type_name)

    def get_composite_fields(self, type_name: str):
        q = """
            SELECT
                att.attname AS name,
                pg_catalog.format_type(att.atttypid, att.atttypmod) AS data_type
            FROM pg_type t
            JOIN pg_class c ON c.oid = t.typrelid
            JOIN pg_attribute att ON att.attrelid = c.oid
            WHERE t.typname = %s
              AND att.attnum > 0
              AND NOT att.attisdropped
            ORDER BY att.attnum;
        """
        with self.cursor() as cur:
            cur.execute(q, (type_name,))
            rows = cur.fetchall()

        return [{"name": r["name"], "type": r["data_type"]} for r in rows]

    def create_enum_type(self, name: str, labels: list[str]):
        """CREATE TYPE <name> AS ENUM (...)."""
        labels = [v.strip() for v in labels if v and v.strip()]
        if not labels:
            raise ValueError("ENUM должен содержать хотя бы одно значение")

        query = sql.SQL("CREATE TYPE {} AS ENUM ({})").format(
            sql.Identifier(name),
            sql.SQL(", ").join(sql.Literal(v) for v in labels),
        )
        with self.cursor() as cur:
            cur.execute(query)

        app_logger.info(f"Создан ENUM-тип {name} со значениями {labels}")

    def add_enum_value(self, type_name: str, value: str):
        value = value.strip()
        if not value:
            return

        query = sql.SQL("ALTER TYPE {} ADD VALUE %s").format(
            sql.Identifier(type_name)
        )
        with self.cursor() as cur:
            cur.execute(query, (value,))

        app_logger.info(f"В ENUM-тип {type_name} добавлено значение {value!r}")

    def drop_enum_value(self, type_name: str, value: str):
        value = (value or "").strip()
        if not value:
            return

        with self.cursor() as cur:
            # проверяем версию сервера
            cur.execute("SHOW server_version_num")
            row = cur.fetchone()
            # RealDictCursor → row — dict
            ver_num = int(row.get("server_version_num") if isinstance(row, dict) else row[0])

            if ver_num < 160000:
                # даём понятную ошибку
                raise RuntimeError(
                    "Удаление значений ENUM поддерживается только в PostgreSQL 16 и новее. "
                    f"Текущая версия сервера: {ver_num}."
                )

            query = sql.SQL("ALTER TYPE {} DROP VALUE %s").format(
                sql.Identifier(type_name)
            )
            cur.execute(query, (value,))

        app_logger.info(f"Из ENUM-типа {type_name} удалено значение {value!r}")

    def create_composite_type(self, name: str, fields: list[tuple[str, str]]):
        cleaned_fields = []
        for fname, ftype in fields:
            fname = (fname or "").strip()
            ftype = (ftype or "").strip()
            if not fname or not ftype:
                continue
            cleaned_fields.append((fname, ftype))

        if not cleaned_fields:
            raise ValueError("Составной тип должен содержать хотя бы одно поле")

        parts = []
        for fname, ftype in cleaned_fields:
            parts.append(
                sql.SQL("{} {}").format(
                    sql.Identifier(fname),
                    sql.SQL(ftype)
                )
            )

        query = sql.SQL("CREATE TYPE {} AS ({})").format(
            sql.Identifier(name),
            sql.SQL(", ").join(parts),
        )

        with self.cursor() as cur:
            cur.execute(query)

        app_logger.info(
            f"Создан составной тип {name} с полями "
            + ", ".join(f"{f[0]} {f[1]}" for f in cleaned_fields)
        )

    def drop_type(self, type_name: str, cascade: bool = False):
        query = sql.SQL("DROP TYPE {} {}").format(
            sql.Identifier(type_name),
            sql.SQL("CASCADE") if cascade else sql.SQL("RESTRICT"),
        )
        with self.cursor() as cur:
            cur.execute(query)

        app_logger.info(
            f"Удалён тип {type_name} с опцией "
            f"{'CASCADE' if cascade else 'RESTRICT'}"
        )
