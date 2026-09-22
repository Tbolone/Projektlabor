# views/home.py
import customtkinter as ctk

class HomeView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.welcome_label = ctk.CTkLabel(
            self,
            text="Üdvözlünk!",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.welcome_label.grid(row=0, column=0, sticky="s")