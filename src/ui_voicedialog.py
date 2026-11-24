# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'voicedialog.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QDateTimeEdit, QDialog, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(502, 228)
        self.c_from_call = QLineEdit(Dialog)
        self.c_from_call.setObjectName(u"c_from_call")
        self.c_from_call.setGeometry(QRect(90, 40, 155, 24))
        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(10, 15, 80, 16))
        self.c_time = QDateTimeEdit(Dialog)
        self.c_time.setObjectName(u"c_time")
        self.c_time.setGeometry(QRect(90, 10, 160, 24))
        self.c_time.setDateTime(QDateTime(QDate(2026, 4, 24), QTime(0, 0, 0)))
        self.c_time.setDate(QDate(2026, 4, 24))
        self.c_time.setMinimumDateTime(QDateTime(QDate(2020, 1, 1), QTime(0, 0, 0)))
        self.c_time.setCalendarPopup(True)
        self.c_ok = QPushButton(Dialog)
        self.c_ok.setObjectName(u"c_ok")
        self.c_ok.setGeometry(QRect(320, 190, 75, 24))
        self.c_cancel = QPushButton(Dialog)
        self.c_cancel.setObjectName(u"c_cancel")
        self.c_cancel.setGeometry(QRect(400, 190, 75, 24))
        self.c_from_message = QLineEdit(Dialog)
        self.c_from_message.setObjectName(u"c_from_message")
        self.c_from_message.setGeometry(QRect(90, 70, 155, 24))
        self.c_to_call = QLineEdit(Dialog)
        self.c_to_call.setObjectName(u"c_to_call")
        self.c_to_call.setGeometry(QRect(90, 100, 155, 24))
        self.c_to_message = QLineEdit(Dialog)
        self.c_to_message.setObjectName(u"c_to_message")
        self.c_to_message.setGeometry(QRect(90, 130, 155, 24))
        self.c_message = QLineEdit(Dialog)
        self.c_message.setObjectName(u"c_message")
        self.c_message.setGeometry(QRect(90, 160, 395, 24))
        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(10, 45, 80, 16))
        self.label_6 = QLabel(Dialog)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(10, 75, 80, 16))
        self.label_7 = QLabel(Dialog)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(10, 105, 80, 16))
        self.label_8 = QLabel(Dialog)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(10, 135, 80, 16))
        self.label_9 = QLabel(Dialog)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setGeometry(QRect(10, 165, 80, 16))
        QWidget.setTabOrder(self.c_time, self.c_from_call)
        QWidget.setTabOrder(self.c_from_call, self.c_from_message)
        QWidget.setTabOrder(self.c_from_message, self.c_to_call)
        QWidget.setTabOrder(self.c_to_call, self.c_to_message)
        QWidget.setTabOrder(self.c_to_message, self.c_message)
        QWidget.setTabOrder(self.c_message, self.c_ok)
        QWidget.setTabOrder(self.c_ok, self.c_cancel)

        self.retranslateUi(Dialog)
        self.c_ok.clicked.connect(Dialog.accept)
        self.c_cancel.clicked.connect(Dialog.reject)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Voice", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"Time", None))
        self.c_time.setDisplayFormat(QCoreApplication.translate("Dialog", u"MM-dd-yyyy HH:mm", None))
        self.c_ok.setText(QCoreApplication.translate("Dialog", u"OK", None))
        self.c_cancel.setText(QCoreApplication.translate("Dialog", u"Cancel", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"From call", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"From msg#", None))
        self.label_7.setText(QCoreApplication.translate("Dialog", u"To call", None))
        self.label_8.setText(QCoreApplication.translate("Dialog", u"To msg#", None))
        self.label_9.setText(QCoreApplication.translate("Dialog", u"Message", None))
    # retranslateUi

