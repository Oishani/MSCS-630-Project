#!/usr/bin/env python3
"""
Advanced Shell Simulation - Deliverable 1
Basic Shell Implementation and Process Management

This module implements a Unix-like shell with:
- Built-in commands (cd, pwd, exit, echo, clear, ls, cat, mkdir, rmdir, rm, touch, kill)
- Process management with foreground/background execution
- Job control (jobs, fg, bg)
"""

import os
import sys
import signal
import subprocess
import shlex
from enum import Enum
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from process_manager import ProcessManager, JobStatus
from builtin_commands import BuiltinCommands


class Shell:
    """Main shell class that handles user input and command execution."""
    
    def __init__(self):
        """Initialize the shell with process manager and builtin commands."""
        self.running = True
        self.process_manager = ProcessManager()
        self.builtin_commands = BuiltinCommands(self)
        self.history: List[str] = []
        
        # Set up signal handlers
        self._setup_signal_handlers()
        
        # Shell prompt
        self.prompt = "myshell> "
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for the shell."""
        # Ignore SIGINT (Ctrl+C) in the shell itself
        # But allow it to be sent to child processes
        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTSTP, self._handle_sigtstp)
        # Handle SIGCHLD to reap zombie processes
        signal.signal(signal.SIGCHLD, self._handle_sigchld)
    
    def _handle_sigint(self, signum, frame):
        """Handle SIGINT (Ctrl+C) signal."""
        print()  # Print newline after ^C
        # If there's a foreground job, it will receive the signal
        # The shell continues running
    
    def _handle_sigtstp(self, signum, frame):
        """Handle SIGTSTP (Ctrl+Z) signal."""
        print()  # Print newline after ^Z
        # Stop the foreground job if any
        self.process_manager.stop_foreground_job()
    
    def _handle_sigchld(self, signum, frame):
        """Handle SIGCHLD signal to reap zombie processes."""
        self.process_manager.reap_children()
    
    def get_prompt(self) -> str:
        """Generate the shell prompt with current directory."""
        try:
            cwd = os.getcwd()
            home = os.path.expanduser("~")
            if cwd.startswith(home):
                cwd = "~" + cwd[len(home):]
            return f"\033[1;32mmyshell\033[0m:\033[1;34m{cwd}\033[0m$ "
        except OSError:
            return "myshell$ "
    
    def parse_command(self, command_line: str) -> Tuple[List[str], bool]:
        """
        Parse the command line into arguments and check for background execution.
        
        Args:
            command_line: The raw command line string
            
        Returns:
            Tuple of (argument list, is_background)
        """
        command_line = command_line.strip()
        
        # Check for background execution
        is_background = False
        if command_line.endswith('&'):
            is_background = True
            command_line = command_line[:-1].strip()
        
        # Parse the command using shlex for proper quote handling
        try:
            args = shlex.split(command_line)
        except ValueError as e:
            print(f"myshell: parse error: {e}")
            return [], False
        
        return args, is_background
    
    def execute_command(self, command_line: str) -> bool:
        """
        Execute a command line.
        
        Args:
            command_line: The raw command line string
            
        Returns:
            True if command executed successfully, False otherwise
        """
        command_line = command_line.strip()
        
        if not command_line:
            return True
        
        # Add to history
        self.history.append(command_line)
        
        # Parse the command
        args, is_background = self.parse_command(command_line)
        
        if not args:
            return True
        
        command = args[0]
        
        # Check if it's a built-in command
        if self.builtin_commands.is_builtin(command):
            return self.builtin_commands.execute(command, args)
        
        # Execute external command
        return self._execute_external(args, is_background)
    
    def _execute_external(self, args: List[str], is_background: bool) -> bool:
        """
        Execute an external command using fork/exec pattern.
        
        Args:
            args: Command arguments
            is_background: Whether to run in background
            
        Returns:
            True if execution started successfully
        """
        try:
            if is_background:
                # Background execution
                process = subprocess.Popen(
                    args,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                job_id = self.process_manager.add_job(process, ' '.join(args))
                print(f"[{job_id}] {process.pid}")
                return True
            else:
                # Foreground execution
                process = subprocess.Popen(
                    args,
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
                job_id = self.process_manager.add_job(process, ' '.join(args), foreground=True)
                
                # Wait for the process to complete
                try:
                    return_code = process.wait()
                    self.process_manager.mark_job_completed(job_id)
                    return return_code == 0
                except KeyboardInterrupt:
                    # Ctrl+C was pressed, send SIGINT to the process
                    process.send_signal(signal.SIGINT)
                    process.wait()
                    self.process_manager.mark_job_completed(job_id)
                    print()
                    return False
                    
        except FileNotFoundError:
            print(f"myshell: {args[0]}: command not found")
            return False
        except PermissionError:
            print(f"myshell: {args[0]}: permission denied")
            return False
        except Exception as e:
            print(f"myshell: {args[0]}: {e}")
            return False
    
    def run(self):
        """Main shell loop."""
        print("Welcome to MyShell - Advanced Shell Simulation")
        print("Type 'help' for available commands, 'exit' to quit.\n")
        
        while self.running:
            try:
                # Update job statuses
                self.process_manager.update_job_statuses()
                
                # Get user input
                command_line = input(self.get_prompt())
                
                # Execute the command
                self.execute_command(command_line)
                
            except EOFError:
                # Handle Ctrl+D
                print("\nexit")
                self.running = False
            except KeyboardInterrupt:
                # Handle Ctrl+C at prompt
                print()
                continue
            except Exception as e:
                print(f"myshell: error: {e}")
        
        # Cleanup before exit
        self.process_manager.cleanup()
        print("Goodbye!")
    
    def exit_shell(self):
        """Exit the shell gracefully."""
        self.running = False


def main():
    """Entry point for the shell."""
    shell = Shell()
    shell.run()


if __name__ == "__main__":
    main()
