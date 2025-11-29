from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QComboBox   # ← добавили QDialog, QComboBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from app.log.log import app_logger
from app.ui.theme import *


class CompositeFieldsDialog(QDialog):
    """
    Диалог ввода полей составного типа:
    несколько строк вида: имя_поля + тип данных (из списка или вручную).
    """

    def __init__(self, base_types: list[str], user_types: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.base_types = base_types
        self.user_types = user_types or []
        self._fields: list[tuple[str, str]] = []

        self.setWindowTitle("Поля составного типа")
        self.resize(440, 260)
        self.setModal(True)

        # немножко красоты в духе остального приложения
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {WINDOW_BG};
                color: {TEXT_MAIN};
            }}
            QLineEdit, QComboBox {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 2px solid {CARD_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }}
            QLineEdit::placeholder {{
                color: {TEXT_MUTED};
                font-style: italic;
            }}
            QPushButton {{
                background-color: {BTN_BG};
                color: {BTN_TEXT};
                border: 1px solid {BTN_BORDER};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {BTN_BG_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BTN_BG_PRESSED};
            }}
        """)

        main = QVBoxLayout(self)
        main.setContentsMargins(16, 16, 16, 16)
        main.setSpacing(10)

        lbl = QLabel("Добавьте поля составного типа.\nКаждая строка: имя поля и тип данных.")
        lbl.setWordWrap(True)
        main.addWidget(lbl)

        # сюда кладём строки с полями
        self.fields_layout = QVBoxLayout()
        self.fields_layout.setSpacing(6)
        main.addLayout(self.fields_layout, 1)

        # кнопка "Добавить поле"
        btn_add_row = QPushButton("Добавить поле")
        btn_add_row.clicked.connect(self._add_row)
        main.addWidget(btn_add_row, alignment=Qt.AlignLeft)

        # нижние кнопки OK / Cancel
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Отмена")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        bottom.addWidget(self.btn_ok)
        bottom.addWidget(self.btn_cancel)
        main.addLayout(bottom)

        self._rows: list[tuple[QLineEdit, QComboBox]] = []
        self._add_row()  # хотя бы одна строка по умолчанию

    def _add_row(self):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("имя_поля")

        type_combo = QComboBox()
        type_combo.setEditable(True)                  # можно выбрать или вписать своё
        type_combo.addItems(self.base_types)
        if self.user_types:
            type_combo.insertSeparator(type_combo.count())
            type_combo.addItems(self.user_types)

        row_layout.addWidget(QLabel("Имя:"))
        row_layout.addWidget(name_edit, 1)
        row_layout.addWidget(QLabel("Тип:"))
        row_layout.addWidget(type_combo, 1)

        self.fields_layout.addWidget(row_widget)
        self._rows.append((name_edit, type_combo))

    def accept(self):
        fields: list[tuple[str, str]] = []
        for name_edit, type_combo in self._rows:
            fname = (name_edit.text() or "").strip()
            ftype = (type_combo.currentText() or "").strip()

            # полностью пустую строку игнорируем
            if not fname and not ftype:
                continue

            # если одна часть заполнена, а другая нет — ругаемся
            if not fname or not ftype:
                QMessageBox.warning(
                    self,
                    "Неверный ввод",
                    "У каждого поля должно быть и имя, и тип данных."
                )
                return

            fields.append((fname, ftype))

        if not fields:
            QMessageBox.warning(self, "Нет полей", "Нужно указать хотя бы одно поле.")
            return

        self._fields = fields
        super().accept()

    def get_fields(self) -> list[tuple[str, str]]:
        return getattr(self, "_fields", [])


# окно управления пользовательскими типами (ENUM + COMPOSITE)
class TypesWindow(QMainWindow):
    """
    * список пользовательских типов (исключая системные схемы)
    * значения ENUM
    * поля составного типа (COMPOSITE)
    * новый ENUM
    * новый COMPOSITE
    * добавить новое значение к существующему ENUM
    * удалить тип (DROP TYPE [CASCADE])
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Пользовательские типы (ENUM / COMPOSITE)")
        self.resize(900, 580)

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
                """)

        self.list_types = None
        self.table_details = None
        self.enum_add_input = None
        self.btn_enum_add = None
        self.btn_enum_delete = None
        self.lbl_details_title = None

        self._build_ui()
        self._load_types()


    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Пользовательские типы данных в PostgreSQL")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        root.addWidget(title)

        subtitle = QLabel("ENUM и составные типы (COMPOSITE). Создание, просмотр, управление.")
        root.addWidget(subtitle)

        # верхняя панель с кнопками
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_refresh = QPushButton("Обновить список")
        self.btn_new_enum = QPushButton("Создать ENUM")
        self.btn_new_composite = QPushButton("Создать COMPOSITE")
        self.btn_drop_type = QPushButton("Удалить тип")

        for b in (self.btn_refresh, self.btn_new_enum, self.btn_new_composite, self.btn_drop_type):
            b.setMinimumWidth(150)
            b.setCursor(Qt.PointingHandCursor)

        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch(1)
        toolbar.addWidget(self.btn_new_enum)
        toolbar.addWidget(self.btn_new_composite)
        toolbar.addWidget(self.btn_drop_type)

        root.addLayout(toolbar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 8, 0, 0)
        body.setSpacing(14)
        root.addLayout(body, 1)

        # левая колонка — список типов
        left_box = QVBoxLayout()
        left_box.setSpacing(6)
        lbl_types = QLabel("Пользовательские типы")
        left_box.addWidget(lbl_types)

        self.list_types = QListWidget()
        left_box.addWidget(self.list_types, 1)
        body.addLayout(left_box, 1)

        # правая колонка — детали выбранного типа
        right_box = QVBoxLayout()
        right_box.setSpacing(6)

        self.lbl_details_title = QLabel("Детали типа")
        right_box.addWidget(self.lbl_details_title)

        self.table_details = QTableWidget()
        self.table_details.setColumnCount(0)
        self.table_details.setRowCount(0)
        self.table_details.setEditTriggers(QTableWidget.NoEditTriggers)

        header = self.table_details.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table_details.verticalHeader().setVisible(False)

        right_box.addWidget(self.table_details, 1)
        # блок для работы со значениями ENUM
        enum_row = QHBoxLayout()
        enum_row.setSpacing(6)

        self.enum_add_input = QLineEdit()
        self.enum_add_input.setPlaceholderText("Новое значение ENUM…")
        self.enum_add_input.textChanged.connect(self._on_enum_input_changed)

        self.btn_enum_add = QPushButton("Добавить")
        self.btn_enum_add.setCursor(Qt.PointingHandCursor)
        self.btn_enum_add.setEnabled(False)

        self.btn_enum_delete = QPushButton("Удалить выбранное")
        self.btn_enum_delete.setCursor(Qt.PointingHandCursor)

        enum_row.addWidget(self.enum_add_input, 1)
        enum_row.addWidget(self.btn_enum_add)
        enum_row.addWidget(self.btn_enum_delete)

        right_box.addLayout(enum_row)

        body.addLayout(right_box, 2)

        # изначально кнопки ENUM недоступны
        self._enable_enum_controls(False)

        # сигналы
        self.btn_refresh.clicked.connect(self._load_types)
        self.btn_new_enum.clicked.connect(self._on_new_enum)
        self.btn_new_composite.clicked.connect(self._on_new_composite)
        self.btn_drop_type.clicked.connect(self._on_drop_type)
        self.btn_enum_add.clicked.connect(self._on_enum_add)
        self.btn_enum_delete.clicked.connect(self._on_enum_delete_value)
        self.list_types.currentItemChanged.connect(self._on_type_selected)
    # ------------------------------------------------------------------
    # Загрузка списка типов и отображение деталей
    # ------------------------------------------------------------------

    def _load_types(self):
        self.list_types.clear()
        self._set_details_empty()

        try:
            types = self.db.get_user_types()
        except Exception as e:
            app_logger.error(f"Не удалось получить список пользовательских типов: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список типов:\n{e}")
            return

        for t in types:
            name = t["name"]
            kind = t["kind"]
            schema = t["schema"]

            human = "ENUM" if kind == "e" else "COMPOSITE"
            item = QListWidgetItem(f"{schema}.{name}   ({human})")
            # кладём словарь, чтобы не строить строки назад
            item.setData(Qt.UserRole, t)
            self.list_types.addItem(item)

        if self.list_types.count() == 0:
            self.lbl_details_title.setText("Детали типа (пользовательские типы не найдены)")
        else:
            self.lbl_details_title.setText("Детали типа")

    def _on_type_selected(self, current: QListWidgetItem, _previous: QListWidgetItem):
        # пользователь выбирает тип слева — показываем детали
        if current is None:
            self._set_details_empty()
            return

        t = current.data(Qt.UserRole) or {}
        name = t.get("name")
        kind = t.get("kind")

        if not name or not kind:
            self._set_details_empty()
            return

        if kind == "e":
            self._show_enum_details(name, t.get("schema"))
        elif kind == "c":
            self._show_composite_details(name, t.get("schema"))
        else:
            self._set_details_empty()

    def _show_enum_details(self, type_name: str, schema: str | None):
        # значения ENUM
        try:
            labels = self.db.get_enum_labels(type_name)
        except Exception as e:
            app_logger.error(f"Не удалось получить значения ENUM {type_name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить значения ENUM:\n{e}")
            self._set_details_empty()
            return

        self.table_details.clear()
        self.table_details.setColumnCount(1)
        self.table_details.setHorizontalHeaderLabels(["Значение"])
        self.table_details.setRowCount(len(labels))

        for row, label in enumerate(labels):
            self.table_details.setItem(row, 0, QTableWidgetItem(label))

        # авто выделяем первую строку, чтобы кнопка сразу работала
        if self.table_details.rowCount() > 0:
            self.table_details.setCurrentCell(0, 0)

        self._enable_enum_controls(True)
        self.lbl_details_title.setText(f"ENUM {schema + '.' if schema else ''}{type_name}")


    def _show_composite_details(self, type_name: str, schema: str | None):
        # поля составного типа
        try:
            fields = self.db.get_composite_fields(type_name)
        except Exception as e:
            app_logger.error(f"Не удалось получить поля COMPOSITE {type_name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить поля составного типа:\n{e}")
            self._set_details_empty()
            return

        self.table_details.clear()
        self.table_details.setColumnCount(2)
        self.table_details.setHorizontalHeaderLabels(["Поле", "Тип"])
        self.table_details.setRowCount(len(fields))

        for row, f in enumerate(fields):
            self.table_details.setItem(row, 0, QTableWidgetItem(f["name"]))
            self.table_details.setItem(row, 1, QTableWidgetItem(f["type"]))

        self._enable_enum_controls(False)
        self.lbl_details_title.setText(f"COMPOSITE {schema + '.' if schema else ''}{type_name}")


    def _on_new_enum(self):
        # создание нового ENUM через два простых ввода
        name, ok = self._prompt("Создать ENUM", "Имя нового ENUM-типа (без схемы):")
        if not ok:
            return

        name = name.strip()
        if not name:
            return

        values_str, ok = self._prompt(
            "Создать ENUM",
            "Список значений через запятую:\nпример: standard, semi_lux, lux"
        )
        if not ok:
            return

        values = [v.strip() for v in (values_str or "").split(",") if v.strip()]
        if not values:
            QMessageBox.warning(self, "Предупреждение", "Нужно указать хотя бы одно значение ENUM.")
            return

        try:
            self.db.create_enum_type(name, values)
        except Exception as e:
            app_logger.error(f"Ошибка создания ENUM {name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать ENUM:\n{e}")
            return

        self._load_types()

    def _on_new_composite(self):
        # 1) спрашиваем имя типа
        name, ok = self._prompt("Создать COMPOSITE", "Имя нового составного типа (без схемы):")
        if not ok:
            return

        name = (name or "").strip()
        if not name:
            return

        # 2) подготовим список базовых типов + пользовательских (ENUM/COMPOSITE),
        #    чтобы можно было выбрать тип как в окне изменения структуры
        base_types = [
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
        ]

        try:
            user_types = self.db.get_user_types()
            user_type_names = [t["name"] for t in user_types]
        except Exception as e:
            app_logger.error(f"Не удалось получить пользовательские типы при создании COMPOSITE: {e}")
            user_type_names = []

        # 3) открываем красивый диалог ввода полей
        dlg = CompositeFieldsDialog(base_types, user_type_names, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return

        fields = dlg.get_fields()
        if not fields:
            return

        # 4) создаём тип в базе
        try:
            self.db.create_composite_type(name, fields)
        except Exception as e:
            app_logger.error(f"Ошибка создания COMPOSITE {name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать составной тип:\n{e}")
            return

        self._load_types()

    def _on_enum_add(self):
        # новое значение в выбранный ENUM
        current = self.list_types.currentItem()
        if current is None:
            return

        t = current.data(Qt.UserRole) or {}
        if t.get("kind") != "e":
            return  # защита от случайного нажатия

        type_name = t["name"]
        value = (self.enum_add_input.text() or "").strip()
        if not value: return

        try:
            self.db.add_enum_value(type_name, value)
        except Exception as e:
            app_logger.error(f"Ошибка добавления значения в ENUM {type_name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить значение:\n{e}")
            return

        self.enum_add_input.clear()
        self._show_enum_details(type_name, t.get("schema"))

    def _on_enum_delete_value(self):
         # удаление выбранного значения
        current = self.list_types.currentItem()
        if current is None:
            return

        t = current.data(Qt.UserRole) or {}
        if t.get("kind") != "e":
            return  # нажали, когда выбран не ENUM

        type_name = t["name"]

        item = self.table_details.currentItem()
        if item is None:
            QMessageBox.warning(
                self,
                "Нет выбранного значения",
                "Сначала выберите строку в таблице значений ENUM справа."
            )
            return

        value = (item.text() or "").strip()
        if not value:
            return

        res = QMessageBox.question(
            self,
            "Удалить значение ENUM",
            f"Удалить значение {value!r} из ENUM {type_name}?\n\n"
            f"Если это значение уже используется в таблицах,\n"
            f"PostgreSQL может запретить его удаление.",
        )
        if res != QMessageBox.Yes:
            return

        try:
            self.db.drop_enum_value(type_name, value)
        except Exception as e:
            app_logger.error(f"Ошибка удаления значения {value!r} из ENUM {type_name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить значение:\n{e}")
            return

        # перечитать список значений
        self._show_enum_details(type_name, t.get("schema"))

    def _on_drop_type(self):
        # удаление выбранного типа
        current = self.list_types.currentItem()
        if current is None:
            return

        t = current.data(Qt.UserRole) or {}
        name = t.get("name")
        kind = t.get("kind")
        schema = t.get("schema")

        if not name or not kind:
            return

        human = "ENUM" if kind == "e" else "COMPOSITE"
        full_name = f"{schema}.{name}" if schema else name

        reply = QMessageBox.question(
            self,
            "Удалить тип",
            f"Удалить тип {human} {full_name}?\n"
            f"ВНИМАНИЕ: при CASCADE будут изменены / удалены объекты, использующие этот тип.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # проще и надёжнее всегда использовать CASCADE — это учебный проект
        try:
            self.db.drop_type(name, cascade=True)
        except Exception as e:
            app_logger.error(f"Ошибка удаления типа {name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тип:\n{e}")
            return

        self._load_types()


    def _prompt(self, title: str, label: str):
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return text, ok

    def _set_details_empty(self):
        self.table_details.clear()
        self.table_details.setColumnCount(0)
        self.table_details.setRowCount(0)
        self._enable_enum_controls(False)

    def _on_enum_input_changed(self, text):
        has_text = bool(text and text.strip())
        self.btn_enum_add.setEnabled(has_text)

    def _enable_enum_controls(self, flag: bool):
        self.enum_add_input.setEnabled(flag)
        has_text = bool(self.enum_add_input.text() and self.enum_add_input.text().strip())
        self.btn_enum_add.setEnabled(flag and has_text)

        btn_del = getattr(self, "btn_enum_delete", None)
        if btn_del is not None:
            btn_del.setEnabled(flag)

    def reload_types(self):
        self._load_types()