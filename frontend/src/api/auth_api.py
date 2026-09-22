from src.api.base_api import BaseAPI
import httpx

class AuthAPI(BaseAPI):
    def __init__(self):
        super().__init__()

    def login(self, email: str, password: str) -> dict:
            response = self.client.post("/api/auth/login", json={
                "email": email,
                "password": password
            })
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            if self.token:
                self.client.headers["Authorization"] = f"Bearer {self.token}"
            return data

    def register(self, email: str, name: str, password: str, password_again: str) -> tuple[bool, str]:
        if not email or not name or not password or not password_again:
            return False, "Minden mezőt tölts ki."

        if password != password_again:
            return False, "A két jelszó nem egyezik."

        if len(password) < 6:
            return False, "A jelszó legalább 6 karakter legyen."

        try:
            self.api.register(email, name, password)
            return True, ""
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                return False, "Ez az email cím már regisztrálva van."
            return False, f"Szerver hiba ({e.response.status_code})."
        except httpx.ConnectError:
            return False, "Nem sikerült csatlakozni a szerverhez."

    