import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QInputDialog
from ui_aboutdialog import Ui_AboutDialog

class AboutDialog(QDialog,Ui_AboutDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setupUi(self)