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
        self.holeMode = False

        self.LUBlue = QColor(0, 0, 128)
        self.LUBronze = QColor(156, 97, 20)
        self.LUBronze_dark = QColor(146, 87, 10)

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
                    for point in self.poly_to_list(poly, "Global"):
                        validator = QRegExpValidator(QRegExp("\\-*\\d*\\.\\d+"))

                        print("x", point.x())
                        print("y", point.y())
                        label_x = QLineEdit(str(point.x()))
                        label_x.setValidator(validator)
                        label_y = QLineEdit(str(-point.y()))
                        label_y.setValidator(validator)
                        
                        index += 1

                    def update():
                            # Update the polygon with the new edited values
                            i = 0
                            for child_item in poly.childItems():
                                if isinstance(child_item, PyQt5.QtWidgets.QGraphicsEllipseItem):
                                    if child_item.localIndex == i:
                                        x = float(grid.itemAtPosition(i, 0).widget().text())
                                        y = -float(grid.itemAtPosition(i, 1).widget().text())
                                        circ = child_item
                                        self.move_node(circ, poly, x, y)
                                        point = circ.scenePos()
                                        self.point_coord_list = np.append(self.point_coord_list,
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
                    self.add_poli(self.currentPoly, holeMode=self.holeMode)
                    self.remove_drawing_poly()

                    # Resetear estado inicial
                    self.currentPoly = None
                    self.newPoly = True
                    self.first_point = None
                    self.prev_point = None
                # print(self.holeList)
                # print(self.polyList)
            elif e.button() == 1:
                if self.newPoly:
                    # Inicializar nuevo poligono
                    self.currentPoly = QPolygonF()

                    point = self.parentScene.addEllipse(
                        x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)
                    self.first_point = QPointF(x, y)
                    self.prev_point = QPointF(x, y)

                    # Pasar el punto inicial al Poligono a construir
                    self.currentPoly << self.first_point
                    self.newPoly = False

                    self.drawing_points.append(point)
                    self.drawing_points_coords.append([x, y])
                else:
                    point = self.parentScene.addEllipse(
                        x - 3, y - 3, 6, 6, self.blackPen, self.greenBrush)

                    line = self.parentScene.addLine(
                        QLineF(self.prev_point, QPointF(x, y)), self.blackPen)

                    self.prev_point = QPointF(x, y)

                    # Pasar el punto previo al Poligono a construir
                    self.currentPoly << self.prev_point

                    self.connecting_line_list.append(line)
                    self.drawing_points.append(point)
                    self.drawing_points_coords.append([x, y])

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

                self.add_poli(self.drawing_rect, holeMode=self.holeMode)
                self.remove_drawing_rect()

    def add_poli(self, polygon, holeMode):
        if holeMode:
            poly = self.parentScene.addPolygon(polygon, QPen(QColor(0, 0, 0, 0)), QBrush(QColor(255, 255, 255)))
            poly.setZValue(1)
            self.polyList.append(poly)
            self.holeList.append(poly)
        else:
            poly = self.parentScene.addPolygon(polygon, QPen(QColor(0, 0, 0, 0)), QBrush(QColor(0, 0, 0, 50)))
            self.polyList.append(poly)
        self.add_poly_corners(poly)
        self.add_poly_edges(poly)
        #poly.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        #poly.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        return poly

    def add_poly_corners(self, poly_item):
        poly = poly_item.polygon()

        for i in range(poly.size()):
            point = poly.at(i)
            p = self.parentScene.addEllipse(-4, -4,
                                            8, 8, self.LUBronze, self.LUBronze)
            # Make sure corners always in front of polygon surfaces
            p.setZValue(2)
            p.setParentItem(poly_item)
            p.__setattr__("localIndex", int(i))
            p.setPos(point.x(), point.y())
            #p.setFlag(QGraphicsItem.ItemIsSelectable)
            #p.setFlag(QGraphicsItem.ItemIsMovable)
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
            display_line = self.parentScene.addLine(
                QLineF(p1, p2), QPen(self.LUBronze, 3))
            line.__setattr__("localIndex", index)
            line.setParentItem(poly_item)
            display_line.setParentItem(line)
            self.edgeList.append(line)

    def remove_drawing_poly(self):
        self.currentPoly = QPolygonF()
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

    def move_node(self, circ, poly, new_x, new_y):
        """
        Update the corner of a polygon when dragging a corner circle of the polygon
        """
        poly_list = self.poly_to_list(poly,
                                      "Local")  # Extract the position of the polygon points before moving the point

        temp_point = QGraphicsEllipseItem()
        temp_point.setPos(new_x, new_y)
        # Do not allow overlap of two points in same polygon
        if temp_point.pos() in self.poly_to_list(poly, "Global"):
            return

        # Get the selected circles index in the polygon
        index = poly_list.index(circ.pos())

        circ.setPos(new_x - poly.scenePos().x(), new_y -
                    poly.scenePos().y())  # Move the selected circle

        # Update the coords of the point in the polygon list
        poly_list[index] = circ.pos()
        # Update the polygon with the new list
        poly.setPolygon(QPolygonF(poly_list))

        # Loop through all the edges of the polygon to determine which two lines are connected to the moved point,
        # update these edges with the new point to match the movement,also move any edge labeltext connected to the edge
        # based on that we know that the connected lines are one with the same index as the corner point and one with
        # index-1
        # exception case 1:  when selecting corner with index 0, then we use that the last edge is indexed with a
        # negative sign
        # exception case 2: when selecting corner with highest index last edge is indexed with a negative sign,
        # catch this with a special if statement for the highest index
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
        # When moving the mouse in the graphicsScene display coords in label
        x = event.pos().x()
        y = event.pos().y() 
        
        if self.mode == "Draw poly":
            # This is to display the line in the polygon from the previous point to see where the new line would occur
            if self.newPoly:
                pass  # Don't draw if the first point has not been initiated
            else:
                # else if there is an existing line update that one with new x,y, if no line create a new one with
                # end point at x,y
                if self.connecting_line:
                    self.connecting_line.setLine(
                        QLineF(self.prev_point, QPointF(x, y)))
                else:
                    self.connecting_line = self.parentScene.addLine(
                        QLineF(self.prev_point, QPointF(x, y)))

        if self.mode == "Draw rect":
            # This is to display the rectangle from the previous point to see where the new rectangle would occur
            if self.newPoly:
                pass  # Don't draw if the first point has not been initiated
            else:
                # else if there is an existing rectangle update that one with new x,y, if no rectangle create a new one
                if self.connecting_rect:
                    if self.prev_point.x() > x and self.prev_point.y() > y:
                        self.connecting_rect.setRect(
                            QRectF(QPointF(x, y), self.prev_point))
                    elif self.prev_point.x() > x:
                        self.connecting_rect.setRect(
                            QRectF(QPointF(x, self.prev_point.y()), QPointF(self.prev_point.x(), y)))
                    elif self.prev_point.y() > y:
                        self.connecting_rect.setRect(
                            QRectF(QPointF(self.prev_point.x(), y), QPointF(x, self.prev_point.y())))
                    else:
                        self.connecting_rect.setRect(
                            QRectF(self.prev_point, QPointF(x, y)))
                else:
                    self.connecting_rect = self.parentScene.addRect(
                        QRectF(self.prev_point, QPointF(x, y)))

    def poly_to_list(self, poly, scope: str):
        """Extract the points from a QGraphicsPolygonItem or a QPolygonF and return a list of all the containing QPointF
        , scope to be chosen as Global return scene coordinates otherwise returns local coordinates """
        inner_list = []
        x = 0
        y = 0

        # To be able to handle input as both QGraphicsPolygonItem and QPolygonF
        if isinstance(poly, PyQt5.QtWidgets.QGraphicsPolygonItem):
            if scope == "Global":
                x = poly.x()
                y = poly.y()
            poly = poly.polygon()

        for i in range(poly.size()):
            inner_list.append(QPointF(poly.at(i).x() + x, poly.at(i).y() + y))
        return inner_list

    def enablePolygonSelect(self, enabled=True):
        # print(self.polyList)
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
            for poly in self.polyList:
                if self.polygon_contains_other_polygon(poly):
                    pass
                else:
                    self.polyList.append(self.polyList.pop(self.polyList.index(poly)))
            for poly in self.polyList:
                if poly in self.holeList:
                    continue

                # Check for polygons overlapping eachother and warn user if any
                if self.polygon_overlaps_other_polygon(poly):
                    print("overlaps")

                # Check if polygon intersects itself and warn user if true
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
                            self.intersection_error()
                            return None

                # Check if there are any holes inside the polygon
                for hole in self.polygon_contains_holes(poly):
                    return self.polygon_contains_holes

                for inner_poly in self.polygon_contains_other_polygon(poly):
                    return self.polygon_contains_other_polygon
        print(self.mode)
        print(self.holeMode)

    def polygon_contains(self, poly_outer, poly_inner):
        """
        Checks if a inner polygon is fully contained by a outer polygon, returns a list with boolean values of all
        points in the inner triangle which holds value true if contained and false else. Not that values on the border
        do not count as contained
        """
        inner_list = self.poly_to_list(poly_inner, "Global")
        contain_list = []
        # Loop over all points in the inner polygon to see if they are contained by the outer polygon
        for point in inner_list:
            # Points are defined in local coordinates, move them so they are both in the local coordinates
            # # of the outer polygon
            p_x = point.x() - poly_outer.x()
            p_y = point.y() - poly_outer.y()
            point.setX(p_x)
            point.setY(p_y)

            # Check if the outer polygon contains none, some, or all of the points
            if poly_outer.contains(point):
                true_contain = []
                # check a square area around the point to see if the whole square is contained, else the point
                # is on a edge and should not be included
                for i, j in itertools.product(range(-1, 2), range(-1, 2)):
                    point.setX(p_x + i)
                    point.setY(p_y + j)
                    if poly_outer.contains(point):
                        true_contain.append(True)
                    else:
                        true_contain.append(False)
                # Add to contain_list if the whole square area is inside the outer polygon
                if all(true_contain):
                    contain_list.append(True)
                else:
                    contain_list.append(False)
            else:
                contain_list.append(False)
        return contain_list

    def polygon_contains_holes(self, outer_poly):
        """Check if the polygon fully contains any hole object, return a list of the contained hole objects"""
        contain_list = []
        for hole_polygon in self.holeList:
            if all(self.polygon_contains(outer_poly, hole_polygon)):
                contain_list.append(hole_polygon)
                print("Agujeros")
        return contain_list

    def polygon_contains_other_polygon(self, outer_poly):
        """Check if the polygon fully contains any other polygon, return a list of the contained polygon objects"""
        contain_list = []
        for inner_poly in self.polyList:
            if outer_poly == inner_poly:
                pass
            elif all(self.polygon_contains(outer_poly, inner_poly)):
                contain_list.append(inner_poly)
                print("contain")
        return contain_list

    def polygon_overlaps_other_polygon(self, outer_poly):
        """ Check if a polygon overlaps any other polygon in the scene"""
        contain_list = []
        for inner_poly in self.polyList:
            if outer_poly == inner_poly:
                pass
            elif all(self.polygon_contains(outer_poly, inner_poly)):
                print("todo overlap")
            elif any(self.polygon_contains(outer_poly, inner_poly)):
                contain_list.append(inner_poly)
                print("Overlap otro poligono")
        return contain_list


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