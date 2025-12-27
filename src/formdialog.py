import datetime
import re
import sys

from PySide6.QtCore import Qt, Signal, QObject, QRect, QPoint
from PySide6.QtWidgets import QMainWindow, QLineEdit, QWidget, QPlainTextEdit, QCheckBox, QRadioButton, QButtonGroup, QComboBox, QFrame
from PySide6.QtGui import QPixmap, QPalette, QColor, QFont, QPainter

from globalsignals import global_signals

from ui_formdialog import Ui_FormDialogClass

class PageController:
    def __init__(self,pages):
        self.pages = pages

    def get_coordinates(self,page:int,f:list,dw=0,dh=0):
        x = int(f[0])
        y = self.page_to_screen(page,int(f[1]))
        w = int(f[2])
        if not w:
                w = dw
        h = int(f[3])
        if not h:
                h = dh
        return (x,y,w,h)

    def screen_to_page(self,y): # returns 0 for first page, 1 for second page, etc
        p = 0
        sumofpages = 0
        for page in self.pages:
            sumofpages += page[2]
        if y < 0 or y >= sumofpages:
            return (-1,0)
        for page in self.pages:
            if y < page[2]:
                return (p,y+page[1])
            p += 1
            y -= page[2]
        assert(False)
        return (p,y+page[1])

    def page_to_screen(self,pageindex,line) -> int: # returns -1 if not on any page
        line_offset = 0
        if 0 <= pageindex < len(self.pages):
            for p,page in enumerate(self.pages):
                if p == pageindex:
                    if line < page[1]:
                        return -1
                    line -= page[1]
                    if line >= page[2]:
                        return -1
                    return line + line_offset
                line_offset += page[2]
        else:
            return -1



class FormItem(QObject):
    def __init__(self,parent,pc:PageController,f,dw=0,dh=0):
        super().__init__(parent)
        self.parent = parent
        self.page_controller = pc
        self.widget = QWidget(parent)
        self.label = f[0]
        self.valid = None
        self.validator = ""
        self.dependson = ""
        self.page = 0
        # at least temporarily there is a "P" in front of the page number - ignore it if so
        f[3] = f[3].lstrip("P")
        self.page = int(f[3])-1 # 0-based 
        if len(f[1]) and f[1] != "Y":
            self.dependson = f[2]
        self.subjectlinesource = "Subject"
        self.group = -1 # gets set if part of a group
        if len(f[2]) and f[4] != "0":
        #if f[4] != "0": # this shows all of boxes that have been defined
            self.valid = QFrame(parent)
            # expand the coordinates a litle
            e = 4
            x,y,w,h = self.page_controller.get_coordinates(self.page,f[4:8],dw,dh)
            x -= e
            y -= e
            w += 2*e
            h += 2*e
            self.valid.setGeometry(x,y,w,h)
            self.valid.setStyleSheet("QFrame { border: 6px solid #C02020;}")
            self.valid.setFrameStyle(QFrame.Shape.Box|QFrame.Shadow.Plain)
            self.valid.hide()
        # determine validator
        self.validator = None
        v = {"dstr":"DateValid","tstr":"TimeValid","nstr":"NumValid","pstr":"PhoneValid","estr":"EmailValid","zstr":"ZipValid"}
        if f[1] in v:
            self.validator = v[f[1]]

    def get_value(self): pass

class FormItemString(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,pc:PageController,f):
        dw = 0 # default sizees
        dh = 26
        super().__init__(parent,pc,f,dw,dh)
        self.widget = QLineEdit("",parent) # or f[1]
        x,y,w,h = self.page_controller.get_coordinates(self.page,f[4:8],dw,dh)
        self.widget.setGeometry(x,y,w,h)
        font = QFont()
        #font =  self.cMailList.item(i,0).font()
        font.setBold(True)
        self.widget.setFont(font)
        palette = self.widget.palette()
        palette.setColor(QPalette.ColorRole.Text,QColor("blue"))
        self.widget.setPalette(palette)
        self.widget.textChanged.connect(lambda: self.signalValidityCheck.emit(self))

    def get_value(self):
        return self.widget.text()

    def setValue(self,value):
        return self.widget.setText(value)

class FormItemMultiString(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,pc:PageController,f):
        super().__init__(parent,pc,f)
        self.widget = QPlainTextEdit(parent)
        x,y,w,h = self.page_controller.get_coordinates(self.page,f[4:8])
        self.widget.setGeometry(x,y,w,h)
        self.widget.setPlainText("") # or f[1]
        font = QFont()
        font.setBold(True)
        self.widget.setFont(font)
        palette = self.widget.palette()
        palette.setColor(QPalette.ColorRole.Text,QColor("blue"))
        self.widget.setPalette(palette)
        self.widget.textChanged.connect(lambda: self.signalValidityCheck.emit(self))

    def get_value(self):
        return self.widget.toPlainText().replace("]","`]").replace("\n","\\n")

    def setValue(self,value):
        return self.widget.setPlainText(value.replace("`]","]").replace("\\n","\n"))

class FormItemRadioButtons(FormItem): # always multiple buttons
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,pc:PageController,f):
        dw = 64 # default size
        dh = 14
        super().__init__(parent,pc,f,dw,dh)
        nb = (len(f)-8)//5
        self.widget = QButtonGroup(parent)
        self.values = []
        for i in range (nb):
            j = i*5+8
            tmpwidget = QRadioButton("                ",parent)
            x,y,w,h = self.page_controller.get_coordinates(self.page,f[j+1:j+5],dw,dh)
            tmpwidget.setGeometry(x,y,w,h)
            self.widget.addButton(tmpwidget,i)
            palette = tmpwidget.palette()
            palette.setColor(QPalette.ColorRole.Text,QColor("blue"))
            tmpwidget.setPalette(palette)
            self.values.append(f[j])
        self.widget.idClicked.connect(lambda: self.signalValidityCheck.emit(self))

    def get_value(self):
        # this does not work when the initial seletion is made using setChecked
        for index, b in enumerate(self.widget.buttons()):
            if b.isChecked():
                return self.values[index]
        return ""
#        index = self.widget.checkedId()
#        if index < 0: return ""
#        return self.values[index]

    def setValue(self,value):
        for i, v in enumerate(self.values):
            if v == value:
                self.widget.button(i).setChecked(True)

class FormItemCheckBox(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,pc:PageController,f):
        dw = 64 # default size
        dh = 14
        super().__init__(parent,pc,f,dw,dh)
        self.widget = QCheckBox("                ",parent) # or f[1]
        x,y,w,h = self.page_controller.get_coordinates(self.page,f[4:8],dw,dh)
        self.widget.setGeometry(x,y,w,h)
        palette = self.widget.palette()
        palette.setColor(QPalette.ColorRole.Text,QColor("blue"))
        self.widget.setPalette(palette)
        self.widget.clicked.connect(lambda: self.signalValidityCheck.emit(self))
    def get_value(self):
        return "checked" if self.widget.isChecked() else ""
    def setValue(self,value):
        return self.widget.setChecked(value)

class FormItemDropDown(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,pc:PageController,f):
        dw = 0 # default size
        dh = 26
        super().__init__(parent,pc,f)
        self.widget = QComboBox(parent) # or f[1]
        x,y,w,h = self.page_controller.get_coordinates(self.page,f[4:8],dw,dh)
        self.widget.setGeometry(x,y,w,h)
        n = len(f)-8
        for i in range(n):
            self.widget.addItem(f[i+8])
        self.widget.setCurrentIndex(-1)
        self.widget.setEditable(True)
        palette = self.widget.palette()
        palette.setColor(QPalette.ColorRole.Text,QColor("blue"))
        self.widget.setPalette(palette)
        self.widget.currentTextChanged.connect(lambda: self.signalValidityCheck.emit(self))
    def get_value(self):
        return self.widget.currentText()
    def setValue(self,value):
        return self.widget.setCurrentText(value)

class FormItemRequiredGroup(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,pc:PageController,f):
        super().__init__(parent,pc,f)
        nc = (len(f)-8)
        self.children = []
        for i in range (nc):
            self.children.append(f[i+8])
        pass
    def get_value(self,dialog):
        for c in self.children:
            v = dialog.get_value_by_id(c)
            if v:
                return True
        return False
    def setValue(self,value):
        pass


class FormDialog(QMainWindow,Ui_FormDialogClass):
    def __init__(self,pd,form,formid,parent=None):
        super().__init__(parent)
        self.pd = pd
        self.form = form # the name of the desc and png files
        self.formid = formid # a short item used in the subject line
        self.to_addr = "" # this get used when redoing a form
        self.setupUi(self)
        self.pages = []
        self.page_controller = None
        self.headers = []
        self.footers = []
        self.fields = [] # a list of FormItem objects
        self.fieldid = {}  # a dictionary that maps the field id to the index
        #self.group = {}  # a dictionary that maps the field id to a container group, if there is one (rare)
        section = 0 # 1 = headers, 2 = footers, 3 = fields, 4 = dependencies
        try:
            with open(form,"rt") as file:
                while l := file.readline():
                    l = l.rstrip()
                    if len(l) < 2: continue
                    if l[0:2] == '//': continue
                    if l == "[Headers]":
                        oldsection = section
                        section = 1
                        continue
                    elif l == "[Footers]":
                        oldsection = section
                        section = 2
                        continue
                    elif l == "[Pages]":
                        oldsection = section
                        section = 3
                        continue
                    elif l == "[Fields]":
                        oldsection = section
                        section = 4
                        continue
                    elif l == "[Dependencies]": # this never happened
                        oldsection = section
                        section = 5
                        continue
                    if oldsection == 3 and section != 3: # we have finished the pages section
                        self.page_controller = PageController(self.pages)
                    if section == 1:
                        self.headers.append(l)
                    elif section == 2:
                        self.footers.append(l)
                    elif section == 3:
                        # format is filename[startline:endline], with the brackets stuff optional
                        b = l.find("[")
                        if b > 0:
                            m = re.match(r"([^[]+)\[(\d*):(\d*)\]",l)
                            if m:
                                l0 = int(m.group(2))
                                l1 = int(m.group(3))
                                nl = (l1-l0)+1
                                self.pages.append((m.group(1),l0,nl)) # specific lines
                        else:
                            self.pages.append((l,0,1100)) # all lines
                    elif section == 4:
                        f = l.split(",")
                        # typical line: 12.,mstr,Y,page,52,105,100,20
                        # fields:       0   1    2 3    4  5   6   7 
                        if len(f) >= 8:
                            index = len(self.fields)
                            if f[0] and f[0][0] == '*':
                                f[0] = f[0][1:]
                                self.subjectlinesource = f[0]
                            if f[1] == "str":
                                self.fields.append(FormItemString(self.cForm,self.page_controller,f))
                            elif f[1] == "mstr":
                                self.fields.append(FormItemMultiString(self.cForm,self.page_controller,f))
                            elif f[1][1:] == "str": # allows all sub-variants like "dstr" for date string
                                self.fields.append(FormItemString(self.cForm,self.page_controller,f))
                            elif f[1] == "rb":
                                self.fields.append(FormItemRadioButtons(self.cForm,self.page_controller,f))
                            elif f[1] == "cb":
                                self.fields.append(FormItemCheckBox(self.cForm,self.page_controller,f))
                            elif f[1] == "dd":
                                self.fields.append(FormItemDropDown(self.cForm,self.page_controller,f))
                            elif f[1] == "rg":
                                self.fields.append(FormItemRequiredGroup(self.cForm,self.page_controller,f))
                            if len(self.fields) > index: #something was added, add to dictionaries
                                if f[0]:
                                    self.fieldid[f[0]] = index
                                self.fields[index].signalValidityCheck.connect(self.updateSingle)

                    elif section == 5:
                        pass
        except FileNotFoundError:
            pass

        # if there were no pages specified, use default
        if not self.pages:
            self.pages.append((self.form.replace("*.desc",".png"),0,1100))
        self.make_composite_picture()

        # set up any groups
        for index, f in enumerate(self.fields):
            if isinstance(f,FormItemRequiredGroup):
                for c in f.children:
                    p = self.get_item_by_id(c)
                    if p:
                        p.group = index
        if self.pd: # formtool does not supply the persistent data object
            subject = self.pd.make_standard_subject() if self.pd else ""
            self.set_value_by_id("MsgNo",subject)
            # special handing for this non-conforming form
            if self.form == "CheckInCheckOut.desc":
                self.set_value_by_id ("UserCall",self.pd.getActiveUserCallSign())
                self.set_value_by_id("UserName",self.pd.getUserCallSign("Name"))
                self.set_value_by_id("TacticalCall",self.pd.getActiveTacticalCallSign())
                self.set_value_by_id("TacticalName",self.pd.getTacticalCallSign("Name"))
                self.set_value_by_id("UseTacticalCall",self.pd.getProfileBool("UseTacticalCallSign"))
            else:
                d = datetime.datetime.now()
                self.set_value_by_id("1a.","{:%m/%d/%Y}".format(d))
                self.set_value_by_id("1b.","{:%H:%M}".format(d))
                self.set_value_by_id("OpDate","{:%m/%d/%Y}".format(d)) # these will get overwritten
                self.set_value_by_id("OpTime","{:%H:%M}".format(d))
                self.set_value_by_id("OpCall",self.pd.getActiveUserCallSign())
                self.set_value_by_id("OpName",self.pd.getUserCallSign("Name"))
                self.set_value_by_id("Method","Other")
                self.set_value_by_id("Other","Packet")
            self.cSend.clicked.connect(self.onSend)
        self.updateAll()

    def resizeEvent(self,event):
        self.scrollArea.resize(event.size().width()-24,event.size().height()-56)
        return super().resizeEvent(event)
    
    def make_composite_picture(self):
        h = 0
        # pages is a tuple (filename,startline,numlines)
        for page in self.pages:
            h += page[2]
        pm = QPixmap(850,h) # all pages *should* be 850x1100
        painter = QPainter(pm)
        h = 0
        for page in self.pages:
            pm2 = QPixmap(page[0])
            painter.drawPixmap(QPoint(0,h),pm2,QRect(0,page[1],850,page[2]))
            h += page[2]
        painter.end()
        h = pm.height()
        w = pm.width()
        self.cForm.setPixmap(pm)
        self.scrollArea.setWidget(self.cForm)

    @staticmethod
    def DateValid(s):
        try:
            datetime.datetime.strptime(s,"%m/%d/%Y")
            return True
        except ValueError:
            return False         
    
    @staticmethod
    def TimeValid(s):
        if s and len(s) == 4 and s.isdigit():
            return True
        try:
            datetime.datetime.strptime(s,"%H:%M")
            return True
        except ValueError:
            return False         

    @staticmethod
    def PhoneValid(s):
        m = re.match(r'^(1\s?)?(\d{3}|\(\d{3}\))[\s\-]?\d{3}[\s\-]?\d{4}(\s?x\d+)?$',s)
        if m:
            return True
        else:
            return False

    @staticmethod
    def NumValid(s):
        if not s or s.startswith("0"): return False
        return s.isdigit()

    @staticmethod
    def ZipValid(s):
        return s and len(s) == 5 and s.isdigit()

    # if any item gets changed, we get here
    def updateSingle(self,f:FormItem):
        if (f.valid):
            # the next block of code decides if the data is valid
            # if it is, the frame will be hidden,
            # otherwise it will be shown, indicating that a valid entry is required
            # v changes types as it goes through the code but True/non-zero/non-empty string all mean "Valid"
            if isinstance(f,FormItemRequiredGroup):
                # these need additional help
                v = f.get_value(self)
            else:
                v = f.get_value().lstrip().rstrip()
            if f.validator and hasattr(self,f.validator):
                func = getattr(self,f.validator)
                if callable(func):
                    v = func(v)  # v is now a bool but that is all we need
            if not v and f.dependson:
                tmp = self.get_item_by_id(f.dependson)
                if (tmp):
                    tmpv = tmp.get_value()
                    if tmpv == "No":
                        tmpv = ""
                    v = not tmpv# add other non-values
            if v:
                f.valid.hide()
            else:
                f.valid.show()
        if f.group >= 0:
            self.updateSingle(self.fields[f.group])
        # even though this item is not required there might be something that depends on it
        for field in self.fields:
            if field.dependson == f.label:
                self.updateSingle(field)
        

    def updateAll(self):
        for f in self.fields:
            self.updateSingle(f)

    # this gets called when reading an existing form
    def prepopulate(self,h,m):
        self.to_addr = h.to_addr
        # we need to process the message, including multiline items
        lines = m.splitlines()
        value = ""
        # some lines at the start do not have "[" chars, ignore them"
        # watch out for lines breaks that have been added in
        for line in lines:
            if value: # we are in the middle of a multi-line item
                value += line
                if value[-1] != ']' or value[-2:] == "`]":
                    continue
                self.set_value_by_id(id,value[1:-1])
                value = ""
                continue
            id,_,r = line.partition(":")
            value = r.lstrip()
            if not value or value[0] != '[':
                value = ""
                continue
            if value[-1] == ']' and value[-2:] != "`]": 
                self.set_value_by_id(id,value[1:-1])
                value = ""
        self.updateAll()
        
    def get_item_by_id(self,fname) -> FormItem:
        if fname in self.fieldid:
            return self.fields[self.fieldid[fname]]
        return None

    def set_value_by_id(self,fname,value):
        if fname in self.fieldid:
            self.fields[self.fieldid[fname]].setValue(value)

    def get_value_by_id(self,fname):
        if fname in self.fieldid:
            return self.fields[self.fieldid[fname]].get_value()
        return ""

    def onSend(self):
        # checkincheckout is comepletely different than any other
        if self.form == "CheckInCheckOut.desc":
            handling = "R"
            line1 = self.get_value_by_id("Type") + " "
            line2 = ""
            usetactical = True if self.get_value_by_id("UseTacticalCall") else False
            if usetactical:
                line1 += self.get_value_by_id("TacticalCall") + ",  " + self.get_value_by_id("TacticalName")
                line2 = self.get_value_by_id("UserCall") + " , " + self.get_value_by_id("UserName")
                message = line1 + "\n" + line2 + "\n"
            else:
                line1 += self.get_value_by_id("UserCall") + " , " + self.get_value_by_id("UserName")
                message = line1 + "\n"

            subject = self.get_value_by_id("MsgNo") + "_" + handling[0] + "_" + line1
        else:
            message = ""
            for h in self.headers:
                message += h + "\n"
            for f in self.fields:
                if not isinstance(f,FormItemRequiredGroup):
                    v = f.get_value()
                    if v:
                        message += f"{f.label}: [{v}]\n"
            for f in self.footers:
                message += f + "\n"
            handling = self.get_value_by_id("5.")
            if not handling: handling = "?"
            subject = self.get_value_by_id("MsgNo") + "_" + handling[0] + "_" + self.formid + "_" + self.get_value_by_id(self.subjectlinesource) 
        global_signals.signal_new_outgoing_form_message.emit(subject,message,handling[0] == 'I',self.to_addr)
        self.close()
