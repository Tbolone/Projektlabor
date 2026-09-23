<#
.SYNOPSIS
    Elinditja a teljes projektet: adatbazis, backend, frontend.

.DESCRIPTION
    Frissiti a fuggosegeket, elinditja a Postgres adatbazist Dockerben,
    utana a backendet, vegul a frontendet. Kilepeskor leallitja a backendet.

.EXAMPLE
    .\start.ps1
    .\start.ps1 -Fresh
    .\start.ps1 -NoDocker
    .\start.ps1 -BackendOnly
#>
[CmdletBinding()]
param(
    # Minden fuggoseg ujratelepitese nulla allapotbol.
    [switch]$Fresh,
    # Docker helyett helyi SQLite adatbazis hasznalata.
    [switch]$NoDocker,
    # Csak a backend induljon el, frontend nelkul.
    [switch]$BackendOnly
)

# Szandekosan nem 'Stop': a natív parancsok (uv, docker) a stderr-re is irnak,
# amit a PowerShell 5.1 kulonben hibakent kezelne. A kilepesi kodot magunk nezzuk.
$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'
$logDir = Join-Path $root '.logs'
$backendLog = Join-Path $logDir 'backend.log'
$backendErrLog = Join-Path $logDir 'backend.err.log'
$backendProc = $null

function Write-Step($message) { Write-Host "`n==> $message" -ForegroundColor Cyan }
function Write-Ok($message) { Write-Host "    $message" -ForegroundColor Green }
function Write-Warn($message) { Write-Host "    $message" -ForegroundColor Yellow }

# --- uv megkeresese ---------------------------------------------------------
# A uv lehet a PATH-ban, vagy csak egy Python modulkent telepitve.
$script:UvExe = $null
$script:UvPrefix = @()

# Csendben lefuttat egy kulso parancsot, es visszaadja a kilepesi kodot.
function Invoke-Quiet {
    param([string]$FilePath, [string[]]$Arguments = @())
    $null = & $FilePath @Arguments 2>&1
    return $LASTEXITCODE
}

function Find-Uv {
    # 1. A PATH-ban
    $direct = Get-Command uv -ErrorAction SilentlyContinue
    if ($direct) {
        $script:UvExe = $direct.Source
        $script:UvPrefix = @()
        return $true
    }

    # 2. A szokasos telepitesi helyeken. Ez akkor is mukodik, ha epp be van
    #    kapcsolva egy virtualis kornyezet: a 'py' indito olyankor a venv
    #    Pythonjat hasznalja, amiben nincs uv.
    $patterns = @(
        (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
        (Join-Path $env:USERPROFILE '.cargo\bin\uv.exe'),
        (Join-Path $env:APPDATA 'Python\Python*\Scripts\uv.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\Scripts\uv.exe'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uv.exe')
    )
    foreach ($pattern in $patterns) {
        $found = Get-Item -Path $pattern -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($found) {
            $script:UvExe = $found.FullName
            $script:UvPrefix = @()
            return $true
        }
    }

    # 3. Vegso esetben Python modulkent
    foreach ($py in @('py', 'python', 'python3')) {
        $cmd = Get-Command $py -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        if ((Invoke-Quiet -FilePath $cmd.Source -Arguments @('-m', 'uv', '--version')) -eq 0) {
            $script:UvExe = $cmd.Source
            $script:UvPrefix = @('-m', 'uv')
            return $true
        }
    }
    return $false
}

function Invoke-Uv {
    param([string]$WorkDir, [string[]]$UvArgs)
    Push-Location $WorkDir
    try {
        & $script:UvExe @($script:UvPrefix + $UvArgs)
        if ($LASTEXITCODE -ne 0) { throw "A parancs hibara futott: uv $($UvArgs -join ' ')" }
    } finally {
        Pop-Location
    }
}

# --- .env beolvasasa --------------------------------------------------------
function Read-DotEnv {
    param([string]$Path)
    $values = @{}
    if (-not (Test-Path $Path)) { return $values }
    foreach ($line in Get-Content $Path) {
        $trimmed = $line.Trim()
        if ($trimmed -eq '' -or $trimmed.StartsWith('#')) { continue }
        $idx = $trimmed.IndexOf('=')
        if ($idx -lt 1) { continue }
        $key = $trimmed.Substring(0, $idx).Trim()
        $value = $trimmed.Substring($idx + 1).Trim().Trim('"').Trim("'")
        $values[$key] = $value
    }
    return $values
}

function Test-Port {
    param([int]$Port)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $ok = $client.ConnectAsync('127.0.0.1', $Port).Wait(300)
        $client.Close()
        return $ok
    } catch {
        return $false
    }
}

function Stop-Backend {
    if ($null -ne $script:backendProc -and -not $script:backendProc.HasExited) {
        Write-Step 'Backend leallitasa...'
        # /T: a gyerekfolyamatokat (uvicorn worker) is leallitja
        $null = Invoke-Quiet -FilePath 'taskkill.exe' -Arguments @(
            '/PID', $script:backendProc.Id, '/T', '/F')
    }
}

# --- 1. uv -----------------------------------------------------------------
Write-Step 'uv keresese...'
if (-not (Find-Uv)) {
    Write-Host @"
Nem talalhato a uv.

Telepitsd egyszer az alabbi paranccsal, majd nyiss uj terminalt:

    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
"@ -ForegroundColor Red
    exit 1
}
if ($script:UvPrefix.Count -gt 0) {
    Write-Ok "uv megtalalva Python modulkent ($($script:UvExe))"
} else {
    Write-Ok "uv megtalalva ($($script:UvExe))"
}

# --- 2. Fuggosegek ----------------------------------------------------------
$syncArgs = @('sync')
if ($Fresh) { $syncArgs += '--reinstall' }

Write-Step 'Backend fuggosegek frissitese...'
Invoke-Uv -WorkDir $backendDir -UvArgs $syncArgs
Write-Ok 'Kesz.'

if (-not $BackendOnly) {
    Write-Step 'Frontend fuggosegek frissitese...'
    Invoke-Uv -WorkDir $frontendDir -UvArgs $syncArgs
    Write-Ok 'Kesz.'
}

# --- 3. Adatbazis -----------------------------------------------------------
$envValues = Read-DotEnv -Path (Join-Path $root '.env')
$pgUser = $envValues['POSTGRES_USER']
$pgPass = $envValues['POSTGRES_PASSWORD']
$pgDb = $envValues['POSTGRES_DB']
if (-not $pgUser) { $pgUser = 'admin' }
if (-not $pgPass) { $pgPass = 'pass' }
if (-not $pgDb) { $pgDb = 'database' }

$useDocker = $false
if (-not $NoDocker) {
    Write-Step 'Docker ellenorzese...'
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        if ((Invoke-Quiet -FilePath 'docker' -Arguments @('info')) -eq 0) {
            $useDocker = $true
            Write-Ok 'A Docker fut.'
        } else {
            Write-Warn 'A Docker telepitve van, de nem fut (indistd el a Docker Desktopot).'
        }
    } else {
        Write-Warn 'A docker parancs nem talalhato.'
    }
}

if ($useDocker) {
    Write-Step 'Postgres adatbazis inditasa...'
    Push-Location $root
    try {
        & docker compose up -d postgres_db
        if ($LASTEXITCODE -ne 0) { throw 'Nem sikerult elinditani az adatbazist.' }
    } finally {
        Pop-Location
    }

    Write-Step 'Varakozas az adatbazisra...'
    $ready = $false
    Push-Location $root
    try {
        foreach ($i in 1..30) {
            $probe = Invoke-Quiet -FilePath 'docker' -Arguments @(
                'compose', 'exec', '-T', 'postgres_db',
                'pg_isready', '-U', $pgUser, '-d', $pgDb)
            if ($probe -eq 0) { $ready = $true; break }
            Start-Sleep -Seconds 2
        }
    } finally {
        Pop-Location
    }
    if (-not $ready) { throw 'Az adatbazis nem valaszolt idoben.' }
    Write-Ok 'Az adatbazis keszen all.'

    $env:DATABASE_URL = "postgresql://${pgUser}:${pgPass}@localhost:5432/${pgDb}"
} else {
    $sqlitePath = (Join-Path $backendDir 'dev.db') -replace '\\', '/'
    $env:DATABASE_URL = "sqlite:///$sqlitePath"
    Write-Warn 'Docker nelkul indul, helyi SQLite adatbazissal (backend/dev.db).'
}

if ($envValues['SECRET_KEY']) { $env:SECRET_KEY = $envValues['SECRET_KEY'] }

# --- 4. Backend -------------------------------------------------------------
try {
    if (Test-Port -Port 8000) {
        Write-Step 'A 8000-es porton mar fut valami, a backend inditasa kimarad.'
    } else {
        Write-Step 'Backend inditasa...'
        if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

        $uvicornArgs = $script:UvPrefix + @(
            'run', 'uvicorn', 'main:app',
            '--app-dir', 'src',
            '--host', '127.0.0.1',
            '--port', '8000',
            '--reload'
        )
        $script:backendProc = Start-Process -FilePath $script:UvExe `
            -ArgumentList $uvicornArgs `
            -WorkingDirectory $backendDir `
            -RedirectStandardOutput $backendLog `
            -RedirectStandardError $backendErrLog `
            -NoNewWindow -PassThru

        Write-Step 'Varakozas a backendre...'
        $up = $false
        foreach ($i in 1..40) {
            if ($script:backendProc.HasExited) { break }
            try {
                $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -TimeoutSec 2
                if ($resp.StatusCode -eq 200) { $up = $true; break }
            } catch {
                Start-Sleep -Milliseconds 500
            }
        }
        if (-not $up) {
            Write-Host 'A backend nem indult el. A naplo vege:' -ForegroundColor Red
            if (Test-Path $backendErrLog) { Get-Content $backendErrLog -Tail 25 }
            if (Test-Path $backendLog) { Get-Content $backendLog -Tail 25 }
            throw 'A backend inditasa sikertelen.'
        }
        Write-Ok 'A backend fut: http://127.0.0.1:8000 (dokumentacio: /docs)'
        Write-Ok "Naplo: $backendLog"
    }

    # --- 5. Frontend --------------------------------------------------------
    if ($BackendOnly) {
        Write-Step 'Csak a backend indult el. Leallitas: Ctrl+C'
        while ($null -ne $script:backendProc -and -not $script:backendProc.HasExited) {
            Start-Sleep -Seconds 1
        }
    } else {
        Write-Step 'Frontend inditasa...'
        Invoke-Uv -WorkDir $frontendDir -UvArgs @('run', 'python', 'main.py')
        Write-Step 'A frontend bezarult.'
    }
} finally {
    Stop-Backend
    if ($useDocker) {
        Write-Host "`nAz adatbazis tovabbra is fut. Leallitas: docker compose down" -ForegroundColor DarkGray
    }
}
