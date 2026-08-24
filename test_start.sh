#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONTROLLER_DIR="$PROJECT_ROOT/controller"

echo -e "${GREEN}"
echo "=================================================="
echo "Mini OS - Test Setup (No Docker)"
echo "=================================================="
echo -e "${NC}"

# Step 1: Create directories
echo -e "${YELLOW}Step 1: Creating necessary directories...${NC}"
mkdir -p "$PROJECT_ROOT/data/logs"
mkdir -p "$PROJECT_ROOT/data/volumes"
mkdir -p "$PROJECT_ROOT/data/users"

echo -e "${GREEN}✓ Directories created${NC}"

# Step 2: Build Docker images
echo -e "${YELLOW}Step 2: Building Docker images...${NC}"

services=("shell" "file" "logger")

for service in "${services[@]}"; do
    echo -e "${YELLOW}  Building mini-os/$service:latest...${NC}"
    if docker build -t "mini-os/$service:latest" "services/$service" 2>&1 | grep -q "Successfully tagged"; then
        echo -e "${GREEN}  ✓ Built mini-os/$service:latest${NC}"
    else
        echo -e "${YELLOW}  ⚠ Docker build skipped or failed (ensure docker daemon is running)${NC}"
    fi
done

# Step 3: Setup Python environment
echo -e "${YELLOW}Step 3: Setting up Python environment...${NC}"

# Use current relative paths
cd "controller" || exit 1
CONTROLLER_DIR="$(pwd)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
VENV_DIR="../venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}  Creating Python virtual environment...${NC}"
    if python3 -m venv "$VENV_DIR"; then
        echo -e "${GREEN}  ✓ Virtual environment created${NC}"
    else
        echo -e "${RED}  ✗ Failed to create virtual environment${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}  Virtual environment already exists${NC}"
fi

# Check if activate script exists
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${RED}✗ Virtual environment activation script not found${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}  Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Install Python dependencies
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}  Creating requirements.txt...${NC}"
    cat > requirements.txt << 'EOF'
docker>=6.0.0
EOF
fi

echo -e "${YELLOW}  Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet

# Make CLI executable
chmod +x "$CONTROLLER_DIR/cli.py"

echo -e "${GREEN}✓ Python environment ready${NC}"

echo -e "${GREEN}"
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Now you can use:"
echo "  python3 controller/cli.py user create USERNAME"
echo "  python3 controller/cli.py status"
echo ""
echo -e "${NC}"
