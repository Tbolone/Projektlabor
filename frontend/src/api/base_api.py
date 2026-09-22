import httpx

class BaseAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url, timeout=5.0)
        self.token = None

    def close(self):
        self.client.close()