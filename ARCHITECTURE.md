# Mini OS - Architecture Details

## System Architecture Diagram

### High-Level Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     User / Administrator                          │
│                         (Human)                                   │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ (CLI Commands)
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│                   Mini OS CLI                                    │
│                    (cli.py)                                      │
│                                                                   │
│  Commands: start, stop, status, user create/enter/delete        │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ (API Calls)
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│              Mini OS Controller                                  │
│               (main.py)                                          │
│                                                                   │
│  Responsibilities:                                               │
│  - Orchestrate services                                          │
│  - Manage user sessions                                          │
│  - Maintain system state                                         │
│  - Track containers                                              │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ (Docker SDK)
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│            Docker Manager                                        │
│          (docker_manager.py)                                     │
│                                                                   │
│  Operations:                                                     │
│  - Container lifecycle                                           │
│  - Network management                                            │
│  - Resource allocation                                           │
│  - Log access                                                    │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ (Docker API)
                       │
┌──────────────────────▼─────────────────────────────────────────┐
│            Docker Engine & Runtime                               │
│                                                                   │
│  - Container isolation                                           │
│  - Volume management                                             │
│  - Network management                                            │
│  - Resource limits                                               │
└──────────────────────┬─────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       Docker        Volumes       Network
      Containers   (Persistence)  (Communication)
```

## Container Architecture

```
                         mini-os-net (Bridge Network)
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        │                        │                        │
    ┌───▼────────────┐   ┌──────▼──────┐      ┌─────────▼────┐
    │ mini-os-logger │   │  mini-os    │      │ mini-os-shell│
    │   Container    │   │ file service│      │  -base       │
    │                │   │  Container  │      │ Container    │
    ├────────────────┤   ├─────────────┤      ├──────────────┤
    │ Services:      │   │ Services:   │      │ Services:    │
    │ - Log collect  │   │ - Data mgmt │      │ - Shell      │
    │ - Event track  │   │ - Volumes   │      │ - Tools      │
    │ - Persistence  │   │ - Sharing   │      │ - Debugging  │
    └───────┬────────┘   └──────┬──────┘      └──────┬───────┘
            │                   │                    │
            ▼                   ▼                    ▼
        /logs                /data              /bin/bash
      (Volume)             (Volume)           (Interactive)
        ┌────────────────────────────────────────┐
        │      User Containers (1:N)             │
        │                                         │
        ├─ mini-os-user-alice   (/home/alice)   │
        ├─ mini-os-user-bob     (/home/bob)     │
        ├─ mini-os-user-charlie (/home/charlie) │
        └─ mini-os-user-dev1    (/home/dev1)    │
```

## Data Flow Diagram

### User Creation Flow

```
CLI Command: user create alice
       │
       ▼
CLI Handler (create_user)
       │
       ▼
Controller.create_user("alice")
       │
       ├─ Create home directory
       │  /var/mini-os/data/users/alice
       │
       ├─ Call DockerManager.create_container()
       │  ├─ Image: mini-os/shell:latest
       │  ├─ Name: mini-os-user-alice
       │  ├─ Network: mini-os-net
       │  ├─ Volumes: /home/alice, /data (ro)
       │  └─ Resources: CPU 0.5, RAM 256MB
       │
       ├─ Call DockerManager.start_container()
       │
       ├─ Update state.json
       │  └─ Add user record
       │
       └─ Return success
```

### User Shell Access Flow

```
CLI Command: user enter alice
       │
       ▼
CLI Handler (enter_user)
       │
       ├─ Get container name from state
       │  (mini-os-user-alice)
       │
       └─ Execute: docker exec -it mini-os-user-alice /bin/bash
              │
              ▼
         User gets interactive shell
         with isolated environment
```

### System Startup Flow

```
./scripts/start.sh
       │
       ├─ Check Docker installation
       │
       ├─ Create system directories
       │  └─ /var/mini-os/{logs,data/volumes,data/users}
       │
       ├─ Build Docker images
       │  ├─ mini-os/shell:latest
       │  ├─ mini-os/file:latest
       │  └─ mini-os/logger:latest
       │
       └─ Run: python3 cli.py start
              │
              └─ Controller.startup()
                 ├─ Create network (mini-os-net)
                 ├─ Start core services
                 │  ├─ Logger
                 │  ├─ File
                 │  └─ Shell-base
                 └─ Update state.json
```

## State Management

### State File Structure (state.json)

```json
{
  "running_services": [
    "logger",
    "file",
    "shell-base"
  ],
  "users": [
    {
      "name": "alice",
      "container_id": "abc123def456",
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

## Network Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────┐
│                    mini-os-net                          │
│              (Docker Bridge Network)                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Container IP Assignment (via Docker IPAM):           │
│  - mini-os-logger:         172.20.0.2                 │
│  - mini-os-file:           172.20.0.3                 │
│  - mini-os-shell-base:     172.20.0.4                 │
│  - mini-os-user-alice:     172.20.0.5                 │
│  - mini-os-user-bob:       172.20.0.6                 │
│  - ...                                                 │
│                                                         │
│  DNS Resolution:                                        │
│  - Container name → IP (internal Docker DNS)           │
│  - Example: ping mini-os-logger (resolves to 172.20.0.2) │
│                                                         │
│  Routing:                                               │
│  - Host ←→ Container via bridge gateway               │
│  - Container ←→ Container via bridge (direct)         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Volume Management

### Volume Layout

```
Host Filesystem                          Container Filesystem
─────────────────────────────────────────────────────────────

/var/mini-os/
├── logs/              ◄───────────────► /logs (mini-os-logger)
│   ├── controller.log                  /logs (mini-os-user-*)
│   └── system.log

├── data/
│   ├── volumes/       ◄───────────────► /data (mini-os-file)
│   │   └── shared.txt    ro access      /data (mini-os-user-*)
│   │
│   └── users/
│       ├── alice/     ◄───────────────► /home/alice (mini-os-user-alice)
│       ├── bob/       ◄───────────────► /home/bob (mini-os-user-bob)
│       └── charlie/   ◄───────────────► /home/charlie (mini-os-user-charlie)

controller/
└── state.json         (Tracks system state)
```

## Module Dependencies

```
cli.py
   │
   ├──► main.py (MiniOSController)
   │     │
   │     ├──► docker_manager.py (DockerManager)
   │     │     │
   │     │     └──► docker (library)
   │     │
   │     ├──► utils.py
   │     │     └──► (standard library functions)
   │     │
   │     └──► json, os, logging
   │
   └──► subprocess (for docker exec)
```

## Resource Allocation

### Per-Container Limits

```
Default Configuration:
┌──────────────────────────────────┐
│     Container Resource Limits     │
├──────────────────────────────────┤
│ CPU Quota:        0.5 cores       │
│ CPU Period:       100ms           │
│ Memory Limit:     256MB           │
│ Memory Swap:      0 (disabled)    │
│ PID Limit:        Max OS default  │
│ I/O Weight:       Default (1024)  │
└──────────────────────────────────┘

Custom per-User:
$ python3 cli.py user create dev \
  --cpu 1.0 \
  --memory 512m
```

### System Resource Requirements

```
Baseline (core services only):
├── Logger:        ~30MB RAM, 0% CPU (idle)
├── File:          ~25MB RAM, 0% CPU (idle)
├── Shell-base:    ~20MB RAM, 0% CPU (idle)
└── Total:         ~75MB RAM

Per User Container:
├── Memory:        20-50MB baseline + workload
├── CPU:           0 (idle) to 0.5 (at limit)
└── Disk:          Minimal (unless writes to /home)

Scaling Example (10 users):
├── Core services: ~100MB
├── 10 Users:      ~200-500MB
└── Total:         ~300-600MB RAM used
```

## Communication Patterns

### Service-to-Service

```
mini-os-user-alice needs shared data
              │
              ▼
        Resolves "mini-os-file"
        (Docker internal DNS)
              │
              ▼
    Connects to 172.20.0.3:PORT
              │
              ▼
    mini-os-file responds
    (Access /data volume)
```

### Logging Flow

```
Container stdout/stderr
              │
              ▼
    Docker collects logs
              │
              ▼
    Stored in: /var/lib/docker/containers/<id>/<id>-json.log
              │
              ▼
    Accessible via: docker logs <container>
              ▼
    CLI: python3 cli.py logs <container>
```

## Security Model

### Isolation Levels

```
Process Level:
└─ Each user container = separate PID namespace

Network Level:
└─ Bridge network with container IP isolation

Storage Level:
└─ Each user has separate volume mount point
└─ /data volume mounted read-only for users

User Level:
└─ minios user inside container
└─ No privilege escalation to host

Resource Level:
└─ CPU and Memory limits enforced
└─ No access to other container resources
```

## Scaling Considerations

### Horizontal Scaling (Adding Users)

```
N users = N containers
│
├─ 1 user:   ~50MB overhead
├─ 5 users:  ~250MB overhead
├─ 10 users: ~500MB overhead
├─ 20 users: ~1GB overhead
└─ 50 users: ~2.5GB overhead
   (approximate, depends on workload)
```

### Performance Characteristics

```
Operation               Time        Notes
──────────────────────────────────────────
Create user            1-2 sec     Network, I/O dependent
Delete user            <1 sec      Container removal
Start system           30-60 sec   Building images, starting services
Stop system            <5 sec      Graceful shutdown
User login             <1 sec      Attach to existing container
Command exec           <100ms      In-process
```

## Error Handling Flow

```
User Command
     │
     ▼
CLI Validation
     │
  ┌──┴──┐
  │     │
  ✓     ✗ ──► Error message, exit
  │
  ▼
Controller Operation
     │
  ┌──┴──┐
  │     │
  ✓     ✗ ──► Logging, cleanup, error message
  │
  ▼
Docker Operation
     │
  ┌──┴──┐
  │     │
  ✓     ✗ ──► Exception handling, rollback attempt
  │
  ▼
Success / Failure
```

## Deployment Architecture

```
Host Machine (Ubuntu 20.04+)
│
├─ Docker Engine
│  └─ Docker Daemon
│
├─ /var/mini-os/
│  ├─ logs/            (mounted to containers)
│  ├─ data/volumes/    (mounted to containers)
│  └─ data/users/      (mounted to user containers)
│
└─ Mini OS Project Directory
   ├─ controller/      (Python code)
   ├─ services/        (Dockerfiles)
   ├─ scripts/         (Automation)
   └─ configs/         (Configuration)

Running Containers (in Docker):
├─ mini-os-logger (service)
├─ mini-os-file (service)
├─ mini-os-shell-base (service)
└─ mini-os-user-* (user sessions)
```

## Development Workflow

```
Developer
    │
    ├─► Modify code (Python, Dockerfile)
    │
    ├─► Rebuild images
    │   └─ docker build -t mini-os/<service> services/<service>
    │
    ├─► Stop system
    │   └─ ./scripts/stop.sh
    │
    ├─► Start system
    │   └─ ./scripts/start.sh
    │
    ├─► Test changes
    │   └─ python3 cli.py <command>
    │
    └─► Iterate
```

---

This architecture supports:
- ✓ Easy understanding of system design
- ✓ Modular component structure
- ✓ Clear isolation boundaries
- ✓ Scalable user addition
- ✓ Future enhancements
- ✓ Production deployment

For implementation details, see the code documentation in each module.
