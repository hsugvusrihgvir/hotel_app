from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QPushButton,
    QMessageBox, QHBoxLayout, QGroupBox, QFormLayout,
    QLabel, QComboBox, QLineEdit, QCheckBox,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt, qWarning
from PySide6.QtGui import QStandardItemModel, QStandardItem

from app.ui.filters_window import FilterWindow


class DataWindow(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)  # вызов конструктора родительского класса
        self.setWindowTitle("Данные о бронированиях")  # установка заголовка окна
        self.setModal(True)  # делаем окно модальным (блокирует родительское)
        self.setMinimumSize(900, 500)  # установка минимального размера окна

        # добавление стиля основного окна
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

        self.setup_ui()

        if db is None:
            raise RuntimeError("Ошибка. Нет подключения к БД. Откройте сначала соединение.")
        self.db = db

        self.update_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)  # создание вертикального layout

        # таблица для отображения данных
        self.table_view = QTableView()
        self.model = QStandardItemModel()  # модель данных для таблицы
        self.table_view.setModel(self.model)  # связываем модель с таблицей
        self.table_view.verticalHeader().setVisible(False)  # убираем счёт строк (есть id)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)  # выделение всей строки
        layout.addWidget(self.table_view)  # добавляем таблицу в layout

        # layout для кнопок
        buttons_layout = QHBoxLayout()

        # кнопка обновления данных
        self.btn_update = QPushButton("Обновить")
        self.btn_update.clicked.connect(self.update_table)  # подключение сигнала к слоту

        # кнопка фильтров (простые фильтры по дате/комфорту/оплате)
        self.btn_filter = QPushButton("Фильтры")
        self.btn_filter.clicked.connect(self.filter_button)  # открытие окна с фильтрами

        # кнопка расширенного запроса (SELECT с WHERE/GROUP BY/HAVING/ORDER BY)
        self.btn_advanced = QPushButton("Расширенный запрос…")
        self.btn_advanced.clicked.connect(self.open_advanced_query)

        # кнопка закрытия окна
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)  # подключение сигнала к слоту

        buttons_layout.addWidget(self.btn_update)   # добавление кнопки обновления
        buttons_layout.addWidget(self.btn_filter)   # рядом с "Обновить", фильтры
        buttons_layout.addWidget(self.btn_advanced) # кнопка конструктора запросов
        buttons_layout.addStretch()                 # добавляем растягивающееся пространство
        buttons_layout.addWidget(self.btn_close)    # добавление кнопки закрытия

        layout.addLayout(buttons_layout)  # добавление layout с кнопками в основной layout

    def update_table(self, filter_params=None):
        """Загрузка стандартной сводной таблицы с простыми фильтрами."""
        self.model.clear()  # очистка модели данных
        data = None

        # заголовки столбцов таблицы
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
            data = self.db.load_data(filter_params)
        except RuntimeError:
            # пробрасываем дальше — верхний уровень уже покажет понятное сообщение
            raise

        if not data:  # проверка на наличие данных
            self.model.setHorizontalHeaderLabels(["Нет данных"])  # заголовок если данных нет
            return

        self.model.setHorizontalHeaderLabels(headers)  # установка заголовков

        # заполнение таблицы данными
        for row in data:
            items = [QStandardItem(str(value)) for value in row]  # создание элементов для каждой ячейки
            self.model.appendRow(items)  # добавление строки в модель

        # автоматическое растягивание столбцов под содержимое
        self.table_view.resizeColumnsToContents()

    def show_custom_data(self, headers, rows):
        """
        Показ данных, полученных из расширенного конструктора SELECT.
        Используется AdvancedSelectDialog.
        """
        self.model.clear()

        if not rows:
            self.model.setHorizontalHeaderLabels(["Нет данных"])
            return

        self.model.setHorizontalHeaderLabels(headers)
        for row in rows:
            items = [QStandardItem(str(value)) for value in row]
            self.model.appendRow(items)

        self.table_view.resizeColumnsToContents()

    def filter_button(self):
        """Открытие окна простых фильтров."""
        try:
            filter_window = FilterWindow(self, self.db)  # создается и показывается модальное окно
            filter_window.filterApplied.connect(self.handle_filter)
            filter_window.exec_()  # блок родительского окна до закрытия
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия фильтра: {str(e)}")

    def handle_filter(self, filter_params):
        """Применение фильтрации из окна фильтров."""
        try:
            # обновляем таблицу с учетом фильтрации
            self.update_table(filter_params)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка применения фильтра: {str(e)}")

    def open_advanced_query(self):
        """Открывает модальный конструктор расширенных SELECT-запросов."""
        try:
            dlg = AdvancedSelectDialog(self, self.db)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка открытия расширенного запроса: {str(e)}")


class AdvancedSelectDialog(QDialog):
    """
    Модальное окно для построения расширенного SELECT:
    - выбор столбцов для вывода
    - одно условие WHERE (в т.ч. LIKE / регулярные выражения)
    - ORDER BY
    - GROUP BY + агрегатные функции + HAVING
    Всё без ручного ввода SQL.
    """

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.parent_window: DataWindow = parent
        self.db = db
        if self.db is None:
            raise RuntimeError("Нет подключения к БД.")

        self.setWindowTitle("Расширенный запрос (SELECT)")
        self.setModal(True)
        self.setMinimumSize(800, 600)

        # тёмный стиль в том же духе
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
            QLabel {
                color: #e8e6e3;
            }
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
            QPushButton:hover {
                background: #2b3238;
            }
            QCheckBox {
                spacing: 6px;
            }
        """)

        self._init_mappings()
        self._build_ui()

    def _init_mappings(self):
        """Соответствие логических полей заголовкам и SQL-именам."""
        # колонки из базовой сводной выборки по бронированиям
        self.columns = [
            ("id", "ID", "stay_id"),
            ("client", "Клиент", "client"),
            ("room_number", "Номер", "room_number"),
            ("comfort", "Комфорт", "comfort"),
            ("check_in", "Заезд", "check_in"),
            ("check_out", "Выезд", "check_out"),
            ("paid", "Оплата", "paid"),
            ("status", "Статус", "status"),
        ]

        # базовый подзапрос по всем заселениям
        self.base_subquery = """
            SELECT 
                s.id AS stay_id,
                c.last_name || ' ' || c.first_name || ' ' || COALESCE(c.patronymic, '') AS client,
                r.room_number AS room_number,
                r.comfort AS comfort,
                s.check_in AS check_in,
                s.check_out AS check_out,
                CASE WHEN s.is_paid THEN 'Да' ELSE 'Нет' END AS paid,
                CASE WHEN s.status THEN 'Активно' ELSE 'Завершено' END AS status
            FROM stays s
            JOIN clients c ON s.client_id = c.id
            JOIN rooms   r ON s.room_id   = r.id
        """

    def _build_ui(self):
        # === Основной layout диалога ===
        main_layout = QVBoxLayout(self)

        # === ScrollArea для всего содержимого ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignTop)

        # === 1. Выводимые столбцы ===
        gb_cols = QGroupBox("Выводимые столбцы")
        cols_layout = QVBoxLayout(gb_cols)
        self.col_checks = {}
        for key, title, sql_name in self.columns:
            cb = QCheckBox(title)
            cb.setChecked(True)
            self.col_checks[key] = cb
            cols_layout.addWidget(cb)
        container_layout.addWidget(gb_cols)

        # === 2. WHERE ===
        gb_where = QGroupBox("Условие отбора (WHERE, LIKE, регулярные выражения)")
        where_layout = QFormLayout(gb_where)

        self.cb_where_col = QComboBox()
        self.cb_where_col.addItem("— нет —", None)
        for key, title, sql_name in self.columns:
            self.cb_where_col.addItem(title, key)

        self.cb_where_op = QComboBox()
        self.cb_where_op.addItems([
            "=", "!=", ">", "<", ">=", "<=",
            "BETWEEN",
            "LIKE", "ILIKE",
            "~", "~*", "!~", "!~*"
        ])

        self.ed_where_val1 = QLineEdit()
        self.ed_where_val2 = QLineEdit()
        self.ed_where_val2.setEnabled(False)

        self.cb_where_op.currentTextChanged.connect(self._update_between_state)

        where_layout.addRow("Столбец:", self.cb_where_col)
        where_layout.addRow("Оператор:", self.cb_where_op)
        where_layout.addRow("Значение 1:", self.ed_where_val1)
        where_layout.addRow("Значение 2 (для BETWEEN):", self.ed_where_val2)

        container_layout.addWidget(gb_where)

        # === 3. ORDER BY ===
        gb_order = QGroupBox("Сортировка (ORDER BY)")
        order_layout = QFormLayout(gb_order)

        self.chk_use_order = QCheckBox("Использовать сортировку")
        self.cb_order_col = QComboBox()
        for key, title, sql_name in self.columns:
            self.cb_order_col.addItem(title, key)

        self.cb_order_dir = QComboBox()
        self.cb_order_dir.addItems(["по возрастанию", "по убыванию"])

        order_layout.addRow(self.chk_use_order)
        order_layout.addRow("Столбец:", self.cb_order_col)
        order_layout.addRow("Порядок:", self.cb_order_dir)

        container_layout.addWidget(gb_order)

        # === 4. GROUP BY / HAVING ===
        gb_group = QGroupBox("Группировка и агрегаты (GROUP BY / HAVING)")
        group_layout = QFormLayout(gb_group)

        self.chk_use_group = QCheckBox("Включить группировку")
        self.cb_group_col = QComboBox()
        for key, title, sql_name in self.columns:
            self.cb_group_col.addItem(title, key)

        self.cb_agg_func = QComboBox()
        self.cb_agg_func.addItems(["(нет)", "COUNT", "SUM", "AVG", "MIN", "MAX"])

        self.cb_agg_col = QComboBox()
        for key, title, sql_name in self.columns:
            self.cb_agg_col.addItem(title, key)

        self.cb_having_op = QComboBox()
        self.cb_having_op.addItems([">", ">=", "<", "<=", "=", "!="])

        self.ed_having_val = QLineEdit()

        self._update_group_enabled(False)
        self.chk_use_group.toggled.connect(self._update_group_enabled)

        group_layout.addRow(self.chk_use_group)
        group_layout.addRow("Группировать по:", self.cb_group_col)
        group_layout.addRow("Агрегатная функция:", self.cb_agg_func)
        group_layout.addRow("Колонка для агрегата:", self.cb_agg_col)
        group_layout.addRow("Оператор HAVING:", self.cb_having_op)
        group_layout.addRow("Значение:", self.ed_having_val)

        container_layout.addWidget(gb_group)

        # === Добавляем основной контейнер в Scroll ===
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # === Кнопки снизу ===
        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_run = QPushButton("Выполнить")
        self.btn_cancel = QPushButton("Отмена")
        self.btn_run.clicked.connect(self._run_query)
        self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_run)
        btns.addWidget(self.btn_cancel)

        main_layout.addLayout(btns)

    def _update_between_state(self, op_text: str):
        """Включение/выключение второго значения для BETWEEN."""
        self.ed_where_val2.setEnabled(op_text == "BETWEEN")

    def _update_group_enabled(self, enabled: bool):
        """Включение/выключение элементов группировки."""
        self.cb_group_col.setEnabled(enabled)
        self.cb_agg_func.setEnabled(enabled)
        self.cb_agg_col.setEnabled(enabled)
        self.cb_having_op.setEnabled(enabled)
        self.ed_having_val.setEnabled(enabled)

    def _get_sql_name(self, key: str) -> str:
        for k, title, sql_name in self.columns:
            if k == key:
                return sql_name
        return key

    def _get_title(self, key: str) -> str:
        for k, title, sql_name in self.columns:
            if k == key:
                return title
        return key

    def _run_query(self):
        """Собирает запрос по выбранным настройкам и выполняет его через db.run_select."""
        # --- SELECT ---
        use_group = self.chk_use_group.isChecked()

        select_parts = []
        headers = []

        if use_group:
            # При группировке делаем простой и понятный вывод:
            #   - столбец группировки
            #   - при необходимости агрегат по выбранной колонке
            group_key = self.cb_group_col.currentData()
            group_sql = self._get_sql_name(group_key)
            group_title = self._get_title(group_key)

            select_parts.append(f"t.{group_sql}")
            headers.append(group_title)

            agg_func = self.cb_agg_func.currentText()
            agg_col_key = self.cb_agg_col.currentData()
            agg_col_sql = self._get_sql_name(agg_col_key)
            agg_col_title = self._get_title(agg_col_key)

            agg_expr = None
            agg_header = None

            if agg_func != "(нет)":
                if agg_func == "COUNT":
                    # COUNT всегда допустим, можно считать по любой колонке
                    agg_expr = f"COUNT(t.{agg_col_sql})"
                else:
                    agg_expr = f"{agg_func}(t.{agg_col_sql})"
                agg_header = f"{agg_func}({agg_col_title})"
                select_parts.append(f"{agg_expr} AS agg_value")
                headers.append(agg_header or "Агрегат")
        else:
            # Без группировки используем галочки "Выводимые столбцы"
            for key, cb in self.col_checks.items():
                if cb.isChecked():
                    sql_name = self._get_sql_name(key)
                    select_parts.append(f"t.{sql_name}")
                    headers.append(self._get_title(key))

            if not select_parts:
                QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один столбец для вывода.")
                return

        # --- FROM ---
        query = "SELECT " + ", ".join(select_parts) + " FROM (\n" + self.base_subquery + "\n) t"

        params = []
        where_clauses = []

        # --- WHERE / LIKE / рег. выражения ---
        where_key = self.cb_where_col.currentData()
        if where_key is not None:
            col_sql = self._get_sql_name(where_key)
            op = self.cb_where_op.currentText()
            v1 = self.ed_where_val1.text().strip()
            v2 = self.ed_where_val2.text().strip()

            if not v1:
                QMessageBox.warning(self, "Предупреждение", "Введите значение для условия.")
                return

            if op == "BETWEEN":
                if not v2:
                    QMessageBox.warning(self, "Предупреждение", "Для BETWEEN нужно указать два значения.")
                    return
                where_clauses.append(f"t.{col_sql} BETWEEN %s AND %s")
                params.append(v1)
                params.append(v2)
            else:
                # LIKE / ILIKE / ~ / ~* / !~ / !~* и обычные сравнения
                where_clauses.append(f"t.{col_sql} {op} %s")
                params.append(v1)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # --- GROUP BY / HAVING ---
        if use_group:
            group_key = self.cb_group_col.currentData()
            group_sql = self._get_sql_name(group_key)
            query += f" GROUP BY t.{group_sql}"

            # HAVING по агрегату (если он включён)
            agg_func = self.cb_agg_func.currentText()
            having_val = self.ed_having_val.text().strip()
            if agg_func != "(нет)" and having_val:
                agg_col_key = self.cb_agg_col.currentData()
                agg_col_sql = self._get_sql_name(agg_col_key)

                if agg_func == "COUNT":
                    agg_expr = f"COUNT(t.{agg_col_sql})"
                else:
                    agg_expr = f"{agg_func}(t.{agg_col_sql})"

                having_op = self.cb_having_op.currentText()
                query += f" HAVING {agg_expr} {having_op} %s"
                params.append(having_val)

        # --- ORDER BY ---
        if self.chk_use_order.isChecked():
            order_key = self.cb_order_col.currentData()
            order_sql = self._get_sql_name(order_key)
            order_dir = "ASC" if self.cb_order_dir.currentText() == "по возрастанию" else "DESC"
            query += f" ORDER BY t.{order_sql} {order_dir}"

        # --- Выполнение запроса ---
        try:
            rows = self.db.run_select(query, tuple(params))
        except RuntimeError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return

        if not rows:
            QMessageBox.information(self, "Результат", "По заданным условиям данные не найдены.")
            # всё равно очищаем таблицу и показываем заголовки
            if self.parent_window is not None:
                self.parent_window.show_custom_data(headers or ["Нет данных"], [])
            self.accept()
            return

        # передаём результат в основное окно
        if self.parent_window is not None:
            self.parent_window.show_custom_data(headers, rows)

        self.accept()
