from PyQt5 import QtWidgets

from hieusugoi.config import CONFIG_FILE
from hieusugoi.storage.app_config import load_app_config, save_app_config


class APIKeyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OpenAI API Key")
        self.setModal(True)
        self.setMinimumWidth(440)

        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Nhập OpenAI API Key. Key sẽ được lưu local tại:\n" + CONFIG_FILE)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.input_key = QtWidgets.QLineEdit()
        self.input_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.input_key.setPlaceholderText("sk-...")
        self.input_key.setText(load_app_config().get("openai_api_key", ""))
        layout.addWidget(self.input_key)

        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_show = QtWidgets.QPushButton("Show/Hide")
        self.btn_show.clicked.connect(self.toggle_show_key)
        btn_layout.addWidget(self.btn_show)
        btn_layout.addStretch()
        self.btn_cancel = QtWidgets.QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        self.btn_save = QtWidgets.QPushButton("Save")
        self.btn_save.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def toggle_show_key(self):
        self.input_key.setEchoMode(
            QtWidgets.QLineEdit.Normal
            if self.input_key.echoMode() == QtWidgets.QLineEdit.Password
            else QtWidgets.QLineEdit.Password
        )

    def api_key(self):
        return self.input_key.text().strip()