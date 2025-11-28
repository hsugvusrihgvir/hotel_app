from PySide6.QtWidgets import (
    QVBoxLayout, QGridLayout, QPushButton,
    QLabel, QFrame, QSizePolicy, QWidget
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt

# цветовая палитра
# базовые фоны
WINDOW_BG = "#050816" # тёмный фон окна
CENTRAL_BG = "#020617" # фон центральной области
CARD_BG = "#111421" # фон карточек
CARD_BORDER = "#111827" # границы карточек

# текст
TEXT_MAIN = "#E5E7EB" # основной текст
TEXT_MUTED = "#9CA3AF" # подписи
TEXT_SOFT = "#CBD5F5" # заголовки

# акцентные цвета
ACCENT_PRIMARY = "#A5B4FC" # schema
ACCENT_SUCCESS = "#6EE7B7" # data
ACCENT_WARNING = "#FCD59F" # alter

# базовые кнопки
BTN_BG = "#1f202e" # фон нормальной кнопки
BTN_BG_HOVER = "#1F2937" # фон при наведении
BTN_BG_PRESSED = "#020617" # фон при нажатии
BTN_BORDER = "#1F2937" # граница кнопки
BTN_TEXT = "#E5E7EB" # текст на кнопке

# кнопка опасного действия
DANGER_BG = "#B96B6B"
DANGER_BG_HOVER = "#A95B5B"
DANGER_BG_PRESSED = "#8A4545"
DANGER_BORDER = "#9A5555"
DANGER_TEXT = "#FFF5F5"

# главное меню
class UIMainWindow(object):
    def setup_ui(self, MainWindow):
        MainWindow.setWindowTitle("AI-DDOS Lab — DB Manager")
        MainWindow.resize(960, 620)

        self._apply_dark_theme(MainWindow)  # базовые цвета

        central = QWidget()
        MainWindow.setCentralWidget(central)
        central.setStyleSheet(f"background-color: {CENTRAL_BG};")

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        header = QLabel("Управление базой данных")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet(f"color: {TEXT_SOFT};")
        main_layout.addWidget(header)

        # блок 1
        structure_frame = self._block("База и структура ツ", kind="primary")
        structure_layout = structure_frame.layout()

        structure_grid = QGridLayout()
        structure_grid.setHorizontalSpacing(12)
        structure_grid.setVerticalSpacing(8)
        structure_layout.addLayout(structure_grid)

        self.btn_create_schema = self._button("Создать схему и таблицы")
        self.btn_alter = self._button("Изменить структуру")
        self.btn_types = self._button("Пользовательские типы")
        self.btn_reset_schema = self._button_danger("Сбросить базу")

        # ряд 1
        structure_grid.addWidget(self.btn_create_schema, 0, 0)
        structure_grid.addWidget(self.btn_alter, 0, 1)

        # ряд 2
        structure_grid.addWidget(self.btn_types, 1, 0)
        structure_grid.addWidget(self.btn_reset_schema, 1, 1)

        main_layout.addWidget(structure_frame)

        # блок 2
        data_frame = self._block("Работа с данными \(^-^)/", kind="success")
        data_layout = data_frame.layout()

        data_grid = QGridLayout()
        data_grid.setHorizontalSpacing(12)
        data_grid.setVerticalSpacing(8)
        data_layout.addLayout(data_grid)

        self.btn_quick_view = self._button("Быстрый просмотр")
        self.btn_add_data = self._button("Внести данные")
        self.btn_show_data = self._button("Показать данные")

        # ряд 1
        data_grid.addWidget(self.btn_quick_view, 0, 0)
        data_grid.addWidget(self.btn_add_data, 0, 1)
        # ряд 2
        data_grid.addWidget(self.btn_show_data, 1, 0, 1, 2)

        main_layout.addWidget(data_frame)

        # блок 3
        queries_frame = self._block("Запросы и представления (✿◠‿◠)", kind="warning")
        queries_layout = queries_frame.layout()

        queries_grid = QGridLayout()
        queries_grid.setHorizontalSpacing(12)
        queries_grid.setVerticalSpacing(8)
        queries_layout.addLayout(queries_grid)

        self.btn_views = self._button("Представления и CTE")
        self.btn_cte_builder = self._button("Создать CTE (подзапрос)")

        queries_grid.addWidget(self.btn_views, 0, 0)
        queries_grid.addWidget(self.btn_cte_builder, 0, 1)

        main_layout.addWidget(queries_frame)


        footer = QLabel("	(╯°□°)╯︵ ┻━┻     	╰( ͡° ͜ʖ ͡° )つ──☆*:・ﾟ     	(◔_◔)")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; margin-top: 20px;"
        )
        main_layout.addWidget(footer)

        structure_frame.layout().setAlignment(Qt.AlignCenter)
        data_frame.layout().setAlignment(Qt.AlignCenter)
        queries_frame.layout().setAlignment(Qt.AlignCenter)

        # ограничения по ширине для кнопок
        for btn in (
                self.btn_create_schema,
                self.btn_alter,
                self.btn_types,
                self.btn_reset_schema,
                self.btn_quick_view,
                self.btn_add_data,
                self.btn_show_data,
                self.btn_views,
                self.btn_cte_builder,
        ):
            btn.setMaximumWidth(260)

    # базовые цвета
    def _apply_dark_theme(self, MainWindow):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(WINDOW_BG))
        palette.setColor(QPalette.WindowText, QColor(TEXT_MAIN))
        palette.setColor(QPalette.Base, QColor(CENTRAL_BG))
        palette.setColor(QPalette.AlternateBase, QColor(CARD_BG))
        palette.setColor(QPalette.Button, QColor(BTN_BG))
        palette.setColor(QPalette.ButtonText, QColor(BTN_TEXT))
        palette.setColor(QPalette.Text, QColor(TEXT_MAIN))
        palette.setColor(QPalette.Highlight, QColor(ACCENT_PRIMARY))
        palette.setColor(QPalette.HighlightedText, QColor(WINDOW_BG))

        MainWindow.setPalette(palette)
        MainWindow.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {WINDOW_BG};
                color: {TEXT_MAIN};
            }}
        """
        )

    # блок
    def _block(self, title: str, kind: str = "default") -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)

        # выбираем акцент под тип блока
        if kind == "primary":
            accent = ACCENT_PRIMARY
        elif kind == "success":
            accent = ACCENT_SUCCESS
        elif kind == "warning":
            accent = ACCENT_WARNING
        else:
            accent = "#4C566A"

        frame.setStyleSheet(
            f"""
            background-color: {CARD_BG};
            border-radius: 12px;
            border: 1px solid {CARD_BORDER};
            border-right: 0.5px solid {accent};
        """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl.setStyleSheet(f"color: {accent};")
        layout.addWidget(lbl)

        return frame

    def _button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(42)
        btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BTN_BG};
                color: {BTN_TEXT};
                border: 1px solid {BTN_BORDER};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 15px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {BTN_BG_HOVER};
                border-color: {BTN_BORDER};
            }}
            QPushButton:pressed {{
                background-color: {BTN_BG_PRESSED};
                border-color: {BTN_BORDER};
            }}
            QPushButton:disabled {{
                background-color: #252937;
                color: #9CA3AF;
                border-color: #3A4257;
            }}
        """
        )
        return btn

    def _button_danger(self, text: str) -> QPushButton:
        # опаснаяя кнопка сброса
        btn = QPushButton(text)
        btn.setMinimumHeight(42)
        btn.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {DANGER_BG};
                color: {DANGER_TEXT};
                border: 1px solid {DANGER_BORDER};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 15px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {DANGER_BG_HOVER};
                border-color: {DANGER_BORDER};
            }}
            QPushButton:pressed {{
                background-color: {DANGER_BG_PRESSED};
                border-color: {DANGER_BORDER};
            }}
            QPushButton:disabled {{
                background-color: #4B3A3A;
                color: #E5E7EB;
                border-color: #6B4A4A;
            }}
        """
        )
        return btn
