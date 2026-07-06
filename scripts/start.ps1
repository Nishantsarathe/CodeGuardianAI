# Start CodeGuardian AI locally (Windows PowerShell)
$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

if (-not (Test-Path ".env")) {
    Write-Host "[start] .env not found - copying from .env.example"
    Copy-Item .env.example .env
    Write-Host "[start] ⚠️  Edit .env and set SECRET_KEY and JWT_SECRET before running in production."
}

if (-not (Get-Command "ollama" -ErrorAction SilentlyContinue)) {
    Write-Host "[start] ⚠️  Ollama not found. Install from https://ollama.com/download"
}

Write-Host "[start] Pulling Ollama model (best effort)..."
ollama pull gemma2:2b 2>$null

Write-Host "[start] Starting Docker Compose stack..."
docker compose -f docker/docker-compose.yml up --build
