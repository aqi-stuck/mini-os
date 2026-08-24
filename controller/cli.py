#!/usr/bin/env python3

import sys
import json
import argparse
from pathlib import Path
from typing import Optional
from main import MiniOSController
import subprocess


class MiniOSCLI:

    def __init__(self):
        """Initialize CLI"""
        self.controller = MiniOSController(str(Path(__file__).parent))

    def command_start(self, args) -> int:
        """Start Mini OS"""
        if self.controller.startup():
            print("✓ Mini OS started successfully")
            return 0
        else:
            print("✗ Failed to start Mini OS")
            return 1

    def command_stop(self, args) -> int:
        """Stop Mini OS"""
        if self.controller.shutdown():
            print("✓ Mini OS stopped successfully")
            return 0
        else:
            print("✗ Failed to stop Mini OS")
            return 1

    def command_status(self, args) -> int:
        """Display system status"""
        status = self.controller.status()

        print("\n" + "=" * 60)
        print("MINI OS STATUS")
        print("=" * 60)
        print(f"Initialized: {status['initialized']}")
        print(f"Network: {status['network']}")
        print(f"Startup Time: {status['startup_time']}")
        print(f"Services Running: {len(status['services'])}")
        print(f"Users: {len(status['users'])}")
        print(
            f"Containers (Total/Running): {status['containers_total']}/{status['containers_running']}"
        )

        if status["services"]:
            print(f"\nRunning Services:")
            for service in status["services"]:
                print(f"  - {service}")

        if status["users"]:
            print(f"\nActive Users:")
            for user in status["users"]:
                print(f"  - {user['name']} (ID: {user['container_id']})")

        print(f"\nContainers:")
        print(f"{'NAME':<30} {'STATUS':<15} {'IMAGE':<25}")
        print("-" * 70)
        for container in status["containers"]:
            print(
                f"{container['name']:<30} {container['status']:<15} {container['image']:<25}"
            )

        print("=" * 60 + "\n")
        return 0

    def command_launch_shell(self, args) -> int:
        """Launch interactive shell in base shell service"""
        try:
            container_name = "mini-os-shell-base"
            print(f"Launching shell in {container_name}...")
            print("Type 'exit' to quit")
            print("-" * 60)

            subprocess.run(
                ["docker", "exec", "-it", container_name, "/bin/bash"], check=False
            )
            return 0
        except Exception as e:
            print(f"✗ Failed to launch shell: {e}")
            return 1

    def command_kill(self, args) -> int:
        """Kill a container"""
        if not args.container:
            print("✗ Container name required")
            return 1

        try:
            print(f"Killing container: {args.container}...")
            if self.controller.docker.stop_container(args.container):
                print(f"✓ Container '{args.container}' stopped")
                return 0
            else:
                print(f"✗ Failed to stop container")
                return 1
        except Exception as e:
            print(f"✗ Error: {e}")
            return 1

    def command_user_create(self, args) -> int:
        """Create a new user session"""
        if not args.username:
            print("✗ Username required")
            return 1

        cpu = getattr(args, "cpu", 0.5)
        memory = getattr(args, "memory", "256m")

        if self.controller.create_user(args.username, cpu, memory):
            print(f"✓ User '{args.username}' created successfully")
            print(f"  Container: mini-os-user-{args.username}")
            print(f"  Home: /home/{args.username}")
            return 0
        else:
            print(f"✗ Failed to create user")
            return 1

    def command_user_enter(self, args) -> int:
        """Enter user session (attach shell)"""
        if not args.username:
            print("✗ Username required")
            return 1

        try:
            container_name = self.controller.get_user_shell(args.username)
            if not container_name:
                print(f"✗ User '{args.username}' not found")
                return 1

            print(f"Entering session for user '{args.username}'")
            print("Type 'exit' to quit")
            print("-" * 60)

            subprocess.run(
                ["docker", "exec", "-it", container_name, "/bin/bash"], check=False
            )
            return 0
        except Exception as e:
            print(f"✗ Failed to enter session: {e}")
            return 1

    def command_user_delete(self, args) -> int:
        """Delete a user session"""
        if not args.username:
            print("✗ Username required")
            return 1

        if self.controller.delete_user(args.username):
            print(f"✓ User '{args.username}' deleted successfully")
            return 0
        else:
            print(f"✗ Failed to delete user")
            return 1

    def command_user_list(self, args) -> int:
        """List all users"""
        status = self.controller.status()
        users = status.get("users", [])

        if not users:
            print("No users created yet")
            return 0

        print("\nActive Users:")
        print(f"{'Username':<20} {'Container ID':<15} {'Created':<30}")
        print("-" * 65)

        for user in users:
            print(
                f"{user['name']:<20} {user['container_id']:<15} {user['created_at']:<30}"
            )

        print()
        return 0

    def command_info(self, args) -> int:
        """Display system information"""
        status = self.controller.status()

        info = {
            "system": {
                "initialized": status["initialized"],
                "network": status["network"],
                "startup_time": status["startup_time"],
            },
            "services": status["services"],
            "user_count": len(status["users"]),
            "container_count": status["containers_total"],
            "running_containers": status["containers_running"],
        }

        print(json.dumps(info, indent=2))
        return 0

    def command_logs(self, args) -> int:
        """View container logs"""
        if not args.container:
            print("✗ Container name required")
            return 1

        try:
            logs = self.controller.docker.get_container_logs(
                args.container, tail=args.tail
            )
            if logs:
                print(f"Logs for '{args.container}' (last {args.tail} lines):")
                print("-" * 60)
                print(logs)
            else:
                print(f"No logs found for container '{args.container}'")
            return 0
        except Exception as e:
            print(f"✗ Error: {e}")
            return 1

    def run(self) -> int:
        """Run CLI"""
        parser = argparse.ArgumentParser(
            description="Mini OS - Container-Native Operating System", prog="mini-os"
        )

        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # System commands
        subparsers.add_parser("start", help="Start Mini OS")
        subparsers.add_parser("stop", help="Stop Mini OS")
        subparsers.add_parser("status", help="Show system status")
        subparsers.add_parser("info", help="Show system information (JSON)")
        subparsers.add_parser("launch-shell", help="Launch interactive shell")

        # Container commands
        kill_parser = subparsers.add_parser("kill", help="Stop a container")
        kill_parser.add_argument("container", help="Container name or ID")

        logs_parser = subparsers.add_parser("logs", help="View container logs")
        logs_parser.add_argument("container", help="Container name")
        logs_parser.add_argument(
            "--tail", type=int, default=100, help="Number of log lines"
        )

        # User commands
        user_parser = subparsers.add_parser("user", help="User management")
        user_subparsers = user_parser.add_subparsers(
            dest="user_command", help="User commands"
        )

        create_parser = user_subparsers.add_parser("create", help="Create user")
        create_parser.add_argument("username", help="Username")
        create_parser.add_argument("--cpu", type=float, default=0.5, help="CPU limit")
        create_parser.add_argument("--memory", default="256m", help="Memory limit")

        enter_parser = user_subparsers.add_parser("enter", help="Enter user session")
        enter_parser.add_argument("username", help="Username")

        delete_parser = user_subparsers.add_parser("delete", help="Delete user")
        delete_parser.add_argument("username", help="Username")

        user_subparsers.add_parser("list", help="List users")

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return 0

        # Route to command handlers
        if args.command == "start":
            return self.command_start(args)
        elif args.command == "stop":
            return self.command_stop(args)
        elif args.command == "status":
            return self.command_status(args)
        elif args.command == "info":
            return self.command_info(args)
        elif args.command == "launch-shell":
            return self.command_launch_shell(args)
        elif args.command == "kill":
            return self.command_kill(args)
        elif args.command == "logs":
            return self.command_logs(args)
        elif args.command == "user":
            if args.user_command == "create":
                return self.command_user_create(args)
            elif args.user_command == "enter":
                return self.command_user_enter(args)
            elif args.user_command == "delete":
                return self.command_user_delete(args)
            elif args.user_command == "list":
                return self.command_user_list(args)
            else:
                user_parser.print_help()
                return 0
        else:
            parser.print_help()
            return 0


def main():
    """Main entry point"""
    cli = MiniOSCLI()
    try:
        sys.exit(cli.run())
    except KeyboardInterrupt:
        print("\n✗ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
