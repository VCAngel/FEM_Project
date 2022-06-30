from tkinter import Y
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsItem, QWidget
from PyQt5.QtGui import QBrush, QPen, QPolygonF, QColor
from PyQt5.QtCore import Qt, QRectF, QPointF, QLineF
import sys
import numpy as np


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

        self.newPoly = True

        # Variables de seguimiento
        self.first_point = None
        self.prev_point = None
        self.currentPoly = None

        # Listas de seguimiento
        self.polyList = []
        self.edgeList = []
        self.holeList = []
        
        self.point_coord_list = np.zeros((1, 2))
        self.connecting_rect = None
        self.connecting_line = None
        self.connecting_line_list = []
        self.drawing_poly = QPolygonF()
        self.drawing_points = []
        self.drawing_points_coords = []
        self.drawing_rect = QPolygonF()

        self.LUBlue = QColor(0, 0, 128)
        self.LUBronze = QColor(156, 97, 20)
        self.LUBronze_dark = QColor(146, 87, 10)

        self.mode="Draw rect"
        

    def paint(self, painter, option, widget):
        painter.setOpacity(1)
        painter.fillRect(self.boundingRect(), Qt.white)

    def boundingRect(self):
        drawArea = QRectF(0, 0, 400, 400)
        return drawArea

    def mousePressEvent(self, e):
        x = e.pos().x()
        y = e.pos().y()

        if self.mode == "Draw poly":
            if e.button() == 2:
                # If a polygon is being drawn, finish the polygon by clicking right mouse button. This will close the
                # polygon and remove the lines drawn as support to show the polygon and replace them with the actual
                # edges and points of the polygon
                if self.newPoly or self.currentPoly.__len__() <= 2:
                    pass
                else:
                    self.parentScene.addLine(
                        QLineF(self.prev_point, self.first_point), self.blackPen)

                    # Agregar poligono a lista
                    self.polyList.append(self.currentPoly)

                    self.add_poli(self.currentPoly)
                    self.remove_drawing_poly()

                    # Resetear estado inicial
                    self.currentPoly = None
                    self.newPoly = True
                    self.first_point = None
                    self.prev_point = None
                    
            elif e.button() == 1:
                if self.newPoly:
                    # Inicializar nuevo poligono
                    self.currentPoly = QPolygonF()

                    self.parentScene.addEllipse(
                        x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)
                    self.first_point = QPointF(x, y)
                    self.prev_point = QPointF(x, y)

                    # Pasar el punto inicial al Poligono a construir
                    self.currentPoly << self.first_point
                    self.newPoly = False
                else:
                    self.parentScene.addEllipse(
                        x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)
                    self.parentScene.addLine(
                        QLineF(self.prev_point, QPointF(x, y)), self.blackPen)
                    self.prev_point = QPointF(x, y)

                    # Pasar el punto previo al Poligono a construir
                    self.currentPoly << self.prev_point

        if self.mode == "Draw rect":

            if self.newPoly:
                self.prev_point = QPointF(x, y)
                self.newPoly = False
            elif self.prev_point.x() == x or self.prev_point.y() == y:
                pass  # Catch to avoid creating a rectangle where points overlap
            else:
                r = self.connecting_rect.rect()
                x1 = r.x()
                x2 = r.x() + r.width()
                y1 = r.y()
                y2 = r.y() + r.height()
                self.drawing_rect << QPointF(x1, y1)
                self.drawing_rect << QPointF(x2, y1)
                self.drawing_rect << QPointF(x2, y2)
                self.drawing_rect << QPointF(x1, y2)

                self.add_poli(self.drawing_rect)
                self.remove_drawing_rect()


    def add_poli(self, polygon):
        poly = self.parentScene.addPolygon(polygon, QPen(QColor(0, 0, 0, 0)), QBrush(QColor(0, 0, 0, 50)))
        self.polyList.append(poly)
        self.add_poly_corners(poly)
        self.add_poly_edges(poly)
        poly.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        poly.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        return poly

    def add_poly_corners(self, poly_item):
        poly = poly_item.polygon()

        for i in range(poly.size()):
            point = poly.at(i)
            p = self.parentScene.addEllipse(-4, -4, 8, 8, self.LUBronze, self.LUBronze)
            p.setZValue(2)  # Make sure corners always in front of polygon surfaces
            p.setParentItem(poly_item)
            p.__setattr__("localIndex", int(i))
            p.setPos(point.x(), point.y())
            p.setFlag(QGraphicsItem.ItemIsSelectable)
            p.setFlag(QGraphicsItem.ItemIsMovable)
            self.point_coord_list = np.append(self.point_coord_list, [[p.x(), p.y()]], axis=0)

    def add_poly_edges(self, poly_item):

        poly = poly_item.polygon()

        for i in range(1, poly.size() + 1):
            if i == poly.size():
                p1 = poly.at(i - 1)
                p2 = poly.at(0)
                index = -poly.size()

            else:
                p1 = poly.at(i - 1)
                p2 = poly.at(i)
                index = i

            line = self.parentScene.addLine(QLineF(p1, p2))
            line.setZValue(-1)
            display_line = self.parentScene.addLine(QLineF(p1, p2), QPen(self.LUBronze, 3))
            line.__setattr__("localIndex", index)
            line.setParentItem(poly_item)
            display_line.setParentItem(line)
            self.edgeList.append(line)

    def remove_drawing_poly(self):
        self.drawing_poly = QPolygonF()
        self.drawing_points_coords = []

        for p in self.drawing_points:
            p.setVisible(False)

        for line in self.connecting_line_list:
            line.setVisible(False)
        if self.connecting_line:
            self.connecting_line.setVisible(False)
        self.connecting_line = None
        self.newPoly = True

    def remove_drawing_rect(self):
        """Hide the supportive rectangle used when drawing"""
        self.drawing_rect = QPolygonF()
        if self.connecting_rect:
            self.connecting_rect.setVisible(False)
        self.connecting_rect = None
        self.newPoly = True
    
    def mouseMoveEvent(self, event):
        # When moving the mouse in the graphicsScene display coords in label
        x = event.pos().x()
        y = event.pos().y() 
        print(x,y)
        if self.mode == "Draw poly":
            # This is to display the line in the polygon from the previous point to see where the new line would occur
            if self.newPoly:
                pass  # Don't draw if the first point has not been initiated
            else:
                # else if there is an existing line update that one with new x,y, if no line create a new one with
                # end point at x,y
                if self.connecting_line:
                    self.connecting_line.setLine(QLineF(self.prev_point, QPointF(x, y)))
                else:
                    self.connecting_line = self.parentScene.addLine(QLineF(self.prev_point, QPointF(x, y)))

        if self.mode == "Draw rect":
            # This is to display the rectangle from the previous point to see where the new rectangle would occur
            print("A")
            if self.newPoly:
                pass  # Don't draw if the first point has not been initiated
            else:
                # else if there is an existing rectangle update that one with new x,y, if no rectangle create a new one
                if self.connecting_rect:
                    if self.prev_point.x() > x and self.prev_point.y() > y:
                        self.connecting_rect.setRect(QRectF(QPointF(x, y), self.prev_point))
                    elif self.prev_point.x() > x:
                        self.connecting_rect.setRect(
                            QRectF(QPointF(x, self.prev_point.y()), QPointF(self.prev_point.x(), y)))
                    elif self.prev_point.y() > y:
                        self.connecting_rect.setRect(
                            QRectF(QPointF(self.prev_point.x(), y), QPointF(x, self.prev_point.y())))
                    else:
                        self.connecting_rect.setRect(QRectF(self.prev_point, QPointF(x, y)))
                else:
                    self.connecting_rect = self.parentScene.addRect(QRectF(self.prev_point, QPointF(x, y)))


class MainView(QGraphicsView):
    # * Window's Main View. The main camera per se
    def __init__(self):
        super(MainView, self).__init__()

        # Crear escena para los items dentro del View
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Agregar el componente Canvas a la escena
        self.canvas = Canvas(self)
        self.setMouseTracking(True)
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
