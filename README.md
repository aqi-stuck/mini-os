# Mini OS - Container-Native Operating System

A minimal "container-native OS" where core system services and user environments run as isolated containers managed via Docker. The system boots into a controller that launches and manages containers as if they were OS processes.

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Mini OS System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Control Layer (Controller)                 │   │
│  │  - Python-based orchestrator                             │   │
│  │  - Manages container lifecycle                           │   │
│  │  - Tracks state and services                             │   │
│  │  - CLI interface                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ▲                                    │
│         ┌────────────────────┼────────────────────┐              │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌─────────────┐      ┌─────────────┐      ┌──────────────┐   │
│  │   Logger    │      │     File    │      │   Shell Base │   │
│  │  Container  │      │  Container  │      │  Container   │   │
│  │             │      │             │      │              │   │
│  │  - Logs     │      │  - /data    │      │  - bash      │   │
│  │  - Events   │      │  - Volumes  │      │  - tools     │   │
│  └─────────────┘      └─────────────┘      └──────────────┘   │
│         ▲                    ▲                    ▲              │
│         └────────────────────┼────────────────────┘              │
│                              │                                   │
│                    mini-os-net (bridge)                          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  User alice  │  │  User bob    │  │  User charlie│          │
│  │  Container   │  │  Container   │  │  Container   │          │
│  │              │  │              │  │              │          │
│  │  /home/alice │  │  /home/bob   │  │/home/charlie │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Components

#### 1. **Host Layer**
- Linux OS (Ubuntu 22.04 recommended)
- Docker runtime installed
- Bridge networking enabled

#### 2. **Control Layer**
- **Controller (main.py)**
  - Python service orchestrator
  - Manages container lifecycle
  - Maintains system state in `state.json`
  - Tracks services and users

- **Docker Manager (docker_manager.py)**
  - Abstraction over Docker SDK
  - Handles container operations
  - Network management
  - Resource constraints

- **CLI Interface (cli.py)**
  - Command-line tool
  - System management commands
  - User session management

#### 3. **Service Layer**
Each service runs as a container:

- **Logger Service** - Central log aggregation
- **File Service** - Shared volume management
- **Shell Base** - Base shell container for interactive use

#### 4. **User Environment Layer**
Each user gets an isolated container:
- Dedicated filesystem volume (`/home/<username>`)
- Resource limits (CPU/Memory)
- Access to shared data
- Interactive shell

## Project Structure

```
mini-os/
├── controller/
│   ├── main.py                 # Main controller logic
│   ├── docker_manager.py       # Docker operations
│   ├── cli.py                  # CLI interface
│   ├── state.json              # System state (auto-generated)
│   └── requirements.txt         # Python dependencies
│
├── services/
│   ├── shell/
│   │   └── Dockerfile          # Shell service image
│   ├── file/
│   │   └── Dockerfile          # File service image
│   └── logger/
│       └── Dockerfile          # Logger service image
│
├── configs/
│   └── docker-compose.yml       # Docker Compose configuration
│
├── scripts/
│   ├── start.sh                # Startup script
│   ├── stop.sh                 # Shutdown script
│   └── reset.sh                # Reset/cleanup script
│
└── README.md                    # This file
```

## Requirements

- **OS**: Ubuntu 20.04+ (or any Linux with Docker support)
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **Python**: 3.8+
- **Bash**: 4.0+

## GitHub Workflow

The repository includes a GitHub Actions workflow that checks Python syntax,
shell syntax, and Docker Compose configuration on every push and pull request.

```bash
git clone https://github.com/<owner>/<repository>.git
cd <repository>
chmod +x scripts/*.sh controller/cli.py
python3 -m venv venv
source venv/bin/activate
python -m pip install -r controller/requirements.txt
```

Run the local checks before opening a pull request:

```bash
python -m py_compile controller/*.py
for script in scripts/*.sh demo.sh test_start.sh; do bash -n "$script"; done
docker compose -f configs/docker-compose.yml config
```

The project runs on a Linux host with Docker. GitHub Actions validates the
repository; it does not provide a Docker host for deploying Mini OS itself.
For a server deployment, clone the repository on the host and follow
[DEPLOYMENT.md](DEPLOYMENT.md).

## Installation & Setup

### Step 1: Clone/Create Project

```bash
mkdir -p ~/mini-os-workspace
cd ~/mini-os-workspace
# Copy the mini-os project folder here
```

### Step 2: Make Scripts Executable

```bash
chmod +x mini-os/scripts/*.sh
chmod +x mini-os/controller/cli.py
```

### Step 3: Install Python Dependencies

```bash
cd mini-os/controller
pip3 install -r requirements.txt
```

### Step 4: Start Mini OS

```bash
cd ~/mini-os-workspace/mini-os
./scripts/start.sh
```

This will:
- Verify Docker installation
- Create necessary directories
- Build all Docker images
- Start the controller
- Initialize core services (logger, file, shell-base)
- Create the mini-os-net network

## Usage

### System Commands

#### Start Mini OS
```bash
python3 controller/cli.py start
```
Initializes the system, creates network, starts core services.

#### Stop Mini OS
```bash
python3 controller/cli.py stop
```
Gracefully stops all services.

#### Check Status
```bash
python3 controller/cli.py status
```
Shows detailed system status including running services and containers.

#### Get System Info (JSON)
```bash
python3 controller/cli.py info
```
Returns system information in JSON format.

### User Management

#### Create User
```bash
python3 controller/cli.py user create <username>
python3 controller/cli.py user create alice

# With custom resources
python3 controller/cli.py user create bob --cpu 0.25 --memory 512m
```

Creates an isolated user container with:
- Home directory: `/home/<username>`
- Shared data access: `/data` (read-only)
- Resource limits (default: 0.5 CPU, 256MB RAM)

#### Enter User Session
```bash
python3 controller/cli.py user enter <username>
python3 controller/cli.py user enter alice
```

Attaches to the user's shell container. Type `exit` to leave.

#### List Users
```bash
python3 controller/cli.py user list
```

Shows all active users and their containers.

#### Delete User
```bash
python3 controller/cli.py user delete <username>
```

Removes user container and home directory.

### Container Management

#### Launch Base Shell
```bash
python3 controller/cli.py launch-shell
```

Launches interactive bash in the shell-base container for system administration.

#### Kill Container
```bash
python3 controller/cli.py kill <container-name>
```

Stops a specific container.

#### View Logs
```bash
python3 controller/cli.py logs <container-name>
python3 controller/cli.py logs mini-os-logger --tail 50
```

View container logs.

## System State

Mini OS maintains state in `controller/state.json`:

```json
{
  "running_services": ["logger", "file", "shell"],
  "users": [
    {
      "name": "alice",
      "container_id": "abc123",
      "container_name": "mini-os-user-alice",
      "created_at": "2024-01-01T10:00:00",
      "home_dir": "/var/mini-os/data/users/alice"
    }
  ],
  "initialized": true,
  "startup_time": "2024-01-01T09:00:00",
  "network": "mini-os-net"
}
```

## Automation Scripts

### Start Script (`scripts/start.sh`)
- Checks Docker installation
- Creates system directories
- Builds Docker images
- Starts the controller
- Initializes the system

Usage:
```bash
./scripts/start.sh
```

### Stop Script (`scripts/stop.sh`)
- Stops all Mini OS services
- Cleans up containers

Usage:
```bash
./scripts/stop.sh
```

### Reset Script (`scripts/reset.sh`)
- **DESTRUCTIVE**: Removes all containers, networks, and optionally system directories
- Use with caution!

Usage:
```bash
./scripts/reset.sh
```

## Resource Management

### Default Limits
- **CPU**: 0.5 cores per container
- **Memory**: 256MB per container

### Custom Limits
When creating a user:
```bash
python3 controller/cli.py user create bob --cpu 1.0 --memory 512m
```

## Directories

### System Directories (created on startup)
- `/var/mini-os/logs/` - System logs
- `/var/mini-os/data/volumes/` - Shared data directory
- `/var/mini-os/data/users/` - User home directories

### Container Volumes
- **Logger**: `/logs` (mounted to `/var/mini-os/logs`)
- **File**: `/data` (mounted to `/var/mini-os/data/volumes`)
- **Users**: `/home/<username>` (mounted to user's directory)

## Networking

### Network Details
- **Name**: `mini-os-net`
- **Type**: Bridge network
- **DNS**: Container names are hostnames

### Service Discovery
Containers can communicate using container names:
```bash
# Inside container
ping mini-os-logger
curl http://mini-os-file:8080
```

## Logging

### Log Locations
- **Controller logs**: `/var/mini-os/logs/controller.log`
- **Container logs**: Accessible via `docker logs <container>`
- **System events**: `/var/mini-os/logs/system.log`

### View Logs
```bash
# View controller logs
tail -f /var/mini-os/logs/controller.log

# View specific container logs
docker logs mini-os-logger
docker logs mini-os-user-alice

# Via CLI
python3 controller/cli.py logs mini-os-logger
```

## Examples

### Example 1: Create and Use a User

```bash
# Start the system
./scripts/start.sh

# Create a user
python3 controller/cli.py user create developer

# Enter the user's shell
python3 controller/cli.py user enter developer

# Inside the container
$ cd /home/developer
$ echo "Hello from Mini OS" > hello.txt
$ ls -la
$ exit

# Back to host
python3 controller/cli.py user list
```

### Example 2: Check System Status

```bash
python3 controller/cli.py status

# Output shows:
# - System initialized: true
# - Running services: logger, file, shell
# - Active users: developer
# - Total containers: 4 (3 services + 1 user)
```

### Example 3: Multiple Users

```bash
python3 controller/cli.py user create alice
python3 controller/cli.py user create bob
python3 controller/cli.py user create charlie

# Each has isolated environment
python3 controller/cli.py user enter alice
# ...work as alice...
exit

python3 controller/cli.py user enter bob
# ...work as bob...
exit
```

### Example 4: Interactive Shell Administration

```bash
# Launch system administration shell
python3 controller/cli.py launch-shell

# Inside the shell
$ docker ps
$ ls /data
$ exit
```

## Known Limitations

1. **No Persistence Across Reboots**
   - System state is stored in state.json but depends on container runtime
   - Recommend systemd service integration for auto-restart

2. **Single-Node Only**
   - No clustering or multi-host support
   - Designed for single Linux machine

3. **Basic Resource Management**
   - CPU/Memory limits enforced at container level
   - No advanced scheduling or prioritization

4. **Limited Inter-Container Communication**
   - Services communicate via standard Docker networking
   - No service mesh or advanced orchestration

5. **No Built-in Security Policies**
   - Containers share same kernel
   - Standard Docker security applies
   - Recommendation: Enable AppArmor/SELinux at OS level

6. **No Storage Orchestration**
   - Uses local Docker volumes only
   - No distributed storage support

7. **No Built-in API**
   - Only CLI interface (can extend with REST API)
   - Controller requires local Python environment

8. **No High Availability**
   - Single point of failure (controller)
   - No failover mechanism

## Troubleshooting

### Issue: Docker permission denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue: Port already in use
```bash
# Find container using port
docker ps -a
# Stop conflicting container
docker stop <container-id>
```

### Issue: Cannot attach to user shell
```bash
# Check if container is running
python3 controller/cli.py status
# Verify with docker
docker ps
```

### Issue: Low disk space
```bash
# Clean up old containers
docker system prune -a
# Remove unused volumes
docker volume prune
```

## Performance Considerations

1. **Container Overhead**: ~10-50MB per container
2. **Network Latency**: Bridge network adds minimal latency (<1ms)
3. **I/O Performance**: Shared volumes have native filesystem performance
4. **Memory Usage**: 2-4GB for base system with 3 services + 5 users

## Extension Ideas

1. **Web Dashboard** - Flask/Node.js UI for management
2. **Process Scheduler** - Schedule tasks within containers
3. **Package Manager** - Pull new container images as "applications"
4. **Security Policies** - Role-based access control
5. **Metrics Collection** - Prometheus integration for monitoring
6. **API Server** - REST API for remote management
7. **Container Registry** - Local registry for custom images
8. **Backup/Restore** - Automated state snapshots

## Development

### Adding a New Service

1. Create service directory: `services/<service-name>/`
2. Create `Dockerfile`:
   ```dockerfile
   FROM ubuntu:22.04
   # Add service implementation
   CMD ["service-command"]
   ```
3. Update controller to recognize service
4. Rebuild images: `docker build -t mini-os/<service-name> services/<service-name>`

### Modifying the Controller

1. Edit `controller/main.py` or `docker_manager.py`
2. Restart controller: `./scripts/stop.sh && ./scripts/start.sh`

## Testing

The system includes automatic testing on startup:
- Network creation ✓
- Service deployment ✓
- Container connectivity ✓
- User container isolation ✓
- Volume mounting ✓

### Manual Tests

```bash
# Test 1: Create multiple users and verify isolation
python3 controller/cli.py user create test1
python3 controller/cli.py user create test2
python3 controller/cli.py user enter test1
# Create file in test1
$ echo "test1 data" > /home/test1/data.txt
$ exit

python3 controller/cli.py user enter test2
# Verify test1's file is not visible
$ ls /home/test2
$ exit

# Test 2: Verify shared data access
python3 controller/cli.py launch-shell
# Inside shell
$ echo "shared data" > /data/shared.txt
$ exit

python3 controller/cli.py user enter test1
# Verify access
$ cat /data/shared.txt
$ exit
```

## Contributing

To contribute improvements:
1. Fork/create a branch
2. Make changes with full error handling
3. Test thoroughly
4. Document changes
5. Submit for review

## License

MIT License - Use freely for educational and production purposes.

## Support

For issues or questions:
1. Check troubleshooting section
2. Review logs: `/var/mini-os/logs/controller.log`
3. Check Docker status: `docker ps -a`
4. Review state: `cat controller/state.json`

## Summary

Mini OS provides a lightweight, modular container-native operating system. It's ideal for:
- Learning containerization concepts
- Development and testing environments
- Isolated user session management
- Educational demonstrations
- Experimenting with container orchestration

Start with `./scripts/start.sh` and explore!
