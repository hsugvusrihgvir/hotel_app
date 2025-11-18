from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QFrame
)
from PySide6.QtCore import Qt


class CollapsibleSection(QWidget):
    """Универсальная сворачиваемая секция."""

    def __init__(self, title: str, content_widget: QWidget, parent=None):
        super().__init__(parent)

        self.title = title
        self.content = content_widget
        self.is_open = False

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # кнопка-секция
        self.btn = QPushButton(f"▸ {self.title}")
        self.btn.setCheckable(True)
        self.btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                background-color: #1D1F22;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 6px 8px;
                color: #dcdcdc;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #25272A;
            }
        """)
        self.btn.clicked.connect(self._toggle)
        layout.addWidget(self.btn)

        # контейнер для содержимого
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: #18191b;
                border: 1px solid #333;
                border-radius: 6px;
            }
        """)
        self.content_frame.setLayout(QVBoxLayout())
        self.content_frame.layout().addWidget(self.content)
        self.content_frame.setVisible(False)

        layout.addWidget(self.content_frame)

    def _toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            self.btn.setText(f"▾ {self.title}")
            self.content_frame.setVisible(True)
        else:
            self.btn.setText(f"▸ {self.title}")
            self.content_frame.setVisible(False)
