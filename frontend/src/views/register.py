# views/register.py
import customtkinter as ctk
from src.api import auth_api

class RegisterView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.api = auth_api.AuthAPI()

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.name = ctk.CTkEntry(self, placeholder_text="Name", height=40)
        self.name.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        self.email = ctk.CTkEntry(self, placeholder_text="Email", height=40)
        self.email.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        self.password = ctk.CTkEntry(self, placeholder_text="Password", show="*", height=40)
        self.password.grid(row=3, column=1, padx=10, pady=5, sticky="nsew")

        self.password_again = ctk.CTkEntry(self, placeholder_text="Password again", show="*", height=40)
        self.password_again.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.grid(row=5, column=1, padx=10, pady=(0, 5), sticky="nsew")

        self.register_btn = ctk.CTkButton(self, text="Register", height=40, command=self.register)
        self.register_btn.grid(row=6, column=1, padx=10, pady=5, sticky="nsew")

        self.back_btn = ctk.CTkButton(
            self, text="Back to login", height=28, fg_color="transparent",
            text_color=("gray10", "gray90"),
            command=lambda: self.controller.show_view("login")
        )
        self.back_btn.grid(row=7, column=1, padx=10, pady=(0, 10), sticky="n")

        self.password_again.bind("<Return>", lambda event: self.register())

    def register(self):
        name = self.name.get().strip()
        email = self.email.get().strip()
        password = self.password.get()
        password_again = self.password_again.get()

        self.register_btn.configure(state="disabled", text="Regisztráció...")
        self.error_label.configure(text="")

        success, message = self.register_controller.register(email, name, password, password_again)

        self.register_btn.configure(state="normal", text="Register")

        if success:
            self.clear_fields()
            self.controller.show_view("login")
        else:
            self.error_label.configure(text=message)

    def clear_fields(self):
        self.name.delete(0, "end")
        self.email.delete(0, "end")
        self.password.delete(0, "end")
        self.password_again.delete(0, "end")