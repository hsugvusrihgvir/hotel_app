# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        MainWindow.setStyleSheet(u"/* \n"
"\n"
"QMainWindow, QWidget#centralwidget {\n"
"    background: #171a1d;\n"
"    color: #e8e6e3;\n"
"    font-family: \"Segoe UI\", \"Inter\", \"Roboto\", Arial;\n"
"    font-size: 14px;\n"
"}\n"
"\n"
"/* \u041a\u043d\u043e\u043f\u043a\u0438 \u043f\u043e \u0443\u043c\u043e\u043b\u0447\u0430\u043d\u0438\u044e */\n"
"QPushButton {\n"
"    background: #242a30;\n"
"    color: #e8e6e3;\n"
"    border: 1px solid #323a42;\n"
"    border-radius: 12px;\n"
"    padding: 8px 16px;\n"
"    min-height: 34px;\n"
"}\n"
"QPushButton:hover {\n"
"    background: #2b3238;\n"
"    border-color: #3a444e;\n"
"}\n"
"QPushButton:pressed {\n"
"    background: #23292f;\n"
"    border-color: #46525e;\n"
"}\n"
"QP"
                        "ushButton:disabled {\n"
"    color: #7b7e82;\n"
"    background: #1f2327;\n"
"    border-color: #2a3036;\n"
"}\n"
"\n"
"QPushButton#btnConnect,\n"
"QPushButton#btnEnterData {\n"
"    background: #2e7d6b;\n"
"    border: 1px solid #2c6f60;\n"
"}\n"
"QPushButton#btnConnect:hover,\n"
"QPushButton#btnEnterData:hover {\n"
"    background: #338a76;\n"
"    border-color: #2f7b6a;\n"
"}\n"
"QPushButton#btnConnect:pressed,\n"
"QPushButton#btnEnterData:pressed {\n"
"    background: #28715f;\n"
"}\n"
"\n"
"QPushButton#btnCreateSchema,\n"
"QPushButton#btnShowData {\n"
"    background: #caa55b;\n"
"    color: #171a1d;\n"
"    border: 1px solid #9b7d3f;\n"
"}\n"
"QPushButton#btnCreateSchema:hover,\n"
"QPushButton#btnShowData:hover {\n"
"    background: #d6b473;\n"
"}\n"
"QPushButton#btnCreateSchema:pressed,\n"
"QPushButton#btnShowData:pressed {\n"
"    background: #b89149;\n"
"}\n"
"\n"
"QPushButton#btnOpenLog, QPushButton#btnAbout, QPushButton#btnExit {\n"
"    background: #242a30;\n"
"}\n"
"QPushButton#btnExit:hover { bor"
                        "der-color: #c45b5b; color: #ffdddd; }\n"
"")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btnExit = QPushButton(self.centralwidget)
        self.btnExit.setObjectName(u"btnExit")
        self.btnExit.setMinimumSize(QSize(225, 52))
        self.btnExit.setMaximumSize(QSize(200, 50))

        self.horizontalLayout.addWidget(self.btnExit)

        self.btnAbout = QPushButton(self.centralwidget)
        self.btnAbout.setObjectName(u"btnAbout")
        self.btnAbout.setMinimumSize(QSize(225, 52))
        self.btnAbout.setMaximumSize(QSize(225, 50))

        self.horizontalLayout.addWidget(self.btnAbout)

        self.btnOpenLog = QPushButton(self.centralwidget)
        self.btnOpenLog.setObjectName(u"btnOpenLog")
        self.btnOpenLog.setMinimumSize(QSize(225, 52))
        self.btnOpenLog.setMaximumSize(QSize(225, 50))

        self.horizontalLayout.addWidget(self.btnOpenLog)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.btnShowData = QPushButton(self.centralwidget)
        self.btnShowData.setObjectName(u"btnShowData")
        self.btnShowData.setMinimumSize(QSize(300, 52))

        self.verticalLayout_3.addWidget(self.btnShowData)

        self.btnEnterData = QPushButton(self.centralwidget)
        self.btnEnterData.setObjectName(u"btnEnterData")
        self.btnEnterData.setMinimumSize(QSize(0, 52))

        self.verticalLayout_3.addWidget(self.btnEnterData)

        self.btnUpdate = QPushButton(self.centralwidget)
        self.btnUpdate.setObjectName(u"btnUpdate")
        self.btnUpdate.setMinimumSize(QSize(0, 52))

        self.verticalLayout_3.addWidget(self.btnUpdate)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btnConnect = QPushButton(self.centralwidget)
        self.btnConnect.setObjectName(u"btnConnect")

        self.horizontalLayout_2.addWidget(self.btnConnect)

        self.btnCreateSchema = QPushButton(self.centralwidget)
        self.btnCreateSchema.setObjectName(u"btnCreateSchema")

        self.horizontalLayout_2.addWidget(self.btnCreateSchema)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.btnExit.setText(QCoreApplication.translate("MainWindow", u"\u0412\u044b\u0445\u043e\u0434", None))
        self.btnAbout.setText(QCoreApplication.translate("MainWindow", u"\u041e \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0435", None))
        self.btnOpenLog.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0442\u043a\u0440\u044b\u0442\u044c \u043b\u043e\u0433-\u0444\u0430\u0439\u043b", None))
        self.btnShowData.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u0434\u0430\u043d\u043d\u044b\u0435", None))
        self.btnEnterData.setText(QCoreApplication.translate("MainWindow", u"\u0412\u043d\u0435\u0441\u0442\u0438 \u0434\u0430\u043d\u043d\u044b\u0435", None))
        self.btnUpdate.setText(QCoreApplication.translate("MainWindow", u"\u041e\u0431\u043d\u043e\u0432\u0438\u0442\u044c", None))
        self.btnConnect.setText(QCoreApplication.translate("MainWindow", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u0441\u044f", None))
        self.btnCreateSchema.setText(QCoreApplication.translate("MainWindow", u"\u0421\u043e\u0437\u0434\u0430\u0442\u044c \u0441\u0445\u0435\u043c\u0443", None))
    # retranslateUi

