import datetime
import re
import sys

from PySide6.QtCore import Qt, Signal, QObject, QRect, QPoint
from PySide6.QtWidgets import QMainWindow, QLineEdit, QWidget, QPlainTextEdit, QCheckBox, QRadioButton, QButtonGroup, QComboBox, QFrame
from PySide6.QtGui import QPixmap, QPalette, QColor, QFont, QPainter

from globalsignals import global_signals

from ui_formdialog import Ui_FormDialogClass

class PageController:
    def __init__(self,pages,scale):
        self.pages = []
        self.scale = scale
        for pn,s,e in pages:
            self.pages.append((pn,int(s*scale),int(e*scale)))
        pass

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
        if pageindex == 2:
            pageindex += 0
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
    def __init__(self,parent,form,f,dw=0,dh=0):
        super().__init__(parent)
        self.form = form
        self.widget = QWidget(parent)
        self.id = f[0]
        # f[1] is the type, which is implicit by the subclass
        self.dependson = f[2]
        self.validity_indicator = None
        self.page = 0
        # at least temporarily there is a "P" in front of the page number - ignore it if so
        f[3] = f[3].lstrip("P")
        self.page = int(f[3])-1 # 0-based 
        #if f[2] and f[2] != "Y":
        #    self.dependson = f[2]
        self.subjectlinesource = "Subject"
        self.group = -1 # gets set if part of a group
        # radio buttons and check boxes are never individually shown in red, just the groups that they are in
        # also, allg groups are never drawn, in that case the children are
        if len(f[2]) and f[4] != "0" and not (f[1] == "rb:" or f[1] == "cb" or f[1] == "allg"):
            self.validity_indicator = QFrame(parent)
            # expand the coordinates a litle
            e = 4
            x,y,w,h = self.form.page_controller.get_coordinates(self.page,f[4:8],dw,dh)
            x -= e
            y -= e
            w += 2*e
            h += 2*e
            self.validity_indicator.setGeometry(x,y,w,h)
            self.validity_indicator.setStyleSheet("QFrame { border: 6px solid #C02020;}")
            self.validity_indicator.setFrameStyle(QFrame.Shape.Box|QFrame.Shadow.Plain)
            self.validity_indicator.hide()

    def get_value(self): 
        pass

    def is_valid(self):
        return bool(self.get_value())
    
    def is_required(self) -> bool:
        if not self.dependson :
            return False
        # can be "always required"
        if self.dependson == "Y":
            return True
        # or conditionally required
        # can be a formula
        n,o,v = FormItem.partition_name_op_value(self.dependson)
        if o and v:
            if o == "==":
                return self.form.get_value_by_id(n) == v
            elif o == "!=":
                return self.form.get_value_by_id(n) != v
        else:
            if tmp := self.form.get_item_by_id(self.dependson):
                return tmp.should_dependent_be_red()
        
    def should_be_red(self) -> bool:
        # an item should be red if:
        # if has a red outline
        if self.validity_indicator:
            # it is required (permanently or conditionally) but it is blank
            if self.is_required() and not self.get_value():
                return True
            # it is not blank but it is invalid
            if self.get_value() and not self.is_valid():
                return True
        return False        

    # this returns True id an item depending on this item should turn red
    def should_dependent_be_red(self):
        return False

    def include_in_output(self):
        return True
    
    @staticmethod
    def partition_name_op_value(s:str):
        # the operator can only be "==" or "!=" (maybe allow "=")
        n,o,v = s.partition("==")
        if o and v:
            return (n.strip(),o,v.strip())
        n,o,v = s.partition("!=")
        if o and v:
            return (n.strip(),o,v.strip())
        n,o,v = s.partition("=")
        if o and v:
            return (n.strip(),"==",v.strip())
        return (n,"","")
    
   
class FormItemString(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,form,f):
        dw = 0 # default sizees
        dh = 26
        super().__init__(parent,form,f,dw,dh)
        self.widget = QLineEdit("",parent) # or f[1]
        x,y,w,h = self.form.page_controller.get_coordinates(self.page,f[4:8],dw,dh)
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

    def set_value(self,value):
        return self.widget.setText(value)
    
    def is_valid(self):
        s = self.get_value()
        return len(s) > 0

class FormItemDateString(FormItemString):
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)
        self.widget.setPlaceholderText("mm/dd/yyyy")

    def is_valid(self):
        s = self.get_value()
        try:
            datetime.datetime.strptime(s,"%m/%d/%Y")
            return True
        except ValueError:
            return False         

class FormItemTimeString(FormItemString):
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)
        self.widget.setPlaceholderText("hh:mm")

    def is_valid(self):
        s = self.get_value()
        if s and len(s) == 4 and s.isdigit():
            return True
        try:
            datetime.datetime.strptime(s,"%H:%M")
            return True
        except ValueError:
            return False         

class FormItemNumberString(FormItemString):
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)

    def is_valid(self):
        s = self.get_value()
        if not s or s.startswith("0"): return False
        return s.isdigit()

class FormItemPhoneString(FormItemString):
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)
        if self.validity_indicator:
            self.widget.setPlaceholderText("###-###-####")

    def is_valid(self):
        s = self.get_value()
        m = re.match(r'^(1\s?)?(\d{3}|\(\d{3}\))[\s\-]?\d{3}[\s\-]?\d{4}(\s?x\d+)?$',s)
        if m:
            return True
        else:
            return False

class FormItemEmailString(FormItemString):
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)

    def is_valid(self):
        s = self.get_value()
        m = re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',s)
        if m:
            return True
        else:
            return False

class FormItemZipString(FormItemString):
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)

    def is_valid(self):
        s = self.get_value()
        return s and len(s) == 5 and s.isdigit()

class FormItemMultiString(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)
        self.widget = QPlainTextEdit(parent)
        x,y,w,h = self.form.page_controller.get_coordinates(self.page,f[4:8])
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

    def set_value(self,value):
        return self.widget.setPlainText(value.replace("`]","]").replace("\\n","\n"))


class FormItemRadioButtons(FormItem): # always multiple buttons
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,form,f):
        # radio buttons (and checkboxes) use the coordinates of their center instead of the upper left
        # width and height are always shown as "0"
        dw = 64 # default size
        dh = 14
        super().__init__(parent,form,f,dw,dh)
        nb = (len(f)-8)//5
        self.widget = QButtonGroup(parent)
        self.values = []
        for i in range (nb):
            j = i*5+8
            tmpwidget = QRadioButton("                ",parent)
            x,y,_,_ = self.form.page_controller.get_coordinates(self.page,f[j+1:j+5],0,0)
            tmpwidget.setGeometry(x-7,y-dh/2,dw,dh) # the "7" is related to how QRadioButtons get rendered
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

    def set_value(self,value):
        for i, v in enumerate(self.values):
            if v == value:
                self.widget.button(i).setChecked(True)

    def should_dependent_be_red(self):
        tmp = self.get_value()
        if tmp and tmp != "No":
            return True
        return False

class FormItemCheckBox(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,form,f):
        # radio buttons (and checkboxes) use the coordinates of their center instead of the upper left
        # width and height are always shown as "0"
        dw = 64 # default size
        dh = 14
        super().__init__(parent,form,f,dw,dh)
        self.widget = QCheckBox("                ",parent) # or f[1]
        x,y,_,_ = self.form.page_controller.get_coordinates(self.page,f[4:8],0,0)
        self.widget.setGeometry(x-7,y-dh/2,dw,dh) # the "7" is related to how QCheckBoxs get rendered (left-justified)
        palette = self.widget.palette()
        palette.setColor(QPalette.ColorRole.Text,QColor("blue"))
        self.widget.setPalette(palette)
        self.widget.clicked.connect(lambda: self.signalValidityCheck.emit(self))

    def get_value(self):
        return "checked" if self.widget.isChecked() else ""

    def set_value(self,value):
        if value == "checked":
            value = True
        return self.widget.setChecked(value)


class FormItemDropDown(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,form,f):
        dw = 0 # default size
        dh = 26
        super().__init__(parent,form,f)
        self.widget = QComboBox(parent) # or f[1]
        x,y,w,h = self.form.page_controller.get_coordinates(self.page,f[4:8],dw,dh)
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

    def set_value(self,value):
        return self.widget.setCurrentText(value)


# this class returns valid if any child item is valid
class FormItemAnyGroup(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)
        self.children = []

    def is_valid(self):
        return not self.should_dependent_be_red()
    
    def should_be_red(self):
        return self.should_dependent_be_red()
    
    def should_dependent_be_red(self):
        for c in self.children:
            v = self.form.get_value_by_id(c)
            if v:
                return False
        return True

    def include_in_output(self): # these exist only for bookkeeping purposes
        return False
    

# this class returns valid if all child items are valid (or none)
class FormItemAllGroup(FormItem):
    signalValidityCheck = Signal(FormItem)
    def __init__(self,parent,form,f):
        super().__init__(parent,form,f)
        self.children = []

    def should_be_red(self):
        return False
    
    def should_dependent_be_red(self):
        all = True
        none = True
        for c in self.children:
            v = self.form.get_value_by_id(c)
            if v:
                none = False
            else:
                all = False
        return not (all or none)

    def include_in_output(self): # these exist only for bookkeeping purposes
        return False
    

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
        self.scale = 1.0
        section = 0 # 1 = headers, 2 = footers, 3 = fields, 4 = dependencies
        oldsection = -1
        try:
            with open(form,"rt") as file:
                while l := file.readline():
                    if comment := l.find("//") >= 0:
                        l = l[:comment]
                    l = l.strip()
                    if len(l) < 2: 
                        continue
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
                        self.compute_scale_and_fix_pages() # this needs to happen before the controls are placed
                        self.page_controller = PageController(self.pages,self.scale)
                        oldsection = -1
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
                                # someimes nl is -1, means the size of the image
                                # I used to do this computation elsewhere, but the immutable-ness of tuples was messing me up
                                if nl < 0:
                                    nl = QPixmap(m.group(1)).height() - l1
                                self.pages.append((m.group(1),l0,nl)) # specific lines
                        else:
                            nl = QPixmap(l).height()
                            self.pages.append((l,0,nl)) # all lines
                    elif section == 4:
                        f = l.split(",")
                        # typical line: 12.,mstr,Y,page,52,105,100,20
                        # fields:       0   1    2 3    4  5   6   7 
                        if len(f) >= 8:
                            # discard extraneous spaces
                            for i in range(len(f)):
                                f[i] = f[i].strip()
                            index = len(self.fields)
                            if f[0] and f[0][0] == '*':
                                f[0] = f[0][1:]
                                self.subjectlinesource = f[0]
                            if f[1] == "str":
                                self.fields.append(FormItemString(self.cForm,self,f))
                            elif f[1] == "dstr":
                                self.fields.append(FormItemDateString(self.cForm,self,f))
                            elif f[1] == "tstr":
                                self.fields.append(FormItemTimeString(self.cForm,self,f))
                            elif f[1] == "nstr":
                                self.fields.append(FormItemNumberString(self.cForm,self,f))
                            elif f[1] == "pstr":
                                self.fields.append(FormItemPhoneString(self.cForm,self,f))
                            elif f[1] == "estr":
                                self.fields.append(FormItemEmailString(self.cForm,self,f))
                            elif f[1] == "zstr":
                                self.fields.append(FormItemZipString(self.cForm,self,f))
                            elif f[1] == "mstr":
                                self.fields.append(FormItemMultiString(self.cForm,self,f))
                            elif f[1] == "rb":
                                self.fields.append(FormItemRadioButtons(self.cForm,self,f))
                            elif f[1] == "cb":
                                self.fields.append(FormItemCheckBox(self.cForm,self,f))
                            elif f[1] == "dd":
                                self.fields.append(FormItemDropDown(self.cForm,self,f))
                            elif f[1] == "anyg":
                                self.fields.append(FormItemAnyGroup(self.cForm,self,f))
                            elif f[1] == "allg":
                                self.fields.append(FormItemAllGroup(self.cForm,self,f))
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
            self.pages.append((self.form.replace("*.desc",".png"),0,-1))
        self.make_composite_picture()

        # set up any groups
        for index, f in enumerate(self.fields):
            if isinstance(f,FormItemAnyGroup) or isinstance(f,FormItemAllGroup):
                f.group = index
                for index2, f2 in enumerate(self.fields):
                    if FormItem.partition_name_op_value(f2.dependson)[0] == f.id:
                        f.children.append(f2.id)
                        f2.group = index

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
    
    def compute_scale_and_fix_pages(self):
        # all x/y/w/h values are in 100ths of an inch, which for 850x1100 images is the same as pixels
        # if the images are any other size, force them to be 850 wide, which will cause a scaling of the items in the "Pages" section (those are always pixels)
        self.scale = 1.0
        # temporarily read first one
        assert(self.pages)
        tmp = QPixmap(self.pages[0][0])
        w = tmp.width()
        self.scale = 850/w


    def make_composite_picture(self):
        # all x/y/w/h values are in 100ths of an inch, which for 850x1100 images is the same as pixels
        # if the images are any other size, force them to be 850 wide, which will cause a scaling of the items in the "Pages" section (those are always pixels)
        assert(self.pages)
        tmp = QPixmap(self.pages[0][0])
        w = tmp.width()
        scale = 850/w

        h = 0
        # pages is a tuple (filename,startline,numlines)
        for page in self.pages:
            h += page[2]*self.scale
        pm = QPixmap(850,h) # all pages *should* be 850x1100
        painter = QPainter(pm)
        y = 0
        for page in self.pages:
            pm2 = QPixmap(page[0])
            # painter.drawPixmap(QPoint(0,h),pm2,QRect(0,page[1],850,page[2]))
            painter.drawPixmap(QRect(0,y,850,page[2]*self.scale),pm2,QRect(0,page[1],w,page[2]))
            y += page[2]*self.scale
        painter.end()
        h = pm.height()
        w = pm.width()
        self.cForm.setPixmap(pm)
        self.scrollArea.setWidget(self.cForm)

    # if any item gets changed, we get here
    # it gets called as the "on_change" handler for all of the controls,
    # it gets called as part of updateAll, 
    # and it gets called recursively

    def updateSingle(self,f:FormItem):
        # if a member of a group has changed, redo all members of the group
        if f.group >= 0:
            for field in self.fields:
                if field.group == f.group:
                    if field.validity_indicator:
                        if field.should_be_red():
                            field.validity_indicator.show()
                        else:
                            field.validity_indicator.hide()
            return
        if f.validity_indicator:
            if f.should_be_red():
                f.validity_indicator.show()
            else:
                f.validity_indicator.hide()
        # even though this item is not required there might be something that depends on it and it needs to be redrawn
        for field in self.fields:
            if FormItem.partition_name_op_value(field.dependson)[0] == f.id:
                self.updateSingle(field)

    # this only gets called in __init__ and after pre-populating
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
            self.fields[self.fieldid[fname]].set_value(value)

    def get_value_by_id(self,fname):
        if fname in self.fieldid:
            return self.fields[self.fieldid[fname]].get_value()
        return ""

    def is_valid_by_id(self,fname):
        if fname in self.fieldid:
            return self.fields[self.fieldid[fname]].is_valid()
        return ""

    def onSend(self):
        # checkincheckout is completely different than any other
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
                if f.include_in_output():
                    v = f.get_value()
                    if v:
                        message += f"{f.id}: [{v}]\n"
            for f in self.footers:
                message += f + "\n"
            handling = self.get_value_by_id("5.")
            if not handling: handling = "?"
            subject = self.get_value_by_id("MsgNo") + "_" + handling[0] + "_" + self.formid + "_" + self.get_value_by_id(self.subjectlinesource) 
        global_signals.signal_new_outgoing_form_message.emit(subject,message,handling[0] == 'I',self.to_addr)
        self.close()
