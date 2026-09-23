#!/usr/bin/env bash
#
# Elinditja a teljes projektet: adatbazis, backend, frontend.
#
# Hasznalat:
#   ./start.sh                # normal inditas
#   ./start.sh --fresh        # minden fuggoseg ujratelepitese
#   ./start.sh --no-docker    # Docker helyett helyi SQLite adatbazis
#   ./start.sh --backend-only # csak a backend, frontend nelkul
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT/backend"
FRONTEND_DIR="$ROOT/frontend"
LOG_DIR="$ROOT/.logs"
BACKEND_LOG="$LOG_DIR/backend.log"

FRESH=0
NO_DOCKER=0
BACKEND_ONLY=0
USE_DOCKER=0
BACKEND_PID=""

for arg in "$@"; do
    case "$arg" in
        --fresh)        FRESH=1 ;;
        --no-docker)    NO_DOCKER=1 ;;
        --backend-only) BACKEND_ONLY=1 ;;
        -h|--help)      sed -n '3,10p' "$0"; exit 0 ;;
        *) echo "Ismeretlen kapcsolo: $arg" >&2; exit 1 ;;
    esac
done

if [ -t 1 ]; then
    C_CYAN='\033[36m'; C_GREEN='\033[32m'; C_YELLOW='\033[33m'
    C_RED='\033[31m'; C_GRAY='\033[90m'; C_OFF='\033[0m'
else
    C_CYAN=''; C_GREEN=''; C_YELLOW=''; C_RED=''; C_GRAY=''; C_OFF=''
fi

step() { printf "\n${C_CYAN}==> %s${C_OFF}\n" "$1"; }
ok()   { printf "    ${C_GREEN}%s${C_OFF}\n" "$1"; }
warn() { printf "    ${C_YELLOW}%s${C_OFF}\n" "$1"; }
err()  { printf "${C_RED}%s${C_OFF}\n" "$1" >&2; }

# --- uv megkeresese ---------------------------------------------------------
# A uv lehet a PATH-ban, vagy csak egy Python modulkent telepitve.
UV=()
find_uv() {
    if command -v uv >/dev/null 2>&1; then
        UV=(uv)
        return 0
    fi
    # A szokasos telepitesi helyek. Ez akkor is mukodik, ha epp be van kapcsolva
    # egy virtualis kornyezet, amiben nincs uv.
    for candidate in \
        "$HOME/.local/bin/uv" \
        "$HOME/.cargo/bin/uv" \
        "/usr/local/bin/uv" \
        "/opt/homebrew/bin/uv" \
        "$APPDATA/Python/Python"*/Scripts/uv.exe
    do
        if [ -x "$candidate" ]; then
            UV=("$candidate")
            return 0
        fi
    done
    for py in python3 python py; do
        if command -v "$py" >/dev/null 2>&1 && "$py" -m uv --version >/dev/null 2>&1; then
            UV=("$py" -m uv)
            return 0
        fi
    done
    return 1
}

cleanup() {
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        step "Backend leallitasa..."
        # A folyamatcsoportot allitjuk le, hogy az uvicorn worker se maradjon futva
        kill -- "-$BACKEND_PID" 2>/dev/null || kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ "$USE_DOCKER" -eq 1 ]; then
        printf "${C_GRAY}\nAz adatbazis tovabbra is fut. Leallitas: docker compose down${C_OFF}\n"
    fi
}
trap cleanup EXIT INT TERM

# --- 1. uv ------------------------------------------------------------------
step "uv keresese..."
if ! find_uv; then
    err "Nem talalhato a uv.

Telepitsd egyszer az alabbi paranccsal, majd nyiss uj terminalt:

    curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
ok "uv megtalalva (${UV[*]})"

# --- 2. Fuggosegek ----------------------------------------------------------
SYNC_ARGS=(sync)
if [ "$FRESH" -eq 1 ]; then
    SYNC_ARGS+=(--reinstall)
fi

step "Backend fuggosegek frissitese..."
(cd "$BACKEND_DIR" && "${UV[@]}" "${SYNC_ARGS[@]}")
ok "Kesz."

if [ "$BACKEND_ONLY" -eq 0 ]; then
    step "Frontend fuggosegek frissitese..."
    (cd "$FRONTEND_DIR" && "${UV[@]}" "${SYNC_ARGS[@]}")
    ok "Kesz."
fi

# --- 3. Adatbazis -----------------------------------------------------------
PG_USER="admin"; PG_PASS="pass"; PG_DB="database"; SECRET=""
if [ -f "$ROOT/.env" ]; then
    while IFS='=' read -r key value; do
        key="${key// /}"
        value="${value%\"}"; value="${value#\"}"
        case "$key" in
            POSTGRES_USER)     PG_USER="$value" ;;
            POSTGRES_PASSWORD) PG_PASS="$value" ;;
            POSTGRES_DB)       PG_DB="$value" ;;
            SECRET_KEY)        SECRET="$value" ;;
        esac
    done < <(grep -v '^[[:space:]]*#' "$ROOT/.env" | grep '=')
fi

if [ "$NO_DOCKER" -eq 0 ]; then
    step "Docker ellenorzese..."
    if command -v docker >/dev/null 2>&1; then
        if docker info >/dev/null 2>&1; then
            USE_DOCKER=1
            ok "A Docker fut."
        else
            warn "A Docker telepitve van, de nem fut (indisd el a Docker szolgaltatast)."
        fi
    else
        warn "A docker parancs nem talalhato."
    fi
fi

if [ "$USE_DOCKER" -eq 1 ]; then
    step "Postgres adatbazis inditasa..."
    (cd "$ROOT" && docker compose up -d postgres_db)

    step "Varakozas az adatbazisra..."
    READY=0
    for _ in $(seq 1 30); do
        if (cd "$ROOT" && docker compose exec -T postgres_db pg_isready -U "$PG_USER" -d "$PG_DB" >/dev/null 2>&1); then
            READY=1
            break
        fi
        sleep 2
    done
    if [ "$READY" -eq 0 ]; then
        err "Az adatbazis nem valaszolt idoben."
        exit 1
    fi
    ok "Az adatbazis keszen all."

    export DATABASE_URL="postgresql://${PG_USER}:${PG_PASS}@localhost:5432/${PG_DB}"
else
    export DATABASE_URL="sqlite:///${BACKEND_DIR}/dev.db"
    warn "Docker nelkul indul, helyi SQLite adatbazissal (backend/dev.db)."
fi

if [ -n "$SECRET" ]; then
    export SECRET_KEY="$SECRET"
fi

# --- 4. Backend -------------------------------------------------------------
port_in_use() {
    (exec 3<>"/dev/tcp/127.0.0.1/8000") 2>/dev/null && exec 3<&- && return 0
    return 1
}

if port_in_use; then
    step "A 8000-es porton mar fut valami, a backend inditasa kimarad."
else
    step "Backend inditasa..."
    mkdir -p "$LOG_DIR"
    (
        cd "$BACKEND_DIR"
        # sajat folyamatcsoport, hogy a leallitas a gyerekeket is elerje
        set -m
        exec "${UV[@]}" run uvicorn main:app \
            --app-dir src --host 127.0.0.1 --port 8000 --reload
    ) > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!

    step "Varakozas a backendre..."
    UP=0
    for _ in $(seq 1 40); do
        if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            break
        fi
        if port_in_use; then
            UP=1
            break
        fi
        sleep 0.5
    done
    if [ "$UP" -eq 0 ]; then
        err "A backend nem indult el. A naplo vege:"
        tail -n 25 "$BACKEND_LOG" >&2 || true
        exit 1
    fi
    ok "A backend fut: http://127.0.0.1:8000 (dokumentacio: /docs)"
    ok "Naplo: $BACKEND_LOG"
fi

# --- 5. Frontend ------------------------------------------------------------
if [ "$BACKEND_ONLY" -eq 1 ]; then
    step "Csak a backend indult el. Leallitas: Ctrl+C"
    if [ -n "$BACKEND_PID" ]; then
        wait "$BACKEND_PID"
    else
        while true; do sleep 1; done
    fi
else
    step "Frontend inditasa..."
    (cd "$FRONTEND_DIR" && "${UV[@]}" run python main.py)
    step "A frontend bezarult."
fi
