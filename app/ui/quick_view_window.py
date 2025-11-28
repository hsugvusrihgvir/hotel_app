from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox, QHeaderView  # ← добавь
)
from PySide6.QtCore import Qt
from app.log.log import app_logger
from app.ui.theme import *

# окно быстрого просмотра таблиц с минимальными фильтрами
class QuickViewWindow(QMainWindow):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.is_first_load = True

        self.setWindowTitle("Быстрый просмотр")
        self.resize(900, 600)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {WINDOW_BG};
                color: {TEXT_MAIN};
            }}
            QListWidget {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 1px solid {CARD_BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {CARD_BORDER};
            }}
            QListWidget::item:selected {{
                background-color: {ACCENT_PRIMARY};
                color: {WINDOW_BG};
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
            QPushButton {{
                background-color: {BTN_BG};
                color: {BTN_TEXT};
                border: 1px solid {BTN_BORDER};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
                font-weight: 500;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {BTN_BG_HOVER};
                border-color: {BTN_BORDER};
            }}
            QPushButton:pressed {{
                background-color: {BTN_BG_PRESSED};
                border-color: {BTN_BORDER};
            }}
            QPushButton:disabled {{
                background-color: #252937;
                color: #9CA3AF;
                border-color: #3A4257;
            }}
            QLineEdit {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 2px solid {CARD_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                selection-background-color: {ACCENT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {ACCENT_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
                font-style: italic;
            }}
            QLabel {{
                color: {TEXT_SOFT};
                font-weight: bold;
            }}
            QComboBox QAbstractItemView {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 1px solid {CARD_BORDER};
                selection-background-color: {ACCENT_PRIMARY};
                selection-color: {WINDOW_BG};
            }}
            QComboBox {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 2px solid {CARD_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                selection-background-color: {ACCENT_PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {ACCENT_PRIMARY};
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
            QSpinBox {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 2px solid {CARD_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QSpinBox:focus {{
                border-color: {ACCENT_PRIMARY};
            }} """)

        self._build_ui()
        self._load_tables()

    def _get_column_type(self, table, column):
        # возвращает data_type из information_schema для выбранной колонки
        if not table or not column:
            return None

        q = """
              SELECT data_type
              FROM information_schema.columns
              WHERE table_schema = 'public'
                AND table_name = %s
                AND column_name = %s
          """
        try:
            with self.db.cursor() as cur:
                cur.execute(q, (table, column))
                row = cur.fetchone()
                return row["data_type"] if row else None
        except Exception as e:
            app_logger.error(e)
            return None


    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # верхняя панель
        top1 = QHBoxLayout()
        layout.addLayout(top1)

        # выбор таблицы
        top1.addWidget(QLabel("В таблице"))
        self.cb_table = QComboBox()
        top1.addWidget(self.cb_table)

        # выбор колонки
        top1.addWidget(QLabel("колонка"))
        self.cb_column = QComboBox()
        top1.addWidget(self.cb_column)

        # поле поиска
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("поиск…")
        top1.addWidget(self.filter_edit)

        top2 = QHBoxLayout()
        layout.addLayout(top2)

        # order by
        lbl_order = QLabel("    ORDER BY")
        lbl_order.setStyleSheet(f"color: {ACCENT_SUCCESS}; font-size: 12px; font-weight: bold;")
        top2.addWidget(lbl_order)
        self.cb_order_col = QComboBox()
        top2.addWidget(self.cb_order_col)

        self.cb_order_dir = QComboBox()
        self.cb_order_dir.addItems(["ASC", "DESC"])
        top2.addWidget(self.cb_order_dir)

        # limit
        lbl_limit = QLabel("LIMIT")
        lbl_limit.setStyleSheet(f"color: {ACCENT_SUCCESS}; font-size: 12px; font-weight: bold;")
        top2.addWidget(lbl_limit)
        self.limit_box = QSpinBox()
        self.limit_box.setRange(1, 50000)
        self.limit_box.setValue(200)
        top2.addWidget(self.limit_box)
        top2.addStretch(1)

        # кнопка
        self.btn_apply = QPushButton("Применить")
        top2.addWidget(self.btn_apply)

        self.btn_apply.clicked.connect(self._on_apply_clicked)
        self.cb_table.currentTextChanged.connect(self._on_table_changed)

        # таблица
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)

    def _on_table_changed(self):
        self._load_columns()
        self._load_data()

    # загрузка таблиц
    def _load_tables(self):
        try:
            tables = self.db.get_tables()
            self.cb_table.addItems(tables)
            if tables:
                self._load_columns()
                self._load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            app_logger.error(e)

    def _load_columns(self):
        table = self.cb_table.currentText()
        if not table:
            return

        q = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """

        try:
            with self.db.cursor() as cur:
                cur.execute(q, (table,))
                cols = [r["column_name"] for r in cur.fetchall()]
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            app_logger.error(e)
            return

        self.cb_column.clear()
        self.cb_order_col.clear()
        self.cb_column.addItems(cols)
        self.cb_order_col.addItems(cols)

    # загрузка данных
    def _build_sql(self):
        table = self.cb_table.currentText()
        col = self.cb_column.currentText()
        flt = self.filter_edit.text().strip()
        order_col = self.cb_order_col.currentText()
        order_dir = self.cb_order_dir.currentText()
        limit = self.limit_box.value()

        # базовый запрос
        q = f"SELECT * FROM {table}"
        params = []

        # поиск по типу колонки
        if flt:
            col_type = self._get_column_type(table, col)
            numeric_types = {
                "integer", "bigint", "smallint",
                "numeric", "real", "double precision"
            }

            if col_type in numeric_types:
                # лучше проверка чисел
                try:
                    num_val = float(flt)
                    q += f' WHERE "{col}" = %s'
                    params.append(num_val)
                except ValueError:
                    # если не число - ищем как текст
                    q += f' WHERE "{col}"::text ILIKE %s'
                    params.append(f"%{flt}%")
            elif col_type == "boolean":
                # true / false / да / нет
                txt = flt.lower()
                if txt in ("true", "t", "1", "yes", "y", "да"):
                    q += f" WHERE {col} = %s"
                    params.append(True)
                elif txt in ("false", "f", "0", "no", "n", "нет"):
                    q += f" WHERE {col} = %s"
                    params.append(False)
                else:
                    q += f" WHERE {col}::text ILIKE %s"
                    params.append(f"%{flt}%")
            else:
                # строки, даты и всё остальное — мягкий поиск по подстроке
                q += f" WHERE {col}::text ILIKE %s"
                params.append(f"%{flt}%")

        # ORDER BY и LIMIT
        if order_col:
            q += f" ORDER BY {order_col} {order_dir}"
        q += " LIMIT %s"
        params.append(limit)

        return q + ";", params

    def _load_data(self):
        try:
            sql, params = self._build_sql()

            with self.db.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()

            if not rows:
                if not self.is_first_load:
                    self.table.setRowCount(1)
                    self.table.setColumnCount(1)
                    self.table.setHorizontalHeaderLabels(["Результат"])
                    item = QTableWidgetItem("Нет результатов по поиску")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(0, 0, item)
                else:
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
            QMessageBox.critical(self, "Ошибка", f"Ошибка запроса:\n{e}")
            app_logger.error(e)

    def _on_apply_clicked(self):
        self.is_first_load = False
        self._load_data()