from PySide6.QtWidgets import (
    QDialog, QMessageBox, QLabel, QLineEdit, QComboBox,
    QVBoxLayout, QHBoxLayout, QWidget, QDateEdit, QDateTimeEdit,
    QScrollArea, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QRegularExpression, QDate, QDateTime
from PySide6.QtGui import QIntValidator, QDoubleValidator, QRegularExpressionValidator, QFont, QPalette, QColor

from app.log.log import app_logger
from app.ui.theme import *


class EnterDataDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.fields = {}
        self.col_info = {}
        self.current_table = ""

        self.setWindowTitle("Добавить запись")
        self.resize(520, 600)
        self.setModal(True)

        self.setStyleSheet(f"""
                    QDialog {{
                        background-color: {WINDOW_BG};
                        color: {TEXT_MAIN};
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
                """)

        self._build_ui()
        self._connect_signals()
        self._load_tables()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

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
                    }}
                """)

        # выбор таблицы
        table_layout = QHBoxLayout()
        table_layout.addWidget(QLabel("Таблица:"))

        self.table_selector = QComboBox()
        table_layout.addWidget(self.table_selector, 1)
        main_layout.addLayout(table_layout)

        # с полями ввода
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        self.fields_layout.setContentsMargins(5, 5, 5, 5)
        self.fields_layout.setSpacing(12)

        scroll.setWidget(self.fields_widget)
        main_layout.addWidget(scroll, 1)

        # кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.btn_save = self._create_button("Сохранить")
        self.btn_cancel = self._create_button("Отмена")

        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_layout)

    def _create_button(self, text):
        btn = QPushButton(text)
        btn.setMinimumHeight(40)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BTN_BG};
                color: {BTN_TEXT};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {BTN_BG_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {BTN_BG_PRESSED};
            }}
        """)
        return btn

    def _connect_signals(self):
        self.table_selector.currentTextChanged.connect(self._load_fields)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self.reject)

    def _load_tables(self):
        try:
            tables = self.db.get_tables()
            self.table_selector.clear()
            self.table_selector.addItems(tables)

            if tables:
                self._load_fields(tables[0])

        except Exception as e:
            app_logger.error(f"Ошибка загрузки таблиц: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список таблиц:\n{e}")

    def _load_fields(self, table_name):
        if not table_name or table_name == self.current_table:
            return

        self.current_table = table_name

        # очищаем старые поля
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.fields.clear()
        self.col_info.clear()

        try:
            cols = self.db.get_table_columns(table_name) # колонки таблицы
            fkeys = self.db.get_foreign_keys(table_name) # внешние ключи
        except Exception as e:
            app_logger.error(f"Ошибка загрузки структуры таблицы {table_name}: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить структуру таблицы:\n{e}")
            return

        # обработка fkeys
        fk_dict = {fk["column"]: fk for fk in fkeys}

        for col in cols:
            name = col["column_name"]
            dtype = col["data_type"]
            nullable = col["is_nullable"] == "YES"
            enum_values = col.get("enum_values")
            default = col.get("column_default")
            max_len = col.get("character_maximum_length")

            # пропускаем автоинкрементные поля
            if name == "id" and default and "nextval" in str(default):
                continue

            # сохраняем эту инфу
            self.col_info[name] = {
                "type": dtype,
                "nullable": nullable,
                "default": default,
                "enum_values": enum_values,
                "max_length": max_len,
            }

            # создаем контейнер для поля
            field_frame = QFrame()
            field_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {CARD_BG};
                    border: 1px solid {CARD_BORDER};
                    border-radius: 6px;
                }}
            """)

            field_layout = QVBoxLayout(field_frame)
            field_layout.setContentsMargins(10, 8, 10, 8)
            field_layout.setSpacing(4)

            # метка поля
            lbl_text = f"{name} ({dtype})"
            if not nullable:
                lbl_text += " *"

            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(f"""
                color: {'#ffaaaa' if not nullable else TEXT_SOFT};
            """)
            field_layout.addWidget(lbl)

            # поле ввода
            field_widget = self._create_field_widget(name, dtype, nullable, enum_values, max_len, fk_dict)
            field_layout.addWidget(field_widget)

            self.fields[name] = field_widget
            self.fields_layout.addWidget(field_frame)

        # Добавляем растяжку
        self.fields_layout.addStretch()

    def _create_field_widget(self, name, dtype, nullable, enum_values, max_len, fk_dict):
        dtype_lower = (dtype or "").lower()

        # ENUM
        if enum_values:
            combo = QComboBox()
            combo.addItems(enum_values)
            self._style_combo(combo)
            return combo

        # внешний ключ
        if name in fk_dict:
            ref_table = fk_dict[name]["ref_table"]
            try:
                options = self.db.get_reference_values(ref_table)
                combo = QComboBox()
                combo.addItem("")  # пустой вариант
                for id_, label in options:
                    combo.addItem(f"{id_} — {label}", userData=id_)
                self._style_combo(combo)
                return combo
            except Exception as e:
                app_logger.error(f"Ошибка загрузки значений из {ref_table}: {e}")

        # boolean
        if dtype_lower == "boolean":
            combo = QComboBox()
            combo.addItems(["", "true", "false"])
            self._style_combo(combo)
            return combo

        # массивы
        if dtype_lower == "array" or dtype_lower.endswith("[]"):
            edit = QLineEdit()
            edit.setPlaceholderText("Значения через запятую...")
            self._style_edit(edit)
            return edit

        # целые числа
        if dtype_lower in ("integer", "int4", "bigint", "smallint"):
            edit = QLineEdit()
            edit.setValidator(QIntValidator(edit))
            self._style_edit(edit)
            return edit

        # вещественные
        if dtype_lower in ("numeric", "real", "double precision"):
            edit = QLineEdit()
            dv = QDoubleValidator(edit)
            dv.setNotation(QDoubleValidator.StandardNotation)
            edit.setValidator(dv)
            self._style_edit(edit)
            return edit

        # дата
        if dtype_lower == "date":
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy-MM-dd")
            date_edit.setDate(QDate.currentDate())
            self._style_edit(date_edit)
            return date_edit

        # временная метка
        if dtype_lower.startswith("timestamp"):
            datetime_edit = QDateTimeEdit()
            datetime_edit.setCalendarPopup(True)
            datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            datetime_edit.setDateTime(QDateTime.currentDateTime())
            self._style_edit(datetime_edit)
            return datetime_edit

        # строки с валидацией
        if dtype_lower in ("character varying", "varchar", "text", "character"):
            edit = QLineEdit()

            if max_len is not None:
                edit.setMaxLength(max_len)

            # валидация для специальных полей
            if name in ("last_name", "first_name", "patronymic"):
                regex = QRegularExpression(r"[A-Za-zА-Яа-яЁё\s\- ]+")
                edit.setValidator(QRegularExpressionValidator(regex, edit))

            if name == "passport":
                regex = QRegularExpression(r"\d{4} \d{6}")
                edit.setValidator(QRegularExpressionValidator(regex, edit))
                edit.setMaxLength(11)

            self._style_edit(edit)
            return edit

        # обычное текстовое поле
        edit = QLineEdit()
        self._style_edit(edit)
        return edit

    def _style_edit(self, widget):
        widget.setStyleSheet(f"""
            background-color: {CENTRAL_BG};
            color: {TEXT_MAIN};
            border: 1px solid {CARD_BORDER};
            border-radius: 4px;
            padding: 6px;
        """)

    def _style_combo(self, widget):
        widget.setStyleSheet(f"""
            QComboBox {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 1px solid {CARD_BORDER};
                border-radius: 4px;
                padding: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {CENTRAL_BG};
                color: {TEXT_MAIN};
                border: 1px solid {CARD_BORDER};
                selection-background-color: {ACCENT_PRIMARY};
            }}
        """)

    def _on_save(self):
        table = self.table_selector.currentText()
        if not table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу.")
            return

        try:
            row_data = self._collect_data()
            self.db.insert_row(table, row_data)

            QMessageBox.information(self, "Готово", "Строка успешно добавлена.")
            app_logger.info(f"INSERT INTO {table}: {row_data}")
            self.accept()

        except Exception as e:
            app_logger.error(f"Ошибка вставки: {e}")
            QMessageBox.critical(self, "Ошибка", f"Вставка не выполнена:\n{e}")

    def _collect_data(self):
        result = {}

        for name, widget in self.fields.items():
            info = self.col_info[name]
            dtype = info["type"]
            nullable = info["nullable"]
            default = info["default"]
            enum_values = info["enum_values"]

            # получаем значение в зависимости от типа виджета
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
            elif isinstance(widget, QComboBox):
                value = widget.currentText().strip()
            elif isinstance(widget, QDateEdit):
                value = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QDateTimeEdit):
                value = widget.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            else:
                value = ""

            # обработка пустых значений
            if not value:
                if not nullable and default is None:
                    raise ValueError(f"Поле '{name}' обязательно для заполнения")
                elif default is not None:
                    result[name] = default # используем значение по умолчанию
                    continue
                else:
                    result[name] = None
                    continue

            dtype_lower = (dtype or "").lower()

            # преобразование типов данных
            if enum_values:
                if value not in enum_values:
                    raise ValueError(f"Недопустимое значение ENUM для '{name}': "
                                     f"'{value}'. Допустимые значения: {enum_values}")
                result[name] = value
                continue



            elif dtype_lower == "array" or dtype_lower.endswith("[]"):
                if value:
                    items = [x.strip() for x in value.split(",") if x.strip()]
                    result[name] = items
                else:
                    result[name] = []

            elif dtype_lower in ("integer", "int4", "bigint", "smallint"):
                # целые числа
                try:
                    result[name] = int(value)
                except ValueError:
                    raise ValueError(f"Поле '{name}' должно быть целым числом")

            elif dtype_lower in ("numeric", "real", "double precision"):
                # вещественные числа
                try:
                    result[name] = float(value.replace(",", "."))
                except ValueError:
                    raise ValueError(f"Поле '{name}' должно быть числом")

            elif dtype_lower == "boolean":
                # логические значения
                value_lower = value.lower()
                if value_lower in ("true", "t", "1", "yes", "y", "да"):
                    result[name] = True
                elif value_lower in ("false", "f", "0", "no", "n", "нет"):
                    result[name] = False
                else:
                    raise ValueError(f"Поле '{name}' принимает значения true/false")

            else:
                # строки и прочие типы
                result[name] = value

        return result

    def refresh_tables(self):
        current_table = self.table_selector.currentText()
        self._load_tables()

        # пытаемся восстановить выбор таблицы
        if current_table and current_table in [self.table_selector.itemText(i)
                                               for i in range(self.table_selector.count())]:
            self.table_selector.setCurrentText(current_table)