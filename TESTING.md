# Mini OS - Testing Guide

Comprehensive test suite to validate Mini OS functionality.

## Pre-Test Requirements

- Mini OS installed and ready to start
- Docker installed and working
- At least 5GB free disk space
- At least 2GB free RAM

## Test Phases

### Phase 1: System Startup and Initialization

#### Test 1.1: Start Mini OS

```bash
./scripts/start.sh
```

**Expected Results:**
- ✓ All Docker images built successfully
- ✓ mini-os-net network created
- ✓ Core services (logger, file, shell) started
- ✓ System shows "Startup Complete"

**Validation:**
```bash
python3 controller/cli.py status
```
Should show: `Initialized: true`

#### Test 1.2: Verify Core Services Running

```bash
docker ps --filter "label=mini-os=true"
```

**Expected Results:**
- ✓ 3 containers running:
  - mini-os-logger
  - mini-os-file
  - mini-os-shell-base

#### Test 1.3: Verify Network Creation

```bash
docker network ls | grep mini-os-net
```

**Expected Results:**
- ✓ mini-os-net network exists with driver "bridge"

#### Test 1.4: Check State File

```bash
cat controller/state.json
```

**Expected Results:**
- ✓ State file exists and is valid JSON
- ✓ Contains running_services array
- ✓ Contains users array (empty initially)
- ✓ initialized: true

---

### Phase 2: User Management

#### Test 2.1: Create Single User

```bash
python3 controller/cli.py user create alice
```

**Expected Results:**
- ✓ User "alice" created successfully
- ✓ Container "mini-os-user-alice" running
- ✓ Home directory created at /var/mini-os/data/users/alice

**Validation:**
```bash
python3 controller/cli.py user list
```
Should show "alice" in active users.

#### Test 2.2: Create Multiple Users

```bash
python3 controller/cli.py user create bob
python3 controller/cli.py user create charlie
python3 controller/cli.py user list
```

**Expected Results:**
- ✓ All 3 users created successfully
- ✓ All containers running
- ✓ State file updated with all users

#### Test 2.3: User Isolation - Filesystem

```bash
# As alice
python3 controller/cli.py user enter alice
$ echo "alice_data" > /home/alice/secret.txt
$ exit

# As bob
python3 controller/cli.py user enter bob
$ ls /home/bob/
$ ls /home/alice/  # Should not exist
$ exit
```

**Expected Results:**
- ✓ alice's file visible only to alice
- ✓ bob cannot access alice's home directory

#### Test 2.4: User Isolation - Processes

```bash
# Terminal 1: As alice
python3 controller/cli.py user enter alice
$ sleep 1000 &
$ jobs
$ exit

# Terminal 2: Check processes
docker exec mini-os-user-bob ps aux
```

**Expected Results:**
- ✓ Processes isolated per container
- ✓ bob cannot see alice's processes

#### Test 2.5: Custom Resource Limits

```bash
python3 controller/cli.py user create developer --cpu 1.0 --memory 512m
python3 controller/cli.py user enter developer
$ # Inside container
$ cat /proc/meminfo | grep MemTotal
$ exit
```

**Expected Results:**
- ✓ User created with custom limits
- ✓ Container respects specified resources

---

### Phase 3: Shared Data Access

#### Test 3.1: File Service Access

```bash
# Terminal 1: Admin shell
python3 controller/cli.py launch-shell
$ echo "shared_data_test" > /data/test.txt
$ exit

# Terminal 2: User shell
python3 controller/cli.py user enter alice
$ cat /data/test.txt
$ exit
```

**Expected Results:**
- ✓ File in /data readable by users
- ✓ Shared data accessible to all users

#### Test 3.2: Shared Data Read-Only

```bash
python3 controller/cli.py user enter alice
$ echo "write_attempt" > /data/writetest.txt
# Should fail or be read-only
$ exit
```

**Expected Results:**
- ✓ /data is read-only for users
- ✓ No modifications possible from user containers

---

### Phase 4: Networking

#### Test 4.1: Service Discovery

```bash
python3 controller/cli.py user enter alice
$ ping mini-os-logger
# Should respond
$ exit
```

**Expected Results:**
- ✓ Container names resolve as hostnames
- ✓ Network connectivity between containers

#### Test 4.2: Container Communication

```bash
python3 controller/cli.py launch-shell
$ docker exec mini-os-user-alice ping -c 3 mini-os-logger
$ exit
```

**Expected Results:**
- ✓ Ping successful
- ✓ Network latency < 2ms

---

### Phase 5: Logging

#### Test 5.1: Controller Logs

```bash
tail -n 20 /var/mini-os/logs/controller.log
```

**Expected Results:**
- ✓ Log file exists and contains entries
- ✓ Startup events logged
- ✓ User creation events logged

#### Test 5.2: Container Logs

```bash
docker logs mini-os-logger | head -20
docker logs mini-os-file | head -20
docker logs mini-os-shell-base | head -20
```

**Expected Results:**
- ✓ All containers have logs
- ✓ Logs contain service startup messages

#### Test 5.3: System Log Aggregation

```bash
cat /var/mini-os/logs/system.log
```

**Expected Results:**
- ✓ System log file exists
- ✓ Contains timestamp entries
- ✓ Updates periodically

---

### Phase 6: Container Management

#### Test 6.1: Stop Container

```bash
docker ps | grep mini-os-user-alice
python3 controller/cli.py kill mini-os-user-alice
docker ps | grep mini-os-user-alice  # Should not appear
```

**Expected Results:**
- ✓ Container stops successfully
- ✓ Not in running containers list

#### Test 6.2: Status Updates

```bash
python3 controller/cli.py status
```

**Expected Results:**
- ✓ Stopped containers no longer counted as running
- ✓ System status reflects current state

---

### Phase 7: Deletion and Cleanup

#### Test 7.1: Delete User

```bash
python3 controller/cli.py user delete bob
python3 controller/cli.py user list
```

**Expected Results:**
- ✓ User "bob" removed from list
- ✓ Container "mini-os-user-bob" removed
- ✓ Home directory cleanup occurs

#### Test 7.2: Delete Multiple Users

```bash
python3 controller/cli.py user delete alice
python3 controller/cli.py user delete charlie
python3 controller/cli.py user list
```

**Expected Results:**
- ✓ All users deleted
- ✓ Only core services remain

---

### Phase 8: System Shutdown

#### Test 8.1: Clean Shutdown

```bash
./scripts/stop.sh
```

**Expected Results:**
- ✓ All containers stopped gracefully
- ✓ "Shutdown Complete" message shown

#### Test 8.2: Verify Cleanup

```bash
docker ps --filter "label=mini-os=true"
```

**Expected Results:**
- ✓ No running mini-os containers
- ✓ Network still exists (for restart capability)

---

### Phase 9: System Restart

#### Test 9.1: Restart System

```bash
./scripts/start.sh
```

**Expected Results:**
- ✓ System starts successfully
- ✓ Core services running again
- ✓ Previous state recoverable

#### Test 9.2: State Persistence

```bash
python3 controller/cli.py status
```

**Expected Results:**
- ✓ System reinitialized
- ✓ Users from previous session not auto-restored (as expected)

---

### Phase 10: Full System Reset

#### Test 10.1: Reset with Confirmation

```bash
./scripts/reset.sh
# Type "yes" at prompt
```

**Expected Results:**
- ✓ All containers removed
- ✓ Network removed
- ✓ State file reset

#### Test 10.2: Fresh Start After Reset

```bash
./scripts/start.sh
```

**Expected Results:**
- ✓ System starts from clean state
- ✓ All services initialized
- ✓ No orphaned containers

---

## Performance Tests

### Test P1: Memory Usage

```bash
# Start system
./scripts/start.sh

# Check memory usage
docker stats --no-stream

# Expected: 
# - Each container: 20-50MB
# - Total system overhead: < 500MB
```

### Test P2: CPU Usage

```bash
# In background, create load
python3 controller/cli.py user create loadtest
docker exec mini-os-user-loadtest /bin/bash -c "dd if=/dev/zero bs=1M count=100 | md5sum"

# Monitor in another terminal
docker stats mini-os-user-loadtest
```

### Test P3: Disk I/O

```bash
# Write test
python3 controller/cli.py user enter alice
$ dd if=/dev/zero of=/home/alice/testfile bs=1M count=100
$ rm /home/alice/testfile
$ exit
```

**Expected Results:**
- ✓ I/O completes without errors
- ✓ Disk usage reflects file sizes

---

## Error Handling Tests

### Test E1: Missing Image

```bash
# Try to create user with non-existent image
docker image rm mini-os/shell:latest
python3 controller/cli.py user create errortest
```

**Expected Results:**
- ✓ Appropriate error message shown
- ✓ System remains stable

### Test E2: Network Failure

```bash
# Simulate by removing network
docker network disconnect mini-os-net mini-os-logger
python3 controller/cli.py status
```

**Expected Results:**
- ✓ Status command handles gracefully
- ✓ Error message informative

---

## Automated Test Script

Save as `test_all.sh`:

```bash
#!/bin/bash

set -e

PASSED=0
FAILED=0

test_case() {
    local name=$1
    local cmd=$2
    echo -n "Testing: $name ... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✓ PASS"
        ((PASSED++))
    else
        echo "✗ FAIL"
        ((FAILED++))
    fi
}

echo "Mini OS Test Suite"
echo "=================="
echo ""

# Basic tests
test_case "System startup" "./scripts/start.sh"
test_case "Status check" "python3 controller/cli.py status"
test_case "Create user" "python3 controller/cli.py user create testuser"
test_case "List users" "python3 controller/cli.py user list | grep testuser"
test_case "Delete user" "python3 controller/cli.py user delete testuser"
test_case "System shutdown" "./scripts/stop.sh"

echo ""
echo "=================="
echo "Tests Passed: $PASSED"
echo "Tests Failed: $FAILED"
echo "=================="

if [ $FAILED -eq 0 ]; then
    exit 0
else
    exit 1
fi
```

Run with:
```bash
chmod +x test_all.sh
./test_all.sh
```

---

## Test Report Template

Use this to document test results:

```markdown
# Mini OS Test Report
Date: [DATE]
Tester: [NAME]
System: [OS/Hardware]

## Summary
- Total Tests: XX
- Passed: XX
- Failed: XX
- Success Rate: XX%

## Details

### Phase 1: System Startup
- [ ] Test 1.1 PASS/FAIL
- [ ] Test 1.2 PASS/FAIL
- [ ] Test 1.3 PASS/FAIL
- [ ] Test 1.4 PASS/FAIL

### Phase 2: User Management
- [ ] Test 2.1 PASS/FAIL
- [ ] Test 2.2 PASS/FAIL
- [ ] Test 2.3 PASS/FAIL
- [ ] Test 2.4 PASS/FAIL
- [ ] Test 2.5 PASS/FAIL

[... continue for all phases ...]

## Issues Found
1. [Description of issue]
   - Severity: Critical/High/Medium/Low
   - Steps to reproduce: [Steps]
   - Expected: [Expected]
   - Actual: [Actual]

## Conclusion
System is [ready/not ready] for production.
```

---

## Continuous Testing

For automated testing in production:

1. **Setup cron job** for daily startup/shutdown cycles
2. **Monitor logs** for errors
3. **Track resource usage** over time
4. **Test user lifecycle** regularly

---

This test suite ensures Mini OS functions correctly across all components and use cases.
