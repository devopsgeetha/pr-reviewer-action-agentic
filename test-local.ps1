# Local testing script for PR reviewer
# Usage: .\test-local.ps1

$ErrorActionPreference = "Stop"

# Load .env file if it exists
$envFile = Join-Path $PSScriptRoot "backend\.env"
if (Test-Path $envFile) {
    Write-Host "Loading environment from backend\.env" -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+?)\s*$') {
            $key = $matches[1]
            $value = $matches[2]
            # Remove quotes if present
            $value = $value -replace '^["' + "'" + ']|["' + "'" + ']$', ''
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
            Write-Host "  Loaded $key" -ForegroundColor Green
        }
    }
} else {
    Write-Host "No .env file found at backend\.env" -ForegroundColor Yellow
}

# Verify required environment variables
if (-not $env:OPENAI_API_KEY) {
    Write-Host "ERROR: OPENAI_API_KEY not set. Please add it to backend\.env" -ForegroundColor Red
    exit 1
}
if (-not $env:GITHUB_TOKEN) {
    Write-Host "ERROR: GITHUB_TOKEN not set. Please add it to backend\.env" -ForegroundColor Red
    exit 1
}

# Set defaults for optional variables
if (-not $env:OPENAI_MODEL) {
    $env:OPENAI_MODEL = "gpt-4-turbo-preview"
}
if (-not $env:GITHUB_REPOSITORY) {
    $env:GITHUB_REPOSITORY = "meetgeetha/pr-reviewer-action"
}
if (-not $env:PR_NUMBER) {
    $env:PR_NUMBER = "5"
}

Write-Host ""
Write-Host "Testing PR Reviewer locally..." -ForegroundColor Cyan
Write-Host "Repository: $env:GITHUB_REPOSITORY" -ForegroundColor Yellow
Write-Host "PR Number: $env:PR_NUMBER" -ForegroundColor Yellow
Write-Host ""

# Navigate to backend and run the Python test script
Push-Location backend
try {
    python test_pr_local.py
} finally {
    Pop-Location
}
