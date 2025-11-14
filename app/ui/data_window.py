# data_window.py — окно просмотра данных (расширенное + панель поиска)

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from app.log.log import app_logger


class DataWindow(QMainWindow):
    """отображение JOIN + фильтры + агрегаты + группировки + поиск"""

    def __init__(self, db, join_info, parent=None):
        super().__init__(parent)
        self.db = db
        self.join_info = join_info

        self.setWindowTitle("Просмотр данных (расширенный)")
        self.resize(1300, 750)

        self._build_ui()
        self._load_data()

    def _load_subquery_tables(self):
        q = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name;
        """
        with self.db.cursor() as cur:
            cur.execute(q)
            tables = [r["table_name"] for r in cur.fetchall()]

        self.sub_table.addItems(tables)
        self._load_subquery_columns()

        self.sub_table.currentTextChanged.connect(self._load_subquery_columns)

    def _load_subquery_columns(self):
        table = self.sub_table.currentText()
        if not table:
            return

        q = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name=%s
            ORDER BY ordinal_position
        """
        with self.db.cursor() as cur:
            cur.execute(q, (table,))
            cols = [r["column_name"] for r in cur.fetchall()]

        self.sub_right_col.clear()
        self.sub_right_col.addItems(cols)

    # =====================================================================
    # UI
    # =====================================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # ---------------- выбор колонок для SELECT ----------------------
        cols_box = QHBoxLayout()
        layout.addLayout(cols_box)

        cols_box.addWidget(QLabel("Колонки (SELECT):"))

        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)
        self.columns_list.setMaximumHeight(120)
        cols_box.addWidget(self.columns_list, 1)

        # ---------------- WHERE ----------------------
        where_box = QHBoxLayout()
        layout.addLayout(where_box)

        self.filter_where = QLineEdit()
        self.filter_where.setPlaceholderText("WHERE условие (например: t1.score > 0)")
        where_box.addWidget(self.filter_where)

        self.btn_apply_where = QPushButton("Применить WHERE")
        where_box.addWidget(self.btn_apply_where)
        self.btn_apply_where.clicked.connect(self._load_data)

        # ---------------- SEARCH PANEL ----------------------
        search_box = QHBoxLayout()
        layout.addLayout(search_box)

        search_box.addWidget(QLabel("Поиск:"))

        self.search_column = QComboBox()
        search_box.addWidget(self.search_column)

        self.search_mode = QComboBox()
        self.search_mode.addItems([
            "LIKE",
            "ILIKE",
            "~",
            "~*",
            "!~",
            "!~*",
            "SIMILAR TO",
            "NOT SIMILAR TO"
        ])
        search_box.addWidget(self.search_mode)

        self.search_value = QLineEdit()
        self.search_value.setPlaceholderText("шаблон (например: %bot% или ^ddos.*)")
        search_box.addWidget(self.search_value)

        self.btn_apply_search = QPushButton("Применить поиск")
        search_box.addWidget(self.btn_apply_search)
        self.btn_apply_search.clicked.connect(self._load_data)

        # ---------------- SUBQUERY PANEL (ANY / ALL / EXISTS) ----------------------

        sub_box = QHBoxLayout()
        layout.addLayout(sub_box)

        sub_box.addWidget(QLabel("Подзапрос:"))

        # колонка, с которой сравнивают
        self.sub_left_col = QComboBox()
        sub_box.addWidget(self.sub_left_col)

        # оператор сравнения
        self.sub_operator = QComboBox()
        self.sub_operator.addItems(["=", "<>", ">", "<", ">=", "<="])
        sub_box.addWidget(self.sub_operator)

        # режим подзапроса
        self.sub_mode = QComboBox()
        self.sub_mode.addItems(["ANY", "ALL", "EXISTS", "NOT EXISTS"])
        sub_box.addWidget(self.sub_mode)

        # таблица подзапроса
        self.sub_table = QComboBox()
        sub_box.addWidget(self.sub_table)

        # колонка подзапроса
        self.sub_right_col = QComboBox()
        sub_box.addWidget(self.sub_right_col)

        # дополнительный WHERE подзапроса
        self.sub_where = QLineEdit()
        self.sub_where.setPlaceholderText("WHERE для подзапроса (опц.)")
        sub_box.addWidget(self.sub_where)

        self.btn_apply_sub = QPushButton("Применить подзапрос")
        sub_box.addWidget(self.btn_apply_sub)
        self.btn_apply_sub.clicked.connect(self._load_data)

        # ---------------- ORDER BY ----------------------
        order_box = QHBoxLayout()
        layout.addLayout(order_box)

        order_box.addWidget(QLabel("ORDER BY:"))

        self.order_col = QComboBox()
        self.order_dir = QComboBox()
        self.order_dir.addItems(["ASC", "DESC"])

        order_box.addWidget(self.order_col)
        order_box.addWidget(self.order_dir)

        self.btn_apply_order = QPushButton("Применить ORDER")
        order_box.addWidget(self.btn_apply_order)
        self.btn_apply_order.clicked.connect(self._load_data)

        # ---------------- GROUP BY + агрегаты ----------------------
        group_box = QHBoxLayout()
        layout.addLayout(group_box)

        group_box.addWidget(QLabel("GROUP BY:"))
        self.group_col = QComboBox()
        group_box.addWidget(self.group_col)

        group_box.addWidget(QLabel("Агрегат:"))
        self.aggregate_func = QComboBox()
        self.aggregate_func.addItems(["", "COUNT", "SUM", "AVG", "MIN", "MAX"])
        group_box.addWidget(self.aggregate_func)

        self.aggregate_target = QComboBox()
        group_box.addWidget(self.aggregate_target)

        self.btn_apply_group = QPushButton("Применить GROUP BY")
        group_box.addWidget(self.btn_apply_group)
        self.btn_apply_group.clicked.connect(self._load_data)

        # ---------------- HAVING ----------------------
        having_box = QHBoxLayout()
        layout.addLayout(having_box)

        self.filter_having = QLineEdit()
        self.filter_having.setPlaceholderText("HAVING условие (например: COUNT(t1.id) > 2)")
        having_box.addWidget(self.filter_having)

        self.btn_apply_having = QPushButton("Применить HAVING")
        having_box.addWidget(self.btn_apply_having)
        self.btn_apply_having.clicked.connect(self._load_data)

        # ---------------- TABLE ----------------------
        self.table = QTableWidget()
        layout.addWidget(self.table)

        # заполняем все списки колонок (из join_info)
        self._load_all_column_lists()
        self._load_subquery_tables()

    # =====================================================================
    # lists
    # =====================================================================

    def _load_all_column_lists(self):
        # полный список доступных колонок из мастера JOIN (table.col)
        all_cols = list(self.join_info.get("selected_columns", []))

        # список с чекбоксами
        self.columns_list.clear()
        for col in all_cols:
            item = QListWidgetItem(col)
            # по умолчанию все включены
            item.setCheckState(Qt.Checked)
            self.columns_list.addItem(item)

        # комбобоксы
        self.search_column.clear()
        self.sub_left_col.clear()
        self.order_col.clear()
        self.group_col.clear()
        self.aggregate_target.clear()

        self.search_column.addItems(all_cols)
        self.sub_left_col.addItems(all_cols)
        self.order_col.addItems(all_cols)
        self.group_col.addItems([""] + all_cols)
        self.aggregate_target.addItems([""] + all_cols)

    # =====================================================================
    # SQL builder
    # =====================================================================

    def _build_sql(self):
        info = self.join_info

        all_cols = info.get("selected_columns", [])

        # какие колонки реально выбрал пользователь (чекбоксы)
        checked = []
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())

        if checked:
            cols = ", ".join(checked)
        elif all_cols:
            cols = ", ".join(all_cols)
        else:
            cols = "*"

        # aggregate overrides normal select
        if self.aggregate_func.currentText() and self.aggregate_target.currentText():
            cols = f"{self.aggregate_func.currentText()}({self.aggregate_target.currentText()}) AS agg_value"

        q = (
            f"SELECT {cols} "
            f"FROM {info['table1']} {info['join_type']} JOIN {info['table2']} "
            f"ON {info['table1']}.{info['col1']} = {info['table2']}.{info['col2']}"
        )

        # WHERE
        if self.filter_where.text().strip():
            q += f" WHERE {self.filter_where.text().strip()}"

        # SEARCH
        if self.search_value.text().strip():
            col = self.search_column.currentText()
            mode = self.search_mode.currentText()
            val = self.search_value.text().strip()

            if "WHERE" in q:
                q += f" AND {col} {mode} '{val}'"
            else:
                q += f" WHERE {col} {mode} '{val}'"

        # GROUP BY
        if self.group_col.currentText().strip():
            q += f" GROUP BY {self.group_col.currentText().strip()}"

        # HAVING
        if self.filter_having.text().strip():
            q += f" HAVING {self.filter_having.text().strip()}"

        # SUBQUERY ANY / ALL / EXISTS
        if self.sub_mode.currentText():
            mode = self.sub_mode.currentText()
            left = self.sub_left_col.currentText()
            right_col = self.sub_right_col.currentText()
            table = self.sub_table.currentText()
            op = self.sub_operator.currentText()

            # строим подзапрос
            sub_sql = f"(SELECT {right_col} FROM {table}"

            if self.sub_where.text().strip():
                sub_sql += f" WHERE {self.sub_where.text().strip()}"

            sub_sql += ")"

            # EXISTS вариант
            if mode == "EXISTS":
                condition = f"EXISTS {sub_sql}"
            elif mode == "NOT EXISTS":
                condition = f"NOT EXISTS {sub_sql}"
            else:
                # ANY / ALL
                condition = f"{left} {op} {mode} {sub_sql}"

            # добавляем в запрос
            if "WHERE" in q:
                q += f" AND {condition}"
            else:
                q += f" WHERE {condition}"

        # ORDER BY
        if self.order_col.currentText().strip():
            q += (
                f" ORDER BY {self.order_col.currentText().strip()} "
                f"{self.order_dir.currentText().strip()}"
            )

        return q + ";"

    # =====================================================================
    # loader
    # =====================================================================

    def _load_data(self):
        try:
            sql = self._build_sql()
            with self.db.cursor() as cur:
                cur.execute(sql)
                rows = cur.fetchall()

            if not rows:
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                return

            cols = list(rows[0].keys())
            self.table.setColumnCount(len(cols))
            self.table.setHorizontalHeaderLabels(cols)
            self.table.setRowCount(len(rows))

            for r, row in enumerate(rows):
                for c, col in enumerate(cols):
                    self.table.setItem(r, c, QTableWidgetItem(str(row[col])))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения запроса:\n{e}")
            app_logger.error(f"DataWindow SQL error: {e}")
