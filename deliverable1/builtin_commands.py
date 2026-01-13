#!/usr/bin/env python3
"""
Built-in Commands Module

This module implements all built-in shell commands:
- cd, pwd, exit, echo, clear
- ls, cat, mkdir, rmdir, rm, touch
- kill, jobs, fg, bg
- help (additional utility command)
"""

import os
import sys
import signal
import shutil
from typing import List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from shell import Shell


class BuiltinCommands:
    """Handles all built-in shell commands."""
    
    def __init__(self, shell: 'Shell'):
        """
        Initialize builtin commands handler.
        
        Args:
            shell: Reference to the parent shell
        """
        self.shell = shell
        
        # Map of command names to their handler methods
        self.commands = {
            'cd': self._cmd_cd,
            'pwd': self._cmd_pwd,
            'exit': self._cmd_exit,
            'echo': self._cmd_echo,
            'clear': self._cmd_clear,
            'ls': self._cmd_ls,
            'cat': self._cmd_cat,
            'mkdir': self._cmd_mkdir,
            'rmdir': self._cmd_rmdir,
            'rm': self._cmd_rm,
            'touch': self._cmd_touch,
            'kill': self._cmd_kill,
            'jobs': self._cmd_jobs,
            'fg': self._cmd_fg,
            'bg': self._cmd_bg,
            'help': self._cmd_help,
            'history': self._cmd_history,
        }
    
    def is_builtin(self, command: str) -> bool:
        """
        Check if a command is a built-in command.
        
        Args:
            command: The command name
            
        Returns:
            True if the command is built-in
        """
        return command in self.commands
    
    def execute(self, command: str, args: List[str]) -> bool:
        """
        Execute a built-in command.
        
        Args:
            command: The command name
            args: Full argument list (including command name)
            
        Returns:
            True if command executed successfully
        """
        if command not in self.commands:
            print(f"myshell: {command}: command not found")
            return False
        
        return self.commands[command](args)
    
    # ==================== Directory Commands ====================
    
    def _cmd_cd(self, args: List[str]) -> bool:
        """
        Change the current working directory.
        
        Usage: cd [directory]
        If no directory is specified, changes to HOME directory.
        """
        if len(args) == 1:
            # No argument - go to home directory
            target = os.path.expanduser("~")
        elif len(args) == 2:
            target = args[1]
            # Handle ~ for home directory
            if target.startswith("~"):
                target = os.path.expanduser(target)
        else:
            print("myshell: cd: too many arguments")
            return False
        
        try:
            os.chdir(target)
            return True
        except FileNotFoundError:
            print(f"myshell: cd: {args[1] if len(args) > 1 else target}: No such file or directory")
            return False
        except NotADirectoryError:
            print(f"myshell: cd: {args[1] if len(args) > 1 else target}: Not a directory")
            return False
        except PermissionError:
            print(f"myshell: cd: {args[1] if len(args) > 1 else target}: Permission denied")
            return False
    
    def _cmd_pwd(self, args: List[str]) -> bool:
        """
        Print the current working directory.
        
        Usage: pwd
        """
        try:
            print(os.getcwd())
            return True
        except OSError as e:
            print(f"myshell: pwd: error: {e}")
            return False
    
    def _cmd_mkdir(self, args: List[str]) -> bool:
        """
        Create a new directory.
        
        Usage: mkdir [directory]
        """
        if len(args) < 2:
            print("myshell: mkdir: missing operand")
            return False
        
        for dirname in args[1:]:
            try:
                os.mkdir(dirname)
            except FileExistsError:
                print(f"myshell: mkdir: cannot create directory '{dirname}': File exists")
                return False
            except PermissionError:
                print(f"myshell: mkdir: cannot create directory '{dirname}': Permission denied")
                return False
            except FileNotFoundError:
                print(f"myshell: mkdir: cannot create directory '{dirname}': No such file or directory")
                return False
            except OSError as e:
                print(f"myshell: mkdir: cannot create directory '{dirname}': {e}")
                return False
        
        return True
    
    def _cmd_rmdir(self, args: List[str]) -> bool:
        """
        Remove an empty directory.
        
        Usage: rmdir [directory]
        """
        if len(args) < 2:
            print("myshell: rmdir: missing operand")
            return False
        
        for dirname in args[1:]:
            try:
                os.rmdir(dirname)
            except FileNotFoundError:
                print(f"myshell: rmdir: failed to remove '{dirname}': No such file or directory")
                return False
            except OSError as e:
                if "not empty" in str(e).lower() or e.errno == 66:  # Directory not empty
                    print(f"myshell: rmdir: failed to remove '{dirname}': Directory not empty")
                else:
                    print(f"myshell: rmdir: failed to remove '{dirname}': {e}")
                return False
        
        return True
    
    # ==================== File Commands ====================
    
    def _cmd_ls(self, args: List[str]) -> bool:
        """
        List directory contents.
        
        Usage: ls [directory]
        Options:
            -l: Long listing format
            -a: Include hidden files
        """
        # Parse options
        show_all = False
        long_format = False
        targets = []
        
        for arg in args[1:]:
            if arg.startswith('-'):
                for char in arg[1:]:
                    if char == 'a':
                        show_all = True
                    elif char == 'l':
                        long_format = True
                    else:
                        print(f"myshell: ls: invalid option -- '{char}'")
                        return False
            else:
                targets.append(arg)
        
        # Default to current directory
        if not targets:
            targets = ['.']
        
        success = True
        for target in targets:
            if len(targets) > 1:
                print(f"{target}:")
            
            try:
                entries = os.listdir(target)
                
                # Filter hidden files unless -a is specified
                if not show_all:
                    entries = [e for e in entries if not e.startswith('.')]
                
                entries.sort()
                
                if long_format:
                    for entry in entries:
                        path = os.path.join(target, entry)
                        try:
                            stat_info = os.stat(path)
                            # Format: permissions, size, modified time, name
                            mode = stat_info.st_mode
                            size = stat_info.st_size
                            mtime = datetime.fromtimestamp(stat_info.st_mtime)
                            
                            # Build permission string
                            is_dir = 'd' if os.path.isdir(path) else '-'
                            perms = is_dir
                            for i in range(2, -1, -1):
                                perms += 'r' if mode & (4 << (i * 3)) else '-'
                                perms += 'w' if mode & (2 << (i * 3)) else '-'
                                perms += 'x' if mode & (1 << (i * 3)) else '-'
                            
                            time_str = mtime.strftime("%b %d %H:%M")
                            
                            # Color directories blue
                            if os.path.isdir(path):
                                name = f"\033[1;34m{entry}\033[0m"
                            else:
                                name = entry
                            
                            print(f"{perms} {size:>8} {time_str} {name}")
                        except OSError:
                            print(f"{entry}")
                else:
                    # Simple listing with colors
                    output = []
                    for entry in entries:
                        path = os.path.join(target, entry)
                        if os.path.isdir(path):
                            output.append(f"\033[1;34m{entry}\033[0m")
                        elif os.access(path, os.X_OK):
                            output.append(f"\033[1;32m{entry}\033[0m")
                        else:
                            output.append(entry)
                    
                    # Print in columns
                    if output:
                        print("  ".join(output))
                
                if len(targets) > 1:
                    print()
                    
            except FileNotFoundError:
                print(f"myshell: ls: cannot access '{target}': No such file or directory")
                success = False
            except PermissionError:
                print(f"myshell: ls: cannot open directory '{target}': Permission denied")
                success = False
        
        return success
    
    def _cmd_cat(self, args: List[str]) -> bool:
        """
        Display the contents of a file.
        
        Usage: cat [filename...]
        """
        if len(args) < 2:
            print("myshell: cat: missing operand")
            return False
        
        success = True
        for filename in args[1:]:
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                    print(content, end='')
                    if content and not content.endswith('\n'):
                        print()  # Ensure newline at end
            except FileNotFoundError:
                print(f"myshell: cat: {filename}: No such file or directory")
                success = False
            except IsADirectoryError:
                print(f"myshell: cat: {filename}: Is a directory")
                success = False
            except PermissionError:
                print(f"myshell: cat: {filename}: Permission denied")
                success = False
            except UnicodeDecodeError:
                print(f"myshell: cat: {filename}: Binary file (cannot display)")
                success = False
        
        return success
    
    def _cmd_rm(self, args: List[str]) -> bool:
        """
        Remove a file.
        
        Usage: rm [filename...]
        Options:
            -r, -R: Remove directories recursively
            -f: Force removal without prompting
        """
        # Parse options
        recursive = False
        force = False
        targets = []
        
        for arg in args[1:]:
            if arg.startswith('-') and len(arg) > 1:
                for char in arg[1:]:
                    if char in 'rR':
                        recursive = True
                    elif char == 'f':
                        force = True
                    else:
                        print(f"myshell: rm: invalid option -- '{char}'")
                        return False
            else:
                targets.append(arg)
        
        if not targets:
            if not force:
                print("myshell: rm: missing operand")
            return False if not force else True
        
        success = True
        for target in targets:
            try:
                if os.path.isdir(target):
                    if recursive:
                        shutil.rmtree(target)
                    else:
                        print(f"myshell: rm: cannot remove '{target}': Is a directory")
                        success = False
                else:
                    os.remove(target)
            except FileNotFoundError:
                if not force:
                    print(f"myshell: rm: cannot remove '{target}': No such file or directory")
                    success = False
            except PermissionError:
                print(f"myshell: rm: cannot remove '{target}': Permission denied")
                success = False
            except OSError as e:
                print(f"myshell: rm: cannot remove '{target}': {e}")
                success = False
        
        return success
    
    def _cmd_touch(self, args: List[str]) -> bool:
        """
        Create an empty file or update the timestamp of an existing file.
        
        Usage: touch [filename...]
        """
        if len(args) < 2:
            print("myshell: touch: missing file operand")
            return False
        
        success = True
        for filename in args[1:]:
            try:
                # Create file if it doesn't exist, otherwise update timestamp
                with open(filename, 'a'):
                    os.utime(filename, None)
            except IsADirectoryError:
                print(f"myshell: touch: cannot touch '{filename}': Is a directory")
                success = False
            except PermissionError:
                print(f"myshell: touch: cannot touch '{filename}': Permission denied")
                success = False
            except OSError as e:
                print(f"myshell: touch: cannot touch '{filename}': {e}")
                success = False
        
        return success
    
    # ==================== Output Commands ====================
    
    def _cmd_echo(self, args: List[str]) -> bool:
        """
        Print text to the terminal.
        
        Usage: echo [text...]
        Options:
            -n: Do not output trailing newline
        """
        no_newline = False
        start_idx = 1
        
        if len(args) > 1 and args[1] == '-n':
            no_newline = True
            start_idx = 2
        
        output = ' '.join(args[start_idx:])
        
        # Handle escape sequences
        output = output.replace('\\n', '\n')
        output = output.replace('\\t', '\t')
        output = output.replace('\\\\', '\\')
        
        if no_newline:
            print(output, end='')
        else:
            print(output)
        
        return True
    
    def _cmd_clear(self, args: List[str]) -> bool:
        """
        Clear the terminal screen.
        
        Usage: clear
        """
        # ANSI escape sequence to clear screen and move cursor to home
        print('\033[2J\033[H', end='')
        return True
    
    # ==================== Shell Control Commands ====================
    
    def _cmd_exit(self, args: List[str]) -> bool:
        """
        Exit the shell.
        
        Usage: exit [status]
        """
        # Check for background jobs
        active_jobs = self.shell.process_manager.list_jobs()
        if active_jobs:
            print(f"myshell: There are {len(active_jobs)} active job(s).")
            print("Use 'exit' again to force exit or terminate jobs first.")
            # Allow exit on second attempt
            if hasattr(self, '_exit_warned') and self._exit_warned:
                self.shell.exit_shell()
            else:
                self._exit_warned = True
            return True
        
        self.shell.exit_shell()
        return True
    
    # ==================== Process Control Commands ====================
    
    def _cmd_kill(self, args: List[str]) -> bool:
        """
        Terminate a process by its PID.
        
        Usage: kill [-signal] [pid...]
        Signals: -9 (SIGKILL), -15 (SIGTERM), -TERM, -KILL, -STOP, -CONT
        """
        if len(args) < 2:
            print("myshell: kill: usage: kill [-signal] pid...")
            return False
        
        # Parse signal
        sig = signal.SIGTERM  # Default signal
        pids = []
        
        for arg in args[1:]:
            if arg.startswith('-'):
                sig_name = arg[1:].upper()
                try:
                    if sig_name.isdigit():
                        sig = int(sig_name)
                    elif sig_name == 'TERM':
                        sig = signal.SIGTERM
                    elif sig_name == 'KILL':
                        sig = signal.SIGKILL
                    elif sig_name == 'STOP':
                        sig = signal.SIGSTOP
                    elif sig_name == 'CONT':
                        sig = signal.SIGCONT
                    elif sig_name == 'INT':
                        sig = signal.SIGINT
                    elif sig_name == 'HUP':
                        sig = signal.SIGHUP
                    else:
                        # Try to get signal by number
                        sig = int(sig_name)
                except ValueError:
                    print(f"myshell: kill: {arg}: invalid signal specification")
                    return False
            else:
                try:
                    pids.append(int(arg))
                except ValueError:
                    print(f"myshell: kill: {arg}: invalid process id")
                    return False
        
        if not pids:
            print("myshell: kill: usage: kill [-signal] pid...")
            return False
        
        success = True
        for pid in pids:
            if not self.shell.process_manager.kill_job(pid, sig):
                success = False
        
        return success
    
    def _cmd_jobs(self, args: List[str]) -> bool:
        """
        List all background jobs.
        
        Usage: jobs
        """
        jobs = self.shell.process_manager.list_jobs()
        
        if not jobs:
            return True
        
        for job in sorted(jobs, key=lambda j: j.job_id):
            print(job)
        
        return True
    
    def _cmd_fg(self, args: List[str]) -> bool:
        """
        Bring a background job to the foreground.
        
        Usage: fg [job_id]
        If no job_id is specified, brings the most recent job to foreground.
        """
        if len(args) == 1:
            # No job_id specified, use most recent job
            job = self.shell.process_manager.get_most_recent_job()
            if not job:
                print("myshell: fg: no current job")
                return False
            job_id = job.job_id
        else:
            try:
                # Handle %n format
                job_arg = args[1]
                if job_arg.startswith('%'):
                    job_arg = job_arg[1:]
                job_id = int(job_arg)
            except ValueError:
                print(f"myshell: fg: {args[1]}: no such job")
                return False
        
        return self.shell.process_manager.bring_to_foreground(job_id)
    
    def _cmd_bg(self, args: List[str]) -> bool:
        """
        Resume a stopped job in the background.
        
        Usage: bg [job_id]
        If no job_id is specified, resumes the most recent stopped job.
        """
        if len(args) == 1:
            # No job_id specified, use most recent job
            job = self.shell.process_manager.get_most_recent_job()
            if not job:
                print("myshell: bg: no current job")
                return False
            job_id = job.job_id
        else:
            try:
                # Handle %n format
                job_arg = args[1]
                if job_arg.startswith('%'):
                    job_arg = job_arg[1:]
                job_id = int(job_arg)
            except ValueError:
                print(f"myshell: bg: {args[1]}: no such job")
                return False
        
        return self.shell.process_manager.send_to_background(job_id)
    
    # ==================== Utility Commands ====================
    
    def _cmd_help(self, args: List[str]) -> bool:
        """
        Display help information about built-in commands.
        
        Usage: help [command]
        """
        help_text = {
            'cd': 'cd [directory] - Change the current working directory',
            'pwd': 'pwd - Print the current working directory',
            'exit': 'exit [status] - Exit the shell',
            'echo': 'echo [-n] [text...] - Display text to the terminal',
            'clear': 'clear - Clear the terminal screen',
            'ls': 'ls [-la] [directory] - List directory contents',
            'cat': 'cat [file...] - Display file contents',
            'mkdir': 'mkdir [directory...] - Create directories',
            'rmdir': 'rmdir [directory...] - Remove empty directories',
            'rm': 'rm [-rf] [file...] - Remove files or directories',
            'touch': 'touch [file...] - Create files or update timestamps',
            'kill': 'kill [-signal] [pid...] - Send signal to processes',
            'jobs': 'jobs - List background jobs',
            'fg': 'fg [job_id] - Bring job to foreground',
            'bg': 'bg [job_id] - Resume job in background',
            'help': 'help [command] - Display this help information',
            'history': 'history - Display command history',
        }
        
        if len(args) > 1:
            cmd = args[1]
            if cmd in help_text:
                print(help_text[cmd])
            else:
                print(f"myshell: help: no help available for '{cmd}'")
                return False
        else:
            print("MyShell - Built-in Commands")
            print("=" * 50)
            print("\nFile & Directory Commands:")
            print("  cd       - Change directory")
            print("  pwd      - Print working directory")
            print("  ls       - List directory contents")
            print("  mkdir    - Create directory")
            print("  rmdir    - Remove empty directory")
            print("  touch    - Create file or update timestamp")
            print("  rm       - Remove files")
            print("  cat      - Display file contents")
            print("\nOutput Commands:")
            print("  echo     - Print text")
            print("  clear    - Clear screen")
            print("\nProcess Control Commands:")
            print("  jobs     - List background jobs")
            print("  fg       - Bring job to foreground")
            print("  bg       - Resume job in background")
            print("  kill     - Send signal to process")
            print("\nShell Commands:")
            print("  exit     - Exit the shell")
            print("  help     - Display this help")
            print("  history  - Show command history")
            print("\nBackground Execution:")
            print("  Append '&' to run a command in background")
            print("  Example: sleep 10 &")
            print("\nType 'help <command>' for detailed help on a command.")
        
        return True
    
    def _cmd_history(self, args: List[str]) -> bool:
        """
        Display command history.
        
        Usage: history
        """
        for i, cmd in enumerate(self.shell.history, 1):
            print(f"  {i}  {cmd}")
        return True
