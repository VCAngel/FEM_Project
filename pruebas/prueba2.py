from PyQt5.QtGui import QPen, QColor, QBrush, QPolygonF, QFont, QRegExpValidator, QPainter

from PyQt5.QtCore import Qt, QPointF

from PyQt5 import QtGui, QtCore

from PyQt5.QtWidgets import QApplication, QMainWindow

import sys

class Window(QMainWindow):
    painter = QPainter()
    def __init__(self, parent=None):

        super().__init__()

        self.title = "PyQt5 Drawing Tutorial"

        self.top= 150

        self.left= 150

        self.width = 500

        self.height = 500

        self.InitWindow()

        self.points = QtGui.QPolygon()

    def InitWindow(self):

        self.setWindowTitle(self.title)

        self.setGeometry(self.top, self.left, self.width, self.height)

        self.show()

    def mousePressEvent(self, e):
        self.points << e.pos()
        self.update()

    def paintEvent(self, ev):
        qp = QtGui.QPainter(self)
        pen = QtGui.QPen(QtCore.Qt.red, 5)
        brush = QtGui.QBrush(QtCore.Qt.red)
        qp.setPen(pen)
        qp.setBrush(brush)
        for i in range(self.points.count()):
            qp.drawEllipse(self.points.point(i), 5, 5)

App = QApplication(sys.argv)

window = Window()

sys.exit(App.exec())