#!/usr/bin/env bash
# Run helper for the project: activates venv and starts Streamlit
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

if [ -f "$VENV_DIR/bin/activate" ]; then
  echo "Activating virtualenv at $VENV_DIR"
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
else
  echo "Virtual environment not found at $VENV_DIR."
  echo "Create it with: python3 -m venv venv" 
  echo "Then install dependencies: pip install -r requirements.txt"
  exit 1
fi

if [ ! -f "$PROJECT_ROOT/app.py" ]; then
  echo "Error: app.py not found in project root ($PROJECT_ROOT)." >&2
  exit 1
fi

# Default port can be overridden with STREAMLIT_PORT environment variable
PORT="${STREAMLIT_PORT:-8501}"

echo "Starting Streamlit on port $PORT..."
exec streamlit run "$PROJECT_ROOT/app.py" --server.port "$PORT" "$@"
