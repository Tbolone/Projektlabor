import httpx

class APIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=5.0)
        self.token = None

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

    def close(self):
        self.client.close()