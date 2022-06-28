from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QPushButton , QGraphicsView, QGraphicsItem
from PyQt5.QtGui import QBrush, QPen, QFont
from PyQt5.QtCore import Qt
import sys
from PyQt5.QtCore import QPointF, QLineF, QRectF, QRegExp
 
class Window(QMainWindow):
    def __init__(self):
        super().__init__()
 
        self.setWindowTitle("Pyside2 QGraphic View")
        self.setGeometry(300,200,640,520)
 
        self.scene = QGraphicsScene(self)

        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0,0,640, 440)
 
        
        self.greenBrush = QBrush(Qt.green)
        self.blueBrush = QBrush(Qt.blue)
 
        self.blackPen = QPen(Qt.black)
        self.blackPen.setWidth(5)
        self.first_draw = True
        self.show()
        

    def mousePressEvent(self, e):
        x = e.pos().x()
        y = e.pos().y()
        if e.button() == 2:
            # If a polygon is being drawn, finish the polygon by clicking right mouse button. This will close the
            # polygon and remove the lines drawn as support to show the polygon and replace them with the actual
            # edges and points of the polygon
            if self.first_draw:
                pass
            else:
                line = self.scene.addLine(QLineF(self.prev_point, self.first_point))
        elif e.button() == 1:
            if self.first_draw:
                point = self.scene.addEllipse(x - 3, y - 3, 6, 6)
                self.prev_point = QPointF(x, y)
                self.first_point = QPointF(x, y)
                self.first_draw = False
            else:
                point = self.scene.addEllipse(x - 3, y - 3, 6, 6)
                line = self.scene.addLine(QLineF(self.prev_point, QPointF(x, y)))
                self.prev_point = QPointF(x, y)
                
 
app = QApplication(sys.argv)
window = Window()
sys.exit(app.exec_())