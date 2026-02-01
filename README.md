# MSCS-630: Operating Systems Project

A custom Unix-like shell implementing core OS concepts including process management, scheduling, memory management, synchronization, and security.

## Overview

This project simulates fundamental operating system concepts through four integrated deliverables:

| Deliverable | Focus Area |
|-------------|------------|
| D1 | Basic shell, built-in commands, process management |
| D2 | Process scheduling (Round-Robin, Priority-Based) |
| D3 | Memory management (paging, FIFO/LRU), synchronization |
| D4 | Integration, piping, authentication, file permissions |

## Quick Start

```bash
# Run the fully integrated shell (recommended)
cd deliverable4
python3 integrated_shell.py

# Or run the interactive demo
python3 demo.py
```

**Default Login Credentials:**
- Admin: `admin` / `admin123`
- User: `user1` / `password1`

## Features

### Shell Commands
- **Built-ins**: `cd`, `pwd`, `ls`, `cat`, `mkdir`, `rm`, `touch`, `echo`, `clear`, `exit`
- **Process Control**: `jobs`, `fg`, `bg`, `kill`, background execution (`&`)
- **Piping**: `cmd1 | cmd2 | cmd3` (e.g., `cat file | grep error | sort`)

### Process Scheduling
- Round-Robin with configurable time quantum
- Priority-Based scheduling
- Performance metrics (waiting time, turnaround time, response time)

### Memory Management
- Paging system with configurable frame count
- FIFO and LRU page replacement algorithms
- Page fault tracking and visualization

### Synchronization
- Mutex and Semaphore primitives
- Producer-Consumer problem solution
- Dining Philosophers with deadlock prevention

### Security
- User authentication with password hashing
- Role-based access (admin, standard, guest)
- Unix-like file permissions (rwx, chmod, chown)

## Project Structure

```
├── deliverable1/    # Basic shell & process management
├── deliverable2/    # Process scheduling algorithms
├── deliverable3/    # Memory management & synchronization
└── deliverable4/    # Integration, piping, security
    └── integrated_shell.py  # Main entry point
```

## Requirements

- Python 3.6+
- No external dependencies

## Usage Examples

```bash
# In the integrated shell:
login admin admin123          # Authenticate
ls /home                      # List directory (with permissions)
cat file.txt | grep error     # Piping commands
scheduler rr 2                # Initialize Round-Robin scheduler
memory 4 fifo                 # Initialize memory manager with 4 frames
help                          # View all commands
```