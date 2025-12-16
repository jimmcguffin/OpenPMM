# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'logsettingsdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QGroupBox,
    QPushButton, QSizePolicy, QWidget)

class Ui_LogSettingsDialogClass(object):
    def setupUi(self, LogSettingsDialogClass):
        if not LogSettingsDialogClass.objectName():
            LogSettingsDialogClass.setObjectName(u"LogSettingsDialogClass")
        LogSettingsDialogClass.resize(490, 430)
        self.cOK = QPushButton(LogSettingsDialogClass)
        self.cOK.setObjectName(u"cOK")
        self.cOK.setGeometry(QRect(335, 395, 75, 30))
        self.cCancel = QPushButton(LogSettingsDialogClass)
        self.cCancel.setObjectName(u"cCancel")
        self.cCancel.setGeometry(QRect(410, 395, 75, 30))
        self.groupBox = QGroupBox(LogSettingsDialogClass)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 476, 156))
        self.cL1 = QCheckBox(self.groupBox)
        self.cL1.setObjectName(u"cL1")
        self.cL1.setGeometry(QRect(20, 25, 400, 20))
        self.cL2 = QCheckBox(self.groupBox)
        self.cL2.setObjectName(u"cL2")
        self.cL2.setGeometry(QRect(20, 55, 400, 20))
        self.cL3 = QCheckBox(self.groupBox)
        self.cL3.setObjectName(u"cL3")
        self.cL3.setGeometry(QRect(20, 85, 400, 20))
        self.cL4 = QCheckBox(self.groupBox)
        self.cL4.setObjectName(u"cL4")
        self.cL4.setGeometry(QRect(20, 110, 400, 20))

        self.retranslateUi(LogSettingsDialogClass)
        self.cOK.clicked.connect(LogSettingsDialogClass.accept)
        self.cCancel.clicked.connect(LogSettingsDialogClass.reject)

        QMetaObject.connectSlotsByName(LogSettingsDialogClass)
    # setupUi

    def retranslateUi(self, LogSettingsDialogClass):
        LogSettingsDialogClass.setWindowTitle(QCoreApplication.translate("LogSettingsDialogClass", u"LogSettingsDialog", None))
        self.cOK.setText(QCoreApplication.translate("LogSettingsDialogClass", u"OK", None))
        self.cCancel.setText(QCoreApplication.translate("LogSettingsDialogClass", u"Cancel", None))
        self.groupBox.setTitle(QCoreApplication.translate("LogSettingsDialogClass", u"Options", None))
        self.cL1.setText(QCoreApplication.translate("LogSettingsDialogClass", u"L1: Send/Receive session window logging", None))
        self.cL2.setText(QCoreApplication.translate("LogSettingsDialogClass", u"L2: Send/Receive interface data trace", None))
        self.cL3.setText(QCoreApplication.translate("LogSettingsDialogClass", u"L3: Send/Receive diagnostic trace", None))
        self.cL4.setText(QCoreApplication.translate("LogSettingsDialogClass", u"L4: Main program diagnostics trace (restart to apply)", None))
    # retranslateUi

