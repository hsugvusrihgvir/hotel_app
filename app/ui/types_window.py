# app/ui/types_window.py — управление пользовательскими типами PostgreSQL

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from app.log.log import app_logger


class TypesWindow(QMainWindow):
    """
    Окно управления пользовательскими типами PostgreSQL (ENUM + COMPOSITE).

    Возможности:
    * просмотреть список пользовательских типов (исключая системные схемы);
    * посмотреть значения ENUM;
    * посмотреть поля составного типа (COMPOSITE);
    * создать новый ENUM;
    * создать новый COMPOSITE;
    * добавить новое значение к существующему ENUM;
    * удалить тип (DROP TYPE [CASCADE]).

    Всё делается через GUI-кнопки, без ручного ввода сырого SQL.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Пользовательские типы (ENUM / COMPOSITE)")
        self.resize(900, 580)

        self.list_types = None
        self.table_details = None
        self.enum_add_input = None
        self.btn_enum_add = None
        self.btn_enum_delete = None  # ← добавили
        self.lbl_details_title = None

        self._build_ui()
        self._load_types()

    # ------------------------------------------------------------------
    # Построение UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Пользовательские типы данных PostgreSQL")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #e5e7eb; margin-bottom: 8px;")
        root.addWidget(title)

        subtitle = QLabel("ENUM и составные типы (COMPOSITE). Создание, просмотр, управление.")
        subtitle.setStyleSheet("color: #9ca3af; font-size: 12px;")
        root.addWidget(subtitle)

        # --- верхняя панель с кнопками ---
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

        # --- основная область: список типов слева, детали справа ---
        body = QHBoxLayout()
        body.setContentsMargins(0, 8, 0, 0)
        body.setSpacing(14)
        root.addLayout(body, 1)

        # левая колонка — список типов
        left_box = QVBoxLayout()
        left_box.setSpacing(6)
        lbl_types = QLabel("Пользовательские типы")
        lbl_types.setStyleSheet("color: #d1d5db; font-weight: 600;")
        left_box.addWidget(lbl_types)

        self.list_types = QListWidget()
        self.list_types.setStyleSheet("""
            QListWidget {
                background-color: #020617;
                border: 1px solid #374151;
                color: #e5e7eb;
            }
            QListWidget::item:selected{
                background-color: #1d4ed8;
            }
        """)
        left_box.addWidget(self.list_types, 1)
        body.addLayout(left_box, 1)

        # правая колонка — детали выбранного типа
        right_box = QVBoxLayout()
        right_box.setSpacing(6)

        self.lbl_details_title = QLabel("Детали типа")
        self.lbl_details_title.setStyleSheet("color: #d1d5db; font-weight: 600;")
        right_box.addWidget(self.lbl_details_title)

        self.table_details = QTableWidget()
        self.table_details.setColumnCount(0)
        self.table_details.setRowCount(0)
        self.table_details.setStyleSheet("""
            QTableWidget {
                background-color: #020617;
                border: 1px solid #374151;
                gridline-color: #374151;
                color: #e5e7eb;
            }
            QHeaderView::section {
                background-color: #111827;
                color: #e5e7eb;
                padding: 3px 6px;
                border: 1px solid #374151;
            }
        """)
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

        self.btn_enum_add = QPushButton("Добавить")
        self.btn_enum_add.setCursor(Qt.PointingHandCursor)

        self.btn_enum_delete = QPushButton("Удалить выбранное")
        self.btn_enum_delete.setCursor(Qt.PointingHandCursor)

        enum_row.addWidget(self.enum_add_input, 1)
        enum_row.addWidget(self.btn_enum_add)
        enum_row.addWidget(self.btn_enum_delete)

        right_box.addLayout(enum_row)

        body.addLayout(right_box, 2)

        # изначально кнопки ENUM недоступны (нет выбранного ENUM)
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
        """Заполняем левый список типами из БД."""
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
            kind = t["kind"]      # 'e' или 'c'
            schema = t["schema"]

            human = "ENUM" if kind == "e" else "COMPOSITE"
            item = QListWidgetItem(f"{schema}.{name}   ({human})")
            # в userData кладём словарь, чтобы не строить строки назад
            item.setData(Qt.UserRole, t)
            self.list_types.addItem(item)

        if self.list_types.count() == 0:
            self.lbl_details_title.setText("Детали типа (пользовательские типы не найдены)")
        else:
            self.lbl_details_title.setText("Детали типа")

    def _on_type_selected(self, current: QListWidgetItem, _previous: QListWidgetItem):
        """Когда пользователь выбирает тип слева — показываем детали."""
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
        """Показываем значения ENUM."""
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

        # авто-выделяем первую строку, чтобы кнопка сразу работала
        if self.table_details.rowCount() > 0:
            self.table_details.setCurrentCell(0, 0)

        self._enable_enum_controls(True)
        self.lbl_details_title.setText(f"ENUM {schema + '.' if schema else ''}{type_name}")


    def _show_composite_details(self, type_name: str, schema: str | None):
        """Показываем поля составного типа."""
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

    # ------------------------------------------------------------------
    # Действия пользователя
    # ------------------------------------------------------------------

    def _on_new_enum(self):
        """Создание нового ENUM через два простых ввода."""
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
        """Создание нового составного типа."""
        name, ok = self._prompt("Создать COMPOSITE", "Имя нового составного типа (без схемы):")
        if not ok:
            return

        name = name.strip()
        if not name:
            return

        fields_str, ok = self._prompt(
            "Создать COMPOSITE",
            "Поля (формат: field1 type1, field2 type2, ...):"
        )
        if not ok:
            return

        raw_parts = [p.strip() for p in (fields_str or "").split(",") if p.strip()]
        fields: list[tuple[str, str]] = []

        for part in raw_parts:
            # делим на имя и тип: "field_name type_name"
            pieces = part.split(None, 1)
            if len(pieces) != 2:
                QMessageBox.warning(
                    self,
                    "Неверный формат",
                    f"Не удалось разобрать поле: «{part}».\nОжидается «имя_поля тип_данных»."
                )
                return
            fname, ftype = pieces[0].strip(), pieces[1].strip()
            if not fname or not ftype:
                QMessageBox.warning(
                    self,
                    "Неверный формат",
                    f"Не удалось разобрать поле: «{part}»."
                )
                return
            fields.append((fname, ftype))

        if not fields:
            QMessageBox.warning(self, "Предупреждение", "Нужно указать хотя бы одно поле.")
            return

        try:
            self.db.create_composite_type(name, fields)
        except Exception as e:
            app_logger.error(f"Ошибка создания COMPOSITE {name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать составной тип:\n{e}")
            return

        self._load_types()

    def _on_enum_add(self):
        """Добавление нового значения в выбранный ENUM."""
        current = self.list_types.currentItem()
        if current is None:
            return

        t = current.data(Qt.UserRole) or {}
        if t.get("kind") != "e":
            return  # защита от случайного нажатия

        type_name = t["name"]
        value = (self.enum_add_input.text() or "").strip()
        if not value:
            return

        try:
            self.db.add_enum_value(type_name, value)
        except Exception as e:
            app_logger.error(f"Ошибка добавления значения в ENUM {type_name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить значение:\n{e}")
            return

        self.enum_add_input.clear()
        self._show_enum_details(type_name, t.get("schema"))

    def _on_enum_delete_value(self):
        """Удаление выбранного значения из ENUM."""
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
        """Удаление выбранного типа (DROP TYPE)."""
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

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    def _prompt(self, title: str, label: str):
        """Обёртка над QInputDialog.getText, чтобы не плодить импортов."""
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, label)
        return text, ok

    def _set_details_empty(self):
        self.table_details.clear()
        self.table_details.setColumnCount(0)
        self.table_details.setRowCount(0)
        self._enable_enum_controls(False)

    def _enable_enum_controls(self, flag: bool):
        self.enum_add_input.setEnabled(flag)
        self.btn_enum_add.setEnabled(flag)
        # аккуратно работаем с кнопкой удаления, вдруг её ещё нет
        btn_del = getattr(self, "btn_enum_delete", None)
        if btn_del is not None:
            btn_del.setEnabled(flag)

    def reload_types(self):
        """Перечитать список пользовательских типов из БД."""
        self._load_types()