from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget
)
from PySide6.QtCore import Qt

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.resize(500, 400)

        text = (
            "Система управления гостиницей\n\n"
            "Приложение разработано в рамках контрольной работы по дисциплине «Базы данных». Предметная область — гостиница.\n"
            "\n"
            "Возможности приложения:\n\n"
            "- Подключение к базе данных PostgreSQL.\n\n"
            "- Создание схемы (ENUM + таблицы) одной кнопкой.\n\n"
            "- Внесение данных в таблицы (clients, rooms, stays).\n\n"
            "- Просмотр данных в интерфейсе c различными фильтрами/сортировками/поиском.\n\n"
            "- Обновление данных.\n\n"
            "- Ведение лог-файла.\n\n"
            "- Обработка ошибок с понятными пользователю сообщениями.\n\n"
            "\n"
            "Авторы:\n\n"
            "Гончарова Маргарита, ЭФБО-03-24\n\n"
            "Емельянова Дарья, ЭФБО-03-24\n\n"
            "Доськова Мария, ЭФБО-03-24\n\n"
            "Жулева Дарья, ЭФБО-03-24\n\n"
        )

        label = QLabel(text)  # виджет label для текста
        label.setWordWrap(True)  # перенос строк по ширине окна

        scroll = QScrollArea()  # область прокрутки
        scroll.setWidgetResizable(True)

        scroll_content = QWidget()  # контейнер для содержимого
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.addWidget(label)

        scroll.setWidget(scroll_content)  # контейнер помещен в область прокрутки

        btn_close = QPushButton("Закрыть")  # кнопка для закрытия окна
        btn_close.clicked.connect(self.close)

        layout = QVBoxLayout()  # вертикальный layout для всего окна
        layout.addWidget(scroll)  # область прокрутки в layout
        layout.addWidget(btn_close, alignment=Qt.AlignRight)
        self.setLayout(layout)

        self.setStyleSheet("""
            QDialog { 
                background: #171a1d;  /* фон окна */
                color: #e8e6e3;       /* цвет текста */
                font-family: "Segoe UI", "Inter", "Roboto", Arial;
                font-size: 14px;
            }

            QLabel {
                color: #e8e6e3;
                font-size: 14px;
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

            QScrollArea {
                background: #171a1d;  /* фон скролл-области */
                border: none;
            }

            QScrollArea QWidget { 
                background: #171a1d;  /* фон контейнера внутри scroll */
            }
        """)

        self.setModal(True)