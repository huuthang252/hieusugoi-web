import os
import json
import datetime
from typing import Any, Dict, Optional

from hieusugoi.config import get_app_data_dir

SESSION_FILENAME = "session.json"

class SessionManager:
    def __init__(self) -> None:
        self.session_dir = get_app_data_dir()
        os.makedirs(self.session_dir, exist_ok=True)
        self.session_file = os.path.join(self.session_dir, SESSION_FILENAME)

    def load_session(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.session_file):
            return None

        try:
            with open(self.session_file, "r", encoding="utf-8") as handle:
                data = json.load(handle)

            if not isinstance(data, dict):
                return None

            return data
        except Exception:
            return None

    def save_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        os.makedirs(self.session_dir, exist_ok=True)

        if "last_license_check" not in session or session["last_license_check"] is None:
            session["last_license_check"] = self._today_str()

        with open(self.session_file, "w", encoding="utf-8") as handle:
            json.dump(session, handle, indent=2, ensure_ascii=False)

        return session

    def clear_session(self) -> None:
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
        except Exception:
            pass

    def update_last_license_check(self, session: Dict[str, Any], date_str: Optional[str] = None) -> Dict[str, Any]:
        session["last_license_check"] = date_str or self._today_str()
        return self.save_session(session)

    def is_session_current(self, session: Dict[str, Any]) -> bool:
        return session.get("last_license_check") == self._today_str()

    def is_logged_in_today(self, session: Dict[str, Any]) -> bool:
        """True nếu user đã nhập credentials và login thành công hôm nay."""
        return bool(session.get("last_login_date") == self._today_str())

    def mark_login_today(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Ghi last_login_date = hôm nay và persist."""
        session["last_login_date"] = self._today_str()
        return self.save_session(session)

    def _today_str(self) -> str:
        return datetime.date.today().isoformat()
