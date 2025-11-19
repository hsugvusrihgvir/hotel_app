# app/main_window.py — связывает UI и логику

from PySide6.QtWidgets import QMainWindow, QMessageBox

from app.ui.ui_main_window import UIMainWindow
from app.ui.enter_data_dialog import EnterDataDialog
from app.ui.join_master_dialog import JoinMasterDialog
from app.ui.data_window import DataWindow
from app.ui.alter_table_window import AlterTableWindow
from app.ui.types_window import TypesWindow  # на будущее, если понадобится кнопка
from app.log.log import app_logger
from app.ui.quick_view_window import QuickViewWindow
from PySide6.QtWidgets import QDialog


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.ui = UIMainWindow()
        self.ui.setup_ui(self)

        self._types_window = None  # ← добавь эту строку

        self._connect_signals()

    # ---------------------------------------------------
    # связывание кнопок и логики
    # ---------------------------------------------------

    def _connect_signals(self):
        self.ui.btn_create_schema.clicked.connect(self.on_create_schema)
        self.ui.btn_add_data.clicked.connect(self.on_add_data)
        self.ui.btn_show_data.clicked.connect(self.on_show_data)
        self.ui.btn_alter.clicked.connect(self.on_alter)
        self.ui.btn_reset_schema.clicked.connect(self.on_reset_schema)
        self.ui.btn_quick_view.clicked.connect(self.on_quick_view)
        # отдельный модуль пользовательских типов
        self.ui.btn_types.clicked.connect(self.on_manage_types)

    # ---------------------------------------------------
    # обработчики
    # ---------------------------------------------------

    def on_create_schema(self):
        """запуск SQL-скрипта schema.sql"""
        try:
            with open("db/schema.sql", "r", encoding="utf-8") as f:
                script = f.read()

            self.db.execute_ddl(script)
            QMessageBox.information(self, "Готово", "Схема успешно создана.")
            app_logger.info("schema created")

        except Exception as e:
            self._error(f"Ошибка создания схемы:\n{e}")

        if self._types_window is not None:
            try:
                self._types_window.reload_types()
            except Exception as e:
                app_logger.error(f"Не удалось обновить окно типов после создания схемы: {e}")

    def on_add_data(self):
        """модальное окно для вставки данных"""
        try:
            dlg = EnterDataDialog(self.db, self)
            dlg.exec()
        except Exception as e:
            self._error(f"Ошибка при добавлении данных:\n{e}")

    def on_show_data(self):
        """мастер JOIN → окно просмотра данных"""
        try:
            # сначала мастер выбора таблиц / полей / типа JOIN
            join_dlg = JoinMasterDialog(self.db, self)
            if join_dlg.exec() != QDialog.Accepted:
                return

            join_info = {
                "table1": join_dlg.table1,
                "table2": join_dlg.table2,
                "col1": join_dlg.col1,
                "col2": join_dlg.col2,
                "join_type": join_dlg.join_type,
                "selected_columns": join_dlg.selected_columns,
            }

            wnd = DataWindow(self.db, join_info, self)
            wnd.show()

        except Exception as e:
            self._error(f"Ошибка загрузки данных:\n{e}")

    def on_alter(self):
        """окно изменения структуры таблиц (ALTER TABLE + типы)"""
        try:
            dlg = AlterTableWindow(self.db, self)
            dlg.exec()
        except Exception as e:
            self._error(f"Ошибка ALTER TABLE:\n{e}")

    # ---------------------------------------------------
    # внутренние функции
    # ---------------------------------------------------

    def _error(self, text: str):
        """одинаковый вывод ошибок + лог"""
        QMessageBox.critical(self, "Ошибка", text)
        app_logger.error(text)

    def on_reset_schema(self):
        """подтверждение и полный сброс базы через schema.sql"""
        reply = QMessageBox.question(
            self,
            "Подтверждение сброса",
            "Все данные будут удалены и схема будет пересоздана.\nПродолжить?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            with open("db/reset.sql", "r", encoding="utf-8") as f:
                script = f.read()

            self.db.execute_ddl(script)
            QMessageBox.information(self, "Сброс", "База данных успешно сброшена.")
            app_logger.info("schema reset by user")

        except Exception as e:
            self._error(f"Ошибка при сбросе базы:\n{e}")


        if self._types_window is not None:
            try:
                self._types_window.reload_types()
            except Exception as e:
                app_logger.error(f"Не удалось обновить окно типов после сброса: {e}")


    def on_quick_view(self):
        try:
            wnd = QuickViewWindow(self.db, self)
            wnd.show()
        except Exception as e:
            self._error(f"Ошибка быстрого просмотра:\n{e}")

    def on_manage_types(self):
        """Открыть отдельное окно управления пользовательскими типами."""
        try:
            if self._types_window is None:
                self._types_window = TypesWindow(self.db, self)
            self._types_window.show()
            self._types_window.raise_()
            self._types_window.activateWindow()
        except Exception as e:
            self._error(f"Ошибка при открытии окна типов:\n{e}")
