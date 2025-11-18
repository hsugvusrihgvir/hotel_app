from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from app.log.log import app_logger


class QuickViewWindow(QMainWindow):
    """Окно быстрого просмотра таблиц с минимальными фильтрами."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Быстрый просмотр")
        self.resize(900, 600)

        self._build_ui()
        self._apply_theme()
        self._load_tables()

    # ---------------- UI ----------------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # верхняя панель
        top = QHBoxLayout()
        layout.addLayout(top)

        # выбор таблицы
        top.addWidget(QLabel("Таблица:"))
        self.cb_table = QComboBox()
        top.addWidget(self.cb_table)

        # выбор колонки
        top.addWidget(QLabel("Колонка:"))
        self.cb_column = QComboBox()
        top.addWidget(self.cb_column)

        # поле фильтра
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Фильтр (LIKE)")
        top.addWidget(self.filter_edit)

        # order by
        top.addWidget(QLabel("ORDER BY:"))
        self.cb_order_col = QComboBox()
        top.addWidget(self.cb_order_col)

        self.cb_order_dir = QComboBox()
        self.cb_order_dir.addItems(["ASC", "DESC"])
        top.addWidget(self.cb_order_dir)

        # limit
        top.addWidget(QLabel("LIMIT:"))
        self.limit_box = QSpinBox()
        self.limit_box.setRange(1, 50000)
        self.limit_box.setValue(200)
        top.addWidget(self.limit_box)

        # кнопка
        self.btn_apply = QPushButton("Применить")
        top.addWidget(self.btn_apply)

        self.btn_apply.clicked.connect(self._load_data)
        self.cb_table.currentTextChanged.connect(self._load_columns)

        # таблица
        self.table = QTableWidget()
        layout.addWidget(self.table)

    def _apply_theme(self):
        """Пастельная тема для окна быстрого просмотра."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111318;
            }
            QWidget {
                color: #e5e7eb;
            }

            QLineEdit, QComboBox, QSpinBox {
                background-color: #1b1f29;
                border: 1px solid #2a2f3c;
                border-radius: 6px;
                padding: 3px 6px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #8BA4E0;
            }

            QPushButton {
                background-color: #3F4F79;
                color: #F5F5F7;
                border: 1px solid #323A52;
                border-radius: 6px;
                padding: 4px 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #364568;
                border-color: #2B3550;
            }
            QPushButton:pressed {
                background-color: #2B3452;
                border-color: #222A40;
            }
            QPushButton:disabled {
                background-color: #252937;
                color: #9CA3AF;
                border-color: #3A4257;
            }

            QTableWidget {
                background-color: #15171f;
                gridline-color: #2a2f3c;
                selection-background-color: #3F4F79;
                selection-color: #f9fafb;
            }
            QHeaderView::section {
                background-color: #1f222b;
                color: #e5e7eb;
                border: 1px solid #2a2f3c;
                padding: 4px;
            }
        """)

    # ---------------- загрузка таблиц ----------------
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

    # ---------------- ЗАГРУЗКА ДАННЫХ ----------------
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

        # простой фильтр LIKE c параметром
        if flt:
            q += f" WHERE {col}::text ILIKE %s"
            params.append(f"%{flt}%")

        # ORDER BY (имена колонок/направление берутся из combobox, не из ввода)
        if order_col:
            q += f" ORDER BY {order_col} {order_dir}"

        # LIMIT тоже как параметр
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