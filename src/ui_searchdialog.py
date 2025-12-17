# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'searchdialog.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QLineEdit,
    QPushButton, QRadioButton, QSizePolicy, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(405, 219)
        self.c_search_text = QLineEdit(Dialog)
        self.c_search_text.setObjectName(u"c_search_text")
        self.c_search_text.setGeometry(QRect(10, 20, 310, 24))
        self.c_search = QPushButton(Dialog)
        self.c_search.setObjectName(u"c_search")
        self.c_search.setGeometry(QRect(320, 20, 75, 24))
        self.c_subject_line = QCheckBox(Dialog)
        self.c_subject_line.setObjectName(u"c_subject_line")
        self.c_subject_line.setGeometry(QRect(10, 55, 125, 20))
        self.c_message_text = QCheckBox(Dialog)
        self.c_message_text.setObjectName(u"c_message_text")
        self.c_message_text.setGeometry(QRect(10, 80, 125, 20))
        self.c_local_message_id = QCheckBox(Dialog)
        self.c_local_message_id.setObjectName(u"c_local_message_id")
        self.c_local_message_id.setGeometry(QRect(10, 105, 125, 20))
        self.c_from = QCheckBox(Dialog)
        self.c_from.setObjectName(u"c_from")
        self.c_from.setGeometry(QRect(10, 130, 125, 20))
        self.c_to = QCheckBox(Dialog)
        self.c_to.setObjectName(u"c_to")
        self.c_to.setGeometry(QRect(10, 155, 125, 20))
        self.c_bbs = QCheckBox(Dialog)
        self.c_bbs.setObjectName(u"c_bbs")
        self.c_bbs.setGeometry(QRect(10, 180, 125, 20))
        self.c_all_folders = QRadioButton(Dialog)
        self.c_all_folders.setObjectName(u"c_all_folders")
        self.c_all_folders.setGeometry(QRect(200, 55, 200, 20))
        self.c_all_folders.setChecked(True)
        self.c_all_folders_ex = QRadioButton(Dialog)
        self.c_all_folders_ex.setObjectName(u"c_all_folders_ex")
        self.c_all_folders_ex.setGeometry(QRect(200, 80, 200, 20))
        self.c_current_folder = QRadioButton(Dialog)
        self.c_current_folder.setObjectName(u"c_current_folder")
        self.c_current_folder.setGeometry(QRect(200, 105, 200, 20))

        self.retranslateUi(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Search", None))
        self.c_search.setText(QCoreApplication.translate("Dialog", u"Search", None))
        self.c_subject_line.setText(QCoreApplication.translate("Dialog", u"Subject line", None))
        self.c_message_text.setText(QCoreApplication.translate("Dialog", u"Message text", None))
        self.c_local_message_id.setText(QCoreApplication.translate("Dialog", u"Local message ID", None))
        self.c_from.setText(QCoreApplication.translate("Dialog", u"From", None))
        self.c_to.setText(QCoreApplication.translate("Dialog", u"To", None))
        self.c_bbs.setText(QCoreApplication.translate("Dialog", u"BBS", None))
        self.c_all_folders.setText(QCoreApplication.translate("Dialog", u"All folders", None))
        self.c_all_folders_ex.setText(QCoreApplication.translate("Dialog", u"All folders except \"Deleted\"", None))
        self.c_current_folder.setText(QCoreApplication.translate("Dialog", u"Only the current folder", None))
    # retranslateUi

