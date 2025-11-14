# ui_enter_data_dialog.py — UI-форма для ввода данных (динамическая, исправленный setupUi)

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QLineEdit, QComboBox, QCheckBox, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt


class UIEnterDataDialog(object):
    """модальное окно для динамического ввода данных"""

    def setupUi(self, Dialog):
        Dialog.setWindowTitle("Добавить запись")
        Dialog.resize(520, 600)
        Dialog.setModal(True)
        self._apply_dark_theme(Dialog)

        # основной layout
        self.main_layout = QVBoxLayout(Dialog)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # заголовок
        self.title = QLabel("Добавление данных")
        self.title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title.setStyleSheet("color: #e0e0e0; margin-bottom: 5px;")
        self.main_layout.addWidget(self.title)

        # блок полей со скроллом
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.scroll_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.scroll_widget)
        self.fields_layout.setContentsMargins(5, 5, 5, 5)
        self.fields_layout.setSpacing(12)

        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

        # кнопки
        self.btn_box = QHBoxLayout()
        self.btn_box.setSpacing(15)

        self.btn_save = self._button("Сохранить")
        self.btn_cancel = self._button("Отмена")

        self.btn_box.addWidget(self.btn_save)
        self.btn_box.addWidget(self.btn_cancel)

        self.main_layout.addLayout(self.btn_box)

        # селектор таблицы (необязателен в UI, но используется в коде)
        self.table_selector = QComboBox()
        self.table_selector.setStyleSheet(self._combo_style())
        self.main_layout.insertWidget(1, self.table_selector)

    # =============================
    # вспомогательные методы UI
    # =============================

    def _apply_dark_theme(self, widget):
        """тёмная палитра"""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(20, 22, 25))
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
        palette.setColor(QPalette.Base, QColor(30, 32, 36))
        palette.setColor(QPalette.Text, QColor(230, 230, 230))
        palette.setColor(QPalette.Button, QColor(45, 47, 52))
        palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
        widget.setPalette(palette)
        widget.setStyleSheet("background-color: #141618;")

    def _field_frame(self):
        """контейнер для одного поля"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #1d1f22;
                border: 1px solid #333;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        return frame

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #c8c8c8; font-size: 14px;")
        return lbl

    def _edit_style(self):
        return """
            QLineEdit {
                background-color: #2b2d31;
                color: #e8e8e8;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus {
                border-color: #6b8cff;
            }
        """

    def _combo_style(self):
        return """
            QComboBox {
                background-color: #2b2d31;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox:hover {
                border-color: #666;
            }
        """

    def _button(self, text):
        btn = QPushButton(text)
        btn.setMinimumHeight(40)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2e3136;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #393c42;
            }
            QPushButton:pressed {
                background-color: #24272c;
            }
        """)
        return btn
