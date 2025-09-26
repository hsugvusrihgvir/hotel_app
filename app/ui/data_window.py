from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableView, QPushButton,
                               QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt, qWarning
from PySide6.QtGui import QStandardItemModel, QStandardItem

from app.ui.filters_window import FilterWindow


class DataWindow(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)  # вызов конструктора родительского класса
        self.setWindowTitle("Данные о бронированиях")  # установка заголовка окна
        self.setModal(True)  # делаем окно модальным (блокирует родительское)
        self.setMinimumSize(900, 500)  # установка минимального размера окна

        # добавление стиля основного окна
        self.setStyleSheet("""
                    QDialog { 
                        background: #171a1d; 
                        color: #e8e6e3; 
                    }
                    QTableView { 
                        background: #242a30; 
                        color: #e8e6e3;
                        border: 1px solid #323a42;
                        gridline-color: #323a42;
                        outline: 0;
                    }
                    QTableView::item:hover { 
                        background: #2b3238; 
                        selection-background-color: #2b3238;
                    }
                    QHeaderView::section { 
                        background: #20252a; 
                        color: #e8e6e3;
                        border: 1px solid #323a42;
                        padding: 8px;
                    }
                    QPushButton { 
                        background: #242a30; 
                        color: #e8e6e3;
                        border: 1px solid #323a42;
                        padding: 8px 16px;
                        border-radius: 5px;
                    }
                    QPushButton:hover { 
                        background: #2b3238; 
                    }
                """)

        self.setup_ui()

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
        self.table_view.verticalHeader().setVisible(False) # убираем счёт строк (есть id)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows) # выделение всей строки
        layout.addWidget(self.table_view)  # добавляем таблицу в layout

        # layout для кнопок
        buttons_layout = QHBoxLayout()

        # кнопка обновления данных
        self.btn_update = QPushButton("Обновить")
        self.btn_update.clicked.connect(self.update_table)  # подключение сигнала к слоту

        # кнопка фильтров
        self.btn_filter = QPushButton("Фильтры")
        self.btn_filter.clicked.connect(self.filter_button)  # открытие окна с фильтрами

        # кнопка закрытия окна
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)  # подключение сигнала к слоту

        buttons_layout.addWidget(self.btn_update)  # добавление кнопки обновления
        buttons_layout.addWidget(self.btn_filter)  # рядом с "Обновить", фильтры
        buttons_layout.addStretch()  # добавляем растягивающееся пространство
        buttons_layout.addWidget(self.btn_close)  # добавление кнопки закрытия

        layout.addLayout(buttons_layout)  # добавление layout с кнопками в основной layout


    def update_table(self, selected_column = None, selected_sort = None):
        self.model.clear()  # очистка модели данных

        # заголовки столбцов таблицы
        headers = ["ID",
                   "Клиент",
                   "Номер",
                   "Комфорт",
                   "Заезд",
                   "Выезд",
                   "Оплата",
                   "Статус"]

        if selected_column is None: selected_column = headers[0]
        if selected_sort is None: selected_sort = "по возрастанию"

        data = self.db.load_data(selected_column, selected_sort)

        if not data:  # проверка на наличие данных
            self.model.setHorizontalHeaderLabels(["Нет данных"])  # заголовок если данных нет
            return

        self.model.setHorizontalHeaderLabels(headers) # установка заголовков

        # заполнение таблицы данными
        for row in data:
            items = [QStandardItem(str(value)) for value in row]  # создание элементов для каждой ячейки
            self.model.appendRow(items)  # добавление строки в модель

        # автоматическое растягивание столбцов под содержимое
        self.table_view.resizeColumnsToContents()

    def filter_button(self):
        filter_window = FilterWindow(self, self.db)  # создается и показывается модальное окно
        filter_window.filterApplied.connect(self.handle_filter_data)
        filter_window.exec_()  # блок родительского окна до закрытия

    def handle_filter_data(self, filter_data):
        # Обновляем таблицу с учетом фильтрации
        self.update_table(filter_data[0],filter_data[1])