from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableView, QPushButton,
                               QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem



class DataWindow(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)  # вызов конструктора родительского класса
        self.setWindowTitle("Данные о бронированиях")  # установка заголовка окна
        self.setModal(True)  # делаем окно модальным (блокирует родительское)
        self.setMinimumSize(900, 500)  # установка минимального размера окна

        self.setup_ui()  # настройка пользовательского интерфейса

        if db is None:
            raise RuntimeError("Ошибка. Нет подключения к БД. Откройте сначала соединение.")
        self.db = db

        self.update_table()


    def setup_ui(self):
        layout = QVBoxLayout(self)  # создание вертикального layout

        # таблица для отображения данных
        self.table_view = QTableView()
        self.model = QStandardItemModel()  # модель данных для таблицы
        self.table_view.setModel(self.model)  # связываем модель с таблицей
        layout.addWidget(self.table_view)  # добавляем таблицу в layout

        # layout для кнопок
        buttons_layout = QHBoxLayout()

        # кнопка обновления данных
        self.btn_update = QPushButton("Обновить")
        self.btn_update.clicked.connect(self.update_table)  # подключение сигнала к слоту

        # кнопка фильтров
        self.btn_filter = QPushButton("Поиск по...")
        self.btn_filter.clicked.connect(self.filter_button)  # открытие окна с фильтрами

        # кнопка закрытия окна
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)  # подключение сигнала к слоту

        buttons_layout.addWidget(self.btn_update)  # добавление кнопки обновления
        buttons_layout.addWidget(self.btn_filter)  # рядом с "Обновить", фильтры
        buttons_layout.addStretch()  # добавляем растягивающееся пространство
        buttons_layout.addWidget(self.btn_close)  # добавление кнопки закрытия

        layout.addLayout(buttons_layout)  # добавление layout с кнопками в основной layout


    def update_table(self):
        self.model.clear()  # очистка модели данных

        data = self.db.load_data()

        if not data:  # проверка на наличие данных
            self.model.setHorizontalHeaderLabels(["Нет данных"])  # заголовок если данных нет
            return

        # заголовки столбцов таблицы
        headers = ["ID", "Клиент", "Номер", "Комфорт", "Заезд", "Выезд", "Оплата", "Статус"]
        self.model.setHorizontalHeaderLabels(headers)  # установка заголовков

        # заполнение таблицы данными
        for row in data:
            items = [QStandardItem(str(value)) for value in row]  # создание элементов для каждой ячейки
            self.model.appendRow(items)  # добавление строки в модель

        # автоматическое растягивание столбцов под содержимое
        self.table_view.resizeColumnsToContents()

    def filter_button(self):
        pass