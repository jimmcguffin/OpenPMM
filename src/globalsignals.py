from PySide6.QtCore import QObject, Signal
from sql_mailbox import MailBoxHeader

class GlobalSignals(QObject):
    signal_new_incoming_message = Signal(MailBoxHeader,str)
    signal_new_outgoing_text_message = Signal(MailBoxHeader,str)
    signal_new_outgoing_form_message = Signal(str,str,bool,str)
    signal_new_outgoing_receipt = Signal(MailBoxHeader)
    signal_message_sent = Signal(int) # moves from OutTray to Sent
    signal_status_bar_message = Signal(str)
    signal_connected = Signal()
    signal_timeout = Signal()
    signal_disconnected = Signal()

global_signals = GlobalSignals()

