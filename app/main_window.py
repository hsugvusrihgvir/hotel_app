from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Slot

from app.ui.ui_main_window import Ui_MainWindow
from db.db import HotelDB


class MainWindow(QMainWindow):  # меню
    def __init__(self) -> None:
        super().__init__()

        self.db = HotelDB()
        self.connected = False # подключение к бд

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.btnConnect.clicked.connect(self.on_connect) # соединение
        self.ui.btnCreateSchema.clicked.connect(self.on_create_schema) # создать схему
        self.ui.btnShowData.clicked.connect(self.on_show_data) # показать данные
        self.ui.btnEnterData.clicked.connect(self.on_enter_data) # ввсти данные
        self.ui.btnUpdate.clicked.connect(self.on_update) # обновить
        self.ui.btnOpenLog.clicked.connect(self.on_open_log) # открыть лог файл
        self.ui.btnAbout.clicked.connect(self.on_about) # о приложении
        self.ui.btnExit.clicked.connect(self.close) # закрыть

    def _info(self, text: str) -> None: # открытие окна с информацией
        QMessageBox.information(self, "Информация", text)

    def _error(self, text: str) -> None: # открытие окна с ошибкой
        QMessageBox.critical(self, "Ошибка", text)

    @Slot()
    def on_connect(self) -> None:  # соединение
        try:
            self.db.connect()
            self.connected = True
            self._info("Подключение к базе данных установлено.")
        except RuntimeError as e:
            self.connected = False
            self._error(f"Не удалось подключиться:\n{e}")

    @Slot()
    def on_create_schema(self) -> None: # создать схему
        try:
            self.db.create()
            self._info("Создание схемы прошло успешно")
        except RuntimeError as e:
            self._error(f"Не удалось создать схему:\n{e}")



    @Slot()
    def on_show_data(self) -> None: # показать данные
        pass


    @Slot()
    def on_enter_data(self) -> None:  # ввести данные
        pass


    @Slot()
    def on_update(self) -> None: # обновить
        pass


    @Slot()
    def on_open_log(self) -> None: # открыть лог файл
        pass


    @Slot()
    def on_about(self) -> None: # о приложении
        pass

    def closeEvent(self, event):
        try:
            if self.connected:
                self.db.close()
                self.connected = False
        except Exception as e:
            print(f"Ошибка при закрытии БД: {e}")
        finally:
            super().closeEvent(event)


    def _confirm(self, text: str) -> bool:
        pass

