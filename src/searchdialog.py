import sys
import datetime
from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import QDialog, QLineEdit, QWidget, QPlainTextEdit, QCheckBox, QRadioButton, QButtonGroup, QComboBox, QFrame
from persistentdata import PersistentData
from globalsignals import global_signals
from sql_mailbox import FieldsToSearch
from ui_searchdialog import Ui_Dialog

class SearchDialog(QDialog,Ui_Dialog):
    def __init__(self,pd,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.setupUi(self)
        self.c_search.clicked.connect(self.on_search)
        self.fields_to_search = 0
        self.search = ""
        self.c_subject_line.setChecked(True)

    def on_search(self):
        self.search = self.c_search_text.text()
        if not self.search:
            return super().reject()
        self.fields_to_search = 0
        if self.c_subject_line.isChecked():
            self.fields_to_search |= FieldsToSearch.SUBJECT.value
        if self.c_message_text.isChecked():
            self.fields_to_search |= FieldsToSearch.MESSAGE.value
        if self.c_local_message_id.isChecked():
            self.fields_to_search |= FieldsToSearch.LOCAL_MSG_ID.value
        if self.c_from.isChecked():
            self.fields_to_search |= FieldsToSearch.FROM.value
        if self.c_to.isChecked():
            self.fields_to_search |= FieldsToSearch.TO.value
        if self.c_bbs.isChecked():
            self.fields_to_search |= FieldsToSearch.BBS.value
        if not self.fields_to_search: # at least one must be checked
            return super().reject()
        if self.c_all_folders.isChecked():
            self.fields_to_search |= FieldsToSearch.ALL_FOLDERS.value
        elif self.c_all_folders_ex.isChecked():
            self.fields_to_search |= FieldsToSearch.ALL_FOLDERS_EX.value
        super().accept()