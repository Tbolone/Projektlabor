import customtkinter as ctk

class RegisteredCustomerView(ctk.CTkFrame):
    """A 'Home' menüpontra betöltődő kezdőnézet."""
    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="transparent")
        
        self.welcome_label = ctk.CTkLabel(
            self,
            text="Üdvözöljük a Pagyar Mostánál, ahol csomagja valamikor biztos célba ér!",
            font=ctk.CTkFont(size=24, weight="bold"),
            wraplength=500,
            justify="center",
        )
        self.welcome_label.pack(expand=True, padx=30, pady=30)