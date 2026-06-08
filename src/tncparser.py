# pylint:  disable="line-too-long,missing-function-docstring,multiple-statements,no-name-in-module"

from collections import deque
from datetime import datetime
from enum import IntEnum


import ax25
from ax25v20_controller import AX25_Controller
from bbsparser import Jnos2Parser
from globalsignals import global_signals
from serialstream import Level1
from sql_mailbox import MailBoxHeader
from PySide6.QtCore import QObject, Signal, QTimer, qDebug
from persistentdata import PersistentData
#from pipeline import Pipeline

class TncDevice(QObject):
    signal_bytes_ready = Signal(str)
    signal_write = Signal(str)
    #signalConnected = Signal()
    #signalTimeout = Signal()
    #signalDisconnected = Signal()
    def __init__(self,pipeline,pd):
        super().__init__()
        self.pipeline = pipeline
        self.pd = pd
        self.monitor_mode = False

    def start_session(self,mycalls:tuple[str,str],bbscall:str):
        self.mycalls = mycalls
        self.bbscall = bbscall
        self.monitor_mode = False

    def stop_session(self):
        pass

    def start_monitor_session(self):
        self.monitor_mode = True

    def send(self,b):
        self.signal_write.emit(b)

    def set_line_end(self,le:bytes,include_line_end_in_reply:True):
        pass

    def send_tactical_signoff(self):
        pass

    @staticmethod
    def starts_with_ignore_case(str1, str2): # if str1 starts with str2
        l = len(str2)
        str1 = str1[0:l].upper()
        str2 = str2.upper()
        return str1 == str2

    @staticmethod
    def matches_ignore_case(str1, str2): # if str2 is a prefix of str1
        l = len(str2)
        str1 = str1[0:l].upper()
        str2 = str2.upper()
        return str1 == str2
# when I write some tests: mactches_ignore_case("disconnect","d") should return True
#                          mactches_ignore_case("disconnect","dis") should return True
#                          mactches_ignore_case("disconnect","disp") should return False


# maybe this class should be called TAPR
# todo: need to implement time-out/retry stuff in both this class and bbsparser
class TAPR_Device(TncDevice):
    def __init__(self,pipeline,pd):
        super().__init__(pipeline,pd)
        self.message_queue = deque()
        self.using_echo = False
        self.special_disconnect_value = "\x03\x03\x03*** Disconnect\r" # tells the session to end
        self.in_passthru_mode = False

    def start_session(self,mycalls:tuple[str,str],bbscall:str):
        super().start_session(mycalls,bbscall)
        self.message_queue.clear()
        global_signals.signal_connected.connect(self.on_connected)        
        global_signals.signal_disconnected.connect(self.on_disconnected)
        global_signals.signal_status_bar_message.emit("Initializing TNC")
        self.pipeline.set_line_end(b"cmd:",self.using_echo)
        mycall = f"{self.get_command("CommandMyCall")} {mycalls[0]}\r"
        connectstr = f"{self.get_command("CommandConnect")} {self.pd.getBBS("ConnectName")}\r"
        # these are internally generated
        # self.send(b"\r") // flush out any half-written commands
        self.send("\x03\r")
        self.send("disconnect\r")
        if self.using_echo:
            self.send("echo on\r")
        else:
            self.send("echo off\r")
        self.send(mycall)
        self.send("monitor off\r")
        # these come from the dialog
        if self.pd.getInterfaceBool("AlwaysSendInitCommands"):
            for s in self.pd.getInterface("CommandsBefore"):
                s = s.strip()
                if s:
                    self.send(s+"\r")
        self.send(connectstr)

        # start things going
        #qDebug() << "writing" << self.message_queue.front() << '\n'
        # self.io_device.write(self.message_queue[0])
    
    def on_connected(self):
        print("TNC connected!")
        # give control over to BBS parser
        self.in_passthru_mode = True
        self.pipeline.add_bbs("[JNOS-2.0k.2.xsc.8-B1FHIM$]") #!! temporary, should pass the welcome message sent by the BBS

    def on_disconnected(self):
        self.pipeline.remove_bbs()
        global_signals.signal_status_bar_message.emit("")
        print("TNC got disconnected!")
        self.in_passthru_mode = False
        global_signals.signal_status_bar_message.emit("Resetting TNC")
        self.pipeline.set_line_end(b"cmd:",self.using_echo) # and reset this
        if self.pd.getInterfaceBool("AlwaysSendInitCommands"):
            for s in self.pd.getInterface("CommandsAfter"):
                s = s.strip()
                if s:
                    self.send(s+"\r")
        self.send(self.special_disconnect_value)


    def is_valid_query_response(self,q,r):
        if self.using_echo: # is much simpler in this case
            # ignore any ctrl-c's
            if q[0] == '\x03': q = q[1:]
            qDebug(f"TNC: <<{q.replace("\r","|")}>> returned <<{r.replace("\r","|").replace("\n","|")}>>")
            return r.startswith(q)
        else:
            q = q.rstrip()
            r = r.rstrip()
            # any response to a ctrl-c is fine
            if q and q[0] == '\x03':
                return True
            qDebug(f"TNC: <<{q.replace("\r","|")}>> returned <<{r.replace("\r","|").replace("\n","|")}>>")
            # pick off the first word of each item
            q1,_,_ = q.partition(" ")
            r1,_,_ = r.partition(" ")
            if self.matches_ignore_case(r1,q1):
                return True
            # there are some things that don't match well
            elif self.matches_ignore_case("disconnect",q1):
                if not r or "DISCONNECT" in r: # r is the entire response, not just the first word
                    return True
            elif self.matches_ignore_case("mycall",q1):
                if not r or r == "Not while connected": # for some reason, there is no reply tp mycall, unless you are already cinnected
                    return True
            elif self.matches_ignore_case("connect",q1) and not r: # connect has no immediate response
                return True
            return False

    def send(self,b):
        if self.in_passthru_mode:
            self.signal_write.emit(b)
        else:
            self.message_queue.append(b)
            if len(self.message_queue) == 1:
                if self.message_queue[0] == self.special_disconnect_value:
                    global_signals.signal_end_send_receive.emit()
                else:
                    self.signal_write.emit(self.message_queue[0])

    def set_line_end(self,le:bytes,include_line_end_in_reply:True):
        self.pipeline.set_line_end(le,include_line_end_in_reply)

    def send_tactical_signoff(self):
        pass

    def on_bytes_ready(self,r):
        if self.in_passthru_mode:
            return self.signal_bytes_ready.emit(r)
        # this is probably the reponse to the front element
        if not self.message_queue: return
        # # handle confused responses first
        # if "\r\nEH?" in r:
        #     print("TNC: EH response, resending")
        #     self.io_device.write(self.message_queue[0]) # resend the last command?
        #     return
        if self.is_valid_query_response(self.message_queue[0],r):
            self.message_queue.popleft()
            if self.message_queue:
                if self.message_queue[0] == self.special_disconnect_value:
                    global_signals.signal_end_send_receive.emit()
                else:
                    self.signal_write.emit(self.message_queue[0])
        else:
            print("spurious")
            # maybe try sending again?
            # self.io_device.write(self.message_queue[0]) this did NOT work

    @staticmethod
    def get_default_prompts():
        return  [
			("PromptCommand","cmd:"),
			("PromptTimeout","*** retry count exceeded"),
			("PromptConnected","*** CONNECTED"),
			("PromptDisconnected","*** DISCONNECTED"),
            ]   

    def get_command(self,s):
        c = self.pd.getInterface(s)
        if c:
            return c
        if s in self.get_default_commands():
            return self.get_default_commands()[s]
        return "<"+s+">" # this will never work but it will show in the log as a problem

    @staticmethod
    def get_default_commands():
         return {
				"CommandMyCall":"my",
				"CommandConnect":"connect",
				"CommandRetry":"retry",
				"CommandConvers":"convers",
				"CommandDayTime":"daytime",
         }
    
    @staticmethod
    def get_default_before_init_commands():
        return [
            "INTFACE TERMINAL",
            "CD SOFTWARE",
            "NEWMODE ON",
            "8BITCONV ON",
            "BEACON EVERY 0",
            "SLOTTIME 10",
            "PERSIST 63",
            "PACLEN 128",
            "MAXFRAME 2",
            "FRACK 6",
            "RETRY 8",
            "CHECK 30",
            "TXDELAY 40",
            "XFLOW OFF",
            "SENDPAC $05",
            "CR OFF",
            "PACTIME AFTER 2",
            "CPACTIME ON",
            "STREAMEV OFF",
            "STREAMSW $00",
        ]

    @staticmethod
    def get_default_after_init_commands():
        return [
            "SENDPAC $0D",
            "CR ON",
            "PACTIME AFTER 10",
            "CPACTIME OFF",
            "STREAMSW $7C"
        ]
"""
class KISS_Device(TncDevice):
    def __init__(self,pipeline:Pipeline,pd):
        super().__init__(pipeline,pd)
        self.mycall = ""
        self.bytes_already_searched = 0

    def start_session(self,mailbox,srflags:int,sendimmediate:list[int]=None):
        super().start_session(l1,lp,mailbox,srflags,sendimmediate)
        self.mycall = self.pd.getActiveCallSign().upper()
        self.bbs = self.pd.getBBS("ConnectName").upper()
        self.signal_frame_read_handle = self.io_device.signal_frame_read.connect(self.ax25_controller.on_frame)   
        #mycall = f"{self.get_command("CommandMyCall")} {self.pd.getActiveCallSign()}\r"
        self.ax25_controller.dl_connect_request()

    def stop_session(self):
        ### send IDENT if operating in z mode
        super().stop_session()
        if self.signal_frame_read_handle:
            self.io_device.signal_frame_read.disconnect(self.signal_frame_read_handle)
        self.signal_frame_read_handle = None
        self.connect = None
        self.monitor_mode = False
        global_signals.signal_status_bar_message.emit("")
        self.signalDisconnected.emit()

    def onConnected(self):
        print("Connected!")
        # give control over to BBS parser
        self.bbs_parser = Jnos2Parser(self.pd,False,self)
        #self.bbs_parser.signalDisconnected.connect(self.onDisconnected)
        self.bbs_parser.start_session(self,self.mailbox,self.srflags,self.sendimmediate)

    def onDisconnected(self):
        # if we never actually connected, there will not be a bbs_parser
        if not self.bbs_parser:
            return # this happens at startup sometimes - the TNC was holding on to it from a previous session
        print("TNC got disconnected!")
        global_signals.signal_status_bar_message.emit("Resetting TNC")
        #self.bbs_parser.signalDisconnected.disconnect()
        self.bbs_parser = None

    def on_bytes_ready(self):
        done = False
        while not done:
            assert(self.line_end)
            start = max(self.bytes_already_searched-len(self.line_end)+1,0)
            if (p := self._sdata.find(self.line_end,start)) >= 0:
                if self.include_line_end_in_reply:
                    global_signals.signal_line_read.emit(self._sdata[0:p+len(self.line_end)].decode())
                else:
                    global_signals.signal_line_read.emit(self._sdata[0:p].decode())
                # extract
                del self._sdata[0:p+len(self.line_end)]
                self.bytes_already_searched = 0
            else:
                self.bytes_already_searched = len(self._sdata)
                done = True

    def send(self,s:str): # these are ordinary strings, get sent as "I" frames
        self.ax25_controller.dl_data_request(s)

    def send_ui(self,s:str): # these are ordinary strings, get sent as "UI" frames
        self.ax25_controller.dl_unit_data_request(s)

"""