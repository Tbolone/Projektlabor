from src.api.auth_api import AuthAPI

auth_api = AuthAPI()

def logout():
    auth_api.token = None
    auth_api.client.headers.pop("Authorization", None)