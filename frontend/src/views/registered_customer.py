import customtkinter as ctk

class RegisteredCustomerView(ctk.CTkFrame):
    MENU_ITEMS = [
        ("📍  Csomag nyomon követése", "tracking"),
        ("📦  Csomagfeladás", "send_package"),
    ]

    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

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

        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="Pagyar Mosta Zrt.",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))

        for i, (text, route) in enumerate(self.MENU_ITEMS, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                anchor="w",
                height=40,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda r=route: self._navigate(r),
            )
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")

        self.settings_button = ctk.CTkButton(
            self.sidebar,
            text="⚙  Beállítások",
            anchor="w",
            height=40,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=lambda: self._navigate("settings"),
        )
        self.settings_button.grid(row=11, column=0, padx=15, pady=(5, 20), sticky="ew")
        self.sidebar.grid_columnconfigure(0, weight=1)

    def _build_content(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.welcome_label = ctk.CTkLabel(
            self.content,
            text="Üdvözöljük a Pagyar Mostánál, ahol csomagja valamikor biztos célba ér!",
            font=ctk.CTkFont(size=24, weight="bold"),
            wraplength=500,
            justify="center",
        )
        self.welcome_label.grid(row=0, column=0, padx=30, pady=30)

    def _navigate(self, route):
        handler = getattr(self.controller, f"show_{route}", None)
        if callable(handler):
            handler()
        else:
            print(f"[HomeView] Nincs controller.show_{route}() metódus még.")
