from collections import deque
from datetime import datetime
from enum import IntEnum

import ax25
from PySide6.QtCore import QObject, Signal, QTimer, qDebug

UNPROTO_PID = 0xf0

class AX25State(IntEnum):
    DISCONNECTED = 0 # idle
    AWAITING_CONNECTION = 1
    AWAITING_RELEASE = 2
    CONNECTED = 3
    TIMER_RECOVERY = 4
    # not supported AWAITING_V2_2_CONNECTION = 5

class AX25_Controller(QObject):
    signal_bytes_ready = Signal(str) # I frame ready
    signal_write = Signal(ax25.Frame) # sends to left
    def __init__(self):
        super().__init__()
        self.mycalls = ("","")
        self.bbscall = ""
        self.monitor_mode = False
        # these variable names are right out of the AX25 spec
        self.vs = 0 # Send State variable
        self.ns = 0 # Send Sequence Number
        self.vr = 0 # Receive State variable
        self.nr = 0 # Receive Sequence Number
        self.va = 0 # Acknowledge State Variable
        self.layer3initiated = False
        self.reject_exception = False
        self.acknowledge_pending = False
        self.srt = 0 # smoothed round trip time
        # some more variable names from the spec
        self.t1_v = 4000 # acknowledgement time
        self.t2_v = 1000 # response delay time, is milliseconds to wait for consecutive packets
        self.t3_v = 10000 # inactive link time
        self.n1 = 128 # maximum bytes in a I packet, aka PACLEN
        self.n2 = 4 # maximum retries
        self.k = 2 # window size, known to many users as MAXFRAME
        self.modulo = 8 # 128 would be better but not supported in ax25 module, is part of v2.2
        self.state = AX25State.DISCONNECTED
        self.error_code = ""
        self.rc = 0 # retry counter
        self.i_frame_queue = deque() # contains strings
        self.stuff_waiting_to_be_acknowleged = deque() # contains tuples of (seq;int,ft:x25.FrameType,packet:bytes)
        self.t1 = QTimer()
        self.t1.setSingleShot(True)
        self.t1.timeout.connect(self.on_t1_timeout)
        self.t2 = QTimer()
        self.t2.setSingleShot(True)
        self.t2.timeout.connect(self.on_t2_timeout)
        self.t3 = QTimer()
        self.t3.setSingleShot(True)
        self.t3.timeout.connect(self.on_t3_timeout)

    def start_session(self,mycalls:tuple[str,str],bbscall:str):
        self.mycalls = mycalls
        self.bbscall = bbscall
        self.monitor_mode = False
    # hi-level functions


    def stop_session(self):
        # send IDENT if operating in tactical mode
        super().stop_session()
        if self.mycalls[0] != self.mycalls[1]:
            msg = f"{self.mycall[1]} operating as {self.mycall[0]}"
            self.create_and_send_ident_frame(msg)
        global_signals.signal_status_bar_message.emit("")
        self.signalDisconnected.emit()

	# the next group of functions are called by the upper layer (slots using Qt terminology)
    def dl_connect_request(self):
        self.bbscall = self.bbscall
        self.srt = 2000 # initial guess for t1 
        self.t1_v = self.srt * 2
        self.establish_data_link()
        self.layer3initiated = True
        self.state = AX25State.AWAITING_CONNECTION

    def dl_disconnect_request(self):
        pass
		
    def dl_data_request(self,msg:bytes):
        pass
		
    def dl_unit_data_request(self,msg:bytes):
        pass

    def on_t1_timeout(self):
        print(f"Timer 1 triggered at {datetime.now().strftime("%H:%M:%S.%f")}")
        if self.state == AX25State.AWAITING_CONNECTION:
            if self.rc >= self.n2:
                self.state = AX25State.DISCONNECTED
                ### maybe stop_session?
            else:
                self.rc += 1
                self.create_and_send_frame(ax25.FrameType.SABM,True,True)
        elif self.state ==  AX25State.CONNECTED:
            # must be an I-packet timeout
            if self.rc >= self.n2:
                self.state = AX25State.DISCONNECTED
                ### maybe stop_session?
            else:
                self.rc += 1
                self.resend_all_pending()

    def on_t2_timeout(self):
        print(f"Timer 2 triggered at {datetime.now().strftime("%H:%M:%S.%f")}, l={self.va} r={self.vr}/{self.nr}")
        #if self.va + 1 != self.vr:
        #    self.create_and_send_frame(ax25.FrameType.RR)
        self.state_connected_i_frame_queue_not_empty()

    def on_t3_timeout(self):
        print(f"Timer 3 triggered at {datetime.now().strftime("%H:%M:%S.%f")}")

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
        if frame.dst.call != self.mycall[0]:
            return
        # what we do next is dependent on our current state
        match(self.state):
            case AX25State.DISCONNECTED:
                self.state = self.state_disconnected_message(msg)
            case AX25State.AWAITING_CONNECTION:
                self.state = self.state_awaiting_connection(msg)
            case AX25State.AWAITING_RELEASE:
                self.state = self.state_awaiting_release(msg)
            case AX25State.CONNECTED:
                self.state = self.state_connected_message(msg)
            case AX25State.TIMER_RECOVERY:
                self.state = self.status_timer_recovery_message(msg)
    
    def state_disconnected_message(self,msg:bytes):
        frame = ax25.Frame.unpack(msg)
        control = frame.control
        ft = control.frame_type
        match ft:
            case ax25.FrameType.UA:
                self.error_code = "C,D"
                return AX25State.DISCONNECTED
            case ax25.FrameType.DM:
                return AX25State.DISCONNECTED
            case ax25.FrameType.UI:
                self.ui_check()
                if control.poll_final:
                    self.create_and_send_frame(ax25.FrameType.DM,False,True)
            case ax25.FrameType.DISC:
                if control.poll_final:
                    self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
            case ax25.FrameType.SABM: # we don't really need to support these, not operating as peers
                self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
            case ax25.FrameType.SABME: # we don't really need to support these, not operating as peers
                self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
            case _:
                self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)

        return AX25State.DISCONNECTED

    def state_awaiting_connection(self,msg:bytes):
        frame = ax25.Frame.unpack(msg)
        control = frame.control
        ft = control.frame_type
        match ft:
            case ax25.FrameType.SABM | ax25.FrameType.SABME:
                self.create_and_send_frame(ax25.FrameType.UA,False,control.poll_final)
            case ax25.FrameType.DISC:
                if control.poll_final:
                    self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
            case ax25.FrameType.UI:
                self.ui_check()
                if control.poll_final:
                    self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
            case ax25.FrameType.DM:
                if control.poll_final:
                    #! more stuff
                    self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
                    return AX25State.DISCONNECTED
            case ax25.FrameType.UA:
                if control.poll_final:
                    #! more stuff, this is the "no" then "yes" branch
                    self.t1.stop()
                    self.t2.stop()
                    #! select t1 value
                    return AX25State.CONNECTED
            case ax25.FrameType.SABME:
                self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
        return AX25State.AWAITING_CONNECTION

    def state_awaiting_release(self,msg:bytes):
        frame = ax25.Frame.unpack(msg)
        control = frame.control
        ft = control.frame_type
        match ft:
            case ax25.FrameType.UA | ax25.FrameType.DM:
                if control.poll_final:
                    self.t1.stop()
                    return AX25State.DISCONNECTED
        return AX25State.AWAITING_RELEASE

    def state_connected_i_frame_queue_not_empty(self):
        if self.vs == self.va + self.k:
            return
        self.ns = self.vs
        self.nr = self.vr
        tmp = self.i_frame_queue.popleft()
        self.create_and_send_frame(ax25.FrameType.I,True,False,tmp)
        self.vs = self.vs + 1
        self.acknowledge_pending = False
        if self.t1.remainingTime() < 0:
            self.t3.stop()
            self.t1.start()

    def state_connected_message(self,msg:bytes): # this is a long one
        frame = ax25.Frame.unpack(msg)
        control = frame.control
        ft = control.frame_type
        match ft:
            case ax25.FrameType.SABM:
                self.create_and_send_frame(ax25.FrameType.UA,False,control.poll_final)
                self.clear_exception_conditions()
                self.error_code = "F"
                if self.vs != self.va:
                    self.i_frame_queue.clear()
                self.t1.stop()
                self.t3.start()
                self.vs = 0
                self.va = 0
                self.vr = 0
            case ax25.FrameType.SABME:
                self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
            case ax25.FrameType.DISC:
                self.i_frame_queue.clear()
                self.create_and_send_frame(ax25.FrameType.UA,False,control.poll_final)
                self.t1.stop()
                self.t3.stop()
                self.state = AX25State.DISCONNECTED
            case ax25.FrameType.UA:
                self.error_code = "C"
                self.establish_data_link()
                self.layer3initiated = False
                self.state = AX25State.AWAITING_CONNECTION
            case ax25.FrameType.DM:
                self.error_code = "E"
                self.i_frame_queue.clear()
                self.t1.stop()
                self.t3.stop()
                self.state = AX25State.DISCONNECTED
            case ax25.FrameType.FRMR:
                self.error_code = "K"
                self.establish_data_link()
                self.layer3initiated = False
                self.state = AX25State.AWAITING_CONNECTION
            case ax25.FrameType.UI:
                # self.create_and_send_frame(ax25.FrameType.UI,True,False)
                self.ui_check()
                if control.poll_final:
                    self.enquiry_response()
            # note - LM-SEIZE is here in the spec
            case ax25.FrameType.RR | ax25.FrameType.RNR:
                self.check_need_for_response()
                if self.va <= self.nr <= self.vs:
                    self.check_i_frame_ackd()
                    self.state_connected_i_frame_queue_not_empty()
                else:
                    self.nr_error_recovey()
                    self.state = AX25State.AWAITING_CONNECTION
            case ax25.FrameType.SREJ:
                self.check_need_for_response()
                if self.va <= self.nr <= self.vs:
                    if control.poll_final:
                        self.va = self.nr
                    self.t1.stop()
                    self.t3.start()
                    self.select_t1_value()
                    # push frame NR on queue
                else:
                    self.nr_error_recovey()
                    self.state = AX25State.AWAITING_CONNECTION
            case ax25.FrameType.REJ:
                self.check_need_for_response()
                if self.va <= self.nr <= self.vs:
                    self.va = self.nr
                    self.t1.stop()
                    self.t3.stop()
                    self.select_t1_value()
                    self.invoke_retransmission()
                else:
                    self.nr_error_recovey()
                    self.state = AX25State.AWAITING_CONNECTION
            case ax25.FrameType.I:
                if frame.dst.command_response and not frame.src.command_response:
                    pass
                if self.va <= self.nr <= self.vs:
                    self.check_i_frame_ackd()
                    if self.ns == self.vr:
                        self.vr = self.vr + 1
                        self.reject_exception = False
                        #! tell app we have data
                        self.signal_bytes_ready.emit(frame.data.decode())
                        #while self.xx[self.vr]: #!!! don't understand this loop, looks through saved frames - must be related to SREJ
                        #    #! get self.xx[self.vr]
                        #    #! tell app we have it
                        #    self.signal_bytes_ready.emit()
                        #    self.vr = self.vr + 1
                        if control.poll_final:
                            self.nr = self.vr
                            self.create_and_send_frame(ax25.FrameType.RM,False,True)
                            self.acknowledge_pending = False
                        else:
                            if not self.acknowledge_pending:
                                #! LM_SIEZE
                                self.acknowledge_pending = True
                    else:
                        if self.reject_exception:
                            #! what to they mean by discard contents of I frame? self.i_frame_queue.clear()
                            if control.poll_final:
                                self.nr = self.vr
                                self.create_and_send_frame(ax25.FrameType.DM,False,True)
                                self.acknowledge_pending = False
                        else:
                            if False: ## self.srej_enabled
                                pass
                            else:
                                #! what to they mean by discard comtents of I frame? self.i_frame_queue.clear()
                                self.reject_exception = True
                                self.nr = self.vr
                                self.create_and_send_frame(ax25.FrameType.REJ,False,True)
                                self.acknowledge_pending = False

                else:
                    self.nr_error_recovey()
                    self.state = AX25State.AWAITING_CONNECTION
        return AX25State.CONNECTED

    def status_timer_recovery_message(self,msg:bytes):
        frame = ax25.Frame.unpack(msg)
        control = frame.control
        ft = control.frame_type
        match ft:
            case ax25.FrameType.SABM:
                self.create_and_send_frame(ax25.FrameType.UI,False,control.poll_final)
                #! more stuff
                self.t1.stop()
                self.t3.start()
                self.vs = 0
                self.va = 0
                self.vr = 0
            case ax25.FrameType.SABME:
                self.create_and_send_frame(ax25.FrameType.DM,False,control.poll_final)
            case ax25.FrameType.RR:
                pass
            case ax25.FrameType.RNR:
                pass
            case ax25.FrameType.DISC:
                pass
            case ax25.FrameType.UA:
                pass
            case ax25.FrameType.UI:
                pass
            case ax25.FrameType.REJ:
                pass
            case ax25.FrameType.DM:
                pass
            case ax25.FrameType.SREG:
                pass
        return AX25State.TIMER_RECOVERY
    
    def nr_error_recovey(self):
        self.establish_data_link()
        self.layer3initiated = False

    def establish_data_link(self):
        self.clear_exception_conditions()
        self.rc = 0
        self.create_and_send_frame(ax25.FrameType.SABM,True,True)
        self.t3.stop()
        self.t1.start()

    def clear_exception_conditions(self):
        self.reject_exception = False
        self.acknowledge_pending = False
        pass # busy stuff not supported

    def transmit_enquiry(self):
        self.nr = self.vr
        self.create_and_send_frame(ax25.FrameType.RR,True,True)
        self.acknowledge_pending = False
        self.t1.start()

    def enquiry_response(self):
        self.nr = self.vr
        self.create_and_send_frame(ax25.FrameType.RR,True,True) #! not sure about P/F bit
        self.acknowledge_pending = False
    
    def invoke_retransmission(self):
        x = self.vs    
        while True:
            #!push frane "VS"
            self.vs = self.vs + 1
            if self.vs == x:
                break

    def check_i_frame_ackd(self):
        if self.n2 == self.vs:
            self.va = self.nr
            self.t1.stop()
            self.t3.start()
            self.select_t1_value()
        else: # not all frames ackd
            if self.nr != self.va:
                self.va = self.nr
                self.t1.start()

    def check_need_for_response(self,cmd:bool,p:bool):
        if cmd and p:
            self.enquiry_response(True)
        #! more stuff

    def ui_check(self,cmd:bool,p:bool):
        if cmd:
            #! tell app
            pass

    def select_t1_value(self):
        pass #! needs work


        #     if ft.is_I() and control.send_seqno != self.vr:
        #     print(f"sent seq {control.send_seqno}, was expecting {self.vr}")
        #     self.create_and_send_frame(ax25.FrameType.REJ)
        #     return # spec says to discard these

        # # if this is a type I or a type RR, it will have an acknowledge number in it
        # # if this is a type "I", pass to upper layers
        # # this code is similar to the code in LineDelimitedSerialStream and should be shared somehow
        # if ft.is_I() or ft.is_S(): # this includes RR and REJ
        #     if ft.is_I():
        #         print(f"state={self.state} ft={ft.name} s={control.send_seqno} vs={self.vs} ns={self.ns} r={control.recv_seqno} vr={self.vr} nr={self.nr}")
        #     else:
        #         print(f"state={self.state} ft={ft.name} ns={self.ns} r={control.recv_seqno} vr={self.vr} nr={self.nr}")
        #     # discard any pending frames up to that number
        #     while self.stuff_waiting_to_be_acknowleged and self.stuff_waiting_to_be_acknowleged[0][0] != control.recv_seqno:
        #         print(f"ack {control.recv_seqno}, removing {self.stuff_waiting_to_be_acknowleged[0][0]}")
        #         self.stuff_waiting_to_be_acknowleged.popleft()
        #     # send any pending stuff if in window
        #     while self.stuff_to_write and len(self.stuff_waiting_to_be_acknowleged) < self.k:
        #         tmp = self.stuff_to_write.popleft()
        #         self.create_and_send_frame(ax25.FrameType.I,True,False,tmp)
        #     # if we are caught up, turn off T1
        #     if control.recv_seqno == self.vs:
        #         self.t1_timer.stop()
        #     if ft == ax25.FrameType.REJ:
        #         self.va = control.recv_seqno
        #         self.vs = control.recv_seqno
        #         self.resend_all_pending() # resend stuff
        # if ft.is_I():
        #     self.vr = (self.vr+1) & (self.modulo-1)
        #     # if the P bit is set, respond immediately
        #     if control.poll_final:
        #         self.t2_timer.stop()
        #         self.create_and_send_frame(ax25.FrameType.RR,False,True)
        #     else:
        #         self.t2_timer.start(self.t2)
        #         print(f"Timer 2 set at {datetime.now().strftime("%H:%M:%S.%f")}")
        #     if frame.data:
        #         self._sdata += frame.data
        #     self.find_lines()
        # elif ft == ax25.FrameType.UA:
        #     self.t1_timer.stop()
        #     if self.state == STATE_AWAITING_CONNECTION:
        #         # we are connected!
        #         self.vs = 0
        #         self.vr = 0
        #         self.va = 0
        #         self.state = STATE_CONNECTED
        #         self.onConnected()
        # elif ft == ax25.FrameType.DISC:
        #     # we are disconnected
        #     # acknowledge it
        #     self.state = STATE_DISCONNECTED
        #     self.create_and_send_frame(ax25.FrameType.UA,False,True)
        #     self.onDisconnected()
        #     pass
        # elif control.frame_type == ax25.FrameType.UI:
        #     # beacon-type message
        #     # if P bit is set, respond with RR or DM
        #     if control.poll_final:
        #         if self.state == STATE_CONNECTED: 
        #             self.create_and_send_frame(ax25.FrameType.RR,False,True)
        #         else:
        #             self.create_and_send_frame(ax25.FrameType.DM,False,True)
        #     pass

    # slots

    def onConnected(self):
        print("Connected!")

    def onDisconnected(self):
        print("TNC got disconnected!")
        globals.signal_status_bar_message.emit("Resetting TNC")
 
    def send(self,s:str): # these are ordinary strings, get sent as "I" frames
        # if too big, split
        while len(s) > self.n1:
            self.i_frame_queue.append(s[:self.n1])
            s = s[self.n1:]
        self.i_frame_queue.append(s)
        self.state_connected_i_frame_queue_not_empty()
#        while self.i_frame_queue and len(self.stuff_waiting_to_be_acknowleged) < self.k:
#            tmp = self.i_frame_queue.popleft()
#            self.create_and_send_frame(ax25.FrameType.I,True,False,tmp)
#            # !!! here is the problem, if stuff_waiting_to_be_acknowleged >= self.k, it never gets sent

    def send_ui(self,s:str): # these are ordinary strings, get sent as "UI" frames
        # if too big, split
        while len(s) > self.n1:
            self.create_and_send_frame(ax25.FrameType.UI,True,False,s[:self.n1])
            s = s[self.n1:]
        self.create_and_send_frame(ax25.FrameType.UI,True,False,s)

    def create_and_send_frame(self,ft:ax25.FrameType,cr:bool=False,pf:bool=False,s:str=None):
        dst = ax25.Address(self.bbscall)
        dst.command_response = cr
        src = ax25.Address(self.mycall[0])
        src.command_response = not cr
        control = ax25.Control(ft)
        control.poll_final = pf
        if ft.is_I():
            self.ns = self.vs
            control.send_seqno = self.ns
            self.vs = (self.vs+1) & (self.modulo-1)
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
        self.send_frame(ft,msg)


    def create_and_send_ident_frame(self,s:str):
        dst = ax25.Address("IDENT")
        dst.command_response = False
        src = ax25.Address(self.mycall[0])
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
            self.stuff_waiting_to_be_acknowleged.append((self.ns,ft,msg))
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
