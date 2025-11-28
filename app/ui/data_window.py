from typing import Optional, Set, Dict
import re

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QHeaderView,
    QTabWidget, QInputDialog, QDialog,
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QColor, QRegularExpressionValidator

from app.log.log import app_logger
from app.ui.collapsible_section import CollapsibleSection
from app.ui.cte_storage import GLOBAL_SAVED_CTES

import re


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
        # 'table.col' -> data_type
        self.col_types: dict[str, str] = {}
        self.columns: list[str] = []

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

        buttons_row = QHBoxLayout()
        btn_delete = QPushButton("Удалить выбранное")
        btn_clear = QPushButton("Очистить все")
        buttons_row.addWidget(btn_delete)
        buttons_row.addWidget(btn_clear)
        buttons_row.addStretch()
        main.addLayout(buttons_row)

        btn_delete.clicked.connect(self._delete_selected)
        btn_clear.clicked.connect(self.conditions_list.clear)

        # двойной клик по условию — тоже удаляет его
        self.conditions_list.itemDoubleClicked.connect(self._on_item_double_clicked)

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
        col = self.cb_column.currentText().strip()
        op = self.cb_operator.currentText().strip()
        raw_val = self.value_edit.text().strip()

        if not col or not op:
            QMessageBox.warning(self, "Внимание", "Выберите колонку и оператор.")
            return

        if raw_val == "":
            QMessageBox.warning(self, "Внимание", "Введите значение.")
            return

        data_type = self.col_types.get(col, "").lower()

        # группы типов для простых проверок
        numeric_like = ("smallint", "integer", "bigint", "numeric", "real", "double")
        bool_like = ("boolean",)
        date_like = ("date", "timestamp", "timestamp with time zone", "time")

        # страховка: не даём LIKE/ILIKE по числам, датам и bool,
        # даже если вдруг оператор как-то сюда попал
        if op in ("LIKE", "ILIKE") and (
                any(t in data_type for t in numeric_like)
                or any(t in data_type for t in bool_like)
                or any(t in data_type for t in date_like)
        ):
            QMessageBox.warning(
                self,
                "Недопустимый оператор",
                "Для этого типа столбца оператор LIKE/ILIKE не используется.\n"
                "Выберите другой оператор (например, =, <, > и т.п.).",
            )
            return

        try:
            literal = self._format_literal(raw_val, data_type, op)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка значения", str(e))
            return

        # здесь никакого CAST и прочей магии — ровно то, что выбрал пользователь
        self.conditions_list.addItem(f"{col} {op} {literal}")
        self.value_edit.clear()

    def _delete_selected(self):
        """Удалить выбранные условия из списка."""
        for item in self.conditions_list.selectedItems():
            row = self.conditions_list.row(item)
            self.conditions_list.takeItem(row)

    def _on_item_double_clicked(self, item):
        """Двойной клик по условию — удаление одной строки."""
        row = self.conditions_list.row(item)
        self.conditions_list.takeItem(row)

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

    def build_where_sql(self) -> str:
        """
        Собирает все условия в одну строку через AND.
        Нужно и для DataWindow (если захочешь), и для CTE-конструктора.
        """
        conditions = self.get_conditions()
        if not conditions:
            return ""
        return " AND ".join(conditions)


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

        # при смене колонки — пересобираем список допустимых операторов
        self.cb_column.currentIndexChanged.connect(self._update_operators_for_column)

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
        # сразу подстроить операторы под первый столбец
        self._update_operators_for_column()

    def get_conditions(self) -> list[str]:
        res = []
        for i in range(self.conditions_list.count()):
            res.append(self.conditions_list.item(i).text())
        return res

    def build_having_sql(self) -> str:
        """
        То же самое, что get_conditions, но сразу одной строкой для HAVING.
        Нужен CTE-конструктору.
        """
        conditions = self.get_conditions()
        if not conditions:
            return ""
        return " AND ".join(conditions)

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

        # ------------ внутренняя логика -------------

    def _update_operators_for_column(self):
        """
        Для HAVING оставляем только числовые сравнения.
        Операторы не зависят от типа колонки, агрегаты всё равно дают число.
        """
        current = self.cb_op.currentText()

        ops = ["=", "<>", ">", "<", ">=", "<="]

        self.cb_op.blockSignals(True)
        self.cb_op.clear()
        self.cb_op.addItems(ops)

        # если старый оператор ещё допустим — вернём его
        idx = self.cb_op.findText(current)
        if idx >= 0:
            self.cb_op.setCurrentIndex(idx)

        self.cb_op.blockSignals(False)

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

        # панель сохранения запроса (VIEW / MATERIALIZED VIEW / CTE)
        save_panel = QWidget()
        save_layout = QHBoxLayout(save_panel)
        save_layout.setContentsMargins(8, 8, 8, 8)
        save_layout.setSpacing(10)

        lbl_save = QLabel("Сохранить текущий SELECT как:")
        lbl_save.setStyleSheet("color: #e5e7eb; font-weight: 600;")

        self.btn_save_view = QPushButton("VIEW")
        self.btn_save_mat_view = QPushButton("MATERIALIZED VIEW")
        self.btn_save_cte = QPushButton("CTE")

        for btn in (self.btn_save_view, self.btn_save_mat_view, self.btn_save_cte):
            btn.setMinimumHeight(32)
            btn.setStyleSheet(
                "QPushButton {"
                "  background-color: #4b5563;"
                "  color: #e5e7eb;"
                "  padding: 6px 12px;"
                "  border-radius: 6px;"
                "  font-weight: 600;"
                "}"
                "QPushButton:hover {"
                "  background-color: #6b7280;"
                "}"
            )

        save_layout.addWidget(lbl_save)
        save_layout.addWidget(self.btn_save_view)
        save_layout.addWidget(self.btn_save_mat_view)
        save_layout.addWidget(self.btn_save_cte)
        save_layout.addStretch()

        main_layout.addWidget(save_panel)

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
        left_layout.setSpacing(10)

        # --- табы с инструментами SELECT ---
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet("""
                    QTabWidget::pane {
                        border: 1px solid #374151;
                    }
                    QTabBar::tab {
                        background-color: #020617;
                        color: #E5E7EB;
                        padding: 6px 10px;
                        margin-right: 2px;
                    }
                    QTabBar::tab:selected {
                        background-color: #111827;
                    }
                """)

        # ===== Вкладка 1: ФИЛЬТРЫ =====
        filters_tab = QWidget()
        filters_layout = QVBoxLayout(filters_tab)
        filters_layout.setContentsMargins(6, 6, 6, 6)
        filters_layout.setSpacing(6)

        # SELECT
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)

        select_widget = QWidget()
        sl = QVBoxLayout(select_widget)
        sl.addWidget(QLabel("Выберите колонки для SELECT:"))
        sl.addWidget(self.columns_list)

        select_section = CollapsibleSection("SELECT — выбор колонок", select_widget)
        filters_layout.addWidget(select_section)

        # WHERE
        self.where_builder = WhereBuilderWidget(self)
        where_section = CollapsibleSection("WHERE — условия отбора", self.where_builder)
        filters_layout.addWidget(where_section)

        # Поиск по строкам
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
        self.btn_apply_search.clicked.connect(self._load_data)

        search_widget = QWidget()
        sh = QHBoxLayout(search_widget)
        sh.addWidget(QLabel("Колонка:"))
        sh.addWidget(self.search_column)
        sh.addWidget(self.search_mode)
        sh.addWidget(self.search_value)
        sh.addWidget(self.btn_apply_search)

        search_section = CollapsibleSection("Поиск по строкам (LIKE / Regex / SIMILAR)", search_widget)
        filters_layout.addWidget(search_section)

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
        sb.addWidget(QLabel("Поле:"))
        sb.addWidget(self.sub_left_col)
        sb.addWidget(self.sub_operator)
        sb.addWidget(self.sub_mode)
        sb.addWidget(QLabel("Таблица:"))
        sb.addWidget(self.sub_table)
        sb.addWidget(self.sub_right_col)
        sb.addWidget(self.sub_where)
        sb.addWidget(self.btn_apply_sub)

        sub_section = CollapsibleSection("Подзапросы ANY / ALL / EXISTS", sub_widget)
        filters_layout.addWidget(sub_section)

        filters_layout.addStretch()

        # ===== Вкладка 2: АГРЕГАЦИЯ =====
        agg_tab = QWidget()
        agg_layout = QVBoxLayout(agg_tab)
        agg_layout.setContentsMargins(6, 6, 6, 6)
        agg_layout.setSpacing(6)

        # GROUP BY + агрегаты (включая ROLLUP / CUBE / GROUPING SETS)

        # режим группировки
        self.group_mode = QComboBox()
        self.group_mode.addItem("Нет", userData="none")
        self.group_mode.addItem("Обычный GROUP BY", userData="plain")
        self.group_mode.addItem("ROLLUP", userData="rollup")
        self.group_mode.addItem("CUBE", userData="cube")
        self.group_mode.addItem("GROUPING SETS", userData="grouping_sets")

        # до трёх уровней группировки
        self.group_col = QComboBox()
        self.group_col2 = QComboBox()
        self.group_col3 = QComboBox()

        # агрегат
        self.aggregate_func = QComboBox()
        self.aggregate_func.addItems(["", "COUNT", "SUM", "AVG", "MIN", "MAX"])
        self.aggregate_target = QComboBox()

        self.btn_apply_group = QPushButton("Применить группировку")
        self.btn_apply_group.clicked.connect(self._load_data)

        # когда меняются режим/колонки/агрегат – обновляем допустимые ORDER BY
        self.group_mode.currentIndexChanged.connect(self._update_order_choices)
        self.group_col.currentIndexChanged.connect(self._update_order_choices)
        self.group_col2.currentIndexChanged.connect(self._update_order_choices)
        self.group_col3.currentIndexChanged.connect(self._update_order_choices)
        self.aggregate_func.currentIndexChanged.connect(self._update_order_choices)
        self.aggregate_target.currentIndexChanged.connect(self._update_order_choices)

        group_widget = QWidget()
        gw_layout = QVBoxLayout(group_widget)
        gw_layout.setContentsMargins(0, 0, 0, 0)
        gw_layout.setSpacing(4)

        # строка 1 — режим
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Режим:"))
        mode_row.addWidget(self.group_mode)
        mode_row.addStretch()

        # строка 2 — уровни группировки
        cols_row = QHBoxLayout()
        cols_row.addWidget(QLabel("Уровни группировки:"))
        cols_row.addWidget(self.group_col)
        cols_row.addWidget(self.group_col2)
        cols_row.addWidget(self.group_col3)

        # строка 3 — агрегат
        agg_row = QHBoxLayout()
        agg_row.addWidget(QLabel("Агрегат:"))
        agg_row.addWidget(self.aggregate_func)
        agg_row.addWidget(self.aggregate_target)
        agg_row.addWidget(self.btn_apply_group)

        gw_layout.addLayout(mode_row)
        gw_layout.addLayout(cols_row)
        gw_layout.addLayout(agg_row)

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
        self.btn_apply_order.clicked.connect(self._load_data)

        order_widget = QWidget()
        ow = QHBoxLayout(order_widget)
        ow.addWidget(QLabel("ORDER BY:"))
        ow.addWidget(self.order_col)
        ow.addWidget(self.order_dir)
        ow.addWidget(self.btn_apply_order)

        order_section = CollapsibleSection("ORDER BY", order_widget)
        agg_layout.addWidget(order_section)

        agg_layout.addStretch()

        # ===== Вкладка 3: CASE / NULL =====
        case_tab = QWidget()
        case_layout = QVBoxLayout(case_tab)
        case_layout.setContentsMargins(6, 6, 6, 6)
        case_layout.setSpacing(6)

        self._build_case_null_section(case_layout)
        case_layout.addStretch()

        # Добавляем вкладки в таб-виджет
        tabs.addTab(filters_tab, "Фильтры")
        tabs.addTab(agg_tab, "Агрегация")
        tabs.addTab(case_tab, "CASE / NULL")

        left_layout.addWidget(tabs)

        # Кнопка обновления под табами
        self.btn_refresh = QPushButton("Обновить данные")
        self.btn_refresh.clicked.connect(self._load_data)
        left_layout.addWidget(self.btn_refresh, alignment=Qt.AlignRight)

        split.addWidget(scroll, 3)

        # ---------- правый блок: панель строковых операций ----------
        self._build_string_panel(split)

        # ---------- низ: таблица + поиск по результату ----------
        main_layout.addWidget(top_container)

        # строка поиска по уже полученной таблице
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Поиск по результату:"))

        self.result_search_column = QComboBox()
        search_row.addWidget(self.result_search_column)

        self.result_search_edit = QLineEdit()
        self.result_search_edit.setPlaceholderText("Введите текст для фильтрации")
        search_row.addWidget(self.result_search_edit)

        # фильтрация при вводе и смене колонки
        self.result_search_edit.textChanged.connect(self._apply_result_filter)
        self.result_search_column.currentIndexChanged.connect(self._apply_result_filter)

        main_layout.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        # нормальные размеры колонок + горизонтальный скролл
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)  # можно руками тянуть

        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        main_layout.addWidget(self.table)


        # служебная инфа
        self._load_all_column_lists()
        self._load_column_types()
        self._apply_columns_to_builders()
        self._apply_columns_to_case_null()  # <-- ДОБАВЬ ЭТО
        self._load_subquery_tables()
        self._load_string_op_columns()

        self._apply_table_style()

        # сохранение запроса как VIEW / MATERIALIZED VIEW / CTE
        self.btn_save_view.clicked.connect(self._save_as_view)
        self.btn_save_mat_view.clicked.connect(self._save_as_mat_view)
        self.btn_save_cte.clicked.connect(self._save_as_cte)

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

    def _update_result_search_columns(self):
        """Обновляет список колонок для фильтрации по результату."""
        if not hasattr(self, "result_search_column"):
            return

        self.result_search_column.blockSignals(True)
        self.result_search_column.clear()

        headers = []
        for c in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(c)
            if item:
                headers.append(item.text())

        if headers:
            self.result_search_column.addItems(headers)

        self.result_search_column.blockSignals(False)

    def _apply_result_filter(self):
        """Фильтр по подстроке внутри выбранной колонки (кейс-инсенситив)."""
        if not hasattr(self, "result_search_edit") or self.table.rowCount() == 0:
            return

        text = self.result_search_edit.text().strip().lower()
        col_name = self.result_search_column.currentText() if hasattr(self, "result_search_column") else ""

        # если строка пустая — показываем всё
        if not text or not col_name:
            for r in range(self.table.rowCount()):
                self.table.setRowHidden(r, False)
            return

        # ищем индекс выбранной колонки
        col_idx = -1
        for c in range(self.table.columnCount()):
            item = self.table.horizontalHeaderItem(c)
            if item and item.text() == col_name:
                col_idx = c
                break

        if col_idx == -1:
            return

        # прячем строки, где нет подстроки
        for r in range(self.table.rowCount()):
            item = self.table.item(r, col_idx)
            value = item.text().lower() if item else ""
            self.table.setRowHidden(r, text not in value)

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



    def _build_case_null_section(self, parent_layout: QVBoxLayout):
        """Секция 'CASE / Работа с NULL' в левой панели."""

        from PySide6.QtWidgets import QGridLayout  # локально, чтобы не плодить импорт сверху

        wrapper = QWidget()
        grid = QGridLayout(wrapper)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)

        row = 0

        # ---------- CASE ----------
        title_case = QLabel("CASE — вычисляемый столбец")
        title_case.setStyleSheet("color:#9CA3AF; font-size:11px;")
        grid.addWidget(title_case, row, 0, 1, 4)
        row += 1

        grid.addWidget(QLabel("Колонка:"), row, 0)
        self.case_col = QComboBox()
        grid.addWidget(self.case_col, row, 1, 1, 3)
        row += 1

        grid.addWidget(QLabel("Оператор:"), row, 0)
        self.case_op = QComboBox()
        self.case_op.addItems(["=", "<>", ">", "<", ">=", "<=", "BETWEEN"])
        grid.addWidget(self.case_op, row, 1)

        grid.addWidget(QLabel("Значение 1:"), row, 2)
        self.case_value1 = QLineEdit()
        grid.addWidget(self.case_value1, row, 3)
        row += 1

        grid.addWidget(QLabel("Значение 2 (для BETWEEN):"), row, 0, 1, 2)
        self.case_value2 = QLineEdit()
        grid.addWidget(self.case_value2, row, 2, 1, 2)
        row += 1

        grid.addWidget(QLabel("THEN:"), row, 0)
        self.case_then = QLineEdit()
        grid.addWidget(self.case_then, row, 1, 1, 3)
        row += 1

        grid.addWidget(QLabel("ELSE (опционально):"), row, 0)
        self.case_else = QLineEdit()
        grid.addWidget(self.case_else, row, 1, 1, 3)
        row += 1

        grid.addWidget(QLabel("Alias:"), row, 0)
        self.case_alias = QLineEdit()
        self.case_alias.setPlaceholderText("например: price_case")
        grid.addWidget(self.case_alias, row, 1, 1, 2)
        self.btn_apply_case = QPushButton("Применить CASE")
        self.btn_apply_case.clicked.connect(self._load_data)
        grid.addWidget(self.btn_apply_case, row, 3)
        row += 1

        # ---------- COALESCE ----------
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFrameShadow(QFrame.Sunken)
        grid.addWidget(sep1, row, 0, 1, 4)
        row += 1

        title_coa = QLabel("COALESCE — заменить NULL значением")
        title_coa.setStyleSheet("color:#9CA3AF; font-size:11px;")
        grid.addWidget(title_coa, row, 0, 1, 4)
        row += 1

        grid.addWidget(QLabel("Колонка:"), row, 0)
        self.coalesce_col = QComboBox()
        grid.addWidget(self.coalesce_col, row, 1, 1, 3)
        row += 1

        grid.addWidget(QLabel("Если NULL, то:"), row, 0)
        self.coalesce_value = QLineEdit()
        self.coalesce_value.setPlaceholderText("подставляемое значение")
        grid.addWidget(self.coalesce_value, row, 1, 1, 3)
        row += 1

        grid.addWidget(QLabel("Alias:"), row, 0)
        self.coalesce_alias = QLineEdit()
        self.coalesce_alias.setPlaceholderText("например: comment_filled")
        grid.addWidget(self.coalesce_alias, row, 1, 1, 2)
        self.btn_apply_coalesce = QPushButton("Применить COALESCE")
        self.btn_apply_coalesce.clicked.connect(self._load_data)
        grid.addWidget(self.btn_apply_coalesce, row, 3)
        row += 1

        # ---------- NULLIF ----------
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        grid.addWidget(sep2, row, 0, 1, 4)
        row += 1

        title_nullif = QLabel("NULLIF — NULL, если значения равны")
        title_nullif.setStyleSheet("color:#9CA3AF; font-size:11px;")
        grid.addWidget(title_nullif, row, 0, 1, 4)
        row += 1

        grid.addWidget(QLabel("Колонка:"), row, 0)
        self.nullif_col = QComboBox()
        grid.addWidget(self.nullif_col, row, 1, 1, 3)
        row += 1

        grid.addWidget(QLabel("Сравнить с:"), row, 0)
        self.nullif_value = QLineEdit()
        self.nullif_value.setPlaceholderText("значение, при котором вернуть NULL")
        grid.addWidget(self.nullif_value, row, 1, 1, 3)
        row += 1

        grid.addWidget(QLabel("Alias:"), row, 0)
        self.nullif_alias = QLineEdit()
        self.nullif_alias.setPlaceholderText("например: paid_or_null")
        grid.addWidget(self.nullif_alias, row, 1, 1, 2)
        self.btn_apply_nullif = QPushButton("Применить NULLIF")
        self.btn_apply_nullif.clicked.connect(self._load_data)
        grid.addWidget(self.btn_apply_nullif, row, 3)
        row += 1

        section = CollapsibleSection("CASE / Работа с NULL", wrapper)
        parent_layout.addWidget(section)

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

        # запомним базовый список для обычного ORDER BY
        self._base_order_cols = list(all_cols)

        self.columns_list.clear()
        for c in all_cols:
            item = QListWidgetItem(c)
            item.setCheckState(Qt.Checked)
            self.columns_list.addItem(item)

        self.search_column.clear()
        self.sub_left_col.clear()
        self.order_col.clear()
        self.group_col.clear()
        self.group_col2.clear()
        self.group_col3.clear()
        self.aggregate_target.clear()

        self.search_column.addItems(all_cols)
        self.sub_left_col.addItems(all_cols)
        self.order_col.addItems(all_cols)  # базовый набор

        # уровни группировки: до трёх колонок
        group_items = [""] + all_cols
        self.group_col.addItems(group_items)
        self.group_col2.addItems(group_items)
        self.group_col3.addItems(group_items)

        self.aggregate_target.addItems([""] + all_cols)

        # сразу привести ORDER BY в согласованное состояние
        self._update_order_choices()

    def _update_order_choices(self):
        """
        Обновить список допустимых вариантов ORDER BY
        в зависимости от выбранных агрегатов / GROUP BY.
        """
        if not hasattr(self, "order_col"):
            return  # на всякий случай, если метод вызовут слишком рано

        # есть ли сейчас агрегирование
        aggregate_mode = bool(
            self.aggregate_func.currentText() and self.aggregate_target.currentText()
        )

        current = self.order_col.currentText().strip()

        self.order_col.blockSignals(True)
        self.order_col.clear()

        if not aggregate_mode:
            # обычный режим — можно сортировать по любой колонке
            if self._base_order_cols:
                self.order_col.addItems(self._base_order_cols)
        else:
            # агрегатный режим: только колонки группировки и agg_value
            options: list[str] = []

            group_cols = self._get_group_columns()
            options.extend(group_cols)

            # результат агрегата — алиас из SELECT
            options.append("agg_value")

            # пустая строка = без сортировки
            self.order_col.addItem("")
            seen: set[str] = set()
            for opt in options:
                if opt and opt not in seen:
                    self.order_col.addItem(opt)
                    seen.add(opt)

        # если старое значение ещё допустимо — вернуть его
        idx = self.order_col.findText(current)
        if idx >= 0:
            self.order_col.setCurrentIndex(idx)

        self.order_col.blockSignals(False)

    def _get_group_columns(self) -> list[str]:
        """Текущий набор колонок для группировки в заданном порядке.

        Игнорируем пустые значения и дубликаты, чтобы не собирать
        некорректные конструкции в GROUP BY / ROLLUP / CUBE.
        """
        cols: list[str] = []
        for cb in (self.group_col, self.group_col2, self.group_col3):
            if cb is None:
                continue
            name = cb.currentText().strip()
            if name and name not in cols:
                cols.append(name)
        return cols

    def _build_grouping_sets_sql(self, cols: list[str]) -> str:
        """Собрать выражение для GROUPING SETS по выбранным колонкам.

        Строим все непустые комбинации колонок + пустое множество для
        общего итога. Для 3 колонок получится, например:
        GROUPING SETS ((a), (b), (c), (a, b), (a, c), (b, c), (a, b, c), ()).
        """
        if not cols:
            return ""

        n = len(cols)
        sets: list[str] = []

        # все непустые подмножества
        for mask in range(1, 1 << n):
            subset = [cols[i] for i in range(n) if mask & (1 << i)]
            if subset:
                sets.append("(" + ", ".join(subset) + ")")

        # общий итог
        sets.append("()")

        return ", ".join(sets)

    def _apply_columns_to_case_null(self):
        """Проставляем список колонок в комбобоксы CASE / COALESCE / NULLIF."""
        all_cols = list(self.join_info.get("selected_columns", []))

        if not all_cols:
            return

        for cb in (
                getattr(self, "case_col", None),
                getattr(self, "coalesce_col", None),
                getattr(self, "nullif_col", None),
        ):
            if cb is not None:
                cb.clear()
                cb.addItems(all_cols)

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

    def _build_case_null_exprs(self) -> list[str]:
        """
        Строит вычисляемые столбцы:
        - CASE ... END AS alias
        - COALESCE(col, value) AS alias
        - NULLIF(col, value) AS alias
        Возвращает список строк вида 'expr AS alias'.
        """
        exprs: list[str] = []

        def register_alias(alias: str, core_expr: str):
            """Регистрируем новый виртуальный столбец, чтобы по нему можно было сортировать и дальше его использовать."""
            self.string_virtual_expr[alias] = core_expr
            self.string_virtual_columns.add(alias)
            if self.order_col.findText(alias) == -1:
                self.order_col.addItem(alias)
            self.current_string_alias = alias

        # ---------- CASE ----------
        if hasattr(self, "case_col"):
            col = (self.case_col.currentText() or "").strip()
            op = (self.case_op.currentText() or "").strip()
            alias = (self.case_alias.text() or "").strip()
            v1 = (self.case_value1.text() or "").strip()
            v2 = (self.case_value2.text() or "").strip()
            then_raw = (self.case_then.text() or "").strip()
            else_raw = (self.case_else.text() or "").strip()

            if col and op and v1 and then_raw:
                # alias по умолчанию, если пользователь не ввёл
                if not alias:
                    base = col.split(".")[-1] or "col"
                    alias = f"{base}_case"

                try:
                    dt = self.col_types.get(col, "text").lower()

                    if op == "BETWEEN":
                        if not v2:
                            QMessageBox.warning(self, "CASE", "Для BETWEEN укажите два значения.")
                        else:
                            lit1 = self.where_builder._format_literal(v1, dt, op)
                            lit2 = self.where_builder._format_literal(v2, dt, op)
                            cond = f"{col} BETWEEN {lit1} AND {lit2}"
                    else:
                        lit = self.where_builder._format_literal(v1, dt, op)
                        cond = f"{col} {op} {lit}"

                    then_esc = then_raw.replace("'", "''")
                    if else_raw:
                        else_esc = else_raw.replace("'", "''")
                        core = (
                            f"CASE WHEN {cond} "
                            f"THEN '{then_esc}' "
                            f"ELSE '{else_esc}' END"
                        )
                    else:
                        core = f"CASE WHEN {cond} THEN '{then_esc}' END"

                    exprs.append(f"{core} AS {alias}")
                    register_alias(alias, core)

                except Exception as e:
                    QMessageBox.warning(self, "CASE", f"Не удалось построить CASE:\n{e}")

        # ---------- COALESCE ----------
        if hasattr(self, "coalesce_col"):
            col = (self.coalesce_col.currentText() or "").strip()
            alias = (self.coalesce_alias.text() or "").strip()
            raw = (self.coalesce_value.text() or "").strip()

            if col and raw:
                # alias по умолчанию
                if not alias:
                    base = col.split(".")[-1] or "col"
                    alias = f"{base}_coalesce"

                try:
                    dt = self.col_types.get(col, "text").lower()
                    lit = self.where_builder._format_literal(raw, dt, "=")
                    core = f"COALESCE({col}, {lit})"
                    exprs.append(f"{core} AS {alias}")
                    register_alias(alias, core)
                except Exception as e:
                    QMessageBox.warning(self, "COALESCE", f"Не удалось построить COALESCE:\n{e}")

        # ---------- NULLIF ----------
        if hasattr(self, "nullif_col"):
            col = (self.nullif_col.currentText() or "").strip()
            alias = (self.nullif_alias.text() or "").strip()
            raw = (self.nullif_value.text() or "").strip()

            if col and raw:
                # alias по умолчанию
                if not alias:
                    base = col.split(".")[-1] or "col"
                    alias = f"{base}_nullif"

                try:
                    dt = self.col_types.get(col, "text").lower()
                    lit = self.where_builder._format_literal(raw, dt, "=")
                    core = f"NULLIF({col}, {lit})"
                    exprs.append(f"{core} AS {alias}")
                    register_alias(alias, core)
                except Exception as e:
                    QMessageBox.warning(self, "NULLIF", f"Не удалось построить NULLIF:\n{e}")

        return exprs

    def _ask_object_name(self, title: str, label: str) -> Optional[str]:
        """Диалог запроса имени объекта (VIEW / MAT VIEW / CTE) с валидатором."""
        dlg = QInputDialog(self)
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.setWindowTitle(title)
        dlg.setLabelText(label)

        # навешиваем валидатор на поле ввода, чтобы нельзя было вводить
        # недопустимые символы (только латиница, цифры и "_",
        # первый символ — буква или подчёркивание)
        line_edit = dlg.findChild(QLineEdit)
        if line_edit is not None:
            regex = QRegularExpression(r"^[A-Za-z_][A-Za-z0-9_]*$")
            validator = QRegularExpressionValidator(regex, line_edit)
            line_edit.setValidator(validator)
            line_edit.setPlaceholderText("Например: report_view_1")

        if dlg.exec() != QDialog.Accepted:
            return None

        name = dlg.textValue().strip()
        if not name:
            QMessageBox.warning(self, title, "Имя не может быть пустым.")
            return None

        # дополнительная проверка на случай, если по какой-то причине
        # валидатор не сработал
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            QMessageBox.warning(
                self,
                title,
                "Имя должно состоять из латинских букв, цифр и подчёркивания\n"
                "и не начинаться с цифры.",
            )
            return None

        return name

    def _get_current_select_sql(self) -> str:
        """Построить SELECT для сохранения (без завершающей точки с запятой)."""
        sql = self._build_sql()
        sql = sql.strip()
        if sql.endswith(";"):
            sql = sql[:-1].strip()
        return sql

    def _save_as_view(self):
        """Сохранить текущий SELECT как обычное представление (VIEW)."""
        title = "Сохранить как VIEW"
        sql = self._get_current_select_sql()
        if not sql:
            QMessageBox.warning(self, title, "Нет запроса для сохранения.")
            return

        name = self._ask_object_name(title, "Имя представления (без схемы):")
        if not name:
            return

        try:
            # helper из db.py: CREATE OR REPLACE VIEW name AS <sql>
            self.db.create_view(name, sql)
            QMessageBox.information(
                self,
                title,
                f'Представление "{name}" создано или обновлено.\n'
                "Оно доступно в окне «Представления и CTE».",
            )
            app_logger.info(f"VIEW {name} создано из DataWindow")
        except Exception as e:
            app_logger.error(f"Ошибка создания VIEW {name} из DataWindow: {e}")
            QMessageBox.critical(
                self,
                title,
                f"Не удалось сохранить представление:\n{e}",
            )

    def _save_as_mat_view(self):
        """Сохранить текущий SELECT как материализованное представление."""
        title = "Сохранить как MATERIALIZED VIEW"
        sql = self._get_current_select_sql()
        if not sql:
            QMessageBox.warning(self, title, "Нет запроса для сохранения.")
            return

        name = self._ask_object_name(title, "Имя MATERIALIZED VIEW (без схемы):")
        if not name:
            return

        try:
            self.db.create_mat_view(name, sql)
            QMessageBox.information(
                self,
                title,
                f'Материализованное представление "{name}" создано.\n'
                "Его можно обновлять через REFRESH в окне «Представления и CTE».",
            )
            app_logger.info(f"MATERIALIZED VIEW {name} создано из DataWindow")
        except Exception as e:
            app_logger.error(f"Ошибка создания MATERIALIZED VIEW {name} из DataWindow: {e}")
            QMessageBox.critical(
                self,
                title,
                "Не удалось создать материализованное представление:\n"
                f"{e}\n\n"
                "Если объект с таким именем уже существует, удалите его\n"
                "в окне «Представления и CTE» и повторите попытку.",
            )

    def _save_as_cte(self):
        """Сохранить текущий SELECT как CTE в менеджере представлений."""
        title = "Сохранить как CTE"
        sql = self._get_current_select_sql()
        if not sql:
            QMessageBox.warning(self, title, "Нет запроса для сохранения.")
            return

        name = self._ask_object_name(title, "Имя CTE (будет использоваться в WITH):")
        if not name:
            return

        if name in GLOBAL_SAVED_CTES:
            res = QMessageBox.question(
                self,
                title,
                f'CTE с именем "{name}" уже существует. Перезаписать?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if res != QMessageBox.Yes:
                return

        GLOBAL_SAVED_CTES[name] = sql
        QMessageBox.information(
            self,
            title,
            f'CTE "{name}" сохранён.\n'
            "Он появится в окне «Представления и CTE» после обновления списка.",
        )
        app_logger.info(f"CTE {name} сохранён из DataWindow")

    # ---------------------------------------------------------
    # SQL builder
    # ---------------------------------------------------------

    def _build_sql(self) -> str:
        info = self.join_info
        all_cols = info.get("selected_columns", [])

        checked: list[str] = []
        for i in range(self.columns_list.count()):
            item = self.columns_list.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(item.text())

        # базовый список выбранных колонок
        if checked:
            base_cols = checked
        else:
            base_cols = all_cols if all_cols else []

        # безопасный SELECT-список: алиасим table.col → table_col
        select_parts: list[str] = []
        for c in base_cols:
            upper = c.upper()
            # если пользователь уже сам написал "expr AS alias" — не трогаем
            if " AS " in upper:
                select_parts.append(c)
                continue

            # table.col → table_col, убираем точки и кавычки
            alias = c.replace('"', "").replace(".", "_")
            select_parts.append(f"{c} AS {alias}")

        cols = ", ".join(select_parts) if select_parts else "*"

        aggregate_mode = bool(
            self.aggregate_func.currentText() and self.aggregate_target.currentText()
        )

        # вычисляемые столбцы (строковые операции + CASE/NULL)
        extra_exprs: list[str] = []

        str_expr = self._build_string_expr()
        if str_expr and not aggregate_mode:
            extra_exprs.append(str_expr)

        case_null_exprs = self._build_case_null_exprs()
        if case_null_exprs and not aggregate_mode:
            extra_exprs.extend(case_null_exprs)

        if extra_exprs:
            extra_sql = ", ".join(extra_exprs)
            cols = f"{cols}, {extra_sql}" if cols.strip() else extra_sql

        # агрегат (если указан) перекрывает обычный SELECT
        if aggregate_mode:
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

            # тип колонки — чтобы понимать, текстовая она или нет
            data_type = self.col_types.get(col, "").lower()
            is_text = any(x in data_type for x in ("char", "text"))

            # для нетекстовых колонок ищем по col::text
            col_expr = col if (is_text or not data_type) else f"{col}::text"

            if mode in ("LIKE", "ILIKE"):
                if "%" not in esc and "_" not in esc:
                    esc = f"%{esc}%"
                cond = f"{col_expr} {mode} '{esc}'"
            elif mode in ("~", "~*", "!~", "!~*"):
                cond = f"{col_expr} {mode} '{esc}'"
            elif mode == "SIMILAR TO":
                cond = f"{col_expr} SIMILAR TO '{esc}'"
            elif mode == "NOT SIMILAR TO":
                cond = f"{col_expr} NOT SIMILAR TO '{esc}'"
            else:
                cond = f"{col_expr} LIKE '{esc}'"

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

        # GROUP BY / ROLLUP / CUBE / GROUPING SETS
        group_cols = self._get_group_columns()
        mode = self.group_mode.currentData() if hasattr(self, "group_mode") else "none"

        if group_cols and mode != "none":
            if mode == "plain":
                group_expr = ", ".join(group_cols)
                q += f" GROUP BY {group_expr}"
            elif mode == "rollup":
                inner = ", ".join(group_cols)
                q += f" GROUP BY ROLLUP ({inner})"
            elif mode == "cube":
                inner = ", ".join(group_cols)
                q += f" GROUP BY CUBE ({inner})"
            elif mode == "grouping_sets":
                sets_sql = self._build_grouping_sets_sql(group_cols)
                if sets_sql:
                    q += f" GROUP BY GROUPING SETS ({sets_sql})"
            else:
                # на всякий случай — как обычный GROUP BY
                group_expr = ", ".join(group_cols)
                q += f" GROUP BY {group_expr}"

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

            # обновляем список колонок для поиска и применяем текущий фильтр
            self._update_result_search_columns()
            self._apply_result_filter()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка выполнения запроса:\n{e}")
            app_logger.error(f"DataWindow SQL error: {e}")
