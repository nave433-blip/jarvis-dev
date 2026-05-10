#!/bin/bash

# JARVIS: Local AI Coding Assistant Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/nave433-blip/jarvis-dev/main/install.sh | bash

set -e

REPO="https://github.com/nave433-blip/jarvis-dev.git"
INSTALL_DIR="$HOME/jarvis-dev"

echo "Installing JARVIS..."

# 1. Clone
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory $INSTALL_DIR already exists. Updating..."
    cd "$INSTALL_DIR" && git pull
else
    git clone "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 2. Setup Venv
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 3. Add Alias
SHELL_RC="$HOME/.zshrc"
if [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bash_profile"
fi

if ! grep -q "alias jarvis=" "$SHELL_RC"; then
    echo "Adding alias to $SHELL_RC"
    echo "alias jarvis='$INSTALL_DIR/jarvis'" >> "$SHELL_RC"
    echo "Restart your terminal or run 'source $SHELL_RC' to start using jarvis."
fi

echo "JARVIS installation complete!"
