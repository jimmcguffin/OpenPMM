import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QInputDialog
from persistentdata import PersistentData
from ui_messagesettingsdialog import Ui_MessageSettingsDialogClass

class MessageSettingsDialog(QDialog,Ui_MessageSettingsDialogClass):
    def __init__(self,pd,parent=None):
        super(MessageSettingsDialog,self).__init__(parent)
        self.pd = pd
        self.setupUi(self)
        self.tabWidget.setCurrentIndex(0)
        self.need_save = False
        self.load()

    def accept(self):
        self.save()
        return super().accept()
    
    def load(self):
        # page 1
        t = self.pd.getProfile("MessageSettings/DefaultNewMessageType","P")
        if t == "P": self.cNewDefaultPrivate.setChecked(True)
        elif t == "B": self.cNewDefaultBulletin.setChecked(True)
        elif t == "N": self.cNewdefaultNts.setChecked(True)
        else: self.cNewDefaultPrivate.setChecked(True)
        self.cSendNtsAsPrivate.setChecked(self.pd.getProfileBool("MessageSettings/SendNtsAsPrivate"))
        self.cUseDefaultDestination.setChecked(self.pd.getProfileBool("MessageSettings/UseDefaultDestination"))
        self.cDefaultDestination.setText(self.pd.getProfile("MessageSettings/DefaultDestination"))
        # page 2
        self.cAddMessageNumber.setChecked(self.pd.getProfileBool("MessageSettings/AddMessageNumber"))
        f = int(self.pd.getProfile("MessageSettings/Hyphenation_flag","0"))
        self.cWithoutHyphenation.setChecked(f == 0)
        self.cWithHyphenation.setChecked(f == 1)
        self.cWithDateTimeFormat.setChecked(f == 2)
        self.cAddCharacter.setChecked(self.pd.getProfileBool("MessageSettings/AddCharacter"))
        self.cCharacterToAdd.setText(self.pd.getProfile("MessageSettings/CharacterToAdd"))
        self.cAddMessageNumberSeparator.setChecked(self.pd.getProfileBool("MessageSettings/AddMessageNumberSeparator"))
        self.cAddMessageNumberToInbound.setChecked(self.pd.getProfileBool("MessageSettings/AddMessageNumberToInbound"))
        self.cNextMessageId.setValue(self.pd.get_next_message_number(False))
        # page 3
        # page 4
        self.cRequestDr.setChecked(self.pd.getProfileBool("MessageSettings/RequestDeliveryReceipt"))
        self.cRequestRr.setChecked(self.pd.getProfileBool("MessageSettings/RequestReadReceipt"))
        self.cSendDr.setChecked(self.pd.getProfileBool("MessageSettings/SendDeliveryReceipt"))
        self.cSendRr.setChecked(self.pd.getProfileBool("MessageSettings/SendReadReceipt"))
        # page 5
        # page 6
        self.need_save = True
       
    def save(self):
        if not self.need_save: return

        # page 1
        t = "P"
        if self.cNewDefaultBulletin.isChecked(): t = "B"
        elif self.cNewdefaultNts.isChecked(): t = "N"
        self.pd.setProfile("MessageSettings/DefaultNewMessageType",t)
        self.pd.setProfile("MessageSettings/SendNtsAsPrivate",self.cSendNtsAsPrivate.isChecked())
        self.pd.setProfile("MessageSettings/UseDefaultDestination",self.cUseDefaultDestination.isChecked())
        self.pd.setProfile("MessageSettings/DefaultDestination",self.cDefaultDestination.text())
        # page 2
        self.pd.setProfile("MessageSettings/AddMessageNumber",self.cAddMessageNumber.isChecked())
        f = 0
        if self.cWithoutHyphenation.isChecked(): f = 0
        elif self.cWithHyphenation.isChecked(): f = 1
        elif self.cWithDateTimeFormat.isChecked(): f = 2
        else:  f = 0
        self.pd.setProfile("MessageSettings/Hyphenation_flag",str(f))
        self.cWithoutHyphenation.setChecked(f == 0)
        self.cWithHyphenation.setChecked(f == 1)
        self.cWithDateTimeFormat.setChecked(f == 2)
        self.pd.setProfile("MessageSettings/AddCharacter",self.cAddCharacter.isChecked())
        self.pd.setProfile("MessageSettings/CharacterToAdd",self.cCharacterToAdd.text())
        self.pd.setProfile("MessageSettings/AddMessageNumberSeparator",self.cAddMessageNumberSeparator.isChecked())
        self.pd.setProfile("MessageSettings/AddMessageNumberToInbound",self.cAddMessageNumberToInbound.isChecked())
        self.pd.set_next_message_number(self.cNextMessageId.value())
        # page 3
        # page 4
        self.pd.setProfile("MessageSettings/RequestDeliveryReceipt",self.cRequestDr.isChecked())
        self.pd.setProfile("MessageSettings/RequestReadReceipt",self.cRequestRr.isChecked())
        self.pd.setProfile("MessageSettings/SendDeliveryReceipt",self.cSendDr.isChecked())
        self.pd.setProfile("MessageSettings/SendReadReceipt",self.cSendRr.isChecked())
        # page 5
        # page 6
        self.need_save = False
    
