import customtkinter as ctk

class LoginView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)

        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        

        self.email = ctk.CTkEntry(self, placeholder_text="Email", height=40)
        self.email.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        self.password = ctk.CTkEntry(self, placeholder_text="Password", height=40)
        self.password.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        self.error_label = ctk.CTkLabel(self, text="", text_color="red")
        self.error_label.grid(row=3, column=1, padx=10, pady=(0, 5), sticky="nsew")

        self.login_btn = ctk.CTkButton(self, text="Login", command=self.login, height=40)
        self.login_btn.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")

        self.password.bind("<Return>", lambda event: self.login())

    def login(self):
        email = self.email.get().strip()
        password = self.password.get()

        self.login_btn.configure(state="disabled", text="Bejelentkezés...")
        self.error_label.configure(text="")

        success, message = self.login_controller.login(email, password)

        self.login_btn.configure(state="normal", text="Login")

        if success:
            self.controller.show_view("home")
        else:
            self.error_label.configure(text=message)

