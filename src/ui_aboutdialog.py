# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'aboutdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        if not AboutDialog.objectName():
            AboutDialog.setObjectName(u"AboutDialog")
        AboutDialog.resize(367, 210)
        self.label = QLabel(AboutDialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 5, 260, 35))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label.setFont(font)
        self.label_2 = QLabel(AboutDialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(15, 45, 270, 16))
        self.label_3 = QLabel(AboutDialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(15, 70, 270, 16))
        self.label_4 = QLabel(AboutDialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(15, 95, 330, 16))
        self.label_5 = QLabel(AboutDialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(15, 120, 270, 16))
        self.pushButton = QPushButton(AboutDialog)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setEnabled(False)
        self.pushButton.setGeometry(QRect(205, 170, 75, 24))
        self.pushButton_2 = QPushButton(AboutDialog)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(285, 170, 75, 24))

        self.retranslateUi(AboutDialog)
        self.pushButton_2.clicked.connect(AboutDialog.accept)
    # setupUi

    def retranslateUi(self, AboutDialog):
        AboutDialog.setWindowTitle(QCoreApplication.translate("AboutDialog", u"About OpenPMM", None))
        self.label.setText(QCoreApplication.translate("AboutDialog", u"Open Packet Message Manager", None))
        self.label_2.setText(QCoreApplication.translate("AboutDialog", u"Version 0.5", None))
        self.label_3.setText(QCoreApplication.translate("AboutDialog", u"Copyright \u00a9 2025 Jim McGuffin KW6W", None))
        self.label_4.setText(QCoreApplication.translate("AboutDialog", u"Based very heavily on Outpost by Jim Oberhofer KN6PE", None))
        self.label_5.setText(QCoreApplication.translate("AboutDialog", u"Licensed under GPLv2", None))
        self.pushButton.setText(QCoreApplication.translate("AboutDialog", u"License", None))
        self.pushButton_2.setText(QCoreApplication.translate("AboutDialog", u"OK", None))
    # retranslateUi

