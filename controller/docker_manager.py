"""
Docker Manager Module for Mini OS
Handles container lifecycle operations using Docker SDK
"""

import docker
import logging
from typing import Dict, List, Optional, Tuple
from docker.types import Mount

logger = logging.getLogger(__name__)


class DockerManager:
    """Manages Docker container operations for Mini OS"""

    def __init__(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def create_network(self, network_name: str) -> bool:
        """
        Create a custom bridge network for Mini OS

        Args:
            network_name: Name of the network to create

        Returns:
            True if successful, False otherwise
        """
        try:
            existing_networks = self.client.networks.list(names=[network_name])
            if existing_networks:
                logger.info(f"Network '{network_name}' already exists")
                return True

            self.client.networks.create(network_name, driver="bridge")
            logger.info(f"Network '{network_name}' created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create network: {e}")
            return False

    def remove_network(self, network_name: str) -> bool:
        """Remove a Docker network"""
        try:
            network = self.client.networks.get(network_name)
            network.remove()
            logger.info(f"Network '{network_name}' removed")
            return True
        except docker.errors.NotFound:
            logger.warning(f"Network '{network_name}' not found")
            return False
        except Exception as e:
            logger.error(f"Failed to remove network: {e}")
            return False

    def build_image(
        self, dockerfile_path: str, tag: str, buildargs: Optional[Dict] = None
    ) -> bool:
        """
        Build a Docker image from Dockerfile

        Args:
            dockerfile_path: Path to Dockerfile directory
            tag: Image tag (e.g., "mini-os/shell:latest")
            buildargs: Optional build arguments

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Building image '{tag}' from {dockerfile_path}")
            self.client.images.build(
                path=dockerfile_path, tag=tag, buildargs=buildargs or {}, rm=True
            )
            logger.info(f"Image '{tag}' built successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to build image: {e}")
            return False

    def create_container(
        self,
        name: str,
        image: str,
        network: str,
        volumes: Optional[Dict[str, Dict]] = None,
        ports: Optional[Dict[str, int]] = None,
        environment: Optional[Dict[str, str]] = None,
        cpu_limit: float = 0.5,
        memory_limit: str = "256m",
        stdin_open: bool = False,
        tty: bool = False,
        command: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create a Docker container

        Args:
            name: Container name
            image: Image to run
            network: Network to connect to
            volumes: Volume configuration
            ports: Port mappings
            environment: Environment variables
            cpu_limit: CPU limit (cores)
            memory_limit: Memory limit
            stdin_open: Keep stdin open
            tty: Allocate pseudo-TTY
            command: Override CMD
            labels: Container labels

        Returns:
            Container ID if successful, None otherwise
        """
        try:
            # Check if container already exists
            existing = self._get_container(name)
            if existing:
                logger.warning(f"Container '{name}' already exists")
                return existing.id

            container_config = {
                "image": image,
                "name": name,
                "network": network,
                "detach": True,
                "stdin_open": stdin_open,
                "tty": tty,
                "cpu_period": 100000,
                "cpu_quota": int(cpu_limit * 100000),
                "mem_limit": memory_limit,
                "environment": environment or {},
                "labels": labels or {"mini-os": "true"},
            }

            if volumes:
                container_config["volumes"] = volumes
            if ports:
                container_config["ports"] = ports
            if command:
                container_config["command"] = command

            container = self.client.containers.create(**container_config)

            # Connect to network if specified
            try:
                network_obj = self.client.networks.get(network)
                network_obj.connect(container)
            except Exception as e:
                logger.warning(f"Failed to connect to network: {e}")

            logger.info(f"Container '{name}' created with ID: {container.id[:12]}")
            return container.id
        except Exception as e:
            logger.error(f"Failed to create container '{name}': {e}")
            return None

    def start_container(self, name: str) -> bool:
        """
        Start a container

        Args:
            name: Container name or ID

        Returns:
            True if successful, False otherwise
        """
        try:
            container = self._get_container(name)
            if not container:
                logger.error(f"Container '{name}' not found")
                return False

            if container.status == "running":
                logger.info(f"Container '{name}' is already running")
                return True

            container.start()
            logger.info(f"Container '{name}' started")
            return True
        except Exception as e:
            logger.error(f"Failed to start container '{name}': {e}")
            return False

    def stop_container(self, name: str, timeout: int = 10) -> bool:
        """
        Stop a container

        Args:
            name: Container name or ID
            timeout: Timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            container = self._get_container(name)
            if not container:
                logger.error(f"Container '{name}' not found")
                return False

            if container.status == "exited":
                logger.info(f"Container '{name}' is already stopped")
                return True

            container.stop(timeout=timeout)
            logger.info(f"Container '{name}' stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop container '{name}': {e}")
            return False

    def remove_container(self, name: str, force: bool = False) -> bool:
        """
        Remove a container

        Args:
            name: Container name or ID
            force: Force remove even if running

        Returns:
            True if successful, False otherwise
        """
        try:
            container = self._get_container(name)
            if not container:
                logger.info(f"Container '{name}' not found")
                return True

            if container.status == "running" and not force:
                logger.warning(
                    f"Container '{name}' is running. Use force=True to remove"
                )
                return False

            container.remove(force=force)
            logger.info(f"Container '{name}' removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove container '{name}': {e}")
            return False

    def list_containers(self, all: bool = False) -> List[Dict]:
        """
        List containers

        Args:
            all: List all containers (including stopped)

        Returns:
            List of container dictionaries
        """
        try:
            containers = self.client.containers.list(all=all)
            result = []
            for container in containers:
                result.append(
                    {
                        "id": container.id[:12],
                        "name": container.name,
                        "status": container.status,
                        "image": (
                            container.image.tags[0]
                            if container.image.tags
                            else "unknown"
                        ),
                        "labels": container.labels,
                    }
                )
            return result
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    def get_container_logs(self, name: str, tail: int = 100) -> Optional[str]:
        """
        Get container logs

        Args:
            name: Container name or ID
            tail: Number of log lines to retrieve

        Returns:
            Log string or None if failed
        """
        try:
            container = self._get_container(name)
            if not container:
                return None

            logs = container.logs(tail=tail).decode("utf-8")
            return logs
        except Exception as e:
            logger.error(f"Failed to get logs for '{name}': {e}")
            return None

    def exec_command(self, name: str, command: str) -> Tuple[int, str]:
        """
        Execute a command in a running container

        Args:
            name: Container name or ID
            command: Command to execute

        Returns:
            Tuple of (exit_code, output)
        """
        try:
            container = self._get_container(name)
            if not container:
                return 1, f"Container '{name}' not found"

            result = container.exec_run(command, demux=False)
            return result.exit_code, result.output.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to exec command in '{name}': {e}")
            return 1, str(e)

    def get_container_stats(self, name: str) -> Optional[Dict]:
        """
        Get container resource stats

        Args:
            name: Container name or ID

        Returns:
            Stats dictionary or None if failed
        """
        try:
            container = self._get_container(name)
            if not container:
                return None

            stats = container.stats(stream=False)
            return {
                "id": container.id[:12],
                "name": container.name,
                "cpu_percent": stats.get("cpu_stats", {})
                .get("cpu_usage", {})
                .get("total_usage", 0),
                "memory_usage": stats.get("memory_stats", {}).get("usage", 0),
                "memory_limit": stats.get("memory_stats", {}).get("limit", 0),
            }
        except Exception as e:
            logger.error(f"Failed to get stats for '{name}': {e}")
            return None

    def _get_container(self, name: str) -> Optional[docker.models.containers.Container]:
        """
        Get a container by name or ID

        Args:
            name: Container name or ID

        Returns:
            Container object or None if not found
        """
        try:
            return self.client.containers.get(name)
        except docker.errors.NotFound:
            return None
        except Exception as e:
            logger.error(f"Error getting container: {e}")
            return None

    def cleanup(self) -> bool:
        """Clean up resources"""
        try:
            self.client.close()
            logger.info("Docker manager cleaned up")
            return True
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return False
