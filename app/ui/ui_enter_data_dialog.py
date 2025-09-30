# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'enter_data_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QRect, QSize, Qt, QRegularExpression)
from PySide6.QtGui import QRegularExpressionValidator
from app.db.db import HotelDB
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDateEdit, QDateTimeEdit, QDialog,
    QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QSpinBox, QStackedWidget, QVBoxLayout, QWidget, QMessageBox
)



COMFORT_ENUM = ["standard", "semi_lux", "lux"]

class Ui_EnterDataDialog(object):
    def setupUi(self, EnterDataDialog):
        if not EnterDataDialog.objectName():
            EnterDataDialog.setObjectName(u"EnterDataDialog")
        EnterDataDialog.resize(560, 420)
        EnterDataDialog.setStyleSheet(u"""
/* palette */
* { color:#e8e6e3; font-family:"Segoe UI","Inter","Roboto",Arial; font-size:14px; }
QDialog { background:#171a1d; }
QLabel { color:#e8e6e3; }
QLineEdit, QDateEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background:#242a30; border:1px solid #323a42; border-radius:8px; padding:6px;
}
QLineEdit:focus, QDateEdit:focus, QDateTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color:#6fbfa7;
}
QCheckBox { spacing:8px; }
QDialogButtonBox QPushButton {
    background:#242a30; border:1px solid #323a42; border-radius:10px; padding:8px 16px;
}
QDialogButtonBox QPushButton:hover { background:#2b3238; border-color:#3a444e; }
QDialogButtonBox QPushButton:pressed { background:#23292f; }
QPushButton#btnModeClient, QPushButton#btnModeRoom, QPushButton#btnModeStay {
    background:#20252a; border:1px solid #323a42; border-radius:10px; padding:8px 12px;
}
QPushButton#btnModeClient:hover, QPushButton#btnModeRoom:hover, QPushButton#btnModeStay:hover { background:#2b3238; }
QPushButton#btnModeClient:checked { background:#2e7d6b; border-color:#2c6f60; }
QPushButton#btnModeRoom:checked { background:#caa55b; color:#171a1d; border-color:#9b7d3f; }
QPushButton#btnModeStay:checked { background:#6b7dc0; border-color:#5061a6; }
QComboBox QAbstractItemView { background: #20252a; color: #e8e6e3; }
QCalendarWidget QTableView{ alternate-background-color: #20252a; background: #20252a;
    selection-background-color: #1e6d5b; }
QCalendarWidget QTableView::item:hover { background: #4b5258; }
QCalendarWidget QAbstractItemView:disabled { color: #7b7e82; background-color: #2a2f36; }
QMenu { background-color: #2a2f36; color: #e8e6e3; border: 1px solid #323a42; border-radius: 4px; }
QMenu::item:selected { background-color: #2e7d6b; color: white; }
""")


        self.vMain = QVBoxLayout(EnterDataDialog)
        self.vMain.setObjectName(u"vMain")

        # --- Header: title + mode buttons ---
        self.hHeader = QHBoxLayout()
        self.lblTitle = QLabel(EnterDataDialog)
        self.lblTitle.setObjectName(u"lblTitle")
        self.hHeader.addWidget(self.lblTitle)
        self.hHeader.addStretch(1)

        from PySide6.QtWidgets import QPushButton


        self.vMain.addLayout(self.hHeader)

        # --- Stacked pages ---
        self.stacked = QStackedWidget(EnterDataDialog)
        self.stacked.setObjectName(u"stacked")
        self.vMain.addWidget(self.stacked)

        # ===== Page: CLIENT =====
        self.pgClient = QWidget()
        self.lyClient = QFormLayout(self.pgClient)
        self.lyClient.setObjectName(u"lyClient")
        self.edLast = QLineEdit(self.pgClient); self.edLast.setObjectName(u"edLast")
        self.edLast.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^[a-zA-Zа-яА-ЯёЁ\s\-']{39}+$"), self.edLast))
        self.edLast.setPlaceholderText("Не более 39 символов")

        self.edFirst = QLineEdit(self.pgClient); self.edFirst.setObjectName(u"edFirst")
        self.edFirst.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^[a-zA-Zа-яА-ЯёЁ\s\-']{39}+$"), self.edFirst))
        self.edFirst.setPlaceholderText("Не более 39 символов")

        self.edPatr = QLineEdit(self.pgClient); self.edPatr.setObjectName(u"edPatr")
        self.edPatr.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^[a-zA-Zа-яА-ЯёЁ\s\-']{39}+$"), self.edPatr))
        self.edPatr.setPlaceholderText("Не более 39 символов")

        self.edPassport = QLineEdit(self.pgClient); self.edPassport.setObjectName(u"edPassport")
        self.edPassport.setObjectName(u"edPassport")
        self.edPassport.setMaxLength(11)
        self.edPassport.setPlaceholderText("Серия и Номер паспорта в формате \"#### ######\"")
        self.edPassport.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{4} \d{6}$"), self.edPassport))
                                           
        self.edComment = QLineEdit(self.pgClient); self.edComment.setObjectName(u"edComment")
        self.edComment.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^.{0, 150}+$"), self.edComment))
        self.edComment.setPlaceholderText("Не более 150 символов")
        self.cbRegular = QCheckBox(self.pgClient); self.cbRegular.setObjectName(u"cbRegular")
        self.dtRegistered = QDateTimeEdit(self.pgClient); self.dtRegistered.setObjectName(u"dtRegistered")
        self.dtRegistered.setCalendarPopup(True)
        self.dtRegistered.setDateTime(QDateTime.currentDateTime())

        self.lyClient.addRow(self._lbl("Фамилия *"), self.edLast)
        self.lyClient.addRow(self._lbl("Имя *"), self.edFirst)
        self.lyClient.addRow(self._lbl("Отчество"), self.edPatr)
        self.lyClient.addRow(self._lbl("Паспорт *"), self.edPassport)
        self.lyClient.addRow(self._lbl("Комментарий"), self.edComment)
        self.lyClient.addRow(self._lbl("Постоянный"), self.cbRegular)
        self.lyClient.addRow(self._lbl("Зарегистрирован"), self.dtRegistered)

        self.stacked.addWidget(self.pgClient)

        # ===== Page: ROOM =====
        self.pgRoom = QWidget()
        self.lyRoom = QFormLayout(self.pgRoom)
        self.lyRoom.setObjectName(u"lyRoom")
        self.sbRoomNumber = QSpinBox(self.pgRoom); self.sbRoomNumber.setMinimum(1); self.sbRoomNumber.setMaximum(9999)
        self.sbCapacity = QSpinBox(self.pgRoom); self.sbCapacity.setMinimum(1), self.sbCapacity.setMaximum(10)
        self.cbComfort = QComboBox(self.pgRoom); self.cbComfort.addItems(COMFORT_ENUM)
        self.dsPrice = QDoubleSpinBox(self.pgRoom); self.dsPrice.setDecimals(2); self.dsPrice.setMinimum(0.01); self.dsPrice.setMaximum(1_000_000.0)
        self.edAmenities = QLineEdit(self.pgRoom)
        self.edAmenities.setPlaceholderText("wifi, tv, conditioner")

        self.lyRoom.addRow(self._lbl("Удобства (через запятую)"), self.edAmenities)

        self.lyRoom.addRow(self._lbl("Номер *"), self.sbRoomNumber)
        self.lyRoom.addRow(self._lbl("Вместимость *"), self.sbCapacity)
        self.lyRoom.addRow(self._lbl("Комфорт *"), self.cbComfort)
        self.lyRoom.addRow(self._lbl("Цена/сутки *"), self.dsPrice)

        self.stacked.addWidget(self.pgRoom)

        # ===== Page: STAY =====
        self.pgStay = QWidget()
        self.lyStay = QFormLayout(self.pgStay)
        self.lyStay.setObjectName(u"lyStay")
        self.cbClient = QComboBox(self.pgStay); self.cbClient.setObjectName(u"cbClient")
        self.cbRoom = QComboBox(self.pgStay); self.cbRoom.setObjectName(u"cbRoom")
        self.deIn = QDateEdit(self.pgStay); self.deIn.setCalendarPopup(True); self.deIn.setDate(QDate.currentDate())
        self.deOut = QDateEdit(self.pgStay); self.deOut.setCalendarPopup(True); self.deOut.setDate(QDate.currentDate().addDays(1))
        self.edNote = QLineEdit(self.pgStay); self.edNote.setObjectName(u"edNote")
        self.edNote.setValidator(
            QRegularExpressionValidator(QRegularExpression(r"^.{0, 150}+$"), self.edNote))
        self.edNote.setPlaceholderText("Не более 150 символов")
        self.cbPaid = QCheckBox(self.pgStay); self.cbPaid.setObjectName(u"cbPaid")
        self.cbStatus = QCheckBox(self.pgStay); self.cbStatus.setObjectName(u"cbStatus"); self.cbStatus.setChecked(True)

        self.lyStay.addRow(self._lbl("Клиент *"), self.cbClient)
        self.lyStay.addRow(self._lbl("Номер *"), self.cbRoom)
        self.lyStay.addRow(self._lbl("Заезд *"), self.deIn)
        self.lyStay.addRow(self._lbl("Выезд *"), self.deOut)
        self.lyStay.addRow(self._lbl("Заметка"), self.edNote)
        self.lyStay.addRow(self._lbl("Оплачено"), self.cbPaid)
        self.lyStay.addRow(self._lbl("Активно"), self.cbStatus)

        self.stacked.addWidget(self.pgStay)

        # --- Buttons ---
        self.buttons = QDialogButtonBox(EnterDataDialog)
        self.buttons.setObjectName(u"buttons")
        self.buttons.setOrientation(Qt.Horizontal)
        self.buttons.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.vMain.addWidget(self.buttons)

        self.retranslateUi(EnterDataDialog)
        self.stacked.setCurrentIndex(0)
        QMetaObject.connectSlotsByName(EnterDataDialog)

    def _lbl(self, text):
        l = QLabel(text)
        l.setObjectName("formLabel")
        return l

    def retranslateUi(self, EnterDataDialog):
        EnterDataDialog.setWindowTitle(QCoreApplication.translate("EnterDataDialog", u"Ввод данных", None))
        self.lblTitle.setText(QCoreApplication.translate("EnterDataDialog", u"Режим: Клиент", None))
        self.cbRegular.setText(QCoreApplication.translate("EnterDataDialog", u"Постоянный клиент", None))
        self.cbPaid.setText(QCoreApplication.translate("EnterDataDialog", u"Оплачено", None))
        self.cbStatus.setText(QCoreApplication.translate("EnterDataDialog", u"Активно", None))
        self.dtRegistered.setDisplayFormat(QCoreApplication.translate("EnterDataDialog", u"dd.MM.yyyy HH:mm", None))
# end of Ui_EnterDataDialog


class EnterDataDialog(QDialog): # режимы для разных таблиц
    MODE_CLIENT = 0
    MODE_ROOM = 1
    MODE_STAY = 2

    def __init__(self, parent=None, clients=None, rooms=None, db=None):
        super().__init__(parent)

        self.mode = self.MODE_CLIENT
        self.ui = Ui_EnterDataDialog()
        self.ui.setupUi(self)
        self.db = db


        clients = clients or []
        rooms = rooms or []
        for c in clients:
            # ожидается dict{id, label}
            self.ui.cbClient.addItem(c["label"], c["id"])
        for r in rooms:
            self.ui.cbRoom.addItem(r["label"], r["id"])

        # кнопки
        self.ui.buttons.accepted.connect(self._on_ok)
        self.ui.buttons.rejected.connect(self.reject)


        self.setMode(self.MODE_CLIENT)

    def setMode(self, mode:int):
        self.mode = mode
        self.ui.stacked.setCurrentIndex(mode)
        title = ["Режим: Клиент", "Режим: Номер", "Режим: Размещение"][mode]
        self.ui.lblTitle.setText(title)

    def _on_ok(self):
        # валидации и сбор данных под каждый режим
        try:
            self.payload = self.collect()
        except ValueError as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Ошибка", str(e))
            return
        self.accept()

    def rightRegister(self, name):
        if not name:
            return ""
        name = name.lower()
        " ".join(name.split())
        hyphen_parts = []
        for part in name.split('-'):
            space_parts = [p.capitalize() for p in part.split()]
            hyphen_parts.append(' '.join(space_parts))

        return '-'.join(hyphen_parts)

    def collect(self) -> dict:
        if self.mode == self.MODE_CLIENT:
            last = self.rightRegister(name=self.ui.edLast.text().strip())
            first = self.rightRegister(name=self.ui.edFirst.text().strip())
            passport = self.ui.edPassport.text().strip()
            if not last or not first or len(passport) != 11:
                raise ValueError("Фамилия и Имя обязательны. Паспорт о формату через пробел.")
            return dict(
                last_name=last,
                first_name=first,
                patronymic=self.rightRegister(name=self.ui.edPatr.text().strip()) or None,
                passport=passport,
                comment=self.ui.edComment.text().strip() or None,
                is_regular=self.ui.cbRegular.isChecked(),
                registered=self.ui.dtRegistered.dateTime().toPython()
            )

        if self.mode == self.MODE_ROOM:
            rn = int(self.ui.sbRoomNumber.value())
            cap = int(self.ui.sbCapacity.value())
            price = float(self.ui.dsPrice.value())
            comfort = self.ui.cbComfort.currentText()
            amenities_text = self.ui.edAmenities.text().strip()
            amenities = [a.strip() for a in amenities_text.split(",") if a.strip()] if amenities_text else []
            if rn < 1 or cap < 1 or price <= 0:
                raise ValueError("Номер >= 1, вместимость >= 1, цена > 0.")
            if self.db.room_exists(room_number=rn):
                raise ValueError("Этот номер уже есть в базе.")
            return dict(
                room_number=rn,
                capacity=cap,
                comfort=comfort,
                price=price,
                amenities=amenities
            )

        if self.mode == self.MODE_STAY:
            if self.ui.cbClient.currentIndex() < 0 or self.ui.cbRoom.currentIndex() < 0:
                raise ValueError("Выберите клиента и номер.")
            ci = self.ui.deIn.date().toPython()
            co = self.ui.deOut.date().toPython()
            if co <= ci:
                raise ValueError("Дата выезда должна быть позже даты заезда.")
            return dict(
                client_id=self.ui.cbClient.currentData(),
                room_id=self.ui.cbRoom.currentData(),
                check_in=ci, check_out=co,
                is_paid=self.ui.cbPaid.isChecked(),
                note=self.ui.edNote.text().strip() or None,
                status=self.ui.cbStatus.isChecked()
            )

        raise ValueError("Неизвестный режим")
