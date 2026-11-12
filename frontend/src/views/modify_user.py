import threading
from tkinter import TclError

import customtkinter as ctk

from src.api.session import auth_api
from src.api.user_api import UserAPI

SUCCESS_COLOR = "green"
ERROR_COLOR = "red"
NEUTRAL_COLOR = ("gray30", "gray70")


class ModifyUserView(ctk.CTkFrame):
    """Felhasználói adatok módosítása: név, elsődleges cím és jelszó.

    A tokent a src.api.session közös auth_api példányától kapja, lejárt
    bejelentkezésnél pedig a controller.show_view("login") hívással lép vissza.
    """

    def __init__(self, master, controller):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.controller = controller
        self.api = UserAPI(auth_api=auth_api)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        form.grid_columnconfigure(0, weight=1)

        self.bind("<Configure>", self._on_resize)


        ctk.CTkLabel(
            form, text="Beállítások", font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, pady=(0, 20), sticky="w")

        self._build_profile_section(form)
        self._build_password_section(form)

        self._load_profile()

    def _build_profile_section(self, parent):
        card = ctk.CTkFrame(parent)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Profil", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.email_label = ctk.CTkLabel(
            card, text="", anchor="w", text_color=NEUTRAL_COLOR
        )
        self.email_label.grid(row=1, column=0, padx=20, sticky="ew")

        self.name = self._add_entry(card, row=2, label="Név")
        self.address = self._add_entry(card, row=4, label="Elsődleges cím")

        self.profile_message = ctk.CTkLabel(
            card, text="", anchor="w", justify="left", wraplength=380
        )
        self.profile_message.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.save_btn = ctk.CTkButton(
            card, text="Mentés", height=40, command=self.save_profile
        )
        self.save_btn.grid(row=7, column=0, padx=20, pady=(5, 20), sticky="ew")

        self.address.bind("<Return>", lambda event: self.save_profile())

    def _build_password_section(self, parent):
        card = ctk.CTkFrame(parent)
        card.grid(row=2, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Jelszó módosítása", font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        self.current_password = self._add_entry(
            card, row=1, label="Jelenlegi jelszó", show="*"
        )
        self.new_password = self._add_entry(card, row=3, label="Új jelszó", show="*")
        self.new_password_again = self._add_entry(
            card, row=5, label="Új jelszó mégegyszer", show="*"
        )

        self.password_message = ctk.CTkLabel(
            card, text="", anchor="w", justify="left", wraplength=380
        )
        self.password_message.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="ew")

        self.password_btn = ctk.CTkButton(
            card, text="Jelszó módosítása", height=40, command=self.change_password
        )
        self.password_btn.grid(row=8, column=0, padx=20, pady=(5, 20), sticky="ew")

        self.new_password_again.bind("<Return>", lambda event: self.change_password())

    @staticmethod
    def _add_entry(parent, row, label, show=None):
        """Felirat (row) + beviteli mező (row + 1)."""
        ctk.CTkLabel(parent, text=label, anchor="w").grid(
            row=row, column=0, padx=20, pady=(10, 0), sticky="ew"
        )
        entry = ctk.CTkEntry(parent, height=40, show=show)
        entry.grid(row=row + 1, column=0, padx=20, pady=(2, 0), sticky="ew")
        return entry

    def _on_resize(self, event):
        wrap = max(200, event.width - 140)
        self.profile_message.configure(wraplength=wrap)
        self.password_message.configure(wraplength=wrap)

    def _load_profile(self):
        self.profile_message.configure(text="Adatok betöltése...", text_color=NEUTRAL_COLOR)
        self._run_async(self.api.get_profile, self._on_profile_loaded)

    def _on_profile_loaded(self, ok, data):
        if not ok:
            self._show_error(self.profile_message, data)
            return
        self.profile_message.configure(text="")
        self._fill_profile(data)

    def _fill_profile(self, data):
        self.email_label.configure(text=f"E-mail: {data['email']} (nem módosítható)")
        self._set_entry(self.name, data["name"])
        self._set_entry(self.address, data.get("primary_address") or "")

    def save_profile(self):
        name = self.name.get().strip()
        address = self.address.get().strip()

        self._set_busy(self.save_btn, True, "Mentés...")
        self.profile_message.configure(text="")
        self._run_async(
            lambda: self.api.update_profile(name, address), self._on_profile_saved
        )

    def _on_profile_saved(self, ok, data):
        self._set_busy(self.save_btn, False, "Mentés")
        if ok:
            self._fill_profile(data)
            self.profile_message.configure(
                text="Az adatok sikeresen mentve.", text_color=SUCCESS_COLOR
            )
        else:
            self._show_error(self.profile_message, data)

    def change_password(self):
        current = self.current_password.get()
        new = self.new_password.get()
        again = self.new_password_again.get()

        self._set_busy(self.password_btn, True, "Módosítás...")
        self.password_message.configure(text="")
        self._run_async(
            lambda: self.api.change_password(current, new, again),
            self._on_password_changed,
        )

    def _on_password_changed(self, ok, message):
        self._set_busy(self.password_btn, False, "Jelszó módosítása")
        if ok:
            for entry in (self.current_password, self.new_password, self.new_password_again):
                entry.delete(0, "end")
            self.password_message.configure(
                text="A jelszó sikeresen módosítva.", text_color=SUCCESS_COLOR
            )
        else:
            self._show_error(self.password_message, message)

    def _run_async(self, func, on_done):
        """A hívást háttérszálon futtatja, az eredményt a fő szálon adja át."""

        def worker():
            ok, data = func()
            try:
                self.after(0, self._finish, on_done, ok, data)
            except (RuntimeError, TclError):
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, on_done, ok, data):
        try:
            if not self.winfo_exists():
                return
        except TclError:
            return
        on_done(ok, data)

    def _show_error(self, label, message):
        if message == UserAPI.SESSION_EXPIRED:
            self.controller.show_view("login")
            return
        label.configure(text=message, text_color=ERROR_COLOR)

    @staticmethod
    def _set_busy(button, busy, text):
        button.configure(state="disabled" if busy else "normal", text=text)

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, "end")
        entry.insert(0, value)