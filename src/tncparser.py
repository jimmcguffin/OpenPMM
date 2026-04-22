# pylint:  disable="line-too-long,missing-function-docstring,multiple-statements,no-name-in-module"

from collections import deque
from datetime import datetime

from bbsparser import Jnos2Parser
from globalsignals import global_signals
from serialstream import SerialStream
from sql_mailbox import MailBoxHeader

import ax25
from PySide6.QtCore import QObject, Signal, QTimer, qDebug
from persistentdata import PersistentData

class TncDevice(QObject):
    #signalConnected = Signal()
    #signalTimeout = Signal()
    #signalDisconnected = Signal()
    signalOutgingMessageSent = Signal() # mostly so that mainwinow can repaint mail list if it is viewing the OutTray
    signal_status_bar_message = Signal(str) # send "" to revert to default status bar
    def __init__(self,pd,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.serialStream = None
        self.srflags = 0 # 1=send, 2=recv, 4=recvb
        self.sendimmediate = []
        self.monitor_mode = False

    def start_session(self,ss:SerialStream,mailbox,srflags:int,sendimmediate:list[int]=None):
        self.monitor_mode = False
        self.serialStream = ss
        self.mailbox = mailbox
        self.srflags = srflags
        self.sendimmediate = sendimmediate

    def end_session(self):
        self.signal_status_bar_message.emit("")
        global_signals.signal_disconnected.emit()

    def start_monitor_session(self,ss:SerialStream):
        self.monitor_mode = True
        self.serial_stream = ss

    def send(self,b):
        self.serialStream.write(b)

    def set_line_end(self,le:bytes):
        pass

    def set_include_line_end_in_reply(self,f:bool):
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
    def __init__(self,pd,parent=None):
        super().__init__(pd,parent)
        self.message_queue = deque()
        self.using_echo = False
        self.bbs_parser = None
        self.special_disconnect_value = "*** Disconnect\r" # tells the session to end
        self.in_passthru_mode = False

    def start_session(self,ss,mailbox,srflags:int,sendimmediate:list[int]=None):
        super().start_session(ss,mailbox,srflags,sendimmediate)
        self.message_queue.clear()
        self.signal_line_read_handle = global_signals.signal_line_read.connect(self.onResponse)        
        global_signals.signal_connected.connect(self.onConnected)        
        global_signals.signal_disconnected.connect(self.onDisconnected)
        self.signal_status_bar_message.emit("Initializing TNC")
        self.serialStream.line_end = b"cmd:"
        self.serialStream.include_line_end_in_reply = self.using_echo
        mycall = f"{self.get_command("CommandMyCall")} {self.pd.getActiveCallSign()}\r"
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
        # self.serialStream.write(self.message_queue[0])

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
            self.serialStream.write(b)
        else:
            self.message_queue.append(b)
            if len(self.message_queue) == 1:
                if self.message_queue[0] == self.special_disconnect_value:
                    self.end_session()
                else:
                    self.serialStream.write(self.message_queue[0])

    def set_line_end(self,le:bytes):
        self.serialStream.line_end = le

    def set_include_line_end_in_reply(self,f:bool):
        self.serialStream.include_line_end_in_reply = f

    def send_tactical_signoff(self):
        pass

    def onResponse(self,r):
        # this is probably the reponse to the front element
        if not self.message_queue: return
        # # handle confused responses first
        # if "\r\nEH?" in r:
        #     print("TNC: EH response, resending")
        #     self.serialStream.write(self.message_queue[0]) # resend the last command?
        #     return
        if self.is_valid_query_response(self.message_queue[0],r):
            self.message_queue.popleft()
            if self.message_queue:
                if self.message_queue[0] == self.special_disconnect_value:
                    self.end_session()
                else:
                    self.serialStream.write(self.message_queue[0])
        else:
            print("spurious")
            # maybe try sending again?
            # self.serialStream.write(self.message_queue[0]) this did NOT work

    def onConnected(self):
        print("Connected!")
        # give control over to BBS parser
        self.in_passthru_mode = True
        global_signals.signal_line_read.disconnect(self.signal_line_read_handle)
        self.bbs_parser = Jnos2Parser(self.pd,self.using_echo,self)
        # ? self.bbs_parser.signalDisconnected.connect(self.onDisconnected)
        self.bbs_parser.signal_status_bar_message.connect(lambda s: self.signal_status_bar_message.emit(s))
        self.bbs_parser.start_session(self,self.mailbox,self.srflags,self.sendimmediate)

    def onDisconnected(self):
        # if we never actually connected, there will not be a bbs_parser
        if not self.bbs_parser:
            return # this happens at startup sometimes - the TNC was holding on to it from a previous session
        print("TNC got disconnected!")
        self.in_passthru_mode = False
        self.signal_status_bar_message.emit("Resetting TNC")
        self.bbs_parser.on_disconnected()
        self.bbs_parser = None
        global_signals.signal_line_read.connect(self.onResponse) # point this back to us
        self.serialStream.line_end = b"cmd:" # and reset this
        self.serialStream.include_line_end_in_reply = self.using_echo # and this
        if self.pd.getInterfaceBool("AlwaysSendInitCommands"):
            for s in self.pd.getInterface("CommandsAfter"):
                s = s.strip()
                if s:
                    self.send(s+"\r")
        self.send(self.special_disconnect_value)

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

UNPROTO_PID = 0xf0
STATE_DISCONNECTED = 0 # idle
STATE_CONNECTING = 1
STATE_CONNECTED = 2
STATE_DISCONNECTING = 3

class KISS_Device(TncDevice):
    def __init__(self,pd,parent=None):
        super().__init__(pd,parent)
        self.mycall = ""
        self.signal_frame_read_handle = None
        self._sdata = bytearray()
        self.bytes_already_searched = 0
        # these variable names are right out of the AX25 spec, at this time not sure why all 4 are needed
        self.vs = 0 # Send State variable
        self.ns = 0 # Send Sequence Number
        self.vr = 0 # Receive State variable
        self.nr = 0 # Receive Sequence Number
        # some more variable names from the spec
        self.t1 = 4000 # acknowledgement time
        self.t2 = 1000 # response delay time, is milliseconds to wait for consecutive packets
        self.t3 = 10000 # inactive link time
        self.n1 = 128 # maximum bytes in a I packet, aka PACLEN
        self.n2 = 4 # maximum retries
        self.k = 2 # window size, known to many users as MAXFRAME
        self.modulo = 8 # 128 would be better but not supported in ax25 module, is part of v2.2
        self.state = STATE_DISCONNECTED # see STATE_ vars
        self.retries = 0
        self.last_ack_sent = -1
        self.stuff_to_write = deque()
        self.stuff_waiting_to_be_acknowleged = deque()
        self.t1_timer = QTimer()
        self.t1_timer.setSingleShot(True)
        self.t1_timer.timeout.connect(self.on_t1_timeout)
        self.t2_timer = QTimer()
        self.t2_timer.setSingleShot(True)
        self.t2_timer.timeout.connect(self.on_t2_timeout)
        self.t3_timer = QTimer()
        self.t3_timer.setSingleShot(True)
        self.t3_timer.timeout.connect(self.on_t3_timeout)
        self.signal_frame_read_handle = None

    def start_session(self,ss,mailbox,srflags:int,sendimmediate:list[int]=None):
        super().start_session(ss,mailbox,srflags,sendimmediate)
        self.mycall = self.pd.getActiveCallSign().upper()
        self.bbs = self.pd.getBBS("ConnectName").upper()
        self.signal_frame_read_handle = self.serialStream.signal_frame_read.connect(self.on_message)   
        #mycall = f"{self.get_command("CommandMyCall")} {self.pd.getActiveCallSign()}\r"
        self.configure()
        self.connect()

    def configure(self):
        pass

    def connect(self):
        self.retries = 0
        self.state = STATE_CONNECTING
        self.send_frame(ax25.FrameType.SABM,True,True)

    def start_monitor_session(self,ss:SerialStream):
        super().start_monitor_session(ss)
        self.mycall = self.pd.getActiveCallSign().upper() # not really needed since we don't TX
    
    def end_session(self):
        ### send IDENT if operating in z mode
        super().end_session()
        if self.signal_frame_read_handle:
            self.serialStream.signal_frame_read.disconnect(self.signal_frame_read_handle)
        self.signal_frame_read_handle = None
        self.connect = None
        self.monitor_mode = False
        self.signal_status_bar_message.emit("")
        self.signalDisconnected.emit()

    def set_line_end(self,le:bytes):
        self.line_end = le.replace(b"\r\n",b"\r")

    def set_include_line_end_in_reply(self,f:bool):
        self.include_line_end_in_reply = f

    def on_t1_timeout(self):
        print(f"Timer 1 triggered at {datetime.now().strftime("%H:%M:%S.%f")}")
        if self.state ==  STATE_CONNECTING:
            if self.retries >= self.n2:
                self.state = STATE_DISCONNECTED
                ### maybe end_session?
            else:
                self.retries += 1
                self.send_frame(ax25.FrameType.SABM,True,True)
        elif self.state ==  STATE_CONNECTED:
            # must be an I-packet timeout
            if self.retries >= self.n2:
                self.state = STATE_DISCONNECTED
                ### maybe end_session?
            else:
                self.retries += 1
                self.resend_all_pending()
    def on_t2_timeout(self):
        print(f"Timer 2 triggered at {datetime.now().strftime("%H:%M:%S.%f")}, l={self.last_ack_sent} r={self.vr}/{self.nr}")
        if self.last_ack_sent != self.vr:
            self.send_frame(ax25.FrameType.RR)

    def on_t3_timeout(self):
        print(f"Timer 3 triggered at {datetime.now().strftime("%H:%M:%S.%f")}")

    def resend_all_pending(self):
        for seq,tmp in self.stuff_waiting_to_be_acknowleged:
            self.send_frame(ax25.FrameType.I,True,False,tmp.decode())
    
    def on_message(self,msg:bytes):
        if self.monitor_mode:
            return
        # only pay attention if this is for us
        frame = ax25.Frame.unpack(msg)
        if frame.dst.call != self.mycall:
            return
        control = frame.control
        ft = control.frame_type
        if ft.is_I() and control.send_seqno != self.vr:
            print(f"sent seq {control.send_seqno}, was expecting {self.vr}")
            self.send_frame(ax25.FrameType.REJ)
            return # spec says to discard these

        # if this is a type I or a type RR, it will have an acknowledge number in it
        # if this is a type "I", pass to upper layers
        # this code is similar to the code in LineDelimitedSerialStream and should be shared somehow
        if ft.is_I() or ft.is_S(): # this includes RR and REJ
            if ft.is_I():
                print(f"state={self.state} ft={ft.name} s={control.send_seqno} vs={self.vs} ns={self.ns} r={control.recv_seqno} vr={self.vr} nr={self.nr}")
            else:
                print(f"state={self.state} ft={ft.name} ns={self.ns} r={control.recv_seqno} vr={self.vr} nr={self.nr}")
            # discard any pending frames up to that number
            while self.stuff_waiting_to_be_acknowleged and self.stuff_waiting_to_be_acknowleged[0][0] != control.recv_seqno:
                print(f"ack {control.recv_seqno}, removing {self.stuff_waiting_to_be_acknowleged[0][0]}")
                self.stuff_waiting_to_be_acknowleged.popleft()
            # send any pending stuff if in window
            while self.stuff_to_write and len(self.stuff_waiting_to_be_acknowleged) < self.k:
                tmp = self.stuff_to_write.popleft()
                self.send_frame(ax25.FrameType.I,True,False,tmp)
            # if we are caught up, turn off T1
            if control.recv_seqno == self.vs:
                self.t1_timer.stop()
            if ft == ax25.FrameType.REJ:
                self.vs = control.recv_seqno
                self.resend_all_pending() # resend stuff
        if ft.is_I():
            self.vr = (self.vr+1) & (self.modulo-1)
            # if the P bit is set, respond immediately
            if control.poll_final:
                self.t2_timer.stop()
                self.send_frame(ax25.FrameType.RR,False,True)
            else:
                self.t2_timer.start(self.t2)
                print(f"Timer 2 set at {datetime.now().strftime("%H:%M:%S.%f")}")
            self._sdata += frame.data
            self.find_lines()
        elif ft == ax25.FrameType.UA:
            self.t1_timer.stop()
            if self.state == STATE_CONNECTING:
                # we are connected!
                self.vs = 0
                self.vr = 0
                self.state = STATE_CONNECTED
                self.onConnected()
        elif ft == ax25.FrameType.DISC:
            # we are disconnected
            # acknowledge it
            self.state = STATE_DISCONNECTED
            self.send_frame(ax25.FrameType.UA,False,True)
            self.onDisconnected()
            pass
        elif control.frame_type == ax25.FrameType.UI:
            # beacon-type message
            pass


    def onConnected(self):
        print("Connected!")
        # give control over to BBS parser
        self.bbs_parser = Jnos2Parser(self.pd,False,self)
        #self.bbs_parser.signalDisconnected.connect(self.onDisconnected)
        self.bbs_parser.signal_status_bar_message.connect(lambda s: self.signal_status_bar_message.emit(s))
        self.bbs_parser.start_session(self,self.mailbox,self.srflags,self.sendimmediate)

    def onDisconnected(self):
        # if we never actually connected, there will not be a bbs_parser
        if not self.bbs_parser:
            return # this happens at startup sometimes - the TNC was holding on to it from a previous session
        print("TNC got disconnected!")
        self.signal_status_bar_message.emit("Resetting TNC")
        #self.bbs_parser.signalDisconnected.disconnect()
        self.bbs_parser = None
        # no need for this with KISS global_signals.signal_line_read.connect(self.onResponse) # point this back to us

    def find_lines(self):
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

    def send(self,s:str): # these are ordinary strings, get sent as "I" frame
        # if too big, split
        while len(s) > self.n1:
            self.stuff_to_write.append(s[:self.n1])
            s = s[self.n1:]
        self.stuff_to_write.append(s)
        while self.stuff_to_write and len(self.stuff_waiting_to_be_acknowleged) < self.k:
            tmp = self.stuff_to_write.popleft()
            self.send_frame(ax25.FrameType.I,True,False,tmp)
            # !!! here is the problem, if stuff_waiting_to_be_acknowleged >= self.k, it never gets sent

    def send_frame(self,ft:ax25.FrameType,cr:bool=False,pf:bool=False,s:str=None):
        dst = ax25.Address(self.bbs)
        dst.command_response = cr
        src = ax25.Address(self.mycall)
        src.command_response = not cr
        control = ax25.Control(ft)
        control.poll_final = pf
        if ft.is_I():
            self.ns = self.vs
            control.send_seqno = self.ns
        if ft.is_I() or ft.is_S():
            self.nr = self.vr
            control.recv_seqno = self.nr
            self.last_ack_sent = self.nr
        if ft in (
            ax25.FrameType.I,
            ax25.FrameType.UI,
            ax25.FrameType.FRMR,
            ax25.FrameType.XID,
            ax25.FrameType.TEST) and str:
                frame = ax25.Frame(dst,src,control=control,pid=UNPROTO_PID,data=s.encode())
        else:
                frame = ax25.Frame(dst,src,control=control,pid=UNPROTO_PID)
        
        msg = bytes(1)+frame.pack() # bytes(1) means one byte with a value of 0
        self.serialStream.write(msg)
        if ft.is_I():
            self.t1_timer.start(self.t1)
            print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")
            self.stuff_waiting_to_be_acknowleged.append((self.ns,msg))
            self.vs = (self.vs+1) & (self.modulo-1)
        elif ft == ax25.FrameType.SABM:
            self.t1_timer.start(self.t1)
            print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")

