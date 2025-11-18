from typing import Optional, Set, Dict

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QListWidget, QListWidgetItem, QFrame, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from app.log.log import app_logger
from app.ui.collapsible_section import CollapsibleSection


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ВИДЖЕТЫ: WHERE и HAVING
# ============================================================

class WhereBuilderWidget(QWidget):
    """
    Простой конструктор WHERE:
    - выбор колонки
    - оператор (=, <>, >, <, >=, <=, LIKE, ILIKE)
    - значение
    - несколько условий, объединённых AND
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns: list[str] = []
        self.col_types: dict[str, str] = {}
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(5, 5, 5, 5)
        main.setSpacing(6)

        row = QHBoxLayout()
        main.addLayout(row)

        row.addWidget(QLabel("Колонка:"))
        self.cb_column = QComboBox()
        row.addWidget(self.cb_column)

        row.addWidget(QLabel("Оператор:"))
        self.cb_operator = QComboBox()
        self.cb_operator.addItems([
            "=", "<>", ">", "<", ">=", "<=", "LIKE", "ILIKE"
        ])
        row.addWidget(self.cb_operator)

        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Значение")
        row.addWidget(self.value_edit)

        self.btn_add = QPushButton("Добавить условие")
        row.addWidget(self.btn_add)

        self.btn_add.clicked.connect(self._on_add_condition)

        self.conditions_list = QListWidget()
        main.addWidget(self.conditions_list)

        btn_clear = QPushButton("Очистить условия")
        btn_clear.clicked.connect(self.conditions_list.clear)
        main.addWidget(btn_clear)

    # ------------ API -------------

    def set_columns(self, columns: list[str], col_types: dict[str, str]):
        self.columns = list(columns)
        self.col_types = dict(col_types)
        self.cb_column.clear()
        self.cb_column.addItems(self.columns)

    def get_conditions(self) -> list[str]:
        res = []
        for i in range(self.conditions_list.count()):
            res.append(self.conditions_list.item(i).text())
        return res

    # ------------ внутренняя логика -------------

    def _on_add_condition(self):
        col = self.cb_column.currentText()
        op = self.cb_operator.currentText()
        raw_val = self.value_edit.text().strip()

        if not col or not op:
            QMessageBox.warning(self, "Внимание", "Выберите колонку и оператор.")
            return
        if raw_val == "":
            QMessageBox.warning(self, "Внимание", "Введите значение.")
            return

        data_type = self.col_types.get(col, "text").lower()
        try:
            literal = self._format_literal(raw_val, data_type, op)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка значения", str(e))
            return

        self.conditions_list.addItem(f"{col} {op} {literal}")
        self.value_edit.clear()

    def _format_literal(self, raw_val: str, data_type: str, op: str) -> str:
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


class HavingBuilderWidget(QWidget):
    """
    Конструктор HAVING:
    - агр. функция (COUNT/SUM/AVG/MIN/MAX)
    - колонка
    - оператор / значение
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns: list[str] = []
        self.col_types: dict[str, str] = {}
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(5, 5, 5, 5)
        main.setSpacing(6)

        row = QHBoxLayout()
        main.addLayout(row)

        row.addWidget(QLabel("Агрегат:"))
        self.cb_agg = QComboBox()
        self.cb_agg.addItems(["COUNT", "SUM", "AVG", "MIN", "MAX"])
        row.addWidget(self.cb_agg)

        row.addWidget(QLabel("Колонка:"))
        self.cb_column = QComboBox()
        row.addWidget(self.cb_column)

        row.addWidget(QLabel("Оператор:"))
        self.cb_op = QComboBox()
        self.cb_op.addItems(["=", "<>", ">", "<", ">=", "<="])
        row.addWidget(self.cb_op)

        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Значение")
        row.addWidget(self.value_edit)

        self.btn_add = QPushButton("Добавить условие")
        row.addWidget(self.btn_add)
        self.btn_add.clicked.connect(self._on_add_condition)

        self.conditions_list = QListWidget()
        main.addWidget(self.conditions_list)

        btn_clear = QPushButton("Очистить HAVING")
        btn_clear.clicked.connect(self.conditions_list.clear)
        main.addWidget(btn_clear)

    # ------------ API -------------

    def set_columns(self, columns: list[str], col_types: dict[str, str]):
        self.columns = list(columns)
        self.col_types = dict(col_types)
        self.cb_column.clear()
        self.cb_column.addItems(self.columns)

    def get_conditions(self) -> list[str]:
        res = []
        for i in range(self.conditions_list.count()):
            res.append(self.conditions_list.item(i).text())
        return res

    # ------------ внутренняя логика -------------

    def _on_add_condition(self):
        agg = self.cb_agg.currentText()
        col = self.cb_column.currentText()
        op = self.cb_op.currentText()
        raw_val = self.value_edit.text().strip()

        if not agg or not col or not op:
            QMessageBox.warning(self, "Внимание", "Выберите агрегат, колонку и оператор.")
            return
        if raw_val == "":
            QMessageBox.warning(self, "Внимание", "Введите значение.")
            return

        try:
            literal = self._format_literal(raw_val)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка значения", str(e))
            return

        func = f"{agg}({col})"
        self.conditions_list.addItem(f"{func} {op} {literal}")
        self.value_edit.clear()

    def _format_literal(self, raw_val: str) -> str:
        # для HAVING почти всегда нужно число
        try:
            float(raw_val.replace(",", "."))
        except ValueError:
            raise ValueError("Для HAVING обычно сравнивают с числом — укажите число.")
        return raw_val


# ============================================================
# ОСНОВНОЕ ОКНО DataWindow
# ============================================================

class DataWindow(QMainWindow):
    """Окно расширенного SELECT с JOIN, фильтрами, группировками и поиском."""

    def __init__(self, db, join_info, parent=None):
        super().__init__(parent)
        self.db = db
        self.join_info = join_info

        self.setWindowTitle("Расширенный SELECT")
        self.resize(1350, 780)

        # 'table.col' -> data_type
        self.col_types: dict[str, str] = {}
        # alias последней строковой операции
        self.current_string_alias: Optional[str] = None
        # текстовые вычисленные колонки (названия)
        self.string_virtual_columns: Set[str] = set()
        # alias -> SQL-выражение (без "AS alias")
        self.string_virtual_expr: Dict[str, str] = {}

        self._build_ui()
        self._load_data()

    # ---------------------------------------------------------
    # Построение интерфейса
    # ---------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # верх: слева — конструкторы, справа — панель строковых операций
        top_container = QWidget()
        split = QHBoxLayout(top_container)
        split.setContentsMargins(0, 0, 0, 0)
        split.setSpacing(12)

        # ---------- левый блок: скролл с секциями ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        left_widget = QWidget()
        scroll.setWidget(left_widget)

        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        # SELECT
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)

        select_widget = QWidget()
        sl = QVBoxLayout(select_widget)
        sl.addWidget(QLabel("Выберите колонки для SELECT:"))
        sl.addWidget(self.columns_list)

        select_section = CollapsibleSection("SELECT — выбор колонок", select_widget)
        left_layout.addWidget(select_section)

        # WHERE
        self.where_builder = WhereBuilderWidget(self)
        where_section = CollapsibleSection("WHERE — условия отбора", self.where_builder)
        left_layout.addWidget(where_section)

        # Поиск по строкам
        self.search_column = QComboBox()
        self.search_mode = QComboBox()
        self.search_mode.addItems([
            "",
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
        self.btn_apply_search.clicked.connect(self._load_data)

        search_widget = QWidget()
        sh = QHBoxLayout(search_widget)
        sh.addWidget(QLabel("Колонка:"))
        sh.addWidget(self.search_column)
        sh.addWidget(self.search_mode)
        sh.addWidget(self.search_value)
        sh.addWidget(self.btn_apply_search)

        search_section = CollapsibleSection("Поиск по строкам (LIKE / Regex / SIMILAR)", search_widget)
        left_layout.addWidget(search_section)

        # Подзапросы ANY / ALL / EXISTS
        self.sub_left_col = QComboBox()
        self.sub_operator = QComboBox()
        self.sub_operator.addItems(["=", "<>", ">", "<", ">=", "<="])

        self.sub_mode = QComboBox()
        self.sub_mode.addItems(["", "ANY", "ALL", "EXISTS", "NOT EXISTS"])

        self.sub_table = QComboBox()
        self.sub_right_col = QComboBox()
        self.sub_where = QLineEdit()
        self.sub_where.setPlaceholderText("Доп. WHERE для подзапроса (опционально)")

        self.btn_apply_sub = QPushButton("Применить подзапрос")
        self.btn_apply_sub.clicked.connect(self._load_data)

        sub_widget = QWidget()
        sb = QHBoxLayout(sub_widget)
        sb.addWidget(QLabel("Поле слева:"))
        sb.addWidget(self.sub_left_col)
        sb.addWidget(self.sub_operator)
        sb.addWidget(self.sub_mode)
        sb.addWidget(QLabel("Таблица подзапроса:"))
        sb.addWidget(self.sub_table)
        sb.addWidget(self.sub_right_col)
        sb.addWidget(self.sub_where)
        sb.addWidget(self.btn_apply_sub)

        sub_section = CollapsibleSection("Подзапросы ANY / ALL / EXISTS", sub_widget)
        left_layout.addWidget(sub_section)

        # GROUP BY + агрегаты
        self.group_col = QComboBox()
        self.aggregate_func = QComboBox()
        self.aggregate_func.addItems(["", "COUNT", "SUM", "AVG", "MIN", "MAX"])
        self.aggregate_target = QComboBox()

        self.btn_apply_group = QPushButton("Применить GROUP BY")
        self.btn_apply_group.clicked.connect(self._load_data)

        group_widget = QWidget()
        gl = QHBoxLayout(group_widget)
        gl.addWidget(QLabel("GROUP BY:"))
        gl.addWidget(self.group_col)
        gl.addWidget(QLabel("Агрегат:"))
        gl.addWidget(self.aggregate_func)
        gl.addWidget(self.aggregate_target)
        gl.addWidget(self.btn_apply_group)

        group_section = CollapsibleSection("GROUP BY / Агрегаты", group_widget)
        left_layout.addWidget(group_section)

        # HAVING
        self.having_builder = HavingBuilderWidget(self)
        having_section = CollapsibleSection("HAVING — условия по агрегатам", self.having_builder)
        left_layout.addWidget(having_section)

        # ORDER BY
        self.order_col = QComboBox()
        self.order_dir = QComboBox()
        self.order_dir.addItems(["ASC", "DESC"])
        self.btn_apply_order = QPushButton("Применить ORDER BY")
        self.btn_apply_order.clicked.connect(self._load_data)

        order_widget = QWidget()
        ow = QHBoxLayout(order_widget)
        ow.addWidget(QLabel("ORDER BY:"))
        ow.addWidget(self.order_col)
        ow.addWidget(self.order_dir)
        ow.addWidget(self.btn_apply_order)

        order_section = CollapsibleSection("ORDER BY", order_widget)
        left_layout.addWidget(order_section)

        # Обновить
        self.btn_refresh = QPushButton("Обновить данные")
        self.btn_refresh.clicked.connect(self._load_data)
        left_layout.addWidget(self.btn_refresh)

        left_layout.addStretch()

        split.addWidget(scroll, 3)

        # ---------- правый блок: панель строковых операций ----------
        self._build_string_panel(split)

        # ---------- низ: таблица ----------
        main_layout.addWidget(top_container)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        # служебная инфа
        self._load_all_column_lists()
        self._load_column_types()
        self._apply_columns_to_builders()
        self._load_subquery_tables()
        self._load_string_op_columns()

        self._apply_table_style()

    def _apply_table_style(self):
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #111827;
                gridline-color: #374151;
                selection-background-color: #4B5563;
                selection-color: #F9FAFB;
            }
            QHeaderView::section {
                background-color: #020617;
                color: #E5E7EB;
                border: 1px solid #1F2933;
                padding: 4px;
            }
        """)

    # ---------------------------------------------------------
    # Панель строковых операций (справа)
    # ---------------------------------------------------------

    def _build_string_panel(self, parent_layout: QHBoxLayout):
        panel = QFrame()
        panel.setObjectName("StringOpsPanel")
        panel.setMinimumWidth(360)
        panel.setMaximumWidth(420)

        v = QVBoxLayout(panel)
        v.setContentsMargins(14, 14, 14, 14)
        v.setSpacing(8)

        title = QLabel("Строковые операции")
        title.setObjectName("StringOpsHeader")

        hint = QLabel(
            "Получить новый столбец на основе текста:\n"
            "сделать все буквы заглавными, вырезать подстроку,\n"
            "склеить несколько полей и т.д."
        )
        hint.setWordWrap(True)
        hint.setObjectName("StringOpsHint")

        v.addWidget(title)
        v.addWidget(hint)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        v.addWidget(line)

        # 1. выбор колонки
        self.str_col = QComboBox()
        block_col = QWidget()
        bcl = QVBoxLayout(block_col)
        bcl.setContentsMargins(0, 0, 0, 0)
        bcl.setSpacing(4)
        lbl_col = QLabel("1. Колонка с текстом (исходная или вычисленная)")
        lbl_col.setObjectName("StringOpsSmall")
        bcl.addWidget(lbl_col)
        bcl.addWidget(self.str_col)
        v.addWidget(block_col)

        # 2. выбор операции
        self.str_op = QComboBox()
        self.str_op.addItems([
            "",
            "UPPER",
            "LOWER",
            "SUBSTRING",
            "TRIM",
            "LPAD",
            "RPAD",
            "CONCAT",
        ])

        block_op = QWidget()
        bol = QVBoxLayout(block_op)
        bol.setContentsMargins(0, 0, 0, 0)
        bol.setSpacing(4)
        lbl_op = QLabel("2. Операция над строкой")
        lbl_op.setObjectName("StringOpsSmall")
        bol.addWidget(lbl_op)
        bol.addWidget(self.str_op)
        v.addWidget(block_op)

        # 3. вторая колонка (только для CONCAT)
        self.str_second_col = QComboBox()
        self.str_second_row = QWidget()
        s2l = QVBoxLayout(self.str_second_row)
        s2l.setContentsMargins(0, 0, 0, 0)
        s2l.setSpacing(4)
        lbl_second = QLabel("Дополнительно: вторая колонка (для склейки строк)")
        lbl_second.setObjectName("StringOpsSmall")
        s2l.addWidget(lbl_second)
        s2l.addWidget(self.str_second_col)
        v.addWidget(self.str_second_row)

        # 4. параметры
        self.str_param1 = QLineEdit()
        self.str_param2 = QLineEdit()

        self.str_param1_row = QWidget()
        p1l = QVBoxLayout(self.str_param1_row)
        p1l.setContentsMargins(0, 0, 0, 0)
        p1l.setSpacing(4)
        self.str_param1_label = QLabel()
        self.str_param1_label.setObjectName("StringOpsSmall")
        p1l.addWidget(self.str_param1_label)
        p1l.addWidget(self.str_param1)
        v.addWidget(self.str_param1_row)

        self.str_param2_row = QWidget()
        p2l = QVBoxLayout(self.str_param2_row)
        p2l.setContentsMargins(0, 0, 0, 0)
        p2l.setSpacing(4)
        self.str_param2_label = QLabel()
        self.str_param2_label.setObjectName("StringOpsSmall")
        p2l.addWidget(self.str_param2_label)
        p2l.addWidget(self.str_param2)
        v.addWidget(self.str_param2_row)

        # Кнопка
        self.btn_apply_str = QPushButton("Применить к данным")
        self.btn_apply_str.clicked.connect(self._load_data)
        v.addWidget(self.btn_apply_str)

        self.str_help = QLabel()
        self.str_help.setWordWrap(True)
        self.str_help.setObjectName("StringOpsHint")
        v.addWidget(self.str_help)

        v.addStretch()

        panel.setStyleSheet("""
            QFrame#StringOpsPanel {
                background-color: #020617;
                border: 1px solid #1F2937;
                border-radius: 10px;
            }
            QLabel#StringOpsHeader {
                font-weight: 600;
                font-size: 14px;
                color: #E5E7EB;
            }
            QLabel#StringOpsHint {
                color: #9CA3AF;
                font-size: 11px;
            }
            QLabel#StringOpsSmall {
                color: #9CA3AF;
                font-size: 11px;
            }
            QComboBox, QLineEdit {
                background-color: #020617;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 3px 6px;
                color: #E5E7EB;
            }
            QPushButton {
                background-color: #374151;
                border-radius: 6px;
                padding: 5px 10px;
                color: #F9FAFB;
            }
            QPushButton:hover {
                background-color: #4B5563;
            }
        """)

        self.str_op.currentTextChanged.connect(self._on_string_op_changed)
        self._on_string_op_changed()

        parent_layout.addWidget(panel, 2)

    def _on_string_op_changed(self):
        """Обновляем подсказки и видимость полей под выбранную операцию."""
        op = (self.str_op.currentText() or "").upper()

        self.str_second_row.setVisible(False)
        self.str_param1_row.setVisible(False)
        self.str_param2_row.setVisible(False)

        help_text = "Выберите операцию — ниже появится краткое описание."

        if op == "UPPER":
            help_text = "UPPER: переводит текст в ВЕРХНИЙ регистр — 'abc' → 'ABC'."
        elif op == "LOWER":
            help_text = "LOWER: переводит текст в нижний регистр — 'ABC' → 'abc'."
        elif op == "TRIM":
            help_text = "TRIM: убирает пробелы по краям строки — '  х  ' → 'х'."
        elif op == "SUBSTRING":
            help_text = (
                "SUBSTRING: берёт кусочек строки. "
                "param1 — позиция начала (с 1), param2 — длина подстроки."
            )
            self.str_param1_row.setVisible(True)
            self.str_param1_label.setText("param1: с какой позиции начать (целое число)")
            self.str_param2_row.setVisible(True)
            self.str_param2_label.setText("param2: сколько символов взять (целое число)")
        elif op in ("LPAD", "RPAD"):
            help_text = (
                f"{op}: дополняет строку до нужной длины. "
                "param1 — длина, param2 — символ/строка для заполнения."
            )
            self.str_param1_row.setVisible(True)
            self.str_param1_label.setText("param1: длина итоговой строки (целое число)")
            self.str_param2_row.setVisible(True)
            self.str_param2_label.setText("param2: чем дополнять (например '0')")
        elif op == "CONCAT":
            help_text = (
                "CONCAT: склеивает две колонки в одну строку. "
                "Выберите вторую колонку, param1 — разделитель (по умолчанию пробел)."
            )
            self.str_second_row.setVisible(True)
            self.str_param1_row.setVisible(True)
            self.str_param1_label.setText("param1: разделитель между значениями (можно оставить пустым)")

        self.str_help.setText(help_text)

    # ---------------------------------------------------------
    # Загрузка инфы о колонках
    # ---------------------------------------------------------

    def _load_all_column_lists(self):
        all_cols = list(self.join_info.get("selected_columns", []))

        self.columns_list.clear()
        for c in all_cols:
            item = QListWidgetItem(c)
            item.setCheckState(Qt.Checked)
            self.columns_list.addItem(item)

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

    def _load_column_types(self):
        self.col_types.clear()
        tables = {self.join_info["table1"], self.join_info["table2"]}

        for table in tables:
            try:
                q = """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s;
                """
                with self.db.cursor() as cur:
                    cur.execute(q, (table,))
                    cols = cur.fetchall()
            except Exception as e:
                app_logger.error(f"Ошибка получения типов для {table}: {e}")
                continue

            for col in cols:
                full_name = f"{table}.{col['column_name']}"
                dt = col.get("data_type", "text")
                self.col_types[full_name] = dt

    def _apply_columns_to_builders(self):
        all_cols = list(self.join_info.get("selected_columns", []))
        self.where_builder.set_columns(all_cols, self.col_types)
        self.having_builder.set_columns(all_cols, self.col_types)

    def _load_string_op_columns(self):
        """Текстовые исходные колонки + вычисленные alias'ы для строковых операций."""
        all_cols = list(self.join_info.get("selected_columns", []))

        self.str_col.clear()
        self.str_second_col.clear()

        text_cols: list[str] = []
        for full_name in all_cols:
            dt = self.col_types.get(full_name, "").lower()
            if any(x in dt for x in ("character", "varchar", "text", "char")):
                text_cols.append(full_name)

        virtual_cols = sorted(self.string_virtual_columns)

        if not text_cols and not virtual_cols:
            return

        combined = text_cols + virtual_cols

        self.str_col.addItems(combined)
        self.str_second_col.addItem("")
        self.str_second_col.addItems(combined)

    # ---------------------------------------------------------
    # Подзапросы: таблицы и их колонки
    # ---------------------------------------------------------

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

        self.sub_table.clear()
        self.sub_table.addItems(tables)
        self.sub_table.currentTextChanged.connect(self._load_subquery_columns)
        self._load_subquery_columns()

    def _load_subquery_columns(self):
        table = self.sub_table.currentText()
        if not table:
            return

        q = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """
        with self.db.cursor() as cur:
            cur.execute(q, (table,))
            cols = [r["column_name"] for r in cur.fetchall()]

        self.sub_right_col.clear()
        self.sub_right_col.addItems(cols)

    # ---------------------------------------------------------
    # Строковые выражения для SELECT
    # ---------------------------------------------------------

    def _build_string_expr(self) -> Optional[str]:
        """
        Строит выражение для строковой операции, если она выбрана.
        Важный момент: если выбран alias (виртуальная колонка),
        берём его сохранённое выражение, а не имя alias в SQL.
        """
        self.current_string_alias = None

        op = (self.str_op.currentText() or "").strip().upper()
        col = (self.str_col.currentText() or "").strip()

        if not op or not col:
            return None

        def esc_text(s: str) -> str:
            return s.replace("'", "''")

        # исходное выражение для выбранного "столбца"
        if col in self.string_virtual_expr:
            source_expr = self.string_virtual_expr[col]  # уже выражение, без alias
        else:
            source_expr = col  # обычное table.col

        base_name = col.split(".")[-1]
        alias = f"{base_name}_{op.lower()}"

        # считаем, что результат строковой операции — всегда text
        self.current_string_alias = alias
        self.string_virtual_columns.add(alias)

        col_text = f"({source_expr})::text"

        # собираем "core" выражение (без AS alias)
        if op == "UPPER":
            expr_core = f"UPPER({col_text})"

        elif op == "LOWER":
            expr_core = f"LOWER({col_text})"

        elif op == "TRIM":
            expr_core = f"TRIM({col_text})"

        elif op == "SUBSTRING":
            p1 = (self.str_param1.text() or "").strip()
            p2 = (self.str_param2.text() or "").strip()
            if not p1 or not p2:
                raise ValueError("Для SUBSTRING укажите начало и длину (оба целые числа).")
            try:
                start = int(p1)
                length = int(p2)
            except ValueError:
                raise ValueError("Для SUBSTRING начало и длина должны быть целыми числами.")
            expr_core = f"SUBSTRING({col_text} FROM {start} FOR {length})"

        elif op in ("LPAD", "RPAD"):
            p1 = (self.str_param1.text() or "").strip()
            fill = self.str_param2.text() or ""
            if not p1 or not fill:
                raise ValueError("Для LPAD/RPAD укажите длину и символ заполнения.")
            try:
                length = int(p1)
            except ValueError:
                raise ValueError("Длина для LPAD/RPAD должна быть целым числом.")
            fill_esc = esc_text(fill)
            expr_core = f"{op}({col_text}, {length}, '{fill_esc}')"

        elif op == "CONCAT":
            second = (self.str_second_col.currentText() or "").strip()
            if not second:
                raise ValueError("Для CONCAT выберите вторую колонку.")
            if second in self.string_virtual_expr:
                second_source = self.string_virtual_expr[second]
            else:
                second_source = second
            sep = self.str_param1.text() or " "
            sep_esc = esc_text(sep)
            second_text = f"({second_source})::text"
            expr_core = f"({col_text} || '{sep_esc}' || {second_text})"

        else:
            self.current_string_alias = None
            return None

        # сохраняем выражение для alias, чтобы потом можно было цеплять ещё операции
        self.string_virtual_expr[alias] = expr_core

        # чтобы можно было сортировать по новому столбцу
        if self.current_string_alias and self.order_col.findText(self.current_string_alias) == -1:
            self.order_col.addItem(self.current_string_alias)

        # возвращаем уже с alias
        return f"{expr_core} AS {alias}"

    # ---------------------------------------------------------
    # SQL builder
    # ---------------------------------------------------------

    def _build_sql(self) -> str:
        info = self.join_info
        all_cols = info.get("selected_columns", [])

        checked = []
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())

        if checked:
            cols = ", ".join(checked)
        else:
            cols = ", ".join(all_cols) if all_cols else "*"

        # строковая операция (если есть) — добавляем как вычисленный столбец
        str_expr = self._build_string_expr()
        if str_expr and not (self.aggregate_func.currentText() and self.aggregate_target.currentText()):
            cols = f"{cols}, {str_expr}" if cols.strip() else str_expr

        # агрегат (если указан) перекрывает обычный SELECT
        if self.aggregate_func.currentText() and self.aggregate_target.currentText():
            func = self.aggregate_func.currentText()
            target = self.aggregate_target.currentText()
            cols = f"{func}({target}) AS agg_value"

        q = (
            f"SELECT {cols} "
            f"FROM {info['table1']} {info['join_type']} JOIN {info['table2']} "
            f"ON {info['table1']}.{info['col1']} = {info['table2']}.{info['col2']}"
        )

        where_clauses = []

        # WHERE из конструктора
        where_clauses.extend(self.where_builder.get_conditions())

        # поиск
        if self.search_value.text().strip():
            col = self.search_column.currentText()
            mode = self.search_mode.currentText()
            val = self.search_value.text().strip()
            esc = val.replace("'", "''")

            if mode in ("LIKE", "ILIKE"):
                if "%" not in esc and "_" not in esc:
                    esc = f"%{esc}%"
                cond = f"{col} {mode} '{esc}'"
            elif mode in ("~", "~*", "!~", "!~*"):
                cond = f"{col} {mode} '{esc}'"
            elif mode == "SIMILAR TO":
                cond = f"{col} SIMILAR TO '{esc}'"
            elif mode == "NOT SIMILAR TO":
                cond = f"{col} NOT SIMILAR TO '{esc}'"
            else:
                cond = f"{col} LIKE '{esc}'"

            where_clauses.append(cond)

        # подзапрос
        mode = self.sub_mode.currentText()
        if mode:
            left = self.sub_left_col.currentText()
            right_col = self.sub_right_col.currentText()
            table = self.sub_table.currentText()
            op = self.sub_operator.currentText()

            sub_sql = f"(SELECT {right_col} FROM {table}"
            if self.sub_where.text().strip():
                sub_sql += f" WHERE {self.sub_where.text().strip()}"
            sub_sql += ")"

            if mode == "EXISTS":
                cond = f"EXISTS {sub_sql}"
            elif mode == "NOT EXISTS":
                cond = f"NOT EXISTS {sub_sql}"
            elif mode in ("ANY", "ALL"):
                cond = f"{left} {op} {mode} {sub_sql}"
            else:
                cond = ""

            if cond:
                where_clauses.append(cond)

        if where_clauses:
            q += " WHERE " + " AND ".join(where_clauses)

        # GROUP BY
        group_by = self.group_col.currentText().strip()
        if group_by:
            q += f" GROUP BY {group_by}"

        # HAVING
        having_clauses = self.having_builder.get_conditions()
        if having_clauses:
            q += " HAVING " + " AND ".join(having_clauses)

        # ORDER BY
        order_col = self.order_col.currentText().strip()
        if order_col:
            q += f" ORDER BY {order_col} {self.order_dir.currentText().strip()}"

        return q + ";"

    # ---------------------------------------------------------
    # Подсветка вычисленного столбца
    # ---------------------------------------------------------

    def _highlight_string_column(self):
        alias = self.current_string_alias
        if not alias:
            return

        col_index = -1
        for c in range(self.table.columnCount()):
            header_item = self.table.horizontalHeaderItem(c)
            if header_item and header_item.text() == alias:
                col_index = c
                break

        if col_index == -1:
            return

        # спокойный, но заметный цвет для нового столбца
        highlight_bg = QColor("#064e3b")   # тёмно-зелёный
        header_bg = QColor("#047857")      # чуть ярче для заголовка

        for r in range(self.table.rowCount()):
            item = self.table.item(r, col_index)
            if not item:
                item = QTableWidgetItem("")
                self.table.setItem(r, col_index, item)
            item.setBackground(highlight_bg)

        header_item = self.table.horizontalHeaderItem(col_index)
        if header_item:
            header_item.setBackground(header_bg)
            f = header_item.font()
            f.setBold(True)
            header_item.setFont(f)

    # ---------------------------------------------------------
    # Загрузка и отображение данных
    # ---------------------------------------------------------

    def _load_data(self):
        try:
            sql = self._build_sql()
            app_logger.info(f"DataWindow SQL: {sql}")

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

            # подсветка нового столбца и обновление правой панели
            self._highlight_string_column()
            self._load_string_op_columns()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения запроса:\n{e}")
            app_logger.error(f"DataWindow SQL error: {e}")
