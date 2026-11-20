import customtkinter as ctk

from src.api.warehouse_api import WarehouseAPI
from src.views.base_layout import SidebarView
from src.views.widgets import (
    STATUS_LABELS,
    FormDialog,
    StatCard,
    Table,
    status_color,
    status_label,
)

STATUS_FILTER = {"Mind": None}
STATUS_FILTER.update({label: key for key, (label, _) in STATUS_LABELS.items()})
ARRIVING = "picked_up"


class WarehouseView(SidebarView):
    MENU_ITEMS = [
        ("Raktárkészlet", "stock"),
        ("Beérkezés és kiosztás", "dispatch"),
        ("Futárok", "couriers"),
    ]
    SUBTITLE = "Raktárkezelő felület"

    def __init__(self, master, controller):
        self.api = WarehouseAPI()
        self.couriers_cache: list[dict] = []
        super().__init__(master, controller)

    # ------------------------------------------------------------- segédek
    def _courier_choices(self) -> dict[str, int]:
        ok, data = self.api.list_couriers()
        if ok:
            self.couriers_cache = data
        return {
            f"{c['name']} ({c['vehicle_plate_number']}) — {c['active_package_count']} db"
            : c["id"]
            for c in self.couriers_cache
        }

    def _assign(self, package, stage_default="Felvétel"):
        """Futár kijelölése felvételre vagy kiszállításra."""
        choices = self._courier_choices()
        if not choices:
            self.set_status("Nincs futár a rendszerben.", error=True)
            return

        dialog = FormDialog(
            self,
            f"Futár kijelölése — #{package['id']}",
            [
                ("stage", "Feladat", "option", stage_default, ["Felvétel", "Kiszállítás"]),
                ("courier", "Futár", "option", None, list(choices.keys())),
            ],
            submit_text="Kijelölés",
        )
        values = dialog.show()
        if values is None:
            return

        stage = "pickup" if values["stage"] == "Felvétel" else "delivery"
        ok, data = self.api.assign_courier(package["id"], choices[values["courier"]], stage)

        if ok:
            self.set_status(f"#{package['id']} — futár kijelölve")
            self.refresh_stock()
            self.refresh_dispatch()
        else:
            self.set_status(str(data), error=True)

    def _receive(self, package):
        """A futár által behozott csomag felvétele a raktárba."""
        ok, data = self.api.receive_package(package["id"])
        if ok:
            self.set_status(f"#{package['id']} beérkeztetve a raktárba")
            self.refresh_dispatch()
            self.refresh_stock()
        else:
            self.set_status(str(data), error=True)

    def _details(self, package_id):
        ok, package = self.api.get_package(package_id)
        if not ok:
            self.set_status(str(package), error=True)
            return

        window = ctk.CTkToplevel(self)
        window.title(f"Csomag #{package['id']}")
        window.geometry("620x560")
        window.transient(self.winfo_toplevel())

        box = ctk.CTkScrollableFrame(window)
        box.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            box, text=f"Csomag #{package['id']}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            box, text=status_label(package["current_status"]),
            text_color=status_color(package["current_status"]),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(2, 10))

        pickup = package.get("pickup_courier")
        delivery = package.get("delivery_courier")
        ctk.CTkLabel(
            box,
            text=(f"Felvevő futár: {pickup['name'] if pickup else '— nincs kijelölve'}\n"
                  f"Kiszállító futár: {delivery['name'] if delivery else '— nincs kijelölve'}"),
            justify="left", anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        for title, contact in (("Felvételi cím", package["pickup_contact"]),
                               ("Kézbesítési cím", package["delivery_contact"])):
            ctk.CTkLabel(box, text=title, font=ctk.CTkFont(size=13, weight="bold")).pack(
                anchor="w", pady=(10, 2))
            ctk.CTkLabel(
                box,
                text=(f"{contact['name']}\n{contact['zip_code']} {contact['city']}, "
                      f"{contact['street_address']}\n{contact['phone']}"),
                justify="left", anchor="w",
            ).pack(anchor="w")

        ctk.CTkLabel(box, text="Eseménytörténet",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(14, 4))
        for event in package.get("events", []):
            stamp = str(event["timestamp"]).replace("T", " ")[:16]
            line = f"{stamp}  —  {status_label(event['status'])}"
            if event.get("courier_name"):
                line += f"  ({event['courier_name']})"
            ctk.CTkLabel(box, text=line, justify="left", anchor="w").pack(anchor="w", pady=1)

    def build_stock(self, parent):
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(toolbar, text="🔄  Frissítés", width=120,
                      command=self.refresh_stock).grid(row=0, column=0, padx=(0, 10))

        self.stock_filter = ctk.CTkOptionMenu(
            toolbar, values=list(STATUS_FILTER.keys()), width=190,
            command=lambda _: self.refresh_stock())
        self.stock_filter.set("Mind")
        self.stock_filter.grid(row=0, column=1, padx=(0, 10))

        self.stock_summary = ctk.CTkLabel(toolbar, text="", anchor="w")
        self.stock_summary.grid(row=0, column=2, sticky="w")

        self.stock_cards = ctk.CTkFrame(parent, fg_color="transparent")
        self.stock_cards.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self.stock_table = Table(
            parent,
            columns=[("Az.", 45), ("Állapot", 158), ("Feladó", 108), ("Címzett", 108),
                     ("Felvevő futár", 105), ("Kiszállító futár", 105)],
        )
        self.stock_table.grid(row=2, column=0, sticky="nsew")

    def refresh_stock(self):
        if not hasattr(self, "stock_table"):
            return

        status_key = STATUS_FILTER.get(self.stock_filter.get())
        ok, data = self.api.list_packages(status=status_key)
        if not ok:
            self.stock_table.show_message(str(data))
            self.set_status(str(data), error=True)
            return

        counts = {}
        for package in data:
            counts[package["current_status"]] = counts.get(package["current_status"], 0) + 1

        for child in self.stock_cards.winfo_children():
            child.destroy()

        cards = [
            ("Raktárban", counts.get("in_warehouse", 0), "#0891b2"),
            ("Kiszállításra kijelölve", counts.get("assigned_for_delivery", 0), "#2563eb"),
            ("Kiszállítás alatt", counts.get("out_for_delivery", 0), "#d97706"),
            ("Beérkezésre vár", counts.get("picked_up", 0), "#7c3aed"),
        ]
        for index, (title, value, accent) in enumerate(cards):
            self.stock_cards.grid_columnconfigure(index, weight=1)
            StatCard(self.stock_cards, title, value, accent).grid(
                row=0, column=index, padx=(0 if index == 0 else 10, 0), sticky="ew")

        self.stock_table.clear()
        self.stock_summary.configure(text=f"{len(data)} csomag")

        if not data:
            self.stock_table.show_message("Nincs a szűrésnek megfelelő csomag.")
            return

        for package in data:
            pickup = package.get("pickup_courier")
            delivery = package.get("delivery_courier")
            self.stock_table.add_row(
                [f"#{package['id']}", status_label(package["current_status"]),
                 package["pickup_contact"]["name"], package["delivery_contact"]["name"],
                 pickup["name"] if pickup else "—",
                 delivery["name"] if delivery else "—"],
                buttons=[
                    ("Részletek", lambda p=package: self._details(p["id"]), None),
                    ("Kiosztás", lambda p=package: self._assign(p), None),
                ],
                color_index=1,
                color=status_color(package["current_status"]),
            )

    def build_dispatch(self, parent):
        parent.grid_rowconfigure(3, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(parent, text="🔄  Frissítés", width=120,
                      command=self.refresh_dispatch).grid(row=0, column=0, sticky="w",
                                                          pady=(0, 10))

        ctk.CTkLabel(
            parent,
            text="Beérkezésre váró csomagok — a futár felvette, de még nincs a raktárban",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 4))

        self.arriving_table = Table(
            parent,
            columns=[("Az.", 45), ("Feladó", 150), ("Címzett", 150),
                     ("Méret / súly", 110), ("Felvevő futár", 140)],
        )
        self.arriving_table.grid(row=2, column=0, sticky="nsew", pady=(0, 14))

        ctk.CTkLabel(
            parent,
            text="Kiosztásra váró csomagok — raktárban vannak, futár kell hozzájuk",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).grid(row=3, column=0, sticky="w", pady=(0, 4))

        self.waiting_table = Table(
            parent,
            columns=[("Az.", 45), ("Feladó", 150), ("Címzett", 150),
                     ("Cél város", 130), ("Állapot", 158)],
        )
        self.waiting_table.grid(row=4, column=0, sticky="nsew")
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_rowconfigure(4, weight=1)
        parent.grid_rowconfigure(3, weight=0)

    def refresh_dispatch(self):
        if not hasattr(self, "arriving_table"):
            return

        ok, arriving = self.api.list_packages(status=ARRIVING)
        if not ok:
            self.arriving_table.show_message(str(arriving))
            return

        self.arriving_table.clear()
        if not arriving:
            self.arriving_table.show_message("Nincs beérkezésre váró csomag.")
        else:
            for package in arriving:
                pickup = package.get("pickup_courier")
                self.arriving_table.add_row(
                    [f"#{package['id']}", package["pickup_contact"]["name"],
                     package["delivery_contact"]["name"],
                     f"{package['size']} / {package['weight']} kg",
                     pickup["name"] if pickup else "—"],
                    buttons=[
                        ("Részletek", lambda p=package: self._details(p["id"]), None),
                        ("Beérkeztetés", lambda p=package: self._receive(p), None),
                    ],
                )

        ok, waiting = self.api.list_packages(status="in_warehouse")
        if not ok:
            self.waiting_table.show_message(str(waiting))
            return

        self.waiting_table.clear()
        if not waiting:
            self.waiting_table.show_message("Nincs kiosztásra váró csomag a raktárban.")
            return

        for package in waiting:
            self.waiting_table.add_row(
                [f"#{package['id']}", package["pickup_contact"]["name"],
                 package["delivery_contact"]["name"],
                 package["delivery_contact"]["city"],
                 status_label(package["current_status"])],
                buttons=[
                    ("Részletek", lambda p=package: self._details(p["id"]), None),
                    ("Kiszállításra", lambda p=package: self._assign(p, "Kiszállítás"), None),
                ],
                color_index=4,
                color=status_color(package["current_status"]),
            )

    def build_couriers(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(parent, text="🔄  Frissítés", width=120,
                      command=self.refresh_couriers).grid(row=0, column=0, sticky="w",
                                                          pady=(0, 10))

        self.couriers_table = Table(
            parent,
            columns=[("Név", 170), ("Rendszám", 110), ("Kapacitás", 100),
                     ("Terhelés", 150), ("Állapot", 120)],
        )
        self.couriers_table.grid(row=1, column=0, sticky="nsew")

    def refresh_couriers(self):
        if not hasattr(self, "couriers_table"):
            return

        ok, data = self.api.list_couriers()
        if not ok:
            self.couriers_table.show_message(str(data))
            return

        self.couriers_cache = data
        self.couriers_table.clear()

        if not data:
            self.couriers_table.show_message("Még nincs futár a rendszerben.")
            return

        for courier in data:
            available = courier["is_available"]
            self.couriers_table.add_row(
                [courier["name"], courier["vehicle_plate_number"],
                 f"{courier['max_capacity']} kg",
                 f"{courier['current_load']} kg / {courier['active_package_count']} db",
                 "Elérhető" if available else "Nem elérhető"],
                color_index=4,
                color="#16a34a" if available else "#dc2626",
            )

    def on_show(self):
        self.show_panel("stock")
