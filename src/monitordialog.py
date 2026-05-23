from datetime import datetime
import sys

from globalsignals import global_signals
from ui_monitordialog import Ui_MonitorDialogClass

import ax25
from PySide6 import QtWidgets
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QDialog, QInputDialog

class MonitorDialog(QDialog,Ui_MonitorDialogClass):
    def __init__(self,pd,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.setupUi(self)
        global_signals.signal_monitor_msg_ax25.connect(self.on_msg)
        self.c_text.setReadOnly(True)

    def resizeEvent(self,event):
        self.c_text.resize(event.size().width()-20,event.size().height()-20)
        return super().resizeEvent(event)

    def closeEvent(self, arg__1):
        global_signals.signal_end_send_receive.emit() # this will shut things down
        return super().closeEvent(arg__1)

    def on_msg(self,msg:bytes):
        try:
            frame = ax25.Frame.unpack(msg)
        except (ValueError, IndexError) as e:
            print("Error reading this header:",end=" ")
            for c in msg:
                print(f"{c:02x}",end=" ")
            print("\n")
            return
        now = datetime.now()
        line = f"[{now.strftime("%H:%M:%S.%f")}] {frame.src.call}"
        if frame.src.ssid: line += f"-{frame.src.ssid}"
        line += f">{frame.dst.call}"
        if frame.dst.ssid: line += f"-{frame.dst.ssid}"
        via = frame.via
        if via:
            line += " via "
            line += " ".join([str(v) for v in via])
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
        # handle APRS specially
        if ft is ax25.FrameType.UI and frame.data and frame.data[:1] in {b'!',b'=',b'@',b'/'}:
            symbol_table_id = " "
            symbol_code = " "
            tm = "000000z"
            lat = "0000.00N"
            lon = "00000.00W"
            spos = 1
            if frame.data[:1] == b'!' or frame.data[:1] == b'=':
                pass
            else: # frame.data[:1] == b'@' or frame.data[:1] == b'/':
                tm = frame.data[spos:spos+len(tm)]
                spos += len(tm)
            firstchar = ord(frame.data[spos:spos+1])
            if firstchar >= ord('0') and firstchar <= ord('9'): # digits means uncompressed
                lat = frame.data[spos:spos+len(lat)]
                spos += len(lat)
                symbol_table_id = frame.data[spos:spos+len(symbol_table_id)]
                spos += len(symbol_table_id)
                lon = frame.data[spos:spos+len(lon)]
                spos += len(lon)
                latf = int(lat[0:2]) + float(lat[2:7])/60.0
                if lat[7:8] == b'S':
                    latf = -latf
                lonf = int(lon[0:3]) + float(lon[3:8])/60.0
                if lon[8:9] == b'W':
                    lonf = -lonf
            else:
                symbol_table_id = frame.data[spos:spos+len(symbol_table_id)]
                spos += len(symbol_table_id)
                latf = 90.0 - self.base91_decode(frame.data[spos:spos+4])/380926
                spos += 4
                lonf = 180.0 + self.base91_decode(frame.data[spos:spos+4])/190463
                if lonf >= 180.0:
                    lonf = lonf - 360.0
                spos += 4
            line += f", loc={latf:.4f},{lonf:.4f}) {frame.data}"
        elif ft is ax25.FrameType.I or ft is ax25.FrameType.UI:
            line += f", pid={frame.pid:02X}, len={len(frame.data)}) {frame.data}"
        else:
            line += ")"
        vbar = self.c_text.verticalScrollBar()
        was_at_end = (vbar.value() == vbar.maximum())
        self.c_text.appendPlainText(line)
        if not was_at_end:
            vbar.setValue(vbar.maximum())
    
    @staticmethod
    def base91_decode(b:bytes) -> float:
        assert(len(b) == 4)
        return (b[0]-33)*91*91*91 + (b[1]-33)*91*91 + (b[2]-33)*91 + b[3]-33

    @staticmethod
    def base91_encode(i:int) -> bytes:
        b1,r = divmod(i,91*91*91)
        b2,r = divmod(r,91*91)
        b3,b4 = divmod(r,91)
        return bytes([b1+33,b2+33,b3+33,b4+33])