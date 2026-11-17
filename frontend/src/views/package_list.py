import customtkinter as ctk
from src.api.base_api import BaseAPI


class PackageListView(ctk.CTkFrame):
    """A csomagok listáját rácsos (grid) elrendezésű táblázatban megjelenítő nézet."""
    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        # Címsor és Frissítés gomb sáv
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        self.title_label = ctk.CTkLabel(
            header_frame, 
            text="Csomagok Listája", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            header_frame, 
            text="🔄 Frissítés", 
            width=100, 
            command=self.load_packages
        )
        self.refresh_btn.pack(side="right")

        # Görgethető keret a táblázathoz
        self.scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=8)
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.load_packages()

    def load_packages(self):
        """Lekéri a csomagokat a FastAPI backendről, és rácsos (grid) szerkezetbe rendezve írja ki."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            api = BaseAPI()
            response = api.client.get("/orders/")
            api.close()

            if response.status_code == 200:
                packages = response.json()
                
                if not packages:
                    empty_lbl = ctk.CTkLabel(self.scrollable_frame, text="Nincsenek rögzített csomagok az adatbázisban.", font=ctk.CTkFont(size=14))
                    empty_lbl.pack(pady=20)
                    return

                def configure_grid_columns(row_frame):
                    row_frame.grid_columnconfigure(0, weight=1, minsize=40)   # ID
                    row_frame.grid_columnconfigure(1, weight=2, minsize=110)  # Méret / Súly
                    row_frame.grid_columnconfigure(2, weight=3, minsize=200)  # Felvételi Cím
                    row_frame.grid_columnconfigure(3, weight=2, minsize=140)  # Küldő Email
                    row_frame.grid_columnconfigure(4, weight=2, minsize=140)  # Fogadó Email
                    row_frame.grid_columnconfigure(5, weight=1, minsize=80)   # Státusz
                    row_frame.grid_columnconfigure(6, weight=1, minsize=80)   # Edit Gomb

                # --- TÁBLÁZAT FEJLÉC ---
                header_row = ctk.CTkFrame(self.scrollable_frame, fg_color=("gray80", "gray20"), height=40)
                header_row.pack(fill="x", pady=2)
                configure_grid_columns(header_row)

                ctk.CTkLabel(header_row, text="ID", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, padx=5, sticky="ew")
                ctk.CTkLabel(header_row, text="Méret / Súly", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=1, padx=5, sticky="ew")
                ctk.CTkLabel(header_row, text="Felvételi Cím", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=2, padx=5, sticky="ew")
                ctk.CTkLabel(header_row, text="Küldő Email", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=3, padx=5, sticky="ew")
                ctk.CTkLabel(header_row, text="Fogadó Email", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=4, padx=5, sticky="ew")
                ctk.CTkLabel(header_row, text="Státusz", font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=5, padx=5, sticky="ew")
                ctk.CTkLabel(header_row, text="Művelet", font=ctk.CTkFont(weight="bold"), anchor="center").grid(row=0, column=6, padx=5, sticky="ew")

                # --- TÁBLÁZAT SOROK ---
                for pkg in packages:
                    row_frame = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent", height=45)
                    row_frame.pack(fill="x", pady=2)
                    configure_grid_columns(row_frame)

                    pkg_id = pkg.get("id")

                    # 1. ID
                    ctk.CTkLabel(row_frame, text=str(pkg.get("id")), anchor="w").grid(row=0, column=0, padx=5, sticky="ew")
                    
                    # 2. Méret / Súly
                    size_weight = f"{pkg.get('size', '')} / {pkg.get('weight', '')}kg"
                    ctk.CTkLabel(row_frame, text=size_weight, anchor="w").grid(row=0, column=1, padx=5, sticky="ew")

                    # 3. Cím konkatenálása
                    p_contact = pkg.get("pickup_contact")
                    if p_contact:
                        full_address = f"{p_contact.get('zip_code', '')} {p_contact.get('city', '')}, {p_contact.get('street_address', '')}"
                    else:
                        full_address = "Nincs adat"
                    ctk.CTkLabel(row_frame, text=full_address, anchor="w").grid(row=0, column=2, padx=5, sticky="ew")

                    # 4. Küldő email
                    sender_data = pkg.get("sender")
                    sender_email = sender_data.get("email") if sender_data else "Ismeretlen"
                    ctk.CTkLabel(row_frame, text=sender_email, anchor="w").grid(row=0, column=3, padx=5, sticky="ew")

                    # 5. Fogadó email
                    receiver_data = pkg.get("receiver")
                    receiver_email = receiver_data.get("email") if receiver_data else "Nincs megadva"
                    ctk.CTkLabel(row_frame, text=receiver_email, anchor="w").grid(row=0, column=4, padx=5, sticky="ew")

                    # 6. Státusz
                    ctk.CTkLabel(row_frame, text=str(pkg.get("current_status")), text_color="green", anchor="w").grid(row=0, column=5, padx=5, sticky="ew")

                    # 7. Edit gomb (átadja az adott csomag adatait a részletek nézetnek)
                    edit_btn = ctk.CTkButton(
                        row_frame, 
                        text="Részletek", 
                        width=70, 
                        height=28,
                        command=lambda id_val=pkg_id: self.open_package_detail(id_val)
                    )
                    edit_btn.grid(row=0, column=6, padx=5, sticky="e")

            else:
                err_lbl = ctk.CTkLabel(self.scrollable_frame, text=f"Hiba a betöltés során: {response.status_code}", text_color="red")
                err_lbl.pack(pady=20)

        except Exception as e:
            err_lbl = ctk.CTkLabel(self.scrollable_frame, text=f"Nem sikerült kapcsolódni a szerverhez: {e}", text_color="red")
            err_lbl.pack(pady=20)

    def open_package_detail(self, package_id):
        """Átlép a részletek nézetre, átadva kizárólag a csomag ID-ját."""
        main_layout = self.master
        while main_layout and not hasattr(main_layout, "load_package_detail"):
            main_layout = main_layout.master

        if main_layout and hasattr(main_layout, "load_package_detail"):
            main_layout.load_package_detail(package_id)
        else:
            print("[Hiba] Nem található a nézetváltó metódus a szülő komponensen.")