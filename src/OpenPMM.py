import sys

from PySide6.QtWidgets import QApplication, QStyleFactory

from mainwindow import MainWindow

if __name__ == "__main__": 
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    darkmode = False
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-dark":
            darkmode = True
        # elif sys.argv[i] == "-x":
        #     i += 1
        #     z = int(sys.argv[i])
        i += 1
        
    # if darkmode: # the forms look vary bad in this mode
    #     p = QPalette()
    #     p.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    #     p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    #     p.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42)) # the color of QTableWidgets
    #     p.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
    #     p.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    #     p.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    #     p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    #     p.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    #     p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    #     p.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    #     p.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    #     p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    #     p.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
    #     app.setPalette(p)

    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec())
