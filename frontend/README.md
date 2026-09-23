# Frontend

CustomTkinter asztali alkalmazás, ami a backend API-ját hívja (`http://localhost:8000`).

## Futtatás

A teljes rendszert a repo gyökeréből az indítószkript hozza fel:

```bash
.\start.ps1      # Windows
./start.sh       # Linux / macOS
```

Ha csak a frontendet indítod (a backendnek futnia kell), a `frontend` mappából:

```bash
uv run python main.py
```

> A `uv run` fontos: ez használja a frontend saját környezetét. Sima
> `python main.py` esetén hiányzó csomagokat (pl. `customtkinter`, `httpx`) fogsz kapni,
> mert azok nem a rendszer-Pythonba vannak telepítve.

## Szerkezet

- `main.py` – az alkalmazás belépési pontja, a nézetek közti váltást kezeli
- `src/views/` – képernyők (login, register, home)
- `src/api/` – a backend hívása (`base_api.py`, `auth_api.py`)
