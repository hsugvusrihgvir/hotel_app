from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox, QHeaderView,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.log.log import app_logger
from app.ui.cte_builder_window import CteBuilderWindow

from app.ui.cte_storage import GLOBAL_SAVED_CTES


class ViewsWindow(QMainWindow):
    """
    Менеджер представлений PostgreSQL (VIEW / MATERIALIZED VIEW / CTE).

    - слева: список VIEW, MATERIALIZED VIEW и сохранённых CTE;
    - справа: вкладки «Структура», «SQL / запрос», «Данные»;
    - кнопки: Показать данные, REFRESH MAT VIEW, Удалить VIEW/MAT VIEW,
      Обновить список, Создать через конструктор CTE.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        # name -> inner SELECT (без WITH)
        self.saved_ctes = GLOBAL_SAVED_CTES

        self.current_obj: dict | None = None  # {'schema','name','kind',...}

        self.setWindowTitle("Представления и CTE")
        self.resize(1000, 650)

        self._build_ui()
        self._load_views_list()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        header = QLabel("Представления (VIEW / MATERIALIZED VIEW / CTE)")
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet("color: #e5e7eb; font-size: 18px; font-weight: 600;")
        main_layout.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)
        main_layout.addWidget(body, 1)

        # -------- левая часть: список объектов --------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        lbl_list = QLabel("Объекты схемы public:")
        lbl_list.setStyleSheet("color: #d1d5db;")
        left_layout.addWidget(lbl_list)

        self.list_views = QListWidget()
        self.list_views.itemSelectionChanged.connect(self._on_selection_changed)
        left_layout.addWidget(self.list_views, 1)

        left_buttons = QHBoxLayout()
        self.btn_reload = QPushButton("Обновить")
        self.btn_new_cte = QPushButton("Создать через конструктор CTE")
        left_buttons.addWidget(self.btn_reload)
        left_buttons.addWidget(self.btn_new_cte)
        left_layout.addLayout(left_buttons)

        self.btn_reload.clicked.connect(self._load_views_list)
        self.btn_new_cte.clicked.connect(self._open_cte_builder)

        body_layout.addWidget(left, 0)

        # -------- правая часть --------
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs, 1)

        # вкладка "Структура"
        struct_tab = QWidget()
        struct_layout = QVBoxLayout(struct_tab)
        struct_layout.setContentsMargins(4, 4, 4, 4)
        struct_layout.setSpacing(6)

        self.lbl_current = QLabel("Ничего не выбрано")
        self.lbl_current.setStyleSheet("color: #d1d5db;")
        struct_layout.addWidget(self.lbl_current)

        self.table_columns = QTableWidget()
        self.table_columns.setColumnCount(3)
        self.table_columns.setHorizontalHeaderLabels(["#", "Имя колонки", "Тип"])
        self.table_columns.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_columns.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_columns.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        struct_layout.addWidget(self.table_columns, 1)

        self.tabs.addTab(struct_tab, "Структура")

        # вкладка "SQL / запрос"
        sql_tab = QWidget()
        sql_layout = QVBoxLayout(sql_tab)
        sql_layout.setContentsMargins(4, 4, 4, 4)
        sql_layout.setSpacing(6)

        self.lbl_sql = QLabel("Определение объекта будет показано здесь.")
        self.lbl_sql.setStyleSheet("color: #e5e7eb;")
        self.lbl_sql.setWordWrap(True)
        self.lbl_sql.setTextInteractionFlags(Qt.TextSelectableByMouse)
        sql_layout.addWidget(self.lbl_sql)

        self.tabs.addTab(sql_tab, "SQL / запрос")

        # вкладка "Данные"
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        data_layout.setContentsMargins(4, 4, 4, 4)
        data_layout.setSpacing(6)

        self.table_data = QTableWidget()

        # нормальные размеры колонок + горизонтальный скролл
        header_data = self.table_data.horizontalHeader()
        header_data.setStretchLastSection(False)
        header_data.setSectionResizeMode(QHeaderView.Interactive)

        self.table_data.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table_data.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        data_layout.addWidget(self.table_data, 1)

        header = self.table_data.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)


        data_layout.addWidget(self.table_data, 1)

        self.tabs.addTab(data_tab, "Данные")

        # нижние кнопки
        bottom = QHBoxLayout()

        # кнопку "Показать данные" больше не показываем — данные
        # подгружаются автоматически при переходе на вкладку "Данные"
        self.btn_open_data = QPushButton("Показать данные")
        self.btn_open_data.hide()

        self.btn_refresh_mat = QPushButton("REFRESH MATERIALIZED VIEW")
        self.btn_drop = QPushButton("Удалить VIEW / MAT VIEW")

        bottom.addWidget(self.btn_refresh_mat)
        bottom.addStretch()
        bottom.addWidget(self.btn_drop)

        right_layout.addLayout(bottom)
        body_layout.addWidget(right, 1)

        # сигналы
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.btn_refresh_mat.clicked.connect(self._refresh_current_mat_view)
        self.btn_drop.clicked.connect(self._drop_current)

        self._update_buttons_state()
        self._clear_details()

    # ------------------------------------------------------------------
    # Загрузка списка объектов
    # ------------------------------------------------------------------

    def _load_views_list(self):
        """Читает VIEW / MAT VIEW из БД и добавляет CTE из памяти."""
        self.list_views.clear()
        self.current_obj = None
        self._update_buttons_state()
        self._clear_details()

        rows = []
        try:
            with self.db.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_schema AS schema, table_name AS name, 'VIEW' AS kind
                    FROM information_schema.views
                    WHERE table_schema = 'public'
                    UNION ALL
                    SELECT schemaname AS schema, matviewname AS name, 'MATERIALIZED VIEW' AS kind
                    FROM pg_matviews
                    WHERE schemaname = 'public'
                    ORDER BY 1, 2;
                    """
                )
                rows = cur.fetchall()
        except Exception as e:
            app_logger.error(f"Ошибка загрузки списка представлений: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список представлений:\n{e}")

        # VIEW / MAT VIEW
        for row in rows:
            text = f"{row['schema']}.{row['name']} ({row['kind']})"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, {
                "schema": row["schema"],
                "name": row["name"],
                "kind": row["kind"],
            })
            if row["kind"] == "VIEW":
                item.setForeground(QColor("#93c5fd"))   # голубой
            else:
                item.setForeground(QColor("#6ee7b7"))   # мятный
            self.list_views.addItem(item)

        # CTE из памяти
        for name, inner_sql in self.saved_ctes.items():
            text = f"{name} (CTE)"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, {
                "schema": None,
                "name": name,
                "kind": "CTE",
                "inner_sql": inner_sql,
            })
            item.setForeground(QColor("#c4b5fd"))  # сиреневый
            self.list_views.addItem(item)

    # ------------------------------------------------------------------
    # Выбор объекта
    # ------------------------------------------------------------------

    def _on_selection_changed(self):
        items = self.list_views.selectedItems()
        if not items:
            self.current_obj = None
            self._clear_details()
            self._update_buttons_state()
            return

        item = items[0]
        self.current_obj = item.data(Qt.UserRole)
        self._load_details_for_current()
        self._update_buttons_state()

        # если уже открыта вкладка "Данные" — сразу обновим превью
        if self.tabs.currentIndex() == 2:
            self._load_data_for_current()

    def _clear_details(self):
        self.lbl_current.setText("Ничего не выбрано")
        self.lbl_sql.setText("Определение объекта будет показано здесь.")
        self.table_columns.setRowCount(0)
        self.table_data.setRowCount(0)
        self.table_data.setColumnCount(0)

    def _update_buttons_state(self):
        has_obj = self.current_obj is not None
        self.btn_open_data.setEnabled(has_obj)
        self.btn_drop.setEnabled(
            has_obj and self.current_obj.get("kind") in ("VIEW", "MATERIALIZED VIEW")
        )
        is_mat = has_obj and self.current_obj.get("kind") == "MATERIALIZED VIEW"
        self.btn_refresh_mat.setEnabled(is_mat)

    def _on_tab_changed(self, index: int):
        """Автоподгрузка данных при переходе на вкладку «Данные»."""
        # 0 — Структура, 1 — SQL, 2 — Данные
        if index == 2 and self.current_obj is not None:
            self._load_data_for_current()

    # ------------------------------------------------------------------
    # Детали объекта
    # ------------------------------------------------------------------

    def _load_details_for_current(self):
        if not self.current_obj:
            return

        kind = self.current_obj["kind"]
        schema = self.current_obj.get("schema")
        name = self.current_obj["name"]

        if kind == "CTE":
            self.lbl_current.setText(f"{name} — CTE (подзапрос)")
            inner_sql = self.current_obj.get("inner_sql", "")
            self.lbl_sql.setText(inner_sql or "Inner SELECT для CTE отсутствует.")
            self._load_columns_for_cte(name, inner_sql)
        else:
            self.lbl_current.setText(f"{schema}.{name} — {kind}")
            self._load_columns_for_view(schema, name)
            self._load_definition_for_view(kind, schema, name)

    def _load_columns_for_view(self, schema: str, name: str):
        """Структура для VIEW и MATERIALIZED VIEW.

        Сначала пробуем information_schema.columns, если пусто —
        падаем обратно на pg_catalog (работает и для мат. представлений).
        """
        cols = []
        try:
            with self.db.cursor() as cur:
                # обычный путь — information_schema
                cur.execute(
                    """
                    SELECT ordinal_position, column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (schema, name),
                )
                cols = cur.fetchall()

                # если вдруг пусто (часть мат. представлений), берём из pg_catalog
                if not cols:
                    cur.execute(
                        """
                        SELECT
                            a.attnum AS ordinal_position,
                            a.attname AS column_name,
                            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type
                        FROM pg_catalog.pg_attribute a
                        JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                        JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                        WHERE n.nspname = %s
                          AND c.relname = %s
                          AND a.attnum > 0
                          AND NOT a.attisdropped
                        ORDER BY a.attnum;
                        """,
                        (schema, name),
                    )
                    cols = cur.fetchall()
        except Exception as e:
            app_logger.error(f"Ошибка получения структуры {schema}.{name}: {e}")
            cols = []

        self.table_columns.setRowCount(0)
        self.table_columns.setRowCount(len(cols))
        for i, col in enumerate(cols):
            self.table_columns.setItem(i, 0, QTableWidgetItem(str(col["ordinal_position"])))
            self.table_columns.setItem(i, 1, QTableWidgetItem(col["column_name"]))
            self.table_columns.setItem(i, 2, QTableWidgetItem(col["data_type"]))

    def _load_definition_for_view(self, kind: str, schema: str, name: str):
        definition = None
        try:
            with self.db.cursor() as cur:
                if kind == "VIEW":
                    cur.execute(
                        """
                        SELECT view_definition
                        FROM information_schema.views
                        WHERE table_schema = %s AND table_name = %s;
                        """,
                        (schema, name),
                    )
                    row = cur.fetchone()
                    if row:
                        definition = row["view_definition"]
                else:
                    cur.execute(
                        """
                        SELECT definition
                        FROM pg_matviews
                        WHERE schemaname = %s AND matviewname = %s;
                        """,
                        (schema, name),
                    )
                    row = cur.fetchone()
                    if row:
                        definition = row["definition"]
        except Exception as e:
            app_logger.error(f"Ошибка получения SQL-определения для {schema}.{name}: {e}")

        if definition:
            self.lbl_sql.setText(definition)
        else:
            self.lbl_sql.setText("Не удалось получить SQL-определение для выбранного объекта.")

    def _load_columns_for_cte(self, cte_name: str, inner_sql: str):
        """Структура CTE: выполняем WITH ... SELECT * FROM cte LIMIT 0 и читаем cursor.description."""
        if not inner_sql:
            self.table_columns.setRowCount(0)
            return

        sql = f"WITH {cte_name} AS ({inner_sql}) SELECT * FROM {cte_name} LIMIT 0;"
        try:
            with self.db.cursor() as cur:
                cur.execute(sql)
                desc = cur.description
        except Exception as e:
            app_logger.error(f"Ошибка получения структуры CTE {cte_name}: {e}")
            self.table_columns.setRowCount(0)
            return

        if not desc:
            self.table_columns.setRowCount(0)
            return

        self.table_columns.setRowCount(len(desc))
        for i, col in enumerate(desc):
            name = col.name if hasattr(col, "name") else col[0]
            self.table_columns.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table_columns.setItem(i, 1, QTableWidgetItem(name))
            self.table_columns.setItem(i, 2, QTableWidgetItem("-"))

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def _load_data_for_current(self):
        if not self.current_obj:
            return

        kind = self.current_obj["kind"]
        schema = self.current_obj.get("schema")
        name = self.current_obj["name"]

        if kind == "CTE":
            inner_sql = self.current_obj.get("inner_sql", "")
            if not inner_sql:
                QMessageBox.warning(self, "CTE", "У этого CTE нет inner SELECT.")
                return
            sql = f"WITH {name} AS ({inner_sql}) SELECT * FROM {name} LIMIT 200;"
        else:
            sql = f'SELECT * FROM "{schema}"."{name}" LIMIT 200;'

        app_logger.info(f"ViewsWindow data SQL: {sql}")

        try:
            with self.db.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        except Exception as e:
            app_logger.error(f"Ошибка выборки данных: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные:\n{e}")
            return

        if not rows:
            self.table_data.setRowCount(0)
            self.table_data.setColumnCount(0)
            return

        cols = list(rows[0].keys())
        self.table_data.setColumnCount(len(cols))
        self.table_data.setHorizontalHeaderLabels(cols)
        self.table_data.setRowCount(len(rows))

        for r_idx, row in enumerate(rows):
            for c_idx, col in enumerate(cols):
                val = row[col]
                text = "" if val is None else str(val)
                self.table_data.setItem(r_idx, c_idx, QTableWidgetItem(text))

    # ------------------------------------------------------------------
    # REFRESH / DROP
    # ------------------------------------------------------------------

    def _refresh_current_mat_view(self):
        if not self.current_obj or self.current_obj.get("kind") != "MATERIALIZED VIEW":
            return

        schema = self.current_obj["schema"]
        name = self.current_obj["name"]

        sql = f'REFRESH MATERIALIZED VIEW "{schema}"."{name}";'
        try:
            with self.db.cursor() as cur:
                cur.execute(sql)
            QMessageBox.information(self, "REFRESH", f"Материализованное представление {schema}.{name} обновлено.")
            app_logger.info(f"REFRESH MATERIALIZED VIEW {schema}.{name}")
        except Exception as e:
            app_logger.error(f"Ошибка REFRESH MATERIALIZED VIEW {schema}.{name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить материализованное представление:\n{e}")

    def _drop_current(self):
        if not self.current_obj:
            return

        kind = self.current_obj["kind"]
        if kind not in ("VIEW", "MATERIALIZED VIEW"):
            QMessageBox.information(self, "Удаление", "Удалять можно только VIEW и MATERIALIZED VIEW.")
            return

        schema = self.current_obj["schema"]
        name = self.current_obj["name"]

        res = QMessageBox.question(
            self,
            "Удаление",
            f"Удалить {kind} {schema}.{name}?\n\nОбъект будет удалён из базы данных.",
        )
        if res != QMessageBox.Yes:
            return

        if kind == "VIEW":
            sql = f'DROP VIEW IF EXISTS "{schema}"."{name}" CASCADE;'
        else:
            sql = f'DROP MATERIALIZED VIEW IF EXISTS "{schema}"."{name}" CASCADE;'

        try:
            with self.db.cursor() as cur:
                cur.execute(sql)
            QMessageBox.information(self, "Удалено", f"{kind} {schema}.{name} удалено.")
            app_logger.info(f"Dropped {kind} {schema}.{name}")
            self._load_views_list()
        except Exception as e:
            app_logger.error(f"Ошибка удаления {kind} {schema}.{name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить объект:\n{e}")

    # ------------------------------------------------------------------
    # Конструктор CTE
    # ------------------------------------------------------------------

    def _open_cte_builder(self):
        """Открывает окно CteBuilderWindow и передаёт колбэк сохранения CTE."""
        try:
            wnd = CteBuilderWindow(self.db, self, on_save_cte=self._register_cte)
            wnd.show()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть конструктор CTE:\n{e}")
            app_logger.error(f"Ошибка открытия CteBuilderWindow: {e}")

    def _register_cte(self, name: str, inner_sql: str):
        """Колбэк из CteBuilderWindow: сохраняем CTE в памяти и обновляем список."""
        self.saved_ctes[name] = inner_sql
        self._load_views_list()
