import customtkinter as ctk
from src.api.base_api import BaseAPI


class PackageDetailView(ctk.CTkFrame):
    """A kiválasztott csomag adatait ID alapján lekérdező és megjelenítő nézet."""
    def __init__(self, master, package_id, controller=None):
        super().__init__(master, fg_color="transparent")
        self.package_id = package_id
        self.controller = controller

        # Fő görgethető keret
        self.scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Adat lekérése API-n keresztül az induláskor (Initial load)
        self.package_data = self.fetch_package_details()

        # UI felépítése a kapott adatok alapján
        self.build_ui()

    def fetch_package_details(self):
        """Lekéri az egyedi csomag adatait a backendről a megadott ID alapján."""
        try:
            api = BaseAPI()
            response = api.client.get(f"/orders/{self.package_id}")
            api.close()

            if response.status_code == 200:
                return response.json()
            else:
                err_msg = response.text
                print(f"Hiba a csomag lekérésekor: ({response.status_code}): {err_msg}")
                return None
        except Exception as e:
            print(f"Kapcsolódási hiba: {e}")
            return None

    def build_ui(self):
        """Felépíti a felületet a lekért adatokkal."""
        # Címsor és Vissza gomb
        top_bar = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 15))

        title_text = f"Csomag Részletek (ID: {self.package_id})"
        if self.package_data:
            title_text = f"Csomag Részletek (ID: {self.package_data.get('id')})"

        self.title_label = ctk.CTkLabel(
            top_bar, 
            text=title_text, 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(side="left")

        self.back_btn = ctk.CTkButton(
            top_bar, 
            text="← Vissza a listához", 
            width=130, 
            command=self.go_back
        )
        self.back_btn.pack(side="right")

        if not self.package_data:
            err_lbl = ctk.CTkLabel(self.scrollable_frame, text="Nem sikerült betölteni a csomag adatait a szerverről.", text_color="red", font=ctk.CTkFont(size=14))
            err_lbl.pack(pady=30)
            return

        # --- 1. Csomag alapadatok kártya ---
        self.create_info_card("Csomag Alapadatok", [
            ("Tracking ID:", str(self.package_data.get("tracking_id"))),
            ("Méret:", str(self.package_data.get("size"))),
            ("Súly:", f"{self.package_data.get('weight')} kg"),
            ("Felvételi Dátum:", str(self.package_data.get("pickup_date"))),
            ("Felvételi Idősáv:", str(self.package_data.get("pickup_time_slot"))),
            ("Jelenlegi Státusz:", str(self.package_data.get("current_status"))),
        ])

        # --- 2. Feladó (Pickup) kontakt adatok kártya ---
        p_contact = self.package_data.get("pickup_contact") or {}
        self.create_info_card("Feladó Kontakt Adatok", [
            ("Név:", p_contact.get("name", "N/A")),
            ("Email:", p_contact.get("email", "N/A")),
            ("Telefonszám:", p_contact.get("phone", "N/A")),
            ("Irányítószám:", p_contact.get("zip_code", "N/A")),
            ("Város:", p_contact.get("city", "N/A")),
            ("Utca, házszám:", p_contact.get("street_address", "N/A")),
        ])

        # --- 3. Címzett / Fogadó (Delivery) kontakt adatok kártya ---
        d_contact = self.package_data.get("delivery_contact") or {}
        self.create_info_card("Címzett Kontakt Adatok", [
            ("Név:", d_contact.get("name", "N/A")),
            ("Email:", d_contact.get("email", "N/A")),
            ("Telefonszám:", d_contact.get("phone", "N/A")),
            ("Irányítószám:", d_contact.get("zip_code", "N/A")),
            ("Város:", d_contact.get("city", "N/A")),
            ("Utca, házszám:", d_contact.get("street_address", "N/A")),
        ])

    def create_info_card(self, title, items):
        """Segédfüggvény egy vizuális kártya létrehozásához az adatoknak."""
        card = ctk.CTkFrame(self.scrollable_frame, corner_radius=8)
        card.pack(fill="x", pady=10, padx=5)

        title_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        title_lbl.pack(anchor="w", padx=15, pady=(12, 8))

        for label_text, value_text in items:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)

            lbl = ctk.CTkLabel(row, text=label_text, width=160, anchor="w", font=ctk.CTkFont(weight="bold"))
            lbl.pack(side="left")

            val = ctk.CTkLabel(row, text=value_text, anchor="w")
            val.pack(side="left", expand=True, fill="x")

        ctk.CTkLabel(card, text="", height=5).pack()

    def go_back(self):
        """Visszanavigál a csomaglistához."""
        main_layout = self.master
        while main_layout and not hasattr(main_layout, "load_package_list"):
            main_layout = main_layout.master

        if main_layout and hasattr(main_layout, "load_package_list"):
            main_layout.load_package_list()