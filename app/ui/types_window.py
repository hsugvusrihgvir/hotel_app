# types_window.py — управление ENUM и COMPOSITE типами

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from app.log.log import app_logger


class TypesWindow(QMainWindow):
    """окно управления пользовательскими типами PostgreSQL (ENUM + COMPOSITE)"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Пользовательские типы данных (ENUM / COMPOSITE)")
        self.resize(900, 600)

        self._build_ui()
        self._load_types()

    # =====================================================================
    # UI
    # =====================================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # ---------------- LEFT: type list ----------------------
        left_box = QVBoxLayout()
        layout.addLayout(left_box, 1)

        title = QLabel("Типы данных (public)")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color:#e0e0e0;")
        left_box.addWidget(title)

        self.list_types = QListWidget()
        left_box.addWidget(self.list_types)

        # buttons left
        btn_new_enum = QPushButton("Создать ENUM")
        btn_new_composite = QPushButton("Создать COMPOSITE")
        btn_delete = QPushButton("Удалить выбранный тип")

        left_box.addWidget(btn_new_enum)
        left_box.addWidget(btn_new_composite)
        left_box.addWidget(btn_delete)

        btn_new_enum.clicked.connect(self._create_enum_dialog)
        btn_new_composite.clicked.connect(self._create_composite_dialog)
        btn_delete.clicked.connect(self._delete_type)

        self.list_types.currentItemChanged.connect(self._on_type_selected)

        # ---------------- RIGHT: details ----------------------
        right_box = QVBoxLayout()
        layout.addLayout(right_box, 2)

        self.lbl_type_name = QLabel("Выберите тип слева")
        self.lbl_type_name.setFont(QFont("Segoe UI", 12, QFont.Bold))
        right_box.addWidget(self.lbl_type_name)

        self.table_details = QTableWidget()
        right_box.addWidget(self.table_details)

        # ENUM: add value
        enum_add_box = QHBoxLayout()
        right_box.addLayout(enum_add_box)

        self.enum_add_input = QLineEdit()
        self.enum_add_input.setPlaceholderText("Новое значение ENUM…")
        enum_add_box.addWidget(self.enum_add_input)

        self.btn_enum_add = QPushButton("Добавить значение")
        enum_add_box.addWidget(self.btn_enum_add)

        self.btn_enum_add.clicked.connect(self._add_enum_value)

        self._set_details_empty()

    # =====================================================================
    # loading
    # =====================================================================

    def _load_types(self):
        self.list_types.clear()

        q = """
            SELECT typname, typtype
            FROM pg_type
            WHERE typnamespace = 'public'::regnamespace
              AND typtype IN ('e', 'c')
            ORDER BY typname;
        """

        with self.db.cursor() as cur:
            cur.execute(q)
            rows = cur.fetchall()

        for r in rows:
            name = r["typname"]
            kind = r["typtype"]   # e = enum, c = composite

            item = QListWidgetItem(f"{name}    ({'ENUM' if kind=='e' else 'COMPOSITE'})")
            item.setData(Qt.UserRole, (name, kind))
            self.list_types.addItem(item)

    # =====================================================================
    # when user selects a type
    # =====================================================================

    def _on_type_selected(self, item):
        if not item:
            self._set_details_empty()
            return

        name, kind = item.data(Qt.UserRole)

        self.lbl_type_name.setText(
            f"{name} — {'ENUM' if kind=='e' else 'COMPOSITE'}"
        )

        if kind == "e":
            self._load_enum_values(name)
        else:
            self._load_composite_fields(name)

    # =====================================================================
    # ENUM viewer
    # =====================================================================

    def _load_enum_values(self, typename):
        q = "SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_type.oid = enumtypid WHERE typname=%s ORDER BY enumsortorder;"

        with self.db.cursor() as cur:
            cur.execute(q, (typename,))
            rows = cur.fetchall()

        self.table_details.setColumnCount(1)
        self.table_details.setHorizontalHeaderLabels(["Значение"])
        self.table_details.setRowCount(len(rows))

        for i, r in enumerate(rows):
            self.table_details.setItem(i, 0, QTableWidgetItem(r["enumlabel"]))

        self._enable_enum_controls(True)

    # =====================================================================
    # COMPOSITE viewer
    # =====================================================================

    def _load_composite_fields(self, typename):
        q = """
            SELECT attname, format_type(atttypid, atttypmod) AS type
            FROM pg_attribute
            JOIN pg_type ON pg_type.oid = attrelid
            WHERE typname=%s
              AND attnum > 0
            ORDER BY attnum;
        """

        with self.db.cursor() as cur:
            cur.execute(q, (typename,))
            rows = cur.fetchall()

        self.table_details.setColumnCount(2)
        self.table_details.setHorizontalHeaderLabels(["Поле", "Тип"])
        self.table_details.setRowCount(len(rows))

        for i, r in enumerate(rows):
            self.table_details.setItem(i, 0, QTableWidgetItem(r["attname"]))
            self.table_details.setItem(i, 1, QTableWidgetItem(r["type"]))

        self._enable_enum_controls(False)

    # =====================================================================
    # ENUM: add value
    # =====================================================================

    def _add_enum_value(self):
        item = self.list_types.currentItem()
        if not item:
            return

        name, kind = item.data(Qt.UserRole)
        if kind != "e":
            QMessageBox.warning(self, "Ошибка", "Это не ENUM тип.")
            return

        val = self.enum_add_input.text().strip()
        if not val:
            return

        try:
            sql = f"ALTER TYPE {name} ADD VALUE %s;"
            with self.db.cursor() as cur:
                cur.execute(sql, (val,))
            self.db.commit()

            self.enum_add_input.clear()
            self._load_enum_values(name)

            app_logger.info(f"enum {name}: added value '{val}'")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить значение:\n{e}")
            app_logger.error(e)

    # =====================================================================
    # delete type
    # =====================================================================

    def _delete_type(self):
        item = self.list_types.currentItem()
        if not item:
            return

        name, kind = item.data(Qt.UserRole)

        confirm = QMessageBox.question(
            self, "Удалить тип",
            f"Удалить тип {name}? Все таблицы, использующие его, перестанут работать.",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            sql = f"DROP TYPE {name} CASCADE;"
            self.db.execute_ddl(sql)

            self._load_types()
            self._set_details_empty()

            app_logger.info(f"type deleted: {name}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тип:\n{e}")
            app_logger.error(e)

    # =====================================================================
    # create enum dialog
    # =====================================================================

    def _create_enum_dialog(self):
        name, ok = self._prompt("Создать ENUM", "Имя типа:")
        if not ok or not name.strip():
            return

        values_str, ok = self._prompt("Создать ENUM", "Значения через запятую:")
        if not ok:
            return

        values = [v.strip() for v in values_str.split(",") if v.strip()]
        if not values:
            QMessageBox.warning(self, "Ошибка", "Нет значений.")
            return

        try:
            sql = f"CREATE TYPE {name} AS ENUM ({', '.join('%s' for _ in values)});"
            with self.db.cursor() as cur:
                cur.execute(sql, values)
            self.db.commit()

            self._load_types()
            app_logger.info(f"created enum {name}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать ENUM:\n{e}")
            app_logger.error(e)

    # =====================================================================
    # create composite dialog
    # =====================================================================

    def _create_composite_dialog(self):
        name, ok = self._prompt("Создать COMPOSITE", "Имя типа:")
        if not ok or not name.strip():
            return

        # поле ввода состава
        fields_str, ok = self._prompt(
            "Создать COMPOSITE",
            "Поля (формат: field1 type1, field2 type2 ...)"
        )
        if not ok:
            return

        fields = [f.strip() for f in fields_str.split(",") if f.strip()]
        if not fields:
            QMessageBox.warning(self, "Ошибка", "Не указаны поля.")
            return

        try:
            sql = f"CREATE TYPE {name} AS ({', '.join(fields)});"
            self.db.execute_ddl(sql)

            self._load_types()
            app_logger.info(f"created composite type {name}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать тип:\n{e}")
            app_logger.error(e)

    # =====================================================================
    # helpers
    # =====================================================================

    def _prompt(self, title, label):
        from PySide6.QtWidgets import QInputDialog
        return QInputDialog.getText(self, title, label)

    def _set_details_empty(self):
        self.table_details.setColumnCount(0)
        self.table_details.setRowCount(0)
        self._enable_enum_controls(False)

    def _enable_enum_controls(self, flag):
        self.enum_add_input.setEnabled(flag)
        self.btn_enum_add.setEnabled(flag)
