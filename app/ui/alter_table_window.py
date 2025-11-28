from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QHBoxLayout, QPushButton, QLineEdit,
    QMessageBox, QTableWidget, QTableWidgetItem, QGroupBox, QScrollArea, QWidget,
    QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.log.log import app_logger
from app.ui.theme import *

def setup_wide_combo(cmb: QComboBox, min_chars: int = 18, popup_width: int = 260):
    """
    Настройки для комбобоксов с длинными названиями колонок.
    """
    cmb.setMinimumContentsLength(min_chars)
    cmb.setSizeAdjustPolicy(QComboBox.AdjustToContents)
    cmb.setMinimumWidth(popup_width)
    cmb.view().setMinimumWidth(popup_width)


def style_button(btn: QPushButton):
    """Ограничиваем ширину, чтобы кнопки не растягивались на весь ряд."""
    btn.setMinimumWidth(150)
    btn.setMaximumWidth(190)


class AlterTableWindow(QDialog):
    """Окно изменения структуры таблиц: столбцы, ключи, UNIQUE / FK / CHECK."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Изменение структуры таблиц")
        # поуже, но высокое окно
        self.resize(1000, 680)

        # числовые колонки текущей таблицы (для простых CHECK)
        self.numeric_cols: list[str] = []

        # мягкая тёмная тема + пастельные кнопки
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
            }}
        """)

        self._build_ui()
        self._load_tables()

        if self.cb_table.count() > 0:
            self._load_table_info()


    def _build_ui(self):
        # основной layout с прокруткой
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll)

        container = QWidget()
        container.setStyleSheet(f"background-color: {WINDOW_BG};")
        scroll.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)  # расстояние между блоками

        # выбор таблицы
        top_row = QHBoxLayout()
        layout.addLayout(top_row)

        lbl_table = QLabel("Таблица для просмотра:")
        lbl_table.setFont(QFont("", 16, QFont.Bold))
        top_row.addWidget(lbl_table)

        self.cb_table = QComboBox()
        setup_wide_combo(self.cb_table)
        self.cb_table.currentTextChanged.connect(self._on_table_changed)
        top_row.addWidget(self.cb_table, 1)

        self.btn_reload = QPushButton("Обновить список")
        style_button(self.btn_reload)
        self.btn_reload.clicked.connect(self._load_tables)
        top_row.addWidget(self.btn_reload)

        # таблица колонок
        self.tbl_columns = QTableWidget()
        self.tbl_columns.setColumnCount(4)
        self.tbl_columns.setHorizontalHeaderLabels(["Имя столбца", "Тип", "Mожет быть NULL", "DEFAULT"])
        self.tbl_columns.verticalHeader().setVisible(False)
        self.tbl_columns.setMinimumHeight(200)

        # лок редактирования и выделение
        self.tbl_columns.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tbl_columns.setSelectionBehavior(QTableWidget.SelectRows)

        header = self.tbl_columns.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tbl_columns)

        # helper для групп — карточка в вертикальном формате
        def make_group(title: str) -> tuple[QGroupBox, QVBoxLayout]:
            gb = QGroupBox(title)
            ly = QVBoxLayout(gb)
            ly.setContentsMargins(10, 10, 10, 10)
            ly.setSpacing(6)
            return gb, ly


        gb_add, ly_add_v = make_group("Добавить столбец")

        row_add1 = QHBoxLayout()
        self.le_add_name = QLineEdit()
        self.le_add_name.setPlaceholderText("имя_столбца")
        row_add1.addWidget(QLabel("Имя:"))
        row_add1.addWidget(self.le_add_name)

        row_add2 = QHBoxLayout()
        self.le_add_type = QLineEdit()
        self.le_add_type.setPlaceholderText("тип данных, например VARCHAR(50)")

        row_add2.addWidget(QLabel("Тип:"))
        row_add2.addWidget(self.le_add_type)

        row_add3 = QHBoxLayout()
        self.cb_add_null = QComboBox()
        self.cb_add_null.addItems(["YES", "NO"])
        self.cb_add_null.setCurrentText("YES")

        self.le_add_default = QLineEdit()
        self.le_add_default.setPlaceholderText("None")

        row_add3.addWidget(QLabel("NULL:"))
        row_add3.addWidget(self.cb_add_null)
        row_add3.addWidget(QLabel("DEFAULT:"))
        row_add3.addWidget(self.le_add_default, 1)
        self.btn_add_col = QPushButton("Добавить")
        style_button(self.btn_add_col)
        self.btn_add_col.clicked.connect(self._add_column)

        row_add3.addStretch(1)  # отодвигаем вправо
        row_add3.addWidget(self.btn_add_col)

        ly_add_v.addLayout(row_add1)
        ly_add_v.addLayout(row_add2)
        ly_add_v.addLayout(row_add3)
        layout.addWidget(gb_add)


        gb_drop, ly_drop_v = make_group("Удалить столбец")

        row_drop1 = QHBoxLayout()
        self.cb_drop_col = QComboBox()
        setup_wide_combo(self.cb_drop_col)
        self.btn_drop_col = QPushButton("Удалить столбец")
        style_button(self.btn_drop_col)
        self.btn_drop_col.clicked.connect(self._drop_column)

        row_drop1.addWidget(QLabel("Столбец:"))
        row_drop1.addWidget(self.cb_drop_col)
        row_drop1.addStretch(1)
        row_drop1.addWidget(self.btn_drop_col)

        ly_drop_v.addLayout(row_drop1)
        layout.addWidget(gb_drop)


        gb_rt, ly_rt_v = make_group("Переименовать таблицу")

        row_rt1 = QHBoxLayout()
        self.le_new_table_name = QLineEdit()
        self.le_new_table_name.setPlaceholderText("новое_имя_таблицы")
        btn_rename_table = QPushButton("Переименовать таблицу")
        style_button(btn_rename_table)
        btn_rename_table.clicked.connect(self._rename_table)

        row_rt1.addWidget(QLabel("Новое имя:"))
        row_rt1.addWidget(self.le_new_table_name)
        row_rt1.addWidget(btn_rename_table, 0, Qt.AlignRight)

        ly_rt_v.addLayout(row_rt1)
        layout.addWidget(gb_rt)


        gb_rc, ly_rc_v = make_group("Переименовать столбец")

        row_rc1 = QHBoxLayout()
        self.cb_rename_col = QComboBox()
        setup_wide_combo(self.cb_rename_col)
        row_rc1.addWidget(QLabel("Столбец:"))
        row_rc1.addWidget(self.cb_rename_col)
        row_rc1.addStretch(1)

        row_rc2 = QHBoxLayout()
        self.le_new_col_name = QLineEdit()
        self.le_new_col_name.setPlaceholderText("новое_имя_столбца")
        btn_rename_col = QPushButton("Переименовать столбец")
        style_button(btn_rename_col)
        btn_rename_col.clicked.connect(self._rename_column)

        row_rc2.addWidget(QLabel("Новое имя:"))
        row_rc2.addWidget(self.le_new_col_name)
        row_rc2.addWidget(btn_rename_col, 0, Qt.AlignRight)

        ly_rc_v.addLayout(row_rc1)
        ly_rc_v.addLayout(row_rc2)
        layout.addWidget(gb_rc)

        gb_type, ly_type_v = make_group("Изменить тип столбца")

        row_type1 = QHBoxLayout()
        self.cb_type_col = QComboBox()
        setup_wide_combo(self.cb_type_col)

        row_type1.addWidget(QLabel("Столбец:"))
        row_type1.addWidget(self.cb_type_col)
        row_type1.addStretch(1)

        row_type2 = QHBoxLayout()

        self.cb_new_type = QComboBox()
        self.cb_new_type.setEditable(True)  # можно выбрать из списка или вписать своё
        setup_wide_combo(self.cb_new_type)
        self.cb_new_type.setInsertPolicy(QComboBox.NoInsert)
        self.cb_new_type.addItems([
            "INTEGER",
            "BIGINT",
            "SMALLINT",
            "NUMERIC(10,2)",
            "BOOLEAN",
            "DATE",
            "TIMESTAMP",
            "VARCHAR(50)",
            "VARCHAR(100)",
            "TEXT",
        ])

        # добавим в список пользовательские типы (ENUM / COMPOSITE),
        # чтобы их было удобно выбирать при ALTER COLUMN TYPE
        try:
            user_types = self.db.get_user_types()
        except Exception as e:
            app_logger.error(f"Не удалось получить пользовательские типы в ALTER: {e}")
            user_types = []

        if user_types:
            self.cb_new_type.insertSeparator(self.cb_new_type.count())
            for t in user_types:
                # показываем только имя типа; пользователь понимает, что это ENUM / COMPOSITE
                self.cb_new_type.addItem(t["name"])

        self.btn_type = QPushButton("Изменить тип")
        style_button(self.btn_type)
        self.btn_type.clicked.connect(self._change_type)

        row_type2.addWidget(QLabel("Новый тип:"))
        row_type2.addWidget(self.cb_new_type)
        row_type2.addStretch(1)
        row_type2.addWidget(self.btn_type)

        ly_type_v.addLayout(row_type1)
        ly_type_v.addLayout(row_type2)
        layout.addWidget(gb_type)


        gb_nn, ly_nn_v = make_group("NOT NULL")

        row_nn1 = QHBoxLayout()
        self.cb_not_null_col = QComboBox()
        setup_wide_combo(self.cb_not_null_col)
        row_nn1.addWidget(QLabel("Столбец:"))
        row_nn1.addWidget(self.cb_not_null_col)

        self.btn_set_not_null = QPushButton("SET NOT NULL")
        style_button(self.btn_set_not_null)
        self.btn_drop_not_null = QPushButton("DROP NOT NULL")
        style_button(self.btn_drop_not_null)

        self.btn_set_not_null.clicked.connect(self._set_not_null)
        self.btn_drop_not_null.clicked.connect(self._drop_not_null)

        row_nn1.addStretch(1)
        row_nn1.addWidget(self.btn_set_not_null)
        row_nn1.addWidget(self.btn_drop_not_null)

        ly_nn_v.addLayout(row_nn1)
        layout.addWidget(gb_nn)


        gb_u, ly_u_v = make_group("UNIQUE")

        row_u1 = QHBoxLayout()
        self.cb_unique_col = QComboBox()
        setup_wide_combo(self.cb_unique_col)
        row_u1.addWidget(QLabel("Столбец:"))
        row_u1.addWidget(self.cb_unique_col)
        row_u1.addStretch(1)

        row_u2 = QHBoxLayout()
        self.le_unique_name = QLineEdit()
        self.le_unique_name.setPlaceholderText("имя ограничения (опционально)")
        self.btn_add_unique = QPushButton("Добавить UNIQUE")
        style_button(self.btn_add_unique)
        self.btn_add_unique.clicked.connect(self._add_unique)

        row_u2.addWidget(QLabel("Имя:"))
        row_u2.addWidget(self.le_unique_name)
        row_u2.addWidget(self.btn_add_unique, 0, Qt.AlignRight)

        row_u3 = QHBoxLayout()
        self.cb_unique_drop = QComboBox()
        setup_wide_combo(self.cb_unique_drop)
        self.btn_drop_unique = QPushButton("Удалить UNIQUE")
        style_button(self.btn_drop_unique)
        self.btn_drop_unique.clicked.connect(self._drop_unique)

        row_u3.addWidget(QLabel("Существующие:"))
        row_u3.addWidget(self.cb_unique_drop)
        row_u3.addStretch(1)
        row_u3.addWidget(self.btn_drop_unique, 0, Qt.AlignRight)

        ly_u_v.addLayout(row_u1)
        ly_u_v.addLayout(row_u2)
        ly_u_v.addLayout(row_u3)
        layout.addWidget(gb_u)


        gb_fk, ly_fk_v = make_group("FOREIGN KEY")

        # строка 1 — выбор колонок и таблицы
        row_fk1 = QHBoxLayout()
        self.cb_fk_local_col = QComboBox()
        setup_wide_combo(self.cb_fk_local_col)
        self.cb_fk_ref_table = QComboBox()
        setup_wide_combo(self.cb_fk_ref_table)
        self.cb_fk_ref_table.currentTextChanged.connect(self._on_fk_ref_table_changed)

        row_fk1.addWidget(QLabel("Локальный столбец:"))
        row_fk1.addWidget(self.cb_fk_local_col)
        row_fk1.addStretch(1)
        row_fk1.addWidget(QLabel("Таблица-ссылка:"))
        row_fk1.addWidget(self.cb_fk_ref_table)
        row_fk1.addStretch(1)

        # строка 2 — столбец ссылки + ON DELETE/UPDATE + кнопка
        row_fk2 = QHBoxLayout()
        self.cb_fk_ref_col = QComboBox()
        setup_wide_combo(self.cb_fk_ref_col)

        self.cb_fk_on_delete = QComboBox()
        self.cb_fk_on_update = QComboBox()
        for cb in (self.cb_fk_on_delete, self.cb_fk_on_update):
            cb.addItems(["NO ACTION", "CASCADE", "SET NULL", "RESTRICT"])

        self.btn_add_fk = QPushButton("Добавить FK")
        style_button(self.btn_add_fk)
        self.btn_add_fk.clicked.connect(self._add_fk)

        row_fk2.addWidget(QLabel("Столбец-ссылка:"))
        row_fk2.addWidget(self.cb_fk_ref_col)
        lbl_on_delete = QLabel("    ON DELETE")
        lbl_on_delete.setStyleSheet(f"color: {ACCENT_SUCCESS}; font-weight: bold;")
        row_fk2.addWidget(lbl_on_delete)
        row_fk2.addWidget(self.cb_fk_on_delete)
        row_fk2.addStretch(1)
        lbl_on_update = QLabel("ON UPDATE")
        lbl_on_update.setStyleSheet(f"color: {ACCENT_SUCCESS}; font-weight: bold;")
        row_fk2.addWidget(lbl_on_update)
        row_fk2.addWidget(self.cb_fk_on_update)
        row_fk2.addStretch(1)
        row_fk2.addWidget(self.btn_add_fk, 0, Qt.AlignRight)

        # строка 3 — удаление FK
        row_fk3 = QHBoxLayout()
        self.cb_fk_drop = QComboBox()
        setup_wide_combo(self.cb_fk_drop)
        self.btn_drop_fk = QPushButton("Удалить FK")
        style_button(self.btn_drop_fk)
        self.btn_drop_fk.clicked.connect(self._drop_fk)

        row_fk3.addWidget(QLabel("Существующие FK:"))
        row_fk3.addWidget(self.cb_fk_drop)
        row_fk3.addStretch(1)
        row_fk3.addWidget(self.btn_drop_fk, 0, Qt.AlignRight)

        ly_fk_v.addLayout(row_fk1)
        ly_fk_v.addLayout(row_fk2)
        ly_fk_v.addLayout(row_fk3)
        layout.addWidget(gb_fk)



        gb_check, ly_check_v = make_group("CHECK-ограничения")

        # простое числовое ограничение
        row_simple1 = QHBoxLayout()
        self.cb_check_col = QComboBox()
        setup_wide_combo(self.cb_check_col)
        self.cb_check_op1 = QComboBox()
        self.cb_check_op1.addItems([">", ">=", "<", "<=", "=", "<>"])
        self.le_check_val1 = QLineEdit()
        self.le_check_val1.setPlaceholderText("значение")

        row_simple1.addWidget(QLabel("Колонка (числовая):"))
        row_simple1.addWidget(self.cb_check_col)
        row_simple1.addWidget(self.cb_check_op1)
        row_simple1.addWidget(self.le_check_val1)

        row_simple2 = QHBoxLayout()
        self.le_check_name = QLineEdit()
        self.le_check_name.setPlaceholderText("имя CHECK (опционально)")
        self.btn_add_simple_check = QPushButton("Добавить простое CHECK")
        style_button(self.btn_add_simple_check)
        self.btn_add_simple_check.setMinimumWidth(200)
        self.btn_add_simple_check.setMaximumWidth(250)
        self.btn_add_simple_check.clicked.connect(self._add_simple_check)

        row_simple2.addWidget(QLabel("Имя:"))
        row_simple2.addWidget(self.le_check_name)
        row_simple2.addWidget(self.btn_add_simple_check, 0, Qt.AlignRight)

        ly_check_v.addLayout(row_simple1)
        ly_check_v.addLayout(row_simple2)

        # произвольное выражение
        ly_check_v.addWidget(QLabel("Произвольное условие (для сложных случаев):"))

        example_lbl = QLabel('Например:  price > 0 AND price < 100000')
        example_lbl.setFont(QFont("", 9))
        ly_check_v.addWidget(example_lbl)

        row_custom = QHBoxLayout()
        self.le_check_custom_expr = QLineEdit()
        self.le_check_custom_expr.setPlaceholderText(
            "любой валидный фрагмент SQL-предиката, например total >= 0 AND total <= 100"
        )
        self.btn_add_custom_check = QPushButton("Добавить произвольный CHECK")
        style_button(self.btn_add_custom_check)
        self.btn_add_custom_check.setMinimumWidth(200)
        self.btn_add_custom_check.setMaximumWidth(250)
        self.btn_add_custom_check.clicked.connect(self._add_custom_check)

        row_custom.addWidget(self.le_check_custom_expr, 1)
        row_custom.addWidget(self.btn_add_custom_check, 0, Qt.AlignRight)

        ly_check_v.addLayout(row_custom)

        # существующие CHECK
        row_exist = QHBoxLayout()
        self.cb_check_drop = QComboBox()
        setup_wide_combo(self.cb_check_drop)
        self.btn_drop_check = QPushButton("Удалить CHECK")
        style_button(self.btn_drop_check)
        self.btn_drop_check.clicked.connect(self._drop_check)

        row_exist.addWidget(QLabel("Существующие:"))
        row_exist.addWidget(self.cb_check_drop, 1)
        row_exist.addWidget(self.btn_drop_check, 0, Qt.AlignRight)

        ly_check_v.addLayout(row_exist)

        layout.addWidget(gb_check)
        layout.addStretch(1)



    def _load_tables(self):
        try:
            tables = self.db.get_tables()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список таблиц:\n{e}")
            app_logger.error(e)
            tables = []

        current = self.cb_table.currentText() if hasattr(self, "cb_table") else ""
        self.cb_table.blockSignals(True)
        self.cb_table.clear()
        self.cb_table.addItems(tables)
        self.cb_table.blockSignals(False)

        # FK-целевые таблицы
        if hasattr(self, "cb_fk_ref_table"):
            self.cb_fk_ref_table.blockSignals(True)
            self.cb_fk_ref_table.clear()
            self.cb_fk_ref_table.addItems(tables)
            self.cb_fk_ref_table.blockSignals(False)
            self._on_fk_ref_table_changed()

        if current and current in tables:
            self.cb_table.setCurrentText(current)
        elif self.cb_table.count() > 0:
            self._load_table_info()

    def _on_table_changed(self, _):
        self._load_table_info()

    def _load_table_info(self):
        table = self.cb_table.currentText()
        if not table:
            return

        try:
            cols = self.db.get_table_columns(table)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить колонки:\n{e}")
            app_logger.error(e)
            return

        self.tbl_columns.setRowCount(len(cols))
        self.numeric_cols = []
        col_names: list[str] = []

        for row, col in enumerate(cols):
            name = col.get("column_name")
            dtype = col.get("data_type")
            nullable = col.get("is_nullable")
            default = col.get("column_default")

            col_names.append(name)

            self.tbl_columns.setItem(row, 0, QTableWidgetItem(str(name)))
            self.tbl_columns.setItem(row, 1, QTableWidgetItem(str(dtype)))
            self.tbl_columns.setItem(row, 2, QTableWidgetItem(str(nullable)))
            self.tbl_columns.setItem(row, 3, QTableWidgetItem(str(default)))

            dt_lower = (dtype or "").lower()
            if any(x in dt_lower for x in ("integer", "smallint", "bigint", "numeric", "real", "double")):
                self.numeric_cols.append(name)

        # обновляем комбобоксы с колонками
        for combo in (
            self.cb_drop_col,
            self.cb_rename_col,
            self.cb_type_col,
            self.cb_not_null_col,
            self.cb_unique_col,
            self.cb_fk_local_col,
        ):
            combo.clear()
            combo.addItems(col_names)

        # числовые колонки – только они в списке для простого CHECK
        self.cb_check_col.clear()
        self.cb_check_col.addItems(self.numeric_cols)

        self._load_constraints()

    def _on_fk_ref_table_changed(self, *_):
        table = self.cb_fk_ref_table.currentText()
        if not table:
            return
        try:
            cols = self.db.get_table_columns(table)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить колонки для {table}:\n{e}")
            app_logger.error(e)
            return

        self.cb_fk_ref_col.clear()
        self.cb_fk_ref_col.addItems([c.get("column_name") for c in cols])

    def _load_constraints(self):
        #UNIQUE, CHECK, FK для выбранной таблицы
        table = self.cb_table.currentText()
        if not table:
            return

        # UNIQUE
        self.unique_constraints = []
        self.cb_unique_drop.clear()

        # FK
        self.fk_constraints = []
        self.cb_fk_drop.clear()

        # CHECK
        self.check_constraints = []
        self.cb_check_drop.clear()

        try:
            with self.db.cursor() as cur:
                # UNIQUE
                cur.execute(
                    """
                    SELECT tc.constraint_name, kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = %s
                      AND tc.constraint_type = 'UNIQUE'
                    ORDER BY kcu.ordinal_position;
                    """,
                    (table,),
                )
                self.unique_constraints = cur.fetchall()

                # FK
                cur.execute(
                    """
                    SELECT
                        tc.constraint_name,
                        kcu.column_name AS local_column,
                        ccu.table_name AS foreign_table,
                        ccu.column_name AS foreign_column
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                     AND ccu.table_schema = tc.table_schema
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = %s
                      AND tc.constraint_type = 'FOREIGN KEY';
                    """,
                    (table,),
                )
                self.fk_constraints = cur.fetchall()

                # CHECK
                cur.execute(
                    """
                    SELECT con.constraint_name, con.check_clause
                    FROM information_schema.check_constraints con
                    JOIN information_schema.table_constraints tc
                      ON con.constraint_name = tc.constraint_name
                    WHERE tc.table_schema = 'public'
                      AND tc.table_name = %s;
                    """,
                    (table,),
                )
                raw_checks = cur.fetchall()

        except Exception as e:
            app_logger.error(f"Ошибка загрузки ограничений для {table}: {e}")
            return

        for uc in self.unique_constraints:
            name = uc.get("constraint_name")
            col = uc.get("column_name")
            text = f"{name} ({col})"
            self.cb_unique_drop.addItem(text, userData=name)

        for fk in self.fk_constraints:
            name = fk.get("constraint_name")
            loc = fk.get("local_column")
            ft = fk.get("foreign_table")
            fc = fk.get("foreign_column")
            text = f"{name}: {loc} → {ft}.{fc}"
            self.cb_fk_drop.addItem(text, userData=name)

        # фильтруем системные NOT NULL CHECK-и
        self.check_constraints = []
        for ch in raw_checks:
            clause = (ch.get("check_clause") or "").upper()
            simplified = clause.replace("(", "").replace(")", "").strip()
            if simplified.endswith("IS NOT NULL"):
                continue
            self.check_constraints.append(ch)

        for ch in self.check_constraints:
            name = ch.get("constraint_name")
            clause = ch.get("check_clause")
            text = f"{name}: {clause}"
            if len(text) > 80:
                text = text[:77] + "..."
            idx = self.cb_check_drop.count()
            self.cb_check_drop.addItem(text, userData=name)
            # полный текст в тултипе
            self.cb_check_drop.setItemData(idx, f"{name}: {clause}", Qt.ToolTipRole)


    # операции ALTER TABLE
    def _add_column(self):
        table = self.cb_table.currentText()
        name = self.le_add_name.text().strip()
        col_type = self.le_add_type.text().strip()
        nullable = self.cb_add_null.currentText()
        default = self.le_add_default.text().strip()

        if not table or not name or not col_type:
            QMessageBox.warning(self, "Внимание", "Укажите таблицу, имя и тип столбца.")
            return

        sql_parts = [f'ALTER TABLE public."{table}" ADD COLUMN "{name}" {col_type}']
        # если указано
        if nullable == "NO":
            sql_parts.append("NOT NULL")
        if default:
            sql_parts.append(f"DEFAULT {default}")

        sql = " ".join(sql_parts) + ";"

        self._execute(sql, f"Столбец {name} добавлен.")


    def _drop_column(self):
        table = self.cb_table.currentText()
        col = self.cb_drop_col.currentText()

        if not table or not col:
            QMessageBox.warning(self, "Внимание", "Выберите столбец для удаления.")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить столбец {col} из таблицы {table}?",
        )
        if reply != QMessageBox.Yes:
            return

        sql = f'ALTER TABLE public."{table}" DROP COLUMN "{col}" CASCADE;'
        self._execute(sql, f"Столбец {col} удалён.")

    def _rename_table(self):
        old = self.cb_table.currentText()
        new = self.le_new_table_name.text().strip()
        if not old or not new:
            QMessageBox.warning(self, "Внимание", "Укажите новое имя таблицы.")
            return

        sql = f'ALTER TABLE public."{old}" RENAME TO "{new}";'
        self._execute(sql, f"Таблица {old} переименована в {new}.")
        self._load_tables()
        self.cb_table.setCurrentText(new)

    def _rename_column(self):
        table = self.cb_table.currentText()
        old = self.cb_rename_col.currentText()
        new = self.le_new_col_name.text().strip()

        if not table or not old or not new:
            QMessageBox.warning(self, "Внимание", "Выберите столбец и укажите новое имя.")
            return

        sql = f'ALTER TABLE public."{table}" RENAME COLUMN "{old}" TO "{new}";'
        self._execute(sql, f"Столбец {old} переименован в {new}.")

    def _change_type(self):
        table = self.cb_table.currentText()
        col = self.cb_type_col.currentText()
        new_type = self.cb_new_type.currentText().strip()

        if not table or not col or not new_type:
            QMessageBox.warning(self, "Внимание", "Выберите столбец и укажите новый тип.")
            return

        sql = f'ALTER TABLE public."{table}" ALTER COLUMN "{col}" TYPE {new_type};'
        self._execute(sql, f"Тип столбца {col} изменён на {new_type}.")

    def _set_not_null(self):
        table = self.cb_table.currentText()
        col = self.cb_not_null_col.currentText()
        if not table or not col:
            QMessageBox.warning(self, "Внимание", "Выберите столбец.")
            return

        sql = f'ALTER TABLE public."{table}" ALTER COLUMN "{col}" SET NOT NULL;'
        self._execute(sql, f"Для {col} установлено NOT NULL.")

    def _drop_not_null(self):
        table = self.cb_table.currentText()
        col = self.cb_not_null_col.currentText()
        if not table or not col:
            QMessageBox.warning(self, "Внимание", "Выберите столбец.")
            return

        sql = f'ALTER TABLE public."{table}" ALTER COLUMN "{col}" DROP NOT NULL;'
        self._execute(sql, f"Для {col} снято NOT NULL.")

    def _add_unique(self):
        table = self.cb_table.currentText()
        col = self.cb_unique_col.currentText()
        name = self.le_unique_name.text().strip()

        if not table or not col:
            QMessageBox.warning(self, "Внимание", "Выберите столбец.")
            return

        if not name:
            name = f"uq_{table}_{col}"

        sql = f'ALTER TABLE public."{table}" ADD CONSTRAINT "{name}" UNIQUE ("{col}");'
        self._execute(sql, f"UNIQUE {name} добавлен.")
        self._load_constraints()

    def _drop_unique(self):
        table = self.cb_table.currentText()
        if not table:
            return
        idx = self.cb_unique_drop.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Внимание", "Нет UNIQUE-ограничений для удаления.")
            return
        name = self.cb_unique_drop.currentData()
        if not name:
            text = self.cb_unique_drop.currentText()
            name = text.split(" ", 1)[0]

        sql = f'ALTER TABLE public."{table}" DROP CONSTRAINT "{name}";'
        self._execute(sql, f"UNIQUE {name} удалён.")
        self._load_constraints()

    def _add_fk(self):
        table = self.cb_table.currentText()
        local = self.cb_fk_local_col.currentText()
        ref_table = self.cb_fk_ref_table.currentText()
        ref_col = self.cb_fk_ref_col.currentText()
        on_delete = self.cb_fk_on_delete.currentText()
        on_update = self.cb_fk_on_update.currentText()

        if not table or not local or not ref_table or not ref_col:
            QMessageBox.warning(self, "Внимание", "Заполните все поля для FK.")
            return

        name = f"fk_{table}_{local}_{ref_table}_{ref_col}"

        sql = (
            f'ALTER TABLE public."{table}" '
            f'ADD CONSTRAINT "{name}" FOREIGN KEY ("{local}") '
            f'REFERENCES public."{ref_table}" ("{ref_col}") '
            f'ON DELETE {on_delete} ON UPDATE {on_update};'
        )
        self._execute(sql, f"FK {name} добавлен.")
        self._load_constraints()

    def _drop_fk(self):
        table = self.cb_table.currentText()
        if not table:
            return
        idx = self.cb_fk_drop.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Внимание", "Нет FK для удаления.")
            return
        name = self.cb_fk_drop.currentData()
        if not name:
            text = self.cb_fk_drop.currentText()
            name = text.split(":", 1)[0]

        sql = f'ALTER TABLE public."{table}" DROP CONSTRAINT "{name}";'
        self._execute(sql, f"FK {name} удалён.")
        self._load_constraints()

    # CHECK

    def _add_simple_check(self):
        # одна колонка, один оператор, одно число
        table = self.cb_table.currentText()
        col = self.cb_check_col.currentText()
        op = (self.cb_check_op1.currentText() or "").strip()
        val_raw = self.le_check_val1.text().strip()
        name = self.le_check_name.text().strip()

        if not table or not col:
            QMessageBox.warning(self, "Внимание", "Выберите таблицу и числовой столбец.")
            return
        if not op or not val_raw:
            QMessageBox.warning(self, "Внимание", "Заполните оператор и значение.")
            return

        if col not in self.numeric_cols:
            QMessageBox.warning(self, "Внимание", "Простое CHECK доступно только для числовых столбцов.")
            return

        val_norm = val_raw.replace(",", ".")
        try:
            float(val_norm)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Значение должно быть числом.")
            return

        expr = f'"{col}" {op} {val_norm}'

        if not name:
            name = f"ck_{table}_{col}_{len(self.check_constraints) + 1}"

        sql = f'ALTER TABLE public."{table}" ADD CONSTRAINT "{name}" CHECK ({expr});'
        self._execute(sql, f"CHECK {name} добавлен.")
        self.le_check_val1.clear()
        self.le_check_name.clear()
        self._load_constraints()

    def _add_custom_check(self):
        # пользователь вводит руками
        table = self.cb_table.currentText()
        expr = (self.le_check_custom_expr.text() or "").strip()
        name = self.le_check_name.text().strip()

        if not table:
            QMessageBox.warning(self, "Внимание", "Выберите таблицу.")
            return
        if not expr:
            QMessageBox.warning(self, "Внимание", "Введите выражение для CHECK.")
            return

        if not name:
            name = f"ck_{table}_{len(self.check_constraints) + 1}"

        sql = f'ALTER TABLE public."{table}" ADD CONSTRAINT "{name}" CHECK ({expr});'
        self._execute(sql, f"CHECK {name} добавлен.")
        self.le_check_custom_expr.clear()
        self.le_check_name.clear()
        self._load_constraints()

    def _drop_check(self):
        table = self.cb_table.currentText()
        if not table:
            return
        idx = self.cb_check_drop.currentIndex()
        if idx < 0:
            QMessageBox.warning(self, "Внимание", "Нет CHECK-ограничений для удаления.")
            return
        name = self.cb_check_drop.currentData()
        if not name:
            text = self.cb_check_drop.currentText()
            name = text.split(":", 1)[0]

        sql = f'ALTER TABLE public."{table}" DROP CONSTRAINT "{name}";'
        self._execute(sql, f"CHECK {name} удалён.")
        self._load_constraints()


    def _execute(self, sql: str, msg: str):
        try:
            self.db.execute_ddl(sql)
            QMessageBox.information(self, "Готово", msg)
            app_logger.info(sql)
            self._load_table_info()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            app_logger.error(e)
