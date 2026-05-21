import os
import json
import unicodedata

import requests

from hieusugoi.config import CACHE_FILE
from hieusugoi.ocr.text_cleanup import contains_japanese, normalize_selected_ocr_text
from hieusugoi.storage.app_config import load_app_config, save_app_config


TARGET_LANGUAGES = [
    "English", "Vietnamese", "Japanese", "Korean", "Chinese",
    "French", "German", "Spanish", "Portuguese", "Thai",
]

# Output labels per target language: original / reading / translation / explanation
TARGET_LABELS = {
    "English":    ("Original:",           "Reading:",          "Translation:",    "Explanation:"),
    "Vietnamese": ("Nội dung gốc:",       "Cách đọc:",         "Dịch nghĩa:",     "Diễn giải:"),
    "Japanese":   ("原文:",               "読み方:",            "翻訳:",           "解説:"),
    "Korean":     ("원문:",               "읽는 법:",           "번역:",           "설명:"),
    "Chinese":    ("原文:",               "读音:",              "翻译:",           "说明:"),
    "French":     ("Texte original:",     "Prononciation:",    "Traduction:",     "Explication:"),
    "German":     ("Originaltext:",       "Aussprache:",       "Übersetzung:",    "Erklärung:"),
    "Spanish":    ("Texto original:",     "Pronunciación:",    "Traducción:",     "Explicación:"),
    "Portuguese": ("Texto original:",     "Pronúncia:",        "Tradução:",       "Explicação:"),
    "Thai":       ("ข้อความต้นฉบับ:",    "การออกเสียง:",      "การแปล:",         "คำอธิบาย:"),
}

ALL_READING_LABELS = [v[1] for v in TARGET_LABELS.values()]
ALL_TRANSLATION_LABELS = [v[2] for v in TARGET_LABELS.values()]


class TranslatorAI:
    def __init__(self):
        self.cache = self.load_cache()
        self.target_lang = "English"
        self.server_url = "https://www.hieusugoi.com/api/translate"

    def set_target_language(self, target: str):
        self.target_lang = target

    # kept for backwards compat (called by old change_language_mode paths)
    def set_language(self, source, target):
        self.target_lang = target

    def cache_key(self, text):
        return f"auto->{self.target_lang}::{text.strip()}"

    def load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_cache(self):
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def should_skip(self, text):
        text = text.strip()
        if text.isdigit():
            return True
        if len(text) <= 1 and text.isascii():
            return True
        return False

    def _labels(self):
        return TARGET_LABELS.get(self.target_lang, TARGET_LABELS["English"])

    def translate_text(self, text):
        text = text.strip()
        if not text:
            return ""

        if self.should_skip(text):
            orig, rdg, trn, exp = self._labels()
            return (
                f"{orig} {text}\n"
                f"{rdg}\n"
                f"{trn} (particle / symbol / number)\n"
                f"{exp} Usually no translation needed."
            )

        key = self.cache_key(text)
        if key in self.cache:
            return self.cache[key]

        text = unicodedata.normalize("NFKC", text.strip())
        text = text.replace("竿・", "'")

        orig, rdg, trn, exp = self._labels()

        prompt = f"""You are a translation assistant.

Input text (language unknown — detect automatically):
{text}

Task: Detect the source language, then translate and explain in {self.target_lang}.

Rules:
- {orig} copy the input text exactly.
- {rdg} write pronunciation/reading (hiragana for Japanese, IPA for English/French/German/Spanish/Portuguese, romanisation for Korean/Chinese/Thai). Leave blank if source is {self.target_lang} or reading is not useful.
- {trn} write a natural, concise translation in {self.target_lang}. Max 1–2 sentences.
- {exp} write one brief contextual note in {self.target_lang}.
- Do not add anything outside the four lines.

Output format (use exactly these labels, one per line):
{orig}
{rdg}
{trn}
{exp}
"""

        try:
            response = requests.post(
                self.server_url,
                json={"text": prompt},
                timeout=20
            )
            if response.status_code == 200:
                result = response.json().get("result", "").strip()
            else:
                result = f"Server error: {response.status_code}"
        except Exception as e:
            result = f"Connection error:\n{e}"

        self.cache[key] = result
        self.save_cache()
        return result

    # === JLPT Fill-in (unchanged) ===
    def translate_with_jlpt_prompt(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""

        key = f"JLPT_FILL::{text}"
        if key in self.cache:
            return self.cache[key]

        from hieusugoi.jlpt import parse_choices, build_closed_choice_prompt, validate_answer
        choices = parse_choices(text)
        prompt  = build_closed_choice_prompt(text, choices)

        try:
            response = requests.post(
                self.server_url,
                json={"text": prompt},
                timeout=20
            )
            if response.status_code == 200:
                result = response.json().get("result", "").strip()
            else:
                result = f"Server error: {response.status_code}"
        except Exception as e:
            result = f"Connection error:\n{e}"

        if choices:
            result = validate_answer(result, choices)

        self.cache[key] = result
        self.save_cache()
        return result

    # --- legacy OCR helpers (kept so nothing breaks if still imported) ---
    def should_ai_clean_ocr_text(self, text):
        return False

    def clean_ocr_text_with_ai(self, text):
        return normalize_selected_ocr_text(text) if text else text
