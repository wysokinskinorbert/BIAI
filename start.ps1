<#
.SYNOPSIS
    BIAI - Business Intelligence AI - Skrypt startowy
.DESCRIPTION
    Uruchamia wszystkie wymagane serwisy aplikacji BIAI:
    1. Sprawdza/uruchamia Ollama (LLM backend)
    2. Opcjonalnie uruchamia Docker z testowymi bazami danych
    3. Uruchamia aplikacje Reflex (frontend + backend)
.PARAMETER NoDB
    Pomija uruchamianie kontenerow Docker z bazami danych
.PARAMETER Docker
    Wymusza uruchomienie kontenerow Docker z testowymi bazami
.PARAMETER Dev
    Uruchamia w trybie deweloperskim (reflex run --loglevel debug)
.EXAMPLE
    .\start.ps1              # Standardowe uruchomienie (bez Docker)
    .\start.ps1 -Docker      # Z testowymi bazami Docker
    .\start.ps1 -Dev         # Tryb deweloperski
    .\start.ps1 -Docker -Dev # Docker + tryb deweloperski
#>

param(
    [switch]$Docker,
    [switch]$Dev
)

# ============================================================
# Konfiguracja
# ============================================================
$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
$OllamaModel = "qwen2.5-coder:7b-instruct-q4_K_M"

# Porty
$OllamaPort = 11434
$ReflexPort = 3000
$PostgresPort = 5433
$OraclePort = 1521

# Kolory
function Write-Step   { param($msg) Write-Host "`n[$([char]0x2714)] $msg" -ForegroundColor Green }
function Write-Info   { param($msg) Write-Host "    $msg" -ForegroundColor Cyan }
function Write-Warn   { param($msg) Write-Host "    [!] $msg" -ForegroundColor Yellow }
function Write-Fail   { param($msg) Write-Host "    [X] $msg" -ForegroundColor Red }

function Test-Port {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return ($null -ne $conn)
}

# ============================================================
# Banner
# ============================================================
Write-Host ""
Write-Host "  =====================================" -ForegroundColor Magenta
Write-Host "   BIAI - Business Intelligence AI" -ForegroundColor Magenta
Write-Host "   Skrypt startowy" -ForegroundColor Magenta
Write-Host "  =====================================" -ForegroundColor Magenta
Write-Host ""

$mode = if ($Dev) { "DEV" } else { "PRODUCTION" }
Write-Info "Tryb: $mode"
Write-Info "Projekt: $ProjectRoot"
Write-Info "Docker: $(if ($Docker) { 'TAK' } else { 'NIE' })"

# ============================================================
# 1. Sprawdzenie srodowiska wirtualnego
# ============================================================
Write-Step "Sprawdzanie srodowiska wirtualnego..."

if (-not (Test-Path $VenvPython)) {
    Write-Fail "Brak srodowiska wirtualnego: $VenvPython"
    Write-Fail "Uruchom najpierw: python -m venv .venv && pip install -e '.[dev]'"
    exit 1
}
Write-Info "venv OK: $VenvPython"

# ============================================================
# 2. Sprawdzenie/uruchomienie Ollama
# ============================================================
Write-Step "Sprawdzanie Ollama..."

$ollamaRunning = Test-Port $OllamaPort

if ($ollamaRunning) {
    Write-Info "Ollama juz dziala na porcie $OllamaPort"
} else {
    Write-Info "Ollama nie dziala - uruchamiam..."

    $ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollamaPath) {
        Write-Fail "Ollama nie znaleziona w PATH!"
        Write-Fail "Zainstaluj: https://ollama.ai/download"
        exit 1
    }

    # Uruchom Ollama serve w tle
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Write-Info "Czekam na uruchomienie Ollama..."

    $attempts = 0
    $maxAttempts = 15
    while (-not (Test-Port $OllamaPort) -and $attempts -lt $maxAttempts) {
        Start-Sleep -Seconds 2
        $attempts++
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    Write-Host ""

    if (Test-Port $OllamaPort) {
        Write-Info "Ollama uruchomiona pomyslnie"
    } else {
        Write-Fail "Nie udalo sie uruchomic Ollama po $($maxAttempts * 2)s"
        exit 1
    }
}

# Sprawdz model
Write-Info "Sprawdzam model $OllamaModel..."
$modelList = & ollama list 2>&1
if ($modelList -match [regex]::Escape($OllamaModel)) {
    Write-Info "Model $OllamaModel dostepny"
} else {
    Write-Warn "Model $OllamaModel nie znaleziony - pobieram..."
    Write-Warn "To moze zając kilka minut przy pierwszym uruchomieniu"
    & ollama pull $OllamaModel
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Blad pobierania modelu $OllamaModel"
        exit 1
    }
    Write-Info "Model pobrany pomyslnie"
}

# ============================================================
# 3. Docker (opcjonalnie)
# ============================================================
if ($Docker) {
    Write-Step "Uruchamianie kontenerow Docker..."

    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerCmd) {
        Write-Fail "Docker nie znaleziony w PATH!"
        Write-Fail "Zainstaluj Docker Desktop: https://docker.com/products/docker-desktop"
        exit 1
    }

    # Sprawdz czy Docker daemon dziala
    $dockerInfo = & docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Fail "Docker daemon nie dziala! Uruchom Docker Desktop."
        exit 1
    }

    $composeFile = Join-Path $ProjectRoot "docker-compose.dev.yml"
    if (-not (Test-Path $composeFile)) {
        Write-Fail "Brak pliku: $composeFile"
        exit 1
    }

    # Sprawdz czy kontenery juz dzialaja
    $pgRunning = Test-Port $PostgresPort
    $oraRunning = Test-Port $OraclePort

    if ($pgRunning -and $oraRunning) {
        Write-Info "Kontenery juz dzialaja (PostgreSQL:$PostgresPort, Oracle:$OraclePort)"
    } else {
        Push-Location $ProjectRoot
        & docker compose -f docker-compose.dev.yml up -d
        Pop-Location

        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Blad uruchamiania kontenerow Docker"
            exit 1
        }

        Write-Info "Czekam na PostgreSQL..."
        $attempts = 0
        while (-not (Test-Port $PostgresPort) -and $attempts -lt 15) {
            Start-Sleep -Seconds 2
            $attempts++
        }

        if (Test-Port $PostgresPort) {
            Write-Info "PostgreSQL gotowy (port $PostgresPort)"
        } else {
            Write-Warn "PostgreSQL jeszcze sie uruchamia - moze potrzebowac wiecej czasu"
        }

        Write-Info "Oracle XE moze potrzebowac do 2 minut na pelne uruchomienie"
        Write-Info "Sprawdz status: docker compose -f docker-compose.dev.yml ps"
    }
}

# ============================================================
# 4. Sprawdzenie portu Reflex
# ============================================================
Write-Step "Sprawdzanie portu Reflex ($ReflexPort)..."

if (Test-Port $ReflexPort) {
    Write-Warn "Port $ReflexPort jest juz zajety!"
    Write-Warn "Aplikacja BIAI moze juz dzialac."
    Write-Warn "Otwieram przegladarke na http://localhost:$ReflexPort"
    Start-Process "http://localhost:$ReflexPort"
    exit 0
}

Write-Info "Port $ReflexPort wolny"

# ============================================================
# 5. Uruchomienie Reflex
# ============================================================
Write-Step "Uruchamianie aplikacji BIAI..."

# Aktywuj venv i uruchom reflex
$reflexArgs = if ($Dev) { "run --loglevel debug" } else { "run" }

Write-Info "Komenda: reflex $reflexArgs"
Write-Info ""
Write-Host "  =====================================" -ForegroundColor Green
Write-Host "   BIAI dostepna pod:" -ForegroundColor Green
Write-Host "   http://localhost:$ReflexPort" -ForegroundColor White
Write-Host "  =====================================" -ForegroundColor Green
Write-Host ""
Write-Info "Nacisnij Ctrl+C aby zatrzymac aplikacje"
Write-Host ""

# Uruchom reflex w kontekscie venv
Push-Location $ProjectRoot
try {
    & $VenvActivate
    if ($Dev) {
        & reflex run --loglevel debug
    } else {
        & reflex run
    }
} finally {
    Pop-Location
}
