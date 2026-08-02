<#
.SYNOPSIS
    Bootstraps the SakThai Agent v2 on Windows.

.DESCRIPTION
    Creates the .env file from .env.example if missing, sets up a Python virtual environment,
    activates it, and installs the package with all dependencies.
#>

$ErrorActionPreference = "Stop"

# Ensure we are in the root directory
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location -Path $RepoRoot

Write-Host "Bootstrapping SakThai Agent v2..." -ForegroundColor Cyan

# 1. Setup .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example." -ForegroundColor Green
    } else {
        Write-Host "Warning: .env.example not found." -ForegroundColor Yellow
    }
} else {
    Write-Host ".env already exists. Skipping creation." -ForegroundColor DarkGray
}

# 2. Setup Virtual Environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error creating virtual environment. Ensure python is in your PATH." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment (.venv) already exists." -ForegroundColor DarkGray
}

# 3. Activate Virtual Environment and Install
Write-Host "Installing dependencies..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -e ".[all]"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBootstrap complete! ✨" -ForegroundColor Green
    Write-Host "To start using the agent, activate the environment:" -ForegroundColor Yellow
    Write-Host "    .\.venv\Scripts\Activate.ps1"
    Write-Host "Then run:" -ForegroundColor Yellow
    Write-Host "    sakthai doctor"
} else {
    Write-Host "`nBootstrap failed during pip install." -ForegroundColor Red
    exit 1
}
