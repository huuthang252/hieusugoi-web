from PyQt5 import QtCore


class TranslateWorker(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(str, str)

    def __init__(self, translator, text):
        super().__init__()
        self.translator = translator
        self.text = text

    def run(self):
        result = self.translator.translate_text(self.text)
        self.finished_signal.emit(self.text, result)
