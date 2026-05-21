import os
import sys
import shutil
from dataclasses import dataclass, field


# ================= CONFIG / PRODUCTION PATH =================
APP_NAME = "Hieusugoi"
MODEL_NAME = "gpt-4.1-mini"
OCR_INTERVAL_MS = 600
DEFAULT_OPENAI_API_KEY = ""
APP_VERSION = "v2.2.1"
APP_PLAN    = "Trial version"

# Update manifest: JSON endpoint với các field: latest_version, download_url, release_notes
# Để rỗng nếu chưa cấu hình — app sẽ không crash.
UPDATE_MANIFEST_URL = ""  # TODO: đặt URL thực khi server sẵn sàng

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def get_app_data_dir(app_name: str = APP_NAME) -> str:
    """Trả về đường dẫn lưu dữ liệu app theo platform."""
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
    elif sys.platform == "win32":
        return os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), app_name)
    else:
        xdg = os.getenv("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
        return os.path.join(xdg, app_name)


APP_DATA_DIR = get_app_data_dir()
HISTORY_DIR = os.path.join(APP_DATA_DIR, "history")
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
CACHE_FILE = os.path.join(APP_DATA_DIR, "translation_cache.json")

AUDIO_CACHE_DIR = os.path.join(APP_DATA_DIR, "audio_cache")
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)

os.makedirs(APP_DATA_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)


def _migrate_old_app_data() -> None:
    """Copy-only migration: chuyển dữ liệu còn thiếu từ Hieusuge/ → Hieusugoi/.
    Không overwrite file đã có. Không xóa thư mục cũ. Chỉ chạy trên Windows."""
    if sys.platform != "win32":
        return
    old_root = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "Hieusuge")
    if not os.path.isdir(old_root):
        return

    # Single files: copy nếu chưa có ở new dir
    for fname in ("config.json", "translation_cache.json"):
        src = os.path.join(old_root, fname)
        dst = os.path.join(APP_DATA_DIR, fname)
        if os.path.isfile(src) and not os.path.isfile(dst):
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass

    # Subdirs: copy từng file thiếu, không overwrite
    for dname in ("history", "audio_cache"):
        src_dir = os.path.join(old_root, dname)
        dst_dir = os.path.join(APP_DATA_DIR, dname)
        if not os.path.isdir(src_dir):
            continue
        os.makedirs(dst_dir, exist_ok=True)
        for fname in os.listdir(src_dir):
            src_file = os.path.join(src_dir, fname)
            dst_file = os.path.join(dst_dir, fname)
            if os.path.isfile(src_file) and not os.path.isfile(dst_file):
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception:
                    pass


_migrate_old_app_data()


LANG_MODES = {
    "JP → VI": {"ocr": "jpn+eng", "source": "Japanese", "target": "Vietnamese"},
    "EN → VI": {"ocr": "eng", "source": "English", "target": "Vietnamese"},
    "VI → EN": {"ocr": "vie+eng", "source": "Vietnamese", "target": "English"},
    "VI → JP": {"ocr": "vie+eng", "source": "Vietnamese", "target": "Japanese"},
}


# === App Mode System ===
# ModeConfig mô tả toàn bộ behavior của một app mode.
# Các subsystem (TTS, panel, service) đọc flag từ đây — không hard-code mode_id.
@dataclass
class ModeConfig:
    mode_id: str
    name: str           # "Học Sâu"  — tên đầy đủ hiển thị trên UI
    label: str          # "Sâu"      — nhãn ngắn (dự phòng nếu UI chật)

    # Translation panel: kiểm soát từng section hiển thị
    show_original: bool    = True
    show_reading: bool     = True
    show_meaning: bool     = True
    show_explanation: bool = True

    # TTS: mode quick tắt speaker
    tts_enabled: bool      = True

    # API prompt strategy: "full" | "minimal" | "none"
    prompt_style: str      = "full"

    # Cache prefix: "" = dùng key gốc (tương thích cache cũ), "QUICK::" = tách biệt
    cache_prefix: str      = ""

    # Quick popup style: "full" | "minimal" | "none"
    popup_style: str       = "full"

    # Extension fields — thêm mode mới không làm hỏng mode cũ
    ocr_mode: str          = "standard"
    panel_layout: str      = "standard"


# Registry trung tâm của tất cả app modes.
# Thêm mode mới = thêm entry ở đây. Không cần sửa code khác.
APP_MODE_CONFIG: dict = {
    "deep": ModeConfig(
        mode_id          = "deep",
        name             = "Học Sâu",
        label            = "Sâu",
        show_original    = True,
        show_reading     = True,
        show_meaning     = True,
        show_explanation = True,
        tts_enabled      = True,
        prompt_style     = "full",
        cache_prefix     = "",       # key gốc — backward compatible với cache cũ
        popup_style      = "full",
    ),
    "quick": ModeConfig(
        mode_id          = "quick",
        name             = "Dịch Nhanh",
        label            = "Nhanh",
        show_original    = False,
        show_reading     = False,
        show_meaning     = True,
        show_explanation = False,
        tts_enabled      = False,
        prompt_style     = "minimal",
        cache_prefix     = "QUICK::",
        popup_style      = "minimal",
    ),
    "chat": ModeConfig(
        mode_id          = "chat",
        name             = "Chat với Hieusugoi",
        label            = "Chat",
        show_original    = True,
        show_reading     = True,
        show_meaning     = True,
        show_explanation = True,
        tts_enabled      = True,
        prompt_style     = "full",
        cache_prefix     = "CHAT::",
        popup_style      = "full",
        panel_layout     = "standard",
    ),
}

DEFAULT_APP_MODE = "deep"


def get_mode_config(mode_id: str) -> ModeConfig:
    """Trả về ModeConfig cho mode_id, fallback về deep nếu không tìm thấy."""
    return APP_MODE_CONFIG.get(mode_id, APP_MODE_CONFIG[DEFAULT_APP_MODE])
