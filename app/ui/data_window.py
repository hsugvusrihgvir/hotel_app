from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QPushButton,
    QMessageBox, QHBoxLayout, QGroupBox, QFormLayout,
    QLabel, QComboBox, QLineEdit, QCheckBox,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem

from app.ui.filters_window import FilterWindow


class DataWindow(QDialog):
    """
    Окно вывода данных о бронированиях.
    Содержит:
      - стандартную сводную таблицу по бронированиям (JOIN stays/clients/rooms),
      - простые фильтры (дата/комфорт/оплата),
      - расширенный конструктор SELECT (AdvancedSelectDialog).
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.setWindowTitle("Данные о бронированиях")
        self.setModal(True)
        self.setMinimumSize(900, 500)

        self.setStyleSheet("""
            QDialog {
                background: #171a1d;
                color: #e8e6e3;
            }
            QTableView {
                background: #242a30;
                color: #e8e6e3;
                border: 1px solid #323a42;
                gridline-color: #323a42;
                outline: 0;
            }
            QTableView::item:hover {
                background: #2b3238;
                selection-background-color: #2b3238;
            }
            QHeaderView::section {
                background: #20252a;
                color: #e8e6e3;
                border: 1px solid #323a42;
                padding: 8px;
            }
            QPushButton {
                background: #242a30;
                color: #e8e6e3;
                border: 1px solid #323a42;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #2b3238;
            }
        """)

        if db is None:
            raise RuntimeError("Ошибка. Нет подключения к БД. Откройте сначала соединение.")
        self.db = db

        self._setup_ui()
        self.update_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # таблица
        self.table_view = QTableView()
        self.model = QStandardItemModel()
        self.table_view.setModel(self.model)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table_view)

        # кнопки
        btns = QHBoxLayout()
        self.btn_update = QPushButton("Обновить")
        self.btn_update.clicked.connect(self.update_table)

        self.btn_filter = QPushButton("Фильтры")
        self.btn_filter.clicked.connect(self.filter_button)

        self.btn_advanced = QPushButton("Расширенный запрос…")
        self.btn_advanced.clicked.connect(self.open_advanced_query)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)

        btns.addWidget(self.btn_update)
        btns.addWidget(self.btn_filter)
        btns.addWidget(self.btn_advanced)
        btns.addStretch()
        btns.addWidget(self.btn_close)

        layout.addLayout(btns)

    def update_table(self, filter_params=None):
        """
        Стандартная сводная таблица по stays/clients/rooms
        с поддержкой простых фильтров (окон FilterWindow).
        """
        self.model.clear()
        headers = [
            "ID",
            "Клиент",
            "Номер",
            "Комфорт",
            "Заезд",
            "Выезд",
            "Оплата",
            "Статус",
        ]

        try:
            rows = self.db.load_data(filter_params)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        if not rows:
            self.model.setHorizontalHeaderLabels(["Нет данных"])
            return

        self.model.setHorizontalHeaderLabels(headers)
        for row in rows:
            items = [QStandardItem(str(v)) for v in row]
            self.model.appendRow(items)

        self.table_view.resizeColumnsToContents()

    def show_custom_data(self, headers, rows):
        """
        Показ результата расширенного SELECT.
        """
        self.model.clear()
        if not rows:
            self.model.setHorizontalHeaderLabels(["Нет данных"])
            return

        self.model.setHorizontalHeaderLabels(headers)
        for row in rows:
            items = [QStandardItem(str(v)) for v in row]
            self.model.appendRow(items)

        self.table_view.resizeColumnsToContents()

    def filter_button(self):
        """Открытие окна простых фильтров."""
        try:
            fw = FilterWindow(self, self.db)
            fw.filterApplied.connect(self.handle_filter)
            fw.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия фильтра: {e}")

    def handle_filter(self, params):
        """Применение фильтров из FilterWindow."""
        self.update_table(params)

    def open_advanced_query(self):
        """Открытие конструктора расширенных SELECT-запросов."""
        try:
            dlg = AdvancedSelectDialog(self, self.db)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия расширенного запроса: {e}")


class AdvancedSelectDialog(QDialog):
    """
    Конструктор расширенного SELECT, который работает
    с АКТУАЛЬНОЙ схемой БД.

    Логика:
      1) Пользователь выбирает таблицу из существующих (list_tables()).
      2) Для выбранной таблицы подгружаются поля и их типы через get_table_columns.
      3) На основе типов:
         - формируется список выводимых столбцов (чекбоксы);
         - формируются списки столбцов для WHERE / ORDER BY / GROUP BY / HAVING;
         - подбираются допустимые операторы (для текста/чисел/дат/boolean).
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent)

        if db is None:
            raise RuntimeError("Нет подключения к БД.")
        self.db = db
        self.parent_window: DataWindow = parent  # тип подсказка

        self.setWindowTitle("Расширенный запрос (SELECT)")
        self.setModal(True)
        self.setMinimumSize(850, 650)

        self.setStyleSheet("""
            QDialog {
                background: #171a1d;
                color: #e8e6e3;
            }
            QGroupBox {
                border: 1px solid #323a42;
                margin-top: 12px;
                padding: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QLabel { color: #e8e6e3; }
            QLineEdit, QComboBox {
                background: #242a30;
                color: #e8e6e3;
                border: 1px solid #323a42;
                padding: 4px 6px;
                border-radius: 4px;
            }
            QPushButton {
                background: #242a30;
                color: #e8e6e3;
                border: 1px solid #323a42;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #2b3238; }
            QCheckBox { spacing: 6px; }
        """)

        # текущее описание полей таблицы
        self.columns = []        # список словарей с метаданными поля
        self.col_checks = {}     # чекбоксы вывода
        self.tables = []         # список доступных таблиц

        self._load_tables()
        self._build_ui()

        # сразу загрузим колонки для первой таблицы (если она есть)
        if self.tables:
            self.cb_table.setCurrentIndex(0)
            self._load_columns_for_table(self.cb_table.currentData())

    # ====== МЕТАДАННЫЕ БД ======

    def _load_tables(self):
        """Считываем список таблиц схемы public."""
        try:
            self.tables = self.db.list_tables()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список таблиц: {e}")
            self.tables = []

    def _categorize_type(self, type_str: str) -> str:
        """
        Грубое определение категории типа:
          - text:  text, varchar, char, ...
          - number: int, numeric, real, double
          - date: date, time, timestamp
          - bool: bool
          - other: всё остальное (enum, массивы и т.п.)
        """
        if type_str is None:
            return "other"
        t = type_str.lower()
        if "char" in t or "text" in t:
            return "text"
        if "int" in t or "numeric" in t or "real" in t or "double" in t:
            return "number"
        if "date" in t or "time" in t:
            return "date"
        if "bool" in t:
            return "bool"
        return "other"

    def _load_columns_for_table(self, table_name: str | None):
        """Загружаем список полей и типов для выбранной таблицы и перестраиваем UI."""
        self.columns = []
        self.col_checks.clear()

        # чистим динамические элементы (чекбоксы, комбобоксы по столбцам)
        # колонки будут добавлены заново
        for i in reversed(range(self.cols_layout.count())):
            w = self.cols_layout.itemAt(i).widget()
            if w is not None:
                w.setParent(None)

        self.cb_where_col.clear()
        self.cb_where_col.addItem("— нет —", None)

        self.cb_order_col.clear()
        self.cb_group_col.clear()
        self.cb_agg_col.clear()

        if not table_name:
            return

        # получаем структуру таблицы
        try:
            cols = self.db.get_table_columns("public", table_name)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить столбцы таблицы {table_name}: {e}")
            return

        # формируем внутреннее описание колонок
        for c in cols:
            name = c["name"]
            tstr = c["type"]
            cat = self._categorize_type(tstr)
            self.columns.append(
                {
                    "name": name,      # имя колонки в таблице
                    "sql": name,       # имя для SQL (t.name)
                    "title": name,     # подпись в интерфейсе
                    "type": tstr,
                    "category": cat,
                }
            )

        # строим чекбоксы вывода и заполняем комбобоксы
        for col in self.columns:
            title = col["title"]
            key = col["name"]

            cb = QCheckBox(title)
            cb.setChecked(True)
            self.col_checks[key] = cb
            self.cols_layout.addWidget(cb)

            self.cb_where_col.addItem(title, key)
            self.cb_order_col.addItem(title, key)
            self.cb_group_col.addItem(title, key)
            self.cb_agg_col.addItem(title, key)

        # обновляем набор операторов для WHERE при смене колонки
        self._update_where_operators()

    # ====== UI ======

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # ScrollArea для содержимого
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignTop)

        # ---- 0. Выбор таблицы ----
        gb_table = QGroupBox("Таблица")
        table_layout = QFormLayout(gb_table)
        self.cb_table = QComboBox()
        for t in self.tables:
            self.cb_table.addItem(t, t)
        self.cb_table.currentIndexChanged.connect(self._on_table_changed)
        table_layout.addRow("Таблица:", self.cb_table)
        container_layout.addWidget(gb_table)

        # ---- 1. Выводимые столбцы ----
        gb_cols = QGroupBox("Выводимые столбцы")
        self.cols_layout = QVBoxLayout(gb_cols)
        container_layout.addWidget(gb_cols)

        # ---- 2. WHERE / LIKE / регулярки ----
        gb_where = QGroupBox("Условие отбора (WHERE, LIKE, регулярные выражения)")
        where_layout = QFormLayout(gb_where)

        self.cb_where_col = QComboBox()
        self.cb_where_col.addItem("— нет —", None)
        self.cb_where_col.currentIndexChanged.connect(self._update_where_operators)

        self.cb_where_op = QComboBox()
        self.ed_where_val1 = QLineEdit()
        self.ed_where_val2 = QLineEdit()
        self.ed_where_val2.setEnabled(False)

        self.cb_where_op.currentTextChanged.connect(self._on_where_op_changed)

        where_layout.addRow("Столбец:", self.cb_where_col)
        where_layout.addRow("Оператор:", self.cb_where_op)
        where_layout.addRow("Значение 1:", self.ed_where_val1)
        where_layout.addRow("Значение 2 (для BETWEEN):", self.ed_where_val2)

        container_layout.addWidget(gb_where)

        # ---- 3. ORDER BY ----
        gb_order = QGroupBox("Сортировка (ORDER BY)")
        order_layout = QFormLayout(gb_order)

        self.chk_use_order = QCheckBox("Использовать сортировку")
        self.cb_order_col = QComboBox()
        self.cb_order_dir = QComboBox()
        self.cb_order_dir.addItems(["по возрастанию", "по убыванию"])

        order_layout.addRow(self.chk_use_order)
        order_layout.addRow("Столбец:", self.cb_order_col)
        order_layout.addRow("Порядок:", self.cb_order_dir)

        container_layout.addWidget(gb_order)

        # ---- 4. GROUP BY / HAVING ----
        gb_group = QGroupBox("Группировка и агрегаты (GROUP BY / HAVING)")
        group_layout = QFormLayout(gb_group)

        self.chk_use_group = QCheckBox("Включить группировку")

        self.cb_group_col = QComboBox()
        self.cb_agg_func = QComboBox()
        self.cb_agg_func.addItems(["(нет)", "COUNT", "SUM", "AVG", "MIN", "MAX"])
        self.cb_agg_col = QComboBox()

        self.cb_having_op = QComboBox()
        self.cb_having_op.addItems([">", ">=", "<", "<=", "=", "!="])
        self.ed_having_val = QLineEdit()

        self.chk_use_group.toggled.connect(self._update_group_enabled)
        self._update_group_enabled(False)

        group_layout.addRow(self.chk_use_group)
        group_layout.addRow("Группировать по:", self.cb_group_col)
        group_layout.addRow("Агрегатная функция:", self.cb_agg_func)
        group_layout.addRow("Колонка для агрегата:", self.cb_agg_col)
        group_layout.addRow("Оператор HAVING:", self.cb_having_op)
        group_layout.addRow("Значение:", self.ed_having_val)

        container_layout.addWidget(gb_group)

        # Вставляем контейнер в скролл
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # ---- Кнопки ----
        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_run = QPushButton("Выполнить")
        self.btn_cancel = QPushButton("Отмена")
        self.btn_run.clicked.connect(self._run_query)
        self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_run)
        btns.addWidget(self.btn_cancel)

        main_layout.addLayout(btns)

    # ====== HELPERS ДЛЯ UI ======

    def _on_table_changed(self, idx: int):
        table_name = self.cb_table.itemData(idx)
        self._load_columns_for_table(table_name)

    def _on_where_op_changed(self, text: str):
        self.ed_where_val2.setEnabled(text == "BETWEEN")

    def _update_group_enabled(self, enabled: bool):
        self.cb_group_col.setEnabled(enabled)
        self.cb_agg_func.setEnabled(enabled)
        self.cb_agg_col.setEnabled(enabled)
        self.cb_having_op.setEnabled(enabled)
        self.ed_having_val.setEnabled(enabled)

    def _find_col(self, name: str):
        for c in self.columns:
            if c["name"] == name:
                return c
        return None

    def _update_where_operators(self):
        """
        Выбор набора операторов в зависимости от типа столбца.
        """
        self.cb_where_op.clear()
        col_name = self.cb_where_col.currentData()
        if col_name is None:
            # ничего не выбрано
            self.cb_where_op.addItem("=")
            self.cb_where_op.addItem("!=")
            self.cb_where_op.addItem("IS NULL")
            self.cb_where_op.addItem("IS NOT NULL")
            return

        col = self._find_col(col_name)
        cat = col["category"] if col else "other"

        # базовые операторы
        ops = ["=", "!="]

        if cat in ("number", "date"):
            ops += [">", "<", ">=", "<=", "BETWEEN"]
        if cat == "text":
            ops += ["LIKE", "ILIKE", "~", "~*", "!~", "!~*"]
        # для любых типов доступны проверки на NULL
        ops += ["IS NULL", "IS NOT NULL"]

        for op in ops:
            self.cb_where_op.addItem(op)

        # BETWEEN управляет вторым значением
        self.ed_where_val2.setEnabled(self.cb_where_op.currentText() == "BETWEEN")

    # ====== ПОСТРОЕНИЕ И ВЫПОЛНЕНИЕ ЗАПРОСА ======

    def _run_query(self):
        table_name = self.cb_table.currentData()
        if not table_name:
            QMessageBox.warning(self, "Предупреждение", "Выберите таблицу.")
            return

        # SELECT
        use_group = self.chk_use_group.isChecked()
        select_parts = []
        headers = []

        if use_group:
            group_col_name = self.cb_group_col.currentData()
            if group_col_name is None:
                QMessageBox.warning(self, "Предупреждение", "Выберите столбец для группировки.")
                return
            select_parts.append(f"t.\"{group_col_name}\"")
            headers.append(group_col_name)

            agg_func = self.cb_agg_func.currentText()
            agg_col_name = self.cb_agg_col.currentData()
            if agg_func != "(нет)" and agg_col_name is not None:
                agg_expr = f"{agg_func}(t.\"{agg_col_name}\")"
                select_parts.append(f"{agg_expr} AS agg_value")
                headers.append(f"{agg_func}({agg_col_name})")
        else:
            # выводимые столбцы по чекбоксам
            for name, cb in self.col_checks.items():
                if cb.isChecked():
                    select_parts.append(f"t.\"{name}\"")
                    headers.append(name)

            if not select_parts:
                QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один столбец для вывода.")
                return

        query = "SELECT " + ", ".join(select_parts) + f" FROM \"{table_name}\" t"
        params = []
        # WHERE
        where_clauses = []

        col_name = self.cb_where_col.currentData()
        op = self.cb_where_op.currentText()

        if col_name is not None and op:
            col = self._find_col(col_name)
            cat = col["category"] if col else "other"

            v1 = self.ed_where_val1.text().strip()
            v2 = self.ed_where_val2.text().strip()

            if op in ("IS NULL", "IS NOT NULL"):
                where_clauses.append(f"t.\"{col_name}\" {op}")
            elif op == "BETWEEN":
                if not v1 or not v2:
                    QMessageBox.warning(self, "Предупреждение", "Для BETWEEN укажите два значения.")
                    return
                where_clauses.append(f"t.\"{col_name}\" BETWEEN %s AND %s")
                params.extend([v1, v2])
            else:
                if not v1:
                    QMessageBox.warning(self, "Предупреждение", "Укажите значение для условия.")
                    return
                where_clauses.append(f"t.\"{col_name}\" {op} %s")
                params.append(v1)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # GROUP BY / HAVING
        if use_group:
            group_col_name = self.cb_group_col.currentData()
            query += f" GROUP BY t.\"{group_col_name}\""

            agg_func = self.cb_agg_func.currentText()
            having_val = self.ed_having_val.text().strip()
            agg_col_name = self.cb_agg_col.currentData()

            if agg_func != "(нет)" and having_val and agg_col_name is not None:
                agg_expr = f"{agg_func}(t.\"{agg_col_name}\")"
                having_op = self.cb_having_op.currentText()
                query += f" HAVING {agg_expr} {having_op} %s"
                params.append(having_val)

        # ORDER BY
        if self.chk_use_order.isChecked():
            order_col_name = self.cb_order_col.currentData()
            if order_col_name is not None:
                order_dir = "ASC" if self.cb_order_dir.currentText() == "по возрастанию" else "DESC"
                query += f" ORDER BY t.\"{order_col_name}\" {order_dir}"

        # выполнение
        try:
            rows = self.db.run_select(query, tuple(params))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        if not rows:
            QMessageBox.information(self, "Результат", "По заданным условиям данные не найдены.")
            self.parent_window.show_custom_data(headers or ["Нет данных"], [])
            self.accept()
            return

        self.parent_window.show_custom_data(headers, rows)
        self.accept()
