
STREAMING_CHUNK:Configuring environment variables...

Exit immediately if a command exits with a non-zero status

set -e

STREAMING_CHUNK:Initializing the virtual environment...

echo "🧠 Setting up local Second Brain Python Environment..."

Check if .venv folder exists, if not, create it

if [ ! -d ".venv" ]; then
echo "📦 Creating isolated virtual environment (.venv)..."
python3 -m venv .venv
fi

STREAMING_CHUNK:Activating the virtual environment...

echo "🔌 Activating virtual environment..."
source .venv/bin/activate

STREAMING_CHUNK:Upgrading pip package manager...

echo "⚡ Upgrading pip..."
python3 -m pip install --upgrade pip

STREAMING_CHUNK:Installing gpt4free dependencies...

echo "📦 Installing gpt4free package..."
python3 -m pip install -U "g4f[all]"

STREAMING_CHUNK:Launching the UI dashboard...

echo "🚀 Launching Second Brain Dashboard UI..."
python3 brain_ui.py

STREAMING_CHUNK:Deactivating virtual environment on exit...

Deactivate virtual environment when the script finishes or is killed

deactivate


