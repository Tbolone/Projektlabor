from src.api.base_api import BaseAPI
import httpx
import json
import re

class AuthAPI(BaseAPI):
    def __init__(self):
        super().__init__()
        self.EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def is_valid_email(self, email: str) -> bool:
        return bool(self.EMAIL_PATTERN.match(email))

    def login(self, email: str, password: str) -> tuple[bool, str]:
        if not email or not password:
            return False, "Add meg az emailt és a jelszót."

        if not self.is_valid_email(email):
            return False, "Érvénytelen email cím formátum."

        try:
            response = self.client.post("/api/auth/login", json={
                "email": email,
                "password": password
            })
            response.raise_for_status()
            data = response.json()

            self.token = data.get("access_token")
            if self.token:
                self.client.headers["Authorization"] = f"Bearer {self.token}"

            return True, ""

        except httpx.HTTPStatusError as e:
            return False, self._handle_status_error(e)

        except httpx.RequestError:
            return False, "Nem sikerült csatlakozni a szerverhez."

        except Exception:
            return False, "Váratlan hiba történt. Próbáld újra."

    def register(self, email: str, name: str, password: str, password_again: str) -> tuple[bool, str]:
        if not email or not name or not password or not password_again:
            return False, "Minden mezőt tölts ki."

        if not self.is_valid_email(email):
            return False, "Érvénytelen email cím formátum."

        if password != password_again:
            return False, "A két jelszó nem egyezik."

        if len(password) < 6:
            return False, "A jelszó legalább 6 karakter legyen."

        try:
            response = self.client.post("/api/auth/register", json={
                "email": email,
                "name": name,
                "password": password
            })
            response.raise_for_status()
            return True, ""

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                return False, "Ez az email cím már regisztrálva van."
            return False, self._handle_status_error(e)

        except httpx.RequestError:
            return False, "Nem sikerült csatlakozni a szerverhez."

        except Exception:
            return False, "Váratlan hiba történt. Próbáld újra."

    @staticmethod
    def _handle_status_error(e: httpx.HTTPStatusError) -> str:
        status_code = e.response.status_code

        if status_code == 401:
            return "Hibás email vagy jelszó."

        if status_code == 422:
            try:
                detail = e.response.json().get("detail", [])
                if isinstance(detail, list) and detail:
                    field = detail[0].get("loc", [""])[-1]
                    msg = detail[0].get("msg", "Érvénytelen adat.")
                    return f"{field}: {msg}"
            except (json.JSONDecodeError, KeyError, IndexError):
                pass
            return "Érvénytelen adat."

        return f"Szerver hiba ({status_code})."
    