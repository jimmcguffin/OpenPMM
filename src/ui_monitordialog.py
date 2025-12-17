# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'monitordialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QPlainTextEdit, QSizePolicy,
    QWidget)

class Ui_MonitorDialogClass(object):
    def setupUi(self, MonitorDialogClass):
        if not MonitorDialogClass.objectName():
            MonitorDialogClass.setObjectName(u"MonitorDialogClass")
        MonitorDialogClass.resize(818, 986)
        self.cText = QPlainTextEdit(MonitorDialogClass)
        self.cText.setObjectName(u"cText")
        self.cText.setGeometry(QRect(0, 5, 816, 981))
        self.cText.setReadOnly(True)
        self.cText.setPlainText(u"")
        self.cText.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.retranslateUi(MonitorDialogClass)
    # setupUi

    def retranslateUi(self, MonitorDialogClass):
        MonitorDialogClass.setWindowTitle(QCoreApplication.translate("MonitorDialogClass", u"MonitorDialog", None))
    # retranslateUi

