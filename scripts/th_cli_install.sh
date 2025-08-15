#!/bin/bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd .. && pwd)"

echo "Installing Matter CLI..."

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "Installing pipx..."
    sudo apt update
    sudo apt install -y pipx
    pipx ensurepath
    export PATH="$HOME/.local/bin:$PATH"
fi

# Running Poetry install
source ~/.profile #ensure poetry is in path
poetry self update
poetry --project="$PROJECT_ROOT" install

# Build the package
echo "Building package..."
poetry --project="$PROJECT_ROOT" build

# Install with pipx
echo "Installing with pipx..."
cd "$PROJECT_ROOT"
pipx install . --force

echo ""
echo "Installation complete!"
echo ""
echo "To test: th-cli --help"
