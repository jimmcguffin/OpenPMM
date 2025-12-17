import sys
from PySide6 import QtWidgets
from PySide6.QtCore import QDateTime, Signal
from PySide6.QtWidgets import QMainWindow
from persistentdata import PersistentData
from sql_mailbox import MailBoxHeader, MailFlags
from globalsignals import global_signals
from ui_newpacketmessage import Ui_NewPacketMessageClass

class NewPacketMessage(QMainWindow,Ui_NewPacketMessageClass):
    def __init__(self,pd,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.setupUi(self)
        t = self.pd.getProfile("MessageSettings/DefaultNewMessageType","P")
        if t == "P": self.cMessageTypePrivate.setChecked(True)
        elif t == "B": self.cMessageTypeBulletin.setChecked(True)
        elif t == "N": self.cMessageTypeNts.setChecked(True)
        else: self.cNewDefaultPrivate.setChecked(True)
        self.actionSend.triggered.connect(self.onSend)
        self.cSend.clicked.connect(self.onSend)
        self.cBBS.setText(self.pd.getBBS("ConnectName"))
        self.cFrom.setText(self.pd.getActiveCallSign()) # gets user or tactical
        subject = self.pd.make_standard_subject()
        self.cSubject.setText(subject)

    def resizeEvent(self,event):
        self.cMessage.resize(event.size().width()-20,event.size().height()-50)
        return super().resizeEvent(event)

    def setInitialData(self,subject,message,urgent=False,to_addr=""):
        self.cSubject.setText(subject)
        self.cMessage.setPlainText(message)
        self.cUrgent.setChecked(urgent)
        self.cTo.setText(to_addr)

    def onSend(self):
        message = self.cMessage.toPlainText()
        if not message:
            message = '\n'
        else:
            if message[-1] != '\n':
                message += '\n'
        mbh = MailBoxHeader()
        msgflags = ""
        if self.cUrgent.isChecked():
            msgflags +=  "!URG!"
        if self.pd.getProfileBool("MessageSettings/ReqeustDeliveryReceipt"):
            msgflags +=  "!RDR!"
        if self.pd.getProfileBool("MessageSettings/ReqeustReadReceipt"):
            msgflags +=  "!RRR!"
        # I can't tell if I am supposed to generate headers or if the system makes them
        generate_headers = False # for today I will assume no
        if generate_headers:
            h1 = f"Date: {MailBoxHeader.to_in_mail_date()}"
            h2 = f"From: {self.cFrom.text()}"
            h3 = f"To: {self.cTo.text()}"
            h4 = f"Subject: {self.cSubject.text()}"
            if self.cUrgent.isChecked():
                mbh.flags |= MailFlags.IS_URGENT.value
            message = f"{h1}\n{h2}\n{h3}\n{h4}\n\n{msgflags}{message}"
        else:
            message =  msgflags + message
        # want this to work however we get the message, so support all of "\r\n", "\r", "\n"
        #message = message.replace("\r\n","\n").replace("\r","\n").replace("\n","\r\n")
        message = message.replace("\r\n","\n").replace("\r","\n") # if you want just "\n" in mail file
        if self.cMessageTypeBulletin.isChecked(): mbh.set_type(1)
        elif self.cMessageTypeNts.isChecked(): mbh.set_type(2)
        mbh.from_addr = self.cFrom.text()
        mbh.to_addr = self.cTo.text()
        # if they used some non-standard separator, fix that
        mbh.to_addr = mbh.to_addr.replace(";",",")
        mbh.bbs = self.cBBS.text()
        #mbh.local_id = ""
        #mbh.target_id = ""
        mbh.subject = self.cSubject.text()
        mbh.date_sent = MailBoxHeader.normalized_date()
        #mbh.date_received = "" # in ISO-8601 format
        mbh.size = len(message)
        global_signals.signal_new_outgoing_text_message.emit(mbh,message)
        self.close()
