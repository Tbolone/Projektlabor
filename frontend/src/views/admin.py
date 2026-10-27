import customtkinter as ctk

from src.api.admin_api import AdminAPI
from src.views.base_layout import SidebarView
from src.views.widgets import (
    STATUS_LABELS,
    USER_TYPE_LABELS,
    ConfirmDialog,
    FormDialog,
    StatCard,
    Table,
    status_color,
    status_label,
)

STATUS_FILTER = {"Mind": None}
STATUS_FILTER.update({label: key for key, (label, _) in STATUS_LABELS.items()})

USER_TYPE_OPTIONS = {
    "Adminisztrátor": "admin",
    "Regisztrált ügyfél": "registered customer",
    "Vendég ügyfél": "unregistered customer",
    "Raktáros": "warehouse_staff",
    "Futár": "delivery_man",
}


class AdminView(SidebarView):
    MENU_ITEMS = [
        ("📊  Áttekintés", "overview"),
        ("📦  Csomagok", "packages"),
        ("🚚  Futárok", "couriers"),
        ("👥  Felhasználók", "users"),
        ("🏭  Raktár", "warehouse"),
    ]
    SUBTITLE = "Adminisztrátori felület"

    def __init__(self, master, controller):
        self.api = AdminAPI()
        self.couriers_cache: list[dict] = []
        super().__init__(master, controller)

    def _load_couriers(self) -> list[dict]:
        ok, data = self.api.list_couriers()
        if ok:
            self.couriers_cache = data
        return self.couriers_cache

    def _courier_choices(self) -> dict[str, int]:
        return {
            f"{c['name']} ({c['vehicle_plate_number']})": c["id"]
            for c in self._load_couriers()
        }

    def build_overview(self, parent):
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            parent, text="🔄  Frissítés", width=120, command=self.refresh_overview
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        self.overview_cards = ctk.CTkFrame(parent, fg_color="transparent")
        self.overview_cards.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        self.courier_stats_table = Table(
            parent,
            columns=[
                ("Futár", 180),
                ("Rendszám", 110),
                ("Kiszállítva", 100),
                ("Felvéve", 90),
                ("Sikertelen", 95),
                ("Aktív", 70),
                ("Átlag kiszállítás", 140),
                ("Csomag / nap", 110),
            ],
        )
        self.courier_stats_table.grid(row=2, column=0, sticky="nsew")

    def refresh_overview(self):
        ok, stats = self.api.get_stats()
        if not ok:
            self.courier_stats_table.show_message(str(stats))
            self.set_status(str(stats), error=True)
            return

        for child in self.overview_cards.winfo_children():
            child.destroy()

        warehouse = stats["warehouse"]
        avg = stats.get("avg_delivery_hours")
        cards = [
            ("Összes csomag", stats["total_packages"], "#2563eb"),
            ("Raktárban", warehouse["in_warehouse"], "#0891b2"),
            ("Felvételre vár", warehouse["waiting_for_pickup"], "#6b7280"),
            ("Kiszállítás alatt", warehouse["out_for_delivery"], "#d97706"),
            ("Kézbesítve", warehouse["delivered_total"], "#16a34a"),
            (
                "Átlagos kiszállítási idő",
                f"{avg} óra" if avg is not None else "—",
                "#7c3aed",
            ),
        ]
        for index, (title, value, accent) in enumerate(cards):
            self.overview_cards.grid_columnconfigure(index, weight=1)
            StatCard(self.overview_cards, title, value, accent).grid(
                row=0, column=index, padx=(0 if index == 0 else 8, 0), sticky="ew"
            )

        self.courier_stats_table.clear()
        couriers = stats.get("couriers", [])

        if not couriers:
            self.courier_stats_table.show_message(
                "Még nincs futár a rendszerben. A Futárok képernyőn tudsz újat felvenni."
            )
            return

        for courier in couriers:
            avg_hours = courier.get("avg_delivery_hours")
            per_day = courier.get("packages_per_day")
            self.courier_stats_table.add_row(
                [
                    courier["name"],
                    courier["vehicle_plate_number"],
                    f"{courier['delivered_count']} db",
                    f"{courier['picked_up_count']} db",
                    f"{courier['failed_count']} db",
                    f"{courier['active_count']} db",
                    f"{avg_hours} óra" if avg_hours is not None else "—",
                    f"{per_day} db" if per_day is not None else "—",
                ]
            )

    def build_packages(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(3, weight=1)

        self.package_status_filter = ctk.CTkOptionMenu(
            toolbar,
            values=list(STATUS_FILTER.keys()),
            width=190,
            command=lambda _: self.refresh_packages(),
        )
        self.package_status_filter.set("Mind")
        self.package_status_filter.grid(row=0, column=0, padx=(0, 8))

        self.package_search = ctk.CTkEntry(
            toolbar, placeholder_text="Keresés név, város vagy azonosító szerint", width=280
        )
        self.package_search.grid(row=0, column=1, padx=(0, 8))
        self.package_search.bind("<Return>", lambda event: self.refresh_packages())

        ctk.CTkButton(
            toolbar, text="🔍  Keresés", width=110, command=self.refresh_packages
        ).grid(row=0, column=2, padx=(0, 8))

        self.packages_summary = ctk.CTkLabel(toolbar, text="", anchor="w")
        self.packages_summary.grid(row=0, column=3, sticky="w", padx=8)

        ctk.CTkButton(
            toolbar, text="＋  Új csomag", width=130, command=self._create_package
        ).grid(row=0, column=4)

        self.packages_table = Table(
            parent,
            columns=[
                ("Az.", 45),
                ("Állapot", 158),
                ("Feladó", 108),
                ("Címzett", 108),
                ("Felvevő futár", 105),
                ("Kiszállító futár", 105),
            ],
        )
        self.packages_table.grid(row=1, column=0, sticky="nsew")

    def refresh_packages(self):
        status_key = STATUS_FILTER.get(self.package_status_filter.get())
        search = self.package_search.get().strip() or None

        ok, data = self.api.list_packages(status=status_key, search=search)
        if not ok:
            self.packages_table.show_message(str(data))
            self.set_status(str(data), error=True)
            return

        self.packages_table.clear()
        self.packages_summary.configure(text=f"{len(data)} csomag")

        if not data:
            self.packages_table.show_message("Nincs a szűrésnek megfelelő csomag.")
            return

        for package in data:
            pickup_courier = package.get("pickup_courier")
            delivery_courier = package.get("delivery_courier")

            buttons = [
                ("Részletek", lambda p=package: self._package_details(p["id"]), None),
                ("Kiosztás", lambda p=package: self._assign_courier(p), None),
                ("Szerkesztés", lambda p=package: self._edit_package(p), None),
                ("Törlés", lambda p=package: self._delete_package(p), "#dc2626"),
            ]

            self.packages_table.add_row(
                [
                    f"#{package['id']}",
                    status_label(package["current_status"]),
                    package["pickup_contact"]["name"],
                    package["delivery_contact"]["name"],
                    pickup_courier["name"] if pickup_courier else "—",
                    delivery_courier["name"] if delivery_courier else "—",
                ],
                buttons=buttons,
                color_index=1,
                color=status_color(package["current_status"]),
            )

    def _assign_courier(self, package):
        choices = self._courier_choices()
        if not choices:
            self.set_status("Előbb vegyél fel futárt a Futárok képernyőn.", error=True)
            return

        dialog = FormDialog(
            self,
            f"Futár kijelölése — #{package['id']}",
            [
                ("stage", "Feladat", "option", "Felvétel", ["Felvétel", "Kiszállítás"]),
                ("courier", "Futár", "option", None, list(choices.keys())),
            ],
            submit_text="Kijelölés",
        )
        values = dialog.show()
        if values is None:
            return

        stage = "pickup" if values["stage"] == "Felvétel" else "delivery"
        courier_id = choices[values["courier"]]

        ok, data = self.api.assign_courier(package["id"], courier_id, stage)
        if ok:
            self.set_status(f"#{package['id']} — futár kijelölve")
            self.refresh_packages()
        else:
            self.set_status(str(data), error=True)

    def _edit_package(self, package):
        current_status_label = status_label(package["current_status"])

        dialog = FormDialog(
            self,
            f"Csomag szerkesztése — #{package['id']}",
            [
                ("size", "Méret", "text", package["size"], None),
                ("weight", "Súly (kg)", "number", package["weight"], None),
                ("pickup_date", "Felvétel napja (ÉÉÉÉ-HH-NN)", "text", package["pickup_date"], None),
                ("pickup_time_slot", "Idősáv", "text", package["pickup_time_slot"], None),
                (
                    "status",
                    "Állapot",
                    "option",
                    current_status_label,
                    [label for label, _ in STATUS_LABELS.values()],
                ),
            ],
            submit_text="Mentés",
        )
        values = dialog.show()
        if values is None:
            return

        try:
            weight = float(values["weight"].replace(",", "."))
        except ValueError:
            self.set_status("A súlynak számnak kell lennie.", error=True)
            return

        new_status = STATUS_FILTER.get(values["status"])

        ok, data = self.api.update_package(
            package["id"],
            size=values["size"],
            weight=weight,
            pickup_date=values["pickup_date"],
            pickup_time_slot=values["pickup_time_slot"],
            current_status=new_status if new_status != package["current_status"] else None,
        )
        if ok:
            self.set_status(f"#{package['id']} mentve")
            self.refresh_packages()
        else:
            self.set_status(str(data), error=True)

    def _delete_package(self, package):
        confirmed = ConfirmDialog(
            self,
            "Csomag törlése",
            f"Biztosan törlöd a(z) #{package['id']} csomagot? "
            "A hozzá tartozó eseménytörténet is elvész. A művelet nem vonható vissza.",
        ).show()

        if not confirmed:
            return

        ok, data = self.api.delete_package(package["id"])
        if ok:
            self.set_status(f"#{package['id']} törölve")
            self.refresh_packages()
        else:
            self.set_status(str(data), error=True)

    def _create_package(self):
        dialog = FormDialog(
            self,
            "Új csomag előjegyzése",
            [
                ("p_name", "Feladó neve", "text", "", None),
                ("p_zip", "Feladó irányítószám", "text", "", None),
                ("p_city", "Feladó város", "text", "", None),
                ("p_street", "Feladó cím", "text", "", None),
                ("p_email", "Feladó email", "text", "", None),
                ("p_phone", "Feladó telefon", "text", "", None),
                ("d_name", "Címzett neve", "text", "", None),
                ("d_zip", "Címzett irányítószám", "text", "", None),
                ("d_city", "Címzett város", "text", "", None),
                ("d_street", "Címzett cím", "text", "", None),
                ("d_email", "Címzett email", "text", "", None),
                ("d_phone", "Címzett telefon", "text", "", None),
                ("size", "Méret (S / M / L)", "text", "M", None),
                ("weight", "Súly (kg)", "number", "1", None),
                ("pickup_date", "Felvétel napja (ÉÉÉÉ-HH-NN)", "text", "", None),
                ("slot", "Idősáv", "text", "08:00-12:00", None),
            ],
            submit_text="Előjegyzés",
        )
        values = dialog.show()
        if values is None:
            return

        try:
            weight = float(values["weight"].replace(",", "."))
        except ValueError:
            self.set_status("A súlynak számnak kell lennie.", error=True)
            return

        payload = {
            "pickup_contact": {
                "name": values["p_name"],
                "zip_code": values["p_zip"],
                "city": values["p_city"],
                "street_address": values["p_street"],
                "email": values["p_email"],
                "phone": values["p_phone"],
            },
            "delivery_contact": {
                "name": values["d_name"],
                "zip_code": values["d_zip"],
                "city": values["d_city"],
                "street_address": values["d_street"],
                "email": values["d_email"],
                "phone": values["d_phone"],
            },
            "size": values["size"],
            "weight": weight,
            "pickup_date": values["pickup_date"],
            "pickup_time_slot": values["slot"],
        }

        ok, data = self.api._request("POST", "/api/admin/packages", json=payload)
        if ok:
            self.set_status(f"#{data['id']} csomag előjegyezve")
            self.refresh_packages()
        else:
            self.set_status(str(data), error=True)

    def _package_details(self, package_id):
        ok, package = self.api.get_package(package_id)
        if not ok:
            self.set_status(str(package), error=True)
            return

        window = ctk.CTkToplevel(self)
        window.title(f"Csomag #{package['id']}")
        window.geometry("640x580")
        window.transient(self.winfo_toplevel())

        container = ctk.CTkScrollableFrame(window)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            container,
            text=f"Csomag #{package['id']}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text=status_label(package["current_status"]),
            text_color=status_color(package["current_status"]),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(2, 8))

        ctk.CTkLabel(
            container,
            text=f"Követési azonosító: {package['tracking_id']}",
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", pady=(0, 8))

        pickup = package.get("pickup_courier")
        delivery = package.get("delivery_courier")
        ctk.CTkLabel(
            container,
            text=(
                f"Felvevő futár: {pickup['name'] if pickup else '— nincs kijelölve'}\n"
                f"Kiszállító futár: {delivery['name'] if delivery else '— nincs kijelölve'}"
            ),
            justify="left",
            anchor="w",
        ).pack(anchor="w", pady=(0, 8))

        for title, contact in (
            ("Felvételi cím", package["pickup_contact"]),
            ("Kézbesítési cím", package["delivery_contact"]),
        ):
            ctk.CTkLabel(
                container, text=title, font=ctk.CTkFont(size=13, weight="bold")
            ).pack(anchor="w", pady=(10, 2))
            ctk.CTkLabel(
                container,
                text=(
                    f"{contact['name']}\n"
                    f"{contact['zip_code']} {contact['city']}, {contact['street_address']}\n"
                    f"{contact['phone']}  ·  {contact['email']}"
                ),
                justify="left",
                anchor="w",
            ).pack(anchor="w")

        ctk.CTkLabel(
            container, text="Eseménytörténet", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(14, 4))

        for event in package.get("events", []):
            stamp = str(event["timestamp"]).replace("T", " ")[:16]
            line = f"{stamp}  —  {status_label(event['status'])}"
            if event.get("actor_name"):
                line += f"  ({event['actor_name']})"
            if event.get("comment"):
                line += f"\n        {event['comment']}"
            ctk.CTkLabel(container, text=line, justify="left", anchor="w").pack(
                anchor="w", pady=1
            )

    def build_couriers(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            toolbar, text="🔄  Frissítés", width=120, command=self.refresh_couriers
        ).grid(row=0, column=0, padx=(0, 10))

        ctk.CTkButton(
            toolbar, text="＋  Új futár", width=130, command=self._create_courier
        ).grid(row=0, column=2)

        self.couriers_table = Table(
            parent,
            columns=[
                ("Név", 170),
                ("Email", 200),
                ("Rendszám", 110),
                ("Kapacitás", 100),
                ("Terhelés", 110),
                ("Állapot", 120),
            ],
        )
        self.couriers_table.grid(row=1, column=0, sticky="nsew")

    def refresh_couriers(self):
        ok, data = self.api.list_couriers()
        if not ok:
            self.couriers_table.show_message(str(data))
            self.set_status(str(data), error=True)
            return

        self.couriers_cache = data
        self.couriers_table.clear()

        if not data:
            self.couriers_table.show_message(
                "Még nincs futár. Az „Új futár” gombbal tudsz felvenni egyet."
            )
            return

        for courier in data:
            available = courier["is_available"]
            self.couriers_table.add_row(
                [
                    courier["name"],
                    courier["email"],
                    courier["vehicle_plate_number"],
                    f"{courier['max_capacity']} kg",
                    f"{courier['current_load']} kg / {courier['active_package_count']} db",
                    "Elérhető" if available else "Nem elérhető",
                ],
                buttons=[
                    ("Szerkesztés", lambda c=courier: self._edit_courier(c), None),
                    ("Törlés", lambda c=courier: self._delete_courier(c), "#dc2626"),
                ],
                color_index=5,
                color="#16a34a" if available else "#dc2626",
            )

    def _create_courier(self):
        dialog = FormDialog(
            self,
            "Új futár felvétele",
            [
                ("name", "Név", "text", "", None),
                ("email", "Email", "text", "", None),
                ("password", "Jelszó", "password", "", None),
                ("plate", "Rendszám", "text", "", None),
                ("capacity", "Maximális kapacitás (kg)", "number", "200", None),
                ("available", "Elérhető", "switch", True, None),
            ],
            submit_text="Létrehozás",
        )
        values = dialog.show()
        if values is None:
            return

        try:
            capacity = float(values["capacity"].replace(",", "."))
        except ValueError:
            self.set_status("A kapacitásnak számnak kell lennie.", error=True)
            return

        ok, data = self.api.create_courier(
            name=values["name"],
            email=values["email"],
            password=values["password"],
            max_capacity=capacity,
            vehicle_plate_number=values["plate"],
            is_available=values["available"],
        )
        if ok:
            self.set_status(f"{data['name']} felvéve futárként")
            self.refresh_couriers()
        else:
            self.set_status(str(data), error=True)

    def _edit_courier(self, courier):
        dialog = FormDialog(
            self,
            f"Futár szerkesztése — {courier['name']}",
            [
                ("name", "Név", "text", courier["name"], None),
                ("email", "Email", "text", courier["email"], None),
                ("password", "Új jelszó (üresen hagyható)", "password", "", None),
                ("plate", "Rendszám", "text", courier["vehicle_plate_number"], None),
                ("capacity", "Maximális kapacitás (kg)", "number", courier["max_capacity"], None),
                ("available", "Elérhető", "switch", courier["is_available"], None),
            ],
            submit_text="Mentés",
        )
        values = dialog.show()
        if values is None:
            return

        try:
            capacity = float(values["capacity"].replace(",", "."))
        except ValueError:
            self.set_status("A kapacitásnak számnak kell lennie.", error=True)
            return

        ok, data = self.api.update_courier(
            courier["id"],
            name=values["name"],
            email=values["email"],
            password=values["password"] or None,
            vehicle_plate_number=values["plate"],
            max_capacity=capacity,
        )
        if not ok:
            self.set_status(str(data), error=True)
            return

        if values["available"] != courier["is_available"]:
            self.api.update_courier(courier["id"], is_available=values["available"])

        self.set_status(f"{values['name']} adatai mentve")
        self.refresh_couriers()

    def _delete_courier(self, courier):
        confirmed = ConfirmDialog(
            self,
            "Futár törlése",
            f"Biztosan törlöd {courier['name']} futárt? A belépése is megszűnik. "
            "Aktív csomaggal rendelkező futár nem törölhető.",
        ).show()

        if not confirmed:
            return

        ok, data = self.api.delete_courier(courier["id"])
        if ok:
            self.set_status(f"{courier['name']} törölve")
            self.refresh_couriers()
        else:
            self.set_status(str(data), error=True)

    def build_users(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(3, weight=1)

        self.user_type_filter = ctk.CTkOptionMenu(
            toolbar,
            values=["Mind"] + list(USER_TYPE_OPTIONS.keys()),
            width=180,
            command=lambda _: self.refresh_users(),
        )
        self.user_type_filter.set("Mind")
        self.user_type_filter.grid(row=0, column=0, padx=(0, 8))

        self.user_search = ctk.CTkEntry(
            toolbar, placeholder_text="Keresés név vagy email szerint", width=260
        )
        self.user_search.grid(row=0, column=1, padx=(0, 8))
        self.user_search.bind("<Return>", lambda event: self.refresh_users())

        ctk.CTkButton(
            toolbar, text="🔍  Keresés", width=110, command=self.refresh_users
        ).grid(row=0, column=2)

        ctk.CTkButton(
            toolbar, text="＋  Új felhasználó", width=160, command=self._create_user
        ).grid(row=0, column=4)

        self.users_table = Table(
            parent,
            columns=[("Az.", 55), ("Név", 200), ("Email", 240), ("Szerepkör", 170)],
        )
        self.users_table.grid(row=1, column=0, sticky="nsew")

    def refresh_users(self):
        type_key = USER_TYPE_OPTIONS.get(self.user_type_filter.get())
        search = self.user_search.get().strip() or None

        ok, data = self.api.list_users(user_type=type_key, search=search)
        if not ok:
            self.users_table.show_message(str(data))
            self.set_status(str(data), error=True)
            return

        self.users_table.clear()

        if not data:
            self.users_table.show_message("Nincs a szűrésnek megfelelő felhasználó.")
            return

        for user in data:
            self.users_table.add_row(
                [
                    f"#{user['user_id']}",
                    user["name"],
                    user["email"],
                    USER_TYPE_LABELS.get(user["type"], user["type"]),
                ],
                buttons=[
                    ("Szerkesztés", lambda u=user: self._edit_user(u), None),
                    ("Törlés", lambda u=user: self._delete_user(u), "#dc2626"),
                ],
            )

    def _create_user(self):
        dialog = FormDialog(
            self,
            "Új felhasználó",
            [
                ("name", "Név", "text", "", None),
                ("email", "Email", "text", "", None),
                ("password", "Jelszó", "password", "", None),
                (
                    "type",
                    "Szerepkör",
                    "option",
                    "Regisztrált ügyfél",
                    list(USER_TYPE_OPTIONS.keys()),
                ),
            ],
            submit_text="Létrehozás",
        )
        values = dialog.show()
        if values is None:
            return

        ok, data = self.api.create_user(
            name=values["name"],
            email=values["email"],
            password=values["password"],
            user_type=USER_TYPE_OPTIONS[values["type"]],
        )
        if ok:
            self.set_status(f"{data['name']} létrehozva")
            self.refresh_users()
        else:
            self.set_status(str(data), error=True)

    def _edit_user(self, user):
        current_label = USER_TYPE_LABELS.get(user["type"], user["type"])

        dialog = FormDialog(
            self,
            f"Felhasználó szerkesztése — {user['name']}",
            [
                ("name", "Név", "text", user["name"], None),
                ("email", "Email", "text", user["email"], None),
                ("password", "Új jelszó (üresen hagyható)", "password", "", None),
                (
                    "type",
                    "Szerepkör",
                    "option",
                    current_label,
                    list(USER_TYPE_OPTIONS.keys()),
                ),
            ],
            submit_text="Mentés",
        )
        values = dialog.show()
        if values is None:
            return

        ok, data = self.api.update_user(
            user["user_id"],
            name=values["name"],
            email=values["email"],
            password=values["password"] or None,
            type=USER_TYPE_OPTIONS[values["type"]],
        )
        if ok:
            self.set_status(f"{values['name']} adatai mentve")
            self.refresh_users()
        else:
            self.set_status(str(data), error=True)

    def _delete_user(self, user):
        confirmed = ConfirmDialog(
            self,
            "Felhasználó törlése",
            f"Biztosan törlöd {user['name']} felhasználót ({user['email']})? "
            "A művelet nem vonható vissza.",
        ).show()

        if not confirmed:
            return

        ok, data = self.api.delete_user(user["user_id"])
        if ok:
            self.set_status(f"{user['name']} törölve")
            self.refresh_users()
        else:
            self.set_status(str(data), error=True)

    def build_warehouse(self, parent):
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            parent, text="🔄  Frissítés", width=120, command=self.refresh_warehouse
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        self.warehouse_cards = ctk.CTkFrame(parent, fg_color="transparent")
        self.warehouse_cards.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        self.warehouse_table = Table(
            parent,
            columns=[
                ("Nap", 160),
                ("Beérkezett", 130),
                ("Kiment", 130),
                ("Záró készlet", 140),
            ],
        )
        self.warehouse_table.grid(row=2, column=0, sticky="nsew")

    def refresh_warehouse(self):
        ok, stats = self.api.get_stats()
        if not ok:
            self.warehouse_table.show_message(str(stats))
            self.set_status(str(stats), error=True)
            return

        for child in self.warehouse_cards.winfo_children():
            child.destroy()

        warehouse = stats["warehouse"]
        cards = [
            ("Jelenleg raktáron", warehouse["in_warehouse"], "#0891b2"),
            ("Úton a csomagért", warehouse["out_for_pickup"], "#7c3aed"),
            ("Kiszállítás alatt", warehouse["out_for_delivery"], "#d97706"),
            ("Sikertelen / visszaküldve", warehouse["failed_total"], "#dc2626"),
        ]
        for index, (title, value, accent) in enumerate(cards):
            self.warehouse_cards.grid_columnconfigure(index, weight=1)
            StatCard(self.warehouse_cards, title, value, accent).grid(
                row=0, column=index, padx=(0 if index == 0 else 10, 0), sticky="ew"
            )

        self.warehouse_table.clear()
        history = stats.get("warehouse_history", [])

        if not history:
            self.warehouse_table.show_message("Még nincs raktári mozgás.")
            return

        for row in history:
            self.warehouse_table.add_row(
                [
                    row["day"],
                    f"{row['arrived']} db",
                    f"{row['left']} db",
                    f"{row['closing_stock']} db",
                ]
            )

    def on_show(self):
        self.show_panel("overview")
