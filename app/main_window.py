import sys, csv, os, logging
from dataclasses import dataclass
from contextlib import contextmanager

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog,
)
from PySide6.QtCore import Slot

from app.ui.ui_main_window import Ui_MainWindow

import psycopg2
from psycopg2.extras import RealDictCursor


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.db = None  # здесь будет объект подключения к PostgreSQL

        # связи кнопок
        self.ui.btnConnect.clicked.connect(self.on_connect)
        self.ui.btnCreateSchema.clicked.connect(self.on_create_schema)
        self.ui.btnShowData.clicked.connect(self.on_show_data)
        self.ui.btnEnterData.clicked.connect(self.on_enter_data)
        self.ui.btnUpdate.clicked.connect(self.on_update)
        self.ui.btnOpenLog.clicked.connect(self.on_open_log)
        self.ui.btnAbout.clicked.connect(self.on_about)
        self.ui.btnExit.clicked.connect(self.close)

    @Slot()
    def on_connect(self) -> None:
        pass

    @Slot()
    def on_create_schema(self) -> None:
        pass


    @Slot()
    def on_show_data(self) -> None:
        pass


    @Slot()
    def on_enter_data(self) -> None:
        pass


    @Slot()
    def on_update(self) -> None:
        pass


    @Slot()
    def on_open_log(self) -> None:
        pass


    @Slot()
    def on_about(self) -> None:
        pass



    # ---------- helpers ----------
    def _confirm(self, text: str) -> bool:
        pass

