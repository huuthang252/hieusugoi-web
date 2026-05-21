# -*- coding: utf-8 -*-
"""
Tesseract OCR runtime configuration and setup.
Handles bundled Tesseract deployment and pytesseract initialization.
"""

import os
import shutil
import pytesseract


def prepare_tesseract_runtime(app_data_dir, resource_path_func):
    """
    PyInstaller one-file mode extracts bundled files into a temporary _MEI folder.
    Some Tesseract builds fail to load traineddata reliably from that temp folder.
    To make OCR stable, copy the bundled Tesseract runtime once to AppData and run it there.

    Args:
        app_data_dir: Application data directory path
        resource_path_func: Function to resolve bundled resource paths

    Returns:
        Tuple of (tesseract_exe_path, tessdata_path)
    """
    bundled_root = resource_path_func("tesseract")
    bundled_exe = os.path.join(bundled_root, "tesseract.exe")
    bundled_tessdata = os.path.join(bundled_root, "tessdata")

    runtime_root = os.path.join(app_data_dir, "runtime", "tesseract")
    runtime_exe = os.path.join(runtime_root, "tesseract.exe")
    runtime_tessdata = os.path.join(runtime_root, "tessdata")

    required_langs = ["eng.traineddata", "jpn.traineddata", "vie.traineddata", "osd.traineddata"]

    def runtime_ready():
        return (
            os.path.exists(runtime_exe)
            and os.path.isdir(runtime_tessdata)
            and all(os.path.exists(os.path.join(runtime_tessdata, f)) for f in required_langs)
        )

    # Prefer bundled Tesseract, but copy it to AppData before use.
    if os.path.exists(bundled_exe) and os.path.isdir(bundled_tessdata):
        if not runtime_ready():
            try:
                if os.path.exists(runtime_root):
                    shutil.rmtree(runtime_root)
                shutil.copytree(bundled_root, runtime_root)
            except Exception:
                # If copying fails, still try to run from bundled temp path.
                return bundled_exe, bundled_tessdata
        return runtime_exe, runtime_tessdata

    # Fallback for development machines that already have Tesseract installed.
    return (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files\Tesseract-OCR\tessdata",
    )


def initialize_tesseract(tesseract_path, tessdata_path):
    """
    Initialize pytesseract with Tesseract executable and tessdata paths.

    Args:
        tesseract_path: Path to tesseract.exe
        tessdata_path: Path to tessdata directory
    """
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    os.environ["TESSDATA_PREFIX"] = tessdata_path + os.sep
