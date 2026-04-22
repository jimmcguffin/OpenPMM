# pylint:  disable="line-too-long,missing-function-docstring,multiple-statements,no-name-in-module"

from datetime import datetime
import socket

from globalsignals import global_signals

import ax25
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtNetwork import QUdpSocket

# hide these for ordinary serial ports
BSIM_ADDR = None
#BSIM_ADDR = "127.0.0.1"
#BSIM_PORT_OUT = 2600
#BSIM_PORT_IN = (BSIM_PORT_OUT+1)

class SerialStream(QObject):
    def __init__(self,serial_port:str):
        super().__init__()
        self.encoding = "utf-8"
        self._sdata = bytearray()
        # no access to this if self.settings.getInterface("ConnectionType") == "Network":
        if BSIM_ADDR:
            self.serial_port = None
            #self.sock_in = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
            #self.sock_in.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            #self.sock_in.bind((BSIM_ADDR,BSIM_PORT_IN))
            self.sock_in = QUdpSocket()
            self.sock_in.bind(BSIM_PORT_IN)
            self.sock_in.readyRead.connect(self.read_pending_datagrams)
            self.sock_out = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
            self.sock_out.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            self.sock_out.bind((BSIM_ADDR,BSIM_PORT_OUT))
            #while (True):
            #    b,r = sock.recvfrom(1540)
        else:
            self.serial_port = serial_port
            self.sock_in = None
            self.sock_out = None
            self.serial_port.readyRead.connect(self.on_serial_port_ready)
            self._log_file = open("serial.log","ab")
            if self._log_file:
                self._log_file.write(b"\r\n--------\r\n")

    def reset(self) -> None:
        if self.serial_port:
            self.serial_port.close()
            self.serial_port.readyRead.disconnect()
        self._sdata.clear()

    def on_serial_port_ready(self) -> None: # normal path, uses serial port
        sdata = bytearray(self.serial_port.readAll())
        if self._log_file:
            self._log_file.write(sdata)
            self._log_file.flush()
        self._sdata += sdata
        return self.find_lines()

    def read_pending_datagrams(self):
        while self.sock_in.hasPendingDatagrams():
            datagram, host, port = self.sock_in.readDatagram(self.sock_in.pendingDatagramSize())
            self._sdata += datagram.data()
            return self.find_lines()        
    
        
    def find_lines(self) -> None:
        pass

    def write(self,s:str) -> None:
        pass

# this class reads fom a serial stream looking for "line" ends, which can be any string
# it also looks for asynchronous notifications, like "*** Connected"


class LineDelimitedSerialStream(SerialStream):
    def __init__(self,serial_port):
        super().__init__(serial_port)
        self.bytes_already_searched = 0
        self.line_end = b"cmd:"
        self.include_line_end_in_reply = True
        self._async_connected = b"*** CONNECTED"
        self._async_disconnected = b"*** DISCONNECTED\r\n"
        self._async_error = b"*** retry count exceeded\r\n"
        
    def write(self,s):
        if not (s and s[0] != '\r'):
            pass
        assert(s and s[0] != '\r') # no blank lines
        if self.serial_port:
            self.serial_port.write(s.encode(self.encoding))
        elif self.sock_out:
            self.sock_out.sendto(s.encode(self.encoding),(BSIM_ADDR,BSIM_PORT_OUT))
        if self.serial_port: # True:
            if self._log_file:
                tmp = s
                #tmp = tmp.replace('\r',"<cr>")
                #tmp = tmp.replace('\n',"<lf>")
                #tmp = "{"+tmp+"}"
                tmp = tmp.replace("\r","\r\n")
                tmp = tmp.replace("\x03","^c")
                self._log_file.write(b"\x1b[31m"+tmp.encode(self.encoding)+b"\x1b[0m")
                self._log_file.flush()

    def find_lines(self):
        done = False
        while not done:
            if self._async_connected:
                start = max(self.bytes_already_searched-len(self._async_connected)+1,0)
                if (p := self._sdata.find(self._async_connected,start)) >= 0:
                    global_signals.signal_connected.emit()
                    # extract
                    del self._sdata[p:p+len(self._async_connected)]
                    self.bytes_already_searched = min(p,self.bytes_already_searched)
            if self._async_disconnected:
                start = max(self.bytes_already_searched-len(self._async_disconnected)+1,0)
                if (p := self._sdata.find(self._async_disconnected,start)) >= 0:
                    global_signals.signal_disconnected.emit()
                    # extract
                    del self._sdata[p:p+len(self._async_disconnected)]
                    self.bytes_already_searched = min(p,self.bytes_already_searched)
            if self._async_error:
                start = max(self.bytes_already_searched-len(self._async_error)+1,0)
                if (p := self._sdata.find(self._async_error,start)) >= 0:
                    global_signals.signal_timeout.emit()
                    # extract
                    del self._sdata[p:p+len(self._async_error)]
                    self.bytes_already_searched = min(p,self.bytes_already_searched)
            assert(self.line_end)
            start = max(self.bytes_already_searched-len(self.line_end)+1,0)
            if (p := self._sdata.find(self.line_end,start)) >= 0:
                if self.include_line_end_in_reply:
                    global_signals.signal_line_read.emit(self._sdata[0:p+len(self.line_end)].decode(self.encoding))
                else:
                    global_signals.signal_line_read.emit(self._sdata[0:p].decode(self.encoding))
                # extract
                del self._sdata[0:p+len(self.line_end)]
                self.bytes_already_searched = 0
            else:
                self.bytes_already_searched = len(self._sdata)
                done = True

FEND =  0xc0
FESC =  0xdb
TFEND = 0xdc
TFESC = 0xdd

class KissSerialStream(SerialStream):
    signal_frame_read = Signal(ax25.Frame)
    def __init__(self,serial_port):
        super().__init__(serial_port)

    def write(self,b): # b is a complete KISS packet starting with the command byte which is generally 0
        # for c in b:
        #     print(f"{c:02x} ",end="")
        # print("")
        self.debug_display(b)
        tmp = KissSerialStream.kiss_encode_plus(b)
        if self.serial_port:
            self.serial_port.write(tmp)
        elif self.sock_out:
            self.sock_out.sendto(tmp,(BSIM_ADDR,BSIM_PORT_OUT))
        if self.serial_port: # True:
            if self._log_file:
                tmp = tmp
                self._log_file.write(tmp)
                self._log_file.flush()
        pass

    def find_lines(self):
        # need to find a start AND ending FEND
        while True:
            i0 = self._sdata.find(FEND)
            if i0 < 0:
                break
            i1 = self._sdata.find(FEND,i0+1)
            if i1 < 0:
                break
            if i1-i0 > 2:
                # skip first byte with seems to always be 0
                msg = KissSerialStream.kiss_decode(self._sdata[i0+2:i1])
                self.debug_display(msg)
                self.signal_frame_read.emit(msg)
                global_signals.signal_monitor_msg_ax25.emit(msg)
            self._sdata = self._sdata[i1:] # leave the last FEND in the buffer
        pass
    
    def debug_display(self,b:bytes):
        # if the first byte is a zero, (data packet for KISS), skip it
        if not b[0]:
            b = b[1:]
        # global_signals.signal_monitor_msg_ax25.emit(msg)
        frame = ax25.Frame.unpack(b)
        now = datetime.now()
        line = f"[{now.strftime("%H:%M:%S.%f")}] {frame.src.call}"
        if frame.src.ssid: line += f"-{frame.src.ssid}"
        line += f">{frame.dst.call}"
        if frame.dst.ssid: line += f"-{frame.dst.ssid}"
        #via = frame.via
        #if via:
        #    line += " via "
        #    line += " ".join([str(v) for v in via])
        control = frame.control
        ft = control.frame_type
        line += f":({ft.name}"
        if frame.dst.command_response and not frame.src.command_response: line += " cmd"
        elif not frame.dst.command_response and frame.src.command_response: line += " res"
        else: line += " !!!"
        if ft.is_I():
            line += f", n(s)={control.send_seqno}"
        if not ft.is_U():
            line += f", n(r)={control.recv_seqno}"
        line += f", p={1 if control.poll_final else 0}"
        if ft is ax25.FrameType.I or ft is ax25.FrameType.UI:
            line += f", pid={frame.pid:02X}, len={len(frame.data)}) {frame.data}"
        else:
            line += ")"
        print(line)

    @staticmethod
    def kiss_encode_plus(s:bytes) -> bytes: # "plus" because it adds the start/end markers
        r = bytearray()
        r.append(FEND)
        for c in s:
            if c == FEND:
                r.append(FESC)
                r.append(TFEND)
            elif c == FESC:
                r.append(FESC)
                r.append(TFESC)
            else:
                r.append(c)
        r.append(FEND)
        return r

    @staticmethod
    def kiss_decode(s:bytes) -> bytes:
        r = bytearray()
        flag = False
        for c in s:
            if flag:
                if c == TFESC:
                    r.append(FESC)
                elif c == TFEND:
                    r.append(FEND)
                flag = False;
            else:
                if c == FESC:
                    flag = True
                else:
                    r.append(c)
        return bytes(r)

