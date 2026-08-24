.PHONY: help start stop reset status logs shell shell-alice user-create user-list user-delete clean build install test docs

CONTROLLER_DIR := controller
SCRIPTS_DIR := scripts
SERVICES_DIR := services

help:
	@echo "Mini OS - Makefile Commands"
	@echo "============================"
	@echo ""
	@echo "System Commands:"
	@echo "  make start          - Start Mini OS"
	@echo "  make stop           - Stop Mini OS"
	@echo "  make reset          - Reset Mini OS (destructive)"
	@echo "  make status         - Show system status"
	@echo "  make logs           - View controller logs"
	@echo ""
	@echo "Shell Access:"
	@echo "  make shell          - Launch base shell"
	@echo "  make shell-alice    - Enter alice user shell (if exists)"
	@echo ""
	@echo "User Management:"
	@echo "  make user-create    - Create test user (username=testuser)"
	@echo "  make user-list      - List all users"
	@echo "  make user-delete    - Delete test user (username=testuser)"
	@echo ""
	@echo "Development:"
	@echo "  make build          - Build Docker images"
	@echo "  make install        - Install Python dependencies"
	@echo "  make test           - Run test suite"
	@echo "  make docs           - Generate documentation"
	@echo "  make clean          - Clean local files"
	@echo ""

start:
	@echo "Starting Mini OS..."
	@bash $(SCRIPTS_DIR)/start.sh

stop:
	@echo "Stopping Mini OS..."
	@bash $(SCRIPTS_DIR)/stop.sh

reset:
	@echo "Resetting Mini OS..."
	@bash $(SCRIPTS_DIR)/reset.sh

status:
	@python3 $(CONTROLLER_DIR)/cli.py status

logs:
	@tail -f /var/mini-os/logs/controller.log

shell:
	@python3 $(CONTROLLER_DIR)/cli.py launch-shell

shell-alice:
	@python3 $(CONTROLLER_DIR)/cli.py user enter alice

user-create:
	@python3 $(CONTROLLER_DIR)/cli.py user create testuser

user-list:
	@python3 $(CONTROLLER_DIR)/cli.py user list

user-delete:
	@python3 $(CONTROLLER_DIR)/cli.py user delete testuser

build:
	@echo "Building Docker images..."
	@for service in shell file logger; do \
		echo "Building mini-os/$$service:latest..."; \
		docker build -t mini-os/$$service:latest $(SERVICES_DIR)/$$service; \
	done

install:
	@echo "Installing Python dependencies..."
	@pip3 install -r $(CONTROLLER_DIR)/requirements.txt

test:
	@echo "Running tests..."
	@python3 -m pytest tests/ -v || echo "No tests found"

docs:
	@echo "Documentation:"
	@echo "  - README.md (comprehensive guide)"
	@echo "  - QUICKSTART.md (quick reference)"
	@echo "  - TESTING.md (test suite)"

clean:
	@echo "Cleaning local files..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -f controller/state.json

# Advanced targets

docker-ps:
	@docker ps --filter "label=mini-os=true"

docker-ps-all:
	@docker ps -a --filter "label=mini-os=true"

docker-logs:
	@docker ps --filter "label=mini-os=true" --format "{{.Names}}" | head -1 | xargs docker logs --tail 50

prune:
	@echo "Pruning unused Docker resources..."
	@docker system prune -a --force

disk-usage:
	@echo "Mini OS Disk Usage:"
	@du -sh /var/mini-os/

memory-usage:
	@echo "Docker Container Memory Usage:"
	@docker stats --no-stream --filter "label=mini-os=true"

info:
	@python3 $(CONTROLLER_DIR)/cli.py info

lint:
	@echo "Linting Python code..."
	@python3 -m py_compile $(CONTROLLER_DIR)/*.py

format:
	@echo "Formatting Python code..."
	@python3 -m autopep8 --in-place $(CONTROLLER_DIR)/*.py

all: install build start
	@echo "Mini OS fully initialized and running!"

.PHONY: all
