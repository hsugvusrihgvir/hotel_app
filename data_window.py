from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableView, QPushButton,
                               QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem


class DataWindow(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)  # вызов конструктора родительского класса
        self.db = db  # сохранение ссылки на базу данных
        self.setWindowTitle("Данные о бронированиях")  # установка заголовка окна
        self.setModal(True)  # делаем окно модальным (блокирует родительское)
        self.setMinimumSize(900, 500)  # установка минимального размера окна

        self.setup_ui()  # настройка пользовательского интерфейса
        self.load_data()  # загрузка данных при создании окна

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
        self.btn_update.clicked.connect(self.load_data)  # подключение сигнала к слоту

        # кнопка закрытия окна
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)  # подключение сигнала к слоту

        buttons_layout.addWidget(self.btn_update)  # добавление кнопки обновления
        buttons_layout.addStretch()  # добавляем растягивающееся пространство
        buttons_layout.addWidget(self.btn_close)  # добавление кнопки закрытия

        layout.addLayout(buttons_layout)  # добавление layout с кнопками в основной layout

    def load_data(self):
        if not self.db or not hasattr(self.db, 'conn') or not self.db.conn:  # проверка подключения к бд
            QMessageBox.warning(self, "Ошибка", "Нет подключения к базе данных")
            return

        try:
            # метод для выполнения запроса (если его нет в db.py)
            if not hasattr(self.db, 'execute_query'):
                self.add_execute_query_method()

            # простой join-запрос без фильтров
            query = (
                "SELECT \n"
                "    s.id,\n"
                "    c.last_name || ' ' || c.first_name as client,\n"
                "    r.room_number,\n"
                "    r.comfort,\n"
                "    s.check_in,\n"
                "    s.check_out,\n"
                "    CASE WHEN s.is_paid THEN 'Да' ELSE 'Нет' END as paid,\n"
                "    CASE WHEN s.status THEN 'Активно' ELSE 'Завершено' END as status\n"
                "FROM stays s\n"
                "JOIN clients c ON s.client_id = c.id\n"
                "JOIN rooms r ON s.room_id = r.id\n"
                "ORDER BY s.check_in DESC"
            )

            data = self.db.execute_query(query)  # выполнение запроса к бд
            self.update_table(data)  # обновление таблицы с полученными данными

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные:\n{str(e)}")

    def update_table(self, data):
        self.model.clear()  # очистка модели данных

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

    def add_execute_query_method(self):
        #добавляет метод execute_query к объекту базы данных если его нет

        def execute_query(query: str, params=None):
            #выполнение sql-запрос и возвращение результата
            if not self.db.conn:  # проверка наличия подключения к базе данных
                raise RuntimeError("Нет подключения к базе данных")  # исключение если подключения нет

            try:
                with self.db.conn.cursor() as cursor:  # создание курсора для выполнения запросов
                    cursor.execute(query, params or [])  # выполнение sql-запроса с параметрами
                    return cursor.fetchall()  # получение всех результатов запроса
            except Exception as e:  # обработка возможных ошибок
                raise RuntimeError(f"Ошибка выполнения запроса: {str(e)}")  # преобразование ошибки в RuntimeError

        # добавление метода к объекту базы данных
        self.db.execute_query = execute_query