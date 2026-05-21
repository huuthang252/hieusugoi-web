import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# === Remember credentials — keyring (Windows Credential Manager) ===
try:
    import keyring as _keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

_KEYRING_SERVICE = "Hieusugoi"


def _load_keyring_password(email: str) -> str:
    if not _KEYRING_AVAILABLE or not email:
        return ""
    try:
        return _keyring.get_password(_KEYRING_SERVICE, email) or ""
    except Exception:
        return ""


def _save_keyring_password(email: str, password: str) -> None:
    if not _KEYRING_AVAILABLE or not email:
        return
    try:
        _keyring.set_password(_KEYRING_SERVICE, email, password)
    except Exception:
        pass


def _clear_keyring_password(email: str) -> None:
    if not _KEYRING_AVAILABLE or not email:
        return
    try:
        _keyring.delete_password(_KEYRING_SERVICE, email)
    except Exception:
        pass

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

from typing import Any, Dict, Optional

from PyQt5 import QtWidgets, QtCore

from hieusugoi.auth.session_manager import SessionManager
from hieusugoi.auth.license_validator import LicenseValidator


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Hieusugoi Desktop Login")
        self.setModal(True)
        self.setFixedSize(360, 255)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("Please sign in to continue")
        title.setAlignment(QtCore.Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setClearButtonEnabled(True)
        layout.addWidget(self.email_input)

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setClearButtonEnabled(True)
        layout.addWidget(self.password_input)

        self.status_label = QtWidgets.QLabel("Enter your Supabase email and password.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #444444; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self.attempt_login)
        layout.addWidget(self.login_button)

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        # === Remember credentials ===
        # "Save information" lưu cả email (session.json) và password (Windows Credential Manager / keyring).
        # Nếu keyring chưa cài: chỉ lưu email, password không được pre-fill.
        # Cài keyring: pip install keyring
        remember_row = QtWidgets.QHBoxLayout()
        self.remember_email_cb = QtWidgets.QCheckBox("Save information")
        if not _KEYRING_AVAILABLE:
            self.remember_email_cb.setToolTip(
                "Email sẽ được lưu. Cài 'keyring' để lưu mật khẩu tự động."
            )
        remember_row.addWidget(self.remember_email_cb)
        remember_row.addStretch()
        layout.addLayout(remember_row)

        self.session_manager = SessionManager()
        self.validator = LicenseValidator()
        self.session: Optional[Dict[str, Any]] = None

        self._load_remembered_credentials()

    def attempt_login(self) -> None:
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            self.set_status("Email and password are required.", error=True)
            return

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            self.set_status("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables.", error=True)
            return

        self.set_loading(True)
        auth_result = self.sign_in_with_password(email, password, supabase_url, supabase_key)
        self.set_loading(False)

        if not auth_result.get("success"):
            reason = auth_result.get("reason") or "Login failed."
            self.set_status(reason, error=True)
            return

        session_data = auth_result["session"]
        if not session_data:
            self.set_status("Failed to retrieve session from Supabase.", error=True)
            return

        validation_result = self.validator.validate(session_data["access_token"])
        if not validation_result["success"]:
            self.set_status(f"License validation failed: {validation_result['reason']}", error=True)
            return

        validation_user = validation_result.get("user") or {}

        username = (
            validation_user.get("username")
            or session_data.get("username")
            or email.split("@", 1)[0]
        )

        print("SESSION DATA =", session_data)
        print("VALIDATION RESULT =", validation_result)
        print("USERNAME =", username)
        save_info = self.remember_email_cb.isChecked()
        saved_session = {
            "access_token": session_data["access_token"],
            "refresh_token": session_data.get("refresh_token", ""),
            "last_license_check": validation_result.get("server_date") or self._today_str(),
            "last_login_date": self._today_str(),
            "user_email": email,
            "username": username,
            "last_login_email": email,
            "remember_email": save_info,
            "remember_password": save_info,
        }
        self.session_manager.save_session(saved_session)
        if save_info:
            _save_keyring_password(email, password)  # no-op nếu keyring chưa cài
        else:
            _clear_keyring_password(email)
        self.session = saved_session
        self.accept()

    def sign_in_with_password(
        self,
        email: str,
        password: str,
        supabase_url: str,
        supabase_key: str,
    ) -> Dict[str, Any]:
        try:
            from supabase import create_client
        except ImportError:
            return {"success": False, "reason": "Supabase Python client is not installed."}

        try:
            client = create_client(supabase_url, supabase_key)
            response = client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as error:
            return {"success": False, "reason": str(error)}

        print(f"Supabase login response type: {type(response)}")

        error = self._unwrap_response_value(response, "error")
        if error:
            if isinstance(error, dict):
                error_message = error.get("message") or error.get("msg") or str(error)
            else:
                error_message = str(error)
            return {"success": False, "reason": error_message or "Authentication failed."}

        session = self._unwrap_response_value(response, "session")
        if session is None:
            data = self._unwrap_response_value(response, "data")
            session = self._unwrap_response_value(data, "session")

        if session is None:
            print(f"Supabase login session missing; response type: {type(response)}")
            return {"success": False, "reason": "Supabase login did not return a session object."}

        access_token = self._unwrap_response_value(session, "access_token")
        if not access_token:
            print(f"Supabase login session missing access_token; session type: {type(session)}")
            return {"success": False, "reason": "Supabase session is missing access_token."}

        refresh_token = self._unwrap_response_value(session, "refresh_token") or ""
        user = self._unwrap_response_value(response, "user")
        user_email = self._unwrap_response_value(user, "email") if user is not None else None
        username = self._extract_username(user, user_email or email)

        session_dict = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_email": user_email or email,
            "username": username,
        }

        return {"success": True, "session": session_dict}

    def _unwrap_response_value(self, response: Any, key: str) -> Any:
        if response is None:
            return None

        if isinstance(response, dict):
            return response.get(key)

        return getattr(response, key, None)

    def _extract_username(self, user: Any, email: str) -> str:
        if user is not None:
            for key in ("username", "name", "full_name", "display_name"):
                value = self._unwrap_response_value(user, key)
                if value:
                    return str(value).strip()

        if email:
            if "@" in email:
                return email.split("@", 1)[0]
            return email

        return "User"

    def set_status(self, message: str, error: bool = False) -> None:
        color = "#b00020" if error else "#444444"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px;")

    def set_loading(self, loading: bool) -> None:
        self.login_button.setEnabled(not loading)
        self.cancel_button.setEnabled(not loading)
        if loading:
            self.set_status("Signing in and validating license…", error=False)

    def _load_remembered_credentials(self) -> None:
        """Pre-fill email và password từ lần login trước nếu user đã tick Save information."""
        try:
            session = self.session_manager.load_session() or {}
        except Exception:
            return
        email = session.get("last_login_email", "")
        # Hỗ trợ cả key cũ (remember_email) và key mới (remember_password)
        save_info = session.get("remember_password", False) or session.get("remember_email", False)
        if not (save_info and email):
            return
        self.email_input.setText(email)
        self.remember_email_cb.setChecked(True)
        stored_pw = _load_keyring_password(email)
        if stored_pw:
            self.password_input.setText(stored_pw)

    def _today_str(self) -> str:
        import datetime

        return datetime.date.today().isoformat()
