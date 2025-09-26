from PySide6.QtWidgets import (QDialog, QVBoxLayout, QTableView, QPushButton,
                               QMessageBox, QHBoxLayout, QComboBox, QLabel, QDateEdit, QCheckBox)
from PySide6.QtCore import (Qt, Signal, QDate)
from PySide6.QtGui import QStandardItemModel, QStandardItem


class FilterWindow(QDialog):
    filterApplied = Signal(dict) # сигнал для передачи данных

    def __init__(self, parent=None, db=None):
        super().__init__(parent)  # вызов конструктора родительского класса
        self.setWindowTitle("Сделать фильтрацию по...")  # установка заголовка окна
        self.setModal(True)  # делаем окно модальным (блокирует родительское)
        self.setMinimumSize(550, 400)  # установка минимального размера окна

        # галочки
        self.sort_checkbox = QCheckBox("Сортировка по столбцу")
        self.date_checkbox = QCheckBox("Фильтр по датам")

        # открывающийся фильтр
        self.filter_combo1 = QComboBox()
        self.filter_combo2 = QComboBox()

        # выбор даты
        self.date_from = QDateEdit()
        self.date_to = QDateEdit()

        # добавление стиля окна
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
                    QCheckBox {
                        color: #e8e6e3;
                        font-size: 14px;
                    }
                    QDateEdit {
                        background: #242a30;
                        color: #e8e6e3;
                        border: 1px solid #323a42;
                        border-radius: 5px;
                        padding: 5px;
            }
                    """)

        self.setup_ui()

        if db is None:
            raise RuntimeError("Ошибка. Нет подключения к БД. Откройте сначала соединение.")
        self.db = db


    def setup_ui(self):
        layout = QVBoxLayout(self)  # создание вертикального layout

        self.setup_sort(layout)
        self.setup_date(layout)
        self.set_buttons(layout)


    def setup_sort(self, layout):
        # сортировка
        sort_layout = QHBoxLayout()
        self.sort_checkbox.setChecked(False)
        self.sort_checkbox.toggled.connect(self.on_sort_toggled)
        sort_layout.addWidget(self.sort_checkbox)
        sort_layout.addStretch()
        layout.addLayout(sort_layout)  # добавление в основной layout

        filter_layout1 = QHBoxLayout()
        headers = ["ID", "Клиент", "Номер", "Комфорт", "Заезд", "Выезд", "Оплата", "Статус"]
        self.filter_combo1.addItems(headers)
        self.filter_combo1.setEnabled(False)
        filter_layout1.addWidget(self.filter_combo1)
        layout.addLayout(filter_layout1)

        filter_layout2 = QHBoxLayout()
        sort_var = ["по возрастанию", "по убыванию"]
        self.filter_combo2.addItems(sort_var)
        self.filter_combo2.setEnabled(False)
        filter_layout2.addWidget(self.filter_combo2)
        layout.addLayout(filter_layout2)
        layout.addStretch()

    def on_sort_toggled(self, checked):
        self.filter_combo1.setEnabled(checked)
        self.filter_combo2.setEnabled(checked)


    def setup_date(self, layout):
        # по дате
        date_layout = QHBoxLayout()
        self.date_checkbox.setChecked(False)
        self.date_checkbox.toggled.connect(self.on_date_toggled)
        date_layout.addWidget(self.date_checkbox)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        # заезд
        checkin_layout = QHBoxLayout()
        checkin_label = QLabel("Заезд с:")
        self.date_from.setDate(QDate.currentDate().addDays(-30))  # последние 30 дней
        self.date_from.setCalendarPopup(True)
        self.date_from.setEnabled(False)
        checkin_layout.addWidget(checkin_label)
        checkin_layout.addWidget(self.date_from)
        checkin_layout.addStretch()
        layout.addLayout(checkin_layout)

        # выезд
        checkout_layout = QHBoxLayout()
        checkout_label = QLabel("Выезд по:")
        self.date_to.setDate(QDate.currentDate().addDays(30))
        self.date_to.setCalendarPopup(True)
        self.date_to.setEnabled(False)
        checkout_layout.addWidget(checkout_label)
        checkout_layout.addWidget(self.date_to)
        checkout_layout.addStretch()
        layout.addLayout(checkout_layout)

        layout.addStretch()

    def on_date_toggled(self, checked):
        self.date_from.setEnabled(checked)
        self.date_to.setEnabled(checked)


    def set_buttons(self, layout):
        # кнопки
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

        layout.addLayout(buttons_layout)  # добавление в основной layout


    def filters_refresh(self, ):
        try:
            # чекбоксы
            self.sort_checkbox.setChecked(False)
            self.date_checkbox.setChecked(False)

            # комбобоксы
            self.filter_combo1.setCurrentIndex(0)
            self.filter_combo2.setCurrentIndex(0)

            # даты
            self.date_from.setDate(QDate.currentDate().addDays(-30))
            self.date_to.setDate(QDate.currentDate().addDays(30))

            QMessageBox.information(self, "Фильтрация", "Фильтры сброшены")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f": {str(e)}")


    def filters_confirm(self):
        try:
            filter_params = {
                'use_sort': self.sort_checkbox.isChecked(),
                'use_date': self.date_checkbox.isChecked(),
            }
            if filter_params['use_sort']:
                sort_params = self.sort_check()
                if sort_params is not None:
                    filter_params.update(sort_params)
                else:
                    return

            if filter_params['use_date']:
                date_from_to = self.date_check()
                if date_from_to is not None:
                    filter_params.update(date_from_to)
                else: return

            self.filterApplied.emit(filter_params)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка применения фильтра: {str(e)}")


    def sort_check(self):
        try:
            return {
                'sort_column': self.filter_combo1.currentText(),
                'sort_order': self.filter_combo2.currentText()
            }
        except Exception as e:
            raise Exception(f"Ошибка в настройках сортировки: {str(e)}")


    def date_check(self):
        try:
            date_from = self.date_from.date()
            date_to = self.date_to.date()
            # проверка даты
            if self.date_from.date() > self.date_to.date():
                QMessageBox.warning(self, "Предупреждение",
                                    "Дата 'с' не может быть больше даты 'по'")
                return None
            return {
                'date_from': date_from.toString("yyyy-MM-dd"),
                'date_to': date_to.toString("yyyy-MM-dd")
            }
        except Exception as e:
            raise Exception(f"Ошибка в настройках даты: {str(e)}")