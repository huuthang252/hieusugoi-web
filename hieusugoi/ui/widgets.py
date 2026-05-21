from PyQt5 import QtWidgets, QtGui


class MenuButton(QtWidgets.QPushButton):
    def paintEvent(self, event):
        super().paintEvent(event)

        # Icon mode: Qt renders the icon via super(); skip hamburger lines.
        if not self.icon().isNull():
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        pen = QtGui.QPen(QtGui.QColor("#333333"))
        pen.setWidth(1)
        painter.setPen(pen)

        w = self.width()
        h = self.height()

        x1 = int(w * 0.28)
        x2 = int(w * 0.72)
        cy = int(h / 2)

        for dy in [-5, 0, 5]:
            y = cy + dy
            painter.drawLine(x1, y, x2, y)