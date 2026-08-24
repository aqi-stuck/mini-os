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
echo "Mini OS - Shutdown Script"
echo "=================================================="
echo -e "${NC}"

# Step 1: Stop Mini OS system
echo -e "${YELLOW}Step 1: Stopping Mini OS system...${NC}"

cd "$CONTROLLER_DIR"
python3 cli.py stop

echo -e "${GREEN}✓ Mini OS stopped${NC}"

# Step 2: Stop any remaining containers
echo -e "${YELLOW}Step 2: Cleaning up remaining containers...${NC}"

# Stop all mini-os containers
docker ps -a --filter "label=mini-os=true" --format "{{.Names}}" | while read container; do
    if [ -n "$container" ]; then
        echo -e "${YELLOW}  Stopping $container...${NC}"
        docker stop "$container" 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓ Cleanup complete${NC}"

echo -e "${GREEN}"
echo "=================================================="
echo "Mini OS Shutdown Complete!"
echo "=================================================="
echo -e "${NC}"
