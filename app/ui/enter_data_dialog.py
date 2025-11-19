# app/enter_data_dialog.py
# расширенный модальный диалог добавления данных
# поддерживает ENUM, массивы, NOT NULL, валидацию и динамические формы

from PySide6.QtWidgets import (
    QDialog, QMessageBox, QLabel, QLineEdit, QComboBox,
    QVBoxLayout, QHBoxLayout, QWidget, QDateEdit, QDateTimeEdit
)
from PySide6.QtCore import Qt, QRegularExpression, QDate, QDateTime
from PySide6.QtGui import QIntValidator, QDoubleValidator

from app.ui.ui_enter_data_dialog import UIEnterDataDialog
from app.log.log import app_logger

from PySide6.QtGui import QIntValidator, QDoubleValidator, QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression



class EnterDataDialog(QDialog):
    """полноценное окно вставки данных во все таблицы"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        # подключаем UI
        self.ui = UIEnterDataDialog()
        self.ui.setupUi(self)

        self.setModal(True)
        self.fields = {}       # имя_поля -> виджет
        self.col_info = {}     # имя_поля -> инфо (тип/nullable/default)

        self._connect()
        self._load_tables()

    # ----------------------------------------------------------------------
    # signals
    # ----------------------------------------------------------------------

    def _connect(self):
        self.ui.table_selector.currentTextChanged.connect(self._load_fields)
        self.ui.btn_save.clicked.connect(self._on_save)
        self.ui.btn_cancel.clicked.connect(self.reject)

    # ----------------------------------------------------------------------
    # load tables
    # ----------------------------------------------------------------------

    def _load_tables(self):
        try:
            tables = self.db.get_tables()
            self.ui.table_selector.clear()
            self.ui.table_selector.addItems(tables)
        except Exception as e:
            app_logger.error(e)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список таблиц:\n{e}")

    # ----------------------------------------------------------------------
    # fields loader
    # ----------------------------------------------------------------------

    def _load_fields(self):
        """строим UI по структуре выбранной таблицы + ограничения ввода"""
        table = self.ui.table_selector.currentText()
        if not table:
            return

        # очищаем старые поля
        ly = self.ui.fields_layout
        while ly.count():
            item = ly.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.fields.clear()
        self.col_info.clear()

        try:
            cols = self.db.get_table_columns(table)
            fkeys = self.db.get_foreign_keys(table)
        except Exception as e:
            app_logger.error(e)
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить структуру таблицы:\n{e}")
            return

        fk_dict = {fk["column"]: fk for fk in fkeys}

        for col in cols:
            name = col["column_name"]

            # SERIAL id — не вводим руками, БД сама
            if name == "id":
                continue

            dtype = col["data_type"]  # 'character varying', 'integer', ...
            nullable = col["is_nullable"] == "YES"
            enum_values = col.get("enum_values")
            default = col.get("column_default")
            max_len = col.get("character_maximum_length")  # может быть None

            self.col_info[name] = {
                "type": dtype,
                "nullable": nullable,
                "default": default,
                "enum_values": enum_values,
                "max_length": max_len,
            }

            lbl = QLabel(f"{name} ({dtype})")
            if not nullable:
                lbl.setStyleSheet("color:#ffaaaa; margin-top:8px;")
            else:
                lbl.setStyleSheet("color:#dcdcdc; margin-top:8px;")
            ly.addWidget(lbl)

            field = None
            dtype_lower = (dtype or "").lower()

            # ---------- ENUM ----------
            if enum_values:
                field = QComboBox()
                field.addItems(enum_values)
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:4px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # ---------- Внешний ключ ----------
            if name in fk_dict:
                ref_table = fk_dict[name]["ref_table"]
                try:
                    options = self.db.get_reference_values(ref_table)
                    field = QComboBox()
                    for id_, label in options:
                        field.addItem(f"{id_} — {label}", userData=id_)
                    field.setStyleSheet("background:#2b2d31; color:#eee; padding:4px;")
                    ly.addWidget(field)
                    self.fields[name] = field
                    continue
                except Exception as e:
                    app_logger.error(f"Ошибка загрузки значений из {ref_table}: {e}")

            # ---------- Boolean ----------
            if dtype_lower == "boolean":
                field = QComboBox()
                field.addItems(["true", "false"])
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:4px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # ---------- Массивы ----------
            if dtype_lower.endswith("[]"):
                field = QLineEdit()
                field.setPlaceholderText("Введите значения через запятую")
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # ---------- ЦЕЛЫЕ ЧИСЛА ----------
            if dtype_lower in ("integer", "int4", "bigint", "smallint"):
                field = QLineEdit()
                field.setValidator(QIntValidator(field))
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # ---------- ВЕЩЕСТВЕННЫЕ ЧИСЛА ----------
            if dtype_lower in ("numeric", "real", "double precision"):
                field = QLineEdit()
                dv = QDoubleValidator(field)
                dv.setNotation(QDoubleValidator.StandardNotation)
                field.setValidator(dv)
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # ---------- DATE: календарь + ручной ввод с проверкой ----------
            if dtype_lower == "date":
                field = QDateEdit()
                field.setCalendarPopup(True)
                field.setDisplayFormat("yyyy-MM-dd")
                field.setDate(QDate.currentDate())
                # можно и руками, и через календарь
                field.setToolTip("Выберите дату в календаре или измените вручную (ГГГГ-ММ-ДД)")
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # ---------- TIMESTAMP: календарь + время ----------
            if dtype_lower.startswith("timestamp"):
                field = QDateTimeEdit()
                field.setCalendarPopup(True)
                field.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                field.setDateTime(QDateTime.currentDateTime())
                field.setToolTip("Выберите дату и время в календаре или измените вручную")
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # ---------- СТРОКИ: varchar / text / char ----------
            if dtype_lower in ("character varying", "varchar", "text", "character"):
                field = QLineEdit()

                # лимит длины для varchar/char
                if max_len is not None:
                    field.setMaxLength(max_len)

                # только буквы для ФИО
                if name in ("last_name", "first_name", "patronymic"):
                    regex = QRegularExpression(r"[A-Za-zА-Яа-яЁё\s\- ]+")
                    field.setValidator(QRegularExpressionValidator(regex, field))

                # паспорт строго в формате 4 цифры + пробел + 6 цифр
                if name == "passport":
                    regex = QRegularExpression(r"\d{4} \d{6}")
                    field.setValidator(QRegularExpressionValidator(regex, field))
                    # для паспорта всегда жёстко 11 символов: 4 + пробел + 6
                    field.setMaxLength(11)

                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field

            else:
                # ---------- всё остальное — обычное поле ----------
                field = QLineEdit()
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field

            # placeholder для DEFAULT
            if default is not None:
                field.setPlaceholderText(f"По умолчанию: {default}")

    # ----------------------------------------------------------------------
    # save
    # ----------------------------------------------------------------------

    def _on_save(self):
        table = self.ui.table_selector.currentText()
        if not table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу.")
            return

        try:
            row = self._collect_data()
            self.db.insert_row(table, row)
            QMessageBox.information(self, "Готово", "Строка успешно добавлена.")
            app_logger.info(f"INSERT INTO {table}: {row}")
            self.accept()

        except Exception as e:
            app_logger.error(e)
            QMessageBox.critical(self, "Ошибка", f"Вставка не выполнена:\n{e}")

    # ----------------------------------------------------------------------
    # data collector
    # ----------------------------------------------------------------------

    def _collect_data(self):
        """Сбор значений из полей с учётом типов, NULL, DEFAULT и т.д."""
        result = {}

        for name, widget in self.fields.items():
            info = self.col_info[name]
            dtype = info["type"]
            nullable = info["nullable"]
            default = info["default"]
            enum_values = info["enum_values"]

            # забираем текст из виджетов
            if isinstance(widget, QLineEdit):
                text = widget.text().strip()
            elif isinstance(widget, QComboBox):
                text = widget.currentText().strip()
            elif isinstance(widget, QDateEdit):
                # DATE
                text = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QDateTimeEdit):
                # TIMESTAMP
                text = widget.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            else:
                text = ""

            # userData нужно для внешних ключей (там лежит сам id)
            current_data = None
            if isinstance(widget, QComboBox):
                current_data = widget.currentData()

            # ---------- пустое значение ----------
            if text == "":
                # если есть DEFAULT → вообще не включаем поле в INSERT
                if default is not None:
                    continue

                # NULL допустим
                if nullable:
                    result[name] = None
                    continue

                # NOT NULL и нет default → ошибка
                raise ValueError(f"Поле '{name}' обязательно (NOT NULL)")

            dtype_lower = (dtype or "").lower()

            # ---------- ENUM ----------
            if enum_values:
                if text not in enum_values:
                    raise ValueError(f"Недопустимое значение ENUM для '{name}'")
                result[name] = text
                continue

            # ---------- массивы ----------
            if dtype_lower.endswith("[]"):
                arr = [x.strip() for x in text.split(",") if x.strip()]
                result[name] = arr
                continue

            # ---------- целые числа ----------
            if dtype_lower in ("integer", "int4", "bigint", "smallint"):
                # для FK в комбобоксе в userData лежит id
                value = current_data if current_data is not None else text
                try:
                    result[name] = int(value)
                except Exception:
                    raise ValueError(f"Поле '{name}' должно быть целым числом")
                continue

            # ---------- числа с плавающей запятой ----------
            if dtype_lower in ("numeric", "real", "double precision"):
                value = current_data if current_data is not None else text
                try:
                    result[name] = float(str(value).replace(",", "."))
                except Exception:
                    raise ValueError(f"Поле '{name}' должно быть числом")
                continue

            # ---------- boolean ----------
            if dtype_lower == "boolean":
                low = text.lower()
                if low in ("true", "t", "1", "yes", "y", "да"):
                    result[name] = True
                elif low in ("false", "f", "0", "no", "n", "нет"):
                    result[name] = False
                else:
                    raise ValueError(
                        f"Поле '{name}' (boolean) принимает значения true/false"
                    )
                continue

            # ---------- строки и остальное ----------
            result[name] = text

        return result