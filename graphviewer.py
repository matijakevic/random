from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from itertools import combinations
from random import randint, choices
from math import *
from collections import defaultdict


class Body:
    def __init__(self):
        self.mass = 1
        self.velocity = QVector2D()
        self.position = QVector2D()
        self.force = QVector2D()
        self.dragged = False


R = 50


def simulate(bodies, conns, dt):
    for b in bodies.values():
        b.force = QVector2D()

    for b1n, b2n in combinations(bodies.keys(), 2):
        b1 = bodies[b1n]
        b2 = bodies[b2n]
        r = b2.position - b1.position
        rn = r.normalized()
        rm = r.length()
        if b1n in conns and b2n in conns[b1n]:
            C = R / 2
        else:
            C = R
        C *= len(bodies)
        k = rm / C - 1
        f = rn * k
        b1.force += f
        b2.force += -f

    for b in bodies.values():
        if not b.dragged:
            b.velocity = b.force / b.mass * dt
            b.position += b.velocity * dt


class Painter(QWidget):
    def __init__(self):
        super().__init__()
        self.bodies = dict()
        self.conns = defaultdict(set)
        self.setMinimumSize(640, 480)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.dragging = None

        t = QTimer(self)

        def sim():
            simulate(self.bodies, self.conns, 1)

        t.timeout.connect(sim)
        # TODO: Stop the timer when the solution is stable
        t.start()

        t2 = QTimer(self)
        t2.timeout.connect(self.update)
        t2.start(1000//60)

    def rebuild_graph(self, n, complete):
        self.bodies.clear()
        self.conns.clear()
        for i in range(n):
            b = Body()
            b.position = QVector2D(
                randint(0, self.width()), randint(0, self.height()))
            self.bodies[str(i + 1)] = b

        combs = list(combinations(self.bodies, 2))
        if not complete:
            l = choices(combs, k=len(self.bodies))
        else:
            l = combs
        for b1, b2 in l:
            self.conns[b1].add(b2)
            self.conns[b2].add(b1)

    def pick_node(self, pos):
        for bname, b in self.bodies.items():
            if QRect(b.position.x(), b.position.y(), 20, 20).contains(pos):
                return bname
        return None

    def mousePressEvent(self, e):
        self.dragging = self.pick_node(e.pos())
        if self.dragging is not None:
            self.bodies[self.dragging].dragged = True

    def mouseMoveEvent(self, e):
        if self.dragging is not None:
            b = self.bodies[self.dragging]
            b.position = QVector2D(e.x(), e.y())

    def mouseReleaseEvent(self, *args):
        if self.dragging is not None:
            self.bodies[self.dragging].dragged = False
        self.dragging = None

    def paintEvent(self, *args):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0, 80)))
        for b1n in self.conns:
            for b2n in self.conns[b1n]:
                b1 = self.bodies[b1n]
                b2 = self.bodies[b2n]
                painter.drawLine(b1.position.x() + 10, b1.position.y() + 10,
                                 b2.position.x() + 10, b2.position.y() + 10)
        for bname, b in self.bodies.items():
            painter.setPen(QPen(Qt.black))
            painter.setBrush(Qt.black)
            painter.drawEllipse(b.position.x(), b.position.y(), 20, 20)
            painter.setPen(QPen(Qt.white))
            painter.drawText(b.position.x(), b.position.y(),
                             20, 20, Qt.AlignCenter, bname)


if __name__ == '__main__':
    app = QApplication()
    w = QWidget()
    l = QVBoxLayout()
    w.setLayout(l)
    p = Painter()

    l2 = QFormLayout()
    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(5)
    slider.setMaximum(100)
    slider.setValue(R)

    def on_value_changed(val):
        global R
        R = val

    slider.valueChanged.connect(on_value_changed)

    chk = QCheckBox()
    chk.toggle()

    btn = QPushButton('Rebuild')
    btn.clicked.connect(lambda: p.rebuild_graph(inp.value(), chk.isChecked()))

    inp = QSpinBox()
    inp.setMinimum(0)
    inp.setMaximum(50)
    inp.setValue(8)

    l2.addRow('Number of nodes', inp)
    l2.addRow('Spread factor:', slider)
    l2.addRow('Complete graph', chk)
    l2.addRow(btn)
    l.addLayout(l2)
    l.addWidget(p)

    p.rebuild_graph(inp.value(), chk.isChecked())

    w.show()

    app.exec_()
