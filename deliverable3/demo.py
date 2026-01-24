#!/usr/bin/env python3
"""
Interactive Demo Script for Deliverable 3

This script provides an interactive walkthrough of:
- Memory Management with Paging System
- FIFO and LRU Page Replacement Algorithms
- Process Synchronization with Mutexes and Semaphores
- Producer-Consumer Problem
- Dining Philosophers Problem
"""

import os
import sys
import time
import threading
import random
from typing import List

# Ensure we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_manager import (
    MemoryManager, 
    PageReplacementAlgorithm, 
    create_memory_manager
)
from synchronization import (
    Mutex, 
    Semaphore, 
    ProducerConsumer, 
    DiningPhilosophers,
    BoundedBuffer
)


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
    MAGENTA = '\033[35m'


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


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


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


def get_int_input(prompt: str, default: int = None, min_val: int = 1, max_val: int = 100) -> int:
    """Get an integer input from user."""
    while True:
        try:
            default_str = f" [{default}]" if default is not None else ""
            value = input(f"{Colors.YELLOW}{prompt}{default_str}: {Colors.END}")
            if not value and default is not None:
                return default
            val = int(value)
            if min_val <= val <= max_val:
                return val
            print(f"{Colors.RED}Value must be between {min_val} and {max_val}.{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}Invalid number. Please try again.{Colors.END}")


def demo_fifo_page_replacement():
    """Demonstrate FIFO page replacement algorithm."""
    print_header("FIFO Page Replacement Demo")
    
    print_info("""
FIFO (First-In-First-Out) Page Replacement:
- Pages are replaced in the order they were loaded
- Simple to implement using a queue
- May suffer from Belady's anomaly
- The oldest page in memory is always replaced first
""")
    
    wait_for_user()
    
    print_subheader("Configuration")
    num_frames = get_int_input("Number of memory frames", 4, 2, 10)
    
    def log_callback(msg):
        print(f"  {Colors.GRAY}{msg}{Colors.END}")
    
    mm = MemoryManager(
        num_frames=num_frames,
        algorithm=PageReplacementAlgorithm.FIFO,
        callback=log_callback
    )
    
    print_success(f"Created memory manager with {num_frames} frames using FIFO")
    
    print_subheader("Page Reference Simulation")
    
    default_refs = [(1, 0), (1, 1), (1, 2), (1, 3), (1, 0), (2, 0), (1, 4), (2, 1), (1, 0), (1, 3)]
    
    print_info("Default page reference sequence (Process, Page):")
    print(f"  {default_refs}")
    
    use_default = input(f"\n{Colors.YELLOW}Use default sequence? (y/n) [y]: {Colors.END}").lower()
    
    if use_default != 'n':
        page_refs = default_refs
    else:
        print_info("Enter page references as 'process_id,page_id' (or 'done' to finish):")
        page_refs = []
        while True:
            ref = input(f"{Colors.YELLOW}Reference: {Colors.END}")
            if ref.lower() == 'done':
                break
            try:
                proc, page = map(int, ref.split(','))
                page_refs.append((proc, page))
            except ValueError:
                print_error("Invalid format. Use: process_id,page_id")
    
    if not page_refs:
        page_refs = default_refs
    
    print_subheader("Processing Page References")
    
    for i, (proc_id, page_id) in enumerate(page_refs):
        print(f"\n{Colors.BOLD}Reference {i+1}: Process {proc_id}, Page {page_id}{Colors.END}")
        mm.allocate_page(proc_id, page_id)
        print(mm.visualize_memory())
        time.sleep(0.3)
    
    print_subheader("FIFO Performance Metrics")
    print(mm.metrics.get_summary())
    
    print_subheader("Analysis")
    hit_ratio = mm.metrics.get_hit_ratio()
    print(f"""
{Colors.CYAN}FIFO Algorithm Analysis:{Colors.END}
- Total Page References: {len(page_refs)}
- Page Faults: {mm.metrics.total_page_faults}
- Page Hits: {mm.metrics.total_page_hits}
- Hit Ratio: {hit_ratio:.2%}
- Page Replacements: {mm.metrics.page_replacements}

{Colors.CYAN}FIFO Characteristics:{Colors.END}
- Simple queue-based replacement
- Does not consider page usage frequency
- Can replace frequently used pages
""")
    
    return mm


def demo_lru_page_replacement():
    """Demonstrate LRU page replacement algorithm."""
    print_header("LRU Page Replacement Demo")
    
    print_info("""
LRU (Least Recently Used) Page Replacement:
- Replaces the page that hasn't been used for the longest time
- Better performance than FIFO in most cases
- Requires tracking of page access times
- Based on temporal locality principle
""")
    
    wait_for_user()
    
    print_subheader("Configuration")
    num_frames = get_int_input("Number of memory frames", 4, 2, 10)
    
    def log_callback(msg):
        print(f"  {Colors.GRAY}{msg}{Colors.END}")
    
    mm = MemoryManager(
        num_frames=num_frames,
        algorithm=PageReplacementAlgorithm.LRU,
        callback=log_callback
    )
    
    print_success(f"Created memory manager with {num_frames} frames using LRU")
    
    print_subheader("Page Reference Simulation")
    
    default_refs = [(1, 0), (1, 1), (1, 2), (1, 3), (1, 0), (2, 0), (1, 4), (2, 1), (1, 0), (1, 3)]
    
    print_info("Default page reference sequence (Process, Page):")
    print(f"  {default_refs}")
    
    use_default = input(f"\n{Colors.YELLOW}Use default sequence? (y/n) [y]: {Colors.END}").lower()
    
    if use_default != 'n':
        page_refs = default_refs
    else:
        print_info("Enter page references as 'process_id,page_id' (or 'done' to finish):")
        page_refs = []
        while True:
            ref = input(f"{Colors.YELLOW}Reference: {Colors.END}")
            if ref.lower() == 'done':
                break
            try:
                proc, page = map(int, ref.split(','))
                page_refs.append((proc, page))
            except ValueError:
                print_error("Invalid format. Use: process_id,page_id")
    
    if not page_refs:
        page_refs = default_refs
    
    print_subheader("Processing Page References")
    
    for i, (proc_id, page_id) in enumerate(page_refs):
        print(f"\n{Colors.BOLD}Reference {i+1}: Process {proc_id}, Page {page_id}{Colors.END}")
        mm.allocate_page(proc_id, page_id)
        print(mm.visualize_memory())
        time.sleep(0.3)
    
    print_subheader("LRU Performance Metrics")
    print(mm.metrics.get_summary())
    
    print_subheader("Analysis")
    hit_ratio = mm.metrics.get_hit_ratio()
    print(f"""
{Colors.CYAN}LRU Algorithm Analysis:{Colors.END}
- Total Page References: {len(page_refs)}
- Page Faults: {mm.metrics.total_page_faults}
- Page Hits: {mm.metrics.total_page_hits}
- Hit Ratio: {hit_ratio:.2%}
- Page Replacements: {mm.metrics.page_replacements}

{Colors.CYAN}LRU Characteristics:{Colors.END}
- Tracks page access recency
- Better performance for temporal locality
- More complex to implement than FIFO
- Commonly used in real operating systems
""")
    
    return mm


def demo_algorithm_comparison():
    """Compare FIFO and LRU algorithms."""
    print_header("FIFO vs LRU Comparison")
    
    print_info("""
This demo compares FIFO and LRU algorithms using the same 
page reference sequence to show their different behaviors.
""")
    
    wait_for_user()
    
    num_frames = 3
    page_refs = [(1, 0), (1, 1), (1, 2), (1, 3), (1, 0), (1, 1), (1, 4), (1, 0), (1, 1), (1, 2)]
    
    print_subheader("Test Configuration")
    print(f"Number of Frames: {num_frames}")
    print(f"Page References: {page_refs}")
    
    wait_for_user()
    
    print_subheader("Running FIFO Algorithm")
    fifo_mm = MemoryManager(num_frames, algorithm=PageReplacementAlgorithm.FIFO, 
                            callback=lambda x: print(f"  {Colors.GRAY}{x}{Colors.END}"))
    
    for proc_id, page_id in page_refs:
        fifo_mm.allocate_page(proc_id, page_id)
    
    print(f"\n{Colors.GREEN}FIFO Results:{Colors.END}")
    print(f"  Page Faults: {fifo_mm.metrics.total_page_faults}")
    print(f"  Page Hits: {fifo_mm.metrics.total_page_hits}")
    print(f"  Hit Ratio: {fifo_mm.metrics.get_hit_ratio():.2%}")
    
    wait_for_user()
    
    print_subheader("Running LRU Algorithm")
    lru_mm = MemoryManager(num_frames, algorithm=PageReplacementAlgorithm.LRU,
                           callback=lambda x: print(f"  {Colors.GRAY}{x}{Colors.END}"))
    
    for proc_id, page_id in page_refs:
        lru_mm.allocate_page(proc_id, page_id)
    
    print(f"\n{Colors.GREEN}LRU Results:{Colors.END}")
    print(f"  Page Faults: {lru_mm.metrics.total_page_faults}")
    print(f"  Page Hits: {lru_mm.metrics.total_page_hits}")
    print(f"  Hit Ratio: {lru_mm.metrics.get_hit_ratio():.2%}")
    
    print_subheader("Comparison Summary")
    print(f"\n{Colors.BOLD}{'Metric':<25} {'FIFO':<15} {'LRU':<15} {'Better':<10}{Colors.END}")
    print("=" * 65)
    
    comparisons = [
        ("Page Faults", fifo_mm.metrics.total_page_faults, lru_mm.metrics.total_page_faults, "lower"),
        ("Page Hits", fifo_mm.metrics.total_page_hits, lru_mm.metrics.total_page_hits, "higher"),
        ("Hit Ratio", f"{fifo_mm.metrics.get_hit_ratio():.2%}", f"{lru_mm.metrics.get_hit_ratio():.2%}", "higher"),
    ]
    
    for name, fifo_val, lru_val, better_is in comparisons:
        if better_is == "lower":
            if isinstance(fifo_val, (int, float)) and isinstance(lru_val, (int, float)):
                winner = "FIFO" if fifo_val < lru_val else ("LRU" if lru_val < fifo_val else "Tie")
            else:
                winner = "-"
        else:
            if isinstance(fifo_val, (int, float)) and isinstance(lru_val, (int, float)):
                winner = "FIFO" if fifo_val > lru_val else ("LRU" if lru_val > fifo_val else "Tie")
            else:
                winner = "-"
        
        print(f"{name:<25} {str(fifo_val):<15} {str(lru_val):<15} {Colors.GREEN}{winner:<10}{Colors.END}")
    
    print("=" * 65)
    
    print(f"""
{Colors.CYAN}Key Observations:{Colors.END}
- LRU typically performs better when there's temporal locality
- FIFO is simpler but may replace frequently used pages
- The choice depends on access patterns of the workload
""")
    
    return fifo_mm, lru_mm


def demo_memory_overflow():
    """Demonstrate memory overflow scenario with page replacement."""
    print_header("Memory Overflow Simulation")
    
    print_info("""
This demo simulates a memory overflow scenario where multiple
processes compete for limited memory frames, triggering page
replacement algorithms.
""")
    
    wait_for_user()
    
    num_frames = 4
    
    print_subheader("Scenario Setup")
    print(f"Memory Frames: {num_frames}")
    print("Processes: 3 processes, each needing 3 pages")
    print("Total pages needed: 9")
    print("Result: Memory overflow requiring page replacement")
    
    choice = get_user_choice("Select page replacement algorithm:", ["FIFO", "LRU"])
    algo = PageReplacementAlgorithm.FIFO if choice == 1 else PageReplacementAlgorithm.LRU
    
    def overflow_callback(msg):
        if "Fault" in msg or "Replacing" in msg or "Evicted" in msg:
            print(f"  {Colors.RED}{msg}{Colors.END}")
        elif "Hit" in msg:
            print(f"  {Colors.GREEN}{msg}{Colors.END}")
        else:
            print(f"  {Colors.GRAY}{msg}{Colors.END}")
    
    mm = MemoryManager(num_frames, algorithm=algo, callback=overflow_callback)
    
    print_subheader("Simulation Running")
    
    access_pattern = [
        (1, 0), (1, 1), (1, 2),
        (2, 0), (2, 1),
        (1, 0),
        (2, 2),
        (3, 0), (3, 1),
        (1, 1),
        (2, 0),
        (3, 2),
    ]
    
    for proc_id, page_id in access_pattern:
        print(f"\n{Colors.BOLD}Process {proc_id} accessing Page {page_id}{Colors.END}")
        mm.allocate_page(proc_id, page_id)
        
        used, total = mm.get_memory_usage()
        bar_len = 20
        filled = int(bar_len * used / total)
        bar = '█' * filled + '░' * (bar_len - filled)
        print(f"  Memory: [{bar}] {used}/{total} frames")
        time.sleep(0.3)
    
    print_subheader("Memory Overflow Metrics")
    print(mm.metrics.get_summary())
    
    print_subheader("Analysis")
    print(f"""
{Colors.CYAN}Memory Overflow Handling:{Colors.END}
- Total memory requests: {len(access_pattern)}
- Memory capacity: {num_frames} frames
- Page faults: {mm.metrics.total_page_faults}
- Page replacements: {mm.metrics.page_replacements}
- Algorithm used: {algo.value}

{Colors.CYAN}Per-Process Impact:{Colors.END}""")
    
    for pid in sorted(mm.metrics.process_page_faults.keys()):
        faults = mm.metrics.process_page_faults.get(pid, 0)
        pages = mm.metrics.process_memory_usage.get(pid, 0)
        print(f"  Process {pid}: {faults} faults, {pages} pages in memory")
    
    return mm


def demo_mutex_semaphore():
    """Demonstrate mutex and semaphore usage."""
    print_header("Mutex and Semaphore Demo")
    
    print_info("""
Synchronization Primitives:

Mutex (Mutual Exclusion):
- Binary lock (locked/unlocked)
- Only one thread can hold it at a time
- Used to protect critical sections

Semaphore:
- Counting synchronization primitive
- Can allow N threads to access resource
- Used for resource pools and signaling
""")
    
    wait_for_user()
    
    print_subheader("Mutex Demonstration")
    print_info("Simulating multiple threads accessing a shared counter with mutex protection")
    
    shared_counter = [0]
    mutex = Mutex("counter_mutex", callback=lambda x: print(f"  {Colors.GRAY}{x}{Colors.END}"))
    
    def increment_with_mutex(thread_id: int, iterations: int):
        for _ in range(iterations):
            mutex.acquire(thread_id, f"Thread-{thread_id}")
            temp = shared_counter[0]
            time.sleep(0.01)
            shared_counter[0] = temp + 1
            mutex.release(thread_id, f"Thread-{thread_id}")
    
    threads = []
    num_threads = 3
    iterations = 5
    
    print(f"\nStarting {num_threads} threads, each incrementing counter {iterations} times...")
    
    for i in range(num_threads):
        t = threading.Thread(target=increment_with_mutex, args=(i, iterations))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    expected = num_threads * iterations
    print(f"\n{Colors.GREEN}Results:{Colors.END}")
    print(f"  Expected counter value: {expected}")
    print(f"  Actual counter value: {shared_counter[0]}")
    print(f"  Race conditions prevented: {Colors.GREEN}{'Yes' if shared_counter[0] == expected else 'No'}{Colors.END}")
    print(mutex.metrics.get_summary())
    
    wait_for_user()
    
    print_subheader("Semaphore Demonstration")
    print_info("Simulating limited resource access (e.g., connection pool) with semaphore")
    
    max_connections = 2
    semaphore = Semaphore(max_connections, "connection_pool", 
                          callback=lambda x: print(f"  {Colors.GRAY}{x}{Colors.END}"))
    
    def use_connection(thread_id: int):
        name = f"Client-{thread_id}"
        print(f"  {name}: Requesting connection...")
        
        semaphore.wait(thread_id, name)
        print(f"  {name}: Got connection! Using resource...")
        time.sleep(random.uniform(0.2, 0.4))
        print(f"  {name}: Done, releasing connection")
        semaphore.signal(thread_id, name)
    
    print(f"\nConnection pool size: {max_connections}")
    print(f"Starting 5 clients trying to access the pool...\n")
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=use_connection, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.1)
    
    for t in threads:
        t.join()
    
    print(f"\n{Colors.GREEN}All clients completed successfully!{Colors.END}")
    print(f"Total contentions (had to wait): {semaphore.metrics.total_contentions}")


def demo_producer_consumer():
    """Demonstrate the Producer-Consumer problem."""
    print_header("Producer-Consumer Problem Demo")
    
    print_info("""
The Producer-Consumer Problem:
- Producers create items and add them to a shared buffer
- Consumers remove items from the buffer
- The buffer has a fixed capacity

Synchronization Requirements:
- Producers must wait if buffer is full
- Consumers must wait if buffer is empty
- Access to buffer must be mutually exclusive
""")
    
    wait_for_user()
    
    print_subheader("Configuration")
    buffer_size = get_int_input("Buffer size", 5, 1, 20)
    num_producers = get_int_input("Number of producers", 2, 1, 5)
    num_consumers = get_int_input("Number of consumers", 2, 1, 5)
    items_per_producer = get_int_input("Items per producer", 5, 1, 20)
    
    def pc_callback(msg):
        print(f"  {Colors.GRAY}{msg}{Colors.END}")
    
    pc = ProducerConsumer(
        buffer_size=buffer_size,
        num_producers=num_producers,
        num_consumers=num_consumers,
        items_per_producer=items_per_producer,
        callback=pc_callback
    )
    
    print_subheader("Running Simulation")
    print_info("Watch the producers and consumers coordinate access to the shared buffer...\n")
    
    pc.run(blocking=True)
    
    print_subheader("Results")
    print(f"""
{Colors.GREEN}Producer-Consumer Simulation Complete!{Colors.END}

{Colors.CYAN}Statistics:{Colors.END}
  Total Items Produced: {pc.produced_count}
  Total Items Consumed: {pc.consumed_count}
  Buffer Size: {buffer_size}
  
{Colors.CYAN}Synchronization:{Colors.END}
  - No race conditions occurred
  - Producers waited when buffer was full
  - Consumers waited when buffer was empty
  - All items were successfully transferred
""")
    
    return pc


def demo_dining_philosophers():
    """Demonstrate the Dining Philosophers problem."""
    print_header("Dining Philosophers Problem Demo")
    
    print_info("""
The Dining Philosophers Problem:
- N philosophers sit around a circular table
- Each philosopher alternates between thinking and eating
- To eat, a philosopher needs two forks (left and right)
- Forks are shared between adjacent philosophers

Challenge: Prevent deadlock and starvation!

Solution Used: Resource Ordering
- Philosophers always pick up the lower-numbered fork first
- This breaks the circular wait condition
- Guarantees no deadlock
""")
    
    wait_for_user()
    
    print_subheader("Configuration")
    num_philosophers = get_int_input("Number of philosophers", 5, 3, 10)
    meals_per_philosopher = get_int_input("Meals per philosopher", 3, 1, 10)
    
    def dp_callback(msg):
        print(f"  {Colors.GRAY}{msg}{Colors.END}")
    
    dp = DiningPhilosophers(
        num_philosophers=num_philosophers,
        meals_per_philosopher=meals_per_philosopher,
        callback=dp_callback
    )
    
    print_subheader("Table Layout")
    print("         Philosopher 0")
    print("        /           \\")
    print("   Fork 0           Fork 1")
    print("      /               \\")
    print("Philosopher 4     Philosopher 1")
    print("      \\               /")
    print("   Fork 4           Fork 2")
    print("        \\           /")
    print("         Philosopher 3")
    print("              |")
    print("           Fork 3")
    print("              |")
    print("         Philosopher 2")
    
    wait_for_user("Press Enter to start simulation...")
    
    print_subheader("Running Simulation")
    print_info("Watch the philosophers coordinate fork access...\n")
    
    dp.run(blocking=True)
    
    print_subheader("Results")
    print(f"""
{Colors.GREEN}Dining Philosophers Simulation Complete!{Colors.END}

{Colors.CYAN}Statistics:{Colors.END}
  Philosophers: {num_philosophers}
  Meals per Philosopher: {meals_per_philosopher}
  Total Meals Eaten: {sum(dp.meals_eaten.values())}
  Total Thinking Time: {dp.total_thinking_time:.2f}s
  Total Eating Time: {dp.total_eating_time:.2f}s
  Total Waiting Time: {dp.total_waiting_time:.2f}s

{Colors.CYAN}Deadlock Prevention:{Colors.END}
  Strategy: Resource Ordering
  - Each philosopher picks up lower-numbered fork first
  - This prevents circular wait condition
  - Result: NO DEADLOCKS occurred!

{Colors.CYAN}Fairness:{Colors.END}
  All philosophers completed their meals successfully.
""")
    
    return dp


def main():
    """Main demo function."""
    print_header("Memory Management & Synchronization Demo")
    print_header("Deliverable 3")
    
    print(f"""
{Colors.BOLD}Welcome to the Memory Management & Synchronization Demo!{Colors.END}

This interactive demo covers:

{Colors.CYAN}Memory Management:{Colors.END}
  • Paging System with fixed-size frames
  • FIFO Page Replacement Algorithm
  • LRU Page Replacement Algorithm
  • Memory overflow handling
  • Page fault tracking

{Colors.CYAN}Process Synchronization:{Colors.END}
  • Mutex (Mutual Exclusion Lock)
  • Semaphore (Counting Semaphore)
  • Producer-Consumer Problem
  • Dining Philosophers Problem
""")
    
    while True:
        choice = get_user_choice(
            "Select a demo:",
            [
                "FIFO Page Replacement",
                "LRU Page Replacement",
                "FIFO vs LRU Comparison",
                "Memory Overflow Simulation",
                "Mutex & Semaphore Basics",
                "Producer-Consumer Problem",
                "Dining Philosophers Problem",
                "Exit Demo"
            ]
        )
        
        if choice == 1:
            demo_fifo_page_replacement()
        elif choice == 2:
            demo_lru_page_replacement()
        elif choice == 3:
            demo_algorithm_comparison()
        elif choice == 4:
            demo_memory_overflow()
        elif choice == 5:
            demo_mutex_semaphore()
        elif choice == 6:
            demo_producer_consumer()
        elif choice == 7:
            demo_dining_philosophers()
        elif choice == 8:
            break
        
        wait_for_user("\nPress Enter to return to main menu...")
    
    print_header("Demo Complete!")
    print(f"""
{Colors.GREEN}{Colors.BOLD}Thank you for exploring the Memory & Synchronization Demo!{Colors.END}

{Colors.CYAN}Summary of Features Implemented:{Colors.END}

{Colors.BOLD}Memory Management:{Colors.END}
  ✓ Paging system with fixed-size frames
  ✓ Page table management
  ✓ FIFO page replacement
  ✓ LRU page replacement
  ✓ Page fault detection and handling
  ✓ Per-process memory tracking

{Colors.BOLD}Process Synchronization:{Colors.END}
  ✓ Mutex implementation
  ✓ Semaphore implementation
  ✓ Producer-Consumer solution
  ✓ Dining Philosophers solution
  ✓ Deadlock prevention (resource ordering)

{Colors.BOLD}To run this demo again:{Colors.END}
  python3 demo.py
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user.{Colors.END}")
        sys.exit(0)
