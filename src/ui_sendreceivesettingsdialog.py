# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sendreceivesettingsdialog.ui'
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
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QSpinBox, QTabWidget, QWidget)

class Ui_SendReceiveSettingsDialogClass(object):
    def setupUi(self, SendReceiveSettingsDialogClass):
        if not SendReceiveSettingsDialogClass.objectName():
            SendReceiveSettingsDialogClass.setObjectName(u"SendReceiveSettingsDialogClass")
        SendReceiveSettingsDialogClass.resize(490, 430)
        self.tabWidget = QTabWidget(SendReceiveSettingsDialogClass)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(5, 5, 480, 380))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.groupBox_5 = QGroupBox(self.tab)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.groupBox_5.setGeometry(QRect(10, 10, 450, 200))
        self.cManual = QRadioButton(self.groupBox_5)
        self.cManual.setObjectName(u"cManual")
        self.cManual.setGeometry(QRect(15, 30, 400, 20))
        self.cManual.setChecked(True)
        self.cEveryN = QRadioButton(self.groupBox_5)
        self.cEveryN.setObjectName(u"cEveryN")
        self.cEveryN.setGeometry(QRect(15, 55, 240, 20))
        self.cEveryX = QRadioButton(self.groupBox_5)
        self.cEveryX.setObjectName(u"cEveryX")
        self.cEveryX.setGeometry(QRect(15, 80, 400, 20))
        self.cEveryXList = QLineEdit(self.groupBox_5)
        self.cEveryXList.setObjectName(u"cEveryXList")
        self.cEveryXList.setGeometry(QRect(40, 105, 236, 22))
        self.label_4 = QLabel(self.groupBox_5)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(345, 55, 55, 20))
        self.cEveryNTime = QSpinBox(self.groupBox_5)
        self.cEveryNTime.setObjectName(u"cEveryNTime")
        self.cEveryNTime.setGeometry(QRect(260, 55, 88, 24))
        self.cEveryNTime.setMinimum(1)
        self.cEveryNTime.setMaximum(999)
        self.cEveryNTime.setValue(15)
        self.cSendImmediate = QCheckBox(self.groupBox_5)
        self.cSendImmediate.setObjectName(u"cSendImmediate")
        self.cSendImmediate.setGeometry(QRect(15, 140, 400, 20))
        self.groupBox_6 = QGroupBox(self.tab)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setGeometry(QRect(10, 220, 450, 125))
        self.cSendReceive = QRadioButton(self.groupBox_6)
        self.cSendReceive.setObjectName(u"cSendReceive")
        self.cSendReceive.setGeometry(QRect(15, 30, 205, 20))
        self.cSendReceive.setChecked(True)
        self.cSendOnly = QRadioButton(self.groupBox_6)
        self.cSendOnly.setObjectName(u"cSendOnly")
        self.cSendOnly.setGeometry(QRect(15, 55, 205, 20))
        self.cReceiveOnly = QRadioButton(self.groupBox_6)
        self.cReceiveOnly.setObjectName(u"cReceiveOnly")
        self.cReceiveOnly.setGeometry(QRect(15, 80, 205, 20))
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.groupBox_2 = QGroupBox(self.tab_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 10, 450, 330))
        self.cLeaveOnServer = QCheckBox(self.groupBox_2)
        self.cLeaveOnServer.setObjectName(u"cLeaveOnServer")
        self.cLeaveOnServer.setGeometry(QRect(15, 30, 355, 20))
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.groupBox_3 = QGroupBox(self.tab_3)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(10, 10, 450, 330))
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.groupBox_4 = QGroupBox(self.tab_4)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(10, 10, 450, 330))
        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.groupBox_7 = QGroupBox(self.tab_5)
        self.groupBox_7.setObjectName(u"groupBox_7")
        self.groupBox_7.setGeometry(QRect(10, 10, 450, 330))
        self.tabWidget.addTab(self.tab_5, "")
        self.cOK = QPushButton(SendReceiveSettingsDialogClass)
        self.cOK.setObjectName(u"cOK")
        self.cOK.setGeometry(QRect(335, 395, 75, 30))
        self.cCancel = QPushButton(SendReceiveSettingsDialogClass)
        self.cCancel.setObjectName(u"cCancel")
        self.cCancel.setGeometry(QRect(410, 395, 75, 30))

        self.retranslateUi(SendReceiveSettingsDialogClass)
        self.cOK.clicked.connect(SendReceiveSettingsDialogClass.accept)
        self.cCancel.clicked.connect(SendReceiveSettingsDialogClass.reject)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(SendReceiveSettingsDialogClass)
    # setupUi

    def retranslateUi(self, SendReceiveSettingsDialogClass):
        SendReceiveSettingsDialogClass.setWindowTitle(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"SendReceiveSettingsDialog", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Automation", None))
        self.cManual.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Manual - initiate each send/receive session manually", None))
        self.cEveryN.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Schedule a send/receive every", None))
        self.cEveryX.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Schedule a send/receive at \"X\" minutes past the hour", None))
        self.label_4.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"minutes", None))
        self.cSendImmediate.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Send a message immediately when it is complete", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Send/Receive Button Setup", None))
        self.cSendReceive.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Send/Receive", None))
        self.cSendOnly.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Send only", None))
        self.cReceiveOnly.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Receive only", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Automation", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"TEMPORARY", None))
        self.cLeaveOnServer.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Leave messages on server - TEMPORARY USE ONLY!", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Receiving", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"GroupBox", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Printing", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"GroupBox", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Notifications", None))
        self.groupBox_7.setTitle(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"GroupBox", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Other", None))
        self.cOK.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"OK", None))
        self.cCancel.setText(QCoreApplication.translate("SendReceiveSettingsDialogClass", u"Cancel", None))
    # retranslateUi

