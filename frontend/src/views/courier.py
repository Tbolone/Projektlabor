import customtkinter as ctk

from src.api.courier_api import CourierAPI
from src.views.base_layout import SidebarView
from src.views.widgets import (
    ConfirmDialog,
    FormDialog,
    StatCard,
    Table,
    status_color,
    status_label,
)

NEXT_ACTION = {
    "assigned_for_pickup": ("Indulás", "start_pickup", "pickup"),
    "out_for_pickup": ("Felvettem", "confirm_pickup", "pickup"),
    "picked_up": ("Leadás raktárban", "deliver_to_warehouse", "pickup"),
    "assigned_for_delivery": ("Indulás", "start_delivery", "delivery"),
    "out_for_delivery": ("Kézbesítve", "confirm_delivery", "delivery"),
}


class CourierView(SidebarView):
    MENU_ITEMS = [
        ("📋  Feladataim", "tasks"),
        ("🕘  Szállítási történet", "history"),
        ("👤  Profilom", "profile"),
    ]
    SUBTITLE = "Futár felület"

    def __init__(self, master, controller):
        self.api = CourierAPI()
        self.profile = None
        super().__init__(master, controller)

    def build_tasks(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            toolbar, text="🔄  Frissítés", width=120, command=self.refresh_tasks
        ).grid(row=0, column=0, padx=(0, 10))

        self.tasks_summary = ctk.CTkLabel(toolbar, text="", anchor="w")
        self.tasks_summary.grid(row=0, column=1, sticky="w")

        self.tasks_table = Table(
            parent,
            columns=[
                ("Az.", 45),
                ("Feladat", 90),
                ("Cím", 165),
                ("Méret / súly", 100),
                ("Idősáv", 95),
                ("Állapot", 175),
            ],
        )
        self.tasks_table.grid(row=1, column=0, sticky="nsew")

    def refresh_tasks(self):
        ok, data = self.api.get_tasks()
        if not ok:
            self.tasks_table.show_message(str(data))
            self.set_status(str(data), error=True)
            return

        self.tasks_table.clear()

        if not data:
            self.tasks_table.show_message(
                "Jelenleg nincs hozzád rendelt csomag. A raktáros kiosztása után itt jelennek meg a feladataid."
            )
            self.tasks_summary.configure(text="0 aktív feladat")
            return

        pickup_count = sum(
            1 for p in data if p["current_status"] in ("assigned_for_pickup", "out_for_pickup")
        )
        delivery_count = len(data) - pickup_count
        self.tasks_summary.configure(
            text=f"{len(data)} aktív feladat  ·  {pickup_count} felvétel, {delivery_count} kiszállítás"
        )

        for package in data:
            status = package["current_status"]
            is_pickup = status in ("assigned_for_pickup", "out_for_pickup")
            stage_text = "Felvétel" if is_pickup else "Kiszállítás"
            contact = package["pickup_contact"] if is_pickup else package["delivery_contact"]
            address = f"{contact['name']} — {contact['zip_code']} {contact['city']}, {contact['street_address']}"

            buttons = [("Részletek", lambda p=package: self._show_details(p["id"]), None)]

            action = NEXT_ACTION.get(status)
            if action:
                text, method, _ = action
                buttons.append(
                    (text, lambda p=package, m=method: self._do_action(p, m), None)
                )

            if status in ("out_for_delivery", "out_for_pickup"):
                buttons.append(
                    ("Sikertelen", lambda p=package: self._report_failure(p), "#dc2626")
                )

            self.tasks_table.add_row(
                [
                    f"#{package['id']}",
                    stage_text,
                    address,
                    f"{package['size']} / {package['weight']} kg",
                    package["pickup_time_slot"],
                    status_label(status),
                ],
                buttons=buttons,
                color_index=5,
                color=status_color(status),
            )

    def _do_action(self, package, method_name):
        method = getattr(self.api, method_name)
        ok, data = method(package["id"])

        if ok:
            self.set_status(f"#{package['id']} — {status_label(data['current_status'])}")
            self.refresh_tasks()
        else:
            self.set_status(str(data), error=True)

    def _report_failure(self, package):
        dialog = FormDialog(
            self,
            f"Sikertelen kézbesítés — #{package['id']}",
            [("comment", "Mi történt?", "text", "Az átvételt megtagadták", None)],
            submit_text="Rögzítés",
        )
        values = dialog.show()
        if values is None:
            return

        ok, data = self.api.report_failure(package["id"], values["comment"] or None)
        if ok:
            self.set_status(f"#{package['id']} — sikertelen kézbesítés rögzítve")
            self.refresh_tasks()
        else:
            self.set_status(str(data), error=True)

    def _show_details(self, package_id):
        ok, package = self.api.get_package(package_id)
        if not ok:
            self.set_status(str(package), error=True)
            return

        window = ctk.CTkToplevel(self)
        window.title(f"Csomag #{package['id']}")
        window.geometry("620x560")
        window.transient(self.winfo_toplevel())

        container = ctk.CTkScrollableFrame(window)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            container,
            text=f"Csomag #{package['id']}",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            container,
            text=status_label(package["current_status"]),
            text_color=status_color(package["current_status"]),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(
            container,
            text=f"Követési azonosító: {package['tracking_id']}",
            text_color=("gray40", "gray60"),
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", pady=(0, 10))

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
                    + (f"\nMegjegyzés: {contact['comment']}" if contact.get("comment") else "")
                ),
                justify="left",
                anchor="w",
            ).pack(anchor="w")

        ctk.CTkLabel(
            container, text="Csomag adatai", font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(14, 2))
        ctk.CTkLabel(
            container,
            text=(
                f"Méret: {package['size']}   ·   Súly: {package['weight']} kg\n"
                f"Tervezett felvétel: {package['pickup_date']} ({package['pickup_time_slot']})"
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
            if event.get("courier_name"):
                line += f"  ({event['courier_name']})"
            if event.get("comment"):
                line += f"\n        {event['comment']}"
            ctk.CTkLabel(container, text=line, justify="left", anchor="w").pack(
                anchor="w", pady=1
            )

    def build_history(self, parent):
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(toolbar, text="Bontás:").grid(row=0, column=0, padx=(0, 8))

        self.period_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["Napi", "Heti", "Havi"],
            width=140,
            command=lambda _: self.refresh_history(),
        )
        self.period_menu.set("Napi")
        self.period_menu.grid(row=0, column=1, padx=(0, 10))

        ctk.CTkButton(
            toolbar, text="🔄  Frissítés", width=120, command=self.refresh_history
        ).grid(row=0, column=2)

        self.history_table = Table(
            parent,
            columns=[("Időszak", 220), ("Kiszállítva", 140), ("Felvéve", 140)],
        )
        self.history_table.grid(row=1, column=0, sticky="nsew")

    def refresh_history(self):
        mapping = {"Napi": "day", "Heti": "week", "Havi": "month"}
        period = mapping.get(self.period_menu.get(), "day")

        ok, data = self.api.get_history(period)
        if not ok:
            self.history_table.show_message(str(data))
            return

        self.history_table.clear()

        if not data:
            self.history_table.show_message(
                "Még nincs rögzített szállításod. Az első felvétel vagy kézbesítés után itt jelenik meg a történet."
            )
            return

        for row in data:
            self.history_table.add_row(
                [row["period"], f"{row['delivered']} db", f"{row['picked_up']} db"]
            )

    def build_profile(self, parent):
        parent.grid_columnconfigure(0, weight=1)

        self.profile_cards = ctk.CTkFrame(parent, fg_color="transparent")
        self.profile_cards.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        self.profile_box = ctk.CTkFrame(parent, corner_radius=8)
        self.profile_box.grid(row=1, column=0, sticky="ew")
        self.profile_box.grid_columnconfigure(1, weight=1)

        self.profile_labels = {}
        rows = [
            ("name", "Név"),
            ("email", "Email"),
            ("vehicle_plate_number", "Rendszám"),
            ("max_capacity", "Maximális kapacitás"),
        ]
        for index, (key, label) in enumerate(rows):
            ctk.CTkLabel(
                self.profile_box, text=label, anchor="w", text_color=("gray40", "gray60")
            ).grid(row=index, column=0, padx=20, pady=8, sticky="w")

            value_label = ctk.CTkLabel(self.profile_box, text="—", anchor="w")
            value_label.grid(row=index, column=1, padx=20, pady=8, sticky="w")
            self.profile_labels[key] = value_label

        availability_row = ctk.CTkFrame(parent, corner_radius=8)
        availability_row.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        availability_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            availability_row,
            text="Elérhetőség",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=20, pady=(15, 2), sticky="w")

        ctk.CTkLabel(
            availability_row,
            text="Ha kikapcsolod, a raktáros nem oszt rád új csomagot.",
            text_color=("gray40", "gray60"),
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="w")

        self.availability_switch = ctk.CTkSwitch(
            availability_row,
            text="Dolgozom, kaphatok új feladatot",
            command=self._toggle_availability,
        )
        self.availability_switch.grid(row=2, column=0, padx=20, pady=(0, 18), sticky="w")

    def refresh_profile(self):
        ok, data = self.api.get_profile()
        if not ok:
            self.set_status(str(data), error=True)
            return

        self.profile = data

        self.profile_labels["name"].configure(text=data["name"])
        self.profile_labels["email"].configure(text=data["email"])
        self.profile_labels["vehicle_plate_number"].configure(
            text=data["vehicle_plate_number"]
        )
        self.profile_labels["max_capacity"].configure(text=f"{data['max_capacity']} kg")

        if data["is_available"]:
            self.availability_switch.select()
        else:
            self.availability_switch.deselect()

        for child in self.profile_cards.winfo_children():
            child.destroy()

        cards = [
            ("Aktív csomag", data["active_package_count"], "#2563eb"),
            ("Jelenlegi terhelés", f"{data['current_load']} kg", "#0891b2"),
            (
                "Szabad kapacitás",
                f"{round(data['max_capacity'] - data['current_load'], 2)} kg",
                "#16a34a",
            ),
        ]
        for index, (title, value, accent) in enumerate(cards):
            self.profile_cards.grid_columnconfigure(index, weight=1)
            StatCard(self.profile_cards, title, value, accent).grid(
                row=0, column=index, padx=(0 if index == 0 else 10, 0), sticky="ew"
            )

    def _toggle_availability(self):
        is_available = bool(self.availability_switch.get())
        ok, data = self.api.set_availability(is_available)

        if ok:
            self.set_status(
                "Elérhető vagy új feladatra" if is_available else "Nem kapsz új feladatot"
            )
            self.refresh_profile()
        else:
            self.set_status(str(data), error=True)
            self.refresh_profile()

    def on_show(self):
        self.show_panel("tasks")
