import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

VALIDATE_URL = "https://hieusugoi.com/api/auth/validate"
#VALIDATE_URL = "http://localhost:3000/api/auth/validate"

class ValidationResult(Dict[str, Any]):
    success: bool
    reason: Optional[str]
    server_date: Optional[str]
    user: Optional[Dict[str, Any]]
    license: Optional[Dict[str, Any]]


class LicenseValidator:
    def validate(self, access_token: str) -> ValidationResult:
        if not access_token:
            return {"success": False, "reason": "invalid_token"}

        print(f"Token type: {type(access_token)}, first 20 chars: {access_token[:20] if access_token else 'None'}")

        request = urllib.request.Request(
            VALIDATE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            try:
                body = error.read().decode("utf-8")
            except Exception:
                return {"success": False, "reason": "invalid_token"}
        except Exception:
            return {"success": False, "reason": "invalid_token"}

        try:
            data = json.loads(body)
        except Exception:
            return {"success": False, "reason": "invalid_token"}

        if data.get("success"):
            return {
                "success": True,
                "reason": None,
                "server_date": data.get("server_date"),
                "user": data.get("user"),
                "license": data.get("license"),
            }

        return {
            "success": False,
            "reason": data.get("reason") or "invalid_token",
            "server_date": None,
            "user": None,
            "license": None,
        }
