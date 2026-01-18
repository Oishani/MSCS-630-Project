#!/usr/bin/env python3
"""
Interactive Demo Script for Deliverable 2

This script provides an interactive walkthrough of all scheduling features:
- Round-Robin Scheduling with configurable time slices
- Priority-Based Scheduling with preemption
- Performance metrics analysis (waiting time, turnaround time, response time)
"""

import os
import sys
import time
from typing import List

# Ensure we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler import RoundRobinScheduler, PriorityScheduler, SchedulerType
from process import Process, ProcessState


# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    GRAY = '\033[90m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*65}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(65)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*65}{Colors.END}\n")


def print_subheader(text: str):
    """Print a subsection header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- {text} ---{Colors.END}\n")


def print_info(text: str):
    """Print informational text."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_process_status(processes: List[Process], title: str = "Process Status"):
    """Print a formatted table of process statuses."""
    print(f"\n{Colors.BOLD}{title}{Colors.END}")
    print("-" * 75)
    print(f"{'PID':<5} {'Name':<15} {'Priority':<8} {'Burst':<8} {'Remaining':<10} {'State':<12}")
    print("-" * 75)
    
    for p in processes:
        state_color = {
            ProcessState.NEW: Colors.GRAY,
            ProcessState.READY: Colors.YELLOW,
            ProcessState.RUNNING: Colors.GREEN,
            ProcessState.COMPLETED: Colors.BLUE,
            ProcessState.PREEMPTED: Colors.RED,
        }.get(p.state, Colors.END)
        
        print(f"{p.pid:<5} {p.name:<15} {p.priority:<8} {p.burst_time:<8.2f} "
              f"{p.remaining_time:<10.2f} {state_color}{p.state.value:<12}{Colors.END}")
    print("-" * 75)


def print_metrics_table(scheduler, title: str = "Performance Metrics"):
    """Print a formatted metrics table."""
    metrics = scheduler.metrics
    metrics.calculate_averages(scheduler.processes)
    
    print(f"\n{Colors.BOLD}{title}{Colors.END}")
    print("=" * 75)
    print(f"{'PID':<5} {'Name':<15} {'Pri':<4} {'Burst':<8} {'Wait':<10} {'Turnaround':<12} {'Response':<10}")
    print("-" * 75)
    
    for pm in metrics.process_metrics:
        print(f"{pm['pid']:<5} {pm['name']:<15} {pm['priority']:<4} "
              f"{pm['burst_time']:<8.3f} {pm['waiting_time']:<10.3f} "
              f"{pm['turnaround_time']:<12.3f} {pm['response_time'] or 0:<10.3f}")
    
    print("-" * 75)
    print(f"{Colors.BOLD}Averages:{Colors.END}")
    print(f"  Waiting Time:    {metrics.avg_waiting_time:.3f}s")
    print(f"  Turnaround Time: {metrics.avg_turnaround_time:.3f}s")
    print(f"  Response Time:   {metrics.avg_response_time:.3f}s")
    print("=" * 75)


def wait_for_user(message: str = "Press Enter to continue..."):
    """Wait for user to press Enter."""
    input(f"\n{Colors.YELLOW}{message}{Colors.END}")


def get_user_choice(prompt: str, options: List[str]) -> int:
    """Get user's choice from a list of options."""
    while True:
        print(f"\n{Colors.CYAN}{prompt}{Colors.END}")
        for i, opt in enumerate(options, 1):
            print(f"  {i}. {opt}")
        
        try:
            choice = input(f"\n{Colors.YELLOW}Enter choice (1-{len(options)}): {Colors.END}")
            choice_int = int(choice)
            if 1 <= choice_int <= len(options):
                return choice_int
        except ValueError:
            pass
        print(f"{Colors.RED}Invalid choice. Please try again.{Colors.END}")


def get_float_input(prompt: str, default: float = None) -> float:
    """Get a float input from user."""
    while True:
        try:
            default_str = f" [{default}]" if default is not None else ""
            value = input(f"{Colors.YELLOW}{prompt}{default_str}: {Colors.END}")
            if not value and default is not None:
                return default
            return float(value)
        except ValueError:
            print(f"{Colors.RED}Invalid number. Please try again.{Colors.END}")


def get_int_input(prompt: str, default: int = None) -> int:
    """Get an integer input from user."""
    while True:
        try:
            default_str = f" [{default}]" if default is not None else ""
            value = input(f"{Colors.YELLOW}{prompt}{default_str}: {Colors.END}")
            if not value and default is not None:
                return default
            return int(value)
        except ValueError:
            print(f"{Colors.RED}Invalid number. Please try again.{Colors.END}")


def demo_round_robin():
    """Interactive demonstration of Round-Robin scheduling."""
    print_header("Round-Robin Scheduling Demo")
    
    print_info("""
Round-Robin (RR) is a preemptive scheduling algorithm where each process 
is assigned a fixed time slice called a 'quantum'. 

Key characteristics:
- Each process gets equal CPU time in rotation
- After quantum expires, process moves to back of queue
- Fair scheduling - no process starves
- Time quantum affects performance:
  - Too small: High context switch overhead
  - Too large: Approaches FCFS behavior
""")
    
    wait_for_user()
    
    # Get time quantum from user
    print_subheader("Configure Time Quantum")
    quantum = get_float_input("Enter time quantum in seconds", 0.5)
    print_success(f"Time quantum set to {quantum}s")
    
    # Create scheduler with visual output
    events = []
    def log_event(msg):
        events.append(msg)
        print(f"  {Colors.GRAY}[LOG] {msg}{Colors.END}")
    
    scheduler = RoundRobinScheduler(time_quantum=quantum, callback=log_event)
    
    # Let user add processes
    print_subheader("Add Processes")
    print_info("Add processes to the scheduler. Enter 'done' when finished.")
    
    # Add some default processes for demo
    use_defaults = input(f"\n{Colors.YELLOW}Use default processes for demo? (y/n) [y]: {Colors.END}").lower()
    
    if use_defaults != 'n':
        default_processes = [
            ("Process_A", 2.0),
            ("Process_B", 1.5),
            ("Process_C", 1.0),
            ("Process_D", 2.5),
        ]
        for name, burst in default_processes:
            proc = scheduler.create_process(name, burst, priority=0)
            print_success(f"Added: {name} (PID: {proc.pid}, Burst: {burst}s)")
    else:
        while True:
            name = input(f"\n{Colors.YELLOW}Process name (or 'done'): {Colors.END}")
            if name.lower() == 'done':
                break
            burst = get_float_input("Burst time (seconds)")
            proc = scheduler.create_process(name, burst, priority=0)
            print_success(f"Added: {name} (PID: {proc.pid}, Burst: {burst}s)")
    
    if not scheduler.processes:
        print_warning("No processes added. Adding default processes.")
        scheduler.create_process("Default_1", 1.5)
        scheduler.create_process("Default_2", 1.0)
    
    # Show initial state
    print_process_status(scheduler.processes, "Initial Process Queue")
    
    wait_for_user("Press Enter to start Round-Robin scheduling...")
    
    # Run scheduler
    print_subheader("Executing Round-Robin Scheduler")
    print_info(f"Running with quantum = {quantum}s")
    print_info("Watch the scheduling events below:\n")
    
    start_time = time.time()
    scheduler.run(blocking=True)
    end_time = time.time()
    
    # Show results
    print_subheader("Scheduling Complete")
    print_success(f"Total execution time: {end_time - start_time:.3f}s")
    
    print_process_status(scheduler.processes, "Final Process Status")
    print_metrics_table(scheduler, "Round-Robin Performance Metrics")
    
    # Explain metrics
    print_subheader("Metrics Explanation")
    print(f"""
{Colors.CYAN}Waiting Time:{Colors.END}
  Time a process spends waiting in the ready queue.
  Formula: Turnaround Time - Burst Time

{Colors.CYAN}Turnaround Time:{Colors.END}
  Total time from process arrival to completion.
  Formula: Completion Time - Arrival Time

{Colors.CYAN}Response Time:{Colors.END}
  Time from arrival until the process first gets CPU.
  Formula: First Execution Time - Arrival Time
  
{Colors.CYAN}Analysis:{Colors.END}
  Average Waiting Time: {scheduler.metrics.avg_waiting_time:.3f}s
  Average Turnaround: {scheduler.metrics.avg_turnaround_time:.3f}s
  Average Response: {scheduler.metrics.avg_response_time:.3f}s
""")
    
    return scheduler


def demo_priority_scheduling():
    """Interactive demonstration of Priority-Based scheduling."""
    print_header("Priority-Based Scheduling Demo")
    
    print_info("""
Priority-Based Scheduling assigns each process a priority level.
The process with the highest priority (lowest number) runs first.

Key characteristics:
- Priority 0 = Highest priority
- Higher priority processes preempt lower priority ones
- Same priority: First-Come, First-Served (FCFS)
- Can cause starvation of low-priority processes
- Uses a priority queue (min-heap) for efficient scheduling
""")
    
    wait_for_user()
    
    # Configure preemption
    print_subheader("Configure Preemption")
    preemptive = input(f"{Colors.YELLOW}Enable preemption? (y/n) [y]: {Colors.END}").lower() != 'n'
    ptype = "Preemptive" if preemptive else "Non-preemptive"
    print_success(f"{ptype} Priority scheduling selected")
    
    # Create scheduler
    events = []
    def log_event(msg):
        events.append(msg)
        print(f"  {Colors.GRAY}[LOG] {msg}{Colors.END}")
    
    scheduler = PriorityScheduler(preemptive=preemptive, callback=log_event)
    
    # Let user add processes
    print_subheader("Add Processes")
    print_info("Add processes with different priorities.")
    print_info("Priority: 0 = Highest, 10 = Lowest")
    
    use_defaults = input(f"\n{Colors.YELLOW}Use default processes for demo? (y/n) [y]: {Colors.END}").lower()
    
    if use_defaults != 'n':
        default_processes = [
            ("HighPri_A", 1.5, 1),
            ("MedPri_B", 2.0, 5),
            ("LowPri_C", 1.0, 8),
            ("HighPri_D", 1.0, 2),
        ]
        for name, burst, priority in default_processes:
            proc = scheduler.create_process(name, burst, priority)
            print_success(f"Added: {name} (PID: {proc.pid}, Burst: {burst}s, Priority: {priority})")
    else:
        while True:
            name = input(f"\n{Colors.YELLOW}Process name (or 'done'): {Colors.END}")
            if name.lower() == 'done':
                break
            burst = get_float_input("Burst time (seconds)")
            priority = get_int_input("Priority (0=highest)", 5)
            proc = scheduler.create_process(name, burst, priority)
            print_success(f"Added: {name} (PID: {proc.pid}, Burst: {burst}s, Priority: {priority})")
    
    if not scheduler.processes:
        print_warning("No processes added. Adding default processes.")
        scheduler.create_process("Default_High", 1.0, 1)
        scheduler.create_process("Default_Low", 1.5, 5)
    
    # Show initial state
    print_process_status(scheduler.processes, "Initial Process Queue (sorted by priority)")
    
    wait_for_user("Press Enter to start Priority scheduling...")
    
    # Run scheduler
    print_subheader("Executing Priority Scheduler")
    print_info(f"Running in {ptype} mode")
    print_info("Watch the scheduling events below:\n")
    
    start_time = time.time()
    scheduler.run(blocking=True)
    end_time = time.time()
    
    # Show results
    print_subheader("Scheduling Complete")
    print_success(f"Total execution time: {end_time - start_time:.3f}s")
    
    print_process_status(scheduler.processes, "Final Process Status")
    print_metrics_table(scheduler, "Priority-Based Performance Metrics")
    
    # Analysis
    print_subheader("Priority Scheduling Analysis")
    print(f"""
{Colors.CYAN}Observations:{Colors.END}
- High priority processes completed first
- Lower priority processes had longer waiting times
- {'Preemption occurred when higher priority process arrived' if preemptive else 'No preemption - processes ran to completion'}

{Colors.CYAN}Metrics Summary:{Colors.END}
  Average Waiting Time: {scheduler.metrics.avg_waiting_time:.3f}s
  Average Turnaround: {scheduler.metrics.avg_turnaround_time:.3f}s
  Average Response: {scheduler.metrics.avg_response_time:.3f}s
""")
    
    return scheduler


def demo_preemption():
    """Demonstrate preemption in Priority scheduling."""
    print_header("Preemption Demonstration")
    
    print_info("""
This demo shows how preemption works when a high-priority process
arrives while a low-priority process is running.

We'll start a low-priority process, then add a high-priority one
to see the preemption in action.
""")
    
    wait_for_user()
    
    events = []
    def log_event(msg):
        events.append(msg)
        print(f"  {Colors.GRAY}[LOG] {msg}{Colors.END}")
    
    scheduler = PriorityScheduler(preemptive=True, callback=log_event)
    
    # Add initial low-priority process
    print_subheader("Step 1: Add Low-Priority Process")
    low_pri = scheduler.create_process("LowPriority", 3.0, priority=10)
    print_success(f"Added: LowPriority (Priority: 10, Burst: 3.0s)")
    
    print_process_status(scheduler.processes)
    
    # Start scheduler in background
    print_subheader("Step 2: Start Scheduler")
    print_info("Starting scheduler... LowPriority process begins execution")
    
    scheduler_thread = scheduler.run(blocking=False)
    time.sleep(0.5)  # Let it run for a bit
    
    # Add high-priority process
    print_subheader("Step 3: Add High-Priority Process (Triggers Preemption)")
    print_warning("Adding high-priority process while low-priority is running...")
    time.sleep(0.2)
    
    high_pri = scheduler.create_process("HighPriority", 1.0, priority=1)
    print_success(f"Added: HighPriority (Priority: 1, Burst: 1.0s)")
    print_info("Watch the preemption happen!\n")
    
    # Wait for completion
    scheduler_thread.join()
    
    print_subheader("Step 4: Results")
    print_process_status(scheduler.processes, "Final Process Status")
    print_metrics_table(scheduler)
    
    print(f"""
{Colors.GREEN}Preemption Analysis:{Colors.END}
- LowPriority started first but was preempted
- HighPriority ran to completion
- LowPriority resumed and completed after
- Notice the increased waiting time for LowPriority due to preemption
""")
    
    return scheduler


def demo_comparison():
    """Compare Round-Robin and Priority scheduling."""
    print_header("Algorithm Comparison")
    
    print_info("""
This demo runs the same set of processes through both scheduling
algorithms and compares their performance metrics.
""")
    
    wait_for_user()
    
    # Define test processes
    test_processes = [
        ("Process_A", 2.0, 3),
        ("Process_B", 1.0, 1),
        ("Process_C", 1.5, 5),
        ("Process_D", 0.5, 2),
    ]
    
    print_subheader("Test Processes")
    print(f"{'Name':<15} {'Burst Time':<12} {'Priority':<10}")
    print("-" * 40)
    for name, burst, pri in test_processes:
        print(f"{name:<15} {burst:<12.1f} {pri:<10}")
    
    wait_for_user()
    
    # Run Round-Robin
    print_subheader("Running Round-Robin (quantum=0.5s)")
    rr_scheduler = RoundRobinScheduler(time_quantum=0.5, callback=lambda x: None)
    for name, burst, pri in test_processes:
        rr_scheduler.create_process(name, burst, pri)
    
    rr_start = time.time()
    rr_scheduler.run(blocking=True)
    rr_time = time.time() - rr_start
    print_success(f"Completed in {rr_time:.3f}s")
    
    # Run Priority
    print_subheader("Running Priority-Based (Preemptive)")
    pri_scheduler = PriorityScheduler(preemptive=True, callback=lambda x: None)
    for name, burst, pri in test_processes:
        pri_scheduler.create_process(name, burst, pri)
    
    pri_start = time.time()
    pri_scheduler.run(blocking=True)
    pri_time = time.time() - pri_start
    print_success(f"Completed in {pri_time:.3f}s")
    
    # Calculate metrics
    rr_scheduler.metrics.calculate_averages(rr_scheduler.processes)
    pri_scheduler.metrics.calculate_averages(pri_scheduler.processes)
    
    # Comparison table
    print_subheader("Performance Comparison")
    print(f"\n{Colors.BOLD}{'Metric':<25} {'Round-Robin':<15} {'Priority':<15} {'Better':<10}{Colors.END}")
    print("=" * 65)
    
    metrics_comparison = [
        ("Avg Waiting Time", rr_scheduler.metrics.avg_waiting_time, 
         pri_scheduler.metrics.avg_waiting_time, "lower"),
        ("Avg Turnaround Time", rr_scheduler.metrics.avg_turnaround_time,
         pri_scheduler.metrics.avg_turnaround_time, "lower"),
        ("Avg Response Time", rr_scheduler.metrics.avg_response_time,
         pri_scheduler.metrics.avg_response_time, "lower"),
        ("Total Execution", rr_time, pri_time, "lower"),
    ]
    
    for name, rr_val, pri_val, better_is in metrics_comparison:
        if better_is == "lower":
            winner = "RR" if rr_val < pri_val else "Priority"
            winner_color = Colors.GREEN
        else:
            winner = "RR" if rr_val > pri_val else "Priority"
            winner_color = Colors.GREEN
        
        if abs(rr_val - pri_val) < 0.01:
            winner = "Tie"
            winner_color = Colors.YELLOW
        
        print(f"{name:<25} {rr_val:<15.3f} {pri_val:<15.3f} {winner_color}{winner:<10}{Colors.END}")
    
    print("=" * 65)
    
    print(f"""
{Colors.CYAN}Analysis:{Colors.END}

{Colors.BOLD}Round-Robin:{Colors.END}
  - Fair time distribution among all processes
  - Better response time for all processes
  - More context switches (overhead)
  - Good for time-sharing systems

{Colors.BOLD}Priority-Based:{Colors.END}
  - High-priority processes complete faster
  - Can cause starvation of low-priority processes
  - Fewer context switches
  - Good for real-time systems
""")
    
    return rr_scheduler, pri_scheduler


def interactive_shell_demo():
    """Launch the interactive scheduling shell."""
    print_header("Interactive Scheduling Shell")
    
    print_info("""
The scheduling shell provides an interactive way to:
- Create and configure schedulers
- Add processes dynamically
- Run and control scheduling
- View real-time metrics

Let's launch the shell!
""")
    
    wait_for_user("Press Enter to launch the scheduling shell...")
    
    # Import and run the shell
    from scheduling_shell import SchedulingShell
    shell = SchedulingShell()
    shell.run()


def main():
    """Main demo function."""
    print_header("Process Scheduling Demo - Deliverable 2")
    
    print(f"""
{Colors.BOLD}Welcome to the Process Scheduling Demo!{Colors.END}

This interactive demo covers:
  1. Round-Robin Scheduling with configurable time slices
  2. Priority-Based Scheduling with preemption
  3. Performance metrics analysis
  4. Algorithm comparison

All demonstrations include detailed explanations of:
  • {Colors.CYAN}Waiting Time{Colors.END} - Time spent in ready queue
  • {Colors.CYAN}Turnaround Time{Colors.END} - Total time from arrival to completion  
  • {Colors.CYAN}Response Time{Colors.END} - Time until first CPU access
""")
    
    while True:
        choice = get_user_choice(
            "Select a demo:",
            [
                "Round-Robin Scheduling",
                "Priority-Based Scheduling", 
                "Preemption Demonstration",
                "Algorithm Comparison",
                "Interactive Scheduling Shell",
                "Exit Demo"
            ]
        )
        
        if choice == 1:
            demo_round_robin()
        elif choice == 2:
            demo_priority_scheduling()
        elif choice == 3:
            demo_preemption()
        elif choice == 4:
            demo_comparison()
        elif choice == 5:
            interactive_shell_demo()
        elif choice == 6:
            break
        
        wait_for_user("\nPress Enter to return to main menu...")
    
    print_header("Demo Complete!")
    print(f"""
{Colors.GREEN}{Colors.BOLD}Thank you for exploring the Process Scheduling Demo!{Colors.END}

{Colors.CYAN}Summary of Features Implemented:{Colors.END}

{Colors.BOLD}Round-Robin Scheduling:{Colors.END}
  ✓ Configurable time quantum
  ✓ Fair process rotation
  ✓ Proper queue management

{Colors.BOLD}Priority-Based Scheduling:{Colors.END}
  ✓ Priority queue (min-heap)
  ✓ Preemptive scheduling
  ✓ FCFS for same priority

{Colors.BOLD}Performance Metrics:{Colors.END}
  ✓ Waiting Time calculation
  ✓ Turnaround Time calculation
  ✓ Response Time calculation
  ✓ Per-process and average metrics

{Colors.BOLD}To run the shell directly:{Colors.END}
  python3 scheduling_shell.py

{Colors.BOLD}To run this demo again:{Colors.END}
  python3 demo.py
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user.{Colors.END}")
        sys.exit(0)
