from PyQt5 import QtCore


class WordBox:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = QtCore.QRect(x, y, w, h)
