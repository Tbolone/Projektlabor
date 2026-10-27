from src.api.base_api import BaseAPI


class AdminAPI(BaseAPI):

    def list_users(self, user_type: str | None = None, search: str | None = None):
        params = {}
        if user_type:
            params["type"] = user_type
        if search:
            params["search"] = search
        return self._request("GET", "/api/admin/users", params=params)

    def create_user(self, name: str, email: str, password: str, user_type: str):
        return self._request(
            "POST",
            "/api/admin/users",
            json={"name": name, "email": email, "password": password, "type": user_type},
        )

    def update_user(self, user_id: int, **fields):
        payload = {key: value for key, value in fields.items() if value not in (None, "")}
        return self._request("PATCH", f"/api/admin/users/{user_id}", json=payload)

    def delete_user(self, user_id: int):
        return self._request("DELETE", f"/api/admin/users/{user_id}")

    def list_couriers(self):
        return self._request("GET", "/api/admin/couriers")

    def create_courier(
        self,
        name: str,
        email: str,
        password: str,
        max_capacity: float,
        vehicle_plate_number: str,
        is_available: bool = True,
    ):
        return self._request(
            "POST",
            "/api/admin/couriers",
            json={
                "name": name,
                "email": email,
                "password": password,
                "max_capacity": max_capacity,
                "vehicle_plate_number": vehicle_plate_number,
                "is_available": is_available,
            },
        )

    def update_courier(self, courier_id: int, **fields):
        payload = {key: value for key, value in fields.items() if value not in (None, "")}
        return self._request("PATCH", f"/api/admin/couriers/{courier_id}", json=payload)

    def delete_courier(self, courier_id: int):
        return self._request("DELETE", f"/api/admin/couriers/{courier_id}")

    def list_packages(
        self,
        status: str | None = None,
        courier_id: int | None = None,
        search: str | None = None,
    ):
        params = {}
        if status:
            params["status"] = status
        if courier_id:
            params["courier_id"] = courier_id
        if search:
            params["search"] = search
        return self._request("GET", "/api/admin/packages", params=params)

    def get_package(self, package_id: int):
        return self._request("GET", f"/api/admin/packages/{package_id}")

    def update_package(self, package_id: int, **fields):
        payload = {key: value for key, value in fields.items() if value is not None}
        return self._request("PATCH", f"/api/admin/packages/{package_id}", json=payload)

    def delete_package(self, package_id: int):
        return self._request("DELETE", f"/api/admin/packages/{package_id}")

    def assign_courier(self, package_id: int, courier_id: int, stage: str):
        return self._request(
            "POST",
            f"/api/admin/packages/{package_id}/assign",
            json={"courier_id": courier_id, "stage": stage},
        )

    def get_stats(self):
        return self._request("GET", "/api/admin/stats")
