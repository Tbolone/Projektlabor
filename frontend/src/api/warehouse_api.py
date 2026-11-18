from src.api.authed_api import AuthedAPI


class WarehouseAPI(AuthedAPI):

    def list_packages(self, status: str | None = None, courier_id: int | None = None,
                      search: str | None = None):
        params = {}
        if status:
            params["status"] = status
        if courier_id:
            params["courier_id"] = courier_id
        if search:
            params["search"] = search
        return self._request("GET", "/api/warehouse/packages", params=params)

    def get_package(self, package_id: int):
        return self._request("GET", f"/api/warehouse/packages/{package_id}")

    def receive_package(self, package_id: int, comment: str | None = None):
        return self._request(
            "POST", f"/api/warehouse/packages/{package_id}/receive",
            json={"comment": comment},
        )

    def assign_courier(self, package_id: int, courier_id: int, stage: str):
        return self._request(
            "POST", f"/api/warehouse/packages/{package_id}/assign",
            json={"courier_id": courier_id, "stage": stage},
        )

    def list_couriers(self):
        return self._request("GET", "/api/warehouse/couriers")
