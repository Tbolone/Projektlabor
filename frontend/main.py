import sys

try:
    import customtkinter as ctk
    from src.views.login import LoginView
    from src.views.home import HomeView
    from src.views.register import RegisterView
except ModuleNotFoundError as error:
    sys.exit(
        f"Hiányzó csomag: {error.name}\n\n"
        "A frontendet a saját környezetéből kell indítani, a frontend mappából:\n"
        "    uv run python main.py\n\n"
        "Vagy a repo gyökeréből az indítószkripttel:\n"
        "    .\\start.ps1      (Windows)\n"
        "    ./start.sh       (Linux / macOS)\n\n"
        f"A most futó Python: {sys.executable}"
    )

class App(ctk.CTk):
    def __init__(self, view_classes):
        super().__init__()

        self.title("Pagyar Mosta Zrt.")
        self.geometry("1000x500")

        # Set up main frame as a container for views
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand="True")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Initialize views and load Login page
        self.views = {}
        for key, view_class in view_classes.items():
            view = view_class(self.container, self)
            self.views[key] = view
            view.grid(row=0, column=0, sticky="nsew")


        self.show_view("login")

    def show_view(self, view_class):
        view = self.views[view_class]
        view.tkraise()

app = App({"login": LoginView,
           "home": HomeView,
           "register": RegisterView})

app.mainloop()