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

echo -e "${RED}"
echo "=================================================="
echo "Mini OS - Reset Script (DESTRUCTIVE)"
echo "=================================================="
echo -e "${NC}"

echo -e "${YELLOW}WARNING: This will remove all Mini OS containers and data!${NC}"
read -p "Are you sure? (yes/no): " -r response

if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Reset cancelled"
    exit 0
fi

# Step 1: Stop all containers
echo -e "${YELLOW}Step 1: Stopping all Mini OS containers...${NC}"

docker ps -a --filter "label=mini-os=true" --format "{{.Names}}" | while read container; do
    if [ -n "$container" ]; then
        echo -e "${YELLOW}  Stopping $container...${NC}"
        docker stop "$container" 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓ All containers stopped${NC}"

# Step 2: Remove containers
echo -e "${YELLOW}Step 2: Removing containers...${NC}"

docker ps -a --filter "label=mini-os=true" --format "{{.Names}}" | while read container; do
    if [ -n "$container" ]; then
        echo -e "${YELLOW}  Removing $container...${NC}"
        docker rm "$container" 2>/dev/null || true
    fi
done

echo -e "${GREEN}✓ Containers removed${NC}"

# Step 3: Remove network
echo -e "${YELLOW}Step 3: Removing network...${NC}"

if docker network ls --format "{{.Name}}" | grep -q "^mini-os-net$"; then
    docker network remove mini-os-net
    echo -e "${GREEN}✓ Network removed${NC}"
fi

# Step 4: Clean state
echo -e "${YELLOW}Step 4: Cleaning state file...${NC}"

if [ -f "$PROJECT_ROOT/controller/state.json" ]; then
    rm "$PROJECT_ROOT/controller/state.json"
    echo -e "${GREEN}✓ State file removed${NC}"
fi

# Step 5: Optional - Remove system directories
echo -e "${YELLOW}Step 5: Clean system directories...${NC}"

read -p "Remove /var/mini-os directory? (yes/no): " -r response_dir

if [[ "$response_dir" =~ ^[Yy][Ee][Ss]$ ]]; then
    sudo rm -rf /var/mini-os
    echo -e "${GREEN}✓ System directory removed${NC}"
fi

echo -e "${GREEN}"
echo "=================================================="
echo "Mini OS Reset Complete!"
echo "=================================================="
echo -e "${NC}"

echo "To start again, run: ./scripts/start.sh"
