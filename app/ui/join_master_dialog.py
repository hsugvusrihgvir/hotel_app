# join_master_dialog.py — мастер выбора таблиц перед DataWindow

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from app.ui.theme import *


class JoinMasterDialog(QDialog):
    # мастер выбора таблиц, полей и типа JOIN

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {WINDOW_BG};
                color: {TEXT_MAIN};
            }}
            QGroupBox {{
                background-color: {CARD_BG};
                color: {TEXT_SOFT};
                border: 5px solid {CARD_BORDER};
                border-radius: 12px;
                border-right: 0.5px solid {ACCENT_PRIMARY};
                margin-top: 18px;
                padding: 10px 10px 14px 10px;
                font-weight: bold;
                font-size: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                background-color: {CARD_BG};
                color: {ACCENT_PRIMARY};
                font-weight: bold;
            }}
            QTableWidget {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                gridline-color: #404040;
                border: 1px solid {CARD_BORDER};
                border-radius: 8px;
            }}
            QTableWidget::item {{
                padding: 6px;
                border-bottom: 1px solid {CARD_BORDER};
            }}
            QTableWidget::item:selected {{
                background-color: {ACCENT_PRIMARY};
                color: {WINDOW_BG};
                font-weight: bold;
            }}
            QHeaderView::section {{
                background-color: {CARD_BG};
                color: {TEXT_SOFT};
                padding: 8px;
                border: none;
                border-right: 1px solid {CARD_BORDER};
                border-bottom: 1px solid {CARD_BORDER};
                font-weight: bold;
            }}
            QLineEdit, QComboBox {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 2px solid {CARD_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                selection-background-color: {ACCENT_PRIMARY};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {ACCENT_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
                font-style: italic;
            }}
            QComboBox QAbstractItemView {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 1px solid {CARD_BORDER};
                selection-background-color: {ACCENT_PRIMARY};
                selection-color: {WINDOW_BG};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                border: none;
                width: 12px;
                height: 12px;
                background-color: {ACCENT_PRIMARY};
                border-radius: 2px;
            }}
            QLabel {{
                color: {TEXT_SOFT};
                font-weight: bold;
                font-size: 12px;
            }}
            QScrollArea {{
                background-color: {WINDOW_BG};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {CARD_BG};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {ACCENT_PRIMARY};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {ACCENT_SUCCESS};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}""")

        self.table1 = None
        self.table2 = None
        self.col1 = None
        self.col2 = None
        self.join_type = None

        # сюда будем класть полный список колонок формата table.col,
        # чтобы DataWindow знал, что вообще доступно
        self.selected_columns = []

        self.setWindowTitle("Выбор таблиц и JOIN")
        self.resize(520, 320)
        self.setModal(True)
        self._build_ui()
        self._load_tables()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("Мастер JOIN")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color:#e0e0e0; margin-bottom:10px;")
        layout.addWidget(title)

        # таблица 1
        self.cb_table1 = QComboBox()
        layout.addWidget(QLabel("Таблица 1:"))
        layout.addWidget(self.cb_table1)

        # таблица 2
        self.cb_table2 = QComboBox()
        layout.addWidget(QLabel("Таблица 2:"))
        layout.addWidget(self.cb_table2)

        # поле для связи 1
        layout.addWidget(QLabel("Поле связи (таблица 1):"))
        self.cb_col1 = QComboBox()
        layout.addWidget(self.cb_col1)

        # поле 2
        layout.addWidget(QLabel("Поле связи (таблица 2):"))
        self.cb_col2 = QComboBox()
        layout.addWidget(self.cb_col2)

        # тип join
        layout.addWidget(QLabel("Тип JOIN:"))
        self.cb_join_type = QComboBox()
        self.cb_join_type.addItems(["INNER", "LEFT", "RIGHT", "FULL"])
        layout.addWidget(self.cb_join_type)

        # кнопки
        btns = QHBoxLayout()
        self.btn_ok = QPushButton("Продолжить")
        self.btn_cancel = QPushButton("Отмена")
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        # сигналы
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._apply_selection)
        self.cb_table1.currentTextChanged.connect(self._load_cols_1)
        self.cb_table2.currentTextChanged.connect(self._load_cols_2)

    # загрузка таблиц
    def _load_tables(self):
        q = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name;
        """
        with self.db.cursor() as cur:
            cur.execute(q)
            tables = [r["table_name"] for r in cur.fetchall()]

        self.cb_table1.addItems(tables)
        self.cb_table2.addItems(tables)

        self._load_cols_1()
        self._load_cols_2()

    def _load_cols_1(self):
        table = self.cb_table1.currentText()
        self._load_columns(table, self.cb_col1)

    def _load_cols_2(self):
        table2 = self.cb_table2.currentText()

        # тип первого столбца
        table1 = self.cb_table1.currentText()
        col1 = self.cb_col1.currentText()
        type1 = self._get_column_type(table1, col1)

        # загружаем только совместимые по типу поля для связи
        compatible = []
        for col in self._fetch_columns_full(table2):
            if self._is_compatible(type1, col["data_type"]):
                compatible.append(col["column_name"])

        self.cb_col2.clear()
        self.cb_col2.addItems(compatible)

    def _load_columns(self, table, combo):
        combo.clear()
        if not table:
            return
        cols = self._fetch_columns(table)
        combo.addItems(cols)

    def _fetch_columns(self, table):
        q = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name=%s
            ORDER BY ordinal_position
        """
        with self.db.cursor() as cur:
            cur.execute(q, (table,))
            return [r["column_name"] for r in cur.fetchall()]

    def _fetch_columns_full(self, table):
        # возвращает [{column_name, data_type}]
        q = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name=%s
        """
        with self.db.cursor() as cur:
            cur.execute(q, (table,))
            return cur.fetchall()

    def _get_column_type(self, table, column):
        if not table or not column:
            return None
        q = """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name=%s AND column_name=%s
        """
        with self.db.cursor() as cur:
            cur.execute(q, (table, column))
            res = cur.fetchone()
            return res["data_type"] if res else None

    def _is_compatible(self, type1, type2):
        # примерная проверка на совместимость
        if not type1 or not type2:
            return False

        numeric = {"integer", "bigint", "smallint", "numeric", "real", "double precision"}
        text = {"character varying", "text", "varchar", "char"}

        if type1 == type2:
            return True
        if type1 in numeric and type2 in numeric:
            return True
        if type1 in text and type2 in text:
            return True
        return False

    def _apply_selection(self):
        if self.cb_table1.currentText() == self.cb_table2.currentText():
            QMessageBox.warning(self, "Ошибка", "Нужно выбрать две разные таблицы.")
            return

        self.table1 = self.cb_table1.currentText()
        self.table2 = self.cb_table2.currentText()
        self.col1 = self.cb_col1.currentText()
        self.col2 = self.cb_col2.currentText()
        self.join_type = self.cb_join_type.currentText()

        # здесь мы больше НЕ спрашиваем пользователя про колонки
        # просто берём ВСЕ колонки из обеих таблиц в формате table.col
        cols1 = self._fetch_columns(self.table1)
        cols2 = self._fetch_columns(self.table2)
        self.selected_columns = [f"{self.table1}.{c}" for c in cols1] + [
            f"{self.table2}.{c}" for c in cols2
        ]

        self.accept()
