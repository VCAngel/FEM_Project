import itertools
from functools import cmp_to_key

import sys
import PyQt5
import numpy as np
from PyQt5.QtCore import QPointF, QLineF, QRectF, QRegExp, Qt
from PyQt5.QtGui import QPen, QColor, QBrush, QPolygonF, QFont, QRegExpValidator
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QFileDialog, QGraphicsScene, \
    QGraphicsItem, QGraphicsPolygonItem, QToolButton, \
    QGraphicsEllipseItem, QLineEdit, QFormLayout, QGraphicsLineItem, QGraphicsTextItem, QGridLayout, QPushButton, QGraphicsItem, QGraphicsView


class Canvas(QWidget):
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
        self.firstPoint = None
        self.prevPoint = None
        self.currentPoly = None

        # Listas de seguimiento
        self.polyList = []
        self.edgeList = []
        self.holeList = []
        
        self.pointCoordList = np.zeros((1, 2))
        self.connectingRect = None
        self.connectingLine = None
        self.connectingLineList = []
        self.drawingPoly = QPolygonF()
        self.drawingPoints = []
        self.drawingPointsCoords = []
        self.drawingRect = QPolygonF()
        self.holeMode = False

        self.LUBlue = QColor(0, 0, 128)
        self.LUBronze = QColor(156, 97, 20)
        self.LUBronzeDark = QColor(146, 87, 10)

        self.mode = "Draw poly"

        self.setMouseTracking(True)

    def paint(self, painter, option, widget):
        painter.setOpacity(1)
        painter.fillRect(self.boundingRect(), Qt.white)

    def boundingRect(self):
        drawArea = QRectF(0, 0, 400, 400)
        return drawArea

    def mouseReleaseEvent(self, event):
        super(Canvas, self).mouseReleaseEvent(event)
        # If a point or polygon is selected releasing the mouse will de-select the object and add the
        # current coordinates back to the global coordinate list to update to the new position
        if self.mode == "Arrow":
            self.parentScene.clearSelection()

    def mouseDoubleClickEvent(self, event):
        if self.mode == "Arrow":
            super(Canvas, self).mouseDoubleClickEvent(event)
            # If in the surface view highlight the polygon to allow updating exact values of the corner points
            if self.parentScene.selectedItems():
                if isinstance(self.parentScene.selectedItems()[0], PyQt5.QtWidgets.QGraphicsPolygonItem):
                    index = 0
                    poly = self.parentScene.selectedItems()[0]

                    # Add a x- and y- editor for each point of the polygon
                    for point in self.polyToList(poly, "Global"):
                        validator = QRegExpValidator(QRegExp("\\-*\\d*\\.\\d+"))

                        print("x", point.x())
                        print("y", point.y())
                        labelX = QLineEdit(str(point.x()))
                        labelX.setValidator(validator)
                        labelY = QLineEdit(str(-point.y()))
                        labelY.setValidator(validator)
                        
                        index += 1

                    def update():
                            # Update the polygon with the new edited values
                            i = 0
                            for childItem in poly.childItems():
                                if isinstance(childItem, PyQt5.QtWidgets.QGraphicsEllipseItem):
                                    if childItem.localIndex == i:
                                        x = float(grid.itemAtPosition(i, 0).widget().text())
                                        y = -float(grid.itemAtPosition(i, 1).widget().text())
                                        circ = childItem
                                        self.moveNode(circ, poly, x, y)
                                        point = circ.scenePos()
                                        self.pointCoordList = np.append(self.pointCoordList,
                                                                          [[point.x(), point.y()]], axis=0)
                                        i += 1

    def mousePressEvent(self, e):
        x = e.pos().x()
        y = e.pos().y()

        if self.mode == "Arrow":
            if e.button() != 1:
                # Return if button clicked is any is any other than left mouse
                return
            super(Canvas, self).mousePressEvent(e)

        if self.mode == "Draw poly":
            if e.button() == 2:
                # If a polygon is being drawn, finish the polygon by clicking right mouse button. This will close the
                # polygon and remove the lines drawn as support to show the polygon and replace them with the actual
                # edges and points of the polygon
                if self.newPoly or self.currentPoly.__len__() <= 2:
                    pass
                else:

                    # Agregar poligono a lista
                    #self.polyList.append(self.currentPoly)

                    self.addPoly(self.currentPoly, holeMode=self.holeMode)
                    self.removeDrawingPoly()

                    # Resetear estado inicial
                    self.currentPoly = None
                    self.newPoly = True
                    self.firstPoint = None
                    self.prevPoint = None
            elif e.button() == 1:
                if self.newPoly:
                    # Inicializar nuevo poligono
                    self.currentPoly = QPolygonF()

                    point = self.parentScene.addEllipse(
                        x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)
                    self.firstPoint = QPointF(x, y)
                    self.prevPoint = QPointF(x, y)

                    # Pasar el punto inicial al Poligono a construir
                    self.currentPoly << self.firstPoint
                    self.newPoly = False

                    self.drawingPoints.append(point)
                    self.drawingPointsCoords.append([x, y])
                else:
                    point = self.parentScene.addEllipse(
                        x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)

                    line = self.parentScene.addLine(
                        QLineF(self.prevPoint, QPointF(x, y)), self.blackPen)

                    self.prevPoint = QPointF(x, y)

                    # Pasar el punto previo al Poligono a construir
                    self.currentPoly << self.prevPoint

                    self.connectingLineList.append(line)
                    self.drawingPoints.append(point)
                    self.drawingPointsCoords.append([x, y])

        if self.mode == "Draw rect":

            if self.newPoly:
                self.prevPoint = QPointF(x, y)
                self.newPoly = False
            elif self.prevPoint.x() == x or self.prevPoint.y() == y:
                pass  # Catch to avoid creating a rectangle where points overlap
            else:
                r = self.connectingRect.rect()
                x1 = r.x()
                x2 = r.x() + r.width()
                y1 = r.y()
                y2 = r.y() + r.height()
                self.drawingRect << QPointF(x1, y1)
                self.drawingRect << QPointF(x2, y1)
                self.drawingRect << QPointF(x2, y2)
                self.drawingRect << QPointF(x1, y2)

                self.addPoly(self.drawingRect, holeMode=self.holeMode)
                self.removeDrawingRect()

    def addPoly(self, polygon, holeMode):
        if holeMode:
            poly = self.parentScene.addPolygon(polygon, QPen(QColor(0, 0, 0, 0)), QBrush(QColor(255, 255, 255)))
            poly.setZValue(1)
            self.polyList.append(poly)
            self.holeList.append(poly)
        else:
            poly = self.parentScene.addPolygon(polygon, QPen(QColor(0, 0, 0, 0)), QBrush(QColor(0, 0, 0, 50)))
            self.polyList.append(poly)
        self.addPolyCorners(poly)
        self.addPolyEdges(poly)
        #poly.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        #poly.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        return poly

    def addPolyCorners(self, polyItem):
        poly = polyItem.polygon()

        for i in range(poly.size()):
            point = poly.at(i)
            p = self.parentScene.addEllipse(-4, -4, 8, 8, self.LUBronze, self.LUBronze)
            p.setZValue(2)  # Make sure corners always in front of polygon surfaces
            p.setParentItem(polyItem)
            p.__setattr__("localIndex", int(i))
            p.setPos(point.x(), point.y())
            #p.setFlag(QGraphicsItem.ItemIsSelectable)
            #p.setFlag(QGraphicsItem.ItemIsMovable)
            self.pointCoordList = np.append(self.pointCoordList, [[p.x(), p.y()]], axis=0)

    def addPolyEdges(self, polyItem):

        poly = polyItem.polygon()

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
            displayLine = self.parentScene.addLine(QLineF(p1, p2), QPen(self.LUBronze, 3))
            line.__setattr__("localIndex", index)
            line.setParentItem(polyItem)
            displayLine.setParentItem(line)
            self.edgeList.append(line)

    def removeDrawingPoly(self):
        self.currentPoly = QPolygonF()
        self.drawingPointsCoords = []

        for p in self.drawingPoints:
            p.setVisible(False)

        for line in self.connectingLineList:
            line.setVisible(False)

        if self.connectingLine:
            self.connectingLine.setVisible(False)

        self.connectingLine = None
        self.newPoly = True

    def removeDrawingRect(self):
        """Hide the supportive rectangle used when drawing"""
        self.drawingRect = QPolygonF()
        if self.connectingRect:
            self.connectingRect.setVisible(False)
        self.connectingRect = None
        self.newPoly = True
    
    def moveNode(self, circ, poly, newX, newY):
        # En teoria se utiliza para actualizar los puntos, las coodenadas de los puntos en las listas
        polyList = self.polyToList(poly,
                                      "Local")
        # Extrae las posicion de los puntos del poligono antes de mover el punto

        tempPoint = QGraphicsEllipseItem()
        tempPoint.setPos(newX, newY)
        if tempPoint.pos() in self.polyToList(poly, "Global"):
            return
        # No permite que se sobrepongan dos puntos en el mismo poligono

        index = polyList.index(circ.pos())  
        # Consigue el index del circulo seleccionado

        circ.setPos(newX - poly.scenePos().x(), newY - poly.scenePos().y())  
        # Mueve el circulo seleccionado

        polyList[index] = circ.pos()  
        # Actualiza las coordenadas del punto en la lista de poligonos

        poly.setPolygon(QPolygonF(polyList))  
        # Actualiza el poligono con la nueva lista

        # Hace loop a todos los bordes del poligono para determinar que dos lineas estan conectadas al punto que movimos
        # actualiza esos bordes con el nuevo punto
        # las lineas que lo se conectan con este punto son: la que tiene el mismo index que el punto y la que tiene el index-1
        # excepcion 1: cuando seleccionamos el index 0, en este caso utilizamos el ultimo borde indexandalo con un indice negativo
        # excepcion 2: cuando escogemos el borde con el index mayor, el ultimo inex esta indexado con un simbolo negativo
        # en este caso lo atrapamos con un if
        for item in poly.childItems():
            if isinstance(item, PyQt5.QtWidgets.QGraphicsLineItem):
                if circ.localIndex == 0:
                    if item.localIndex < 0:
                        line = item.line()
                        line.setP2(circ.pos())
                        item.setLine(line)
                        item.childItems()[0].setLine(line)
                        if item.childItems()[0].childItems():
                            text = item.childItems()[0].childItems()[0]
                            text.setPos((item.line().x1() + item.line().x2()) / 2,
                                        (item.line().y1() + item.line().y2()) / 2)
                if item.localIndex == circ.localIndex:
                    line = item.line()
                    line.setP2(circ.pos())
                    item.setLine(line)
                    item.childItems()[0].setLine(line)
                    if item.childItems()[0].childItems():
                        text = item.childItems()[0].childItems()[0]
                        text.setPos((item.line().x1() + item.line().x2()) / 2,
                                    (item.line().y1() + item.line().y2()) / 2)
                if item.localIndex == circ.localIndex + 1:
                    line = item.line()
                    line.setP1(circ.pos())
                    item.setLine(line)
                    item.childItems()[0].setLine(line)
                    if item.childItems()[0].childItems():
                        text = item.childItems()[0].childItems()[0]
                        text.setPos((item.line().x1() + item.line().x2()) / 2,
                                    (item.line().y1() + item.line().y2()) / 2)
                if circ.localIndex == poly.polygon().size() - 1:
                    if item.localIndex < 0:
                        line = item.line()
                        line.setP1(circ.pos())
                        item.setLine(line)
                        item.childItems()[0].setLine(line)
                        if item.childItems()[0].childItems():
                            text = item.childItems()[0].childItems()[0]
                            text.setPos((item.line().x1() + item.line().x2()) / 2,
                                        (item.line().y1() + item.line().y2()) / 2)

    def mouseMoveEvent(self, event):
        # Conseguimos las coordenadas X y Y del mouse cada vez que se mueve
        x = event.pos().x()
        y = event.pos().y() 
        
        if self.mode == "Draw poly":
            # Esto muestra la linea desde el punto anterior a la posicion del mouse
            if self.newPoly:
                pass  # No dibuja nada si el primer punto no ha sido dibujado
            else:

                # Si ya existe un punto hay dos casos:
                
                if self.connectingLine:
                    self.connectingLine.setLine(QLineF(self.prevPoint, QPointF(x, y)))
                    # Caso 1: si ya existe una linea, actualiza las coordenadas finales con la posicion del mouse
                else:
                    self.connectingLine = self.parentScene.addLine(QLineF(self.prevPoint, QPointF(x, y)))
                    # caso 2: si no hay una linea creada, crea una con el punto inicial en 
                    # slas coordenadas del punto anterior y la coordenada final 
                    # en la posicion del mouse.

        if self.mode == "Draw rect":
            # Muestra el rectangulo de ayuda desde el punto anterior hasta la posicion actual del mouse
            if self.newPoly:
                pass  # Si el primer punto no ha sido dibujado, no dibuja nada
            else:
                # Si el primer punto ya fue dibujado
                if self.connectingRect:
                    # Si existe un rectangulo lo actualiza con la posicion actual del mouse
                    if self.prevPoint.x() > x and self.prevPoint.y() > y:
                        self.connectingRect.setRect(QRectF(QPointF(x, y), self.prevPoint))
                    elif self.prevPoint.x() > x:
                        self.connectingRect.setRect(
                            QRectF(QPointF(x, self.prevPoint.y()), QPointF(self.prevPoint.x(), y)))
                    elif self.prevPoint.y() > y:
                        self.connectingRect.setRect(
                            QRectF(QPointF(self.prevPoint.x(), y), QPointF(x, self.prevPoint.y())))
                    else:
                        self.connectingRect.setRect(QRectF(self.prevPoint, QPointF(x, y)))
                else:
                    #Si no existe un rectangulo crea uno nuevo
                    self.connectingRect = self.parentScene.addRect(QRectF(self.prevPoint, QPointF(x, y)))

    def polyToList(self, poly, scope: str):
        # Extrae lo puntos de un QGraphicsPolygonItem o un QPolygonF y regresa una lista de todos los QPointF que contiene
        # si el scoope es global regresa las coordenadas de la escena, si no regresa las coordenadas locales
        innerList = []
        x = 0
        y = 0

        # Para que pueda manejar QGraphicsPolygonItem y QPolygonF como inputs
        if isinstance(poly, PyQt5.QtWidgets.QGraphicsPolygonItem):
            if scope == "Global":
                x = poly.x()
                y = poly.y()
            poly = poly.polygon()

        for i in range(poly.size()):
            innerList.append(QPointF(poly.at(i).x() + x, poly.at(i).y() + y))
        return innerList

    def enablePolygonSelect(self, enabled=True):
        # Cambia la etiqueta del poligono para que pueda ser seleccionado o no
        for poly in self.polyList:
            if isinstance(poly, QGraphicsPolygonItem):
                if enabled:
                    poly.setFlag(
                        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
                else:
                    poly.setFlag(
                        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_F5:
            self.mode = "Arrow"
            self.enablePolygonSelect()

        elif e.key() == Qt.Key_F6:
            self.mode = "Draw poly"
            self.enablePolygonSelect(False)
        elif e.key() == Qt.Key_F7:
            self.mode = "Draw rect"
            self.enablePolygonSelect(False)

        if e.key() == Qt.Key_F1:
            self.holeMode = True
        elif e.key() == Qt.Key_F2:
            self.holeMode = False
        
        if e.key() ==Qt.Key_F3:
            # Revisa si el algun poligono tiene otro poligono dentro o parcialmente dentro
           
            for poly in self.polyList:
                if self.polygonContainsOtherPolygon(poly):
                    pass
                else:
                    self.polyList.append(self.polyList.pop(self.polyList.index(poly)))

            for poly in self.polyList:
                if poly in self.holeList:
                    continue

                # Revisa si hay poligonos que se sobrepongan
                if self.polygonOverlapsOtherPolygon(poly):
                    print("overlaps")

                # Revisa si hay poligonos que se intersecten
                lines = []
                for item in poly.childItems():
                    if isinstance(item, QGraphicsLineItem):
                        lines.append(item)

                for a, b in itertools.combinations(lines, 2):
                    if a.collidesWithItem(b):
                        if a.line().p1() == b.line().p1() or a.line().p1() == b.line().p2():
                            pass
                        elif a.line().p2() == b.line().p1() or a.line().p2() == b.line().p2():
                            pass
                        else:
                            self.intersectionError()
                            return None

                # Revisa si hay agujeros en algun poligono
                for hole in self.polygonContainsHoles(poly):
                    print("Contiene hoyos")

                for innerPoly in self.polygonContainsOtherPolygon(poly):
                    print("Contiene otro poligono")
        print(self.mode)
        print(self.holeMode)

    def polygonContains(self, polyOuter, polyInner):
        # Revisa si un poligono interno esta totalmente contenido por un poligono exterior
        # resgresa una lista de boorleanos con los valores de todos los puntos en el triangulo interior que contiene
        # True si esta contenido False si no
        # los valores de los bordes no son contados como contenidos
        
        innerList = self.polyToList(polyInner, "Global")
        containList = []

        #Hace loop a todos los puntos en el poligono interior para ver si estan contenidos por el poligono exterior
        for point in innerList:
            # Los puntos estan definidos con coordenadas locales, los movemos para que ambos tengan las 
            # coordenadas locales del poligono exterior
            pX = point.x() - polyOuter.x()
            pY = point.y() - polyOuter.y()
            point.setX(pX)
            point.setY(pY)

            # Revisar si el poligono exterior contiene ninguno, alguno o todos los puntos
            if polyOuter.contains(point):
                trueContain = []
                
                # Revisar un area cuadrada alrededor del punto para ver si todo el cuadrado esta contenido, 
                # si no esta en un borde y no debe ser incluido
                for i, j in itertools.product(range(-1, 2), range(-1, 2)):
                    point.setX(pX + i)
                    point.setY(pY + j)
                    if polyOuter.contains(point):
                        trueContain.append(True)
                    else:
                        trueContain.append(False)

                # Lo agrega al containList si toda el area cuadrada esta dentro del poligono exterior
                if all(trueContain):
                    containList.append(True)
                else:
                    containList.append(False)
            else:
                containList.append(False)
        return containList

    def polygonContainsHoles(self, outerPoly):
        # Revisa si el poligono contiene un objeto de tipo hoyo, regresa una lista de los objetos tipo agujeros que estan contenidos
        containList = []
        for holePolygon in self.holeList:
            if all(self.polygonContains(outerPoly, holePolygon)):
                containList.append(holePolygon)
        return containList

    def polygonContainsOtherPolygon(self, outerPoly):
        # Revisa si el poligono contiene totalmente cualquier otro poligono, regresa una lista de los objetos de tipo poligono que 
        #estan contenidos
        containList = []
        for innerPoly in self.polyList:
            if outerPoly == innerPoly:
                pass
            elif all(self.polygonContains(outerPoly, innerPoly)):
                containList.append(innerPoly)
                print("contain")
        return containList

    def polygonOverlapsOtherPolygon(self, outerPoly):
        # Revisa si un poligono esta transpuest con algun otro poligono en la escena
        containList = []
        for innerPoly in self.polyList:
            if outerPoly == innerPoly:
                pass
            elif all(self.polygonContains(outerPoly, innerPoly)):
                pass
            elif any(self.polygonContains(outerPoly, innerPoly)):
                containList.append(innerPoly)
        return containList


class MainView(QGraphicsView):
    # * Window's Main View. The main camera per se
    def __init__(self):
        super(MainView, self).__init__()

        # Crear escena para los items dentro del View
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Agregar el componente Canvas a la escena
        self.canvas = Canvas(self)
        self.scene.addWidget(self.canvas)

    def mouseDoubleClickEvent(self, event):
        self.canvas.mouseDoubleClickEvent(event)
    def keyPressEvent(self, event):
        self.canvas.keyPressEvent(event)

class Window(QMainWindow):
    # * Main Application Window
    def __init__(self, screenSize=None):
        super(QMainWindow, self).__init__()
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