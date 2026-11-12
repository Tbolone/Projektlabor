import customtkinter as ctk
from src.api.base_api import BaseAPI

class CreateOrderView(ctk.CTkFrame):
    """A 'Create Order' (Csomagfeladás) menüpontra betöltődő űrlap nézet."""
    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="transparent")
        self.controller = controller
        
        # Fő görgethető keret az űrlapnak
        self.scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True)

        self.title_label = ctk.CTkLabel(
            self.scrollable_frame, 
            text="Csomag Adatfelvétel", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=(0, 15), anchor="w", padx=15)

        # --- 1. BLOKK: FELADÓ ADATAI ---
        self.sender_frame = self.create_section_frame("Feladó adatai")
        self.sender_name = self.add_form_field(self.sender_frame, "Név (Name):")
        self.sender_email = self.add_form_field(self.sender_frame, "E-mail cím:")
        self.sender_phone = self.add_form_field(self.sender_frame, "Telefonszám (Phone):")
        self.sender_zip = self.add_form_field(self.sender_frame, "Irányítószám (Zip code):")
        self.sender_city = self.add_form_field(self.sender_frame, "Város (City):")
        self.sender_street = self.add_form_field(self.sender_frame, "Utca, házszám (Street address):")

        # --- 2. BLOKK: CÍMZETT ADATAI ---
        self.recipient_frame = self.create_section_frame("Címzett adatai")
        self.recipient_name = self.add_form_field(self.recipient_frame, "Név (Name):")
        self.recipient_email = self.add_form_field(self.recipient_frame, "E-mail cím:")
        self.recipient_phone = self.add_form_field(self.recipient_frame, "Telefonszám (Phone):")
        self.recipient_zip = self.add_form_field(self.recipient_frame, "Irányítószám (Zip code):")
        self.recipient_city = self.add_form_field(self.recipient_frame, "Város (City):")
        self.recipient_street = self.add_form_field(self.recipient_frame, "Utca, házszám (Street address):")

        # --- 3. BLOKK: CSOMAG ÉS FELVÉTELI ADATAI ---
        self.package_frame = self.create_section_frame("Csomag és Felvételi adatok")
        
        self.package_size = self.add_dropdown_field(
            self.package_frame, "Méret (Size):", 
            ["S (Kisdoboz)", "M (Közepes)", "L (Nagy)", "XL (Extra nagy)"]
        )
        self.package_weight = self.add_form_field(self.package_frame, "Súly (kg - float):")
        self.pickup_date = self.add_form_field(self.package_frame, "Felvételi dátum (ÉÉÉÉ-HH-NN):")
        self.pickup_time_slot = self.add_dropdown_field(
            self.package_frame, "Felvételi idősáv:", 
            ["08:00 - 12:00", "12:00 - 16:00", "16:00 - 20:00"]
        )

        # Küldés gomb
        self.submit_btn = ctk.CTkButton(
            self.scrollable_frame, 
            text="Űrlap beküldése", 
            command=self.handle_submit,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40
        )
        self.submit_btn.pack(pady=20, fill="x", padx=15)

    def create_section_frame(self, title_text):
        frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=8)
        frame.pack(fill="x", pady=10, padx=10)
        label = ctk.CTkLabel(frame, text=title_text, font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(anchor="w", padx=15, pady=(10, 5))
        return frame

    def add_form_field(self, parent_frame, label_text):
        container = ctk.CTkFrame(parent_frame, fg_color="transparent")
        container.pack(fill="x", padx=15, pady=4)
        label = ctk.CTkLabel(container, text=label_text, width=220, anchor="w")
        label.pack(side="left")
        entry = ctk.CTkEntry(container)
        entry.pack(side="right", expand=True, fill="x")
        return entry

    def add_dropdown_field(self, parent_frame, label_text, values):
        container = ctk.CTkFrame(parent_frame, fg_color="transparent")
        container.pack(fill="x", padx=15, pady=4)
        label = ctk.CTkLabel(container, text=label_text, width=220, anchor="w")
        label.pack(side="left")
        dropdown = ctk.CTkOptionMenu(container, values=values)
        dropdown.pack(side="right", expand=True, fill="x")
        return dropdown

    def handle_submit(self):
        """Kinyeri és strukturálja az űrlap adatait."""
        try:
            weight_val = float(self.package_weight.get().strip().replace(',', '.')) if self.package_weight.get() else 0.0
        except ValueError:
            weight_val = 0.0

        data = {
            "sender": {
                "name": self.sender_name.get(), 
                "email": self.sender_email.get(),
                "phone": self.sender_phone.get(),
                "zip": self.sender_zip.get(), 
                "city": self.sender_city.get(), 
                "street": self.sender_street.get()
            },
            "receiver": {
                "name": self.recipient_name.get(), 
                "email": self.recipient_email.get(),
                "phone": self.recipient_phone.get(),
                "zip": self.recipient_zip.get(), 
                "city": self.recipient_city.get(), 
                "street": self.recipient_street.get()
            },
            "package": {
                "size": self.package_size.get(),
                "weight": weight_val,
                "pickup_date": self.pickup_date.get() or None,
                "pickup_time_slot": self.pickup_time_slot.get(),
            }
        }

        print("Küldés a szerverre...", data)

        # Példányosítjuk a BaseAPI-t token nélkül, majd elküldjük a kérést és bezárjuk
        api = BaseAPI()
        try:
            response = api.client.post("/orders/", json=data)
            
            if response.status_code in (200, 201):
                result = response.json()
                print("Sikeres mentés!", result)
            else:
                print(f"Hiba történt a szerveren! Státusz: {response.status_code}, Válasz: {response.text}")
                
        except Exception as e:
            print(f"Hiba a kérés küldése során: {e}")
        finally:
            api.close()