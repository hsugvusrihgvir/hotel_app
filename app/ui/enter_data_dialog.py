# app/enter_data_dialog.py
# расширенный модальный диалог добавления данных
# поддерживает ENUM, массивы, NOT NULL, валидацию и динамические формы

from PySide6.QtWidgets import (
    QDialog, QMessageBox, QLabel, QLineEdit, QComboBox,
    QVBoxLayout, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt

from app.ui.ui_enter_data_dialog import UIEnterDataDialog
from app.log.log import app_logger


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
        """строим UI по структуре выбранной таблицы"""
        table = self.ui.table_selector.currentText()
        if not table:
            return

        # очищаем старые поля
        ly = self.ui.fields_layout
        while ly.count():
            w = ly.takeAt(0)
            if w.widget():
                w.widget().deleteLater()

        self.fields.clear()
        self.col_info.clear()

        try:
            cols = self.db.get_table_columns(table)
            fkeys = self.db.get_foreign_keys(table)  # ← Добавь такой метод в класс DB
        except Exception as e:
            app_logger.error(e)
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить структуру таблицы:\n{e}")
            return

        fk_dict = {fk['column']: fk for fk in fkeys}

        for col in cols:
            name = col["column_name"]
            dtype = col["data_type"]
            nullable = col["is_nullable"] == "YES"
            enum_values = col.get("enum_values")
            default = col.get("column_default")

            self.col_info[name] = {
                "type": dtype,
                "nullable": nullable,
                "default": default,
                "enum_values": enum_values
            }

            lbl = QLabel(f"{name} ({dtype})")
            lbl.setStyleSheet("color:#dcdcdc; margin-top:8px;")
            ly.addWidget(lbl)

            # ENUM
            if enum_values:
                field = QComboBox()
                field.addItems(enum_values)
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:4px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # Внешний ключ
            if name in fk_dict:
                ref_table = fk_dict[name]['ref_table']
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

            # Массив
            if dtype.endswith("[]"):
                field = QLineEdit()
                field.setPlaceholderText("Введите значения через запятую")
                field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
                ly.addWidget(field)
                self.fields[name] = field
                continue

            # Обычный ввод
            field = QLineEdit()
            field.setStyleSheet("background:#2b2d31; color:#eee; padding:6px;")
            if default:
                field.setPlaceholderText(f"По умолчанию: {default}")
            ly.addWidget(field)
            self.fields[name] = field

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
        """сбор значений из всех полей с валидацией NOT NULL и массивов"""
        result = {}

        for name, widget in self.fields.items():
            info = self.col_info[name]
            dtype = info["type"]
            nullable = info["nullable"]
            enum_vals = info["enum_values"]

            # ENUM
            if enum_vals:
                val = widget.currentText()
                result[name] = val
                continue

            text = widget.text().strip()

            # NULL?
            if text == "":
                if not nullable:
                    raise ValueError(f"Поле '{name}' обязательно (NOT NULL)")
                result[name] = None
                continue

            # массив
            if dtype.endswith("[]"):
                arr = [x.strip() for x in text.split(",") if x.strip()]
                result[name] = arr
                continue

            # numeric → float
            if dtype in ("numeric", "double precision", "real"):
                try:
                    result[name] = float(text)
                except:
                    raise ValueError(f"Поле '{name}' должно быть числом")

                continue

            # integer
            if dtype in ("integer", "int4", "smallint", "bigint"):
                try:
                    result[name] = int(text)
                except:
                    raise ValueError(f"Поле '{name}' должно быть целым числом")
                continue

            # boolean
            if dtype == "boolean":
                if text.lower() in ("true", "t", "1", "yes", "y"):
                    result[name] = True
                elif text.lower() in ("false", "f", "0", "no", "n"):
                    result[name] = False
                else:
                    raise ValueError(
                        f"Поле '{name}' (boolean) принимает значения: true/false"
                    )
                continue

            # всё остальное — строка
            result[name] = text

        return result
