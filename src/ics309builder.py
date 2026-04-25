import sys

from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QDateTime, QDate, QTime, Signal
from PySide6.QtWidgets import QMainWindow
from persistentdata import PersistentData
from ui_ics309builder import Ui_Ics309Builder
from fpdf import FPDF

date_time_format = "MM-dd-yyyy HH:mm"

class Ics309Builder(QMainWindow,Ui_Ics309Builder):
    def __init__(self,pd:PersistentData,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.setupUi(self)
        self.tabWidget.setCurrentIndex(0)
        # these settings apepar to be global, not a part of the profile
        #self.c_date_time.setText(self.pd.settings.value("309Settings/OperationalPeriod",""))
        self.c_incident_name.setText(self.pd.settings.value("309Settings/IncidentName",""))
        self.c_activation_number.setText(self.pd.settings.value("309Settings/ActivationNumber",""))
        #self.c_operational_period_from.setText(self.pd.settings.value("309Settings/OperationalPeriodFrom",""))
        #self.c_operational_period_to.setText(self.pd.settings.value("309Settings/OperationalPeriodTo",""))
        tmp = self.pd.settings.value("309Settings/OperationalPeriodFrom","01/01/2026 12:00")
        dt = QDateTime.fromString(tmp,date_time_format)
        self.c_operational_period_from.setDateTime(dt)
        tmp = self.pd.settings.value("309Settings/OperationalPeriodTo","01/01/2026 12:00")
        dt = QDateTime.fromString(tmp,date_time_format)
        self.c_operational_period_to.setDateTime(dt)
        self.c_tactical_info.setText(self.pd.settings.value("309Settings/TacticalInfo",f"{self.pd.getTacticalCallSign("Name")} / {self.pd.getActiveTacticalCallSign()}"))
        self.c_user_info.setText(self.pd.settings.value("309Settings/UserInfo",f"{self.pd.getUserCallSign("Name")} / {self.pd.getActiveUserCallSign()}"))
        dt = QDateTime.currentDateTime()
        range = self.pd.settings.value("309Settings/Range",0)
        if range < 0 or range > 3:
            range = 0
        self.c_page1_today.setText(f"Today ({dt.toString("MM-dd-yyyy")})")
        self.c_page1_today.setChecked(range==0)
        self.c_page1_since_last.setChecked(range==1)
        self.c_page1_all.setChecked(range==2)
        self.c_page1_custom_range.setChecked(range==3)
        tmp = self.pd.settings.value("309Settings/CustomRangeFrom","01/01/2026 12:00")
        dt = QDateTime.fromString(tmp,date_time_format)
        self.c_page1_custom_range_from.setDateTime(dt)
        tmp = self.pd.settings.value("309Settings/CustomRangeTo","01/01/2026 12:00")
        dt = QDateTime.fromString(tmp,date_time_format)
        self.c_page1_custom_range_to.setDateTime(dt)
        
        self.c_build_data_set.clicked.connect(self.on_build_data_set)
        self.c_print.clicked.connect(self.on_print)
        self.actionExit.triggered.connect(self.on_exit)
        self.actionExit.triggered.connect(self.on_exit)
        self.c_exit.clicked.connect(self.on_exit)
        self.c_page1_today.clicked.connect(self.update_range)
        self.c_page1_since_last.clicked.connect(self.update_range)
        self.c_page1_all.clicked.connect(self.update_range)
        self.c_page1_custom_range.clicked.connect(self.update_range)
        self.c_reset_defaults.clicked.connect(self.reset_defaults)
        self.update_range()
        self.data = []

    def update_range(self):
        iscustom = self.c_page1_custom_range.isChecked()
        self.c_page1_custom_range_from.setEnabled(iscustom)
        self.c_page1_custom_range_to.setEnabled(iscustom)

    def reset_defaults(self):
        dt = QDateTime.currentDateTime()
        # maybe set times to 8am and 6pm or similar
        dt.setTime(QTime(8,0,0))
        self.c_operational_period_from.setDateTime(dt)
        dt.setTime(QTime(18,0,0))
        self.c_operational_period_to.setDateTime(dt)
        self.c_tactical_info.setText(f"{self.pd.getTacticalCallSign("Name")} / {self.pd.getActiveTacticalCallSign()}")
        self.c_user_info.setText(f"{self.pd.getUserCallSign("Name")} / {self.pd.getActiveUserCallSign()}")
        self.save()
    
    def save(self):
        self.pd.settings.setValue("309Settings/IncidentName",self.c_incident_name.text())
        self.pd.settings.setValue("309Settings/ActivationNumber",self.c_activation_number.text())
        self.pd.settings.setValue("309Settings/OperationalPeriodFrom",self.c_operational_period_from.dateTime().toString(date_time_format))
        self.pd.settings.setValue("309Settings/OperationalPeriodTo",self.c_operational_period_to.dateTime().toString(date_time_format))
        self.pd.settings.setValue("309Settings/TacticalInfo",self.c_tactical_info.text())
        self.pd.settings.setValue("309Settings/UserInfo",self.c_user_info.text())
        if self.c_page1_today.isChecked():
            self.pd.settings.setValue("309Settings/Range",0)
        elif self.c_page1_since_last.isChecked():
            self.pd.settings.setValue("309Settings/Range",1)
        elif self.c_page1_all.isChecked():
            self.pd.settings.setValue("309Settings/Range",2)
        elif self.c_page1_custom_range.isChecked():
            self.pd.settings.setValue("309Settings/Range",3)
        else:
            self.pd.settings.setValue("309Settings/Range",0)
        self.pd.settings.setValue("309Settings/CustomRangeFrom",self.c_page1_custom_range_from.dateTime().toString(date_time_format))
        self.pd.settings.setValue("309Settings/CustomRangeTo",self.c_page1_custom_range_to.dateTime().toString(date_time_format))

    def on_build_data_set(self):
        self.save()
        # compute the time range
        range = self.pd.settings.value("309Settings/Range",0)
        dt0 = QDateTime.currentDateTime()
        dt1 = QDateTime.currentDateTime()
        if range < 0 or range > 3:
            range = 0
        if range == 0: # today
            dt0.setTime(QTime(0,0)) # today from midnight to midnight
            dt1 = dt0.addDays(1)
        elif range == 1: # since last
            pass #!!! not ready
        elif range == 2: # all
            pass # just skips compare
        else:
            dt0 = QDateTime.fromString(self.pd.settings.value("309Settings/CustomRangeFrom",""),date_time_format)
            dt1 = QDateTime.fromString(self.pd.settings.value("309Settings/CustomRangeTo",""),date_time_format)
        self.data.clear()
        try:
            with open("activity.log","rt",encoding="windows-1252") as file:
                for line in file.readlines():
                    line = line.rstrip()
                    f = line.split(",",7)
                    if len(f) == 8:
                        dt = QDateTime.fromString(f[1],Qt.DateFormat.ISODate)
                        if range == 2 or (dt >= dt0 and dt < dt1):
                            self.data.append(f)
        except FileNotFoundError:
            pass

    def on_print(self):
        self.on_build_data_set() # in case caller did not do this
        # Create a PDF object
        # this is some work in progress
        pdf = f309(self.pd)
        for d in self.data:
            pdf.add_data(d)
        pdf.done()



    def on_exit(self):
        self.save()
        self.close()


class f309(FPDF):
    def __init__(self,pd:PersistentData):
        super().__init__("portrait","pt","Letter")
        self.pd = pd
        self.vlines = [35,90,148,211,269,337,463,575] # these are X values
        self.hlines = [36,80,113,129,146,163,650,699] # these are Y values
        self.vhlines = [134,310,341,448] # these are some extra X values for the header area
        self.data = []
        self.ndata_lines = 31
        self.spacing = (self.hlines[6]-self.hlines[5])/self.ndata_lines
        self.incidentname = self.pd.settings.value("309Settings/IncidentName","")
        self.activation = self.pd.settings.value("309Settings/ActivationNumber","")
        self.position_tac_call = self.pd.settings.value("309Settings/TacticalInfo",f"{self.pd.getTacticalCallSign("Name")} / {self.pd.getActiveTacticalCallSign()}")
        self.opname_user_call = self.pd.settings.value("309Settings/UserInfo",f"{self.pd.getUserCallSign("Name")} / {self.pd.getActiveUserCallSign()}")

    def add_data(self,s:list[str]):
        assert(len(s) == 8)
        self.data.append(s)

    def done(self):
        # resolve any LMI data
        for i in range(len(self.data)):
            if len(self.data[i]) == 8 and self.data[i][6] and self.data[i][7].startswith("DELIVERED: "):
                os = self.data[i][7][11:]
                for j in range(i):
                    if self.data[j][7] == os:
                        self.data[j][5] = self.data[i][6]
        np = (len(self.data)+self.ndata_lines-1)//(self.ndata_lines)
        if np <= 0:
            return
        for page in range(np):
            self.generate_blank_page(page+1,np)
            self.set_font("Arial",size=8)
            for i in range(self.ndata_lines):
                if page*self.ndata_lines+i >= len(self.data):
                    break
                v = self.data[page*self.ndata_lines+i]
                # only show the time part of the date/time
                self.set_xy(self.vlines[0],self.dline(i)+4)
                self.clipped_cell(self.vlines[1]-self.vlines[0],10,txt=f309.reformat_date_noyear(v[1]),align='L')
                #self.clipped_cell(self.vlines[1]-self.vlines[0],10,txt=v[1][11:16],align='L')
                # only show the from/to up to the "@"
                self.set_xy(self.vlines[1],self.dline(i)+4)
                self.clipped_cell(self.vlines[2]-self.vlines[1],10,txt=v[2].split("@")[0].upper(),align='L')
                self.set_xy(self.vlines[2],self.dline(i)+4)
                self.clipped_cell(self.vlines[3]-self.vlines[2],10,txt=v[3].upper(),align='L')
                self.set_xy(self.vlines[3],self.dline(i)+4)
                self.clipped_cell(self.vlines[4]-self.vlines[3],10,txt=v[4].split("@")[0].upper(),align='L')
                self.set_xy(self.vlines[4],self.dline(i)+4)
                self.clipped_cell(self.vlines[5]-self.vlines[4],10,txt=v[5].upper(),align='L')
                self.set_xy(self.vlines[5],self.dline(i)+4)
                self.clipped_cell(self.vlines[7]-self.vlines[5],10,txt=v[7],align='L')

        # Save the PDF
        self.output("hello_fpdf.pdf")
        print("FPDF file created!")

    @staticmethod
    def reformat_date(date:str) -> str:
        return f"{date[5:7]}/{date[8:10]}/{date[0:4]} {date[11:16]}" if date else "MM/DD/YYYY HH:MM"

    @staticmethod
    def reformat_date_noyear(date:str) -> str:
        return f"{date[5:7]}/{date[8:10]} {date[11:16]}" if date else "MM/DD HH:MM"

    def generate_blank_page(self,page:int,npages:int): # not quite blank, has headers and footers
        self.add_page()
        # find the date range
        date0 = ""
        date1 = ""
        for d in self.data:
            if len(d) >= 8: # if it is a normal entry
                if not date0 or d[1] < date0:
                    date0 = d[1]
                if not date1 or d[1] > date1:
                    date1 = d[1]
        # reformat dates to make usual American
        date0 = f309.reformat_date(date0)   
        date1 = f309.reformat_date(date1)   
        # now disregard all the work we just did and use operator-entered fields
        tmp = self.pd.settings.value("309Settings/OperationalPeriodFrom","01/01/2026 12:00")
        date0 = tmp # QDateTime.fromString(tmp,date_time_format)
        tmp = self.pd.settings.value("309Settings/OperationalPeriodTo","01/01/2026 12:00")
        date1 = tmp # QDateTime.fromString(tmp,date_time_format)


        # first, all the lines
        # drawing the thinner gray lines first looks better
        self.set_line_width(1)
        self.set_draw_color(128)
        for row in range(1,self.ndata_lines):
            self.hline(self.vlines[0],self.dline(row),self.vlines[-1])
        self.set_draw_color(0)
        # the 2X thick lines
        self.set_line_width(2)
        self.vline(self.vlines[0],self.hlines[0],self.hlines[-1]) # left edge
        self.vline(self.vlines[1],self.hlines[3]+1,self.hlines[-2]) # columns
        self.vline(self.vlines[3],self.hlines[3]+1,self.hlines[-1])
        self.vline(self.vlines[5],self.hlines[3]+1,self.hlines[-1])
        self.vline(self.vlines[6],self.hlines[6],self.hlines[-1]) # little stub at botton
        self.vline(self.vlines[7],self.hlines[0],self.hlines[-1]) # right edge
        self.hline(self.vlines[0],self.hlines[0],self.vlines[-1]) # top
        self.hline(self.vlines[1],self.hlines[4],self.vlines[5])
        self.hline(self.vlines[0],self.hlines[5],self.vlines[-1])
        self.hline(self.vlines[0],self.hlines[6],self.vlines[-1]) # bottom1
        self.hline(self.vlines[0],self.hlines[7],self.vlines[-1]) # bottom2
        # then 1X lines
        self.set_line_width(1)
        self.hline(self.vlines[0],self.hlines[1],self.vlines[-1])
        self.hline(self.vlines[0],self.hlines[2],self.vlines[-1])
        self.hline(self.vlines[0],self.hlines[3],self.vlines[-1])
        # some extra lines in the header
        self.vline(self.vhlines[0],self.hlines[0],self.hlines[1])
        self.vline(self.vhlines[1],self.hlines[1],self.hlines[2])
        self.vline(self.vhlines[2],self.hlines[0],self.hlines[1])
        # then dotted lines
        self.set_line_width(0.5)
        self.dashed_line(self.vlines[2],self.hlines[4],self.vlines[2],self.hlines[6],2,2)
        self.dashed_line(self.vlines[4],self.hlines[4],self.vlines[4],self.hlines[6],2,2)

        # now the text, ordered by size
        # first 14 point stuff
        self.set_font("Arial",style="B",size=14)  # Set font
        self.set_xy(self.vlines[0],self.hlines[0]+2)
        self.cell(self.vhlines[0]-self.vlines[0],14,txt="COMM Log",align='C')
        # ten 10 point stuff
        self.set_font("Arial",style="B",size=10)
        self.set_xy(self.vlines[0],self.hlines[0]+18)
        self.cell(self.vhlines[0]-self.vlines[0],10,txt="ICS 309-SCCo",align='C')
        self.set_xy(self.vlines[0],self.hlines[0]+30)
        self.cell(self.vhlines[0]-self.vlines[0],10,txt="ARES/RACES",align='C')
        self.set_xy(self.vlines[0],self.hlines[2]+2)
        self.cell(self.vlines[-1]-self.vhlines[0],12,txt="5.",align='L')
        self.set_xy(self.vlines[3],self.hlines[2]+2)
        self.cell(self.vlines[5]-self.vlines[3],12,txt="COMMUNICATIONS LOG",align='C')
        self.set_xy(self.vlines[1],self.hlines[3]+2)
        self.cell(self.vlines[3]-self.vlines[1],12,txt="FROM",align='C')
        self.set_xy(self.vlines[3],self.hlines[3]+2)
        self.cell(self.vlines[5]-self.vlines[3],12,txt="TO",align='C')
        self.set_xy(self.vlines[6],self.hlines[6]+18)
        self.cell(self.vlines[7]-self.vlines[6],10,txt=f"{page} of {npages}",align='C')
        # the header fields
        self.set_xy(self.vhlines[0]+2,self.hlines[0]+18)
        self.cell(self.vhlines[2]-self.vhlines[0],10,txt=self.incidentname,align='L')
        self.set_xy(self.vhlines[0]+2,self.hlines[0]+30)
        self.cell(self.vhlines[2]-self.vhlines[0],10,txt=self.activation,align='L')
        self.set_xy(self.vhlines[2]+2,self.hlines[0]+30)
        self.cell(self.vlines[-1]-self.vhlines[2],10,txt=f"From: {date0}   To: {date1}",align='L')
        
        self.set_xy(self.vlines[0]+2,self.hlines[1]+18)
        self.cell(self.vhlines[1]-self.vlines[0],10,txt=f"{self.position_tac_call}",align='L')
        self.set_xy(self.vhlines[1]+2,self.hlines[1]+18)
        self.cell(self.vlines[-1]-self.vhlines[2],10,txt=f"{self.opname_user_call}",align='L')

        # then 8 point stuff
        self.set_font("Arial",style="B",size=8)
        self.set_xy(self.vhlines[0],self.hlines[0]+2)
        self.cell(self.vhlines[2]-self.vhlines[0],10,txt="1. Incident Name and Activation Number",align='L')
        self.set_xy(self.vhlines[2],self.hlines[0]+2)
        self.cell(self.vlines[-1]-self.vhlines[2],10,txt="2. Operational Period (Date/Time)",align='L')
        self.set_xy(self.vlines[0],self.hlines[1]+2)
        self.cell(self.vhlines[1]-self.vlines[0],10,txt="3. Radio Net Name (for NCOs) or Position/Tactical Call",align='L')
        self.set_xy(self.vhlines[1],self.hlines[1]+2)
        self.cell(self.vlines[-1]-self.vhlines[1],10,txt="4. Radio Operator (Name/Call Sign)",align='L')
        self.set_xy(self.vlines[0],self.hlines[3]+6)
        self.multi_cell(self.vlines[1]-self.vlines[0],10,txt="Time\n(24:00)",align='C')
        self.set_xy(self.vlines[1],self.hlines[4]+4)
        self.cell(self.vlines[2]-self.vlines[1],10,txt="Call Sign/ID",align='C')
        self.set_xy(self.vlines[2],self.hlines[4]+4)
        self.cell(self.vlines[3]-self.vlines[2],10,txt="Msg #",align='C')
        self.set_xy(self.vlines[3],self.hlines[4]+4)
        self.cell(self.vlines[4]-self.vlines[3],10,txt="Call Sign/ID",align='C')
        self.set_xy(self.vlines[4],self.hlines[4]+4)
        self.cell(self.vlines[5]-self.vlines[4],10,txt="Msg #",align='C')
        self.set_xy(self.vlines[5],self.hlines[3]+12)
        self.cell(self.vlines[-1]-self.vlines[5],10,txt="Message",align='L')
        self.set_xy(self.vlines[0],self.hlines[6]+2)
        self.cell(self.vlines[3]-self.vlines[0],10,txt="6. Prepared By (Name, Call Sign)",align='L')
        self.set_xy(self.vlines[3],self.hlines[6]+2)
        self.cell(self.vlines[4]-self.vlines[3],10,txt="6A. Signature",align='L')
        self.set_xy(self.vlines[5],self.hlines[6]+2)
        self.cell(self.vlines[6]-self.vlines[5],10,txt="7. Date & Time Prepared",align='L')
        self.set_xy(self.vlines[6],self.hlines[6]+2)
        self.cell(self.vlines[7]-self.vlines[6],10,txt="8. Page",align='L')

    def clipped_cell(self, w,h=0,txt='',border=0,ln=0,align='',fill=0,link=''):
        margin = 4
        if self.get_string_width(txt)+margin < w:
            self.cell(w,h,txt,border,ln,align,fill,link)
        else:
            e = "..."
            ew = self.get_string_width(e)
            while txt and self.get_string_width(txt)+ew+margin >= w:
                txt = txt[:-1]
            self.cell(w,h,txt+e,border,ln,align,fill,link)


# Create PDF        pass
    def dline(self,row:int):
        return self.hlines[5]+row*self.spacing

    def hline(self,x0,y,x1):
        self.line(x0,y,x1,y)

    def vline(self,x,y0,y1):
        self.line(x,y0,x,y1)

