from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QHeaderView,
    QTabWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.log.log import app_logger
from app.ui.collapsible_section import CollapsibleSection
from app.ui.data_window import WhereBuilderWidget, HavingBuilderWidget


class CteBuilderWindow(QMainWindow):
    """
    Окно-конструктор CTE (WITH-запросов).

    Работает с одной исходной таблицей/представлением и строит подзапрос вида:

        WITH cte_name AS (
            <собранный SELECT>
        )
        SELECT * FROM cte_name;
    """

    def __init__(self, db, parent=None, on_save_cte=None):
        """
        db — объект Database.
        on_save_cte(name: str, inner_sql: str) — колбэк из ViewsWindow
        для сохранения именованных CTE в менеджере представлений.
        """
        super().__init__(parent)
        self.db = db
        self.on_save_cte = on_save_cte

        self.setWindowTitle("Конструктор CTE (WITH)")
        self.resize(1200, 720)

        # имя исходного объекта
        self.current_source_schema = "public"
        self.current_source_name: str | None = None
        # тип источника: "table" / "view"
        self.current_source_kind: str = "table"

        # список всех колонок текущего источника
        self.all_columns: list[str] = []
        # типы данных по имени колонки
        self.col_types: dict[str, str] = {}

        self._build_ui()
        self._load_sources()
        self._reload_columns()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # верхняя панель: выбор источника и имя CTE
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)

        self.cte_name_edit = QLineEdit()
        self.cte_name_edit.setPlaceholderText("Имя CTE, например cte_report")

        self.source_kind = QComboBox()
        self.source_kind.addItems(["Таблица", "Представление"])
        self.source_kind.currentIndexChanged.connect(self._on_source_kind_changed)

        self.source_combo = QComboBox()
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)

        hl.addWidget(QLabel("Имя CTE:"))
        hl.addWidget(self.cte_name_edit, 2)
        hl.addWidget(QLabel("Источник:"))
        hl.addWidget(self.source_kind)
        hl.addWidget(self.source_combo, 2)

        main_layout.addWidget(header)

        # центральная область: слева конструкторы, справа таблица результата
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)

        # ---- левый блок с вкладками ----
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # ===== вкладка "Фильтры" =====
        filters_tab = QWidget()
        filters_layout = QVBoxLayout(filters_tab)
        filters_layout.setContentsMargins(4, 4, 4, 4)
        filters_layout.setSpacing(6)

        # SELECT
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)

        select_widget = QWidget()
        sl = QVBoxLayout(select_widget)
        sl.addWidget(QLabel("Колонки для SELECT:"))
        sl.addWidget(self.columns_list)

        select_section = CollapsibleSection("SELECT — выбор колонок", select_widget)
        filters_layout.addWidget(select_section)

        # WHERE
        self.where_builder = WhereBuilderWidget(self)
        where_section = CollapsibleSection("WHERE — условия отбора", self.where_builder)
        filters_layout.addWidget(where_section)

        # Поиск по строкам (LIKE / Regex / SIMILAR)
        self.search_column = QComboBox()
        self.search_mode = QComboBox()
        self.search_mode.addItems([
            "LIKE",
            "ILIKE",
            "~",
            "~*",
            "!~",
            "!~*",
            "SIMILAR TO",
            "NOT SIMILAR TO",
        ])
        self.search_value = QLineEdit()
        self.search_value.setPlaceholderText("Строка / шаблон для поиска")

        self.btn_apply_search = QPushButton("Применить поиск")
        self.btn_apply_search.clicked.connect(self._reload_result)

        search_widget = QWidget()
        sh = QHBoxLayout(search_widget)
        sh.addWidget(QLabel("Колонка:"))
        sh.addWidget(self.search_column)
        sh.addWidget(self.search_mode)
        sh.addWidget(self.search_value)
        sh.addWidget(self.btn_apply_search)

        search_section = CollapsibleSection("Поиск по строкам (LIKE / Regex / SIMILAR)", search_widget)
        filters_layout.addWidget(search_section)

        filters_layout.addStretch()
        self.tabs.addTab(filters_tab, "Фильтры")

        # ===== вкладка "Агрегация" =====
        agg_tab = QWidget()
        agg_layout = QVBoxLayout(agg_tab)
        agg_layout.setContentsMargins(4, 4, 4, 4)
        agg_layout.setSpacing(6)

        # GROUP BY + агрегаты
        self.group_col = QComboBox()
        self.aggregate_func = QComboBox()
        self.aggregate_func.addItems(["", "COUNT", "SUM", "AVG", "MIN", "MAX"])
        self.aggregate_target = QComboBox()

        self.btn_apply_group = QPushButton("Применить GROUP BY")
        self.btn_apply_group.clicked.connect(self._reload_result)

        group_widget = QWidget()
        gl = QHBoxLayout(group_widget)
        gl.addWidget(QLabel("GROUP BY:"))
        gl.addWidget(self.group_col)
        gl.addWidget(QLabel("Агрегат:"))
        gl.addWidget(self.aggregate_func)
        gl.addWidget(self.aggregate_target)
        gl.addWidget(self.btn_apply_group)

        group_section = CollapsibleSection("GROUP BY / Агрегаты", group_widget)
        agg_layout.addWidget(group_section)

        # HAVING
        self.having_builder = HavingBuilderWidget(self)
        having_section = CollapsibleSection("HAVING — условия по агрегатам", self.having_builder)
        agg_layout.addWidget(having_section)

        # ORDER BY
        self.order_col = QComboBox()
        self.order_dir = QComboBox()
        self.order_dir.addItems(["ASC", "DESC"])
        self.btn_apply_order = QPushButton("Применить ORDER BY")
        self.btn_apply_order.clicked.connect(self._reload_result)

        order_widget = QWidget()
        ow = QHBoxLayout(order_widget)
        ow.addWidget(QLabel("ORDER BY:"))
        ow.addWidget(self.order_col)
        ow.addWidget(self.order_dir)
        ow.addWidget(self.btn_apply_order)

        order_section = CollapsibleSection("ORDER BY", order_widget)
        agg_layout.addWidget(order_section)

        agg_layout.addStretch()
        self.tabs.addTab(agg_tab, "Агрегация")

        # ===== вкладка "CASE / NULL" =====
        case_tab = QWidget()
        case_layout = QVBoxLayout(case_tab)
        case_layout.setContentsMargins(4, 4, 4, 4)
        case_layout.setSpacing(6)
        case_layout.addWidget(QLabel("Конструктор CASE / COALESCE / NULLIF добавим позже."))
        case_layout.addStretch()
        self.tabs.addTab(case_tab, "CASE / NULL")

        left_layout.addWidget(self.tabs)

        # нижняя панель кнопок
        buttons = QWidget()
        bl = QHBoxLayout(buttons)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(6)

        self.btn_run = QPushButton("Выполнить CTE")
        self.btn_run.clicked.connect(self._reload_result)

        # сохранить только как временный CTE в модуле представлений
        self.btn_save_cte = QPushButton("Сохранить как CTE")
        self.btn_save_cte.clicked.connect(self._save_as_cte)

        # сохранить как обычное / материализованное представление в БД
        self.btn_save_view = QPushButton("Сохранить как VIEW")
        self.btn_save_view.clicked.connect(self._save_as_view)

        self.btn_save_mat_view = QPushButton("Сохранить как MATERIALIZED VIEW")
        self.btn_save_mat_view.clicked.connect(self._save_as_mat_view)

        bl.addWidget(self.btn_run)
        bl.addStretch()
        bl.addWidget(self.btn_save_cte)
        bl.addWidget(self.btn_save_view)
        bl.addWidget(self.btn_save_mat_view)

        left_layout.addWidget(buttons)

        body_layout.addWidget(left, 0)

        # ---- правая таблица результата ----
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        body_layout.addWidget(self.table, 1)

        main_layout.addWidget(body)

    # ------------------------------------------------------------------
    # Загрузка источников и колонок
    # ------------------------------------------------------------------

    def _load_sources(self):
        """Заполняем список источников (таблицы или представления) в combobox."""
        self.source_combo.blockSignals(True)
        self.source_combo.clear()

        kind = self.source_kind.currentText()
        items: list[str] = []

        try:
            with self.db.cursor() as cur:
                if kind == "Таблица":
                    q = """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                        ORDER BY table_name;
                    """
                else:
                    q = """
                        SELECT table_name
                        FROM information_schema.views
                        WHERE table_schema = 'public'
                        ORDER BY table_name;
                    """
                cur.execute(q)
                rows = cur.fetchall()
                items = [r["table_name"] for r in rows]
        except Exception as e:
            app_logger.error(f"Ошибка загрузки списка источников для CTE: {e}")
            items = []

        if not items:
            self.source_combo.addItem("")
        else:
            self.source_combo.addItems(items)

        self.source_combo.blockSignals(False)

    def _on_source_kind_changed(self, index: int):
        self._load_sources()
        self._reload_columns()

    def _on_source_changed(self, index: int):
        self._reload_columns()

    def _reload_columns(self):
        """Подтягиваем колонки и типы для выбранного источника."""
        name = self.source_combo.currentText().strip()
        if not name:
            self.all_columns = []
            self.col_types.clear()
            self._apply_columns_to_builders()
            return

        self.current_source_name = name
        self.current_source_kind = "table" if self.source_kind.currentText() == "Таблица" else "view"

        self.all_columns = []
        self.col_types.clear()

        try:
            q = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position;
            """
            with self.db.cursor() as cur:
                cur.execute(q, (self.current_source_schema, name))
                rows = cur.fetchall()
        except Exception as e:
            app_logger.error(f"Ошибка получения колонок для CTE-источника {name}: {e}")
            rows = []

        for r in rows:
            col_name = r["column_name"]
            self.all_columns.append(col_name)
            self.col_types[col_name] = r.get("data_type", "text")

        # SELECT список
        self.columns_list.clear()
        for c in self.all_columns:
            item = QListWidgetItem(c)
            item.setCheckState(Qt.Checked)
            self.columns_list.addItem(item)

        # combobox'ы
        self.search_column.clear()
        self.group_col.clear()
        self.aggregate_target.clear()
        self.order_col.clear()

        self.search_column.addItems(self.all_columns)
        self.group_col.addItems([""] + self.all_columns)
        self.aggregate_target.addItems([""] + self.all_columns)
        self.order_col.addItems(self.all_columns)

        self._apply_columns_to_builders()

    def _apply_columns_to_builders(self):
        self.where_builder.set_columns(self.all_columns, self.col_types)
        self.having_builder.set_columns(self.all_columns, self.col_types)

    # ------------------------------------------------------------------
    # Форматирование литералов для поиска
    # ------------------------------------------------------------------

    def _format_search_literal(self, raw_val: str, data_type: str, op: str) -> str:
        """
        Упрощённый вариант форматирования значения под операторы LIKE / SIMILAR / regex.
        """

        numeric_like = ("smallint", "integer", "bigint", "numeric", "real", "double")
        bool_like = ("boolean",)
        date_like = ("date", "timestamp", "timestamp with time zone", "time")

        # числа
        if any(x in data_type for x in numeric_like):
            try:
                float(raw_val.replace(",", "."))
            except ValueError:
                raise ValueError("Для числового столбца должно быть числовое значение.")
            return raw_val

        # boolean
        if any(x in data_type for x in bool_like):
            val = raw_val.lower()
            if val in ("true", "t", "1", "yes", "y", "да"):
                return "true"
            if val in ("false", "f", "0", "no", "n", "нет"):
                return "false"
            raise ValueError("Для булевого столбца используйте true/false, да/нет, 1/0.")

        # дата / время
        if any(x in data_type for x in date_like):
            esc = raw_val.replace("'", "''")
            return f"'{esc}'"

        # текст
        esc = raw_val.replace("'", "''")

        if op in ("LIKE", "ILIKE") and "%" not in esc and "_" not in esc:
            esc = f"%{esc}%"

        return f"'{esc}'"

    # ------------------------------------------------------------------
    # Построение SQL
    # ------------------------------------------------------------------

    def _build_inner_select(self) -> str:
        """Собираем внутренний SELECT для CTE (без WITH/SELECT * FROM cte)."""
        if not self.current_source_name:
            return "SELECT 1 WHERE false"

        # SELECT-список
        checked: list[str] = []
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())

        if checked:
            cols = ", ".join(checked)
        else:
            cols = ", ".join(self.all_columns) if self.all_columns else "*"

        q = f"SELECT {cols} FROM {self.current_source_schema}.{self.current_source_name}"

        where_clauses: list[str] = []

        # условия WHERE из конструктора
        where_sql = self.where_builder.build_where_sql()
        if where_sql:
            where_clauses.append(where_sql)

        # поиск по строкам
        col = self.search_column.currentText().strip()
        pattern = self.search_value.text().strip()
        mode = self.search_mode.currentText().strip()

        if col and pattern:
            dt = self.col_types.get(col, "text").lower()
            try:
                literal = self._format_search_literal(pattern, dt, mode)
            except ValueError as e:
                QMessageBox.warning(self, "Ошибка значения", str(e))
                literal = None

            if literal is not None:
                where_clauses.append(f"{col} {mode} {literal}")

        if where_clauses:
            q += " WHERE " + " AND ".join(where_clauses)

        # агрегирование
        aggregate_mode = bool(
            self.aggregate_func.currentText().strip()
            and self.aggregate_target.currentText().strip()
        )

        if aggregate_mode:
            group_col = self.group_col.currentText().strip()
            func = self.aggregate_func.currentText().strip()
            target = self.aggregate_target.currentText().strip()

            if group_col:
                q = f"SELECT {group_col}, {func}({target}) AS agg_value FROM ({q}) AS src"
                q += f" GROUP BY {group_col}"
            else:
                q = f"SELECT {func}({target}) AS agg_value FROM ({q}) AS src"

            having_sql = self.having_builder.build_having_sql()
            if having_sql:
                q += f" HAVING {having_sql}"

        # ORDER BY
        order_col = self.order_col.currentText().strip()
        if order_col:
            q += f" ORDER BY {order_col} {self.order_dir.currentText().strip()}"

        return q

    def _build_cte_sql(self) -> str:
        """Финальный SQL: WITH cte AS (...) SELECT * FROM cte;"""
        inner = self._build_inner_select()
        cte_name = self.cte_name_edit.text().strip() or "cte_result"
        return f"WITH {cte_name} AS ({inner}) SELECT * FROM {cte_name};"

    def _reload_result(self):
        """Выполнить CTE и показать результат в правой таблице."""
        sql = self._build_cte_sql()
        app_logger.info(f"CTEBuilder SQL: {sql}")
        try:
            with self.db.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()
        except Exception as e:
            app_logger.error(f"Ошибка выполнения CTE-запроса: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения запроса:\n{e}")
            return

        if not rows:
            self.table.clear()
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        cols = list(rows[0].keys())
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels(cols)

        for r_idx, row in enumerate(rows):
            for c_idx, col in enumerate(cols):
                val = row[col]
                text = "" if val is None else str(val)
                self.table.setItem(r_idx, c_idx, QTableWidgetItem(text))

    # ---------------------------------------------------------
    # Сохранение CTE / VIEW / MATERIALIZED VIEW
    # ---------------------------------------------------------

    def _save_as_cte(self):
        """Сохранить текущий подзапрос как именованный CTE в модуле представлений."""
        name = self.cte_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Имя CTE", "Сначала введите имя CTE.")
            return

        inner_sql = self._build_inner_select()

        if not self.on_save_cte:
            QMessageBox.information(
                self,
                "CTE",
                "CTE собран, но модуль представлений не передал обработчик сохранения.\n"
                "Вы всё равно можете выполнить запрос и создать VIEW / MATERIALIZED VIEW."
            )
            return

        try:
            self.on_save_cte(name, inner_sql)
            QMessageBox.information(self, "CTE", f"CTE {name} сохранён в модуле представлений.")
            app_logger.info(f"CTE сохранён через CteBuilderWindow: {name}")
        except Exception as e:
            app_logger.error(f"Ошибка сохранения CTE {name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить CTE:\n{e}")

    def _save_as_view(self):
        """Сохранить текущий подзапрос как VIEW в БД."""
        sql_select = self._build_inner_select()
        name = self.cte_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Имя CTE", "Сначала введите имя для CTE / представления.")
            return

        try:
            with self.db.cursor() as cur:
                cur.execute(f"CREATE OR REPLACE VIEW {name} AS {sql_select}")
            QMessageBox.information(self, "VIEW", f"Представление {name} успешно создано.")
            app_logger.info(f"Создано VIEW {name} через CTE-конструктор")
        except Exception as e:
            app_logger.error(f"Ошибка создания VIEW {name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать VIEW:\n{e}")

    def _save_as_mat_view(self):
        """Сохранить текущий подзапрос как MATERIALIZED VIEW в БД."""
        sql_select = self._build_inner_select()
        name = self.cte_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Имя CTE", "Сначала введите имя для CTE / представления.")
            return

        try:
            with self.db.cursor() as cur:
                cur.execute(f"CREATE MATERIALIZED VIEW IF NOT EXISTS {name} AS {sql_select}")
            QMessageBox.information(
                self,
                "MATERIALIZED VIEW",
                f"Материализованное представление {name} создано или уже существует."
            )
            app_logger.info(f"Создано MATERIALIZED VIEW {name} через CTE-конструктор")
        except Exception as e:
            app_logger.error(f"Ошибка создания MATERIALIZED VIEW {name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать MATERIALIZED VIEW:\n{e}")
