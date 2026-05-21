import os
import sys
import hashlib
import subprocess

from PyQt5 import QtCore
from openai import OpenAI

from hieusugoi.config import AUDIO_CACHE_DIR, DEFAULT_OPENAI_API_KEY
from hieusugoi.storage.app_config import load_app_config


class TTSWorker(QtCore.QThread):
    play_signal = QtCore.pyqtSignal(str)

    def __init__(self, text, gender="female", rate_percent=100, language="en-US"):
        super().__init__()
        self.text = text.strip()
        self.gender = gender
        self.rate_percent = rate_percent
        self.language = language

    def cache_file_path(self):
        raw = f"TTS::{self.language}::{self.text}::{self.gender}::{self.rate_percent}"
        key = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        return os.path.join(AUDIO_CACHE_DIR, f"{key}.mp3")

    def voice_name(self):
        if self.gender == "male":
            return "onyx"
        return "nova"

    def speed_value(self):
        if self.rate_percent == 75:
            return 0.75
        if self.rate_percent == 125:
            return 1.25
        return 1.0

    def speech_instructions(self):
        if self.language == "ja-JP":
            return "Read this as Japanese with natural Japanese pronunciation. Do not use Chinese pronunciation."
        if self.language == "en-US":
            return "Read this as English with natural English pronunciation."
        if self.language == "vi-VN":
            return "Read this as Vietnamese with natural Vietnamese pronunciation."
        return None

    def generate_ai_voice(self, path):
        config = load_app_config()
        api_key = (
            config.get("openai_api_key")
            or os.getenv("OPENAI_API_KEY")
            or DEFAULT_OPENAI_API_KEY
        )

        if not api_key:
            return False

        client = OpenAI(api_key=api_key)

        speech_args = {
            "model": "gpt-4o-mini-tts",
            "voice": self.voice_name(),
            "input": self.text,
            "speed": self.speed_value(),
            "response_format": "mp3",
        }
        instructions = self.speech_instructions()
        if instructions:
            speech_args["instructions"] = instructions

        with client.audio.speech.with_streaming_response.create(**speech_args) as response:
            response.stream_to_file(path)

        return os.path.exists(path) and os.path.getsize(path) > 0

    def play_audio(self, path):
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", path])
            elif sys.platform == "win32":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass

    def run(self):
        if not self.text:
            return

        try:
            audio_path = self.cache_file_path()

            if not os.path.exists(audio_path):
                ok = self.generate_ai_voice(audio_path)
                if not ok:
                    return

            self.play_signal.emit(audio_path)

        except Exception:
            pass
