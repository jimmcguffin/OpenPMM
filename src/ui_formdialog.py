# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'formdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton,
    QScrollArea, QSizePolicy, QWidget)

class Ui_FormDialogClass(object):
    def setupUi(self, FormDialogClass):
        if not FormDialogClass.objectName():
            FormDialogClass.setObjectName(u"FormDialogClass")
        FormDialogClass.resize(893, 876)
        self.centralWidget = QWidget(FormDialogClass)
        self.centralWidget.setObjectName(u"centralWidget")
        self.cForm = QLabel(self.centralWidget)
        self.cForm.setObjectName(u"cForm")
        self.cForm.setGeometry(QRect(630, 695, 131, 126))
        self.cForm.setScaledContents(False)
        self.scrollArea = QScrollArea(self.centralWidget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(10, 45, 870, 830))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 868, 828))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.cSend = QPushButton(self.centralWidget)
        self.cSend.setObjectName(u"cSend")
        self.cSend.setGeometry(QRect(10, 10, 75, 30))
        FormDialogClass.setCentralWidget(self.centralWidget)

        self.retranslateUi(FormDialogClass)

        QMetaObject.connectSlotsByName(FormDialogClass)
    # setupUi

    def retranslateUi(self, FormDialogClass):
        FormDialogClass.setWindowTitle(QCoreApplication.translate("FormDialogClass", u"FormDialog", None))
        self.cForm.setText(QCoreApplication.translate("FormDialogClass", u"TextLabel", None))
        self.cSend.setText(QCoreApplication.translate("FormDialogClass", u"Send", None))
    # retranslateUi

