# pylint:  disable="line-too-long,missing-function-docstring,multiple-statements,no-name-in-module"

from datetime import datetime
import socket

from globalsignals import global_signals

import ax25
from PySide6.QtCore import QObject, Signal, QIODevice
from PySide6.QtNetwork import QUdpSocket

class SerialStream(QObject):
    def __init__(self,io_device:QIODevice):
        super().__init__()
        self.encoding = "utf-8"
        self._sdata = bytearray()
        self.io_device = io_device
        if isinstance(io_device,QUdpSocket):
            self.io_device.readyRead.connect(self.read_pending_datagrams)
            self._log_file = None
        else:
            self.io_device.readyRead.connect(self.on_device_read_ready)
            self._log_file = open("serial.log","ab")
            if self._log_file:
                self._log_file.write(b"\r\n--------\r\n")

    def reset(self) -> None:
        if self.io_device:
            if not isinstance(self.io_device,QUdpSocket): # they do not need to be closed
                self.io_device.close()
            self.io_device.readyRead.disconnect()
        self._sdata.clear()

    def on_device_read_ready(self) -> None:
        sdata = bytearray(self.io_device.readAll())
        if self._log_file:
            self._log_file.write(sdata)
            self._log_file.flush()
        self._sdata += sdata
        return self.find_lines()

    def read_pending_datagrams(self):
        while self.io_device.hasPendingDatagrams():
            datagram, host, port = self.io_device.readDatagram(self.io_device.pendingDatagramSize())
            self._sdata += datagram.data()
            return self.find_lines()        
        
    def find_lines(self) -> None:
        pass

    def write(self,s:str) -> None:
        pass

# this class reads fom a serial stream looking for "line" ends, which can be any string
# it also looks for asynchronous notifications, like "*** Connected"


class LineDelimitedSerialStream(SerialStream):
    def __init__(self,io_device:QIODevice):
        super().__init__(io_device)
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
        if isinstance(self.io_device,QUdpSocket):
            self.io_device.writeDatagram(s.encode(self.encoding),self.io_device.out_params[0],self.io_device.out_params[1])
        else:
            self.io_device.write(s.encode(self.encoding))
        if True:
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
    def __init__(self,io_device:QIODevice):
        super().__init__(io_device)

    def write(self,b): # b is a complete KISS packet starting with the command byte which is generally 0
        # for c in b:
        #     print(f"{c:02x} ",end="")
        # print("")
        self.debug_display(b)
        tmp = KissSerialStream.kiss_encode_plus(b)
        if isinstance(self.io_device,QUdpSocket):
            self.io_device.sendto(tmp,self.io_device.out_params)
        else:
            self.io_device.write(tmp)
        if True:
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

