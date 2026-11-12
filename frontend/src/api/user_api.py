# src/api/user_api.py
import httpx

from src.api.auth_api import AuthAPI
from src.api.base_api import BaseAPI


class UserAPI(BaseAPI):
    SESSION_EXPIRED = "A bejelentkezés lejárt. Jelentkezz be újra."

    def __init__(self, auth_api: AuthAPI):
        super().__init__()
        self.auth_api = auth_api

    def _auth_headers(self) -> dict:
        token = self.auth_api.token
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _clear_session(self):
        self.auth_api.token = None
        self.auth_api.client.headers.pop("Authorization", None)

    def _request(self, method: str, url: str, json: dict | None = None):
        """-> (True, httpx.Response) vagy (False, hibaüzenet)"""
        try:
            response = self.client.request(
                method, url, json=json, headers=self._auth_headers()
            )
            response.raise_for_status()
            return True, response

        except httpx.HTTPStatusError as e:
            return False, self._handle_status_error(e)

        except httpx.RequestError:
            return False, "Nem sikerült csatlakozni a szerverhez."

        except Exception:
            return False, "Váratlan hiba történt. Próbáld újra."

    def _handle_status_error(self, e: httpx.HTTPStatusError) -> str:
        status_code = e.response.status_code

        if status_code in (401, 403):
            self._clear_session()
            return self.SESSION_EXPIRED

        try:
            detail = e.response.json().get("detail")
        except ValueError:
            detail = None

        if isinstance(detail, str):
            return detail

        if status_code == 422 and isinstance(detail, list) and detail:
            field = detail[0].get("loc", [""])[-1]
            msg = detail[0].get("msg", "Érvénytelen adat.")
            return f"{field}: {msg}"

        return f"Szerver hiba ({status_code})."

    def get_profile(self) -> tuple[bool, dict | str]:
        """GET /api/users/me"""
        ok, result = self._request("GET", "/api/users/me")
        return (True, result.json()) if ok else (False, result)

    def update_profile(self, name: str, primary_address: str) -> tuple[bool, dict | str]:
        """PUT /api/users/me - a név kötelező, az üres cím törlést jelent."""
        if not name:
            return False, "A név nem lehet üres."

        if len(name) > 100:
            return False, "A név legfeljebb 100 karakter lehet."

        if len(primary_address) > 255:
            return False, "A cím legfeljebb 255 karakter lehet."

        ok, result = self._request(
            "PUT",
            "/api/users/me",
            json={"name": name, "primary_address": primary_address or None},
        )
        return (True, result.json()) if ok else (False, result)

    def change_password(
        self, current_password: str, new_password: str, new_password_again: str
    ) -> tuple[bool, str]:
        """PUT /api/users/me/password (siker: 204)"""
        if not current_password or not new_password or not new_password_again:
            return False, "Minden jelszó mezőt tölts ki."

        if new_password != new_password_again:
            return False, "A két új jelszó nem egyezik."

        if len(new_password) < 6:
            return False, "Az új jelszó legalább 6 karakter legyen."

        if len(new_password.encode("utf-8")) > 72:
            return False, "Az új jelszó legfeljebb 72 bájt hosszú lehet."

        if new_password == current_password:
            return False, "Az új jelszó nem egyezhet a jelenlegivel."

        ok, result = self._request(
            "PUT",
            "/api/users/me/password",
            json={"current_password": current_password, "new_password": new_password},
        )
        return (True, "") if ok else (False, result)