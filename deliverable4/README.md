# Deliverable 4: Integration and Security Implementation

This deliverable integrates all components from previous deliverables into a cohesive shell with advanced features including piping and security mechanisms.

## Features

### 1. Command Piping
- Chain multiple commands using the `|` (pipe) symbol
- Output of one command becomes input to the next
- Supports multi-stage pipelines (e.g., `cat file | grep error | sort`)

**Supported Commands for Piping:**
- `cat`, `echo`, `grep`, `sort`, `head`, `tail`
- `wc`, `uniq`, `tr`, `cut`, `ls`, `pwd`

### 2. User Authentication
- **User Accounts**: Username/password authentication
- **Permission Levels**:
  - `admin`: Full system access
  - `standard`: Normal user operations
  - `guest`: Read-only access

**Default Users:**
| Username | Password   | Role     |
|----------|------------|----------|
| admin    | admin123   | admin    |
| user1    | password1  | standard |
| user2    | password2  | standard |
| guest    | guest      | guest    |

### 3. File Permissions
- Unix-like permission system (read, write, execute)
- Owner/Group/Others permission levels
- System file protection
- `chmod` and `chown` commands

**Permission Format:**
- Octal notation: `755`, `644`, `600`
- String notation: `rwxr-xr-x`

### 4. Integration
All components from previous deliverables are integrated:
- **Deliverable 1**: Basic shell, process management
- **Deliverable 2**: Round-Robin and Priority scheduling
- **Deliverable 3**: Memory management, synchronization

## Files

| File | Description |
|------|-------------|
| `authentication.py` | User authentication and session management |
| `permissions.py` | File permission handling and access control |
| `piping.py` | Command piping implementation |
| `integrated_shell.py` | Main shell integrating all components |
| `demo.py` | Interactive demonstration script |

## Usage

### Running the Integrated Shell
```bash
cd deliverable4
python3 integrated_shell.py
```

### Running the Demo
```bash
python3 demo.py
```

### Quick Start
1. Start the shell: `python3 integrated_shell.py`
2. Login: `login admin admin123`
3. Get help: `help`
4. Try piping: `echo "hello world" | grep "hello"`
5. Check permissions: `ls /home`
6. Exit: `exit`

## Command Reference

### Authentication Commands
```
login <username> <password>  - Login to the shell
logout                       - Logout from the shell
whoami                       - Show current user
users                        - List all users
passwd <old> <new>           - Change password
useradd <user> <pass> [role] - Add user (admin only)
userdel <user>               - Delete user (admin only)
```

### File Commands
```
ls [path]              - List directory contents
cat <file>             - Display file contents
chmod <mode> <file>    - Change file permissions
chown <owner> <file>   - Change file owner (admin only)
touch <file>           - Create a new file
write <file> <text>    - Write content to file
stat <file>            - Show file information
```

### Piping Examples
```
echo "hello" | grep "hello"           - Simple pipe
cat file.txt | grep error | sort      - Multi-stage pipe
cat file.txt | grep error | wc -l     - Count matching lines
ls | head -n 5                        - First 5 entries
cat log.txt | sort | uniq             - Sort and remove duplicates
```

### Scheduling Commands (from D2)
```
scheduler <rr|priority> [quantum]  - Initialize scheduler
schedule <name> <burst> [priority] - Schedule a process
sched_status                       - Show scheduler status
```

### Memory Commands (from D3)
```
memory <frames> [fifo|lru]  - Initialize memory manager
alloc <pid> <page>          - Allocate a page
free <pid>                  - Free process pages
mem_status                  - Show memory status
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Integrated Shell                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Piping    │  │    Auth     │  │    Permissions      │  │
│  │   Module    │  │   Module    │  │      Module         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                  Previous Deliverables                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ D1: Shell   │  │D2: Scheduler│  │ D3: Memory/Sync     │  │
│  │  & Process  │  │   (RR/Pri)  │  │  (FIFO/LRU)         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Security Features

### Authentication Security
- Passwords are hashed using SHA-256
- Session-based authentication
- Login attempts are logged

### Permission Security
- System files protected from non-admin users
- Owner-based access control
- Principle of least privilege

## Demo Walkthrough

The demo script (`demo.py`) provides interactive demonstrations:

1. **Piping Demo**: Shows multi-stage command piping
2. **Authentication Demo**: Login/logout, user management
3. **Permissions Demo**: File access control demonstration
4. **Integration Demo**: Shows D2/D3 components working together
5. **Combined Scenario**: Real-world usage example

## Dependencies

- Python 3.6+
- No external packages required

## Testing

Run the demo to verify all features:
```bash
python3 demo.py
# Select option 7 to run all demos
```

Or test individual components:
```python
from authentication import create_auth_manager
from permissions import create_permission_manager
from piping import create_pipe_executor

# Test authentication
auth = create_auth_manager()
session = auth.login("admin", "admin123")
print(f"Logged in: {session.user.username}")

# Test piping
pipe = create_pipe_executor()
result = pipe.execute_pipeline("echo 'test' | grep 'test'")
print(f"Pipe result: {result.output}")
```