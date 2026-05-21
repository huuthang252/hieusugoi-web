import datetime
import json
import os

from hieusugoi.config import HISTORY_DIR


def today_date_str():
    return datetime.date.today().strftime("%Y-%m-%d")


def history_file_path(date_str=None):
    date_str = date_str or today_date_str()
    return os.path.join(HISTORY_DIR, f"{date_str}.json")


def load_history_records(date_str=None):
    path = history_file_path(date_str)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def append_history_record(record):
    date_str = record.get("date") or today_date_str()
    records = load_history_records(date_str)
    records.append(record)
    try:
        with open(history_file_path(date_str), "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
