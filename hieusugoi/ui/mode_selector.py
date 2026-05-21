# === App Mode System ===
# ModeSelectorWidget: QPushButton mở QMenu để chọn app mode.
# Widget tự render từ APP_MODE_CONFIG — thêm mode mới không cần sửa widget này.
# Nếu import config thất bại, widget vẫn hoạt động ở trạng thái rỗng (safe fallback).

from PyQt5 import QtWidgets, QtCore

try:
    from hieusugoi.config import APP_MODE_CONFIG, get_mode_config, DEFAULT_APP_MODE
except Exception:
    APP_MODE_CONFIG = {}
    DEFAULT_APP_MODE = "deep"

    def get_mode_config(mode_id: str):
        return None


class ModeSelectorWidget(QtWidgets.QPushButton):
    """
    Button mở QMenu liệt kê tất cả app modes từ APP_MODE_CONFIG.
    Scalable: thêm mode mới vào APP_MODE_CONFIG là widget tự cập nhật.
    Không dùng QComboBox.
    """

    mode_changed = QtCore.pyqtSignal(str)   # emit mode_id khi user chọn

    def __init__(self, initial_mode=DEFAULT_APP_MODE, parent=None):
        super().__init__(parent)
        self._current_mode = initial_mode
        self._mode_menu = QtWidgets.QMenu(self)
        self._actions: dict = {}
        self._group = QtWidgets.QActionGroup(self._mode_menu)
        self._group.setExclusive(True)

        self._build_menu()
        self.setMenu(self._mode_menu)
        self._refresh_label()
        self._apply_style()

    # ------------------------------------------------------------------
    def _build_menu(self):
        """Render menu động từ APP_MODE_CONFIG. Gọi lại nếu config thay đổi."""
        self._mode_menu.clear()
        self._actions.clear()

        for mode_id, cfg in APP_MODE_CONFIG.items():
            action = self._mode_menu.addAction(cfg.name)
            action.setCheckable(True)
            action.setActionGroup(self._group)
            # Dùng default arg để tránh closure capture issue
            action.triggered.connect(
                lambda checked, m=mode_id: self._on_selected(m)
            )
            self._actions[mode_id] = action

        # Đánh dấu mode hiện tại
        if self._current_mode in self._actions:
            self._actions[self._current_mode].setChecked(True)
        elif self._actions:
            # Fallback: check item đầu tiên nếu mode không tìm thấy
            list(self._actions.values())[0].setChecked(True)

    def _on_selected(self, mode_id: str):
        self._current_mode = mode_id
        self._refresh_label()
        self.mode_changed.emit(mode_id)

    def _refresh_label(self):
        cfg = get_mode_config(self._current_mode)
        if cfg is not None:
            self.setText(cfg.name)
        else:
            self.setText(self._current_mode)

    def set_mode(self, mode_id: str):
        """Cập nhật mode từ bên ngoài (không emit signal)."""
        if mode_id in self._actions:
            self._current_mode = mode_id
            self._actions[mode_id].setChecked(True)
            self._refresh_label()

    # ------------------------------------------------------------------
    def _apply_style(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border-radius: 5px;
                border: 1px solid #d0d0d0;
                padding: 4px 10px;
                font-size: 12px;
                font-family: "Segoe UI", sans-serif;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton::menu-indicator {
                image: none;
                width: 0px;
            }
        """)
