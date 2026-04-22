import sys
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog, QInputDialog
from persistentdata import PersistentData
from ui_interfacedialog import Ui_InterfaceDialogClass

class InterfaceDialog(QDialog,Ui_InterfaceDialogClass):
    def __init__(self,pd,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.setupUi(self)
        self.tabWidget.setCurrentIndex(0)
        self.need_save = False
        self.loadInterfaces()
        self.load()
        self.cInterfaceName.currentTextChanged.connect(self.onInterfaceChanged)
        self.cNew.clicked.connect(self.onNewClicked)

    def accept(self):
        self.save()
        return super().accept()
    
    def loadInterfaces(self):
        self.cInterfaceName.blockSignals(True)
        self.cInterfaceName.clear()
        self.cInterfaceName.addItems(self.pd.getInterfaces())
        self.cInterfaceName.setCurrentText(self.pd.getActiveInterface())
        self.cInterfaceName.blockSignals(False)
    
    def load(self):
        # this happens later	self.cComPort.setCurrentText(self.pd.GetInterface("ComPort","Com1"))
        # page 1
        self.cDescription.setPlainText(self.pd.getInterface("Description"))
        type = self.pd.getInterface("Type") 
        if type == "KISS":
            self.cTypeKiss.setChecked(True)
        elif type == "OTHER":
            self.cTypeOther.setChecked(True)
        else: # default to TAPR
            self.cTypeTapr.setChecked(True)
        ctype = self.pd.getInterface("ConnectionType") 
        if ctype == "Network":
            self.cConnectionNetwork.setChecked(True)
        else: # default to Serial
            self.cConnectionSerial.setChecked(True)
        # page 2
        self.cBaud.setCurrentText(self.pd.getInterface("Baud"))
        self.cParity.setCurrentText(self.pd.getInterface("Parity"))
        self.cDataBits.setCurrentText(self.pd.getInterface("DataBits"))
        self.cStopBits.setCurrentText(self.pd.getInterface("StopBits"))
        self.cFlowControl.setCurrentText(self.pd.getInterface("FlowControl"))
        self.need_save = True
        # page 3
        self.cPromptCommand.setText(self.pd.getInterface("PromptCommand"))
        self.cPromptTimeout.setText(self.pd.getInterface("PromptTimeout"))
        self.cPromptConnected.setText(self.pd.getInterface("PromptConnected"))
        self.cPromptDisconnected.setText(self.pd.getInterface("PromptDisconnected"))
        # page 4
        self.cCommandMyCall.setText(self.pd.getInterface("CommandMyCall"))
        self.cCommandConnect.setText(self.pd.getInterface("CommandConnect"))
        self.cCommandRetry.setText(self.pd.getInterface("CommandRetry"))
        self.cCommandConvers.setText(self.pd.getInterface("CommandConvers"))
        self.cCommandDayTime.setText(self.pd.getInterface("CommandDayTime"))
        self.cIncludeCommandPrefix.setChecked(self.pd.getInterfaceBool("IncludeCommandPrefix"))
        self.cCommandPrefix.setText(self.pd.getInterface("CommandPrefix"))
        # page 5
        self.cAlwaysSendInitCommands.setChecked(self.pd.getInterfaceBool("AlwaysSendInitCommands"))
        sl1 = self.pd.getInterface("CommandsBefore")
        sl2 = self.pd.getInterface("CommandsAfter")
        self.cCommandsBefore.clear()
        self.cCommandsAfter.clear()
        if sl1:
            for s in sl1: 
                self.cCommandsBefore.appendPlainText(s)
        if sl2:
            for s in sl2: 
                self.cCommandsAfter.appendPlainText(s)
       
    def save(self):
        if not self.need_save: return
        # page 1
        self.pd.setInterface("Description",self.cDescription.toPlainText())
        if self.cTypeTapr.isChecked():
            self.pd.setInterface("Type","TAPR") 
        elif self.cTypeKiss.isChecked():
            self.pd.setInterface("Type","KISS") 
        elif self.cTypeOther.isChecked():
            self.pd.setInterface("Type","OTHER") 
        else:
            self.pd.setInterface("Type","TAPR") 
        if self.cConnectionNetwork.isChecked():
            self.pd.setInterface("ConnectionType","Network") 
        else:
            self.pd.setInterface("ConnectionType","Serial") 
        # page 2
        self.pd.setInterface("ComPort",self.cComPort.currentText())
        self.pd.setInterface("Baud",self.cBaud.currentText())
        self.pd.setInterface("Parity",self.cParity.currentText())
        self.pd.setInterface("DataBits",self.cDataBits.currentText())
        self.pd.setInterface("StopBits",self.cStopBits.currentText())
        self.pd.setInterface("FlowControl",self.cFlowControl.currentText())
        # page 3
        self.pd.setInterface("PromptCommand",self.cPromptCommand.text())
        self.pd.setInterface("PromptTimeout",self.cPromptTimeout.text())
        self.pd.setInterface("PromptConnected",self.cPromptConnected.text())
        self.pd.setInterface("PromptDisconnected",self.cPromptDisconnected.text())
        # page 4
        self.pd.setInterface("CommandMyCall",self.cCommandMyCall.text())
        self.pd.setInterface("CommandConnect",self.cCommandConnect.text())
        self.pd.setInterface("CommandRetry",self.cCommandRetry.text())
        self.pd.setInterface("CommandConvers",self.cCommandConvers.text())
        self.pd.setInterface("CommandDayTime",self.cCommandDayTime.text())
        self.pd.setInterface("IncludeCommandPrefix",self.cIncludeCommandPrefix.isChecked())
        self.pd.setInterface("CommandPrefix",self.cCommandPrefix.text())
        # page 5
        self.pd.setInterface("AlwaysSendInitCommands",self.cAlwaysSendInitCommands.isChecked())
        cb = self.cCommandsBefore.toPlainText()
        ca = self.cCommandsAfter.toPlainText()
        self.pd.setInterface("CommandsBefore",cb.splitlines())
        self.pd.setInterface("CommandsAfter",ca.splitlines())

        self.need_save = False
    
    def onInterfaceChanged(self,str):
        self.save()
        self.pd.setActiveInterface(str)
        self.load()

    def onNewClicked(self):
        text, ok = QInputDialog.getText(self,"New Interface","New interface")
        if ok and text:
            self.pd.addInterface(text)
            self.loadInterfaces()
            self.cInterfaceName.setCurrentText(text)

    def setComPortList(self,ports):
        self.cComPort.clear()
        self.cComPort.addItems(ports)
        # select the one that matches best
        tmp = self.pd.getInterface("ComPort")
        if tmp:
            for i in range(len(ports)):
                if ports[i].startswith(tmp):
                    self.cComPort.setCurrentIndex(i)
        #self.cComPort.setCurrentText()