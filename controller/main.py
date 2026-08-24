"""
Mini OS Controller - Main orchestrator for container-based OS
Manages system state, services, and user sessions
"""

import json
import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from docker_manager import DockerManager

# Setup logging - will configure after determining paths
logger = None


class MiniOSController:
    """Main controller for Mini OS"""

    # Configuration
    NETWORK_NAME = "mini-os-net"
    STATE_FILE = "state.json"
    LOG_DIR = None  # Will be set based on config_dir
    DATA_DIR = None  # Will be set based on config_dir

    # Service definitions
    CORE_SERVICES = ["logger", "file", "shell-base"]

    def __init__(self, config_dir: str = "."):
        """
        Initialize Mini OS Controller

        Args:
            config_dir: Configuration directory
        """
        global logger

        self.config_dir = Path(config_dir)

        # Set up paths relative to config directory
        project_root = self.config_dir.parent
        MiniOSController.LOG_DIR = str(project_root / "data" / "logs")
        MiniOSController.DATA_DIR = str(project_root / "data")

        # Ensure directories exist
        os.makedirs(self.LOG_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(f"{self.LOG_DIR}/controller.log"),
                logging.StreamHandler(),
            ],
            force=True,
        )
        logger = logging.getLogger(__name__)

        self.state_file = self.config_dir / self.STATE_FILE
        self.docker = DockerManager()
        self.state = self._load_state()

        logger.info("Mini OS Controller initialized")

    def _load_state(self) -> Dict:
        """Load system state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

        # Default state
        return {
            "running_services": [],
            "users": [],
            "initialized": False,
            "startup_time": None,
            "network": None,
        }

    def _save_state(self) -> bool:
        """Save system state to file"""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
            logger.info("State saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    def startup(self) -> bool:
        """
        Initialize and start Mini OS

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("MINI OS STARTUP")
        logger.info("=" * 60)

        try:
            # Step 1: Create network
            logger.info("Step 1: Creating network...")
            if not self.docker.create_network(self.NETWORK_NAME):
                logger.error("Failed to create network")
                return False
            self.state["network"] = self.NETWORK_NAME

            # Step 2: Start core services
            logger.info("Step 2: Starting core services...")
            for service in self.CORE_SERVICES:
                if not self._start_service(service):
                    logger.error(f"Failed to start service: {service}")
                    return False

            # Step 3: Update state
            self.state["initialized"] = True
            self.state["startup_time"] = datetime.now().isoformat()
            self._save_state()

            logger.info("=" * 60)
            logger.info("MINI OS STARTUP COMPLETE")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            return False

    def shutdown(self) -> bool:
        """
        Shutdown Mini OS

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("MINI OS SHUTDOWN")
        logger.info("=" * 60)

        try:
            # Stop all containers
            containers = self.docker.list_containers(all=False)
            for container in containers:
                logger.info(f"Stopping container: {container['name']}")
                self.docker.stop_container(container["id"])

            # Update state
            self.state["initialized"] = False
            self.state["running_services"] = []
            self._save_state()

            logger.info("=" * 60)
            logger.info("MINI OS SHUTDOWN COMPLETE")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
            return False

    def status(self) -> Dict:
        """
        Get system status

        Returns:
            Status dictionary
        """
        containers = self.docker.list_containers(all=True)
        running_count = sum(1 for c in containers if "running" in c["status"])

        status = {
            "initialized": self.state.get("initialized", False),
            "startup_time": self.state.get("startup_time"),
            "network": self.state.get("network"),
            "services": self.state.get("running_services", []),
            "users": self.state.get("users", []),
            "containers_total": len(containers),
            "containers_running": running_count,
            "containers": containers,
        }

        return status

    def _start_service(self, service_name: str) -> bool:
        """
        Start a core service

        Args:
            service_name: Service name (logger, file, shell-base)

        Returns:
            True if successful, False otherwise
        """
        try:
            container_name = f"mini-os-{service_name}"
            image_tag = f"mini-os/{service_name}:latest"

            # Check if already running
            containers = self.docker.list_containers()
            for container in containers:
                if (
                    container["name"] == container_name
                    and "running" in container["status"]
                ):
                    logger.info(f"Service '{service_name}' already running")
                    return True

            # Build image
            service_dir = (
                self.config_dir.parent / "services" / service_name.replace("-base", "")
            )
            if service_dir.exists():
                logger.info(f"Building image for {service_name}...")
                if not self.docker.build_image(str(service_dir), image_tag):
                    logger.error(f"Failed to build image for {service_name}")
                    return False

            # Create and start container
            volumes = None
            if service_name == "file":
                volumes = {f"{self.DATA_DIR}/volumes": {"bind": "/data", "mode": "rw"}}
            elif service_name == "logger":
                volumes = {f"{self.LOG_DIR}": {"bind": "/logs", "mode": "rw"}}

            container_id = self.docker.create_container(
                name=container_name,
                image=image_tag,
                network=self.NETWORK_NAME,
                volumes=volumes,
                environment={
                    "MINI_OS_SERVICE": service_name,
                },
                labels={
                    "mini-os": "true",
                    "service": service_name,
                },
            )

            if not container_id:
                logger.error(f"Failed to create container for {service_name}")
                return False

            # Start container
            if not self.docker.start_container(container_name):
                logger.error(f"Failed to start container {container_name}")
                return False

            logger.info(f"Service '{service_name}' started successfully")

            if service_name not in self.state["running_services"]:
                self.state["running_services"].append(service_name)

            return True

        except Exception as e:
            logger.error(f"Failed to start service '{service_name}': {e}")
            return False

    def create_user(
        self, username: str, cpu_limit: float = 0.5, memory_limit: str = "256m"
    ) -> bool:
        """
        Create a user session container

        Args:
            username: Username
            cpu_limit: CPU limit
            memory_limit: Memory limit

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Creating user session: {username}")

        try:
            # Check if user already exists
            if any(u["name"] == username for u in self.state.get("users", [])):
                logger.warning(f"User '{username}' already exists")
                return False

            container_name = f"mini-os-user-{username}"
            home_dir = f"{self.DATA_DIR}/users/{username}"

            # Create home directory
            os.makedirs(home_dir, exist_ok=True)

            # Create container
            container_id = self.docker.create_container(
                name=container_name,
                image="mini-os/shell:latest",
                network=self.NETWORK_NAME,
                volumes={
                    home_dir: {"bind": f"/home/{username}", "mode": "rw"},
                    f"{self.DATA_DIR}/volumes": {"bind": "/data", "mode": "ro"},
                },
                environment={
                    "USERNAME": username,
                    "HOME": f"/home/{username}",
                },
                stdin_open=True,
                tty=True,
                command="/bin/bash",
                cpu_limit=cpu_limit,
                memory_limit=memory_limit,
                labels={
                    "mini-os": "true",
                    "type": "user",
                    "username": username,
                },
            )

            if not container_id:
                logger.error(f"Failed to create user container")
                return False

            # Start container
            if not self.docker.start_container(container_name):
                logger.error(f"Failed to start user container")
                return False

            # Update state
            self.state["users"].append(
                {
                    "name": username,
                    "container_id": container_id[:12],
                    "container_name": container_name,
                    "created_at": datetime.now().isoformat(),
                    "home_dir": home_dir,
                }
            )
            self._save_state()

            logger.info(f"User '{username}' created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    def delete_user(self, username: str) -> bool:
        """
        Delete a user session

        Args:
            username: Username

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deleting user: {username}")

        try:
            user = next(
                (u for u in self.state.get("users", []) if u["name"] == username), None
            )
            if not user:
                logger.warning(f"User '{username}' not found")
                return False

            container_name = user["container_name"]

            # Stop and remove container
            self.docker.stop_container(container_name)
            self.docker.remove_container(container_name, force=True)

            # Update state
            self.state["users"] = [
                u for u in self.state["users"] if u["name"] != username
            ]
            self._save_state()

            logger.info(f"User '{username}' deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False

    def get_user_shell(self, username: str) -> Optional[str]:
        """
        Get user container name for attaching shell

        Args:
            username: Username

        Returns:
            Container name or None
        """
        user = next(
            (u for u in self.state.get("users", []) if u["name"] == username), None
        )
        if user:
            return user["container_name"]
        return None

    def get_running_services(self) -> List[str]:
        """Get list of running services"""
        return self.state.get("running_services", [])

    def cleanup(self) -> bool:
        """Cleanup resources"""
        try:
            self.docker.cleanup()
            logger.info("Controller cleaned up successfully")
            return True
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False
