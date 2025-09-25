from app.ui.ui_enter_data_dialog import EnterDataDialog # открытие, диалоговое окно с выбором режима

from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, )
from PySide6.QtCore import Slot

from app.ui.ui_main_window import Ui_MainWindow
from app.db.db import HotelDB
from app.log.log import HotelLog

from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from app.ui.data_window import DataWindow

class MainWindow(QMainWindow):  # меню
    def __init__(self) -> None:
        super().__init__()

        self.log = HotelLog()
        self.db = HotelDB() # создания объекта класса для взаимодействия с бд
        self.connected = False # подключение к бд изначально false

        self.ui = Ui_MainWindow() # создание объекта меню
        self.ui.setupUi(self)

        # подключение кнопок для
        self.ui.btnConnect.clicked.connect(self.on_connect) # соединение с бд
        self.ui.btnCreateSchema.clicked.connect(self.on_create_schema) #  создание схемы
        self.ui.btnShowData.clicked.connect(self.on_show_data) # показать данные

        self.ui.btnAddClient.clicked.connect(self.on_add_client) # добавление клиента
        self.ui.btnAddRoom.clicked.connect(self.on_add_room) # добавление комнаты
        self.ui.btnAddStays.clicked.connect(self.on_add_stays) # ввсти данные

        self.ui.btnUpdate.clicked.connect(self.on_update) # обновить
        self.ui.btnOpenLog.clicked.connect(self.on_open_log) # открыть лог файл
        self.ui.btnAbout.clicked.connect(self.on_about) # о приложении
        self.ui.btnExit.clicked.connect(self.close) # закрыть

        self.on_connect()

    def _info(self, text: str) -> None: # открытие окна с передаваемой информацией
        QMessageBox.information(self, "Информация", text)
        self.log.addInfo(text)

    def _error(self, text: str) -> None: # открытие окна с передаваемой ошибкой
        QMessageBox.critical(self, "Ошибка", text)
        self.log.addError(text)

    @Slot()
    def on_connect(self) -> None:  # соединение с бд
        try:
            self.db.connect()
            self.connected = True # подключение успешно
            self._info("Подключение к базе данных установлено.")
        except RuntimeError as e:
            self.connected = False
            self._error(f"Не удалось подключиться:\n{e}")

    @Slot()
    def on_create_schema(self) -> None: # создать схему
        try:
            self.db.create() # создание схемы (таблиц)
            self._info("Создание схемы прошло успешно")
        except RuntimeError as e:
            self._error(f"Не удалось создать схему:\n{e}")



    @Slot()
    def on_show_data(self) -> None: # показать данные
        if not self.connected: # проверка подключения к базе данных
            self._error("Сначала подключитесь к базе данных")
            return
        data_window = DataWindow(self, self.db) # создается и показывается модальное окно
        data_window.exec_() # блок родительского окна до закрытия


    @Slot()
    def on_add_client(self) -> None:  # ввести данные
        dlg = EnterDataDialog(self)  # открытие диалогового окна для ввода данных
        dlg.setMode(EnterDataDialog.MODE_CLIENT) # выбор режима (данные для клиента, комнаты или бронирования)
        if dlg.exec(): # при закрытии
            try:
                data = dlg.payload # данные из окна
                self.db.enterDataClient(data) # передача данных в класс для работы с бд
                self._info(f"Добавление клиента [{data['last_name']} {data['first_name']} {data['patronymic']}, {data['passport']}] прошло успешно")
            except RuntimeError as e:
                self._error(f"Не удалось добавить клиента: {e}")


    @Slot()
    def on_add_room(self) -> None:  # аналогично
        dlg = EnterDataDialog(self, db=self.db)
        dlg.setMode(EnterDataDialog.MODE_ROOM)
        if dlg.exec():
            try:
                data = dlg.payload
                self.db.enterDataRooms(data)
                self._info(f"Добавление комнаты {data['room_number']} прошло успешно")
            except RuntimeError as e:
                self._error(f"Не удалось добавить комнату:\n{e}")

    @Slot()
    def on_add_stays(self) -> None:  # аналогично
        try:
            clients = self.db.find_clients()
            rooms = self.db.find_rooms()
        except RuntimeError as e:
            self._error("Ошибка с поиском данных в базе данных. Проверьте подключение.")
        dlg = EnterDataDialog(self, clients=clients, rooms=rooms)
        dlg.setMode(EnterDataDialog.MODE_STAY)
        if dlg.exec():
            try:
                data = dlg.payload
                self.db.enterDataStays(data)
                self._info(f"Добавление бронирования клиентом {data['client_id']} комнаты {data['room_id']} прошло успешно")
            except RuntimeError as e:
                self._error(f"Не удалось добавить: {e}")


    @Slot()
    def on_update(self) -> None: # обновить
        pass


    @Slot()
    def on_open_log(self) -> None: # открыть лог файл
        try:
            path = self.log.FILE
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception as e:
            self._error(f"Не удалось открыть лог-файл: {e}")


    @Slot()
    def on_about(self) -> None: # о приложении
        pass

    def closeEvent(self, event):
        try:
            if self.connected:
                self.db.close()
                self.connected = False
        except Exception as e:
            self._error(f"Ошибка при закрытии БД: {e}")
        finally:
            super().closeEvent(event)


    def _confirm(self, text: str) -> bool:
        pass

