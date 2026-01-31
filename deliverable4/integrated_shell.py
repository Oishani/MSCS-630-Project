#!/usr/bin/env python3
"""
Integrated Shell for Deliverable 4

This module integrates all components from previous deliverables:
- Deliverable 1: Basic shell with built-in commands and process management
- Deliverable 2: Process scheduling (Round-Robin and Priority-Based)
- Deliverable 3: Memory management and process synchronization
- Deliverable 4: Piping, authentication, and file permissions
"""

import os
import sys
import signal
import subprocess
import shlex
import time
from typing import Optional, List, Dict, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deliverable1'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deliverable2'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deliverable3'))

# Import from Deliverable 4
from authentication import AuthenticationManager, User, UserRole, create_auth_manager
from permissions import FilePermissionManager, Permission, create_permission_manager
from piping import PipeExecutor, create_pipe_executor

# Try to import from previous deliverables
try:
    from process_manager import ProcessManager, JobStatus
    HAS_PROCESS_MANAGER = True
except ImportError:
    HAS_PROCESS_MANAGER = False

try:
    from scheduler import RoundRobinScheduler, PriorityScheduler, SchedulerType
    from process import Process, ProcessState
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False

try:
    from memory_manager import MemoryManager, PageReplacementAlgorithm, create_memory_manager
    from synchronization import Mutex, Semaphore, ProducerConsumer, DiningPhilosophers
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False


class IntegratedShell:
    """
    Fully integrated shell with all features from Deliverables 1-4.
    
    Features:
    - User authentication
    - File permissions
    - Command piping
    - Process management
    - Process scheduling
    - Memory management
    - Process synchronization
    """
    
    def __init__(self, callback: Callable = None):
        """Initialize the integrated shell."""
        self.callback = callback or print
        self.running = False
        self.history: List[str] = []
        
        # Deliverable 4 components
        self.auth_manager = create_auth_manager(callback=self._quiet_callback)
        self.perm_manager = create_permission_manager(callback=self._quiet_callback)
        self.pipe_executor = create_pipe_executor(callback=self._quiet_callback)
        
        # Deliverable 1 components
        if HAS_PROCESS_MANAGER:
            self.process_manager = ProcessManager()
        else:
            self.process_manager = None
        
        # Deliverable 2 components
        self.scheduler = None
        self.scheduler_type = None
        
        # Deliverable 3 components
        self.memory_manager = None
        
        # Built-in commands
        self.builtin_commands = {
            # Authentication commands
            'login': self._cmd_login,
            'logout': self._cmd_logout,
            'whoami': self._cmd_whoami,
            'users': self._cmd_users,
            'passwd': self._cmd_passwd,
            'useradd': self._cmd_useradd,
            'userdel': self._cmd_userdel,
            
            # File permission commands
            'ls': self._cmd_ls,
            'cat': self._cmd_cat,
            'chmod': self._cmd_chmod,
            'chown': self._cmd_chown,
            'touch': self._cmd_touch,
            'write': self._cmd_write,
            'stat': self._cmd_stat,
            
            # Basic commands
            'cd': self._cmd_cd,
            'pwd': self._cmd_pwd,
            'echo': self._cmd_echo,
            'clear': self._cmd_clear,
            'exit': self._cmd_exit,
            'help': self._cmd_help,
            'history': self._cmd_history,
            
            # Scheduling commands (Deliverable 2)
            'scheduler': self._cmd_scheduler,
            'schedule': self._cmd_schedule,
            'sched_status': self._cmd_sched_status,
            
            # Memory commands (Deliverable 3)
            'memory': self._cmd_memory,
            'alloc': self._cmd_alloc,
            'free': self._cmd_free,
            'mem_status': self._cmd_mem_status,
            
            # Process commands (Deliverable 1)
            'jobs': self._cmd_jobs,
            'fg': self._cmd_fg,
            'bg': self._cmd_bg,
            'kill': self._cmd_kill,
        }
    
    def _quiet_callback(self, msg: str):
        """Callback that suppresses output (for internal operations)."""
        pass
    
    def _require_auth(self) -> bool:
        """Check if user is authenticated."""
        if not self.auth_manager.is_authenticated():
            self.callback("Error: Please login first (use 'login' command)")
            return False
        return True
    
    def _require_admin(self) -> bool:
        """Check if user has admin privileges."""
        if not self._require_auth():
            return False
        user = self.auth_manager.get_current_user()
        if user.role != UserRole.ADMIN:
            self.callback("Error: Admin privileges required")
            return False
        return True
    
    def get_prompt(self) -> str:
        """Generate the shell prompt."""
        user = self.auth_manager.get_current_user()
        if user:
            role_indicator = '#' if user.role == UserRole.ADMIN else '$'
            try:
                cwd = os.getcwd()
                home = os.path.expanduser("~")
                if cwd.startswith(home):
                    cwd = "~" + cwd[len(home):]
            except OSError:
                cwd = "?"
            return f"\033[1;32m{user.username}\033[0m@\033[1;34mshell\033[0m:{cwd}{role_indicator} "
        else:
            return "login> "
    
    def parse_command(self, command_line: str) -> Tuple[List[str], bool]:
        """Parse command line into arguments and background flag."""
        command_line = command_line.strip()
        
        is_background = False
        if command_line.endswith('&'):
            is_background = True
            command_line = command_line[:-1].strip()
        
        try:
            args = shlex.split(command_line)
        except ValueError as e:
            self.callback(f"Parse error: {e}")
            return [], False
        
        return args, is_background
    
    def execute_command(self, command_line: str) -> bool:
        """Execute a command line."""
        command_line = command_line.strip()
        
        if not command_line:
            return True
        
        # Add to history
        self.history.append(command_line)
        
        # Handle login specially (doesn't require auth)
        if command_line.startswith('login') or command_line == 'exit':
            args, _ = self.parse_command(command_line)
            if args:
                cmd = args[0]
                if cmd in self.builtin_commands:
                    return self.builtin_commands[cmd](args)
        
        # Most commands require authentication
        if not self.auth_manager.is_authenticated():
            if command_line not in ['exit', 'help']:
                self.callback("Please login first. Use: login <username> <password>")
                self.callback("Default users: admin/admin123, user1/password1, user2/password2, guest/guest")
                return False
        
        # Check for piped commands
        if self.pipe_executor.is_piped_command(command_line):
            return self._execute_piped(command_line)
        
        # Parse and execute single command
        args, is_background = self.parse_command(command_line)
        
        if not args:
            return True
        
        cmd = args[0]
        
        # Check if it's a builtin command
        if cmd in self.builtin_commands:
            return self.builtin_commands[cmd](args)
        
        # Try to execute as external command
        return self._execute_external(args, is_background)
    
    def _execute_piped(self, command_line: str) -> bool:
        """Execute a piped command."""
        result = self.pipe_executor.execute_pipeline(command_line)
        
        if result.success:
            if result.output:
                self.callback(result.output.rstrip())
            return True
        else:
            if result.error:
                self.callback(result.error.rstrip())
            return False
    
    def _execute_external(self, args: List[str], is_background: bool) -> bool:
        """Execute an external command."""
        try:
            if is_background:
                process = subprocess.Popen(
                    args,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                self.callback(f"[{process.pid}] Started in background")
                return True
            else:
                process = subprocess.Popen(
                    args,
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
                process.wait()
                return process.returncode == 0
                
        except FileNotFoundError:
            self.callback(f"{args[0]}: command not found")
            return False
        except PermissionError:
            self.callback(f"{args[0]}: permission denied")
            return False
        except Exception as e:
            self.callback(f"{args[0]}: {e}")
            return False
    
    # ==================== Authentication Commands ====================
    
    def _cmd_login(self, args: List[str]) -> bool:
        """Login to the shell."""
        if len(args) < 3:
            self.callback("Usage: login <username> <password>")
            return False
        
        username = args[1]
        password = args[2]
        
        session = self.auth_manager.login(username, password)
        if session:
            self.callback(f"Welcome, {username}! (Role: {session.user.role.value})")
            return True
        else:
            self.callback("Login failed. Invalid username or password.")
            return False
    
    def _cmd_logout(self, args: List[str]) -> bool:
        """Logout from the shell."""
        if self.auth_manager.logout():
            self.callback("Logged out successfully.")
            return True
        else:
            self.callback("Not logged in.")
            return False
    
    def _cmd_whoami(self, args: List[str]) -> bool:
        """Show current user."""
        if not self._require_auth():
            return False
        
        user = self.auth_manager.get_current_user()
        self.callback(user.username)
        return True
    
    def _cmd_users(self, args: List[str]) -> bool:
        """List all users."""
        users = self.auth_manager.list_users()
        
        self.callback(f"\n{'Username':<12} {'Role':<10} {'Home Directory':<20}")
        self.callback("-" * 45)
        
        for u in users:
            home = u.get('home', 'N/A')
            self.callback(f"{u['username']:<12} {u['role']:<10} {home:<20}")
        
        return True
    
    def _cmd_passwd(self, args: List[str]) -> bool:
        """Change password."""
        if not self._require_auth():
            return False
        
        if len(args) < 3:
            self.callback("Usage: passwd <old_password> <new_password>")
            return False
        
        user = self.auth_manager.get_current_user()
        if self.auth_manager.change_password(user.username, args[1], args[2]):
            self.callback("Password changed successfully.")
            return True
        else:
            self.callback("Failed to change password.")
            return False
    
    def _cmd_useradd(self, args: List[str]) -> bool:
        """Add a new user (admin only)."""
        if not self._require_admin():
            return False
        
        if len(args) < 3:
            self.callback("Usage: useradd <username> <password> [role]")
            self.callback("Roles: admin, standard, guest")
            return False
        
        username = args[1]
        password = args[2]
        role_str = args[3] if len(args) > 3 else "standard"
        
        try:
            role = UserRole(role_str)
        except ValueError:
            self.callback(f"Invalid role: {role_str}")
            return False
        
        if self.auth_manager.register_user(username, password, role):
            self.callback(f"User '{username}' created with role '{role.value}'")
            return True
        else:
            self.callback(f"Failed to create user '{username}'")
            return False
    
    def _cmd_userdel(self, args: List[str]) -> bool:
        """Delete a user (admin only)."""
        if not self._require_admin():
            return False
        
        if len(args) < 2:
            self.callback("Usage: userdel <username>")
            return False
        
        if self.auth_manager.delete_user(args[1]):
            self.callback(f"User '{args[1]}' deleted.")
            return True
        else:
            self.callback(f"Failed to delete user '{args[1]}'")
            return False
    
    # ==================== File Permission Commands ====================
    
    def _cmd_ls(self, args: List[str]) -> bool:
        """List directory contents with permissions."""
        if not self._require_auth():
            return False
        
        user = self.auth_manager.get_current_user()
        path = args[1] if len(args) > 1 else '/home'
        
        # Check if it's a simulated path
        if path.startswith('/') and not path.startswith('/Users') and not path.startswith('/home/'):
            contents = self.perm_manager.list_directory(user, path)
            if contents:
                self.callback(f"\nDirectory: {path}")
                self.callback(f"{'Permissions':<12} {'Owner':<10} {'Group':<10} {'Size':<8} {'Name'}")
                self.callback("-" * 55)
                for f in contents:
                    self.callback(f"{f.get_type_char()}{f.permissions} {f.owner:<10} {f.group:<10} {f.size:<8} {f.name}")
                return True
            return False
        else:
            # Use real filesystem
            try:
                entries = os.listdir(path if len(args) > 1 else '.')
                for entry in sorted(entries):
                    self.callback(entry)
                return True
            except Exception as e:
                self.callback(f"ls: {e}")
                return False
    
    def _cmd_cat(self, args: List[str]) -> bool:
        """Display file contents."""
        if not self._require_auth():
            return False
        
        if len(args) < 2:
            self.callback("Usage: cat <filename>")
            return False
        
        user = self.auth_manager.get_current_user()
        path = args[1]
        
        # Check if it's a simulated path
        if path.startswith('/') and not path.startswith('/Users'):
            content = self.perm_manager.read_file(user, path)
            if content is not None:
                self.callback(content)
                return True
            return False
        else:
            # Use real filesystem
            try:
                with open(path, 'r') as f:
                    self.callback(f.read())
                return True
            except Exception as e:
                self.callback(f"cat: {e}")
                return False
    
    def _cmd_chmod(self, args: List[str]) -> bool:
        """Change file permissions."""
        if not self._require_auth():
            return False
        
        if len(args) < 3:
            self.callback("Usage: chmod <mode> <filename>")
            self.callback("Example: chmod 755 /home/user1/script.sh")
            return False
        
        user = self.auth_manager.get_current_user()
        mode = args[1]
        path = args[2]
        
        if self.perm_manager.chmod(user, path, mode):
            self.callback(f"Permissions changed to {mode}")
            return True
        return False
    
    def _cmd_chown(self, args: List[str]) -> bool:
        """Change file owner (admin only)."""
        if not self._require_admin():
            return False
        
        if len(args) < 3:
            self.callback("Usage: chown <owner> <filename>")
            return False
        
        user = self.auth_manager.get_current_user()
        if self.perm_manager.chown(user, args[2], args[1]):
            self.callback(f"Owner changed to {args[1]}")
            return True
        return False
    
    def _cmd_touch(self, args: List[str]) -> bool:
        """Create a new file."""
        if not self._require_auth():
            return False
        
        if len(args) < 2:
            self.callback("Usage: touch <filename>")
            return False
        
        user = self.auth_manager.get_current_user()
        path = args[1]
        
        if self.perm_manager.write_file(user, path, ""):
            self.callback(f"Created: {path}")
            return True
        return False
    
    def _cmd_write(self, args: List[str]) -> bool:
        """Write content to a file."""
        if not self._require_auth():
            return False
        
        if len(args) < 3:
            self.callback("Usage: write <filename> <content>")
            return False
        
        user = self.auth_manager.get_current_user()
        path = args[1]
        content = ' '.join(args[2:])
        
        if self.perm_manager.write_file(user, path, content):
            self.callback(f"Written to: {path}")
            return True
        return False
    
    def _cmd_stat(self, args: List[str]) -> bool:
        """Show file information."""
        if not self._require_auth():
            return False
        
        if len(args) < 2:
            self.callback("Usage: stat <filename>")
            return False
        
        path = args[1]
        info = self.perm_manager.get_file_info(path)
        
        if info:
            self.callback(f"\n  File: {info['path']}")
            self.callback(f"  Type: {info['type']}")
            self.callback(f"  Size: {info['size']}")
            self.callback(f" Owner: {info['owner']}")
            self.callback(f" Group: {info['group']}")
            self.callback(f"Access: {info['permissions']} ({info['octal']})")
            self.callback(f"System: {'Yes' if info['system'] else 'No'}")
            self.callback(f"Created: {info['created']}")
            self.callback(f"Modified: {info['modified']}")
            return True
        else:
            self.callback(f"stat: cannot stat '{path}': No such file")
            return False
    
    # ==================== Basic Commands ====================
    
    def _cmd_cd(self, args: List[str]) -> bool:
        """Change directory."""
        if not self._require_auth():
            return False
        
        path = args[1] if len(args) > 1 else os.path.expanduser("~")
        
        try:
            os.chdir(path)
            return True
        except Exception as e:
            self.callback(f"cd: {e}")
            return False
    
    def _cmd_pwd(self, args: List[str]) -> bool:
        """Print working directory."""
        self.callback(os.getcwd())
        return True
    
    def _cmd_echo(self, args: List[str]) -> bool:
        """Echo arguments."""
        self.callback(' '.join(args[1:]))
        return True
    
    def _cmd_clear(self, args: List[str]) -> bool:
        """Clear the screen."""
        os.system('clear' if os.name != 'nt' else 'cls')
        return True
    
    def _cmd_exit(self, args: List[str]) -> bool:
        """Exit the shell."""
        self.running = False
        self.callback("Goodbye!")
        return True
    
    def _cmd_help(self, args: List[str]) -> bool:
        """Show help information."""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║              Integrated Shell - Command Reference             ║
╠══════════════════════════════════════════════════════════════╣
║ AUTHENTICATION:                                               ║
║   login <user> <pass>  - Login to the shell                  ║
║   logout               - Logout from the shell               ║
║   whoami               - Show current user                   ║
║   users                - List all users                      ║
║   passwd <old> <new>   - Change password                     ║
║   useradd <u> <p> [r]  - Add user (admin only)              ║
║   userdel <user>       - Delete user (admin only)           ║
╠══════════════════════════════════════════════════════════════╣
║ FILE PERMISSIONS:                                             ║
║   ls [path]            - List directory contents             ║
║   cat <file>           - Display file contents               ║
║   chmod <mode> <file>  - Change file permissions             ║
║   chown <owner> <file> - Change file owner (admin only)      ║
║   touch <file>         - Create a new file                   ║
║   write <file> <text>  - Write content to file               ║
║   stat <file>          - Show file information               ║
╠══════════════════════════════════════════════════════════════╣
║ PIPING:                                                       ║
║   cmd1 | cmd2 | cmd3   - Chain commands with pipes           ║
║   Example: cat file | grep error | sort                      ║
╠══════════════════════════════════════════════════════════════╣
║ PROCESS MANAGEMENT:                                           ║
║   jobs                 - List background jobs                ║
║   fg [job_id]          - Bring job to foreground             ║
║   bg [job_id]          - Continue job in background          ║
║   kill <pid>           - Kill a process                      ║
╠══════════════════════════════════════════════════════════════╣
║ SCHEDULING (Deliverable 2):                                   ║
║   scheduler <type>     - Set scheduler (rr/priority)         ║
║   schedule <name> <bt> - Schedule a process                  ║
║   sched_status         - Show scheduler status               ║
╠══════════════════════════════════════════════════════════════╣
║ MEMORY (Deliverable 3):                                       ║
║   memory <frames> [algo] - Initialize memory manager         ║
║   alloc <pid> <page>     - Allocate a page                   ║
║   free <pid>             - Free process pages                ║
║   mem_status             - Show memory status                ║
╠══════════════════════════════════════════════════════════════╣
║ BASIC COMMANDS:                                               ║
║   cd [dir]             - Change directory                    ║
║   pwd                  - Print working directory             ║
║   echo <text>          - Echo text                           ║
║   clear                - Clear the screen                    ║
║   history              - Show command history                ║
║   help                 - Show this help                      ║
║   exit                 - Exit the shell                      ║
╚══════════════════════════════════════════════════════════════╝
"""
        self.callback(help_text)
        return True
    
    def _cmd_history(self, args: List[str]) -> bool:
        """Show command history."""
        for i, cmd in enumerate(self.history[-20:], 1):
            self.callback(f"  {i:3}  {cmd}")
        return True
    
    # ==================== Scheduling Commands ====================
    
    def _cmd_scheduler(self, args: List[str]) -> bool:
        """Initialize or change scheduler."""
        if not self._require_auth():
            return False
        
        if not HAS_SCHEDULER:
            self.callback("Scheduler module not available")
            return False
        
        if len(args) < 2:
            self.callback("Usage: scheduler <rr|priority> [time_quantum]")
            return False
        
        sched_type = args[1].lower()
        
        if sched_type == 'rr':
            quantum = int(args[2]) if len(args) > 2 else 2
            self.scheduler = RoundRobinScheduler(time_quantum=quantum, callback=self._quiet_callback)
            self.scheduler_type = 'Round-Robin'
            self.callback(f"Initialized Round-Robin scheduler with quantum={quantum}")
        elif sched_type == 'priority':
            self.scheduler = PriorityScheduler(callback=self._quiet_callback)
            self.scheduler_type = 'Priority'
            self.callback("Initialized Priority scheduler")
        else:
            self.callback("Invalid scheduler type. Use 'rr' or 'priority'")
            return False
        
        return True
    
    def _cmd_schedule(self, args: List[str]) -> bool:
        """Schedule a process."""
        if not self._require_auth():
            return False
        
        if not self.scheduler:
            self.callback("No scheduler initialized. Use 'scheduler' command first.")
            return False
        
        if len(args) < 3:
            self.callback("Usage: schedule <name> <burst_time> [priority]")
            return False
        
        name = args[1]
        burst_time = int(args[2])
        priority = int(args[3]) if len(args) > 3 else 5
        
        # Generate a unique PID
        pid = len(self.scheduler.ready_queue) + len(self.scheduler.completed) + 1
        process = Process(pid=pid, name=name, burst_time=burst_time, priority=priority)
        self.scheduler.add_process(process)
        self.callback(f"Process '{name}' scheduled (burst={burst_time}, priority={priority})")
        
        return True
    
    def _cmd_sched_status(self, args: List[str]) -> bool:
        """Show scheduler status."""
        if not self.scheduler:
            self.callback("No scheduler initialized")
            return False
        
        self.callback(f"\nScheduler: {self.scheduler_type}")
        self.callback(f"Processes in queue: {len(self.scheduler.ready_queue)}")
        
        if hasattr(self.scheduler, 'get_queue_status'):
            for status in self.scheduler.get_queue_status():
                self.callback(f"  {status}")
        
        return True
    
    # ==================== Memory Commands ====================
    
    def _cmd_memory(self, args: List[str]) -> bool:
        """Initialize memory manager."""
        if not self._require_auth():
            return False
        
        if not HAS_MEMORY:
            self.callback("Memory management module not available")
            return False
        
        if len(args) < 2:
            self.callback("Usage: memory <num_frames> [fifo|lru]")
            return False
        
        frames = int(args[1])
        algo = args[2].lower() if len(args) > 2 else 'fifo'
        
        self.memory_manager = create_memory_manager(frames, algo, callback=self._quiet_callback)
        self.callback(f"Initialized memory manager with {frames} frames using {algo.upper()}")
        
        return True
    
    def _cmd_alloc(self, args: List[str]) -> bool:
        """Allocate a page."""
        if not self._require_auth():
            return False
        
        if not self.memory_manager:
            self.callback("No memory manager initialized. Use 'memory' command first.")
            return False
        
        if len(args) < 3:
            self.callback("Usage: alloc <process_id> <page_id>")
            return False
        
        pid = int(args[1])
        page = int(args[2])
        
        frame = self.memory_manager.allocate_page(pid, page)
        self.callback(f"Allocated page {page} for process {pid} to frame {frame}")
        
        return True
    
    def _cmd_free(self, args: List[str]) -> bool:
        """Free process pages."""
        if not self._require_auth():
            return False
        
        if not self.memory_manager:
            self.callback("No memory manager initialized")
            return False
        
        if len(args) < 2:
            self.callback("Usage: free <process_id>")
            return False
        
        pid = int(args[1])
        self.memory_manager.deallocate_process_pages(pid)
        self.callback(f"Freed all pages for process {pid}")
        
        return True
    
    def _cmd_mem_status(self, args: List[str]) -> bool:
        """Show memory status."""
        if not self.memory_manager:
            self.callback("No memory manager initialized")
            return False
        
        self.callback(self.memory_manager.visualize_memory())
        self.callback(self.memory_manager.metrics.get_summary())
        
        return True
    
    # ==================== Process Commands ====================
    
    def _cmd_jobs(self, args: List[str]) -> bool:
        """List background jobs."""
        if not self._require_auth():
            return False
        
        if not self.process_manager:
            self.callback("Process manager not available")
            return False
        
        jobs = self.process_manager.list_jobs()
        if not jobs:
            self.callback("No active jobs")
        else:
            for job in jobs:
                self.callback(job)
        
        return True
    
    def _cmd_fg(self, args: List[str]) -> bool:
        """Bring job to foreground."""
        if not self._require_auth():
            return False
        
        if not self.process_manager:
            self.callback("Process manager not available")
            return False
        
        job_id = int(args[1]) if len(args) > 1 else None
        
        if self.process_manager.foreground_job(job_id):
            return True
        else:
            self.callback("No such job")
            return False
    
    def _cmd_bg(self, args: List[str]) -> bool:
        """Continue job in background."""
        if not self._require_auth():
            return False
        
        if not self.process_manager:
            self.callback("Process manager not available")
            return False
        
        job_id = int(args[1]) if len(args) > 1 else None
        
        if self.process_manager.background_job(job_id):
            return True
        else:
            self.callback("No such job")
            return False
    
    def _cmd_kill(self, args: List[str]) -> bool:
        """Kill a process."""
        if not self._require_auth():
            return False
        
        if len(args) < 2:
            self.callback("Usage: kill <pid>")
            return False
        
        pid = int(args[1])
        
        try:
            os.kill(pid, signal.SIGTERM)
            self.callback(f"Killed process {pid}")
            return True
        except ProcessLookupError:
            self.callback(f"No such process: {pid}")
            return False
        except PermissionError:
            self.callback(f"Permission denied: {pid}")
            return False
    
    # ==================== Main Loop ====================
    
    def run(self):
        """Main shell loop."""
        self.running = True
        
        print("\n" + "="*60)
        print("Welcome to the Integrated Shell - Deliverable 4")
        print("="*60)
        print("This shell integrates all components from Deliverables 1-4:")
        print("  • Process Management (D1)")
        print("  • Process Scheduling (D2)")
        print("  • Memory Management & Synchronization (D3)")
        print("  • Piping, Authentication & Permissions (D4)")
        print("\nType 'help' for available commands.")
        print("Login required. Default: admin/admin123, user1/password1")
        print("="*60 + "\n")
        
        while self.running:
            try:
                prompt = self.get_prompt()
                command_line = input(prompt)
                self.execute_command(command_line)
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue
            except Exception as e:
                print(f"Error: {e}")


def main():
    """Entry point for the integrated shell."""
    shell = IntegratedShell()
    shell.run()


if __name__ == "__main__":
    main()
