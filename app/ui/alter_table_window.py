# alter_table_window.py — профессиональный модуль ALTER TABLE с поддержкой ENUM и COMPOSITE

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QPushButton, QLineEdit,
    QMessageBox, QTableWidget, QTableWidgetItem, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.log.log import app_logger


class AlterTableWindow(QDialog):
    """окно изменения структуры таблиц — поддержка ENUM + COMPOSITE"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Изменение структуры таблиц")
        self.resize(850, 650)
        self.setModal(True)

        self._build_ui()
        self._load_tables()
        self._load_custom_types()

    # =====================================================================
    # UI
    # =====================================================================

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ---------------- header ------------------------
        title = QLabel("ALTER TABLE — инструменты")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color:#e0e0e0; margin-bottom:8px;")
        layout.addWidget(title)

        # ---------------- select table ------------------
        table_box = QHBoxLayout()
        layout.addLayout(table_box)

        table_box.addWidget(QLabel("Таблица:"))
        self.cb_table = QComboBox()
        table_box.addWidget(self.cb_table)

        self.cb_table.currentTextChanged.connect(self._load_columns)

        # ---------------- group: добавить столбец ------------------
        gb_add = QGroupBox("Добавить столбец")
        gb_layout = QHBoxLayout(gb_add)

        self.add_name = QLineEdit()
        self.add_name.setPlaceholderText("имя столбца")

        self.add_type = QComboBox()
        self.add_type.currentTextChanged.connect(self._on_type_changed)

        self.btn_add = QPushButton("Добавить")
        self.btn_add.clicked.connect(self._add_column)

        gb_layout.addWidget(self.add_name)
        gb_layout.addWidget(self.add_type)
        gb_layout.addWidget(self.btn_add)

        layout.addWidget(gb_add)

        # ---------------- group: удалить столбец ------------------
        gb_drop = QGroupBox("Удалить столбец")
        gb_layout = QHBoxLayout(gb_drop)

        self.cb_drop_col = QComboBox()
        self.btn_drop = QPushButton("Удалить")
        self.btn_drop.clicked.connect(self._drop_column)

        gb_layout.addWidget(self.cb_drop_col)
        gb_layout.addWidget(self.btn_drop)

        layout.addWidget(gb_drop)

        # ---------------- group: переименовать столбец ------------------
        gb_rename = QGroupBox("Переименовать столбец")
        gb_layout = QHBoxLayout(gb_rename)

        self.cb_rename_col = QComboBox()
        self.rename_new = QLineEdit()
        self.rename_new.setPlaceholderText("новое имя")

        self.btn_rename = QPushButton("Переименовать")
        self.btn_rename.clicked.connect(self._rename_column)

        gb_layout.addWidget(self.cb_rename_col)
        gb_layout.addWidget(self.rename_new)
        gb_layout.addWidget(self.btn_rename)

        layout.addWidget(gb_rename)

        # ---------------- group: изменить тип ------------------
        gb_type = QGroupBox("Изменить тип столбца")
        gb_layout = QVBoxLayout(gb_type)

        top = QHBoxLayout()
        gb_layout.addLayout(top)

        self.cb_type_col = QComboBox()
        self.cb_new_type = QComboBox()
        self.cb_new_type.currentTextChanged.connect(self._on_type_changed)

        self.btn_type = QPushButton("Изменить тип")
        self.btn_type.clicked.connect(self._change_type)

        top.addWidget(self.cb_type_col)
        top.addWidget(self.cb_new_type)
        top.addWidget(self.btn_type)

        # детальная панель информации о выбранном типе
        self.type_details = QTableWidget()
        self.type_details.setColumnCount(2)
        self.type_details.setHorizontalHeaderLabels(["Поле", "Тип"])
        self.type_details.horizontalHeader().setStretchLastSection(True)
        gb_layout.addWidget(self.type_details)

        layout.addWidget(gb_type)

        # ---------------- group: NOT NULL / UNIQUE / CHECK ------------------
        gb_constraints = QGroupBox("Ограничения")
        gb_layout = QHBoxLayout(gb_constraints)

        # NOT NULL
        self.cb_nn_col = QComboBox()
        self.btn_set_nn = QPushButton("SET NOT NULL")
        self.btn_drop_nn = QPushButton("DROP NOT NULL")

        self.btn_set_nn.clicked.connect(lambda: self._set_not_null(True))
        self.btn_drop_nn.clicked.connect(lambda: self._set_not_null(False))

        # UNIQUE
        self.cb_unique_col = QComboBox()
        self.btn_set_unique = QPushButton("SET UNIQUE")
        self.btn_drop_unique = QPushButton("DROP UNIQUE")

        self.btn_set_unique.clicked.connect(lambda: self._set_unique(True))
        self.btn_drop_unique.clicked.connect(lambda: self._set_unique(False))

        gb_layout.addWidget(self.cb_nn_col)
        gb_layout.addWidget(self.btn_set_nn)
        gb_layout.addWidget(self.btn_drop_nn)

        gb_layout.addWidget(self.cb_unique_col)
        gb_layout.addWidget(self.btn_set_unique)
        gb_layout.addWidget(self.btn_drop_unique)

        layout.addWidget(gb_constraints)

        # ---------------- group: FOREIGN KEY ------------------
        gb_fk = QGroupBox("FOREIGN KEY")
        gb_layout = QHBoxLayout(gb_fk)

        self.cb_fk_col = QComboBox()        # этот столбец станет FK
        self.fk_ref_table = QComboBox()     # таблица ссылка
        self.fk_ref_col = QComboBox()       # столбец в таблице ссылки

        self.btn_set_fk = QPushButton("SET FK")
        self.btn_drop_fk = QPushButton("DROP FK")

        self.btn_set_fk.clicked.connect(self._set_fk)
        self.btn_drop_fk.clicked.connect(self._drop_fk)

        gb_layout.addWidget(self.cb_fk_col)
        gb_layout.addWidget(self.fk_ref_table)
        gb_layout.addWidget(self.fk_ref_col)
        gb_layout.addWidget(self.btn_set_fk)
        gb_layout.addWidget(self.btn_drop_fk)

        layout.addWidget(gb_fk)

    # =====================================================================
    # загрузка данных
    # =====================================================================

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

        self.cb_table.addItems(tables)

    def _load_columns(self):
        table = self.cb_table.currentText()
        if not table:
            return

        q = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name=%s
            ORDER BY ordinal_position;
        """

        with self.db.cursor() as cur:
            cur.execute(q, (table,))
            cols = [r["column_name"] for r in cur.fetchall()]

        # заполняем все combo для столбцов
        self.cb_drop_col.clear()
        self.cb_rename_col.clear()
        self.cb_type_col.clear()
        self.cb_nn_col.clear()
        self.cb_unique_col.clear()
        self.cb_fk_col.clear()

        for cb in [
            self.cb_drop_col, self.cb_rename_col, self.cb_type_col,
            self.cb_nn_col, self.cb_unique_col, self.cb_fk_col
        ]:
            cb.addItems(cols)

        # FK — загрузка таблиц и колонок
        self._load_fk_tables()

    def _load_fk_tables(self):
        q = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name;
        """

        with self.db.cursor() as cur:
            cur.execute(q)
            tables = [r["table_name"] for r in cur.fetchall()]

        self.fk_ref_table.clear()
        self.fk_ref_table.addItems(tables)
        self.fk_ref_table.currentTextChanged.connect(self._load_fk_columns)

        self._load_fk_columns()

    def _load_fk_columns(self):
        table = self.fk_ref_table.currentText()
        q = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name=%s
            ORDER BY ordinal_position;
        """

        with self.db.cursor() as cur:
            cur.execute(q, (table,))
            cols = [r["column_name"] for r in cur.fetchall()]

        self.fk_ref_col.clear()
        self.fk_ref_col.addItems(cols)

    # =====================================================================
    # загрузка пользовательских типов
    # =====================================================================

    def _load_custom_types(self):
        """заполняем add_type и cb_new_type всеми типами PostgreSQL"""
        # стандартные
        base_types = [
            "integer", "bigint", "serial", "text", "boolean",
            "date", "timestamp", "numeric", "real"
        ]

        custom = self.db.get_custom_types()  # ENUM + COMPOSITE

        for cb in (self.add_type, self.cb_new_type):
            cb.clear()
            cb.addItems(base_types + custom)

    # =====================================================================
    # реакция на выбор типа (показать структуру ENUM/COMPOSITE)
    # =====================================================================

    def _on_type_changed(self, typename):
        """показывает структуру типа справа"""
        if not typename:
            self.type_details.setRowCount(0)
            return

        self.type_details.clear()
        self.type_details.setRowCount(0)

        # ENUM
        if self._is_enum(typename):
            q = """
                SELECT enumlabel
                FROM pg_enum 
                JOIN pg_type ON pg_type.oid = enumtypid
                WHERE typname=%s
                ORDER BY enumsortorder;
            """
            with self.db.cursor() as cur:
                cur.execute(q, (typename,))
                rows = cur.fetchall()

            self.type_details.setColumnCount(1)
            self.type_details.setHorizontalHeaderLabels(["ENUM значение"])
            self.type_details.setRowCount(len(rows))

            for i, r in enumerate(rows):
                self.type_details.setItem(i, 0, QTableWidgetItem(r["enumlabel"]))

        # COMPOSITE
        elif self._is_composite(typename):
            q = """
                SELECT attname, format_type(atttypid, atttypmod) AS type
                FROM pg_attribute
                JOIN pg_type ON pg_type.oid = attrelid
                WHERE typname=%s AND attnum > 0
                ORDER BY attnum;
            """
            with self.db.cursor() as cur:
                cur.execute(q, (typename,))
                rows = cur.fetchall()

            self.type_details.setColumnCount(2)
            self.type_details.setHorizontalHeaderLabels(["Поле", "Тип"])
            self.type_details.setRowCount(len(rows))

            for i, r in enumerate(rows):
                self.type_details.setItem(i, 0, QTableWidgetItem(r["attname"]))
                self.type_details.setItem(i, 1, QTableWidgetItem(r["type"]))

        else:
            self.type_details.setRowCount(0)

    def _is_enum(self, typename):
        q = """
            SELECT 1
            FROM pg_type
            WHERE typnamespace='public'::regnamespace
              AND typname=%s AND typtype='e';
        """
        with self.db.cursor() as cur:
            cur.execute(q, (typename,))
            return cur.fetchone() is not None

    def _is_composite(self, typename):
        q = """
            SELECT 1
            FROM pg_type
            WHERE typnamespace='public'::regnamespace
              AND typname=%s AND typtype='c';
        """
        with self.db.cursor() as cur:
            cur.execute(q, (typename,))
            return cur.fetchone() is not None

    # =====================================================================
    # ALTER TABLE операции
    # =====================================================================

    def _add_column(self):
        table = self.cb_table.currentText()
        name = self.add_name.text().strip()
        typ = self.add_type.currentText()

        if not name:
            return

        sql = f"ALTER TABLE {table} ADD COLUMN {name} {typ};"
        self._execute(sql, f"добавлен столбец {name}")
        self._load_columns()

    def _drop_column(self):
        table = self.cb_table.currentText()
        col = self.cb_drop_col.currentText()
        sql = f"ALTER TABLE {table} DROP COLUMN {col} CASCADE;"
        self._execute(sql, f"столбец {col} удалён")
        self._load_columns()

    def _rename_column(self):
        table = self.cb_table.currentText()
        old = self.cb_rename_col.currentText()
        new = self.rename_new.text().strip()
        if not new:
            return
        sql = f"ALTER TABLE {table} RENAME COLUMN {old} TO {new};"
        self._execute(sql, f"столбец {old} → {new}")
        self._load_columns()

    def _change_type(self):
        table = self.cb_table.currentText()
        col = self.cb_type_col.currentText()
        new = self.cb_new_type.currentText()
        sql = f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {new};"
        self._execute(sql, f"тип столбца {col} изменён")
        self._load_columns()

    def _set_not_null(self, flag):
        table = self.cb_table.currentText()
        col = self.cb_nn_col.currentText()
        action = "SET" if flag else "DROP"
        sql = f"ALTER TABLE {table} ALTER COLUMN {col} {action} NOT NULL;"
        self._execute(sql, f"NOT NULL {action} для {col}")

    def _set_unique(self, flag):
        table = self.cb_table.currentText()
        col = self.cb_unique_col.currentText()

        if flag:
            sql = f"ALTER TABLE {table} ADD CONSTRAINT {col}_uniq UNIQUE({col});"
        else:
            sql = f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {col}_uniq;"

        self._execute(sql, f"UNIQUE {'добавлен' if flag else 'убран'} для {col}")

    def _set_fk(self):
        table = self.cb_table.currentText()
        col = self.cb_fk_col.currentText()
        ref_table = self.fk_ref_table.currentText()
        ref_col = self.fk_ref_col.currentText()

        sql = (
            f"ALTER TABLE {table} "
            f"ADD CONSTRAINT fk_{table}_{col} "
            f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col});"
        )

        self._execute(sql, "FK установлен")

    def _drop_fk(self):
        table = self.cb_table.currentText()
        col = self.cb_fk_col.currentText()

        sql = (
            f"ALTER TABLE {table} "
            f"DROP CONSTRAINT IF EXISTS fk_{table}_{col} CASCADE;"
        )

        self._execute(sql, "FK удалён")

    # =====================================================================
    # SQL exec
    # =====================================================================

    def _execute(self, sql, msg):
        try:
            self.db.execute_ddl(sql)
            QMessageBox.information(self, "Готово", msg)
            app_logger.info(sql)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            app_logger.error(e)
