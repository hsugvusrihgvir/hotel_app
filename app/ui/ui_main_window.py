# ui_main_window.py — правильный UI-класс для QMainWindow
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QSizePolicy, QWidget
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt


class UIMainWindow(object):
    """генератор UI для главного окна"""

    def setup_ui(self, MainWindow):
        MainWindow.setWindowTitle("AI-DDOS Lab — DB Manager")
        MainWindow.resize(960, 620)
        self._apply_dark_theme(MainWindow)

        central = QWidget()
        MainWindow.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # -------- header --------
        header = QLabel("Управление базой данных")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setAlignment(Qt.AlignLeft)
        header.setStyleSheet("color: #e0e0e0;")
        main_layout.addWidget(header)

        # -------- блок 1: операции со схемой --------
        schema_frame = self._block("Работа со схемой", kind="primary")
        schema_layout = schema_frame.layout()

        schema_grid = QGridLayout()
        schema_grid.setHorizontalSpacing(12)
        schema_grid.setVerticalSpacing(8)
        schema_layout.addLayout(schema_grid)

        self.btn_create_schema = self._button("Создать схему и таблицы")
        self.btn_reset_schema = self._button_danger("Сбросить базу")
        self.btn_types = self._button("Пользовательские типы")
        self.btn_views = self._button("Представления и CTE")
        self.btn_cte_builder = self._button("Создать CTE (подзапрос)")

        # раскладка по сетке 2×3
        # 1 ряд
        schema_grid.addWidget(self.btn_create_schema, 0, 0)
        schema_grid.addWidget(self.btn_reset_schema, 0, 1)
        # 2 ряд
        schema_grid.addWidget(self.btn_types, 1, 0)
        schema_grid.addWidget(self.btn_views, 1, 1)
        # 3 ряд — кнопка на всю ширину
        schema_grid.addWidget(self.btn_cte_builder, 2, 0, 1, 2)

        main_layout.addWidget(schema_frame)

        # -------- блок 2: операции с данными --------
        data_frame = self._block("Работа с данными", kind="success")
        data_layout = data_frame.layout()

        data_grid = QGridLayout()
        data_grid.setHorizontalSpacing(12)
        data_grid.setVerticalSpacing(8)
        data_layout.addLayout(data_grid)

        self.btn_quick_view = self._button("Быстрый просмотр")
        self.btn_add_data = self._button("Внести данные")
        self.btn_show_data = self._button("Показать данные")

        # 1 ряд
        data_grid.addWidget(self.btn_quick_view, 0, 0)
        data_grid.addWidget(self.btn_add_data, 0, 1)
        # 2 ряд — на всю ширину
        data_grid.addWidget(self.btn_show_data, 1, 0, 1, 2)

        main_layout.addWidget(data_frame)

        # -------- блок 3: ALTER TABLE --------
        alter_frame = self._block("ALTER TABLE", kind="warning")
        self.btn_alter = self._button("Изменить структуру")
        alter_frame.layout().addWidget(self.btn_alter)
        main_layout.addWidget(alter_frame)

        # -------- footer --------
        footer = QLabel("MLOps Mini-System • PostgreSQL • PySide6")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #777; font-size: 12px; margin-top: 20px;")
        main_layout.addWidget(footer)

        schema_frame.layout().setAlignment(Qt.AlignCenter)
        data_frame.layout().setAlignment(Qt.AlignCenter)
        alter_frame.layout().setAlignment(Qt.AlignCenter)

        # И сами кнопки
        self.btn_create_schema.setMaximumWidth(260)
        self.btn_reset_schema.setMaximumWidth(260)
        self.btn_types.setMaximumWidth(260)
        self.btn_views.setMaximumWidth(260)
        self.btn_cte_builder.setMaximumWidth(260)

        self.btn_quick_view.setMaximumWidth(260)
        self.btn_add_data.setMaximumWidth(260)
        self.btn_show_data.setMaximumWidth(260)
        self.btn_alter.setMaximumWidth(260)


    # =======================
    # helpers
    # =======================

    def _apply_dark_theme(self, MainWindow):
        """тёмная палитра"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(20, 22, 25))
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
        palette.setColor(QPalette.Base, QColor(30, 32, 36))
        palette.setColor(QPalette.Button, QColor(45, 47, 52))
        palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.Text, QColor(230, 230, 230))
        palette.setColor(QPalette.Highlight, QColor(60, 90, 200))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        MainWindow.setPalette(palette)
        MainWindow.setStyleSheet("background-color: #141618;")

    def _block(self, title: str, kind: str = "default") -> QFrame:
        """Цветной блок с заголовком (пастельные цвета)."""

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)

        # мягкие оттенки
        if kind == "primary":
            accent = "#8BA4E0"  # мягкий голубой
        elif kind == "success":
            accent = "#7AC29A"  # мягкий мятный
        elif kind == "warning":
            accent = "#E6B980"  # персиково-бежевый
        else:
            accent = "#4C566A"  # спокойный серо-синий

        frame.setStyleSheet(f"""
               QFrame {{
                   background-color: #191b22;        /* фон блока */
                   border: 1px solid #262933;
                   border-radius: 10px;
                   border-left: 4px solid {accent};  /* цветная лента слева */
               }}
           """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl.setStyleSheet(f"color: {accent};")  # заголовок в том же мягком цвете
        layout.addWidget(lbl)

        return frame

    def _button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(42)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet("""
               QPushButton {
                   background-color: #3F4F79;   /* приглушённый синий */
                   color: #F5F5F7;
                   border: 1px solid #323A52;
                   border-radius: 8px;
                   padding: 6px 14px;
                   font-size: 15px;
                   font-weight: 500;
               }
               QPushButton:hover {
                   background-color: #364568;   /* чуть темнее при hover */
                   border-color: #2B3550;
               }
               QPushButton:pressed {
                   background-color: #2B3452;
                   border-color: #222A40;
               }
               QPushButton:disabled {
                   background-color: #252937;
                   color: #9CA3AF;
                   border-color: #3A4257;
               }
           """)
        return btn


    def _button_danger(self, text: str) -> QPushButton:
        """Кнопка для опасных действий (сброс базы и т.п.) в мягком красном."""
        btn = QPushButton(text)
        btn.setMinimumHeight(42)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #B96B6B;   /* мягкий кирпичный */
                color: #FFF5F5;
                border: 1px solid #9A5555;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #A95B5B;
                border-color: #874545;
            }
            QPushButton:pressed {
                background-color: #8A4545;
                border-color: #6B3434;
            }
            QPushButton:disabled {
                background-color: #4B3A3A;
                color: #E5E7EB;
                border-color: #6B4A4A;
            }
        """)
        return btn
