# src/views/main_layout.py  (a te MainLayoutView fájlod, a Beállítások gomb bekötésével)
import customtkinter as ctk
from src.api.session import logout
from src.views.create_order import CreateOrderView
from src.views.modify_user import ModifyUserView
from src.views.registered_customer import RegisteredCustomerView


class MainLayoutView(ctk.CTkFrame):
    """A fő keret, ami tartalmazza a bal oldali dinamikus menüt és a jobb oldali content területet."""

    # Itt definiálod a menüpontokat: (Megjelenő szöveg, útvonal azonosító, hozzá tartozó View osztály)
    MENU_ITEMS = [
        ("🏠  Kezdőlap", "home", RegisteredCustomerView),
        ("📦  Csomagfeladás", "create_order", CreateOrderView),
    ]

    # (világos téma, sötét téma)
    SIDEBAR_COLOR = ("gray80", "gray10")
    CONTENT_COLOR = ("gray92", "gray14")
    DIVIDER_COLOR = ("gray65", "white")

    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        # Layout rács beállítása: 0. oszlop = fix oldalsáv, 1. oszlop = elválasztó vonal,
        # 2. oszlop = rugalmas tartalom
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)

        self._build_sidebar()
        self._build_divider()
        self._build_content_area()

        self._navigate("home", RegisteredCustomerView)

    def _build_sidebar(self):
        """Felépíti a bal oldali sávot és dinamikusan rendereli a MENU_ITEMS alapján a gombokat."""
        self.sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0, fg_color=self.SIDEBAR_COLOR
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Pagyar Mosta Zrt.",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        # Menüpontok
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

        # Beállítások gomb
        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="⚙  Beállítások",
            anchor="w",
            height=40,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self._open_modify_user,
        )
        self.settings_button.grid(row=11, column=0, padx=15, pady=(5, 5), sticky="ew")

        # Kijelentkezés gomb
        self.logout_button = ctk.CTkButton(
            self.sidebar,
            text="⏻  Kijelentkezés",
            anchor="w",
            height=40,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self._logout,
        )
        self.logout_button.grid(row=12, column=0, padx=15, pady=(5, 20), sticky="ew")
        self.sidebar.grid_columnconfigure(0, weight=1)

    def _build_divider(self):
        """1 pixeles függőleges válaszvonal az oldalsáv és a tartalom között."""
        self.divider = ctk.CTkFrame(
            self, width=1, corner_radius=0, fg_color=self.DIVIDER_COLOR
        )
        self.divider.grid(row=0, column=1, sticky="ns")

    def _build_content_area(self):
        """Létrehozza a jobb oldali tartalom tároló keretet."""
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=self.CONTENT_COLOR)
        self.content.grid(row=0, column=2, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _logout(self):
        """Törli a tokent és az aktuális tartalmat, majd visszalép a belépéshez."""
        logout()

        # Az előző felhasználó nézete ne maradjon meg a következő belépésig
        for widget in self.content.winfo_children():
            widget.destroy()

        login_view = self.controller.views.get("login")
        if login_view is not None and hasattr(login_view, "clear_fields"):
            login_view.clear_fields()

        self.controller.show_view("login")

    def tkraise(self, *args, **kwargs):
        """Az App.show_view ezt hívja. Kijelentkezés után üres a tartalmi rész,
        ilyenkor a következő belépéskor újraépítjük a kezdőlapot."""
        super().tkraise(*args, **kwargs)
        if not self.content.winfo_children():
            self._navigate("home", RegisteredCustomerView)

    def _open_modify_user(self):
        self._navigate(
            "modify_user", lambda master: ModifyUserView(master, self.controller)
        )

    def _navigate(self, route, view_class):
        """Törli az aktuális tartalmat a jobb oldalon, majd példányosítja és betölti az új View-t."""
        for widget in self.content.winfo_children():
            widget.destroy()

        # Példányosítjuk a kívánt nézetet a content kereten belül
        current_view = view_class(self.content)
        current_view.grid(row=0, column=0, sticky="nsew")