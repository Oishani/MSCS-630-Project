# Deliverable 2: Process Scheduling Simulation

## Overview

This deliverable extends the shell from Deliverable 1 with internal process scheduling capabilities. It implements two scheduling algorithms:

1. **Round-Robin Scheduling** - Time-slice based fair scheduling
2. **Priority-Based Scheduling** - Priority queue with preemption support

## Features Implemented

### 1. Round-Robin Scheduling

| Feature | Description |
|---------|-------------|
| Configurable Quantum | User can set time slice duration |
| Process Rotation | Processes cycle through the queue |
| Preemption on Quantum | Process moves to back of queue when quantum expires |
| Early Completion | Process removed from queue if it completes before quantum |

### 2. Priority-Based Scheduling

| Feature | Description |
|---------|-------------|
| Priority Levels | Lower number = higher priority (0 is highest) |
| Preemptive Mode | Higher priority processes preempt running ones |
| FCFS Tiebreaker | Same priority processes scheduled by arrival time |
| Min-Heap Queue | Efficient O(log n) process selection |

### 3. Performance Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| Waiting Time | Turnaround - Burst | Time spent waiting in ready queue |
| Turnaround Time | Completion - Arrival | Total time from arrival to completion |
| Response Time | First Run - Arrival | Time until first CPU access |

## File Structure

```
deliverable2/
├── process.py           # Process class and state definitions
├── scheduler.py         # Scheduling algorithms implementation
├── scheduling_shell.py  # Interactive shell interface
├── demo.py             # Comprehensive demo script
└── README.md           # This file
```

## Dependencies

**Python 3.6+** is required. Only standard library modules are used:

- `time`, `threading`, `heapq`, `collections`, `dataclasses`

## How to Run

### Running the Interactive Demo

```bash
cd deliverable2
python3 demo.py
```

The demo provides:
- Guided walkthrough of Round-Robin scheduling
- Guided walkthrough of Priority scheduling
- Preemption demonstration
- Algorithm comparison with metrics

### Running the Scheduling Shell

```bash
cd deliverable2
python3 scheduling_shell.py
```

## Shell Commands

### Scheduler Setup
```bash
scheduler rr [quantum]     # Create Round-Robin scheduler
scheduler priority         # Create Priority scheduler
rr [quantum]              # Shortcut for Round-Robin
priority                  # Shortcut for Priority
```

### Process Management
```bash
add <name> <burst> [pri]  # Add process (pri: 0=highest)
list                      # List all processes
ps                        # Alias for list
status                    # Show scheduler status
```

### Scheduler Control
```bash
start                     # Start the scheduler
run                       # Alias for start
stop                      # Stop the scheduler
pause                     # Pause scheduling
resume                    # Resume scheduling
```

### Configuration
```bash
quantum <seconds>         # Set Round-Robin time quantum
config                    # Show current configuration
```

### Metrics
```bash
metrics                   # Show performance metrics
report                    # Show detailed report
```

## Implementation Details

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SchedulingShell                      │
│                 (scheduling_shell.py)                   │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│ RoundRobinScheduler │       │  PriorityScheduler  │
│                     │       │                     │
│ - ready_queue       │       │ - priority_queue    │
│ - time_quantum      │       │ - preemptive mode   │
│ - FIFO ordering     │       │ - min-heap ordering │
└─────────────────────┘       └─────────────────────┘
          │                               │
          └───────────────┬───────────────┘
                          │
                          ▼
              ┌─────────────────────┐
              │       Process       │
              │    (process.py)     │
              │                     │
              │ - pid, name         │
              │ - burst_time        │
              │ - priority          │
              │ - state             │
              │ - metrics           │
              └─────────────────────┘
```

### Round-Robin Algorithm

```python
while ready_queue not empty:
    process = ready_queue.pop_front()
    
    execute_time = min(quantum, process.remaining_time)
    process.execute(execute_time)
    
    if process.is_complete():
        mark_completed(process)
    else:
        ready_queue.push_back(process)  # Back to queue
```

### Priority Scheduling Algorithm

```python
while priority_queue not empty:
    process = priority_queue.pop_min()  # Highest priority
    
    while process.remaining_time > 0:
        if higher_priority_arrived():
            preempt(process)
            priority_queue.push(process)
            break
        
        execute_interval(process)
    
    if process.is_complete():
        mark_completed(process)
```

## Usage Examples

### Round-Robin Example

```bash
scheduler> rr 0.5
✓ Round-Robin scheduler created (quantum=0.5s)

scheduler> add Process_A 2.0
✓ Process added: PID=1, Name=Process_A, Burst=2.0s

scheduler> add Process_B 1.5
✓ Process added: PID=2, Name=Process_B, Burst=1.5s

scheduler> start
Starting scheduler...
  [LOG] Running: Process_A (PID: 1, Remaining: 2.00s)
  [LOG] Preempted: Process_A (PID: 1, Remaining: 1.50s)
  [LOG] Running: Process_B (PID: 2, Remaining: 1.50s)
  ...

scheduler> metrics
============================================================
Scheduler Performance Summary: Round-Robin (quantum=0.5s)
============================================================
Average Metrics:
  - Waiting Time:    1.250s
  - Turnaround Time: 3.000s
  - Response Time:   0.250s
```

### Priority Scheduling Example

```bash
scheduler> priority
✓ Preemptive Priority scheduler created

scheduler> add HighPri 1.0 1
✓ Process added: PID=1, Priority=1

scheduler> add LowPri 2.0 5
✓ Process added: PID=2, Priority=5

scheduler> start
Starting scheduler...
  [LOG] Running: HighPri (PID: 1, Priority: 1)
  [LOG] Completed: HighPri (PID: 1)
  [LOG] Running: LowPri (PID: 2, Priority: 5)
  ...

scheduler> report
# Detailed metrics table shown
```

### Preemption Example

```bash
scheduler> priority
scheduler> add LowPri 3.0 10
scheduler> start
  [LOG] Running: LowPri (PID: 1, Priority: 10)

# While running, add high priority process:
scheduler> add HighPri 1.0 1
  [LOG] Preemption triggered: HighPri (Pri: 1) > LowPri (Pri: 10)
  [LOG] Preempted: LowPri (PID: 1)
  [LOG] Running: HighPri (PID: 2, Priority: 1)
```

## Performance Analysis

### Metrics Definitions

**Waiting Time:**
- Time a process spends in the ready queue
- Does not include time while running
- Formula: `Turnaround Time - Burst Time`

**Turnaround Time:**
- Total time from process arrival to completion
- Includes waiting + execution time
- Formula: `Completion Time - Arrival Time`

**Response Time:**
- Time from arrival until first CPU access
- Important for interactive systems
- Formula: `First Execution Time - Arrival Time`

### Algorithm Comparison

| Aspect | Round-Robin | Priority |
|--------|-------------|----------|
| Fairness | High - equal time slices | Low - priority dependent |
| Response Time | Predictable | Fast for high priority |
| Throughput | Moderate | Can be high |
| Starvation | No | Possible for low priority |
| Context Switches | High | Low to moderate |
| Best For | Time-sharing | Real-time systems |

## Error Handling

| Error | Response |
|-------|----------|
| No scheduler created | "Error: No scheduler created. Use 'scheduler rr' or 'scheduler priority' first." |
| Invalid burst time | "Invalid burst time: [value]" |
| Invalid priority | "Invalid priority: [value]" |
| Scheduler already running | "Scheduler is already running." |
| No processes | "Warning: No processes in queue." |
