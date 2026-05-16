#!/bin/bash

# JARVIS: Global Installer
# Target: macOS

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting JARVIS Global Installation...${NC}"

# 1. Dependency Check
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew is not installed. Please install it from https://brew.sh/${NC}"
    exit 1
fi

if ! command -v portaudio &> /dev/null && ! brew list portaudio &> /dev/null; then
    echo -e "${BLUE}📦 Installing portaudio (required for voice)...${NC}"
    brew install portaudio
fi

if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}⚠️ Ollama not found. JARVIS recommends Ollama for local LLM support.${NC}"
    echo -e "Install it from https://ollama.com/"
fi

# 2. Directory Setup
INSTALL_DIR="$HOME/.jarvis-app"
mkdir -p "$INSTALL_DIR"

echo -e "${BLUE}📂 Setting up JARVIS in $INSTALL_DIR...${NC}"

# 3. Clone or Copy Files
if [ -d ".git" ]; then
    echo -e "${BLUE}📂 Copying files from current directory...${NC}"
    cp -R . "$INSTALL_DIR"
else
    echo -e "${BLUE}📂 Cloning JARVIS repository...${NC}"
    git clone https://github.com/nave433-blip/jarvis-dev.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 4. Virtual Environment & Install
echo -e "${BLUE}🐍 Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${BLUE}📦 Installing JARVIS and dependencies...${NC}"
pip install --upgrade pip
pip install -e .

# 5. Global Link
echo -e "${BLUE}🔗 Creating global link...${NC}"
BIN_PATH="/usr/local/bin/jarvis"

# Create a small wrapper script for the global command
cat <<EOF > jarvis-wrapper
#!/bin/bash
source $INSTALL_DIR/venv/bin/activate
exec $INSTALL_DIR/venv/bin/jarvis "\$@"
EOF

chmod +x jarvis-wrapper

if [ -w "/usr/local/bin" ]; then
    mv jarvis-wrapper "$BIN_PATH"
    echo -e "${GREEN}✅ Successfully linked jarvis to $BIN_PATH${NC}"
else
    echo -e "${YELLOW}⚠️ No write access to /usr/local/bin. Using sudo...${NC}"
    sudo mv jarvis-wrapper "$BIN_PATH"
    sudo chown $(whoami) "$BIN_PATH"
    echo -e "${GREEN}✅ Successfully linked jarvis to $BIN_PATH (with sudo)${NC}"
fi

# 6. Final Setup
echo -e "${GREEN}✨ JARVIS is now installed globally!${NC}"
echo -e "Try typing '${BLUE}jarvis${NC}' in your terminal."

# Run setup wizard if config doesn't exist
if [ ! -f "$HOME/.jarvis/config.json" ]; then
    echo -e "${BLUE}🤖 Starting setup wizard...${NC}"
    jarvis setup
fi
