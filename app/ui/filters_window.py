from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableView, QPushButton,
                               QMessageBox, QHBoxLayout, QComboBox, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem


class FilterWindow(QDialog):
    def __init__(self, parent=None, db=None):
        super().__init__(parent)  # вызов конструктора родительского класса
        self.setWindowTitle("Сделать фильтрацию по...")  # установка заголовка окна
        self.setModal(True)  # делаем окно модальным (блокирует родительское)
        self.setMinimumSize(550, 200)  # установка минимального размера окна
        self.filter_combo1 = QComboBox()
        self.filter_combo2 = QComboBox()

        # добавление стиля основного окна
        self.setStyleSheet("""
                    QDialog { 
                        background: #171a1d; 
                        color: #e8e6e3; 
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
                    QComboBox {
                    background: #242a30;
                    color: #e8e6e3;
                    border: 1px solid #323a42;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 14px;
                    }
                    QComboBox:hover {
                        background: #2b3238;
                    }
                    QLabel {
                        color: #e8e6e3;
                        font-size: 14px;
                        
                    }
                    """)

        self.setup_ui()

        if db is None:
            raise RuntimeError("Ошибка. Нет подключения к БД. Откройте сначала соединение.")
        self.db = db


    def setup_ui(self):
        layout = QVBoxLayout(self)  # создание вертикального layout

        filter_layout1 = QHBoxLayout()
        # выбор столбца фильтрации
        filter_label1 = QLabel("Фильтровать:")
        headers = ["ID", "Клиент", "Номер", "Комфорт", "Заезд", "Выезд", "Оплата", "Статус"]
        self.filter_combo1.addItems(headers)
        filter_layout1.addWidget(filter_label1)
        filter_layout1.addWidget(self.filter_combo1)
        layout.addLayout(filter_layout1)

        filter_layout2 = QHBoxLayout()
        filter_label2 = QLabel("По:")
        headers = ["возрастанию", "убыванию"]
        self.filter_combo2.addItems(headers)
        filter_layout2.addWidget(filter_label2)
        filter_layout2.addWidget(self.filter_combo2)
        layout.addLayout(filter_layout2)

        layout.addStretch()

        buttons_layout = QHBoxLayout()
        # кнопка обновления данных
        self.btn_refresh = QPushButton("Сбросить фильтры")
        self.btn_refresh.clicked.connect(self.filters_refresh)

        # кнопка фильтров
        self.btn_confirm = QPushButton("Применить")
        self.btn_confirm.clicked.connect(self.filters_confirm)

        # кнопка закрытия окна
        self.btn_close = QPushButton("Отмена")
        self.btn_close.clicked.connect(self.close)

        buttons_layout.addWidget(self.btn_refresh)  # сброс
        buttons_layout.addStretch()  # растягивающееся пространство
        buttons_layout.addWidget(self.btn_confirm)  # применить
        buttons_layout.addWidget(self.btn_close)  # закрыть

        layout.addLayout(buttons_layout)  # добавление layout с кнопками в основной layout


    def filters_refresh(self, ):
        # очищаем поля
        self.filter_combo1.setCurrentIndex(0)
        self.filter_combo2.setCurrentIndex(0)
        QMessageBox.information(self, "Фильтрация", "Фильтры сброшены")

    def filters_confirm(self):
        try:
            # получаем значения
            pass

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка применения фильтра: {str(e)}")