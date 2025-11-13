from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QWidget, QGroupBox,
    QHBoxLayout, QFormLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QCheckBox, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QWidget, QGroupBox,
    QHBoxLayout, QFormLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QCheckBox, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt


class AlterTableWindow(QDialog):
    """
    Окно изменения структуры таблицы.
    Полностью переписано под требования КР2.
    """
    def __init__(self, parent=None, db=None):
        super().__init__(parent)

        if db is None:
            raise RuntimeError("Ошибка. Нет подключения к БД. Откройте сначала соединение.")

        self.db = db  # объект HotelDB
        self.setModal(True)  # окно модальное
        self.setWindowTitle("Изменение структуры таблиц")
        self.resize(650, 800)

        # ==== ОСНОВНОЙ СКРОЛЛ ====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        self.layout = QVBoxLayout(inner)
        self.layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(inner)

        main = QVBoxLayout(self)
        main.addWidget(scroll)

        # ======================
        # 1) Выбор таблицы
        # ======================
        self.box_table = QComboBox()
        self.btn_refresh = QPushButton("Обновить")
        self.btn_refresh.clicked.connect(self.load_tables)

        gb = QGroupBox("Таблица")
        fl = QFormLayout()
        fl.addRow("Выбор:", self.box_table)
        fl.addRow("", self.btn_refresh)
        gb.setLayout(fl)
        self.layout.addWidget(gb)

        # Подгружаем таблицы сразу
        self.load_tables()

        # ======================
        # 2) Работа со столбцами
        # ======================
        self.build_column_section()

        # ======================
        # 3) Ограничения
        # ======================
        self.build_unique_section()
        self.build_check_section()
        self.build_fk_section()

        # ======================
        # 4) Переименовать таблицу
        # ======================
        self.build_table_rename_section()

        # ======================
        # Кнопка закрытия
        # ======================
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        self.layout.addWidget(btn_close)

        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addSpacerItem(spacer)

        # обновление при смене таблицы
        self.box_table.currentIndexChanged.connect(self.refresh_all_blocks)

    # ------------------------------------------------------------
    # Загрузка таблиц
    # ------------------------------------------------------------
    def load_tables(self):
        self.box_table.clear()
        try:
            tables = self.db.list_tables()
            self.box_table.addItems(tables)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    # ------------------------------------------------------------
    # Построение блока столбцов
    # ------------------------------------------------------------
    def build_column_section(self):
        gb = QGroupBox("Столбцы")
        lay = QVBoxLayout()

        # список столбцов
        self.col_list = QComboBox()

        # --- Добавить столбец ---
        add_gb = QGroupBox("Добавить столбец")
        add_fl = QFormLayout()
        self.add_col_name = QLineEdit()
        self.add_col_type = QComboBox()
        self.add_col_type.addItems(self.db.list_types())
        self.add_col_notnull = QCheckBox("NOT NULL")

        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.add_column)

        add_fl.addRow("Имя:", self.add_col_name)
        add_fl.addRow("Тип:", self.add_col_type)
        add_fl.addRow("", self.add_col_notnull)
        add_fl.addRow("", btn_add)
        add_gb.setLayout(add_fl)

        # --- Удалить столбец ---
        del_gb = QGroupBox("Удалить столбец")
        del_fl = QFormLayout()
        self.del_col = QComboBox()
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.delete_column)
        del_fl.addRow("Столбец:", self.del_col)
        del_fl.addRow("", btn_del)
        del_gb.setLayout(del_fl)

        # --- Переименовать столбец ---
        ren_gb = QGroupBox("Переименовать столбец")
        ren_fl = QFormLayout()
        self.ren_col_old = QComboBox()
        self.ren_col_new = QLineEdit()
        btn_ren = QPushButton("Переименовать")
        btn_ren.clicked.connect(self.rename_column)
        ren_fl.addRow("Старое имя:", self.ren_col_old)
        ren_fl.addRow("Новое имя:", self.ren_col_new)
        ren_fl.addRow("", btn_ren)
        ren_gb.setLayout(ren_fl)

        # --- Изменить тип ---
        type_gb = QGroupBox("Изменить тип")
        type_fl = QFormLayout()
        self.type_col = QComboBox()
        self.type_new = QComboBox()
        self.type_new.addItems(self.db.list_types())
        btn_type = QPushButton("Изменить")
        btn_type.clicked.connect(self.change_type)
        type_fl.addRow("Столбец:", self.type_col)
        type_fl.addRow("Новый тип:", self.type_new)
        type_fl.addRow("", btn_type)
        type_gb.setLayout(type_fl)

        # --- NOT NULL ---
        nn_gb = QGroupBox("NOT NULL / NULL")
        nn_fl = QFormLayout()
        self.nn_col = QComboBox()
        self.nn_flag = QCheckBox("NOT NULL")
        btn_nn = QPushButton("Применить")
        btn_nn.clicked.connect(self.change_notnull)
        nn_fl.addRow("Столбец:", self.nn_col)
        nn_fl.addRow("", self.nn_flag)
        nn_fl.addRow("", btn_nn)
        nn_gb.setLayout(nn_fl)

        lay.addWidget(add_gb)
        lay.addWidget(del_gb)
        lay.addWidget(ren_gb)
        lay.addWidget(type_gb)
        lay.addWidget(nn_gb)
        gb.setLayout(lay)
        self.layout.addWidget(gb)

    # ------------------------------------------------------------
    # UNIQUE
    # ------------------------------------------------------------
    def build_unique_section(self):
        gb = QGroupBox("UNIQUE")
        lay = QVBoxLayout()

        # добавить UNIQUE
        add_gb = QGroupBox("Добавить UNIQUE")
        add_fl = QFormLayout()
        self.unq_col = QComboBox()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.add_unique)
        add_fl.addRow("Столбец:", self.unq_col)
        add_fl.addRow("", btn_add)
        add_gb.setLayout(add_fl)

        # удалить UNIQUE
        del_gb = QGroupBox("Удалить UNIQUE")
        del_fl = QFormLayout()
        self.unq_list = QComboBox()
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.del_unique)
        del_fl.addRow("Ограничение:", self.unq_list)
        del_fl.addRow("", btn_del)
        del_gb.setLayout(del_fl)

        lay.addWidget(add_gb)
        lay.addWidget(del_gb)
        gb.setLayout(lay)
        self.layout.addWidget(gb)

    # ------------------------------------------------------------
    # CHECK
    # ------------------------------------------------------------
    def build_check_section(self):
        gb = QGroupBox("CHECK")
        lay = QVBoxLayout()

        # добавление
        add_gb = QGroupBox("Добавить CHECK")
        add_fl = QFormLayout()
        self.chk_col = QComboBox()
        self.chk_op = QComboBox()
        self.chk_op.addItems(["=", "!=", ">", ">=", "<", "<="])
        self.chk_val = QLineEdit()
        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.add_check)
        add_fl.addRow("Столбец:", self.chk_col)
        add_fl.addRow("Оператор:", self.chk_op)
        add_fl.addRow("Значение:", self.chk_val)
        add_fl.addRow("", btn_add)
        add_gb.setLayout(add_fl)

        # удаление
        del_gb = QGroupBox("Удалить CHECK")
        del_fl = QFormLayout()
        self.chk_list = QComboBox()
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.del_check)
        del_fl.addRow("Ограничение:", self.chk_list)
        del_fl.addRow("", btn_del)
        del_gb.setLayout(del_fl)

        lay.addWidget(add_gb)
        lay.addWidget(del_gb)
        gb.setLayout(lay)
        self.layout.addWidget(gb)

    # ------------------------------------------------------------
    # FOREIGN KEY
    # ------------------------------------------------------------
    def build_fk_section(self):
        gb = QGroupBox("FOREIGN KEY")
        lay = QVBoxLayout()

        # добавление
        add_gb = QGroupBox("Добавить FK")
        add_fl = QFormLayout()
        self.fk_local = QComboBox()
        self.fk_table = QComboBox()
        self.fk_ref_col = QComboBox()
        self.fk_on_del = QComboBox()
        self.fk_on_del.addItems(["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"])
        self.fk_on_upd = QComboBox()
        self.fk_on_upd.addItems(["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"])

        self.fk_table.currentIndexChanged.connect(self.update_fk_ref_columns)

        btn_add = QPushButton("Добавить")
        btn_add.clicked.connect(self.add_fk)

        add_fl.addRow("Локальный столбец:", self.fk_local)
        add_fl.addRow("Таблица ссылка:", self.fk_table)
        add_fl.addRow("Столбец ссылка:", self.fk_ref_col)
        add_fl.addRow("ON DELETE:", self.fk_on_del)
        add_fl.addRow("ON UPDATE:", self.fk_on_upd)
        add_fl.addRow("", btn_add)
        add_gb.setLayout(add_fl)

        # удаление
        del_gb = QGroupBox("Удалить FK")
        del_fl = QFormLayout()
        self.fk_list = QComboBox()
        btn_del = QPushButton("Удалить")
        btn_del.clicked.connect(self.del_fk)
        del_fl.addRow("Ограничение:", self.fk_list)
        del_fl.addRow("", btn_del)
        del_gb.setLayout(del_fl)

        lay.addWidget(add_gb)
        lay.addWidget(del_gb)
        gb.setLayout(lay)
        self.layout.addWidget(gb)

    # ------------------------------------------------------------
    # Переименование таблицы
    # ------------------------------------------------------------
    def build_table_rename_section(self):
        gb = QGroupBox("Переименовать таблицу")
        fl = QFormLayout()
        self.new_table_name = QLineEdit()
        btn = QPushButton("Переименовать")
        btn.clicked.connect(self.rename_table)
        fl.addRow("Новое имя:", self.new_table_name)
        fl.addRow("", btn)
        gb.setLayout(fl)
        self.layout.addWidget(gb)

    # ------------------------------------------------------------
    # Обновление столбцов и ограничений
    # ------------------------------------------------------------
    def refresh_all_blocks(self):
        table = self.box_table.currentText()
        if not table:
            return

        try:
            # столбцы
            cols = self.db.list_columns(table)
            names = [c["name"] for c in cols]

            for combo in [self.col_list, self.del_col, self.ren_col_old,
                          self.type_col, self.nn_col, self.unq_col,
                          self.chk_col, self.fk_local]:
                combo.clear()
                combo.addItems(names)

            # таблицы для FK
            self.fk_table.clear()
            self.fk_table.addItems(self.db.list_tables())
            self.update_fk_ref_columns()

            # UNIQUE
            self.unq_list.clear()
            unq = self.db.list_constraints_unique(table)
            for u in unq:
                if u["name"]:
                    label = f"{u['column']} — UNIQUE ({u['name']})"
                else:
                    label = f"{u['column']} — UNIQUE"
                self.unq_list.addItem(label, u["name"])

            # CHECK
            self.chk_list.clear()
            checks = self.db.list_constraints_check(table)
            for c in checks:
                expr = c["expression"]
                if c["name"]:
                    label = f"{expr} — CHECK ({c['name']})"
                else:
                    label = f"{expr} — CHECK"
                self.chk_list.addItem(label, c["name"])

            # FK
            self.fk_list.clear()
            fks = self.db.list_constraints_fk(table)
            for fk in fks:
                left = fk["column"]
                right = f"{fk['ref_table']}.{fk['ref_column']}"
                if fk["name"]:
                    label = f"{left} → {right} ( {fk['name']} )"
                else:
                    label = f"{left} → {right} — FK"
                self.fk_list.addItem(label, fk["name"])

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    # ==================== Дальше — Реальные действия ====================

    def add_column(self):
        table = self.box_table.currentText()
        name = self.add_col_name.text().strip()
        typ = self.add_col_type.currentText()
        nn = self.add_col_notnull.isChecked()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя столбца.")
            return

        q = f"ALTER TABLE {table} ADD COLUMN {name} {typ}"
        if nn:
            q += " NOT NULL"

        self.exec_alter_and_refresh(q)

    def delete_column(self):
        table = self.box_table.currentText()
        col = self.del_col.currentText()
        q = f"ALTER TABLE {table} DROP COLUMN {col} CASCADE"
        self.exec_alter_and_refresh(q)

    def rename_column(self):
        table = self.box_table.currentText()
        old = self.ren_col_old.currentText()
        new = self.ren_col_new.text().strip()
        if not new:
            QMessageBox.warning(self, "Ошибка", "Введите новое имя.")
            return
        q = f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}"
        self.exec_alter_and_refresh(q)

    def change_type(self):
        table = self.box_table.currentText()
        col = self.type_col.currentText()
        new_type = self.type_new.currentText()
        q = f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {new_type}"
        self.exec_alter_and_refresh(q)

    def change_notnull(self):
        table = self.box_table.currentText()
        col = self.nn_col.currentText()
        if self.nn_flag.isChecked():
            q = f"ALTER TABLE {table} ALTER COLUMN {col} SET NOT NULL"
        else:
            q = f"ALTER TABLE {table} ALTER COLUMN {col} DROP NOT NULL"
        self.exec_alter_and_refresh(q)

    # ---------------- UNIQUE ----------------

    def add_unique(self):
        table = self.box_table.currentText()
        col = self.unq_col.currentText()
        q = f"ALTER TABLE {table} ADD CONSTRAINT unq_{col} UNIQUE ({col})"
        self.exec_alter_and_refresh(q)

    def del_unique(self):
        table = self.box_table.currentText()
        cname = self.unq_list.currentData()  # None → системное имя
        if cname is None:
            QMessageBox.warning(self, "Ошибка", "Это ограничение создано системой, укажите имя вручную.")
            return
        q = f"ALTER TABLE {table} DROP CONSTRAINT {cname}"
        self.exec_alter_and_refresh(q)

    # ---------------- CHECK ----------------

    def add_check(self):
        table = self.box_table.currentText()
        col = self.chk_col.currentText()
        op = self.chk_op.currentText()
        val = self.chk_val.text().strip()

        if not val:
            QMessageBox.warning(self, "Ошибка", "Введите значение.")
            return

        # строковые значения берём в кавычки
        if not val.replace('.', '', 1).isdigit():
            val = f"'{val}'"

        q = f"ALTER TABLE {table} ADD CHECK ({col} {op} {val})"
        self.exec_alter_and_refresh(q)

    def del_check(self):
        table = self.box_table.currentText()
        cname = self.chk_list.currentData()
        if cname is None:
            QMessageBox.warning(self, "Ошибка", "Это ограничение создано системой, укажите имя вручную.")
            return
        q = f"ALTER TABLE {table} DROP CONSTRAINT {cname}"
        self.exec_alter_and_refresh(q)

    # ---------------- FOREIGN KEY ----------------

    def update_fk_ref_columns(self):
        table = self.fk_table.currentText()
        if not table:
            return
        try:
            cols = self.db.list_columns(table)
            names = [c["name"] for c in cols]
            self.fk_ref_col.clear()
            self.fk_ref_col.addItems(names)
        except:
            pass

    def add_fk(self):
        table = self.box_table.currentText()
        col = self.fk_local.currentText()
        rt = self.fk_table.currentText()
        rc = self.fk_ref_col.currentText()
        ondel = self.fk_on_del.currentText()
        onupd = self.fk_on_upd.currentText()

        cname = f"fk_{table}_{col}"

        q = (
            f"ALTER TABLE {table} "
            f"ADD CONSTRAINT {cname} FOREIGN KEY ({col}) "
            f"REFERENCES {rt}({rc}) "
            f"ON DELETE {ondel} ON UPDATE {onupd}"
        )

        self.exec_alter_and_refresh(q)

    def del_fk(self):
        table = self.box_table.currentText()
        cname = self.fk_list.currentData()
        if cname is None:
            QMessageBox.warning(self, "Ошибка", "Это ограничение создано системой, укажите имя вручную.")
            return
        q = f"ALTER TABLE {table} DROP CONSTRAINT {cname}"
        self.exec_alter_and_refresh(q)

    # ---------------- Table rename ----------------

    def rename_table(self):
        table = self.box_table.currentText()
        new = self.new_table_name.text().strip()
        if not new:
            QMessageBox.warning(self, "Ошибка", "Введите новое имя.")
            return
        q = f"ALTER TABLE {table} RENAME TO {new}"
        self.exec_alter_and_refresh(q)

    # ------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------
    def exec_alter_and_refresh(self, query):
        try:
            self.db.execute_alter(query)
            QMessageBox.information(self, "Готово", "Изменение применено.")
            self.refresh_all_blocks()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
