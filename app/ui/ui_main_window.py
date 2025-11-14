# ui_main_window.py — правильный UI-класс для QMainWindow
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QSizePolicy, QWidget
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
        schema_frame = self._block("Работа со схемой")
        self.btn_create_schema = self._button("Создать схему и таблицы")
        schema_frame.layout().addWidget(self.btn_create_schema)
        main_layout.addWidget(schema_frame)

        self.btn_reset_schema = self._button("Сбросить базу")
        schema_frame.layout().addWidget(self.btn_reset_schema)

        # -------- блок 2: операции с данными --------
        data_frame = self._block("Работа с данными")
        self.btn_add_data = self._button("Внести данные")
        self.btn_show_data = self._button("Показать данные")
        data_frame.layout().addWidget(self.btn_add_data)
        data_frame.layout().addWidget(self.btn_show_data)
        main_layout.addWidget(data_frame)

        # -------- блок 3: ALTER TABLE --------
        alter_frame = self._block("ALTER TABLE")
        self.btn_alter = self._button("Изменить структуру")
        alter_frame.layout().addWidget(self.btn_alter)
        main_layout.addWidget(alter_frame)

        # -------- footer --------
        footer = QLabel("MLOps Mini-System • PostgreSQL • PySide6")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #777; font-size: 12px; margin-top: 20px;")
        main_layout.addWidget(footer)

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

    def _block(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #1d1f22;
                border: 1px solid #333;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        lbl.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(lbl)
        return frame

    def _button(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(42)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2d31;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #35373c;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #232528;
            }
        """)
        return btn
