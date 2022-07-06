from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsItem
from PyQt5.QtGui import QPen, QBrush
from PyQt5.Qt import Qt

import sys

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.title = "PyQt5 QGraphicView"
        self.top = 200
        self.left = 500
        self.width = 600
        self.height = 500


        self.InitWindow()


    def InitWindow(self):
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.createGraphicView()

        self.show()


    def createGraphicView(self):
        self.scene  = QGraphicsScene()
        self.greenBrush = QBrush(Qt.green)
        self.grayBrush = QBrush(Qt.gray)

        self.pen = QPen(Qt.red)

        graphicView = QGraphicsView(self.scene, self)
        graphicView.setGeometry(0,0,600,500)

App = QApplication(sys.argv)
window = Window()
sys.exit(App.exec())