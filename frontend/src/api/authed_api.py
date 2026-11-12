import httpx

from src.api.base_api import BaseAPI
from src.api.session import auth_api


class AuthedAPI(BaseAPI):
    """Bejelentkezést igénylő hívások közös alapja.

    A tokent a közös session.auth_api tárolja, innen vesszük minden kéréshez.
    """

    SESSION_EXPIRED = "A bejelentkezés lejárt. Jelentkezz be újra."

    def __init__(self):
        super().__init__()
        self.auth_api = auth_api

    def _auth_headers(self) -> dict:
        token = self.auth_api.token
        return {"Authorization": f"Bearer {token}"} if token else {}

    def _clear_session(self):
        self.auth_api.token = None
        self.auth_api.client.headers.pop("Authorization", None)

    def _request(self, method: str, url: str, **kwargs) -> tuple[bool, object]:
        """Sikeres esetben (True, válasz), hibánál (False, üzenet)."""
        try:
            response = self.client.request(
                method, url, headers=self._auth_headers(), **kwargs
            )
            response.raise_for_status()

            if response.status_code == 204 or not response.content:
                return True, None
            return True, response.json()

        except httpx.HTTPStatusError as error:
            return False, self._handle_status_error(error)

        except httpx.RequestError:
            return False, "Nem sikerült csatlakozni a szerverhez."

        except Exception:
            return False, "Váratlan hiba történt. Próbáld újra."

    def _handle_status_error(self, error: httpx.HTTPStatusError) -> str:
        """A szerver hibaüzenetét olvasható magyar szöveggé alakítja."""
        status_code = error.response.status_code

        if status_code == 401:
            self._clear_session()
            return self.SESSION_EXPIRED

        try:
            detail = error.response.json().get("detail")
        except Exception:
            detail = None

        if status_code == 403:
            return detail if isinstance(detail, str) else "Ehhez nincs jogosultságod."

        if status_code == 404:
            return detail if isinstance(detail, str) else "A keresett elem nem található."

        if status_code == 409:
            return detail if isinstance(detail, str) else "A művelet ütközik a jelenlegi állapottal."

        if status_code == 422:
            if isinstance(detail, list) and detail:
                field = detail[0].get("loc", [""])[-1]
                message = detail[0].get("msg", "Érvénytelen adat.")
                return f"{field}: {message}"
            return "Érvénytelen adat."

        if isinstance(detail, str):
            return detail

        return f"Szerver hiba ({status_code})."
