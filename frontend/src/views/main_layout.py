import customtkinter as ctk
from src.views.create_order import CreateOrderView
from src.views.registered_customer import RegisteredCustomerView

class MainLayoutView(ctk.CTkFrame):
    """A fő keret, ami tartalmazza a bal oldali dinamikus menüt és a jobb oldali content terüleltet."""
    
    # Itt definiálod a menüpontokat: (Megjelenő szöveg, útvonal azonosító, hozzá tartozó View osztály)
    MENU_ITEMS = [
        ("🏠  Kezdőlap", "home", RegisteredCustomerView),
        ("📦  Csomagfeladás", "create_order", CreateOrderView),
    ]

    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        # Layout rács beállítása: 0. oszlop = fix oldalsáv, 1. oszlop = rugalmas tartalom
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Alapértelmezésként az első menüpontot (Home) töltjük be indításkor
        self._navigate("home", RegisteredCustomerView)

    def _build_sidebar(self):
        """Felépíti a bal oldali sávot és dinamikusan rendereli a MENU_ITEMS alapján a gombokat."""
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(10, weight=1)  # Térköz a beállítások gomb tolásához alulra

        # Logó / Céges név
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Pagyar Mosta Zrt.",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        # Menüpontok dinamikus renderelése cikluson keresztül
        for i, (text, route, view_class) in enumerate(self.MENU_ITEMS, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                anchor="w",
                height=40,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda r=route, vc=view_class: self._navigate(r, vc),
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")

        # Beállítások gomb (opcionális alulra rögzítve)
        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="⚙  Beállítások",
            anchor="w",
            height=40,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=lambda: print("Beállítások kattintva"),
        )
        self.settings_button.grid(row=11, column=0, padx=15, pady=(5, 20), sticky="ew")
        self.sidebar.grid_columnconfigure(0, weight=1)

    def _build_content_area(self):
        """Létrehozza a jobb oldali tartalom tároló keretet."""
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _navigate(self, route, view_class):
        """Törli az aktuális tartalmat a jobb oldalon, majd példányosítja és betölti az új View-t."""
        for widget in self.content.winfo_children():
            widget.destroy()

        # Példányosítjuk a kívánt nézetet a content kereten belül
        current_view = view_class(self.content)
        current_view.grid(row=0, column=0, sticky="nsew")
         