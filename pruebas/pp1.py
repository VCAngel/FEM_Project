from tkinter import Y
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt5.QtGui import QBrush, QPen
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
import sys


class Canvas(QGraphicsItem):
    # * Canvas Component. Controls Drawing
    def __init__(self, helper):
        super(Canvas, self).__init__()

        # Referencia a la escena padre. Permite acceder a las funciones de dibujo
        self.parentScene = helper.scene

        # Brushes y Pens
        self.greenBrush = QBrush(Qt.green)
        self.blackPen = QPen(Qt.black)
        self.blackPen.setWidth(5)

        self.firstDraw = True

        # Variables de seguimiento
        self.first_point = None
        self.prev_point = None

    def paint(self, painter, option, widget):
        painter.setOpacity(1)
        painter.fillRect(self.boundingRect(), Qt.white)

    def boundingRect(self):
        drawArea = QRectF(0,0,400,400)
        return drawArea

    def mousePressEvent(self, e):
        x = e.pos().x()
        y = e.pos().y()

        print(x,y)

        if e.button() == 2:
            # If a polygon is being drawn, finish the polygon by clicking right mouse button. This will close the
            # polygon and remove the lines drawn as support to show the polygon and replace them with the actual
            # edges and points of the polygon
            if self.firstDraw:
                pass
            else:
                self.parentScene.addLine(
                    QLineF(self.prev_point, self.first_point), self.blackPen)
        elif e.button() == 1:
            if self.firstDraw:
                self.parentScene.addEllipse(
                    x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)
                self.prev_point = QPointF(x, y)
                self.first_point = QPointF(x, y)
                self.firstDraw = False
            else:
                self.parentScene.addEllipse(
                    x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)
                self.parentScene.addLine(
                    QLineF(self.prev_point, QPointF(x, y)), self.blackPen)
                self.prev_point = QPointF(x, y)


class MainView(QGraphicsView):
    # * Window's Main View. The main camera per se
    def __init__(self):
        super(MainView, self).__init__()

        # Crear escena para los items dentro del View
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setMouseTracking = QGraphicsScene(self)

        # Agregar el componente Canvas a la escena
        self.canvas = Canvas(self)
        self.scene.addItem(self.canvas)


class Window(QMainWindow):
    # * Main Application Window
    def __init__(self, screenSize=None):
        super(Window, self).__init__()
        self.setWindowTitle("Pyside2 QGraphic View - Draw Test")

        self.view = MainView()
        self.setCentralWidget(self.view)

        # Centrar en pantalla
        if screenSize is not None:
            center = (screenSize.width()/2, screenSize.height()/2)
            self.setGeometry(int(center[0]), int(center[1]), 640, 480)
        else:
            self.setGeometry(0, 0, 640, 480)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    screen = app.primaryScreen()

    # Crear ventana
    window = Window(screen.size())
    # Mostrar ventana
    window.show()

    sys.exit(app.exec_())
