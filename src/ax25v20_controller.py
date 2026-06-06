from collections import deque
from datetime import datetime
from enum import IntEnum

import ax25
from PySide6.QtCore import QObject, Signal, QTimer

from globalsignals import global_signals

"""
This file is a partial implmentation of the ax.25 protocol version 2.0
It does not support ant of the"busy" stuff
"""

UNPROTO_PID = 0xf0

class AX25State(IntEnum):
    S1_DISCONNECTED = 1 # idle
    S2_LINK_SETUP = 2
    S3_FRAME_REJECT = 3
    S4_DISCONNECT_REQ = 4
    S5_INFORMATION_XFR = 5
    S6_REJ_FRAME_SENT = 6
    S7_AWAITING_ACK = 7
    # no support for any "busy" stuff, states 8-15

class AX25Event(IntEnum):
    # these all have frames as the second tuple
    I_CMD = 1
    RR_CMD = 2
    REJ_CMD = 3
    RNR_CMD = 4
    SABM_CMD = 5
    DISC_CMD = 6
    RR_RESP = 7
    REJ_RESP = 8
    RNR_RESP = 9
    UA_RESP = 10
    DM_RESP = 11
    FRMR_RESP = 12
    # these do not have a frame associated with them
    LOCAL_START = 20
    LOCAL_STOP = 21
    T1_EXP = 22
    T2_EXP = 23
    T3_EXP = 24
    N2_EXCEEDED = 25
    INVALID_NS = 26
    INVALID_NR = 27
    BOGUS_FRAME = 28

class AX25_Controller(QObject):
    signal_bytes_ready = Signal(bytes) # data output to upper layer
    signal_write = Signal(ax25.Frame) # data output to lower layer
    signal_connected = Signal()
    signal_disconnected = Signal()
    def __init__(self,pipeline):
        super().__init__()
        self.pipeline = pipeline
        self.mycalls = ("","")
        self.bbscall = ""
        self.monitor_mode = False
        # these variable names are right out of the AX25 spec
        self.vs = 0 # Send State variable (the next one to be sent)
        self.ns = 0 # Send Sequence Number (the last one sent)
        self.vr = 0 # Receive State variable (the next one we expect to receive)
        self.nr = 0 # Receive Sequence Number (the last one received)
        self.va = 0 # Acknowledge State Variable (the last one that we sent that has been ack'd)
        self.srt = 0 # smoothed round trip time
        # some more variable names from the spec
        self.t1_v = 40000 # acknowledgement time
        self.t2_v = 200 # response delay time, is milliseconds to wait for consecutive packets
        self.t3_v = 10000 # inactive link time
        self.n1 = 128 # maximum bytes in a I packet, aka PACLEN
        self.n2 = 4 # maximum retries
        self.k = 2 # window size, known to many users as MAXFRAME
        self.modulo = 8 # 128 would be better but not supported in ax25 module, is part of v2.2
        self.state = AX25State.S1_DISCONNECTED
        self.error_code = ""
        self.rc = 0 # retry counter
        self.i_frame_queue = deque() # contains strings
        self.stuff_waiting_to_be_acknowleged = [None] * self.modulo
        self.t1 = QTimer()
        self.t1.setSingleShot(True)
        self.t1.timeout.connect(self.on_t1_timeout)
        self.t2 = QTimer()
        self.t2.setSingleShot(True)
        self.t2.setInterval(self.t2_v)
        self.t2.timeout.connect(self.on_t2_timeout)
        self.t3 = QTimer()
        self.t3.setSingleShot(True)
        self.t3.setInterval(self.t3_v)
        self.t3.timeout.connect(self.on_t3_timeout)
        def is_command(f:ax25.Frame):
            return f.dst.command_response and not f.src.command_response
        ax25.Frame.is_command = is_command

    # hi-level functions

    def start_session(self,mycalls:tuple[str,str],bbscall:str):
        self.mycalls = mycalls
        self.bbscall = bbscall
        self.monitor_mode = False
        global_signals.signal_connected.connect(self.onConnected)        
        self.event(AX25Event.LOCAL_START)

    def start_monitor_session(self):
        self.mycalls = ("","")
        self.bbscall = ""
        self.monitor_mode = True

    def stop_session(self):
        # send IDENT if operating in tactical mode
        if self.mycalls[0] and self.mycalls[0] != self.mycalls[1]:
            msg = f"{self.mycalls[1]} operating as {self.mycalls[0]}"
            self.create_and_send_ident_frame(msg)
        self.event(AX25Event.LOCAL_STOP)
        global_signals.signal_status_bar_message.emit("")

    def event(self,event) -> None: # event is sometimes just an int, but often tupled with an AX25 frame
        match (self.state):
            case AX25State.S1_DISCONNECTED:
                self.state_s1_disconnected_event(event)
            case AX25State.S2_LINK_SETUP:
                self.state_s2_link_setup_event(event)
            case AX25State.S3_FRAME_REJECT:
                self.state_s3_frame_reject_event(event)
            case AX25State.S4_DISCONNECT_REQ:
                 self.state_s4_disconnect_req_event(event)
            case AX25State.S5_INFORMATION_XFR:
                self.state_s5_information_xfr_event(event)
            case AX25State.S6_REJ_FRAME_SENT:
                self.state_s6_rej_frame_sent_event(event)
            case AX25State.S7_AWAITING_ACK:
                self.status_s7_awaiting_ack_event(event)

    def state_s1_disconnected_event(self,event):
        if isinstance(event, tuple):
            evcode = event[0]
            frame = event[1]
            pf = event[2]
        else:
            evcode = event
            frame = None
            pf = False

        match (evcode):
            case AX25Event.I_CMD | AX25Event.RR_CMD | AX25Event.REJ_CMD | AX25Event.RNR_CMD:
                if pf:
                    self.create_and_send_frame(ax25.FrameType.DM,False,pf)
            case AX25Event.SABM_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.DISC_CMD:
                self.create_and_send_frame(ax25.FrameType.DM,False,pf)
            case AX25Event.LOCAL_START:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
    
    def state_s2_link_setup_event(self,event):
        if isinstance(event, tuple):
            evcode = event[0]
            frame = event[1]
            pf = event[2]
        else:
            evcode = event
            frame = None
            pf = False

        match (evcode):
            case AX25Event.SABM_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.DISC_CMD:
                self.create_and_send_frame(ax25.FrameType.DM,False,pf)
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.UA_RESP:
                self.signal_connected.emit()
                self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.DM_RESP:
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.LOCAL_STOP:
                self.create_and_send_frame(ax25.FrameType.DISC,True,True)
                self.state = AX25State.S4_DISCONNECT_REQ
            case AX25Event.T1_EXP | AX25Event.T3_EXP:
                self.rc += 1
                if self.rc >= self.n2:
                    return self.event(AX25Event.N2_EXCEEDED)
                self.create_and_send_frame(ax25.FrameType.SABM,True,True)
                self.t3.stop()
                self.t1.start(self.t1_v)
                print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.T2_EXP:
                pass
            case AX25Event.N2_EXCEEDED:
                self.state = AX25State.S1_DISCONNECTED
    
    def state_s3_frame_reject_event(self,event):
        if isinstance(event, tuple):
            evcode = event[0]
            frame = event[1]
            pf = event[2]
        else:
            evcode = event
            frame = None
            pf = False

        match (evcode):
            case AX25Event.I_CMD | AX25Event.RR_CMD | AX25Event.REJ_CMD | AX25Event.RNR_CMD:
                if (pf):
                    self.create_and_send_frame(ax25.FrameType.FRMR,False,False)
            case AX25Event.SABM_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.DISC_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.FRMR_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_START:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_STOP:
                self.create_and_send_frame(ax25.FrameType.DISC,True,True)
                self.state = AX25State.S4_DISCONNECT_REQ
            case AX25Event.T1_EXP:
                self.create_and_send_frame(ax25.FrameType.FRMR,False,False)
            case AX25Event.T3_EXP:
                self.create_and_send_frame(ax25.FrameType.FRMR,False,False)
            case AX25Event.N2_EXCEEDED:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
    
    def state_s4_disconnect_req_event(self,event):
        if isinstance(event, tuple):
            evcode = event[0]
            frame = event[1]
            pf = event[2]
        else:
            evcode = event
            frame = None
            pf = False

        match (evcode):
            case AX25Event.I_CMD | AX25Event.RR_CMD | AX25Event.REJ_CMD | AX25Event.RNR_CMD:
                if (pf):
                    self.create_and_send_frame(ax25.FrameType.DM,False,pf)
                    self.state = AX25State.S1_DISCONNECTED
            case AX25Event.SABM_CMD:
                self.create_and_send_frame(ax25.FrameType.DM,False,pf)
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.DISC_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.UA_RESP:
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.DM_RESP:
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.LOCAL_START:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.T1_EXP | AX25Event.T3_EXP:
                self.create_and_send_frame(ax25.FrameType.DISC,False,False)
            case AX25Event.N2_EXCEEDED:
                self.state = AX25State.S1_DISCONNECTED
    
    def state_s5_information_xfr_event(self,event):
        if isinstance(event, tuple):
            evcode = event[0]
            frame = event[1]
            pf = event[2]
        else:
            evcode = event
            frame = None
            pf = False

        # RNR should be handled differently but not supporting busy mode noe
        match (evcode):
            case AX25Event.I_CMD | AX25Event.RR_CMD | AX25Event.REJ_CMD | AX25Event.RNR_CMD:
                if (pf):
                    self.create_and_send_frame(ax25.FrameType.RR,False,pf)
                #if not self.send_i_frames():
                #    self.create_and_send_frame(ax25.FrameType.RR,False,False)
            case AX25Event.SABM_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.DISC_CMD:
                self.signal_disconnected.emit()
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.RR_RESP | AX25Event.REJ_RESP | AX25Event.RNR_RESP:
                self.send_i_frames()
            case AX25Event.DM_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.FRMR_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_START:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_STOP:
                self.create_and_send_frame(ax25.FrameType.DISC,True,True)
                self.state = AX25State.S4_DISCONNECT_REQ
            case AX25Event.T1_EXP | AX25Event.T3_EXP:
                self.rc += 1
                if self.rc >= self.n2:
                    return self.event(AX25Event.N2_EXCEEDED)
                self.create_and_send_frame(ax25.FrameType.RR,True,True)
                self.state = AX25State.S7_AWAITING_ACK
            case AX25Event.T2_EXP:
                self.create_and_send_frame(ax25.FrameType.RR,False,False)
            case AX25Event.N2_EXCEEDED:
                self.signal_disconnected.emit()
                self.state = AX25State.S1_DISCONNECTED # docs do not say this but ... 
            case AX25Event.INVALID_NS:
                self.create_and_send_frame(ax25.FrameType.REJ,False,False)
                self.state = AX25State.S6_REJ_FRAME_SENT
            case AX25Event.INVALID_NR | AX25Event.BOGUS_FRAME:
                self.create_and_send_frame(ax25.FrameType.FRMR,False,False)
                self.state = AX25State.S3_FRAME_REJECT
    
    def state_s6_rej_frame_sent_event(self,event):
        if isinstance(event, tuple):
            evcode = event[0]
            frame = event[1]
            pf = event[2]
        else:
            evcode = event
            frame = None
            pf = False

        match (evcode):
            case AX25Event.I_CMD:
                if (pf):
                    self.create_and_send_frame(ax25.FrameType.RR,False,pf)
                    self.state = AX25State.S5_INFORMATION_XFR
                else:
                    if not self.send_i_frames():
                        self.create_and_send_frame(ax25.FrameType.RR,False,False)
                    self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.RR_CMD | AX25Event.REJ_CMD | AX25Event.RNR_CMD:
                if (pf):
                    self.create_and_send_frame(ax25.FrameType.RR,False,pf)
                else:
                    self.send_i_frames()
            case AX25Event.SABM_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.DISC_CMD:
                self.signal_disconnected.emit()
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.RR_RESP | AX25Event.REJ_RESP | AX25Event.RNR_RESP:
                self.send_i_frames()
            case AX25Event.UA_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.DM_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.FRMR_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_START:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_STOP:
                self.create_and_send_frame(ax25.FrameType.DISC,True,True)
                self.state = AX25State.S4_DISCONNECT_REQ
            case AX25Event.T1_EXP:
                self.rc += 1
                if self.rc >= self.n2:
                    return self.event(AX25Event.N2_EXCEEDED)
                self.create_and_send_frame(ax25.FrameType.RR,True,True)
                self.state = AX25State.S7_AWAITING_ACK
            case AX25Event.N2_EXCEEDED:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.INVALID_NS:
                self.create_and_send_frame(ax25.FrameType.REJ,False,False)
                self.state = AX25State.S6_REJ_FRAME_SENT
            case AX25Event.INVALID_NR | AX25Event.BOGUS_FRAME:
                self.create_and_send_frame(ax25.FrameType.FRMR,False,False)
                self.state = AX25State.S3_FRAME_REJECT
    
    def status_s7_awaiting_ack_event(self,event):
        if isinstance(event, tuple):
            evcode = event[0]
            frame = event[1]
            pf = event[2]
        else:
            evcode = event
            frame = None
            pf = False

        match (evcode):
            case AX25Event.I_CMD | AX25Event.RR_CMD | AX25Event.REJ_CMD | AX25Event.RNR_CMD:
                if (pf):
                    self.create_and_send_frame(ax25.FrameType.RR,False,pf)
                else:
                    self.send_i_frames()
            case AX25Event.RR_CMD:
                pass
            case AX25Event.REJ_CMD:
                pass
            case AX25Event.RNR_CMD:
                pass
            case AX25Event.SABM_CMD:
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S5_INFORMATION_XFR
            case AX25Event.DISC_CMD:
                self.signal_disconnected.emit()
                self.create_and_send_frame(ax25.FrameType.UA,False,pf)
                self.state = AX25State.S1_DISCONNECTED
            case AX25Event.RR_RESP | AX25Event.REJ_RESP | AX25Event.RNR_RESP:
                if (pf):
                    self.state = AX25State.S5_INFORMATION_XFR
                    self.send_i_frames()
                else:
                    self.send_i_frames()
            case AX25Event.UA_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.DM_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.FRMR_RESP:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_START:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.LOCAL_STOP:
                self.create_and_send_frame(ax25.FrameType.DISC,True,True)
                self.state = AX25State.S4_DISCONNECT_REQ
            case AX25Event.T1_EXP:
                self.rc += 1
                if self.rc >= self.n2:
                    return self.event(AX25Event.N2_EXCEEDED)
                self.create_and_send_frame(ax25.FrameType.RR,True,True)
            case AX25Event.T2_EXP:
                pass
            case AX25Event.N2_EXCEEDED:
                self.establish_data_link()
                self.state = AX25State.S2_LINK_SETUP
            case AX25Event.INVALID_NR | AX25Event.BOGUS_FRAME:
                self.create_and_send_frame(ax25.FrameType.FRMR,False,False)
                self.state = AX25State.S3_FRAME_REJECT
    
	# the next group of functions are called by the upper layer (slots using Qt terminology)
    def dl_connect_request(self):
        self.srt = 40000 # initial guess for t1 # very large for debugging
        self.t1_v = self.srt * 2

        self.establish_data_link()
        self.layer3initiated = True
        self.state = AX25State.LINK_SETUP

    def dl_disconnect_request(self):
        pass
		
    def dl_data_request(self,msg:bytes):
        self.send(msg)

    def dl_unit_data_request(self,msg:bytes):
        pass

    def on_write(self,msg:bytes):
        self.send(msg)

    def on_t1_timeout(self):
        print(f"Timer 1 triggered at {datetime.now().strftime("%H:%M:%S.%f")}")
        self.event(AX25Event.T1_EXP)

    def on_t2_timeout(self):
        print(f"Timer 2 triggered at {datetime.now().strftime("%H:%M:%S.%f")}, l={self.va} r={self.vr}/{self.nr}")
        self.event(AX25Event.T2_EXP)

    def on_t3_timeout(self):
        print(f"Timer 3 triggered at {datetime.now().strftime("%H:%M:%S.%f")}")
        self.event(AX25Event.T3_EXP)

    def send_i_frames(self) -> bool:
        sent = False
        while self.i_frame_queue and self.vs != (self.va + self.k) % self.modulo: # at maximum window size (backlog)
            tmp = self.i_frame_queue.popleft()
            self.create_and_send_frame(ax25.FrameType.I,True,False,tmp)
            sent = True
            if self.t1.remainingTime() < 0:
                self.t3.stop()
                self.t1.start(self.t1_v)
                print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")
        return sent


    # def resend_all_pending(self):
    #     for seq,ft,tmp in self.stuff_waiting_to_be_acknowleged:
    #         print(f"peeking {seq} {len(tmp)} {tmp}")
    #         try:
    #             self.resend_frame(ft,tmp)
    #         except UnicodeDecodeError:
    #             print(f"{seq} {len(tmp)} {tmp} ",end=" ")
    #             for c in tmp:
    #                 print(c,end=" ")
    #             print

    def on_bytes_ready(self,msg:bytes):
        if self.monitor_mode:
            return
        # only pay attention if this is for us
        frame = ax25.Frame.unpack(msg)
        if frame.dst.call != self.mycalls[0]:
            return

        control = frame.control
        pf = control.poll_final
        ft = control.frame_type

        if ft.is_I():
            self.ns = control.send_seqno
            self.incoming_i_frame(frame)
            print(f"Timer 2 set at {datetime.now().strftime("%H:%M:%S.%f")}")
            self.t2.start()
        if not frame.control.frame_type.is_U():
            self.nr = control.recv_seqno
            self.acknowledge_up_to(self.nr)

        #print(f"new packet: state={self.state} vs={self.vs} vr={self.vr} v={self.va} ns={self.ns} nr={self.nr}")
        if frame.is_command():
            if ft == ax25.FrameType.I:
                self.event((AX25Event.I_CMD,frame,pf))
            elif ft == ax25.FrameType.RR:
                self.event((AX25Event.RR_CMD,frame,pf))
            elif ft == ax25.FrameType.REJ:
                self.event((AX25Event.REJ_CMD,frame,pf))
            elif ft == ax25.FrameType.RNR:
                self.event((AX25Event.RNR_CMD,frame,pf))
            elif ft == ax25.FrameType.SABM:
                self.event((AX25Event.SABM_CMD,frame,pf))
            elif ft == ax25.FrameType.DISC:
                self.event((AX25Event.DISC_CMD,frame,pf))
        else:
            if ft == ax25.FrameType.RR:
                self.event((AX25Event.RR_RESP,frame,pf))
            elif ft == ax25.FrameType.REJ:
                self.event((AX25Event.REJ_RESP,frame,pf))
            elif ft == ax25.FrameType.RNR:
                self.event((AX25Event.RNR_RESP,frame,pf))
            elif ft == ax25.FrameType.UA:
                self.event((AX25Event.UA_RESP,frame,pf))
            elif ft == ax25.FrameType.DM:
                self.event((AX25Event.DM_RESP,frame,pf))
            elif ft == ax25.FrameType.FRMR:
                self.event((AX25Event.FRMR_RESP,frame,pf))
        if self.state.value >= AX25State.S5_INFORMATION_XFR:
            self.send_i_frames()


    def acknowledge_up_to(self,m):
        while self.va != m:
            self.stuff_waiting_to_be_acknowleged[self.va] = None
            self.va = (self.va + 1) % self.modulo
        self.check_i_frame_ackd(m)

    def incoming_i_frame(self,frame):
        if self.ns == self.vr:
            self.vr = (self.vr + 1)  % self.modulo
            self.signal_bytes_ready.emit(frame.data)

    def establish_data_link(self):
        #self.clear_exception_conditions()
        self.rc = 0
        self.create_and_send_frame(ax25.FrameType.SABM,True,True)
        self.t3.stop()
        self.t1.start(self.t1_v)
        print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")

    def check_i_frame_ackd(self,m):
        if m == self.vs:
            self.t1.stop()
            self.t3.start(self.t3_v)
            self.select_t1_value()
        else: # not all frames ackd
            if m != self.va:
                self.t1.start(self.t1_v)
                print(f"Timer 1x set at {datetime.now().strftime("%H:%M:%S.%f")}")

    def select_t1_value(self):
        pass #! needs work

    # def nr_error_recovey(self):
    #     self.establish_data_link()
    #     self.layer3initiated = False

    # def clear_exception_conditions(self):
    #     self.reject_exception = False
    #     self.acknowledge_pending = False
    #     pass # busy stuff not supported

    # def transmit_enquiry(self):
    #     self.nr = self.vr
    #     self.create_and_send_frame(ax25.FrameType.RR,True,True)
    #     self.acknowledge_pending = False
    #     self.t1.start(self.t1_v)

    # def enquiry_response(self):
    #     self.nr = self.vr
    #     self.create_and_send_frame(ax25.FrameType.RR,True,True) #! not sure about P/F bit
    #     self.acknowledge_pending = False
    
    # def invoke_retransmission(self):
    #     x = self.vs    
    #     while True:
    #         #!push frame "VS"
    #         self.vs = (self.vs + 1)  % self.modulo
    #         if self.vs == x:
    #             break


    # def check_need_for_response(self,cmd:bool,p:bool):
    #     if cmd and p:
    #         self.enquiry_response(True)
    #     #! more stuff

    # def ui_check(self,cmd:bool,p:bool):
    #     if cmd:
    #         #! tell app
    #         pass

    # def select_t1_value(self):
    #     pass #! needs work


    # slots

    def onConnected(self):
        print("Connected!")
        self.pipeline.add_bbs("[JNOS-2.0k.2.xsc.8-B1FHIM$]") #!! temporary, should pass the welcome message sent by the BBS


    def send(self,s:str): # these are ordinary strings, get sent as "I" frames
        # if too big, split
        while len(s) > self.n1:
            self.i_frame_queue.append(s[:self.n1])
            s = s[self.n1:]
        self.i_frame_queue.append(s)
        self.send_i_frames()

    def send_ui(self,s:str): # these are ordinary strings, get sent as "UI" frames
        # if too big, split
        while len(s) > self.n1:
            self.create_and_send_frame(ax25.FrameType.UI,True,False,s[:self.n1])
            s = s[self.n1:]
        self.create_and_send_frame(ax25.FrameType.UI,True,False,s)

    def create_and_send_frame(self,ft:ax25.FrameType,cr:bool=False,pf:bool=False,s:str=None):
        dst = ax25.Address(self.bbscall)
        dst.command_response = cr
        src = ax25.Address(self.mycalls[0])
        src.command_response = not cr
        control = ax25.Control(ft)
        control.poll_final = pf
        if ft.is_I():
            control.send_seqno = self.vs
            self.vs = (self.vs + 1) % self.modulo
        if ft.is_I() or ft.is_S():
            self.nr = self.vr
            control.recv_seqno = self.nr
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
        self.send_frame(ft,msg)


    def create_and_send_ident_frame(self,s:str):
        dst = ax25.Address("IDENT")
        dst.command_response = False
        src = ax25.Address(self.mycalls[0])
        src.command_response = False
        control = ax25.Control(ax25.FrameType.UI)
        control.poll_final = False
        frame = ax25.Frame(dst,src,control=control,pid=UNPROTO_PID,data=s.encode())
        msg = bytes(1)+frame.pack() # bytes(1) means one byte with a value of 0
        self.send_frame(ax25.FrameType.UI,msg)


    def send_frame(self,ft:ax25.FrameType,msg:bytes): # msg is a full ax25 frame including the 0 at the start
        self.signal_write.emit(msg)
        if ft.is_I():
            self.t1.start(self.t1_v)
            print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")
            print(f"pushing {self.ns} {len(msg)} {msg})")
            self.stuff_waiting_to_be_acknowleged[self.ns] = (ft,msg)
        elif ft == ax25.FrameType.SABM:
            self.t1.start(self.t1_v)
            print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")

    def resend_frame(self,ft:ax25.FrameType,msg:bytes): # same as previous but does not push into stuff_waiting_to_be_acknowleged
        self.signal_write.emit(msg)
        if ft.is_I():
            self.t1.start(self.t1_v)
            print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")
        elif ft == ax25.FrameType.SABM:
            self.t1.start(self.t1_v)
            print(f"Timer 1 set at {datetime.now().strftime("%H:%M:%S.%f")}")
