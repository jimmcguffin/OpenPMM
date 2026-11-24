import sys
import datetime
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6.QtCore import Qt, Signal, QObject, QDateTime, QDate, QTime
from PySide6.QtWidgets import QDialog, QLineEdit, QWidget, QPlainTextEdit, QCheckBox, QRadioButton, QButtonGroup, QComboBox, QFrame
from persistentdata import PersistentData
from globalsignals import global_signals
from sql_mailbox import FieldsToSearch
from ui_voicedialog import Ui_Dialog

class VoiceDialog(QDialog,Ui_Dialog):
    def __init__(self,pd,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.setupUi(self)
        #date_now = QDateTime.currentDateTime().toString("MM/dd/yyyy HH:mm")
        date_now = QDateTime.currentDateTime()
        self.c_time.setDateTime(date_now)

    def accept(self):
        return super().accept()
    
