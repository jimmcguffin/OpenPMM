from PySide6.QtCore import QObject

from ax25_controller import AX25_Controller
from bbsparser import Jnos2Parser
from serialstream import Level1,LineParser,KissParser
from tncparser import TAPR_Device


# for TAPR:
# io_device object reads bytes, sends one or more bytes to line_parser, which then sends entire messages to TAPR (a TNC device, which sometimes internally passes then to BBS)

# for KISS:
# io_device object reads bytes, sends one or more bytes to KISS pasrser, whcih sends packets to KISS object (a TNC device), which then sends entire packets to AX25, which sends completed I-frame messages to the line_parser, then to BBS

# in the following "left" and "right" refer to the above sequences, so "left" means "towards the io_device"

# this module creates all of the components and then connects them together using signals (going to the right) and callbacks (going to the left, towards the io_device)

# this version attempts to use signals each way, every node should have 2 signals called "signal_bytes_ready" which sends to the right, and "signal_write" which sends to the left
# and they can have in slots called "on_bytes_ready" which accepts messages from the left and "on_read" which gets things from the left

class Pipeline(QObject):
    def __init__(self,pd,l1:Level1):
        self.pd = pd
        self.l1 = l1 # level1 device, usually a serial port or a UDP connection
        self.mycalls = ("","")
        self.bbscall = ""
        # next 3 items are copied adn later passed to BBS
        self.mailbox = None
        self.srflags = 0
        self.sendimmediate = None

    def start_session(self,mycalls:tuple[str,str],bbscall:str,mailbox,srflags:int,sendimmediate:list[int]=None):
        self.mycalls = mycalls
        self.bbscall = bbscall
        self.mailbox = mailbox
        self.srflags = srflags
        self.sendimmediate = sendimmediate

    def add_bbs(self,bbs_id:str="[JNOS-2.0k.2.xsc.8-B1FHIM$]"):
        pass

    def remove_bbs(self):
        if self.bbs:
            self.bbs.onDisconnect()
            self.bbs.signal_write.disconnect()
            self.bbs.stop_session()
        self.bbs = None # does this disconnect all of the signals?
    
    def stop_session(self):
        self.remove_bbs()

class TAPR_Pipeline(Pipeline):
    def __init__(self,pd,l1:Level1):
        super().__init__(pd,l1)
        self.line_parser = LineParser("TAPR")
        self.tnc_parser = TAPR_Device(self,self.pd)
        self.l1.signal_bytes_ready.connect(self.line_parser.find_lines)
        self.tnc_parser.write = self.l1.write

    def start_session(self,mycalls:tuple[str,str],bbscall:str,mailbox,srflags:int,sendimmediate:list[int]=None):
        super().start_session(mycalls,bbscall,mailbox,srflags,sendimmediate)
        self.tnc_parser.start_session(self.mycalls,self.bbscall)

    def add_bbs(self,bbs_id:str):
        self.bbs = None
        if bbs_id.startswith("[JNOS-2.0"):
            self.bbs = Jnos2Parser(self.pd,False)
        if not self.bbs:
            return
        self.tnc_parser.signal_bytes_ready.connect(self.bbs.on_bytes_ready)
        self.bbs.signal_write.connect(self.l1.write)
        self.bbs.start_session(self.mailbox,self.srflags,self.sendimmediate)

    def set_line_end(self,le:bytes,include_line_end_in_reply:True):
        self.line_parser.set_line_end(le,include_line_end_in_reply)

    def stop_session(self):
        super().stop_session()

class KISS_Pipeline(Pipeline):
    def __init__(self,pd,l1:Level1):
        super().__init__(pd,l1)
        self.kiss_parser = KissParser() # these two items are tightly coupled, maybe combine
        self.ax25_controller = AX25_Controller(pd,self.mycalls)
        self.line_parser = LineParser("KISS")

        self.l1.signal_bytes_ready.connect(self.kiss_parser.on_bytes_ready)
        self.kiss_parser.signal_bytes_ready.connect(self.ax25_controller.on_bytes_ready)
        self.ax25_controller.signal_bytes_ready.connect(self.line_parser.on_bytes_ready)
        self.ax25_controller.signal_write.connect(self.kiss_parser.on_write)
        self.kiss_parser.signal_write.connect(self.l1.write)

    def start_session(self,mycalls:tuple[str,str],bbscall:str,mailbox,srflags:int,sendimmediate:list[int]=None):
        super().start_session(mycalls,mailbox,srflags,sendimmediate)
        self.ax25_controller.dl_connect_request(bbscall)
        self.ax25_controller.start_session(self.mycalls,self.bbscall)

    def add_bbs(self,bbs_id:str):
        self.bbs = None
        if bbs_id.startswith("[JNOS-2.0"):
            self.bbs = Jnos2Parser(self.pd,False)
        if not self.bbs:
            return
        self.line_parser.signal_bytes_ready.connect(self.bbs.on_bytes_ready)
        self.bbs.signal_write.connect(self.ax25_controller.on_write)
        self.bbs.start_session(self.mailbox,self.srflags,self.sendimmediate)

    def set_line_end(self,le:bytes,include_line_end_in_reply=True):
        self.line_parser.set_line_end(le.replace(b"\r\n",b"\r"),include_line_end_in_reply)

    def stop_session(self):
        super().stop_session()
        if self.ax25_controller:
            self.ax25_controller.stop_session()


