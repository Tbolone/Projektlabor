import httpx


class BaseAPI:

    _client: httpx.Client | None = None
    _base_url = "http://localhost:8000"
    token: str | None = None

    def __init__(self, base_url: str | None = None):
        if base_url:
            BaseAPI._base_url = base_url
        self.base_url = BaseAPI._base_url

    @property
    def client(self) -> httpx.Client:
        if BaseAPI._client is None:
            BaseAPI._client = httpx.Client(base_url=BaseAPI._base_url, timeout=10.0)
        return BaseAPI._client

    @classmethod
    def set_token(cls, token: str | None):
        BaseAPI.token = token
        client = cls._client
        if client is None:
            return
        if token:
            client.headers["Authorization"] = f"Bearer {token}"
        else:
            client.headers.pop("Authorization", None)

    @classmethod
    def logout(cls):
        cls.set_token(None)

    @classmethod
    def close(cls):
        if cls._client is not None:
            cls._client.close()
            cls._client = None

    def _request(self, method: str, url: str, **kwargs) -> tuple[bool, object]:
        try:
            response = self.client.request(method, url, **kwargs)
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

    @staticmethod
    def _handle_status_error(error: httpx.HTTPStatusError) -> str:
        status_code = error.response.status_code

        try:
            detail = error.response.json().get("detail")
        except Exception:
            detail = None

        if status_code == 401:
            return "A bejelentkezés lejárt. Jelentkezz be újra."

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
