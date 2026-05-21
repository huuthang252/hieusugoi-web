import sys
import os
import time
import json
import unicodedata
import datetime
import shutil
import subprocess
import urllib.request
import urllib.error

# macOS: pynput cho global mouse/keyboard listener
try:
    from pynput import mouse as _pynput_mouse
    from pynput.keyboard import Controller as _KeyboardController, Key as _Key
    _PYNPUT_AVAILABLE = True
except ImportError:
    _PYNPUT_AVAILABLE = False

from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl

from PyQt5 import QtWidgets, QtCore, QtGui

import re
from hieusugoi.config import (
    APP_DATA_DIR,
    CONFIG_FILE,
    HISTORY_DIR,
    resource_path,
    APP_VERSION,
    # === App Mode System ===
    APP_MODE_CONFIG,
    DEFAULT_APP_MODE,
    get_mode_config,
)
from hieusugoi.ocr.text_cleanup import (
    contains_kanji,
    contains_japanese,
    is_japanese_kana_char,
)
from hieusugoi.storage.app_config import load_app_config, save_app_config
from hieusugoi.storage.history import append_history_record, load_history_records
from hieusugoi.translation.service import TranslatorAI, TARGET_LANGUAGES, TARGET_LABELS, ALL_READING_LABELS, ALL_TRANSLATION_LABELS
from hieusugoi.translation.worker import TranslateWorker
from hieusugoi.tts.worker import TTSWorker
from hieusugoi.ui import APIKeyDialog, MenuButton
# === App Mode System ===
try:
    from hieusugoi.ui import ModeSelectorWidget
except Exception:
    ModeSelectorWidget = None
from hieusugoi.auth.login_window import LoginDialog
from hieusugoi.auth.session_manager import SessionManager
from hieusugoi.auth.license_validator import LicenseValidator

# ================= PERFORMANCE LOG HELPER =================
def perf_ms(start_time):
    return (time.perf_counter() - start_time) * 1000


def perf_log(label, start_time):
    print(f"[PERF] {label}: {perf_ms(start_time):.1f} ms")


def _is_own_app_in_foreground() -> bool:
    """True nếu Hieusugoi đang là foreground app — bỏ qua auto-copy.
    macOS: dùng AppKit; fallback: trả về False để không block auto-copy."""
    try:
        from AppKit import NSWorkspace
        pid = NSWorkspace.sharedWorkspace().frontmostApplication().processIdentifier()
        return pid == os.getpid()
    except Exception:
        return False


# Translation and TTS classes were moved to dedicated modules.


class SenseiChatWorker(QtCore.QThread):
    finished_signal = QtCore.pyqtSignal(str)

    def __init__(self, question: str, last_source_text: str,
                 last_translation_result: str, target_language: str):
        super().__init__()
        self.question = question
        self.last_source_text = last_source_text
        self.last_translation_result = last_translation_result
        self.target_language = target_language
        self._server_url = "https://www.hieusugoi.com/api/translate"

    def run(self):
        import requests
        context_block = ""
        if self.last_source_text:
            context_block = (
                f"\n[Context — last studied text]\n"
                f"Source: {self.last_source_text}\n"
                f"Translation result:\n{self.last_translation_result}\n"
            )
        prompt = (
            f"You are Hieusugoi, a helpful AI assistant specializing in Japanese language, "
            f"translation, and general knowledge. "
            f"Always respond in {self.target_language} unless the user writes in Japanese. "
            f"Keep answers concise, clear, and helpful. "
            f"If asked about grammar, vocabulary, kanji, or translation, give a brief explanation with examples."
            f"{context_block}\n"
            f"User: {self.question}\n"
            f"Hieusugoi:"
        )
        try:
            response = requests.post(
                self._server_url,
                json={"text": prompt},
                timeout=30
            )
            if response.status_code == 200:
                result = response.json().get("result", "").strip()
            else:
                result = f"(Server error: {response.status_code})"
        except Exception as e:
            result = f"(Connection error: {e})"
        self.finished_signal.emit(result)



class TranslationPanel(QtWidgets.QWidget):
    def format_html_result(self, text, font_size=19):
        import html

        def is_japanese_char(ch):
            return (
                "\u3040" <= ch <= "\u309F" or  # Hiragana
                "\u30A0" <= ch <= "\u30FF" or  # Katakana
                "\u4E00" <= ch <= "\u9FFF"     # Kanji
            )

        labels = []
        for _orig, _rdg, _trn, _exp in TARGET_LABELS.values():
            for _lbl in (_orig, _rdg, _trn, _exp):
                if _lbl not in labels:
                    labels.append(_lbl)
        html_lines = []

        for line in text.split("\n"):
            line = line.strip()

            if not line:
                html_lines.append('<div style="height: 8px;"></div>')
                continue

            label_html = ""
            line_work = line

            # Tﾃ｡ch label ra trﾆｰ盻嫩 ﾄ黛ｻ・ch盻・label ﾄ柁ｰ盻｣c in ﾄ黛ｺｭm
            for label in labels:
                if line_work.startswith(label):
                    label_html = (
                        f'<span style="font-family: Cambria, Georgia, serif; font-weight:700;">'
                        f'{html.escape(label)}</span> '
                    )
                    line_work = line_work[len(label):].strip()
                    break

            spans = []
            buffer = ""
            current_is_jp = None

            for ch in line_work:
                ch_is_jp = is_japanese_char(ch)

                if current_is_jp is None:
                    current_is_jp = ch_is_jp
                    buffer = ch
                elif ch_is_jp == current_is_jp:
                    buffer += ch
                else:
                    font = (
                        "'Yu Mincho', 'Yu Gothic UI', 'Meiryo', serif"
                        if current_is_jp
                        else "Cambria, Georgia, 'Times New Roman', serif"
                    )
                    spans.append(
                        f'<span style="font-family: {font};">'
                        f'{html.escape(buffer)}</span>'
                    )
                    buffer = ch
                    current_is_jp = ch_is_jp

            if buffer:
                font = (
                    "'Yu Mincho', 'Yu Gothic UI', 'Meiryo', serif"
                    if current_is_jp
                    else "Cambria, Georgia, 'Times New Roman', serif"
                )
                spans.append(
                    f'<span style="font-family: {font};">'
                    f'{html.escape(buffer)}</span>'
                )

            html_lines.append(
                f'<div style="font-size:{font_size}px; line-height:1.42; '
                f'margin-bottom:6px; color:#1e2a3a;">'
                f'{label_html}{"".join(spans)}</div>'
            )

        return "".join(html_lines)
    
    def format_translation_result(self, result):
        lines = [line.strip() for line in result.splitlines() if line.strip()]
        merged = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if line.endswith(":") and i + 1 < len(lines):
                merged.append(f"{line} {lines[i + 1]}")
                i += 2
            else:
                merged.append(line)
                i += 1

        return "\n".join(merged)

    def format_translation_result(self, result):
        lines = [line.strip() for line in result.splitlines() if line.strip()]
        merged = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if line.endswith(":") and i + 1 < len(lines):
                merged.append(f"{line} {lines[i+1]}")
                i += 2
            else:
                merged.append(line)
                i += 1

        output = "\n".join(merged)
        output = re.sub(r"(?:笏≫煤|笏|煤)+\s*$", "", output).strip()
        return output

    def is_actual_english_text(self, text):
        if not text:
            return False
        if contains_japanese(text):
            return False
        return any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in text)

    def __init__(self):
        super().__init__()

        self.main_window = None
        # === App Mode System ===
        self._app_mode = "deep"
        self.resizing_width = False
        self.resize_start_x = 0
        self.resize_start_w = 0
        self.resize_handle_w = 10
        self.min_panel_width = 340
        self.setMinimumSize(self.min_panel_width, 300)

        # Panel-as-main-window: drag + corner resize state
        self.panel_toolbar_h = 42
        self.panel_dragging = False
        self.panel_drag_pos = None
        self.panel_resizing_corner = False
        self.panel_resize_start_pos = None
        self.panel_resize_start_size = None
        self.panel_resize_handle_size = 20

        self.setObjectName("TranslationPanel")
        self.setWindowTitle("Translation History")
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint
        )
        self.setMouseTracking(True)

        self.setStyleSheet("""
            QWidget#TranslationPanel {
                background-color: #f5f7fb;
                font-family: "Segoe UI", "Inter", "Yu Gothic UI", "Meiryo", sans-serif;
                border: 1px solid #d8dee9;
            }

            QPushButton {
                font-family: "Segoe UI", "Inter", "Yu Gothic UI", "Meiryo", sans-serif;
                background-color: #eef1f8;
                color: #2d3748;
                border-radius: 7px;
                padding: 4px 12px;
                border: 1px solid #d8dee9;
                font-size: 12px;
                font-weight: 400;
            }

            QPushButton:hover {
                background-color: #eaf2ff;
                border-color: #4f8cff;
                color: #1a5fd6;
            }

            QPushButton:pressed {
                background-color: #dde8ff;
            }

            QDateEdit {
                font-family: "Segoe UI", "Inter", sans-serif;
                background-color: #ffffff;
                color: #2d3748;
                border: 1px solid #d8dee9;
                border-radius: 7px;
                padding: 3px 8px;
                font-size: 12px;
            }

            QComboBox {
                font-family: "Segoe UI", "Inter", sans-serif;
                background-color: #ffffff;
                color: #2d3748;
                border: 1px solid #d8dee9;
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 12px;
            }

            QComboBox::drop-down { border: none; }

            QTextEdit#currentBox {
                background-color: #ffffff;
                border: 1px solid #d8dee9;
                border-radius: 10px;
                font-family: "Cambria", "Yu Mincho", "Yu Gothic UI", "Georgia", "Meiryo", serif;
                font-size: 19px;
                padding: 18px 20px;
                color: #1e2a3a;
                selection-background-color: #c7dcff;
            }

            QTextEdit#historyBox {
                background-color: #fafbfe;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                font-family: "Cambria", "Yu Gothic UI", "Meiryo", serif;
                font-size: 13px;
                padding: 10px 12px;
                color: #4a5568;
            }
        """)

        # Outer layout: toolbar strip on top, scrollable content below
        _outer = QtWidgets.QVBoxLayout(self)
        _outer.setContentsMargins(0, 0, 0, 0)
        _outer.setSpacing(0)
        self._setup_panel_toolbar(_outer)

        _content = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(_content)
        main_layout.setContentsMargins(14, 10, 14, 12)
        main_layout.setSpacing(8)
        _outer.addWidget(_content, 1)

        # === App Mode System — mode buttons in panel ===
        mode_bar = QtWidgets.QHBoxLayout()
        mode_bar.setSpacing(4)
        self._mode_buttons: dict = {}
        for _mid, _mcfg in APP_MODE_CONFIG.items():
            _btn = QtWidgets.QPushButton(_mcfg.name)
            _btn.setFixedHeight(26)
            _btn.clicked.connect(
                (lambda m: lambda checked=False:
                    self.main_window.change_app_mode(m) if self.main_window else None
                )(_mid)
            )
            mode_bar.addWidget(_btn)
            self._mode_buttons[_mid] = _btn
        main_layout.addLayout(mode_bar)

        self.current_box = QtWidgets.QTextEdit()
        self.current_box.setObjectName("currentBox")
        self.current_box.setReadOnly(True)
        self.current_box.setMinimumHeight(80)
        main_layout.addWidget(self.current_box, 1)

        history_bar = QtWidgets.QHBoxLayout()
        self.history_date = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
        self.history_date.setCalendarPopup(True)
        self.history_date.setDisplayFormat("yyyy-MM-dd")
        history_bar.addWidget(self.history_date)

        self.btn_load_history = QtWidgets.QPushButton("Load history")
        self.btn_load_history.clicked.connect(self.load_history_for_selected_date)
        history_bar.addWidget(self.btn_load_history)

        self._btn_repeat_reading = QtWidgets.QPushButton("🔁 Re-read")
        self._btn_repeat_reading.setFixedHeight(26)
        self._btn_repeat_reading.setToolTip("Replay the reading/pronunciation of the last translation")
        self._btn_repeat_reading.clicked.connect(self._on_repeat_reading)
        history_bar.addWidget(self._btn_repeat_reading)

        self._panel_speaker_btn = QtWidgets.QPushButton("🔊")
        self._panel_speaker_btn.setFixedSize(30, 26)
        self._panel_speaker_btn.setToolTip("Repeat pronunciation")
        self._panel_speaker_btn.setStyleSheet(
            "QPushButton { background: transparent; border: 1px solid #d8dee9; "
            "border-radius: 7px; font-size: 13px; padding: 0px; }"
            "QPushButton:hover { background: #eaf2ff; border-color: #4f8cff; }"
        )
        self._panel_speaker_btn.clicked.connect(self._on_panel_speaker_clicked)
        history_bar.addWidget(self._panel_speaker_btn)

        main_layout.addLayout(history_bar)

        self.history = QtWidgets.QTextEdit()
        self.history.setObjectName("historyBox")
        self.history.setReadOnly(True)
        main_layout.addWidget(self.history, 1)

        # === Chat với Hieusugoi widget (chat mode only) ===
        self._sensei_widget = QtWidgets.QWidget()
        _sensei_layout = QtWidgets.QVBoxLayout(self._sensei_widget)
        _sensei_layout.setContentsMargins(0, 0, 0, 0)
        _sensei_layout.setSpacing(6)

        _sensei_title = QtWidgets.QLabel("💬 Chat với Hieusugoi")
        _sensei_title.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #4f8cff; padding: 2px 0px;"
        )
        _sensei_layout.addWidget(_sensei_title)

        self._sensei_chat_display = QtWidgets.QTextEdit()
        self._sensei_chat_display.setReadOnly(True)
        self._sensei_chat_display.setStyleSheet(
            "QTextEdit { background: #f8faff; border: 1px solid #c5d8f0; "
            "border-radius: 10px; padding: 16px 20px; }"
        )
        _sdoc = self._sensei_chat_display.document()
        if _sdoc:
            _sdoc.setDefaultStyleSheet(
                "body { font-family: Cambria, Georgia, 'Times New Roman', serif; "
                "font-size: 18px; color: #1e2a3a; }"
            )
        self._sensei_chat_display.setPlaceholderText(
            "Hỏi Hieusugoi về tiếng Nhật, dịch thuật, ngôn ngữ..."
        )
        _sensei_layout.addWidget(self._sensei_chat_display, 1)

        _sensei_input_row = QtWidgets.QHBoxLayout()
        _sensei_input_row.setSpacing(6)
        self._sensei_input = QtWidgets.QLineEdit()
        self._sensei_input.setPlaceholderText("Nhắn tin với Hieusugoi...")
        self._sensei_input.setStyleSheet(
            "QLineEdit { background: #ffffff; border: 1px solid #d8dee9; "
            "border-radius: 7px; padding: 6px 12px; "
            "font-family: 'Cambria', 'Yu Gothic UI', 'Meiryo', serif; "
            "font-size: 17px; line-height: 1.4; color: #1f2937; }"
            "QLineEdit:focus { border-color: #4f8cff; }"
        )
        self._sensei_input.returnPressed.connect(self._on_sensei_send)
        _sensei_input_row.addWidget(self._sensei_input, 1)

        self._sensei_send_btn = QtWidgets.QPushButton("Gửi")
        self._sensei_send_btn.setFixedHeight(30)
        self._sensei_send_btn.setStyleSheet(
            "QPushButton { background-color: #4f8cff; color: white; border-radius: 7px; "
            "border: none; font-size: 12px; font-weight: 600; padding: 0px 14px; }"
            "QPushButton:hover { background-color: #3a7be0; }"
            "QPushButton:disabled { background-color: #c5d5f0; color: #8fa8cc; }"
        )
        self._sensei_send_btn.clicked.connect(self._on_sensei_send)
        _sensei_input_row.addWidget(self._sensei_send_btn)

        _sensei_layout.addLayout(_sensei_input_row)

        self._sensei_widget.setVisible(False)
        self._sensei_worker: SenseiChatWorker | None = None
        self._sensei_messages: list = []
        main_layout.addWidget(self._sensei_widget, 1)
        self._main_layout = main_layout

    # ── Panel toolbar (main-window controls) ─────────────────────────────
    def _setup_panel_toolbar(self, parent_layout):
        self._toolbar_frame = QtWidgets.QFrame()
        self._toolbar_frame.setFixedHeight(self.panel_toolbar_h)
        self._toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: #eef1f8;
                border-bottom: 1px solid #d8dee9;
            }
            QPushButton {
                background-color: transparent;
                color: #2d3748;
                border-radius: 6px;
                border: none;
                font-size: 12px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #dde8ff;
                color: #1a5fd6;
            }
        """)
        tl = QtWidgets.QHBoxLayout(self._toolbar_frame)
        tl.setContentsMargins(8, 5, 8, 5)
        tl.setSpacing(2)

        self._panel_menu_btn = MenuButton()
        self._panel_menu_btn.setFixedSize(32, 28)
        self._panel_menu_btn.setToolTip("Menu")
        _logo_icon = QtGui.QIcon(resource_path("assets/logo.ico"))
        self._panel_menu_btn.setIcon(_logo_icon)
        self._panel_menu_btn.setIconSize(QtCore.QSize(22, 22))
        self._panel_menu_btn.setText("")
        self._panel_menu_btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; border-radius: 6px; }
            QPushButton:hover { background-color: #dde8ff; }
            QPushButton::menu-indicator { image: none; width: 0px; }
        """)
        tl.addWidget(self._panel_menu_btn)

        self._panel_brand_label = QtWidgets.QLabel("Hieusugoi")
        self._panel_brand_label.setStyleSheet(
            "QLabel { border: none; background: transparent; color: #2d3748; "
            "font-size: 13px; font-weight: 600; padding-left: 0px; "
            "font-family: 'Segoe UI', 'Inter', sans-serif; }"
        )
        tl.addWidget(self._panel_brand_label)

        tl.addSpacing(6)

        self._panel_target_combo = QtWidgets.QComboBox()
        self._panel_target_combo.addItems(TARGET_LANGUAGES)
        self._panel_target_combo.setCurrentText("English")
        self._panel_target_combo.setFixedSize(75, 24)
        self._panel_target_combo.setStyleSheet(
            "QComboBox { border: 1px solid #d8dee9; border-radius: 6px; "
            "background: #ffffff; font-size: 11px; padding: 1px 4px; "
            "color: #2d3748; font-family: 'Segoe UI', sans-serif; }"
            "QComboBox::drop-down { border: none; width: 12px; }"
        )
        self._panel_target_combo.currentTextChanged.connect(
            lambda t: self.main_window.set_target_language(t) if self.main_window else None
        )
        tl.addWidget(self._panel_target_combo)

        _toolbar_spacer = QtWidgets.QWidget()
        _toolbar_spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        tl.addWidget(_toolbar_spacer)

        # Username / Login button — sits right of spacer, left of window controls
        self.title = QtWidgets.QPushButton("Login")
        self.title.setObjectName("title")
        self.title.setFlat(True)
        self.title.setMaximumWidth(80)
        self.title.setCursor(QtCore.Qt.PointingHandCursor)  # type: ignore[attr-defined]
        self.title.setStyleSheet(
            "QPushButton { color: #6b7a99; font-size: 11px; font-weight: 400; "
            "background: transparent; border: none; padding: 2px 4px; "
            "font-family: 'Segoe UI', 'Inter', sans-serif; }"
            "QPushButton:hover { color: #4f8cff; }"
            "QPushButton:disabled { color: #8898b8; }"
        )
        self.title.clicked.connect(
            lambda: self.main_window.open_login_dialog() if self.main_window else None
        )
        tl.addWidget(self.title)

        self._panel_minimize_btn = QtWidgets.QPushButton("−")
        self._panel_minimize_btn.setFixedSize(32, 28)
        self._panel_minimize_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #6b7a99; font-size: 16px; border: none; }"
            "QPushButton:hover { background: #dde8ff; color: #2d3748; }"
        )
        self._panel_minimize_btn.clicked.connect(
            lambda: self.main_window.minimize_all() if self.main_window else None
        )
        tl.addWidget(self._panel_minimize_btn)

        self._panel_close_btn = QtWidgets.QPushButton("×")
        self._panel_close_btn.setFixedSize(32, 28)
        self._panel_close_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #6b7a99; font-size: 15px; border: none; }"
            "QPushButton:hover { background: #ffd7d7; color: #c0392b; }"
        )
        self._panel_close_btn.clicked.connect(
            lambda: self.main_window.close_all() if self.main_window else None
        )
        tl.addWidget(self._panel_close_btn)

        # Build panel dropdown menu
        _pmenu = QtWidgets.QMenu(self._panel_menu_btn)

        _voice_sub = _pmenu.addMenu("Voice")
        self._panel_action_voice_female = _voice_sub.addAction("Female")
        self._panel_action_voice_female.setCheckable(True)
        self._panel_action_voice_female.setChecked(True)
        self._panel_action_voice_female.triggered.connect(
            lambda: self.main_window.set_tts_voice("female") if self.main_window else None
        )
        self._panel_action_voice_male = _voice_sub.addAction("Male")
        self._panel_action_voice_male.setCheckable(True)
        self._panel_action_voice_male.triggered.connect(
            lambda: self.main_window.set_tts_voice("male") if self.main_window else None
        )
        _voice_sub.addSeparator()
        _speed_sub = _voice_sub.addMenu("Speed")
        self._panel_speed_actions = {}
        for _pct in [75, 100, 125]:
            _sa = _speed_sub.addAction(f"{_pct}%")
            _sa.setCheckable(True)
            if _pct == 100:
                _sa.setChecked(True)
            _sa.triggered.connect(
                (lambda p: lambda: self.main_window.set_tts_rate(p) if self.main_window else None)(_pct)
            )
            self._panel_speed_actions[_pct] = _sa

        _pmenu.addSeparator()
        _pmenu.addAction("Information").triggered.connect(
            lambda: self.main_window.show_information_dialog() if self.main_window else None
        )
        _pmenu.addSeparator()
        _pmenu.addAction("Logout").triggered.connect(
            lambda: self.main_window.logout() if self.main_window else None
        )
        _pmenu.addSeparator()
        self._panel_action_auto_copy = _pmenu.addAction("Auto Copy: ON")
        self._panel_action_auto_copy.setCheckable(True)
        self._panel_action_auto_copy.setChecked(True)
        self._panel_action_auto_copy.triggered.connect(
            lambda: self.main_window.toggle_auto_copy() if self.main_window else None
        )

        _pmenu.addSeparator()
        self._panel_action_overlay = _pmenu.addAction("Ghi Chú: OFF")
        self._panel_action_overlay.setCheckable(True)
        self._panel_action_overlay.setChecked(False)
        self._panel_action_overlay.triggered.connect(
            lambda: self.main_window.toggle_overlay() if self.main_window else None
        )

        self._panel_menu_btn.setMenu(_pmenu)
        parent_layout.addWidget(self._toolbar_frame)

    def _on_panel_speaker_clicked(self):
        if self.main_window:
            self.main_window.toggle_tts_enabled()
            self._panel_speaker_btn.setText("🔊" if self.main_window.tts_enabled else "🔇")

    def sync_toolbar(self):
        if not self.main_window:
            return
        if self.main_window.is_logged_in():
            username = self.main_window.get_session_username() or "User"
            self.title.setText(username)
            self.title.setEnabled(False)
        else:
            self.title.setText("Login")
            self.title.setEnabled(True)
        self._panel_speaker_btn.setText("🔊" if self.main_window.tts_enabled else "🔇")
        if hasattr(self, "_panel_action_auto_copy") and self._panel_action_auto_copy:
            lbl = "Auto Copy: ON" if self.main_window.auto_copy_enabled else "Auto Copy: OFF"
            self._panel_action_auto_copy.setText(lbl)
            self._panel_action_auto_copy.setChecked(self.main_window.auto_copy_enabled)
        if hasattr(self, "_panel_target_combo"):
            lang = getattr(self.main_window, "target_language", "English")
            self._panel_target_combo.blockSignals(True)
            self._panel_target_combo.setCurrentText(lang)
            self._panel_target_combo.blockSignals(False)

    def set_mini_result(self, _text):
        pass

    def _on_repeat_reading(self):
        if self.main_window:
            self.main_window.repeat_reading()

    # ── end panel toolbar ─────────────────────────────────────────────────

    def _is_in_resize_handle(self, x):
        """Resize handle follows the panel's outside edge.
        Left panel: left edge. Right panel: right edge.
        """
        if self.main_window and self.main_window.panel_side == "right":
            return x >= self.width() - self.resize_handle_w
        return x <= self.resize_handle_w

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.main_window:
            self.main_window.update_overlay_position()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.main_window:
            self.main_window.update_overlay_position()

    def changeEvent(self, event):
        _WSC = getattr(QtCore.QEvent, "WindowStateChange", 105)
        if event.type() == _WSC and self.main_window:
            if self.isMinimized():
                self.main_window.hide()
            else:
                if self.main_window.overlay_enabled:
                    self.main_window.show()
                    self.main_window.update_overlay_position()
        super().changeEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)

        if not self.main_window:
            return

        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)

        if self.main_window.panel_collapsed:
            painter.setBrush(QtGui.QBrush(QtGui.QColor(210, 210, 210, 120)))
            painter.drawRect(0, 0, self.width(), self.height())
            return

        # Inner edge strip: click to collapse/expand panel
        painter.setBrush(QtGui.QBrush(QtGui.QColor(210, 210, 210, 90)))
        if self.main_window.panel_side == "right":
            painter.drawRect(0, 0, self.resize_handle_w, self.height())
        else:
            painter.drawRect(self.width() - self.resize_handle_w, 0, self.resize_handle_w, self.height())

        # Outer edge strip: drag to resize panel width
        painter.setBrush(QtGui.QBrush(QtGui.QColor(190, 190, 190, 80)))
        if self.main_window.panel_side == "right":
            painter.drawRect(self.width() - self.resize_handle_w, 0, self.resize_handle_w, self.height())
        else:
            painter.drawRect(0, 0, self.resize_handle_w, self.height())

        # Corner resize handle (bottom-right)
        s = self.panel_resize_handle_size
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 100)))
        painter.drawRect(self.width() - s, self.height() - s, s, s)
        painter.setPen(QtGui.QColor(255, 255, 255, 180))
        painter.setFont(QtGui.QFont("Segoe UI Symbol", 10))
        painter.drawText(  # type: ignore[call-overload]
            QtCore.QRect(self.width() - s, self.height() - s, s, s),
            QtCore.Qt.AlignCenter, "⇲"
        )

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return

        pos = event.pos()

        # Priority 1: corner resize (bottom-right 20×20)
        s = self.panel_resize_handle_size
        if pos.x() >= self.width() - s and pos.y() >= self.height() - s:
            self.panel_resizing_corner = True
            self.panel_resize_start_pos = event.globalPos()
            self.panel_resize_start_size = self.size()
            event.accept()
            return

        # Priority 2: toolbar drag (not on an interactive child)
        if pos.y() <= self.panel_toolbar_h:
            child = self.childAt(pos)
            if not isinstance(child, (QtWidgets.QPushButton, QtWidgets.QComboBox)):
                self.panel_dragging = True
                self.panel_drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
                return

        # Priority 3 & 4: existing edge-strip behaviors
        if not self.main_window:
            return

        x = pos.x()
        if self.main_window.panel_side == "right":
            in_outer_resize_edge = x >= self.width() - self.resize_handle_w
        else:
            in_outer_resize_edge = x <= self.resize_handle_w

        if in_outer_resize_edge:
            self.resizing_width = True
            self.resize_start_x = event.globalX()
            self.resize_start_w = self.width()
            event.accept()
            return

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.panel_dragging = False
            self.panel_resizing_corner = False
            self.resizing_width = False

    def mouseMoveEvent(self, event):
        pos = event.pos()

        # Corner resize
        if self.panel_resizing_corner:
            delta = event.globalPos() - self.panel_resize_start_pos
            new_w = max(self.min_panel_width, self.panel_resize_start_size.width() + delta.x())
            new_h = max(300, self.panel_resize_start_size.height() + delta.y())
            self.resize(new_w, new_h)
            event.accept()
            return

        # Toolbar drag
        if self.panel_dragging:
            self.move(event.globalPos() - self.panel_drag_pos)
            if self.main_window:
                self.main_window.panel_is_free = True
            event.accept()
            return

        if not self.main_window:
            return

        if self.main_window.panel_collapsed:
            self.setCursor(QtCore.Qt.PointingHandCursor)
            return

        # Cursor hints
        s = self.panel_resize_handle_size
        if pos.x() >= self.width() - s and pos.y() >= self.height() - s:
            self.setCursor(QtCore.Qt.SizeFDiagCursor)
            return

        x = pos.x()
        if self.main_window.panel_side == "right":
            in_outer_resize_edge = x >= self.width() - self.resize_handle_w
        else:
            in_outer_resize_edge = x <= self.resize_handle_w

        if in_outer_resize_edge:
            self.setCursor(QtCore.Qt.SizeHorCursor)
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)

        if self.resizing_width:
            delta = event.globalX() - self.resize_start_x
            if self.main_window.panel_side == "right":
                new_w = max(self.min_panel_width, self.resize_start_w + delta)
            else:
                new_w = max(self.min_panel_width, self.resize_start_w - delta)
            self.resize(new_w, self.height())
            self.main_window.panel_width = new_w
            self.main_window.last_panel_width = new_w
            self.main_window.dock_panel()
            event.accept()

    def set_mode(self, *args):
        pass

    # === App Mode System ===
    def set_app_mode(self, mode_id: str):
        self._app_mode = mode_id
        is_chat = (mode_id == "chat")
        show_history = (mode_id == "deep")

        self.history_date.setVisible(show_history)
        self.btn_load_history.setVisible(show_history)
        self._btn_repeat_reading.setVisible(show_history)
        self._panel_speaker_btn.setVisible(show_history)
        self.history.setVisible(show_history)
        self._sensei_widget.setVisible(is_chat)

        # Adjust vertical stretch: chat → 3/7 (translation/chat); others → 1/1 or 1/0
        if is_chat:
            self._main_layout.setStretch(1, 3)  # current_box 30%
            self._main_layout.setStretch(3, 0)  # history hidden
            self._main_layout.setStretch(4, 7)  # chat 70%
        elif mode_id == "deep":
            self._main_layout.setStretch(1, 1)  # current_box 50%
            self._main_layout.setStretch(3, 1)  # history 50%
            self._main_layout.setStretch(4, 0)
        else:  # quick
            self._main_layout.setStretch(1, 1)
            self._main_layout.setStretch(3, 0)
            self._main_layout.setStretch(4, 0)

        self.update_mode_buttons(mode_id)

    def update_mode_buttons(self, mode_id: str) -> None:
        """Highlight nút mode đang active trong panel."""
        for mid, btn in self._mode_buttons.items():
            if mid == mode_id:
                btn.setStyleSheet(
                    "background-color: #1a73e8; color: white; "
                    "border: 1px solid #1558b0; border-radius: 5px; "
                    "padding: 5px 10px; font-size: 12px;"
                )
            else:
                btn.setStyleSheet(
                    "background-color: #f0f0f0; color: #333333; "
                    "border: 1px solid #d0d0d0; border-radius: 5px; "
                    "padding: 5px 10px; font-size: 12px;"
                )

    # === Sensei Chat ===
    def _sensei_render_chat(self):
        import html as _html
        if not self._sensei_messages:
            self._sensei_chat_display.clear()
            return
        parts: list[str] = []
        for msg in self._sensei_messages:
            role = msg["role"]
            text = _html.escape(msg["text"]).replace("\n", "<br>")
            if msg.get("pending"):
                text = f'<i style="color: #999999;">{text}</i>'
            if role == "user":
                lbl_color = "#4f8cff"
                bar_color = "#4f8cff"
                txt_color = "#1d3557"
                label = "Bạn"
            else:
                lbl_color = "#2a9d5c"
                bar_color = "#2a9d5c"
                txt_color = "#2d3748"
                label = "Hieusugoi"
            parts.append(
                f'<p style="margin: 0 0 2px 0; font-size: 11px; font-weight: 700; '
                f'font-family: Segoe UI, sans-serif; color: {lbl_color};">{label}</p>'
                f'<p style="margin: 0 0 10px 0; padding-left: 12px; '
                f'border-left: 3px solid {bar_color}; font-size: 18px; '
                f'line-height: 140%; font-family: Cambria, Georgia, serif; '
                f'color: {txt_color};">{text}</p>'
            )
        self._sensei_chat_display.setHtml("".join(parts))
        self._sensei_chat_display.moveCursor(QtGui.QTextCursor.End)

    def _on_sensei_send(self):
        question = self._sensei_input.text().strip()
        if not question:
            return
        if self._sensei_worker and self._sensei_worker.isRunning():
            return

        self._sensei_input.clear()
        self._sensei_send_btn.setEnabled(False)

        self._sensei_messages.append({"role": "user", "text": question})
        self._sensei_messages.append({"role": "sensei", "text": "đang suy nghĩ...", "pending": True})
        self._sensei_render_chat()

        last_src = ""
        last_res = ""
        if self.main_window:
            last_src = getattr(self.main_window, "_last_translated_text", "")
            last_res = getattr(self.main_window, "_last_translation_result", "")
        target_lang = "English"
        if self.main_window:
            target_lang = getattr(self.main_window, "target_language", "English")

        self._sensei_worker = SenseiChatWorker(question, last_src, last_res, target_lang)
        self._sensei_worker.finished_signal.connect(self._on_sensei_reply)
        self._sensei_worker.start()

    def _on_sensei_reply(self, reply: str):
        self._sensei_send_btn.setEnabled(True)
        for msg in reversed(self._sensei_messages):
            if msg["role"] == "sensei" and msg.get("pending"):
                msg["text"] = reply
                msg["pending"] = False
                break
        self._sensei_render_chat()

    def push_sensei_prompt(self, prompt: str):
        """Inject a prompt into Chat và gửi ngay."""
        if self._sensei_worker and self._sensei_worker.isRunning():
            return
        self._sensei_input.setText(prompt)
        self._on_sensei_send()

    def _extract_quick_display(self, result: str) -> str:
        """Extract translation line regardless of target language label."""
        for line in result.splitlines():
            stripped = line.strip()
            for trn_label in ALL_TRANSLATION_LABELS:
                if stripped.startswith(trn_label):
                    value = stripped[len(trn_label):].strip()
                    if value:
                        return f"{trn_label} {value}"
        return result

    def render_history_records(self, records):
        blocks = []
        for record in reversed(records):
            blocks.append(
                f"[{record.get('time', '')}] {record.get('source_text', '')}\n\n"
                f"{record.get('result', '')}\n"
            )
        return "\n".join(blocks)

    def load_history_for_selected_date(self):
        date_str = self.history_date.date().toString("yyyy-MM-dd")
        records = load_history_records(date_str)
        if not records:
            self.history.setHtml(self.format_html_result(f"Không có lịch sử cho ngày {date_str}.", font_size=14))
            return
        history_text = self.render_history_records(records)
        self.history.setHtml(self.format_html_result(history_text, font_size=14))
        self.history.moveCursor(QtGui.QTextCursor.Start)

    def show_today_history(self):
        self.history_date.setDate(QtCore.QDate.currentDate())
        self.load_history_for_selected_date()

    def show_loading(self, text):
        self.current_box.setHtml(self.format_html_result(f"Đang dịch:\n{text}", font_size=19))

    def should_hide_reading_section(self, text):
        # Hide reading for long/punctuated text where it adds little value
        stripped = text.strip()
        if len(stripped) > 40:
            return True
        return any(ch in stripped for ch in "。、！？!?.,:")

    def hide_reading_section(self, display_result):
        lines = []
        for line in display_result.splitlines():
            stripped = line.strip()
            matched_rdg = None
            for rl in ALL_READING_LABELS:
                if stripped.startswith(rl):
                    matched_rdg = rl
                    break
            if matched_rdg:
                after = stripped[len(matched_rdg):].strip()
                # If the reading and translation got merged on one line, keep translation part
                for tl in ALL_TRANSLATION_LABELS:
                    if after.startswith(tl):
                        lines.append(after)
                        break
                continue
            lines.append(line)
        return "\n".join(lines).strip()

    def add_result(self, text, result):
        if not result or not result.strip():
            return

        display_result = self.format_translation_result(result)
        if self.should_hide_reading_section(text):
            display_result = self.hide_reading_section(display_result)

        if not display_result or not display_result.strip():
            return

        # === App Mode System ===
        # Quick mode: chỉ hiển thị dòng "Dịch nghĩa:" trong current_box.
        # Deep + Chat: hiển thị đầy đủ.
        # History file vẫn ghi đầy đủ (append_history_record không đổi).
        if self._app_mode in ("deep", "chat"):
            box_display = display_result
        else:
            box_display = self._extract_quick_display(display_result)

        self.current_box.setHtml(self.format_html_result(box_display, font_size=19))

        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_text = now.strftime("%H:%M:%S")
        mode = f"→ {self.main_window.target_language}" if self.main_window else ""

        append_history_record({
            "date": date_str,
            "time": time_text,
            "mode": mode,
            "source_text": text,
            "result": display_result
        })

        # Chỉ refresh history display trong deep mode (quick mode ẩn history widget)
        if self._app_mode == "deep" and self.history_date.date().toString("yyyy-MM-dd") == date_str:
            self.load_history_for_selected_date()


# ================= APP MAIN WINDOW =================
class FixedLearningWindow(QtWidgets.QWidget):
    # macOS pynput: signals để emit từ background thread về main thread
    _mac_mouse_press_signal = QtCore.pyqtSignal(int, int)
    _mac_mouse_release_signal = QtCore.pyqtSignal(int, int)

    def set_language_from_menu(self, *args):
        pass  # replaced by set_target_language via panel combobox

    def play_audio_internal(self, path):
        try:
            self.audio_player.stop()   #  ng蘯ｯt audio cﾅｩ
        except Exception:
            pass

        from PyQt5.QtMultimedia import QMediaContent
        from PyQt5.QtCore import QUrl

        url = QUrl.fromLocalFile(path)
        self.audio_player.setMedia(QMediaContent(url))
        self.audio_player.play()

    # TTS:
    # - English: ﾄ黛ｻ皇 tr盻ｱc ti蘯ｿp text OCR
    # - Japanese cﾃｳ Hiragana/Katakana: ﾄ黛ｻ皇 tr盻ｱc ti蘯ｿp text OCR
    # - Japanese ch盻・cﾃｳ Kanji: l蘯･y dﾃｲng "Cﾃ｡ch ﾄ黛ｻ皇:" t盻ｫ k蘯ｿt qu蘯｣ AI r盻妬 ﾄ黛ｻ皇 hiragana/kana
    def has_kana(self, text):
        return any(is_japanese_kana_char(ch) for ch in text)

    def is_english_text(self, text):
        return any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in text)

    def is_actual_english_text(self, text):
        if not text:
            return False
        if contains_japanese(text):
            return False
        return self.is_english_text(text)

    def extract_reading_from_result(self, result):
        if not result:
            return ""
        lines = [line.strip() for line in result.splitlines()]
        for i, line in enumerate(lines):
            for rl in ALL_READING_LABELS:
                if line.startswith(rl):
                    reading = line[len(rl):].strip()
                    if not reading and i + 1 < len(lines):
                        reading = lines[i + 1].strip()
                    reading = reading.lstrip("-•・ ").strip()
                    if "(" in reading:
                        reading = reading.split("(")[0].strip()
                    return reading
        return ""

    def start_tts(self, text, language="en-US"):
        text = text.strip()
        if not text:
            return

        if not self.tts_enabled:
            return

        if self.tts_worker and self.tts_worker.isRunning():
            return

        # === Right-click replay — lưu text/language thực sự sẽ phát ===
        self.last_tts_text     = text
        self.last_tts_language = language

        self.tts_worker = TTSWorker(
            text,
            gender=self.tts_voice_gender,
            rate_percent=self.tts_rate_percent,
            language=language
        )

        self.tts_worker.play_signal.connect(self.play_audio_internal)
        self.tts_worker.start()

    def _tts_lang_for_target(self) -> str:
        return {
            "English": "en-US", "Vietnamese": "vi-VN", "Japanese": "ja-JP",
            "Korean": "ko-KR", "Chinese": "zh-CN", "French": "fr-FR",
            "German": "de-DE", "Spanish": "es-ES", "Portuguese": "pt-BR",
            "Thai": "th-TH",
        }.get(self.target_language, "en-US")

    def speak_after_translation(self, source_text, result):
        if not source_text:
            return

        # Japanese source: prefer hiragana reading for Kanji
        if contains_kanji(source_text) or self.has_kana(source_text):
            if contains_kanji(source_text):
                reading = self.extract_reading_from_result(result)
                if reading and self.has_kana(reading):
                    self.start_tts(reading, language="ja-JP")
                    return
            self.start_tts(source_text, language="ja-JP")
            return

        # English source
        if self.is_actual_english_text(source_text):
            self.start_tts(source_text, language="en-US")
            return

        # Fallback: use target language for TTS
        self.start_tts(source_text, language=self._tts_lang_for_target())

    def update_speaker_tooltip(self):
        if self.tts_enabled:
            self.btn_speaker.setToolTip("Âm thanh đang BẬT - Click để tắt đọc âm thanh")
        else:
            self.btn_speaker.setToolTip("Âm thanh đang TẮT - Click để bật đọc âm thanh")

    def toggle_tts_enabled(self):
        self.tts_enabled = not self.tts_enabled
        icon = "🔊" if self.tts_enabled else "🔇"
        self.btn_speaker.setText(icon)
        self.update_speaker_tooltip()
        if self.panel and hasattr(self.panel, "_panel_speaker_btn"):
            self.panel._panel_speaker_btn.setText(icon)

    def set_tts_voice(self, gender):
        self.tts_voice_gender = gender

        self.action_voice_female.setChecked(gender == "female")
        self.action_voice_male.setChecked(gender == "male")

    def set_tts_rate(self, percent):
        self.tts_rate_percent = percent

        self.action_speed_75.setChecked(percent == 75)
        self.action_speed_100.setChecked(percent == 100)
        self.action_speed_125.setChecked(percent == 125)

    def make_mini_result(self, text, result):
        word = text
        reading = ""
        meaning = ""

        lines = [line.strip() for line in result.splitlines() if line.strip()]
        i = 0
        while i < len(lines):
            line = lines[i]
            matched_rdg = next((rl for rl in ALL_READING_LABELS if line.startswith(rl)), None)
            matched_trn = next((tl for tl in ALL_TRANSLATION_LABELS if line.startswith(tl)), None)
            if matched_rdg and not reading:
                value = line[len(matched_rdg):].strip()
                if not value and i + 1 < len(lines):
                    value = lines[i + 1].strip()
                    i += 1
                if "(" in value:
                    value = value.split("(")[0].strip()
                reading = value
            elif matched_trn and not meaning:
                value = line[len(matched_trn):].strip()
                if not value and i + 1 < len(lines):
                    value = lines[i + 1].strip()
                    i += 1
                meaning = value
            i += 1

        word_part = f"{word}({reading})" if reading else word
        mini = f"{word_part} → {meaning}" if meaning else word_part
        if len(mini) > 80:
            mini = mini[:80] + "..."
        return mini

    def toggle_panel_collapse(self):
        if self.panel_collapsed:
            self.panel_collapsed = False
            self.panel_width = max(300, self.last_panel_width)
        else:
            self.panel_collapsed = True
            self.last_panel_width = max(300, self.panel_width)

        self.dock_panel()
    def minimize_all(self):
        self.hide()
        self.panel.showMinimized()

    def changeEvent(self, event):
        super().changeEvent(event)

    def __init__(self):
        super().__init__()

        self.translator = TranslatorAI()
        self.audio_player = QMediaPlayer()

        # Performance tracking for translation latency analysis
        self.perf_request_start = None
        self.perf_selected_at = None
        self.perf_translate_start = None
        self.perf_worker_start = None
        self.install_perf_hooks()

        self.panel_width = 430
        self.last_panel_width = 430
        self.panel_collapsed = False
        self.panel_peek_width = 8   # d蘯｣i vi盻］ cﾃｲn l蘯｡i khi thu vﾃo
        self.panel_side = "left"
        self.panel_is_free = False
        self.overlay_side = "right"
        self.overlay_enabled = False
        self.was_ocr_enabled_before_drag = True

        self.panel = TranslationPanel()
        self.panel.main_window = self
        self.panel.show()
        self.panel.resize(430, 650)   # default size before dock

        # Target language — AI auto-detects source
        self.target_language = "English"
        self.translator.set_target_language(self.target_language)

        # Store last translation for repeat-reading
        self._last_translated_text = ""
        self._last_translation_result = ""

        # === App Mode System ===
        # Load mode đã lưu từ config.json, fallback về "deep" nếu không có.
        try:
            _saved_cfg   = load_app_config()
            _loaded_mode = _saved_cfg.get("app_mode", DEFAULT_APP_MODE)
            self.app_mode = _loaded_mode if _loaded_mode in APP_MODE_CONFIG else DEFAULT_APP_MODE
            _saved_lang = _saved_cfg.get("target_language", "English")
            if _saved_lang in TARGET_LANGUAGES:
                self.target_language = _saved_lang
                self.translator.set_target_language(_saved_lang)
        except Exception:
            self.app_mode = DEFAULT_APP_MODE

        self.current_worker = None
        self.tts_worker = None
        # TTS Settings
        self.tts_enabled = True
        self.tts_voice_gender = "female"   # female / male
        self.tts_rate_percent = 100        # 75 / 100 / 125
        # === Right-click replay ===
        self.last_tts_text     = ""        # text thực sự đã phát (có thể là reading, không phải source)
        self.last_tts_language = "ja-JP"   # language code đã dùng khi phát lần cuối

        # v2.0.0: clipboard state
        self._last_clipboard_text = ""

        # v2.0.0: auto-copy on mouse release
        self.auto_copy_enabled = True
        self._last_left_down = False
        self._mouse_down_time = 0.0
        self._mouse_down_pos = None
        self._mouse_release_pos = None
        self._auto_copy_last_time = 0.0
        self._pynput_listener = None
        self._mac_mouse_press_signal.connect(self._on_mac_mouse_pressed)
        self._mac_mouse_release_signal.connect(self._on_mac_mouse_released)
        # Khởi động listener sau khi event loop chạy để window đã có parent
        QtCore.QTimer.singleShot(0, self._start_mouse_listener)
        print("[HOOK] Selection listener initializing (macOS pynput)")

        self.dragging = False
        self.resizing = False       # kept as guard for _maybe_auto_copy; never set True
        self.resizing_width = False
        self.resize_margin = 6
        self.lp_min_width = 200
        self.resize_start_global_x = 0
        self.resize_start_width = 0
        self.ocr_enabled = True

        self.session_manager = SessionManager()
        self.validator = LicenseValidator()
        self.session = None
        self.logged_in = False
        self.license_validated_today = False
        self.needs_license_validation = False
        self.lookup_auth_in_progress = False
        self.login_prompted = False
        self.license_validation_failed = False

        self.drag_pos = None

        self.resize_handle_size = 24
        self.control_height = 55

        self.selection_rect = None  # guard for show_quick_popup

        self._note_file_path = None   # đường dẫn file đang mở trong Ghi Chú
        self._note_modified  = False  # True nếu có thay đổi chưa lưu

        self.init_ui()
        self.update_mask()  # restrict mouse to toolbar + resize handle
        self.dock_panel()
        # === App Mode System ===
        self.panel.set_app_mode(self.app_mode)
        self.load_auth_session()
        self.panel.sync_toolbar()

        # v2.0.0: clipboard dataChanged drives translation
        self._clipboard = QtWidgets.QApplication.clipboard()
        self._clipboard.dataChanged.connect(self._on_clipboard_changed)

        # Dock overlay to panel after event loop places the windows
        QtCore.QTimer.singleShot(0, self.update_overlay_position)

    def init_ui(self):
        self.setWindowTitle("Hieusugoi v2.2.1 macOS - Ghi Chú")
        self.setWindowIcon(QtGui.QIcon(resource_path("assets/logo.ico")))
        self.setGeometry(220, 100, 370, 740)
        self.setMinimumSize(200, 150)
        self.control_height = 48

        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint
        )
        self.setMouseTracking(True)

        # ── Root layout ───────────────────────────────────────────────────
        _root = QtWidgets.QVBoxLayout(self)
        _root.setContentsMargins(0, 0, 0, 0)
        _root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────
        self.control = QtWidgets.QFrame(self)
        self.control.setFixedHeight(42)
        self.control.setObjectName("LPHeader")
        self.control.setStyleSheet("""
            QFrame#LPHeader {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2d3748, stop:1 #3a4a6b);
                border-bottom: 1px solid #1a202c;
            }
            QPushButton {
                background: transparent; border: none; color: white;
                font-family: "Segoe UI", "Inter", "Yu Gothic UI", "Meiryo", sans-serif;
                font-size: 12px; border-radius: 6px; padding: 4px 8px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.18); }
            QPushButton::menu-indicator { image: none; width: 0px; }
            QLabel {
                color: white; background: transparent; border: none;
                font-family: "Segoe UI", "Inter", "Yu Gothic UI", "Meiryo", sans-serif;
            }
        """)

        _hdr = QtWidgets.QHBoxLayout(self.control)
        _hdr.setContentsMargins(8, 5, 8, 5)
        _hdr.setSpacing(2)

        _lbl_icon = QtWidgets.QLabel("📋")
        _lbl_icon.setStyleSheet("font-size: 14px; background: transparent; border: none;")
        _hdr.addWidget(_lbl_icon)

        self._note_title_label = QtWidgets.QLabel("Ghi Chú")
        self._note_title_label.setStyleSheet(
            'font-size: 12px; font-weight: 600; '
            'font-family: "Segoe UI", "Inter", "Yu Gothic UI", "Meiryo", sans-serif; '
            "background: transparent; border: none;"
        )
        _hdr.addWidget(self._note_title_label, 1)

        # ── "Tệp ▾" dropdown menu ─────────────────────────────────────────
        _btn_file = QtWidgets.QPushButton("Tệp ▾")
        _btn_file.setFixedHeight(26)
        _btn_file.setToolTip("Tệp — Mới / Mở / Lưu / Lưu thành / Xóa nội dung")

        _file_menu = QtWidgets.QMenu(_btn_file)
        _file_menu.setStyleSheet("""
            QMenu {
                font-family: "Segoe UI", "Inter", "Yu Gothic UI", "Meiryo", sans-serif;
                font-size: 12px;
                background-color: #2d3748;
                color: #f0f4ff;
                border: 1px solid #1a202c;
                padding: 3px 0;
            }
            QMenu::item { padding: 5px 24px 5px 14px; border-radius: 3px; }
            QMenu::item:selected { background-color: #4a6fa5; color: #ffffff; }
            QMenu::separator { height: 1px; background: #4a5568; margin: 3px 8px; }
        """)
        _file_menu.addAction("Mới").triggered.connect(self._note_new)
        _file_menu.addAction("Mở...").triggered.connect(self._note_open)
        _file_menu.addAction("Lưu").triggered.connect(self._note_save)
        _file_menu.addAction("Lưu thành...").triggered.connect(self._note_save_as)
        _file_menu.addSeparator()
        _file_menu.addAction("Xóa nội dung").triggered.connect(self.clear_whiteboard)

        _btn_file.setMenu(_file_menu)
        _hdr.addWidget(_btn_file)

        _btn_hide = QtWidgets.QPushButton("✕")
        _btn_hide.setFixedSize(26, 26)
        _btn_hide.setToolTip("Ẩn Ghi Chú")
        _btn_hide.clicked.connect(self.toggle_overlay)
        _hdr.addWidget(_btn_hide)

        _root.addWidget(self.control)

        # ── WhiteBoard content area ───────────────────────────────────────
        self._wb_display = QtWidgets.QTextEdit()
        self._wb_display.setReadOnly(False)
        self._wb_display.setPlaceholderText(
            "Ghi Chú — dùng để ghi chú tự do hoặc lưu nội dung phụ trợ khi chat với Hieusugoi."
        )
        self._wb_display.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: none;
                font-family: "Cambria", "Yu Gothic UI", "Meiryo", serif;
                font-size: 14px;
                color: #1e2a3a;
                padding: 16px 18px;
            }
            QScrollBar:vertical { width: 8px; background: #f0f3f8; }
            QScrollBar::handle:vertical {
                background: #c0cde0; border-radius: 4px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        _root.addWidget(self._wb_display, 1)
        self._wb_display.textChanged.connect(self._note_mark_modified)

        # ── Compat stubs (referenced by other methods in this class) ───────
        self.menu_button = MenuButton()
        self.menu_button.setVisible(False)
        # mode_selector stub (keeps change_app_mode sync working)
        self.mode_selector = None
        # Note: self.menu_button.setMenu() is called below after setup_menu is built
        if ModeSelectorWidget is not None:
            try:
                self.mode_selector = ModeSelectorWidget(initial_mode=self.app_mode)
                self.mode_selector.mode_changed.connect(self.change_app_mode)
            except Exception:
                self.mode_selector = None

        self.auth_status_button = QtWidgets.QPushButton("Login")
        self.auth_status_button.setVisible(False)
        self.auth_status_button.clicked.connect(self.open_login_dialog)

        self.mini_result_label = QtWidgets.QLabel("")
        self.mini_result_label.setVisible(False)

        self.lang_combo = QtWidgets.QComboBox()
        self.lang_combo.setVisible(False)
        self.lang_combo.addItems(["JP → VI", "EN → VI", "VI → EN", "VI → JP"])
        self.lang_combo.currentTextChanged.connect(self.change_language_mode)

        self.btn_speaker = QtWidgets.QPushButton("🔊")
        self.btn_speaker.setVisible(False)
        self.btn_speaker.clicked.connect(self.toggle_tts_enabled)
        self.update_speaker_tooltip()

        self.ocr_status_label = QtWidgets.QLabel("Copy")
        self.ocr_status_label.setVisible(False)

        self.btn_minimize = QtWidgets.QPushButton("−")
        self.btn_minimize.setVisible(False)
        self.btn_minimize.clicked.connect(self.minimize_all)

        self.btn_close = QtWidgets.QPushButton("×")
        self.btn_close.setVisible(False)
        self.btn_close.clicked.connect(self.close_all)

        # Menu actions (used by toggle_auto_copy, update_auth_status_label, etc.)
        self.setup_menu = QtWidgets.QMenu(self)
        self.language_menu = self.setup_menu.addMenu("Language")
        self.action_lang_jp_vi = self.language_menu.addAction("JP → VI")
        self.action_lang_en_vi = self.language_menu.addAction("EN → VI")
        self.action_lang_vi_en = self.language_menu.addAction("VI → EN")
        self.action_lang_vi_jp = self.language_menu.addAction("VI → JP")
        for _a in [self.action_lang_jp_vi, self.action_lang_en_vi,
                   self.action_lang_vi_en, self.action_lang_vi_jp]:
            if _a is not None:
                _a.setCheckable(True)
        self.action_lang_jp_vi.setChecked(True)
        self.action_lang_jp_vi.triggered.connect(lambda: self.set_language_from_menu("JP → VI"))
        self.action_lang_en_vi.triggered.connect(lambda: self.set_language_from_menu("EN → VI"))
        self.action_lang_vi_en.triggered.connect(lambda: self.set_language_from_menu("VI → EN"))
        self.action_lang_vi_jp.triggered.connect(lambda: self.set_language_from_menu("VI → JP"))

        self.panel_menu = self.setup_menu.addMenu("Panel")
        self.action_panel_left = self.panel_menu.addAction("Left")
        self.action_panel_left.setCheckable(True)
        self.action_panel_left.setChecked(True)
        self.action_panel_left.triggered.connect(lambda: self.set_panel_side("left"))
        self.action_panel_right = self.panel_menu.addAction("Right")
        self.action_panel_right.setCheckable(True)
        self.action_panel_right.triggered.connect(lambda: self.set_panel_side("right"))
        self.panel_menu.addSeparator()
        self.action_panel = self.panel_menu.addAction("Hide Panel")
        self.action_panel.setCheckable(True)
        self.action_panel.triggered.connect(self.toggle_panel_collapse)

        self.tts_voice_menu = self.setup_menu.addMenu("Voice")
        self.action_voice_female = self.tts_voice_menu.addAction("Female")
        self.action_voice_female.setCheckable(True)
        self.action_voice_female.setChecked(True)
        self.action_voice_female.triggered.connect(lambda: self.set_tts_voice("female"))
        self.action_voice_male = self.tts_voice_menu.addAction("Male")
        self.action_voice_male.setCheckable(True)
        self.action_voice_male.triggered.connect(lambda: self.set_tts_voice("male"))
        self.tts_voice_menu.addSeparator()
        self.tts_speed_menu = self.tts_voice_menu.addMenu("Speed")
        self.action_speed_75  = self.tts_speed_menu.addAction("75%")
        self.action_speed_100 = self.tts_speed_menu.addAction("100%")
        self.action_speed_125 = self.tts_speed_menu.addAction("125%")
        for _a in [self.action_speed_75, self.action_speed_100, self.action_speed_125]:
            if _a is not None:
                _a.setCheckable(True)
        self.action_speed_100.setChecked(True)
        self.action_speed_75.triggered.connect(lambda: self.set_tts_rate(75))
        self.action_speed_100.triggered.connect(lambda: self.set_tts_rate(100))
        self.action_speed_125.triggered.connect(lambda: self.set_tts_rate(125))

        self.setup_menu.addSeparator()
        self.action_information = self.setup_menu.addAction("Information")
        self.action_information.triggered.connect(self.show_information_dialog)
        self.action_check_update = self.setup_menu.addAction("Kiểm tra cập nhật")
        self.action_check_update.triggered.connect(self.check_update)
        self.action_logout = self.setup_menu.addAction("Logout")
        self.action_logout.triggered.connect(self.logout)
        self.setup_menu.addSeparator()
        self.action_auto_copy = self.setup_menu.addAction("Auto Copy: ON")
        self.action_auto_copy.setCheckable(True)
        self.action_auto_copy.setChecked(True)
        self.action_auto_copy.triggered.connect(self.toggle_auto_copy)

        self.menu_button.setMenu(self.setup_menu)

        # Floating overlays (message toast + quick popup)
        self.quick_popup = QtWidgets.QLabel("", self)
        self.quick_popup.setStyleSheet("""
            QLabel {
                background-color: rgba(255,255,230,235); color: #222;
                border: 1px solid #d0c080; border-radius: 6px; padding: 4px 8px;
                font-family: "Cambria","Yu Gothic UI","Meiryo",serif; font-size: 13px;
            }
        """)
        self.quick_popup.hide()

        self.message = QtWidgets.QLabel("", self)
        self.message.setWordWrap(True)
        self.message.setMaximumWidth(320)
        self.message.setStyleSheet("""
            QLabel {
                background-color: rgba(30,30,30,220); color: white; padding: 8px;
                border-radius: 8px; font-size: 13px; border: 1px solid #808080;
            }
        """)
        self.message.hide()

        # Right-edge resize handle — 6px strip (width only)
        self._resize_handle = QtWidgets.QWidget(self)
        self._resize_handle.setCursor(QtCore.Qt.SizeHorCursor)  # type: ignore[attr-defined]
        self._resize_handle.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)  # type: ignore[attr-defined]
        self._resize_handle.installEventFilter(self)
        self._position_resize_handle()


    # ── WhiteBoard methods ──────────────────────────────────────────────────

    def update_whiteboard(self, text: str):
        """Cập nhật nội dung Ghi Chú theo lập trình — không đánh dấu modified."""
        try:
            if hasattr(self, '_wb_display') and self._wb_display:
                self._wb_display.blockSignals(True)
                self._wb_display.setPlainText(str(text))
                self._wb_display.moveCursor(QtGui.QTextCursor.Start)
                self._wb_display.blockSignals(False)
        except Exception:
            pass

    def append_whiteboard(self, text: str):
        """Thêm nội dung vào cuối Ghi Chú theo lập trình — không đánh dấu modified."""
        try:
            if hasattr(self, '_wb_display') and self._wb_display:
                self._wb_display.blockSignals(True)
                self._wb_display.moveCursor(QtGui.QTextCursor.End)
                self._wb_display.insertPlainText(str(text))
                self._wb_display.blockSignals(False)
        except Exception:
            pass

    def clear_whiteboard(self):
        """Xóa toàn bộ nội dung Ghi Chú — hỏi xác nhận nếu có nội dung."""
        try:
            if not (hasattr(self, '_wb_display') and self._wb_display):
                return
            if self._wb_display.toPlainText().strip():
                reply = QtWidgets.QMessageBox.question(
                    self, "Xóa nội dung",
                    "Bạn có chắc muốn xóa toàn bộ nội dung Ghi Chú?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No,
                )
                if reply != QtWidgets.QMessageBox.Yes:
                    return
            self._wb_display.blockSignals(True)
            self._wb_display.clear()
            self._wb_display.blockSignals(False)
            self._note_modified = False
        except Exception:
            pass

    # ── Ghi Chú file management ────────────────────────────────────────────

    def _note_mark_modified(self):
        self._note_modified = True

    def _note_update_title(self):
        if hasattr(self, '_note_title_label'):
            if self._note_file_path:
                self._note_title_label.setText(
                    "Ghi Chú — " + os.path.basename(self._note_file_path)
                )
            else:
                self._note_title_label.setText("Ghi Chú")

    def _note_new(self):
        if self._note_modified:
            reply = QtWidgets.QMessageBox.question(
                self, "Ghi Chú mới",
                "Nội dung chưa được lưu. Tiếp tục sẽ mất nội dung hiện tại.\nBạn có muốn tiếp tục không?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply != QtWidgets.QMessageBox.Yes:
                return
        if hasattr(self, '_wb_display') and self._wb_display:
            self._wb_display.blockSignals(True)
            self._wb_display.clear()
            self._wb_display.blockSignals(False)
        self._note_file_path = None
        self._note_modified  = False
        self._note_update_title()

    def _note_open(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Mở file Ghi Chú",
            os.path.expanduser("~"),
            "Text files (*.txt *.md);;All files (*.*)",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            if hasattr(self, '_wb_display') and self._wb_display:
                self._wb_display.blockSignals(True)
                self._wb_display.setPlainText(content)
                self._wb_display.moveCursor(QtGui.QTextCursor.Start)
                self._wb_display.blockSignals(False)
            self._note_file_path = path
            self._note_modified  = False
            self._note_update_title()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Lỗi mở file", f"Không thể mở file:\n{e}")

    def _note_save(self):
        if self._note_file_path:
            self._note_write_file(self._note_file_path)
        else:
            self._note_save_as()

    def _note_save_as(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Lưu Ghi Chú thành",
            os.path.expanduser("~"),
            "Text file (*.txt);;Markdown (*.md);;All files (*.*)",
        )
        if path:
            self._note_write_file(path)

    def _note_write_file(self, path):
        try:
            content = self._wb_display.toPlainText() if (hasattr(self, '_wb_display') and self._wb_display) else ""
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            self._note_file_path = path
            self._note_modified  = False
            self._note_update_title()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Lỗi lưu file", f"Không thể lưu file:\n{e}")


    def install_perf_hooks(self):
        """Add timing logs around TranslatorAI without changing its logic.

        This wraps the method normally used by TranslateWorker to call TranslatorAI.
        If your TranslatorAI uses a different method name, add it to candidate_methods.
        """
        candidate_methods = [
            "translate",
            "translate_text",
            "run",
            "ask",
            "request_translation",
        ]

        for method_name in candidate_methods:
            if not hasattr(self.translator, method_name):
                continue

            original_method = getattr(self.translator, method_name)
            if getattr(original_method, "_perf_wrapped", False):
                return

            def timed_method(*args, __original_method=original_method, __method_name=method_name, **kwargs):
                t_api = time.perf_counter()
                try:
                    return __original_method(*args, **kwargs)
                finally:
                    # This measures the TranslatorAI call used by TranslateWorker.
                    # In most current designs this is the OpenAI/API waiting time.
                    perf_log("openai_api_call", t_api)

            timed_method._perf_wrapped = True
            setattr(self.translator, method_name, timed_method)
            print(f"[PERF] TranslatorAI hook installed: {method_name}()")
            return

        print("[PERF] Warning: no TranslatorAI method was hooked for openai_api_call timing")

    def open_api_key_dialog(self):
        dialog = APIKeyDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.translator.set_api_key(dialog.api_key())
            self.show_message("OpenAI API Key đã được lưu vào AppData.")

    def load_auth_session(self):
        session = self.session_manager.load_session()
        self.session = session
        self.logged_in = bool(session and session.get("access_token"))
        self.license_validated_today = bool(self.logged_in and self.session_manager.is_session_current(session))
        self.needs_license_validation = bool(self.logged_in and not self.license_validated_today)
        self.update_auth_status_label()

        if self.logged_in:
            if self.license_validated_today:
                print("[AUTH] Session loaded: license valid for today")
            else:
                print("[AUTH] Session loaded: license check deferred to first lookup")
        else:
            print("[AUTH] No authenticated session found")

    def is_logged_in(self) -> bool:
        return self.logged_in and bool(self.session and self.session.get("access_token"))

    def license_checked_today(self) -> bool:
        return self.logged_in and bool(self.session and self.session_manager.is_session_current(self.session))

    def needs_license_validation_today(self) -> bool:
        return self.logged_in and bool(self.session and not self.session_manager.is_session_current(self.session))

    def get_session_username(self) -> str:
        if not self.session:
            return ""

        username = self.session.get("username")
        if username:
            return str(username)

        email = self.session.get("user_email") or ""
        if "@" in email:
            return email.split("@", 1)[0]
        return email

    def update_auth_status_label(self):
        if self.is_logged_in():
            username = self.get_session_username() or "User"
            self.auth_status_button.setText(username)
            self.auth_status_button.setEnabled(False)
            if hasattr(self, "action_logout"):
                self.action_logout.setEnabled(True)
        else:
            self.auth_status_button.setText("Login")
            self.auth_status_button.setEnabled(True)
            if hasattr(self, "action_logout"):
                self.action_logout.setEnabled(False)
        if self.panel and hasattr(self.panel, "sync_toolbar"):
            self.panel.sync_toolbar()

    def open_login_dialog(self) -> bool:
        if self.is_logged_in():
            return True

        dialog = LoginDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.session = self.session_manager.load_session() or dialog.session
            self.logged_in = bool(self.session and self.session.get("access_token"))
            self.license_validated_today = self.logged_in
            self.needs_license_validation = False
            self.login_prompted = False
            self.license_validation_failed = False
            self.update_auth_status_label()
            print("DEBUG: Auth success - login accepted")
            self.show_message("Đăng nhập thành công. Translation đã được kích hoạt.")
            self.ocr_enabled = True
            return True

        self.show_message("Đăng nhập bị hủy. Bạn vẫn có thể xem lịch sử.")
        return False

    def validate_license_for_session(self) -> bool:
        if not self.is_logged_in():
            return False

        if self.license_validation_failed:
            return False

        access_token = self.session.get("access_token")
        if not access_token:
            return False

        self.lookup_auth_in_progress = True
        validation_result = self.validator.validate(access_token)
        self.lookup_auth_in_progress = False

        if validation_result.get("success"):
            self.session = self.session_manager.update_last_license_check(
                self.session,
                validation_result.get("server_date") or None,
            )
            self.logged_in = True
            self.license_validated_today = True
            self.needs_license_validation = False
            self.license_validation_failed = False
            self.update_auth_status_label()
            print("DEBUG: Auth success - license validated for today")
            return True

        self.license_validation_failed = True
        self.show_message("License validation failed. Please login again.")
        return False

    def ensure_authenticated_for_lookup(self) -> bool:
        if self.license_checked_today():
            return True

        if self.needs_license_validation_today():
            return self.validate_license_for_session()

        return self.is_logged_in()

    def dock_panel(self):
        """Show/hide panel and sync overlay position. Never resizes the panel."""
        if not self.panel:
            return

        if self.panel_collapsed:
            self.panel.hide()
            return

        self.panel.show()
        self.update_overlay_position()

    def update_overlay_position(self):
        """Dock Ghi Chú adjacent to panel. Always absolute from panel geometry — no delta."""
        if not self.panel or not self.overlay_enabled:
            return
        panel_geo = self.panel.geometry()
        note_x = panel_geo.x() + panel_geo.width()
        note_y = panel_geo.y()
        note_h = panel_geo.height()
        ow = max(self.lp_min_width, self.width())
        self.move(note_x, note_y)
        self.resize(ow, note_h)

    def toggle_overlay(self):
        """Show or hide the overlay window."""
        self.overlay_enabled = not self.overlay_enabled
        _action = getattr(self.panel, "_panel_action_overlay", None) if self.panel else None
        if self.overlay_enabled:
            if self.panel and not self.panel.isMinimized():
                self.show()
                self.update_overlay_position()
            if _action:
                _action.setText("Ghi Chú: ON")
                _action.setChecked(True)
        else:
            self.hide()
            if _action:
                _action.setText("Ghi Chú: OFF")
                _action.setChecked(False)

    def set_overlay_side(self, _side: str):
        # Learning Panel is always fixed to the right — kept for API compat
        pass

    def toggle_auto_copy(self):
        self.auto_copy_enabled = not self.auto_copy_enabled
        label = "Auto Copy: ON" if self.auto_copy_enabled else "Auto Copy: OFF"
        self.action_auto_copy.setText(label)
        self.action_auto_copy.setChecked(self.auto_copy_enabled)
        if self.panel and hasattr(self.panel, "_panel_action_auto_copy"):
            self.panel._panel_action_auto_copy.setText(label)
            self.panel._panel_action_auto_copy.setChecked(self.auto_copy_enabled)

    def _start_mouse_listener(self):
        """macOS: khởi động pynput global mouse listener."""
        if not _PYNPUT_AVAILABLE:
            print("[HOOK] pynput không có sẵn — hiển thị hướng dẫn cài đặt")
            self._show_accessibility_warning(import_error=True)
            return

        def _on_click(x, y, button, pressed):
            if button == _pynput_mouse.Button.left:
                if pressed:
                    self._mac_mouse_press_signal.emit(int(x), int(y))
                else:
                    self._mac_mouse_release_signal.emit(int(x), int(y))

        try:
            self._pynput_listener = _pynput_mouse.Listener(on_click=_on_click)
            self._pynput_listener.start()
            print("[HOOK] pynput mouse listener started")
        except Exception as exc:
            print(f"[HOOK] pynput listener khởi động thất bại: {exc}")
            self._pynput_listener = None
            QtCore.QTimer.singleShot(500, self._show_accessibility_warning)

    def _on_mac_mouse_pressed(self, x: int, y: int):
        """Callback khi nhấn chuột trái — chạy trên main thread qua signal."""
        self._mouse_down_time = time.perf_counter()
        self._mouse_down_pos = (x, y)
        self._last_left_down = True

    def _on_mac_mouse_released(self, x: int, y: int):
        """Callback khi nhả chuột trái — chạy trên main thread qua signal."""
        self._last_left_down = False
        self._mouse_release_pos = (x, y)
        QtCore.QTimer.singleShot(100, self._maybe_auto_copy)

    def _maybe_auto_copy(self):
        if not self.auto_copy_enabled:
            return

        # Guard: overlay drag or resize in progress
        if self.dragging or self.resizing:
            return

        # Guard: debounce 300 ms between auto-copies
        now = time.perf_counter()
        if now - self._auto_copy_last_time < 0.3:
            return

        # Guard: foreground window belongs to this process (Hieusugoi or TranslationPanel)
        if _is_own_app_in_foreground():
            return

        # Guard: too short a press — just a click, not a selection drag
        duration_ms = (now - self._mouse_down_time) * 1000
        if duration_ms < 120:
            return

        # Guard: mouse barely moved — not a selection drag
        if self._mouse_down_pos is not None and self._mouse_release_pos is not None:
            dx = abs(self._mouse_release_pos[0] - self._mouse_down_pos[0])
            dy = abs(self._mouse_release_pos[1] - self._mouse_down_pos[1])
            if dx < 5 and dy < 5:
                return

        self._auto_copy_last_time = now
        self.copy_selected_text()

    def copy_selected_text(self):
        """macOS: gửi Cmd+C để copy selected text vào clipboard."""
        if not _PYNPUT_AVAILABLE:
            return
        try:
            kb = _KeyboardController()
            with kb.pressed(_Key.cmd):
                kb.press('c')
                kb.release('c')
        except Exception as exc:
            print(f"[COPY] copy_selected_text thất bại: {exc}")

    def _show_accessibility_warning(self, import_error: bool = False):
        """Hiển thị hướng dẫn cấp quyền Accessibility cho macOS."""
        if import_error:
            body = (
                "Thư viện <b>pynput</b> chưa được cài đặt.<br><br>"
                "Chạy lệnh sau để cài đặt:<br>"
                "<tt>pip install pynput</tt>"
            )
        else:
            body = (
                "Để Hieusugoi tự động nhận text bạn bôi đen,<br>"
                "hãy cấp quyền <b>Accessibility</b>:<br><br>"
                "1. Mở <b>System Settings</b><br>"
                "2. Vào <b>Privacy &amp; Security → Accessibility</b><br>"
                "3. Bật <b>Hieusugoi</b> trong danh sách<br><br>"
                "Sau khi cấp quyền, khởi động lại Hieusugoi."
            )

        dlg = QtWidgets.QMessageBox(self)
        dlg.setWindowTitle("Cần quyền Accessibility — Hieusugoi")
        dlg.setIcon(QtWidgets.QMessageBox.Warning)
        dlg.setTextFormat(QtCore.Qt.RichText)
        dlg.setText(
            "<b>Hieusugoi cần quyền Accessibility để hoạt động.</b><br><br>"
            + body
        )
        btn_open = dlg.addButton("Mở System Settings", QtWidgets.QMessageBox.ActionRole)
        dlg.addButton("Để sau", QtWidgets.QMessageBox.RejectRole)
        dlg.exec_()
        if dlg.clickedButton() is btn_open:
            try:
                subprocess.Popen([
                    "open",
                    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
                ])
            except Exception:
                pass

    def close_all(self):
        if hasattr(self, "_pynput_listener") and self._pynput_listener is not None:
            try:
                self._pynput_listener.stop()
            except Exception:
                pass

        if hasattr(self, "_clipboard"):
            try:
                self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except Exception:
                pass

        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.wait(1000)

        self.panel.close()
        self.close()

    def logout(self):
        if hasattr(self, "session_manager") and self.session_manager:
            self.session_manager.clear_session()

        self.session = None
        self.logged_in = False
        self.license_validated_today = False
        self.needs_license_validation = False
        self.login_prompted = False
        self.license_validation_failed = False
        self.update_auth_status_label()
        self.show_message("Đã đăng xuất. Vui lòng đăng nhập để sử dụng translation.")
        self.dock_panel()

    def toggle_panel(self):
        if self.panel.isVisible():
            self.panel.hide()
        else:
            self.panel.show()
            self.dock_panel()

    def toggle_panel_collapse(self):
        self.panel_collapsed = not self.panel_collapsed

        if self.panel_collapsed:
            self.panel.hide()
        else:
            self.panel_width = max(300, self.last_panel_width)
            self.panel.show()

        self.dock_panel()
        self._sync_panel_menu_checks()

    def _sync_panel_menu_checks(self) -> None:
        """Luôn giữ đúng 1 trong 3 mục panel được check."""
        hidden = self.panel_collapsed
        if hasattr(self, "action_panel_left"):
            self.action_panel_left.setChecked(not hidden and self.panel_side == "left")
        if hasattr(self, "action_panel_right"):
            self.action_panel_right.setChecked(not hidden and self.panel_side == "right")
        if hasattr(self, "action_panel"):
            self.action_panel.setChecked(hidden)

    def toggle_panel_side(self):
        new_side = "left" if self.panel_side == "right" else "right"
        self.set_panel_side(new_side)

    def set_panel_side(self, side: str):
        self.panel_side = side
        if self.panel_collapsed:
            self.panel_collapsed = False
            self.panel_width = max(300, self.last_panel_width)
            self.panel.show()
        self.dock_panel()
        if self.panel:
            self.panel.update()
        self._sync_panel_menu_checks()

    def show_information_dialog(self):
        try:
            from hieusugoi.config import APP_VERSION, APP_PLAN
        except Exception:
            APP_VERSION = "v2.2.1"
            APP_PLAN    = "Trial version"

        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Hieusugoi — Information")
        msg.setTextFormat(QtCore.Qt.RichText)
        msg.setText(
            "<b>App:</b> Hieusugoi macOS<br>"
            f"<b>Version:</b> {APP_VERSION}<br>"
            f"<b>Plan:</b> {APP_PLAN}"
        )
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()

    def check_update(self):
        """Kiểm tra phiên bản mới từ UPDATE_MANIFEST_URL."""
        try:
            from hieusugoi.config import UPDATE_MANIFEST_URL
        except Exception:
            UPDATE_MANIFEST_URL = ""

        if not UPDATE_MANIFEST_URL:
            QtWidgets.QMessageBox.information(
                self, "Kiểm tra cập nhật",
                "Chức năng kiểm tra cập nhật chưa được cấu hình.",
            )
            return

        def _parse_version(v):
            try:
                return tuple(int(x) for x in v.lstrip("v").split("."))
            except Exception:
                return (0,)

        try:
            req = urllib.request.Request(UPDATE_MANIFEST_URL, headers={"User-Agent": "HieusugoiApp"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            latest       = data.get("latest_version", "")
            download_url = data.get("download_url", "")
            notes        = data.get("release_notes", "")

            if latest and _parse_version(latest) > _parse_version(APP_VERSION):
                msg = QtWidgets.QMessageBox(self)
                msg.setWindowTitle("Có bản cập nhật mới")
                msg.setTextFormat(QtCore.Qt.RichText)
                body = (
                    f"<b>Phiên bản hiện tại:</b> {APP_VERSION}<br>"
                    f"<b>Phiên bản mới:</b> {latest}<br><br>"
                )
                if notes:
                    import html as _html
                    body += f"<b>Nội dung cập nhật:</b><br>{_html.escape(notes).replace(chr(10), '<br>')}"
                msg.setText(body)
                msg.setIcon(QtWidgets.QMessageBox.Information)
                btn_dl   = msg.addButton("Tải bản cập nhật", QtWidgets.QMessageBox.AcceptRole)
                msg.addButton("Để sau", QtWidgets.QMessageBox.RejectRole)
                msg.exec_()
                if msg.clickedButton() is btn_dl and download_url:
                    QtGui.QDesktopServices.openUrl(QtCore.QUrl(download_url))
            else:
                QtWidgets.QMessageBox.information(
                    self, "Kiểm tra cập nhật",
                    f"Bạn đang dùng phiên bản mới nhất ({APP_VERSION}).",
                )
        except Exception:
            QtWidgets.QMessageBox.information(
                self, "Kiểm tra cập nhật",
                "Không thể kiểm tra cập nhật lúc này.\nVui lòng thử lại sau.",
            )

    def resizeEvent(self, event):
        self.update_mask()
        self._position_resize_handle()
        super().resizeEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)

    def set_target_language(self, lang: str):
        if lang not in TARGET_LANGUAGES:
            return
        self.target_language = lang
        self.translator.set_target_language(lang)
        try:
            cfg = load_app_config()
            cfg["target_language"] = lang
            save_app_config(cfg)
        except Exception:
            pass
        if self.panel and hasattr(self.panel, "_panel_target_combo"):
            self.panel._panel_target_combo.blockSignals(True)
            self.panel._panel_target_combo.setCurrentText(lang)
            self.panel._panel_target_combo.blockSignals(False)
        self.show_message(f"Target: {lang}")

    def repeat_reading(self):
        result = self._last_translation_result
        text = self._last_translated_text
        if not result and not text:
            return
        reading = self.extract_reading_from_result(result)
        if reading and self.has_kana(reading):
            self.start_tts(reading, language="ja-JP")
        elif reading:
            self.start_tts(reading, language=self._tts_lang_for_target())
        elif text:
            if contains_kanji(text) or self.has_kana(text):
                self.start_tts(text, language="ja-JP")
            else:
                self.start_tts(text, language=self._tts_lang_for_target())

    # kept for compatibility — old overlay lang_combo still calls this
    def change_language_mode(self, *args):
        pass

    # === App Mode System ===
    def change_app_mode(self, mode_id: str):
        """
        Chuyển app mode. Được gọi bởi ModeSelectorWidget.
        Deep + Chat: full panel, TTS bật, history hiển thị.
        Quick: chỉ hiển thị Dịch nghĩa, ẩn history.
        """
        if mode_id not in APP_MODE_CONFIG:
            return

        self.app_mode = mode_id
        cfg = get_mode_config(mode_id)

        # Đồng bộ lại widget label nếu call từ nơi khác (không phải từ widget)
        if self.mode_selector is not None:
            self.mode_selector.set_mode(mode_id)

        # Persist vào config.json để nhớ qua lần restart
        self._save_app_mode(mode_id)

        # === App Mode System ===
        if self.panel is not None:
            self.panel.set_app_mode(mode_id)

        self.show_message(f"App Mode: {cfg.name}")

    def _save_app_mode(self, mode_id: str):
        """Load config hiện tại, update đúng key app_mode, ghi lại. Không overwrite key khác."""
        try:
            saved = load_app_config()
            saved["app_mode"] = mode_id
            save_app_config(saved)
        except Exception:
            pass   # lỗi lưu config không làm crash app

    def toggle_lock(self):
        self.locked = not self.locked
        self.btn_lock.setText("Lock: ON" if self.locked else "Lock: OFF")

    def clear_cache(self):
        self.translator.cache.clear()
        self.translator.save_cache()
        self.show_message("Cache đã được xóa")

    def show_message(self, msg):
        self.message.setText(msg)
        self.message.adjustSize()
        self.message.move(20, 65)
        self.message.show()
        QtCore.QTimer.singleShot(2500, self.message.hide)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Solid background + outer border
        painter.setPen(QtGui.QPen(QtGui.QColor("#d8dee9"), 1))
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#f5f7fb")))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

        # Subtle right-edge resize indicator (always visible)
        painter.setPen(QtGui.QPen(QtGui.QColor("#b0c4de"), 2))
        x_r = self.width() - 1
        painter.drawLine(x_r, 4, x_r, self.height() - 4)
    def update_mask(self):
        self.clearMask()

    def _position_resize_handle(self):
        """Keep the right-edge resize strip in sync with the window geometry."""
        if hasattr(self, "_resize_handle"):
            self._resize_handle.setGeometry(
                self.width() - self.resize_margin, 0,
                self.resize_margin, self.height()
            )
            self._resize_handle.raise_()

    def eventFilter(self, obj, event):
        if obj is getattr(self, "_resize_handle", None):
            t = event.type()
            if t == QtCore.QEvent.MouseButtonPress and event.button() == QtCore.Qt.LeftButton:
                self.resizing_width = True
                self.resize_start_global_x = event.globalX()
                self.resize_start_width = self.width()
                return True
            if t == QtCore.QEvent.MouseMove and self.resizing_width:
                delta = event.globalX() - self.resize_start_global_x
                new_w = max(self.lp_min_width, self.resize_start_width + delta)
                self.resize(new_w, self.height())
                return True
            if t == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
                self.resizing_width = False
                return True
        return super().eventFilter(obj, event)

    def is_in_resize_area(self, pos):
        return (
            pos.x() >= self.width() - self.resize_handle_size and
            pos.y() >= self.height() - self.resize_handle_size
        )

    def mousePressEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            # === Right-click replay (deep mode only) ===
            # Gọi handler cho mọi non-left button — _handle_right_click có đủ guards bên trong.
            self._handle_right_click(event)
            return

        pos = event.pos()

        # Only drag from toolbar strip — body area must not move the window
        if pos.y() <= self.control_height:
            child = self.childAt(pos)
            if not isinstance(child, (QtWidgets.QPushButton, QtWidgets.QComboBox)):
                self.dragging = True
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() != QtCore.Qt.LeftButton:
            return

        if self.dragging:
            self.dragging = False
            self.update()
            return

        # v2.0.0: clipboard handles input

    def mouseMoveEvent(self, event):
        if self.dragging:
            new_pos = event.globalPos() - self.drag_pos
            self.move(new_pos)
            self.dock_panel()
            event.accept()

    def show_quick_popup(self, text):
        if not text:
            return

        self.quick_popup.setText(text)
        self.quick_popup.adjustSize()

        # Show popup just below toolbar in the overlay body
        x = 8
        y = self.control_height + 8


        # trﾃ｡nh popup vﾆｰ盻｣t quﾃ｡ mﾃｩp ph蘯｣i
        if x + self.quick_popup.width() > self.width() - 10:
            x = self.width() - self.quick_popup.width() - 10

        if x < 10:
            x = 10

        self.quick_popup.move(x, y)
        self.quick_popup.show()
        self.quick_popup.raise_()

        QtCore.QTimer.singleShot(3500, self.quick_popup.hide)

    def translate_selected_text(self, text, request_start=None, selected_at=None):
        self.perf_translate_start = time.perf_counter()

        if request_start is not None:
            self.perf_request_start = request_start

        if selected_at is not None:
            self.perf_selected_at = selected_at
            print(f"[PERF] delay_before_translate: {(self.perf_translate_start - selected_at) * 1000:.1f} ms")


        t_auth = time.perf_counter()
        if not self.ensure_authenticated_for_lookup():
            perf_log("auth_check", t_auth)
            if self.is_logged_in():
                self.show_message("Vui lòng xác thực giấy phép trước khi sử dụng OCR/translation.")
            else:
                self.show_message("Vui lòng đăng nhập để sử dụng OCR/translation.")
            return
        perf_log("auth_check", t_auth)

        if not self.panel_collapsed:
            self.panel.show()
            self.panel.raise_()
            self.dock_panel()
            self.panel.show_loading(text)
        else:
            self.mini_result_label.setText("Đang dịch...")

        if self.current_worker and self.current_worker.isRunning():
            self.show_message("Đang dịch nội dung trước, vui lòng đợi...")
            return

        self.perf_worker_start = time.perf_counter()
        self.current_worker = TranslateWorker(self.translator, text)
        self.current_worker.finished_signal.connect(self.on_translation_finished)
        self.current_worker.start()


    def _on_clipboard_changed(self):
        """v2.0.0: Clipboard Copy input.
        Triggered when user copies text (Ctrl+C) from any app.
        Feeds text into the existing translate_selected_text pipeline.
        """
        try:
            text = self._clipboard.text()
        except Exception:
            return

        if not text:
            return
        text = text.strip()
        if not text:
            return
        if text == self._last_clipboard_text:
            return

        self._last_clipboard_text = text
        self.translate_selected_text(text)

    def on_translation_finished(self, text, result):
        t_render = time.perf_counter()

        if self.perf_worker_start is not None:
            perf_log("worker_total", self.perf_worker_start)

        if not result or not result.strip():
            self.show_message("Không nhận được kết quả dịch.")
            perf_log("render_result", t_render)
            if self.perf_request_start is not None:
                perf_log("total_user_wait", self.perf_request_start)
            QtCore.QTimer.singleShot(300, self.clear_selection)
            return

        # Store for Re-read button
        self._last_translated_text = text
        self._last_translation_result = result

        mini = self.make_mini_result(text, result)

        if self.panel_collapsed:
            self.mini_result_label.setText(mini)
        else:
            self.panel.add_result(text, result)
            self.mini_result_label.clear()

        if self.panel and hasattr(self.panel, "set_mini_result"):
            self.panel.set_mini_result(mini)

        perf_log("render_result", t_render)
        if self.perf_request_start is not None:
            perf_log("total_user_wait", self.perf_request_start)

        self.speak_after_translation(text, result)
        self.show_quick_popup(mini)

        QtCore.QTimer.singleShot(300, self.clear_selection)


    def clear_selection(self):
        self.selection_rect = None
        self.update()

    # === Right-click replay (deep mode only) ===

    def replay_last_tts(self):
        """
        Phát lại TTS của lần tra gần nhất.
        Dùng voice gender + speed hiện tại (tts_voice_gender, tts_rate_percent).
        Chỉ được gọi khi app_mode == "deep".
        """
        if not self.last_tts_text:
            self.show_message("No speech to replay")
            return

        # Dùng lại start_tts — đã có guard tts_enabled và worker busy bên trong
        self.start_tts(self.last_tts_text, self.last_tts_language)

    def _handle_right_click(self, event):
        """
        Bộ lọc an toàn cho right-click trên overlay.
        Chỉ trigger replay khi không có thao tác nào đang diễn ra.
        """
        # Guard 1: chỉ hoạt động trong deep và chat mode (tts_enabled=True)
        if self.app_mode not in ("deep", "chat"):
            return

        # Guard 2: không trigger khi đang resize / drag / select OCR
        if self.resizing or self.dragging:
            return


        self.replay_last_tts()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close_all()


def bootstrap_auth() -> bool:
    """Always show login dialog at startup so the full auth init path always runs.
    Returns False → app exits without starting."""
    print("[AUTH] Login dialog required at startup")
    dialog = LoginDialog()
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print("[AUTH] Login success, starting authenticated app")
        return True
    print("[AUTH] Login cancelled -- application will exit")
    return False


def start_authenticated_app(app: QtWidgets.QApplication):
    # v2.0.0: No Tesseract — clipboard-based input
    print("[AUTH] Creating FixedLearningWindow")
    window = FixedLearningWindow()
    window.session_manager = SessionManager()
    window.setWindowIcon(QtGui.QIcon(resource_path("assets/logo.ico")))
    print("[AUTH] Existing session restored, starting authenticated app through full init path")
    return window


if __name__ == "__main__":
    print("DEBUG: Creating QApplication")
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(resource_path("assets/logo.ico")))

    print("[AUTH] Bootstrapping authentication")
    if not bootstrap_auth():
        sys.exit(0)

    print("[AUTH] Starting authenticated app")
    window = start_authenticated_app(app)

    print("[AUTH] Entering app event loop")
    exit_code = app.exec_()

    print(f"DEBUG: App event loop exited with code {exit_code}")
    sys.exit(exit_code)