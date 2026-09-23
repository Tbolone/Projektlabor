import customtkinter as ctk
from src.api.auth_api import AuthAPI

class LoginView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)

        self.controller = controller
        self.api = AuthAPI()

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        

        self.email = ctk.CTkEntry(self, placeholder_text="Email", height=40)
        self.email.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        self.password = ctk.CTkEntry(self, placeholder_text="Password", height=40, show="*")
        self.password.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.grid(row=3, column=1, padx=10, pady=(0, 5), sticky="nsew")

        self.login_btn = ctk.CTkButton(self, text="Login", command=self.login, height=40)
        self.login_btn.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")

        self.register_link = ctk.CTkButton(
            self, text="Nincs még fiókod? Regisztrálj", height=28, fg_color="transparent",
            text_color=("gray10", "gray90"),
            command=lambda: self.controller.show_view("register")
        )
        self.register_link.grid(row=5, column=1, padx=10, pady=(0, 10), sticky="n")

        self.password.bind("<Return>", lambda event: self.login())

    def login(self):
        email = self.email.get().strip()
        password = self.password.get()

        self.login_btn.configure(state="disabled", text="Bejelentkezés...")
        self.error_label.configure(text="")

        try:
            success, message = self.api.login(email, password)
            if success:
                self.controller.show_view("home")
            else:
                self.error_label.configure(text=message)
        finally:
            self.login_btn.configure(state="normal", text="Login")
