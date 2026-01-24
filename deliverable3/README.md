# Deliverable 3: Memory Management and Process Synchronization

## Overview

This deliverable implements memory management with paging and page replacement algorithms, along with process synchronization primitives and classical synchronization problem solutions.

## Features Implemented

### 1. Memory Management

#### Paging System
| Feature | Description |
|---------|-------------|
| Fixed-size Frames | Memory divided into fixed-size page frames |
| Page Table | Maps (process_id, page_id) to frame_id |
| Page Allocation | Allocates pages to available frames |
| Page Deallocation | Frees frames when processes terminate |
| Page Fault Handling | Detects and handles page faults |

#### Page Replacement Algorithms

| Algorithm | Description |
|-----------|-------------|
| **FIFO** | First-In-First-Out - replaces oldest page |
| **LRU** | Least Recently Used - replaces least recently accessed page |

### 2. Process Synchronization

#### Synchronization Primitives
| Primitive | Description |
|-----------|-------------|
| **Mutex** | Mutual exclusion lock for critical sections |
| **Semaphore** | Counting semaphore for resource pools |

#### Classical Problems Implemented
| Problem | Solution |
|---------|----------|
| **Producer-Consumer** | Bounded buffer with condition variables |
| **Dining Philosophers** | Resource ordering to prevent deadlock |

### 3. Performance Metrics

| Metric | Description |
|--------|-------------|
| Page Faults | Count of pages not in memory |
| Page Hits | Count of pages found in memory |
| Hit Ratio | Percentage of successful page accesses |
| Memory Usage | Per-process page allocation tracking |

## File Structure

```
deliverable3/
├── memory_manager.py     # Paging system and page replacement
├── synchronization.py    # Mutex, Semaphore, and sync problems
├── demo.py              # Interactive demonstration script
└── README.md            # This file
```

## Dependencies

**Python 3.6+** is required. Only standard library modules are used:

- `threading`, `time`, `collections`, `dataclasses`, `random`

## How to Run

### Running the Interactive Demo

```bash
cd deliverable3
python3 demo.py
```

The demo provides:
- FIFO page replacement demonstration
- LRU page replacement demonstration
- Algorithm comparison
- Memory overflow simulation
- Mutex and semaphore demonstration
- Producer-Consumer simulation
- Dining Philosophers simulation

## Implementation Details

### Memory Management Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MemoryManager                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Page Table  │  │   Frames    │  │ FIFO/LRU Queue  │  │
│  │ (pid,pg)->f │  │ [0][1]...[n]│  │  Track order    │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                      Methods                             │
│  allocate_page() | access_page() | deallocate_pages()   │
└─────────────────────────────────────────────────────────┘
```

### FIFO Page Replacement

```
Queue: [Page1] -> [Page2] -> [Page3] -> [Page4]
         ↑                                 ↑
      Oldest                            Newest
      (Victim)                         (Last In)

When memory is full:
1. Select front of queue (oldest page)
2. Evict the victim page
3. Load new page into freed frame
4. Add new page to back of queue
```

### LRU Page Replacement

```
Access Order: Page3 -> Page1 -> Page4 -> Page2
                ↑                          ↑
         Least Recent                 Most Recent
           (Victim)                  (Last Accessed)

When memory is full:
1. Find least recently accessed page
2. Evict the victim page
3. Load new page into freed frame
4. Update access order
```

### Synchronization Primitives

#### Mutex Usage
```python
mutex.acquire(thread_id, "Thread-1")
# Critical section - only one thread at a time
shared_resource += 1
mutex.release(thread_id, "Thread-1")
```

#### Semaphore Usage
```python
# Semaphore with count=3 (allows 3 concurrent accesses)
semaphore.wait(thread_id, "Client")    # Decrement count
# Use limited resource
semaphore.signal(thread_id, "Client")  # Increment count
```

### Producer-Consumer Solution

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Producer   │───>│  Bounded Buffer │───>│   Consumer   │
│              │    │  [___][___][___]│    │              │
│  Produces    │    │                 │    │  Consumes    │
│  items       │    │  Synchronized   │    │  items       │
└──────────────┘    └─────────────────┘    └──────────────┘

Synchronization:
- Mutex protects buffer access
- not_full condition: producers wait if buffer full
- not_empty condition: consumers wait if buffer empty
```

### Dining Philosophers Solution

```
        [P0]
       /    \
    (F0)    (F1)
     /        \
  [P4]        [P1]
     \        /
    (F4)    (F2)
       \    /
        [P3]
          |
        (F3)
          |
        [P2]

Deadlock Prevention: Resource Ordering
- Always acquire lower-numbered fork first
- Breaks circular wait condition
- Guarantees deadlock-free execution
```

## Usage Examples

### Memory Management

```python
from memory_manager import MemoryManager, PageReplacementAlgorithm

# Create memory manager with 4 frames using LRU
mm = MemoryManager(
    num_frames=4,
    algorithm=PageReplacementAlgorithm.LRU
)

# Allocate pages for process 1
mm.allocate_page(process_id=1, page_id=0)
mm.allocate_page(process_id=1, page_id=1)

# Access a page (updates LRU order)
mm.access_page(process_id=1, page_id=0)

# View metrics
print(mm.metrics.get_summary())
```

### Process Synchronization

```python
from synchronization import Mutex, ProducerConsumer

# Using Mutex
mutex = Mutex("shared_resource")
mutex.acquire(thread_id=1, thread_name="Worker-1")
# Critical section
mutex.release(thread_id=1, thread_name="Worker-1")

# Producer-Consumer simulation
pc = ProducerConsumer(
    buffer_size=5,
    num_producers=2,
    num_consumers=2,
    items_per_producer=10
)
pc.run()  # Runs the simulation
```

## Performance Metrics

### Memory Management Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| Page Fault Rate | Percentage of accesses causing faults | faults / total_accesses |
| Hit Ratio | Percentage of successful accesses | hits / total_accesses |
| Memory Utilization | Frames in use | used_frames / total_frames |

### Synchronization Metrics

| Metric | Description |
|--------|-------------|
| Lock Contentions | Times threads had to wait for locks |
| Items Produced/Consumed | Throughput measurement |
| Deadlocks Prevented | Resource ordering interventions |

## Error Handling

| Error | Response |
|-------|----------|
| Page not in memory | Page fault triggered, load from disk |
| Memory full | Page replacement algorithm invoked |
| Invalid mutex release | RuntimeError raised |
| Buffer full (producer) | Producer waits on condition |
| Buffer empty (consumer) | Consumer waits on condition |

## Algorithm Comparison

### FIFO vs LRU

| Aspect | FIFO | LRU |
|--------|------|-----|
| Complexity | O(1) | O(1) with OrderedDict |
| Belady's Anomaly | Yes | No |
| Temporal Locality | Poor | Good |
| Implementation | Simple queue | Access tracking |
| Best For | Predictable access | Random access |

### When to Use Each Algorithm

**FIFO:**
- Simple workloads
- Sequential access patterns
- Memory-constrained systems

**LRU:**
- General-purpose workloads
- Programs with temporal locality
- Database buffer pools
