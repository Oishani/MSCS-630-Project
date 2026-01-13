# Deliverable 1: Basic Shell Implementation and Process Management

## Overview

This deliverable implements a custom Unix-like shell in Python that demonstrates key operating system concepts including process management, job control, and signal handling.

## Features Implemented

### 1. Built-in Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `cd` | Change directory | `cd [directory]` |
| `pwd` | Print working directory | `pwd` |
| `exit` | Exit the shell | `exit [status]` |
| `echo` | Print text to terminal | `echo [-n] [text...]` |
| `clear` | Clear the terminal | `clear` |
| `ls` | List directory contents | `ls [-la] [directory]` |
| `cat` | Display file contents | `cat [file...]` |
| `mkdir` | Create directory | `mkdir [directory...]` |
| `rmdir` | Remove empty directory | `rmdir [directory...]` |
| `rm` | Remove file/directory | `rm [-rf] [file...]` |
| `touch` | Create file or update timestamp | `touch [file...]` |
| `kill` | Send signal to process | `kill [-signal] [pid...]` |

### 2. Job Control Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `jobs` | List background jobs | `jobs` |
| `fg` | Bring job to foreground | `fg [job_id]` |
| `bg` | Resume job in background | `bg [job_id]` |

### 3. Process Management

- **Foreground Execution**: Commands run in the foreground block the shell until completion
- **Background Execution**: Append `&` to run commands in the background
- **Job Tracking**: All processes are tracked with job ID, PID, status, and command

### 4. Signal Handling

- **Ctrl+C (SIGINT)**: Interrupts the foreground process
- **Ctrl+Z (SIGTSTP)**: Stops the foreground process
- **Ctrl+D (EOF)**: Exits the shell

## File Structure

```
deliverable1/
├── shell.py              # Main shell implementation
├── process_manager.py    # Process and job management
├── builtin_commands.py   # Built-in command implementations
├── demo.py              # Interactive demo script
└── README.md            # This file
```

## Dependencies

**Python 3.6+** is required. No external packages are needed - the shell uses only Python standard library modules:

- `os`, `sys`, `signal`, `subprocess`, `shlex`, `shutil`, `datetime`

### Installation

1. Verify Python is installed:
   ```bash
   python3 --version
   ```

2. If not installed, download from [python.org](https://www.python.org/downloads/) or use a package manager:
   ```bash
   # macOS (Homebrew)
   brew install python3
   
   # Ubuntu/Debian
   sudo apt install python3
   
   # Windows
   # Download installer from python.org
   ```

## How to Run

### Running the Shell

```bash
cd deliverable1
python3 shell.py
```

### Running the Interactive Demo

```bash
cd deliverable1
python3 demo.py
```

## Implementation Details

### Architecture

The shell is organized into three main modules:

1. **shell.py**: Main shell loop and command execution
   - Handles user input
   - Parses commands
   - Manages the read-eval-print loop
   - Sets up signal handlers

2. **process_manager.py**: Process and job management
   - `ProcessManager` class tracks all jobs
   - `Job` dataclass represents individual jobs
   - `JobStatus` enum for job states (Running, Stopped, Completed, Terminated)

3. **builtin_commands.py**: Built-in command implementations
   - Each command is a method in `BuiltinCommands` class
   - Comprehensive error handling for each command

### Process Management Design

```
                    ┌─────────────────┐
                    │     Shell       │
                    │   (shell.py)    │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐ ┌──────────┐ ┌──────────────┐
    │ BuiltinCommands │ │  Parse   │ │   Execute    │
    │                 │ │ Command  │ │  External    │
    └─────────────────┘ └──────────┘ └──────┬───────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ProcessManager │
                                    │               │
                                    │ - Job Table   │
                                    │ - Status      │
                                    │ - Signals     │
                                    └───────────────┘
```

### Job Control Flow

1. **Background Job Creation**:
   ```
   User Input: sleep 30 &
   → Parse: command="sleep 30", background=True
   → subprocess.Popen(start_new_session=True)
   → Add to job table
   → Return immediately to prompt
   ```

2. **Foreground Job with Ctrl+Z**:
   ```
   User Input: sleep 30
   → Execute in foreground (wait)
   → User presses Ctrl+Z
   → SIGTSTP sent to process
   → Process stopped
   → Job status = Stopped
   → Return to prompt
   ```

3. **Resuming with fg/bg**:
   ```
   fg 1 → Send SIGCONT → Wait for completion
   bg 1 → Send SIGCONT → Continue in background
   ```

## Error Handling

The shell implements comprehensive error handling:

| Error Type | Example | Response |
|------------|---------|----------|
| Command not found | `xyz` | `myshell: xyz: command not found` |
| File not found | `cat missing.txt` | `myshell: cat: missing.txt: No such file or directory` |
| Permission denied | `cat /etc/shadow` | `myshell: cat: /etc/shadow: Permission denied` |
| Is a directory | `cat somedir/` | `myshell: cat: somedir/: Is a directory` |
| Directory not empty | `rmdir nonempty/` | `myshell: rmdir: failed to remove 'nonempty/': Directory not empty` |
| No such job | `fg 99` | `myshell: fg: 99: no such job` |
| Invalid process | `kill 99999` | `myshell: kill: (99999) - No such process` |
| Parse error | `echo "unclosed` | `myshell: parse error: No closing quotation` |

## Usage Examples

### Basic File Operations

```bash
myshell> pwd
/home/user

myshell> mkdir projects
myshell> cd projects
myshell> touch readme.txt
myshell> ls
readme.txt

myshell> echo "Hello World"
Hello World

myshell> cat readme.txt
(empty file)

myshell> rm readme.txt
myshell> cd ..
myshell> rmdir projects
```

### Process Management

```bash
# Start a background job
myshell> sleep 60 &
[1] 12345

# List jobs
myshell> jobs
[1]+ 12345 Running    sleep 60 &

# Bring to foreground
myshell> fg 1
sleep 60
(process continues in foreground)

# Press Ctrl+Z to stop
^Z
[1]+ Stopped    sleep 60

# Resume in background
myshell> bg 1
[1]+ sleep 60 &

# Kill the process
myshell> kill 12345
```