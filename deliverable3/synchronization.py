#!/usr/bin/env python3
"""
Synchronization Module for Deliverable 3

This module implements process synchronization primitives and
classical synchronization problems:
- Mutex (Mutual Exclusion Lock)
- Semaphore (Counting Semaphore)
- Producer-Consumer Problem
- Dining Philosophers Problem
"""

import threading
import time
import random
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from collections import deque


class SyncEventType(Enum):
    """Types of synchronization events."""
    ACQUIRE = "Acquire"
    RELEASE = "Release"
    WAIT = "Wait"
    SIGNAL = "Signal"
    PRODUCE = "Produce"
    CONSUME = "Consume"
    THINKING = "Thinking"
    EATING = "Eating"
    WAITING = "Waiting"
    PICKUP = "Pickup"
    PUTDOWN = "Putdown"


@dataclass
class SyncEvent:
    """Represents a synchronization event."""
    timestamp: float
    event_type: SyncEventType
    entity_id: int
    entity_name: str
    resource: str
    details: str = ""
    
    def __str__(self) -> str:
        return f"[{self.timestamp:.3f}] {self.entity_name}: {self.event_type.value} - {self.details}"


@dataclass
class SyncMetrics:
    """Tracks synchronization metrics."""
    total_acquires: int = 0
    total_releases: int = 0
    total_waits: int = 0
    total_contentions: int = 0
    items_produced: int = 0
    items_consumed: int = 0
    deadlocks_prevented: int = 0
    
    events: List[SyncEvent] = field(default_factory=list)
    
    def log_event(self, event: SyncEvent):
        """Log a synchronization event."""
        self.events.append(event)
    
    def get_summary(self) -> str:
        """Get a summary of synchronization metrics."""
        lines = [
            "\n" + "=" * 50,
            "Synchronization Metrics Summary",
            "=" * 50,
            f"Total Lock Acquires:    {self.total_acquires}",
            f"Total Lock Releases:    {self.total_releases}",
            f"Total Wait Operations:  {self.total_waits}",
            f"Total Contentions:      {self.total_contentions}",
            f"Items Produced:         {self.items_produced}",
            f"Items Consumed:         {self.items_consumed}",
            f"Deadlocks Prevented:    {self.deadlocks_prevented}",
            "=" * 50,
        ]
        return '\n'.join(lines)


class Mutex:
    """
    Mutex (Mutual Exclusion Lock) implementation.
    
    Ensures only one thread can access a critical section at a time.
    """
    
    def __init__(self, name: str = "mutex", callback: Callable = None):
        """Initialize the mutex."""
        self.name = name
        self._lock = threading.Lock()
        self._owner: Optional[int] = None
        self.callback = callback or print
        self.metrics = SyncMetrics()
    
    def acquire(self, thread_id: int, thread_name: str = "Thread", blocking: bool = True) -> bool:
        """Acquire the mutex."""
        if self._lock.locked():
            self.metrics.total_contentions += 1
            event = SyncEvent(
                timestamp=time.time(),
                event_type=SyncEventType.WAIT,
                entity_id=thread_id,
                entity_name=thread_name,
                resource=self.name,
                details=f"Waiting for mutex '{self.name}'"
            )
            self.metrics.log_event(event)
            self.callback(str(event))
        
        acquired = self._lock.acquire(blocking=blocking)
        
        if acquired:
            self._owner = thread_id
            self.metrics.total_acquires += 1
            event = SyncEvent(
                timestamp=time.time(),
                event_type=SyncEventType.ACQUIRE,
                entity_id=thread_id,
                entity_name=thread_name,
                resource=self.name,
                details=f"Acquired mutex '{self.name}'"
            )
            self.metrics.log_event(event)
            self.callback(str(event))
        
        return acquired
    
    def release(self, thread_id: int, thread_name: str = "Thread"):
        """Release the mutex."""
        if self._owner != thread_id:
            raise RuntimeError(f"Thread {thread_id} cannot release mutex owned by {self._owner}")
        
        self._owner = None
        self._lock.release()
        self.metrics.total_releases += 1
        
        event = SyncEvent(
            timestamp=time.time(),
            event_type=SyncEventType.RELEASE,
            entity_id=thread_id,
            entity_name=thread_name,
            resource=self.name,
            details=f"Released mutex '{self.name}'"
        )
        self.metrics.log_event(event)
        self.callback(str(event))
    
    def is_locked(self) -> bool:
        """Check if mutex is currently locked."""
        return self._lock.locked()


class Semaphore:
    """
    Counting Semaphore implementation.
    
    Allows a limited number of threads to access a resource simultaneously.
    """
    
    def __init__(self, initial_value: int = 1, name: str = "semaphore", 
                 callback: Callable = None):
        """Initialize the semaphore."""
        self.name = name
        self._value = initial_value
        self._max_value = initial_value
        self._semaphore = threading.Semaphore(initial_value)
        self._lock = threading.Lock()
        self.callback = callback or print
        self.metrics = SyncMetrics()
    
    @property
    def value(self) -> int:
        """Get current semaphore value."""
        return self._value
    
    def wait(self, thread_id: int, thread_name: str = "Thread", blocking: bool = True) -> bool:
        """Wait (P operation) on the semaphore."""
        with self._lock:
            if self._value <= 0:
                self.metrics.total_contentions += 1
                event = SyncEvent(
                    timestamp=time.time(),
                    event_type=SyncEventType.WAIT,
                    entity_id=thread_id,
                    entity_name=thread_name,
                    resource=self.name,
                    details=f"Waiting on semaphore '{self.name}' (value={self._value})"
                )
                self.metrics.log_event(event)
                self.callback(str(event))
        
        acquired = self._semaphore.acquire(blocking=blocking)
        
        if acquired:
            with self._lock:
                self._value -= 1
                self.metrics.total_waits += 1
                
            event = SyncEvent(
                timestamp=time.time(),
                event_type=SyncEventType.ACQUIRE,
                entity_id=thread_id,
                entity_name=thread_name,
                resource=self.name,
                details=f"Acquired semaphore '{self.name}' (value={self._value})"
            )
            self.metrics.log_event(event)
            self.callback(str(event))
        
        return acquired
    
    def signal(self, thread_id: int, thread_name: str = "Thread"):
        """Signal (V operation) the semaphore."""
        with self._lock:
            self._value += 1
            if self._value > self._max_value:
                self._value = self._max_value
        
        self._semaphore.release()
        self.metrics.total_releases += 1
        
        event = SyncEvent(
            timestamp=time.time(),
            event_type=SyncEventType.SIGNAL,
            entity_id=thread_id,
            entity_name=thread_name,
            resource=self.name,
            details=f"Signaled semaphore '{self.name}' (value={self._value})"
        )
        self.metrics.log_event(event)
        self.callback(str(event))


class BoundedBuffer:
    """Thread-safe bounded buffer for Producer-Consumer problem."""
    
    def __init__(self, capacity: int, callback: Callable = None):
        """Initialize the bounded buffer."""
        self.capacity = capacity
        self.buffer: deque = deque()
        self.callback = callback or print
        
        self._mutex = threading.Lock()
        self._not_empty = threading.Condition(self._mutex)
        self._not_full = threading.Condition(self._mutex)
        
        self.items_produced = 0
        self.items_consumed = 0
    
    def put(self, item: Any, producer_id: int, producer_name: str) -> bool:
        """Add an item to the buffer."""
        with self._not_full:
            while len(self.buffer) >= self.capacity:
                self.callback(f"  {producer_name}: Buffer full, waiting...")
                self._not_full.wait()
            
            self.buffer.append(item)
            self.items_produced += 1
            self.callback(f"  {producer_name}: Produced item {item} (buffer: {len(self.buffer)}/{self.capacity})")
            
            self._not_empty.notify()
            return True
    
    def get(self, consumer_id: int, consumer_name: str) -> Any:
        """Remove and return an item from the buffer."""
        with self._not_empty:
            while len(self.buffer) == 0:
                self.callback(f"  {consumer_name}: Buffer empty, waiting...")
                self._not_empty.wait()
            
            item = self.buffer.popleft()
            self.items_consumed += 1
            self.callback(f"  {consumer_name}: Consumed item {item} (buffer: {len(self.buffer)}/{self.capacity})")
            
            self._not_full.notify()
            return item
    
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self.buffer) == 0
    
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return len(self.buffer) >= self.capacity


class ProducerConsumer:
    """Producer-Consumer synchronization problem implementation."""
    
    def __init__(self, buffer_size: int = 5, num_producers: int = 2, 
                 num_consumers: int = 2, items_per_producer: int = 5,
                 callback: Callable = None):
        """Initialize the Producer-Consumer simulation."""
        self.buffer_size = buffer_size
        self.num_producers = num_producers
        self.num_consumers = num_consumers
        self.items_per_producer = items_per_producer
        self.callback = callback or print
        
        self.buffer = BoundedBuffer(buffer_size, callback)
        
        self.running = False
        self.total_items = num_producers * items_per_producer
        self.produced_count = 0
        self.consumed_count = 0
        self._count_lock = threading.Lock()
        
        self.producers: List[threading.Thread] = []
        self.consumers: List[threading.Thread] = []
        
        self.metrics = SyncMetrics()
    
    def _producer_task(self, producer_id: int):
        """Producer thread function."""
        name = f"Producer-{producer_id}"
        
        for i in range(self.items_per_producer):
            if not self.running:
                break
            
            time.sleep(random.uniform(0.1, 0.3))
            
            item = f"P{producer_id}-Item{i}"
            self.buffer.put(item, producer_id, name)
            
            with self._count_lock:
                self.produced_count += 1
                self.metrics.items_produced += 1
    
    def _consumer_task(self, consumer_id: int):
        """Consumer thread function."""
        name = f"Consumer-{consumer_id}"
        
        while self.running:
            with self._count_lock:
                if self.consumed_count >= self.total_items:
                    break
            
            with self._count_lock:
                if self.produced_count >= self.total_items and self.buffer.is_empty():
                    break
            
            try:
                item = self.buffer.get(consumer_id, name)
                
                with self._count_lock:
                    self.consumed_count += 1
                    self.metrics.items_consumed += 1
                
                time.sleep(random.uniform(0.1, 0.2))
            except Exception:
                break
    
    def run(self, blocking: bool = True):
        """Run the Producer-Consumer simulation."""
        self.running = True
        self.callback(f"\n{'='*50}")
        self.callback("Starting Producer-Consumer Simulation")
        self.callback(f"Buffer Size: {self.buffer_size}")
        self.callback(f"Producers: {self.num_producers}, Consumers: {self.num_consumers}")
        self.callback(f"Total Items: {self.total_items}")
        self.callback(f"{'='*50}\n")
        
        for i in range(self.num_producers):
            t = threading.Thread(target=self._producer_task, args=(i,))
            t.daemon = True
            self.producers.append(t)
            t.start()
        
        for i in range(self.num_consumers):
            t = threading.Thread(target=self._consumer_task, args=(i,))
            t.daemon = True
            self.consumers.append(t)
            t.start()
        
        if blocking:
            for t in self.producers:
                t.join()
            
            while self.consumed_count < self.total_items:
                time.sleep(0.1)
            
            self.running = False
            
            for t in self.consumers:
                t.join(timeout=1.0)
            
            self.callback(f"\n{'='*50}")
            self.callback("Producer-Consumer Simulation Complete")
            self.callback(f"Items Produced: {self.produced_count}")
            self.callback(f"Items Consumed: {self.consumed_count}")
            self.callback(f"{'='*50}")
    
    def stop(self):
        """Stop the simulation."""
        self.running = False


class Fork:
    """Represents a fork in the Dining Philosophers problem."""
    
    def __init__(self, fork_id: int):
        self.fork_id = fork_id
        self._lock = threading.Lock()
        self.holder: Optional[int] = None
    
    def pickup(self, philosopher_id: int) -> bool:
        """Try to pick up the fork (non-blocking)."""
        acquired = self._lock.acquire(blocking=False)
        if acquired:
            self.holder = philosopher_id
        return acquired
    
    def pickup_blocking(self, philosopher_id: int):
        """Pick up the fork (blocking)."""
        self._lock.acquire()
        self.holder = philosopher_id
    
    def putdown(self, philosopher_id: int):
        """Put down the fork."""
        if self.holder == philosopher_id:
            self.holder = None
            self._lock.release()
    
    def is_available(self) -> bool:
        """Check if fork is available."""
        return not self._lock.locked()


class DiningPhilosophers:
    """
    Dining Philosophers synchronization problem implementation.
    
    Uses resource ordering to prevent deadlock.
    """
    
    def __init__(self, num_philosophers: int = 5, meals_per_philosopher: int = 3,
                 callback: Callable = None):
        """Initialize the Dining Philosophers simulation."""
        self.num_philosophers = num_philosophers
        self.meals_per_philosopher = meals_per_philosopher
        self.callback = callback or print
        
        self.forks = [Fork(i) for i in range(num_philosophers)]
        
        self.running = False
        self.meals_eaten: Dict[int, int] = {i: 0 for i in range(num_philosophers)}
        self._lock = threading.Lock()
        
        self.philosophers: List[threading.Thread] = []
        
        self.metrics = SyncMetrics()
        self.total_thinking_time = 0
        self.total_eating_time = 0
        self.total_waiting_time = 0
    
    def _get_fork_order(self, philosopher_id: int) -> tuple:
        """Get forks in order to prevent deadlock (resource ordering)."""
        left_fork = philosopher_id
        right_fork = (philosopher_id + 1) % self.num_philosophers
        
        if left_fork < right_fork:
            return (left_fork, right_fork)
        else:
            return (right_fork, left_fork)
    
    def _philosopher_task(self, philosopher_id: int):
        """Philosopher thread function."""
        name = f"Philosopher-{philosopher_id}"
        first_fork, second_fork = self._get_fork_order(philosopher_id)
        
        while self.running and self.meals_eaten[philosopher_id] < self.meals_per_philosopher:
            think_time = random.uniform(0.1, 0.3)
            self.callback(f"  {name}: Thinking...")
            time.sleep(think_time)
            
            with self._lock:
                self.total_thinking_time += think_time
            
            self.callback(f"  {name}: Hungry, trying to pick up forks {first_fork} and {second_fork}")
            
            wait_start = time.time()
            
            self.forks[first_fork].pickup_blocking(philosopher_id)
            self.callback(f"  {name}: Picked up fork {first_fork}")
            self.metrics.deadlocks_prevented += 1
            
            self.forks[second_fork].pickup_blocking(philosopher_id)
            self.callback(f"  {name}: Picked up fork {second_fork}")
            
            wait_time = time.time() - wait_start
            with self._lock:
                self.total_waiting_time += wait_time
            
            eat_time = random.uniform(0.1, 0.2)
            self.callback(f"  {name}: Eating (meal {self.meals_eaten[philosopher_id] + 1})")
            time.sleep(eat_time)
            
            with self._lock:
                self.meals_eaten[philosopher_id] += 1
                self.total_eating_time += eat_time
            
            self.forks[second_fork].putdown(philosopher_id)
            self.forks[first_fork].putdown(philosopher_id)
            self.callback(f"  {name}: Put down forks {first_fork} and {second_fork}")
        
        self.callback(f"  {name}: Finished all meals!")
    
    def run(self, blocking: bool = True):
        """Run the Dining Philosophers simulation."""
        self.running = True
        self.callback(f"\n{'='*50}")
        self.callback("Starting Dining Philosophers Simulation")
        self.callback(f"Philosophers: {self.num_philosophers}")
        self.callback(f"Meals per Philosopher: {self.meals_per_philosopher}")
        self.callback("Strategy: Resource Ordering (prevents deadlock)")
        self.callback(f"{'='*50}\n")
        
        for i in range(self.num_philosophers):
            t = threading.Thread(target=self._philosopher_task, args=(i,))
            t.daemon = True
            self.philosophers.append(t)
            t.start()
        
        if blocking:
            for t in self.philosophers:
                t.join()
            
            self.running = False
            
            self.callback(f"\n{'='*50}")
            self.callback("Dining Philosophers Simulation Complete")
            self.callback(f"Total Meals Eaten: {sum(self.meals_eaten.values())}")
            self.callback(f"Total Thinking Time: {self.total_thinking_time:.2f}s")
            self.callback(f"Total Eating Time: {self.total_eating_time:.2f}s")
            self.callback(f"Total Waiting Time: {self.total_waiting_time:.2f}s")
            self.callback("No deadlocks occurred (resource ordering strategy)")
            self.callback(f"{'='*50}")
    
    def stop(self):
        """Stop the simulation."""
        self.running = False
    
    def get_status(self) -> str:
        """Get current status of all philosophers."""
        lines = ["\nPhilosopher Status:"]
        for i in range(self.num_philosophers):
            meals = self.meals_eaten[i]
            lines.append(f"  Philosopher {i}: {meals}/{self.meals_per_philosopher} meals")
        return '\n'.join(lines)
