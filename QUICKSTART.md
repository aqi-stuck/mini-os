# Mini OS - Quick Start Guide

Get Mini OS up and running in minutes!

## Prerequisites

- Ubuntu 20.04+ or compatible Linux distribution
- Docker 20.10+ installed
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

## Installation (5 minutes)

### 1. Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

### 2. Clone Mini OS Project

```bash
git clone <repo-url> mini-os-workspace
cd mini-os-workspace/mini-os
```

### 3. Make Scripts Executable

```bash
chmod +x scripts/*.sh
chmod +x controller/cli.py
```

### 4. Start Mini OS

```bash
./scripts/start.sh
```

This takes 2-3 minutes and will:
- ✓ Build Docker images
- ✓ Create system network
- ✓ Start core services
- ✓ Initialize system state

**You should see**: "Mini OS Startup Complete!"

## Basic Usage (5 minutes)

### Create Your First User

```bash
python3 controller/cli.py user create alice
```

### Enter the User's Shell

```bash
python3 controller/cli.py user enter alice
```

You're now inside alice's isolated container!

```bash
$ whoami
alice

$ ls /home/alice
# Your home directory

$ echo "Hello Mini OS" > hello.txt

$ exit
```

### Check System Status

```bash
python3 controller/cli.py status
```

Output shows all running services and users.

### Create More Users

```bash
python3 controller/cli.py user create bob
python3 controller/cli.py user create charlie
python3 controller/cli.py user list
```

## Interactive Shell

Launch the base shell for system administration:

```bash
python3 controller/cli.py launch-shell
```

Inside the shell:
```bash
$ docker ps          # See all containers
$ ls /data           # Shared data directory
$ cat /logs/system.log  # System logs
$ exit
```

## Cleanup

### Stop Mini OS

```bash
./scripts/stop.sh
```

### Reset Everything (WARNING - Destructive)

```bash
./scripts/reset.sh
```

This removes all containers and data. Requires confirmation.

## Common Commands Cheat Sheet

| Command | Purpose |
|---------|---------|
| `./scripts/start.sh` | Start Mini OS |
| `./scripts/stop.sh` | Stop Mini OS |
| `python3 controller/cli.py status` | Show status |
| `python3 controller/cli.py user create <name>` | Create user |
| `python3 controller/cli.py user enter <name>` | Enter user shell |
| `python3 controller/cli.py user delete <name>` | Delete user |
| `python3 controller/cli.py user list` | List users |
| `python3 controller/cli.py launch-shell` | Admin shell |
| `docker ps` | List containers |
| `docker logs mini-os-logger` | View service logs |

## Troubleshooting

### "Docker permission denied" Error

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Then retry the command.

### "No such image: mini-os/shell:latest"

The images need to be built:
```bash
./scripts/start.sh
```

This builds the images automatically.

### Cannot Connect to User Shell

Check if system is running:
```bash
python3 controller/cli.py status
```

Should show "Initialized: true"

If not, start it:
```bash
./scripts/start.sh
```

### Low Disk Space

Clean up Docker:
```bash
docker system prune -a
docker volume prune
```

## What's Happening Behind the Scenes?

1. **Network Creation**: A Docker bridge network named `mini-os-net` is created
2. **Core Services Start**:
   - `mini-os-logger` - Collects system logs
   - `mini-os-file` - Manages shared data
   - `mini-os-shell-base` - Base shell container
3. **Controller Running**: Python controller manages everything
4. **Users Created**: Each user gets an isolated container

## Next Steps

After getting familiar with basics:

1. **Explore Logs**:
   ```bash
   tail -f /var/mini-os/logs/controller.log
   ```

2. **View System State**:
   ```bash
   cat controller/state.json
   ```

3. **Create Development Users**:
   ```bash
   python3 controller/cli.py user create dev1 --cpu 1.0 --memory 512m
   python3 controller/cli.py user create dev2 --cpu 1.0 --memory 512m
   ```

4. **Test Isolation**:
   - Create two users
   - Each has separate `/home` directory
   - Changes in one don't affect the other

5. **Read Full Documentation**:
   See [README.md](README.md) for comprehensive documentation

## Performance Tips

- For better performance, use SSD for `/var/mini-os`
- Allocate more resources in `controller/main.py` based on your hardware
- Monitor container resource usage: `docker stats`

## Cleanup Before Shutdown

```bash
# Delete users first
python3 controller/cli.py user delete alice
python3 controller/cli.py user delete bob

# Stop the system
./scripts/stop.sh

# Optional: Full reset
./scripts/reset.sh
```

## Get Help

1. Check logs: `tail -f /var/mini-os/logs/controller.log`
2. View status: `python3 controller/cli.py status`
3. Use docker commands: `docker ps`, `docker logs <container>`
4. Read full README: [README.md](README.md)

---

**You're ready to go!** Start with `./scripts/start.sh` 🚀
