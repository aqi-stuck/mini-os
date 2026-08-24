"""
Utility functions for Mini OS
"""

import os
import json
import time
from typing import Dict, List, Any
from datetime import datetime
import subprocess


def ensure_directories():
    """Ensure all required directories exist"""
    dirs = [
        "/var/mini-os/logs",
        "/var/mini-os/data/volumes",
        "/var/mini-os/data/users",
    ]

    for dir_path in dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            os.chmod(dir_path, 0o777)
        except Exception as e:
            print(f"Warning: Could not create {dir_path}: {e}")


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable format"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def format_cpu_percent(cpu_usage: int, cpu_limit: int = 0) -> str:
    """Format CPU usage as percentage"""
    if cpu_limit == 0:
        return "N/A"
    percent = (cpu_usage / cpu_limit) * 100
    return f"{percent:.1f}%"


def timestamp_now() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def log_event(
    event_type: str, description: str, details: Dict[str, Any] = None
) -> bool:
    """Log an event to the system log"""
    try:
        log_file = "/var/mini-os/logs/system.log"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        event = {
            "timestamp": timestamp_now(),
            "type": event_type,
            "description": description,
            "details": details or {},
        }

        with open(log_file, "a") as f:
            f.write(json.dumps(event) + "\n")

        return True
    except Exception as e:
        print(f"Error logging event: {e}")
        return False


def run_command(command: str, shell: bool = False) -> tuple:
    """
    Run a shell command

    Args:
        command: Command to run
        shell: Whether to use shell=True

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command if shell else command.split(),
            capture_output=True,
            text=True,
            shell=shell,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def validate_username(username: str) -> bool:
    """Validate username format"""
    if not username or len(username) < 1 or len(username) > 32:
        return False

    # Allow alphanumeric, dash, underscore
    valid_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    )
    return all(c in valid_chars for c in username)


def validate_container_name(name: str) -> bool:
    """Validate Docker container name"""
    if not name or len(name) < 1 or len(name) > 64:
        return False

    # Docker container names: alphanumeric, dash, underscore
    valid_chars = set(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    )
    return all(c in valid_chars for c in name)


def parse_memory_limit(memory_str: str) -> int:
    """
    Parse memory limit string to bytes

    Args:
        memory_str: Memory string (e.g., "256m", "1g")

    Returns:
        Memory in bytes
    """
    units = {
        "b": 1,
        "k": 1024,
        "m": 1024**2,
        "g": 1024**3,
    }

    memory_str = memory_str.lower().strip()

    for unit, multiplier in units.items():
        if memory_str.endswith(unit):
            try:
                value = float(memory_str[:-1])
                return int(value * multiplier)
            except ValueError:
                return 256 * 1024 * 1024  # Default 256MB

    return 256 * 1024 * 1024  # Default 256MB


def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    info = {
        "timestamp": timestamp_now(),
        "hostname": os.uname().nodename,
        "kernel": os.uname().release,
        "python_version": os.sys.version,
    }

    # Try to get CPU count
    try:
        import multiprocessing

        info["cpu_count"] = multiprocessing.cpu_count()
    except:
        info["cpu_count"] = "Unknown"

    return info


def read_state_file(filepath: str) -> Dict:
    """Safely read state JSON file"""
    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading state file: {e}")

    return {}


def write_state_file(filepath: str, state: Dict) -> bool:
    """Safely write state JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing state file: {e}")
        return False


def get_container_size(container_id: str) -> Dict[str, int]:
    """Get container size info"""
    exit_code, stdout, stderr = run_command(
        f"docker inspect --format='{{json .SizeRw}},{{json .SizeRootFs}}' {container_id}"
    )

    try:
        parts = stdout.strip().split(",")
        return {
            "rw_size": int(parts[0]) if parts[0] else 0,
            "root_fs_size": int(parts[1]) if parts[1] else 0,
        }
    except:
        return {"rw_size": 0, "root_fs_size": 0}


def cleanup_old_logs(log_dir: str, max_age_days: int = 7) -> int:
    """
    Clean up old log files

    Args:
        log_dir: Log directory path
        max_age_days: Maximum age in days

    Returns:
        Number of files deleted
    """
    import glob

    deleted = 0
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60

    try:
        for log_file in glob.glob(os.path.join(log_dir, "*.log*")):
            file_age = current_time - os.path.getmtime(log_file)
            if file_age > max_age_seconds:
                try:
                    os.remove(log_file)
                    deleted += 1
                except:
                    pass
    except Exception as e:
        print(f"Error cleaning up logs: {e}")

    return deleted
