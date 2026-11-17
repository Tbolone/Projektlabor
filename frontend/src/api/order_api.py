from src.api.authed_api import AuthedAPI


class OrderAPI(AuthedAPI):
    def create_order(self, data: dict) -> tuple[bool, dict | str]:
        """POST /orders/ - csomagfeladás a bejelentkezett felhasználó nevében.

        Siker: (True, {"message", "tracking_id", "package_id"})
        Hiba:  (False, olvasható hibaüzenet)
        """
        return self._request("POST", "/orders/", json=data)