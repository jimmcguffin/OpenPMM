# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'generalsettingsdialog.ui'
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
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTabWidget, QWidget)

class Ui_GeneralSettingsDialogClass(object):
    def setupUi(self, GeneralSettingsDialogClass):
        if not GeneralSettingsDialogClass.objectName():
            GeneralSettingsDialogClass.setObjectName(u"GeneralSettingsDialogClass")
        GeneralSettingsDialogClass.resize(490, 430)
        self.tabWidget = QTabWidget(GeneralSettingsDialogClass)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(5, 5, 480, 380))
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.groupBox = QGroupBox(self.tab)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(10, 10, 450, 90))
        self.cShowStationIdAtStartup = QCheckBox(self.groupBox)
        self.cShowStationIdAtStartup.setObjectName(u"cShowStationIdAtStartup")
        self.cShowStationIdAtStartup.setGeometry(QRect(10, 30, 305, 20))
        self.cShowTimeAtStartup = QCheckBox(self.groupBox)
        self.cShowTimeAtStartup.setObjectName(u"cShowTimeAtStartup")
        self.cShowTimeAtStartup.setGeometry(QRect(10, 50, 370, 20))
        self.groupBox_6 = QGroupBox(self.tab)
        self.groupBox_6.setObjectName(u"groupBox_6")
        self.groupBox_6.setGeometry(QRect(10, 110, 450, 211))
        self.cFolder_1 = QLineEdit(self.groupBox_6)
        self.cFolder_1.setObjectName(u"cFolder_1")
        self.cFolder_1.setGeometry(QRect(110, 25, 130, 22))
        self.label_3 = QLabel(self.groupBox_6)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(10, 30, 100, 16))
        self.label_4 = QLabel(self.groupBox_6)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(10, 55, 100, 16))
        self.cFolder_2 = QLineEdit(self.groupBox_6)
        self.cFolder_2.setObjectName(u"cFolder_2")
        self.cFolder_2.setGeometry(QRect(110, 50, 130, 22))
        self.label_5 = QLabel(self.groupBox_6)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(10, 80, 100, 16))
        self.cFolder_3 = QLineEdit(self.groupBox_6)
        self.cFolder_3.setObjectName(u"cFolder_3")
        self.cFolder_3.setGeometry(QRect(110, 75, 130, 22))
        self.label_6 = QLabel(self.groupBox_6)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(10, 105, 100, 16))
        self.cFolder_4 = QLineEdit(self.groupBox_6)
        self.cFolder_4.setObjectName(u"cFolder_4")
        self.cFolder_4.setGeometry(QRect(110, 100, 130, 22))
        self.label_7 = QLabel(self.groupBox_6)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(10, 130, 100, 16))
        self.cFolder_5 = QLineEdit(self.groupBox_6)
        self.cFolder_5.setObjectName(u"cFolder_5")
        self.cFolder_5.setGeometry(QRect(110, 125, 130, 22))
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.groupBox_2 = QGroupBox(self.tab_2)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 10, 450, 330))
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
        self.groupBox_5 = QGroupBox(self.tab_5)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.groupBox_5.setGeometry(QRect(10, 10, 450, 330))
        self.tabWidget.addTab(self.tab_5, "")
        self.cOK = QPushButton(GeneralSettingsDialogClass)
        self.cOK.setObjectName(u"cOK")
        self.cOK.setGeometry(QRect(335, 395, 75, 30))
        self.cCancel = QPushButton(GeneralSettingsDialogClass)
        self.cCancel.setObjectName(u"cCancel")
        self.cCancel.setGeometry(QRect(410, 395, 75, 30))

        self.retranslateUi(GeneralSettingsDialogClass)
        self.cOK.clicked.connect(GeneralSettingsDialogClass.accept)
        self.cCancel.clicked.connect(GeneralSettingsDialogClass.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(GeneralSettingsDialogClass)
    # setupUi

    def retranslateUi(self, GeneralSettingsDialogClass):
        GeneralSettingsDialogClass.setWindowTitle(QCoreApplication.translate("GeneralSettingsDialogClass", u"GeneralSettingsDialog", None))
        self.groupBox.setTitle(QCoreApplication.translate("GeneralSettingsDialogClass", u"Program Startup", None))
        self.cShowStationIdAtStartup.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Show station ID on startup", None))
        self.cShowTimeAtStartup.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Show the PC time check to confirm time is correct", None))
        self.groupBox_6.setTitle(QCoreApplication.translate("GeneralSettingsDialogClass", u"Custom Folder Labels", None))
        self.label_3.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Folder 1", None))
        self.label_4.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Folder 2", None))
        self.label_5.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Folder 3", None))
        self.label_6.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Folder 4", None))
        self.label_7.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Folder 5", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("GeneralSettingsDialogClass", u"Startup", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("GeneralSettingsDialogClass", u"GroupBox", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("GeneralSettingsDialogClass", u"Addressing", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("GeneralSettingsDialogClass", u"GroupBox", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("GeneralSettingsDialogClass", u"Profiles", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("GeneralSettingsDialogClass", u"GroupBox", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("GeneralSettingsDialogClass", u"Printing", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("GeneralSettingsDialogClass", u"GroupBox", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("GeneralSettingsDialogClass", u"Miscellaneous", None))
        self.cOK.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"OK", None))
        self.cCancel.setText(QCoreApplication.translate("GeneralSettingsDialogClass", u"Cancel", None))
    # retranslateUi

