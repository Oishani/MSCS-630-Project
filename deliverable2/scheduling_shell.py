#!/usr/bin/env python3
"""
Scheduling Shell for Deliverable 2

This module extends the shell from Deliverable 1 with process scheduling
capabilities using Round-Robin and Priority-Based algorithms.
"""

import os
import sys
import time
import threading
from typing import Optional, List

# Add parent directory to path to import from deliverable1
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'deliverable1'))

from scheduler import (
    RoundRobinScheduler, 
    PriorityScheduler, 
    SchedulerType,
    create_scheduler
)
from process import Process, ProcessState


class SchedulingShell:
    """Shell with integrated process scheduling simulation."""
    
    def __init__(self):
        """Initialize the scheduling shell."""
        self.running = True
        self.scheduler: Optional[RoundRobinScheduler | PriorityScheduler] = None
        self.scheduler_thread: Optional[threading.Thread] = None
        self.scheduler_type: Optional[SchedulerType] = None
        
        # Default settings
        self.default_quantum = 1.0
        self.default_priority = 5
        
        # Command handlers
        self.commands = {
            'help': self._cmd_help,
            'exit': self._cmd_exit,
            'quit': self._cmd_exit,
            'clear': self._cmd_clear,
            
            # Scheduler commands
            'scheduler': self._cmd_scheduler,
            'rr': self._cmd_rr,
            'priority': self._cmd_priority,
            
            # Process commands
            'add': self._cmd_add,
            'create': self._cmd_add,
            'list': self._cmd_list,
            'ps': self._cmd_list,
            'status': self._cmd_status,
            
            # Control commands
            'start': self._cmd_start,
            'run': self._cmd_start,
            'stop': self._cmd_stop,
            'pause': self._cmd_pause,
            'resume': self._cmd_resume,
            
            # Configuration
            'quantum': self._cmd_quantum,
            'config': self._cmd_config,
            
            # Metrics
            'metrics': self._cmd_metrics,
            'report': self._cmd_report,
        }
        
        self.prompt = "\033[1;35mscheduler\033[0m> "
    
    def log(self, message: str):
        """Print a log message."""
        print(f"  \033[90m{message}\033[0m")
    
    def _cmd_help(self, args: List[str]) -> bool:
        """Display help information."""
        help_text = """
\033[1mScheduling Shell - Deliverable 2\033[0m
=====================================

\033[1;36mScheduler Setup:\033[0m
  scheduler rr [quantum]     - Create Round-Robin scheduler
  scheduler priority         - Create Priority-Based scheduler
  rr [quantum]              - Shortcut for Round-Robin
  priority                  - Shortcut for Priority scheduler

\033[1;36mProcess Management:\033[0m
  add <name> <burst> [pri]  - Add a process (pri: 0=highest, default=5)
  list / ps                 - List all processes
  status                    - Show scheduler status

\033[1;36mScheduler Control:\033[0m
  start / run               - Start the scheduler
  stop                      - Stop the scheduler
  pause                     - Pause scheduling
  resume                    - Resume scheduling

\033[1;36mConfiguration:\033[0m
  quantum <seconds>         - Set Round-Robin time quantum
  config                    - Show current configuration

\033[1;36mMetrics & Analysis:\033[0m
  metrics                   - Show performance metrics
  report                    - Show detailed report

\033[1;36mOther:\033[0m
  help                      - Show this help
  clear                     - Clear screen
  exit / quit               - Exit the shell

\033[1;33mExample Usage:\033[0m
  scheduler rr 0.5          # Create RR scheduler with 0.5s quantum
  add Process1 3            # Add process with 3s burst time
  add Process2 2 1          # Add process with 2s burst, priority 1
  start                     # Run the scheduler
  metrics                   # View performance metrics
"""
        print(help_text)
        return True
    
    def _cmd_exit(self, args: List[str]) -> bool:
        """Exit the shell."""
        if self.scheduler and self.scheduler.running:
            print("Stopping scheduler...")
            self.scheduler.stop()
        self.running = False
        return True
    
    def _cmd_clear(self, args: List[str]) -> bool:
        """Clear the screen."""
        print('\033[2J\033[H', end='')
        return True
    
    def _cmd_scheduler(self, args: List[str]) -> bool:
        """Create a scheduler."""
        if len(args) < 2:
            print("Usage: scheduler <rr|priority> [options]")
            print("  scheduler rr [quantum]  - Round-Robin with optional quantum")
            print("  scheduler priority      - Priority-Based scheduler")
            return False
        
        sched_type = args[1].lower()
        
        if sched_type in ('rr', 'roundrobin', 'round-robin'):
            quantum = self.default_quantum
            if len(args) > 2:
                try:
                    quantum = float(args[2])
                except ValueError:
                    print(f"Invalid quantum: {args[2]}")
                    return False
            
            self.scheduler = RoundRobinScheduler(
                time_quantum=quantum,
                callback=self.log
            )
            self.scheduler_type = SchedulerType.ROUND_ROBIN
            print(f"\033[1;32m✓\033[0m Round-Robin scheduler created (quantum={quantum}s)")
            
        elif sched_type in ('priority', 'pri'):
            preemptive = True
            if len(args) > 2 and args[2].lower() == 'nonpreemptive':
                preemptive = False
            
            self.scheduler = PriorityScheduler(
                preemptive=preemptive,
                callback=self.log
            )
            self.scheduler_type = SchedulerType.PRIORITY
            ptype = "Preemptive" if preemptive else "Non-preemptive"
            print(f"\033[1;32m✓\033[0m {ptype} Priority scheduler created")
        else:
            print(f"Unknown scheduler type: {sched_type}")
            return False
        
        return True
    
    def _cmd_rr(self, args: List[str]) -> bool:
        """Shortcut for creating Round-Robin scheduler."""
        new_args = ['scheduler', 'rr'] + args[1:]
        return self._cmd_scheduler(new_args)
    
    def _cmd_priority(self, args: List[str]) -> bool:
        """Shortcut for creating Priority scheduler."""
        new_args = ['scheduler', 'priority'] + args[1:]
        return self._cmd_scheduler(new_args)
    
    def _cmd_add(self, args: List[str]) -> bool:
        """Add a process to the scheduler."""
        if not self.scheduler:
            print("Error: No scheduler created. Use 'scheduler rr' or 'scheduler priority' first.")
            return False
        
        if len(args) < 3:
            print("Usage: add <name> <burst_time> [priority]")
            print("  name: Process name")
            print("  burst_time: CPU time needed (seconds)")
            print("  priority: 0=highest priority (default=5)")
            return False
        
        name = args[1]
        try:
            burst_time = float(args[2])
        except ValueError:
            print(f"Invalid burst time: {args[2]}")
            return False
        
        priority = self.default_priority
        if len(args) > 3:
            try:
                priority = int(args[3])
            except ValueError:
                print(f"Invalid priority: {args[3]}")
                return False
        
        process = self.scheduler.create_process(name, burst_time, priority)
        print(f"\033[1;32m✓\033[0m Process added: PID={process.pid}, Name={name}, Burst={burst_time}s, Priority={priority}")
        return True
    
    def _cmd_list(self, args: List[str]) -> bool:
        """List all processes."""
        if not self.scheduler:
            print("No scheduler created.")
            return False
        
        processes = self.scheduler.get_all_processes()
        
        if not processes:
            print("No processes in queue.")
            return True
        
        print(f"\n\033[1mProcess List ({len(processes)} processes)\033[0m")
        print("-" * 70)
        
        for proc in processes:
            # Color based on state
            if proc.state == ProcessState.RUNNING:
                color = '\033[1;32m'  # Green
            elif proc.state == ProcessState.COMPLETED:
                color = '\033[1;34m'  # Blue
            elif proc.state == ProcessState.READY:
                color = '\033[1;33m'  # Yellow
            else:
                color = '\033[0m'
            
            print(f"{color}{proc.get_status_line()}\033[0m")
        
        print("-" * 70)
        return True
    
    def _cmd_status(self, args: List[str]) -> bool:
        """Show scheduler status."""
        if not self.scheduler:
            print("No scheduler created.")
            return False
        
        print(f"\n\033[1mScheduler Status\033[0m")
        print("-" * 40)
        print(f"Type: {self.scheduler.metrics.algorithm}")
        print(f"Running: {'Yes' if self.scheduler.running else 'No'}")
        print(f"Paused: {'Yes' if self.scheduler.paused else 'No'}")
        
        if self.scheduler.current_process:
            print(f"Current Process: {self.scheduler.current_process.name} (PID: {self.scheduler.current_process.pid})")
        else:
            print("Current Process: None")
        
        total = len(self.scheduler.processes)
        completed = len([p for p in self.scheduler.processes if p.state == ProcessState.COMPLETED])
        print(f"Processes: {completed}/{total} completed")
        
        if isinstance(self.scheduler, RoundRobinScheduler):
            print(f"Time Quantum: {self.scheduler.time_quantum}s")
            print(f"Queue Length: {len(self.scheduler.ready_queue)}")
        elif isinstance(self.scheduler, PriorityScheduler):
            print(f"Preemptive: {'Yes' if self.scheduler.preemptive else 'No'}")
            print(f"Queue Length: {len(self.scheduler.priority_queue)}")
        
        print("-" * 40)
        return True
    
    def _cmd_start(self, args: List[str]) -> bool:
        """Start the scheduler."""
        if not self.scheduler:
            print("Error: No scheduler created.")
            return False
        
        if self.scheduler.running:
            print("Scheduler is already running.")
            return False
        
        if not self.scheduler.processes:
            print("Warning: No processes in queue. Add processes with 'add' command.")
            return False
        
        print("\033[1;32mStarting scheduler...\033[0m")
        print("(Scheduler will run in background. Use 'status' to check progress.)\n")
        
        # Run in non-blocking mode
        self.scheduler_thread = self.scheduler.run(blocking=False)
        return True
    
    def _cmd_stop(self, args: List[str]) -> bool:
        """Stop the scheduler."""
        if not self.scheduler:
            print("No scheduler to stop.")
            return False
        
        if not self.scheduler.running:
            print("Scheduler is not running.")
            return False
        
        self.scheduler.stop()
        print("\033[1;33mScheduler stopped.\033[0m")
        return True
    
    def _cmd_pause(self, args: List[str]) -> bool:
        """Pause the scheduler."""
        if not self.scheduler or not self.scheduler.running:
            print("Scheduler is not running.")
            return False
        
        self.scheduler.pause()
        print("\033[1;33mScheduler paused.\033[0m")
        return True
    
    def _cmd_resume(self, args: List[str]) -> bool:
        """Resume the scheduler."""
        if not self.scheduler or not self.scheduler.running:
            print("Scheduler is not running.")
            return False
        
        self.scheduler.resume()
        print("\033[1;32mScheduler resumed.\033[0m")
        return True
    
    def _cmd_quantum(self, args: List[str]) -> bool:
        """Set Round-Robin time quantum."""
        if len(args) < 2:
            print(f"Current quantum: {self.default_quantum}s")
            print("Usage: quantum <seconds>")
            return True
        
        try:
            quantum = float(args[1])
            if quantum <= 0:
                print("Quantum must be positive.")
                return False
            
            self.default_quantum = quantum
            
            if isinstance(self.scheduler, RoundRobinScheduler):
                self.scheduler.set_time_quantum(quantum)
            
            print(f"\033[1;32m✓\033[0m Time quantum set to {quantum}s")
            return True
        except ValueError:
            print(f"Invalid quantum: {args[1]}")
            return False
    
    def _cmd_config(self, args: List[str]) -> bool:
        """Show current configuration."""
        print(f"\n\033[1mCurrent Configuration\033[0m")
        print("-" * 30)
        print(f"Default Quantum: {self.default_quantum}s")
        print(f"Default Priority: {self.default_priority}")
        
        if self.scheduler:
            print(f"Scheduler: {self.scheduler.metrics.algorithm}")
        else:
            print("Scheduler: Not created")
        
        print("-" * 30)
        return True
    
    def _cmd_metrics(self, args: List[str]) -> bool:
        """Show performance metrics."""
        if not self.scheduler:
            print("No scheduler created.")
            return False
        
        # Make sure metrics are calculated
        self.scheduler.metrics.calculate_averages(self.scheduler.processes)
        
        print(self.scheduler.metrics.get_summary())
        return True
    
    def _cmd_report(self, args: List[str]) -> bool:
        """Show detailed metrics report."""
        if not self.scheduler:
            print("No scheduler created.")
            return False
        
        # Make sure metrics are calculated
        self.scheduler.metrics.calculate_averages(self.scheduler.processes)
        
        print(self.scheduler.metrics.get_detailed_report())
        return True
    
    def parse_command(self, command_line: str) -> List[str]:
        """Parse command line into arguments."""
        return command_line.strip().split()
    
    def execute_command(self, command_line: str) -> bool:
        """Execute a command."""
        args = self.parse_command(command_line)
        
        if not args:
            return True
        
        command = args[0].lower()
        
        if command in self.commands:
            return self.commands[command](args)
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")
            return False
    
    def run(self):
        """Main shell loop."""
        print("\n\033[1;35m" + "="*50 + "\033[0m")
        print("\033[1;35m  Process Scheduling Shell - Deliverable 2\033[0m")
        print("\033[1;35m" + "="*50 + "\033[0m")
        print("Type 'help' for available commands.\n")
        
        while self.running:
            try:
                command_line = input(self.prompt)
                self.execute_command(command_line)
            except EOFError:
                print("\nexit")
                self.running = False
            except KeyboardInterrupt:
                print()
                continue
            except Exception as e:
                print(f"Error: {e}")
        
        print("Goodbye!")


def main():
    """Entry point."""
    shell = SchedulingShell()
    shell.run()


if __name__ == "__main__":
    main()
