import customtkinter as ctk

STATUS_LABELS = {
    "created": ("Előjegyezve", "#6b7280"),
    "ready_for_pickup": ("Felvételre vár", "#6b7280"),
    "assigned_for_pickup": ("Felvételre kijelölve", "#2563eb"),
    "out_for_pickup": ("Futár úton a csomagért", "#7c3aed"),
    "picked_up": ("Felvéve", "#7c3aed"),
    "in_warehouse": ("Raktárban", "#0891b2"),
    "assigned_for_delivery": ("Kiszállításra kijelölve", "#2563eb"),
    "out_for_delivery": ("Kiszállítás alatt", "#d97706"),
    "delivered": ("Kézbesítve", "#16a34a"),
    "failed_delivery": ("Sikertelen kézbesítés", "#dc2626"),
    "returned_to_sender": ("Visszaküldve", "#dc2626"),
    "cancelled": ("Visszamondva", "#6b7280"),
}

USER_TYPE_LABELS = {
    "admin": "Adminisztrátor",
    "registered customer": "Regisztrált ügyfél",
    "unregistered customer": "Vendég ügyfél",
    "warehouse_staff": "Raktáros",
    "delivery_man": "Futár",
}


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, (status, "#6b7280"))[0]


def status_color(status: str) -> str:
    return STATUS_LABELS.get(status, (status, "#6b7280"))[1]


def _fit(text: str, width: int) -> str:
    max_chars = max(4, int(width / 7.2))
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


class Table(ctk.CTkFrame):

    def __init__(self, master, columns, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columns = columns

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, corner_radius=6, height=36)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 4))
        for index, (title, width) in enumerate(columns):
            header.grid_columnconfigure(index, weight=0, minsize=width)
            ctk.CTkLabel(
                header,
                text=title,
                width=width,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=index, padx=8, pady=8, sticky="w")

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_columnconfigure(0, weight=1)

        self.empty_label = None

    def clear(self):
        for child in self.body.winfo_children():
            child.destroy()

    def show_message(self, text):
        self.clear()
        ctk.CTkLabel(self.body, text=text, text_color=("gray40", "gray60")).grid(
            row=0, column=0, padx=10, pady=20, sticky="w"
        )

    def add_row(self, values, buttons=None, color_index=None, color=None):
        row_index = len(self.body.winfo_children())
        row = ctk.CTkFrame(self.body, corner_radius=6)
        row.grid(row=row_index, column=0, sticky="ew", pady=2)
        row.grid_columnconfigure(len(self.columns), weight=1)

        for index, value in enumerate(values):
            width = self.columns[index][1] if index < len(self.columns) else 100
            text_color = None
            if color_index is not None and index == color_index and color:
                text_color = color

            label = ctk.CTkLabel(
                row,
                text=_fit(str(value), width),
                width=width,
                anchor="w",
                justify="left",
            )
            if text_color:
                label.configure(text_color=text_color)
            label.grid(row=0, column=index, padx=8, pady=8, sticky="w")

        if buttons:
            button_box = ctk.CTkFrame(row, fg_color="transparent")
            button_box.grid(row=0, column=len(self.columns), padx=8, pady=4, sticky="e")
            for position, (text, command, btn_color) in enumerate(buttons):
                width = min(150, max(76, int(7.2 * len(text)) + 16))
                btn = ctk.CTkButton(
                    button_box,
                    text=text,
                    command=command,
                    width=width,
                    height=26,
                    font=ctk.CTkFont(size=11),
                )
                if btn_color:
                    btn.configure(fg_color=btn_color, hover_color=btn_color)
                btn.grid(row=0, column=position, padx=3)

        return row


class FormDialog(ctk.CTkToplevel):

    def __init__(self, master, title, fields, submit_text="Mentés"):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.widgets = {}

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        for index, field in enumerate(fields, start=1):
            key, label, kind, default, options = field

            ctk.CTkLabel(self, text=label, anchor="w").grid(
                row=index, column=0, padx=(20, 10), pady=6, sticky="w"
            )

            if kind == "option":
                widget = ctk.CTkOptionMenu(self, values=options or [], width=260)
                if default:
                    widget.set(default)
                elif options:
                    widget.set(options[0])

            elif kind == "switch":
                widget = ctk.CTkSwitch(self, text="")
                if default:
                    widget.select()
                else:
                    widget.deselect()

            else:
                widget = ctk.CTkEntry(self, width=260)
                if kind == "password":
                    widget.configure(show="*")
                if default is not None:
                    widget.insert(0, str(default))

            widget.grid(row=index, column=1, padx=(0, 20), pady=6, sticky="ew")
            self.widgets[key] = (widget, kind)

        self.error_label = ctk.CTkLabel(self, text="", text_color="#dc2626", wraplength=380)
        self.error_label.grid(
            row=len(fields) + 1, column=0, columnspan=2, padx=20, pady=(4, 0), sticky="w"
        )

        button_box = ctk.CTkFrame(self, fg_color="transparent")
        button_box.grid(row=len(fields) + 2, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="e")

        ctk.CTkButton(
            button_box,
            text="Mégse",
            width=100,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._cancel,
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(button_box, text=submit_text, width=120, command=self._submit).grid(
            row=0, column=1, padx=5
        )

        self.bind("<Return>", lambda event: self._submit())
        self.bind("<Escape>", lambda event: self._cancel())

        self.transient(master.winfo_toplevel())
        self.after(100, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def set_error(self, message):
        self.error_label.configure(text=message)

    def _collect(self):
        values = {}
        for key, (widget, kind) in self.widgets.items():
            if kind == "switch":
                values[key] = bool(widget.get())
            elif kind == "option":
                values[key] = widget.get()
            else:
                values[key] = widget.get().strip()
        return values

    def _submit(self):
        self.result = self._collect()
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.result = None
        self.grab_release()
        self.destroy()

    def show(self):
        self.wait_window()
        return self.result


class ConfirmDialog(ctk.CTkToplevel):

    def __init__(self, master, title, message, confirm_text="Igen, törlöm"):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result = False

        ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 6), sticky="w")

        ctk.CTkLabel(self, text=message, wraplength=380, justify="left").grid(
            row=1, column=0, padx=20, pady=(0, 15), sticky="w"
        )

        button_box = ctk.CTkFrame(self, fg_color="transparent")
        button_box.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="e")

        ctk.CTkButton(
            button_box,
            text="Mégse",
            width=100,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._cancel,
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(
            button_box,
            text=confirm_text,
            width=140,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=self._confirm,
        ).grid(row=0, column=1, padx=5)

        self.bind("<Escape>", lambda event: self._cancel())
        self.transient(master.winfo_toplevel())
        self.after(100, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _confirm(self):
        self.result = True
        self.grab_release()
        self.destroy()

    def _cancel(self):
        self.result = False
        self.grab_release()
        self.destroy()

    def show(self):
        self.wait_window()
        return self.result


class StatCard(ctk.CTkFrame):

    def __init__(self, master, title, value, accent="#2563eb", **kwargs):
        super().__init__(master, corner_radius=8, **kwargs)

        ctk.CTkLabel(
            self,
            text=str(value),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=accent,
        ).grid(row=0, column=0, padx=18, pady=(14, 0), sticky="w")

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=("gray35", "gray65"),
            wraplength=160,
            justify="left",
            anchor="w",
        ).grid(row=1, column=0, padx=18, pady=(0, 14), sticky="w")
