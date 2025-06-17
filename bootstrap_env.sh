#!/usr/bin/env bash

set -e

echo -e "\n🔧 Bootstrapping Teams Monitor Environment..."

# Define environment directory
VENV=".venv"

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python3 not found. Please install Python 3.10+ and retry."
  exit 1
fi

# Create virtual environment if needed
if [ ! -d "$VENV" ]; then
  echo "📦 Creating virtual environment at $VENV..."
  python3 -m venv "$VENV"
else
  echo "🔁 Virtual environment already exists at $VENV"
fi

# Activate the virtual environment
echo "⚙️ Activating virtual environment..."
source "$VENV/bin/activate"

# Install dependencies
if [ -f "requirements.txt" ]; then
  echo "📄 Installing from existing requirements.txt..."
  pip install --upgrade pip
  pip install -r requirements.txt
else
  echo "🧰 Installing default package stack..."
  pip install --upgrade pip
  pip install requests pycaw paho-mqtt colorlog pystray Pillow pywin32 || true
fi

# Save frozen requirements
echo "📝 Exporting requirements.txt..."
pip freeze > requirements.txt

echo -e "\n✅ Setup complete! To start monitoring, activate venv with:\nsource $VENV/bin/activate\nand run:\npython3 teams_monitor.py\n"
