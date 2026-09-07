[CmdletBinding()]
param(
    [string]$InstallDirectory = (Join-Path $HOME "Semi-Graph"),
    [string]$GitHubUsername = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repository = "https://github.com/Semi-Graph-Project/Semi-Graph.git"
$branch = "advisor-work"

function Assert-CommandSucceeded {
    param([string]$Message)

    if ($LASTEXITCODE -ne 0) {
        throw $Message
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git was not found. Install Git for Windows first."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker was not found. Install and start Docker Desktop first."
}

& docker info *> $null
Assert-CommandSucceeded "Docker Desktop is not running."

if (Test-Path (Join-Path $PSScriptRoot ".git")) {
    $projectDirectory = $PSScriptRoot
}
elseif (Test-Path (Join-Path $InstallDirectory ".git")) {
    $projectDirectory = (Resolve-Path $InstallDirectory).Path
}
else {
    if (Test-Path $InstallDirectory) {
        throw "Install directory already exists but is not a Git repository: $InstallDirectory"
    }

    New-Item -ItemType Directory -Force `
        -Path (Split-Path $InstallDirectory -Parent) | Out-Null
    & git clone --branch $branch --single-branch $repository $InstallDirectory
    Assert-CommandSucceeded "Unable to clone the private repository. Check GitHub access."
    $projectDirectory = (Resolve-Path $InstallDirectory).Path
}

Push-Location $projectDirectory
try {
    & .\handoff.ps1 setup

    Write-Host "Edit .env, then save and close Notepad."
    $envFile = Join-Path $projectDirectory ".env"
    Start-Process notepad.exe -ArgumentList "`"$envFile`"" -Wait

    if ([string]::IsNullOrWhiteSpace($GitHubUsername)) {
        $GitHubUsername = Read-Host "GitHub username for GHCR"
    }
    & docker login ghcr.io -u $GitHubUsername
    Assert-CommandSucceeded "GHCR login failed. Use a token with read:packages permission."

    & .\handoff.ps1 start
    & .\handoff.ps1 smoke

    Start-Process "http://localhost:8501"

    Write-Host ""
    Write-Host "SemiGraph is ready. Daily commands:"
    Write-Host "  .\handoff.ps1 start        # Agent UI: http://localhost:8501"
    Write-Host "  .\handoff.ps1 comparison   # Comparison UI: http://localhost:8502"
    Write-Host "  .\handoff.ps1 smoke"
    Write-Host "  .\handoff.ps1 status"
    Write-Host "  .\handoff.ps1 logs"
    Write-Host "  .\handoff.ps1 stop"
    Write-Host "  git pull --ff-only origin advisor-work   # Update source"
}
finally {
    Pop-Location
}
