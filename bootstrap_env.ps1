# Set working directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "`n🔧 Bootstrapping Teams Monitor Environment..." -ForegroundColor Cyan

# Check for Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "❌ Python is not installed or not in PATH. Please install Python 3.10+."
    exit 1
}

# Create virtual environment
$venvPath = ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "📦 Creating virtual environment..."
    python -m venv $venvPath
} else {
    Write-Host "🔁 Virtual environment already exists at $venvPath"
}

# Activate only if not already in venv
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚙️ Activating virtual environment..."
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "⚡ Already inside a virtual environment"
}

# Install dependencies
if (Test-Path "requirements.txt") {
    Write-Host "📄 Installing from existing requirements.txt..."
    pip install -r requirements.txt
} else {
    Write-Host "🧰 Installing default package stack..."
    $defaultPackages = @(
        "requests",
        "pycaw",
        "paho-mqtt>=2.0.0",
        "colorlog",
        "pystray",
        "Pillow",
        "pywin32"
    )
    foreach ($pkg in $defaultPackages) {
        Write-Host "📦 Installing $pkg..."
        pip install $pkg
    }
}

# Export full list to requirements.txt
Write-Host "📝 Generating requirements.txt..."
pip freeze | Out-File -Encoding UTF8 requirements.txt

Write-Host "`n✅ Environment ready! Launch with '.venv\\Scripts\\Activate.ps1' and run 'python teams_monitor.py'" -ForegroundColor Green
