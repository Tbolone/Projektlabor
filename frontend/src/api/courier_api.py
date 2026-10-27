from src.api.base_api import BaseAPI


class CourierAPI(BaseAPI):

    def get_profile(self) -> tuple[bool, object]:
        return self._request("GET", "/api/courier/me")

    def set_availability(self, is_available: bool) -> tuple[bool, object]:
        return self._request(
            "PATCH", "/api/courier/me/availability", json={"is_available": is_available}
        )

    def get_tasks(self) -> tuple[bool, object]:
        return self._request("GET", "/api/courier/tasks")

    def get_package(self, package_id: int) -> tuple[bool, object]:
        return self._request("GET", f"/api/courier/packages/{package_id}")

    def _action(self, package_id: int, action: str, comment: str | None = None):
        return self._request(
            "POST",
            f"/api/courier/packages/{package_id}/{action}",
            json={"comment": comment},
        )

    def start_pickup(self, package_id: int, comment: str | None = None):
        return self._action(package_id, "start-pickup", comment)

    def confirm_pickup(self, package_id: int, comment: str | None = None):
        return self._action(package_id, "pickup", comment)

    def deliver_to_warehouse(self, package_id: int, comment: str | None = None):
        return self._action(package_id, "deliver-to-warehouse", comment)

    def start_delivery(self, package_id: int, comment: str | None = None):
        return self._action(package_id, "start-delivery", comment)

    def confirm_delivery(self, package_id: int, comment: str | None = None):
        return self._action(package_id, "deliver", comment)

    def report_failure(self, package_id: int, comment: str | None = None):
        return self._action(package_id, "fail", comment)

    def get_history(self, period: str = "day") -> tuple[bool, object]:
        return self._request("GET", "/api/courier/history", params={"period": period})
