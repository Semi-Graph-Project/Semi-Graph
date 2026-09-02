[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet(
        "setup", "start", "comparison", "extended", "status", "smoke",
        "eval-smoke", "eval", "ingest", "shell", "logs", "disk", "stop", "help"
    )]
    [string]$Action = "help",

    [ValidateSet("vector", "graph", "agent_vector", "agent_graph")]
    [string]$Tool = "vector",

    [ValidateSet("retrieve_only", "full_answer")]
    [string]$Mode = "retrieve_only",

    [ValidateRange(1, 64)]
    [int]$Workers = 4,

    [ValidateRange(1, 74)]
    [int]$Limit = 3,

    [string]$VersionName = "advisor",
    [string]$Ticker = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-HandoffCompose {
    & docker compose --env-file .env -f compose.handoff.yaml @args
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed with exit code $LASTEXITCODE"
    }
}

function Show-HandoffHelp {
    @"
SemiGraph Docker handoff

  .\handoff.ps1 setup
  .\handoff.ps1 start
  .\handoff.ps1 smoke
  .\handoff.ps1 comparison
  .\handoff.ps1 eval-smoke -Tool vector -Limit 3
  .\handoff.ps1 eval -Tool graph -Mode retrieve_only -Workers 4
  .\handoff.ps1 ingest -Ticker NVDA -Workers 2
  .\handoff.ps1 status | logs | shell | disk | stop

Use '.\handoff.ps1 extended' only when FinReflectKG and PostgreSQL are needed.
Named database volumes remain after 'stop'. This script never deletes volumes.
"@
}

Push-Location $PSScriptRoot
try {
    if ($Action -eq "help") {
        Show-HandoffHelp
        return
    }

    if ($Action -eq "setup") {
        if (Test-Path .env) {
            Write-Host ".env already exists; nothing was overwritten."
        }
        else {
            Copy-Item .env.handoff.example .env
            Write-Host "Created .env from .env.handoff.example."
            Write-Host "Edit .env and set your own passwords and OPENROUTER_API_KEY."
        }
        return
    }

    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI was not found. Start Docker Desktop and reopen PowerShell."
    }
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker engine is not ready. Start Docker Desktop first."
    }
    if (-not (Test-Path .env)) {
        throw ".env is missing. Run '.\handoff.ps1 setup' first."
    }

    switch ($Action) {
        "start" {
            Invoke-HandoffCompose pull
            Invoke-HandoffCompose up -d --no-build
            Invoke-HandoffCompose ps
            Write-Host "Agent UI: http://localhost:8501"
        }
        "comparison" {
            Invoke-HandoffCompose --profile comparison pull --include-deps comparison-demo
            Invoke-HandoffCompose --profile comparison up -d --no-build comparison-demo
            Start-Process "http://localhost:8502"
        }
        "extended" {
            Invoke-HandoffCompose --profile extended pull
            Invoke-HandoffCompose --profile extended up -d --no-build
            Invoke-HandoffCompose --profile extended ps
        }
        "status" {
            Invoke-HandoffCompose --profile comparison --profile extended ps
        }
        "smoke" {
            Invoke-HandoffCompose exec -T app python scripts/handoff_smoke.py
        }
        "eval-smoke" {
            Invoke-HandoffCompose exec -T app python eval_scripts/evaluate.py `
                --tool $Tool --mode $Mode --workers $Workers `
                --limit $Limit --version_name $VersionName
        }
        "eval" {
            Invoke-HandoffCompose exec -T app python eval_scripts/evaluate.py `
                --tool $Tool --mode $Mode --workers $Workers `
                --version_name $VersionName
        }
        "ingest" {
            if ([string]::IsNullOrWhiteSpace($Ticker)) {
                throw "-Ticker is required, for example: .\handoff.ps1 ingest -Ticker NVDA"
            }
            Invoke-HandoffCompose exec -T app python scripts/pilot.py `
                --ticker $Ticker --workers $Workers
        }
        "shell" {
            Invoke-HandoffCompose exec app bash
        }
        "logs" {
            Invoke-HandoffCompose logs --tail 200 -f app
        }
        "disk" {
            & docker system df
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to read Docker disk usage."
            }
            Invoke-HandoffCompose --profile comparison --profile extended images
        }
        "stop" {
            Invoke-HandoffCompose --profile comparison --profile extended down
            Write-Host "Containers stopped. Named database volumes were preserved."
        }
    }
}
finally {
    Pop-Location
}
