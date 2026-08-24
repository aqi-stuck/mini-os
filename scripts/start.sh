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
SERVICES_DIR="$PROJECT_ROOT/services"
CONTROLLER_DIR="$PROJECT_ROOT/controller"
CONFIGS_DIR="$PROJECT_ROOT/configs"

echo -e "${GREEN}"
echo "=================================================="
echo "Mini OS - Startup Script"
echo "=================================================="
echo -e "${NC}"

# Step 1: Check Docker
echo -e "${YELLOW}Step 1: Checking Docker installation...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"

# Step 2: Create directories
echo -e "${YELLOW}Step 2: Creating necessary directories...${NC}"
mkdir -p "$PROJECT_ROOT/data/logs"
mkdir -p "$PROJECT_ROOT/data/volumes"
mkdir -p "$PROJECT_ROOT/data/users"

echo -e "${GREEN}✓ Directories created${NC}"

# Step 3: Build Docker images
echo -e "${YELLOW}Step 3: Building Docker images...${NC}"

services=("shell" "file" "logger")

for service in "${services[@]}"; do
    echo -e "${YELLOW}  Building mini-os/$service:latest...${NC}"
    if docker build -t "mini-os/$service:latest" "$SERVICES_DIR/$service" 2>/dev/null; then
        echo -e "${GREEN}  ✓ Built mini-os/$service:latest${NC}"
    else
        echo -e "${YELLOW}  ⚠ Skipping docker build (requires docker daemon access)${NC}"
    fi
done

# Step 4: Start controller
echo -e "${YELLOW}Step 4: Starting Mini OS controller...${NC}"

cd "$CONTROLLER_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
VENV_DIR="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}  Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}  ✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install Python dependencies if needed
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

echo -e "${GREEN}✓ Controller ready${NC}"

# Step 5: Initialize system
echo -e "${YELLOW}Step 5: Initializing Mini OS system...${NC}"

python3 cli.py start

echo -e "${GREEN}"
echo "=================================================="
echo "Mini OS Startup Complete!"
echo "=================================================="
echo ""
echo "Available commands:"
echo "  ./scripts/stop.sh              - Stop Mini OS"
echo "  ./scripts/reset.sh             - Reset Mini OS (remove containers)"
echo "  $CONTROLLER_DIR/cli.py status          - Show system status"
echo "  $CONTROLLER_DIR/cli.py user create <name> - Create user"
echo "  $CONTROLLER_DIR/cli.py user enter <name>  - Enter user shell"
echo "  $CONTROLLER_DIR/cli.py launch-shell       - Launch base shell"
echo ""
echo -e "${NC}"
