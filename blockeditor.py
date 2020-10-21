from typing import List
from PySide2.QtCore import QPoint, QLine, QRect, Qt
from PySide2.QtWidgets import QWidget, QApplication
from PySide2.QtGui import QPainter, QPainterPath, QPen
from collections import defaultdict
from sortedcontainers import SortedSet
from collections import deque
from random import randint
import time


def generate_graph(blocks, points):
    vertical = SortedSet(key=lambda it: it[0])
    horizontal = SortedSet(key=lambda it: it[0])
    graph = defaultdict(set)

    for block in blocks:
        vertical.add((block.left(), block))
        vertical.add((block.right(), block))
        horizontal.add((block.top(), block))
        horizontal.add((block.bottom(), block))

    for point in points:
        vertical.add((point.x(), None))
        horizontal.add((point.y(), None))

    for y, _ in horizontal:
        open = set()
        prev = None
        for x, block in vertical:
            if prev is not None and not open:
                graph[(x, y)].add(prev)
                graph[prev].add((x, y))
            if block is not None and block.bottom() > y > block.top():
                if block not in open:
                    open.add(block)
                else:
                    open.remove(block)
            prev = (x, y)

    for x, _ in vertical:
        open = set()
        prev = None
        for y, block in horizontal:
            if prev is not None and not open:
                graph[(x, y)].add(prev)
                graph[prev].add((x, y))
            if block is not None and block.right() > x > block.left():
                if block not in open:
                    open.add(block)
                else:
                    open.remove(block)
            prev = (x, y)

    return graph


def find_path(graph, start, end):
    def dist(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def heuristic(p):
        return dist(p, end)

    start = (start.x(), start.y())  
    end = (end.x(), end.y())
    data = dict()
    q = SortedSet(key=lambda it: -sum(data[it]))
    # cost, heuristic
    data[start] = (0, heuristic(start))
    q.add(start)
    back = dict()
    back[start] = start
    found = False
    while q:
        curr = q.pop()
        c, h = data[curr]
        prev = back[curr]
        dx = curr[0] - prev[0]
        dy = curr[1] - prev[1]
        if curr == end:
            found = True
            break
        for next in graph.get(curr, tuple()):
            if not (dx == 0 and next[0] - curr[0] == 0 or
                dy == 0 and next[1] - curr[1] == 0):
                np = 1e20
            else:
                np = 0
            if next in data:
                if c + dist(curr, next) + np < data[next][0]:
                    q.discard(next)
                    data[next] = (c + dist(curr, next) + np, heuristic(next))
                    back[next] = curr
                    q.add(next)
            else:
                back[next] = curr
                data[next] = (c + dist(curr, next) + np, heuristic(next))
                q.add(next)

    if found:
        path = [end]
        while path[-1] != start:
            path.append(back[path[-1]])

        return list(reversed(path))
    return list()


class BlockEditor(QWidget):
    def __init__(self):
        super().__init__()

        self._dragging = None
        self._drag_point = None
        self.debug = False

        self.start_point = QPoint()
        self.end_point = QPoint()

        self._path = list()

        self.blocks = list()
        for _ in range(10):
            x = randint(0, self.width())
            y = randint(0, self.height())
            w = randint(50, 100)
            h = randint(50, 100)
            r = QRect(x, y, w, h)
            self.blocks.append(r)

        self._generate_graph()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_D:
            self.debug = not self.debug
            self.update()

    def _generate_graph(self):
        self.graph = generate_graph(
            self.blocks, (self.start_point, self.end_point))
        self.path = find_path(self.graph, self.start_point, self.end_point)

    def mousePressEvent(self, e):
        for block in self.blocks:
            if block.contains(e.pos()):
                self._dragging = block
                self._drag_point = block.topLeft() - e.pos()
        if self._dragging is None:
            if e.button() == Qt.MouseButton.LeftButton:
                self.start_point = e.pos()
            elif e.button() == Qt.MouseButton.RightButton:
                self.end_point = e.pos()
            self._generate_graph()
            self.update()

    def mouseMoveEvent(self, e):
        if self._dragging:
            self._dragging.moveTopLeft(e.pos() + self._drag_point)
            self._generate_graph()
            self.update()

    def mouseReleaseEvent(self, e):
        self._dragging = None

    def paintEvent(self, *args):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(Qt.black)
        painter.setPen(QPen(Qt.transparent))
        for block in self.blocks:
            painter.drawRect(block)

        if self.debug:
            lines = list()
            points = list()
            for p1 in self.graph:
                for p2 in self.graph[p1]:
                    lines.append(QLine(*p1, *p2))
                    points.append(QPoint(*p1))
                    points.append(QPoint(*p2))

            painter.setPen(QPen(Qt.black))
            painter.drawLines(lines)
            painter.setPen(QPen(Qt.red, 3))
            painter.drawPoints(points)

        if self.path:
            painter.setPen(QPen(Qt.green))
            painter.setBrush(Qt.transparent)
            p = QPainterPath()
            p.moveTo(*self.path[0])
            for point in self.path:
                p.lineTo(*point)
            painter.drawPath(p)


if __name__ == '__main__':
    app = QApplication()

    ed = BlockEditor()
    ed.show()

    app.exec_()
