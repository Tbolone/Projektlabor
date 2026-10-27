import customtkinter as ctk


class SidebarView(ctk.CTkFrame):
    MENU_ITEMS: list[tuple[str, str]] = []
    TITLE = "Pagyar Mosta Zrt."
    SUBTITLE = ""

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.panels: dict[str, ctk.CTkFrame] = {}
        self.menu_buttons: dict[str, ctk.CTkButton] = {}
        self.active_panel: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(10, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text=self.TITLE,
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 2))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar,
            text=self.SUBTITLE,
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        for index, (text, route) in enumerate(self.MENU_ITEMS, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                anchor="w",
                height=40,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda r=route: self.show_panel(r),
            )
            btn.grid(row=index, column=0, padx=15, pady=5, sticky="ew")
            self.menu_buttons[route] = btn

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
        self.logout_button.grid(row=11, column=0, padx=15, pady=(5, 20), sticky="ew")

    def _build_content(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        self.panel_title = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=22, weight="bold"), anchor="w"
        )
        self.panel_title.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(header, text="", anchor="e")
        self.status_label.grid(row=0, column=1, sticky="e")

        self.panel_host = ctk.CTkFrame(self.content, fg_color="transparent")
        self.panel_host.grid(row=1, column=0, sticky="nsew", padx=25, pady=(0, 20))
        self.panel_host.grid_rowconfigure(0, weight=1)
        self.panel_host.grid_columnconfigure(0, weight=1)

    def show_panel(self, key: str):
        if key not in self.panels:
            builder = getattr(self, f"build_{key}", None)
            if not callable(builder):
                self.set_status(f"Nincs még ilyen képernyő: {key}", error=True)
                return

            panel = ctk.CTkFrame(self.panel_host, fg_color="transparent")
            panel.grid(row=0, column=0, sticky="nsew")
            builder(panel)
            self.panels[key] = panel

        self.panels[key].tkraise()
        self.active_panel = key
        self.set_status("")

        title = next((text for text, route in self.MENU_ITEMS if route == key), "")
        self.panel_title.configure(text=title.split("  ", 1)[-1] if title else "")

        refresher = getattr(self, f"refresh_{key}", None)
        if callable(refresher):
            refresher()

        self._highlight_menu(key)

    def _highlight_menu(self, active_key: str):
        for key, button in self.menu_buttons.items():
            if key == active_key:
                button.configure(fg_color=("gray75", "gray25"))
            else:
                button.configure(fg_color="transparent")

    def set_status(self, message: str, error: bool = False):
        color = "#dc2626" if error else "#16a34a"
        self.status_label.configure(text=message, text_color=color)

    def on_show(self):
        if not self.MENU_ITEMS:
            return
        self.show_panel(self.MENU_ITEMS[0][1])

    def _logout(self):
        from src.api.base_api import BaseAPI

        BaseAPI.logout()
        for panel in self.panels.values():
            panel.destroy()
        self.panels.clear()
        self.controller.show_view("login")
