#!/usr/bin/env python3
"""
Scheduler Module for Deliverable 2

This module implements Round-Robin and Priority-Based scheduling algorithms
for process management simulation.
"""

import heapq
import time
import threading
from collections import deque
from typing import List, Optional, Callable, Dict
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from process import Process, ProcessState, ProcessMetrics


class SchedulerType(Enum):
    """Types of scheduling algorithms."""
    ROUND_ROBIN = "Round-Robin"
    PRIORITY = "Priority-Based"


@dataclass
class SchedulerMetrics:
    """Aggregate metrics for scheduler performance analysis."""
    algorithm: str = ""
    total_processes: int = 0
    completed_processes: int = 0
    total_execution_time: float = 0.0
    
    # Average metrics
    avg_waiting_time: float = 0.0
    avg_turnaround_time: float = 0.0
    avg_response_time: float = 0.0
    
    # Individual process metrics
    process_metrics: List[Dict] = field(default_factory=list)
    
    # Scheduling events log
    events: List[str] = field(default_factory=list)
    
    def calculate_averages(self, processes: List[Process]):
        """Calculate average metrics from completed processes."""
        completed = [p for p in processes if p.state == ProcessState.COMPLETED]
        self.completed_processes = len(completed)
        
        if not completed:
            return
        
        total_waiting = sum(p.metrics.waiting_time for p in completed)
        total_turnaround = sum(p.metrics.turnaround_time for p in completed)
        total_response = sum(p.metrics.response_time or 0 for p in completed)
        
        self.avg_waiting_time = total_waiting / len(completed)
        self.avg_turnaround_time = total_turnaround / len(completed)
        self.avg_response_time = total_response / len(completed)
        
        # Store individual metrics
        for p in completed:
            self.process_metrics.append({
                'pid': p.pid,
                'name': p.name,
                'priority': p.priority,
                'burst_time': p.burst_time,
                'waiting_time': p.metrics.waiting_time,
                'turnaround_time': p.metrics.turnaround_time,
                'response_time': p.metrics.response_time
            })
    
    def add_event(self, event: str):
        """Add a scheduling event to the log."""
        timestamp = time.time()
        self.events.append(f"[{timestamp:.3f}] {event}")
    
    def get_summary(self) -> str:
        """Get a formatted summary of the metrics."""
        lines = [
            f"\n{'='*60}",
            f"Scheduler Performance Summary: {self.algorithm}",
            f"{'='*60}",
            f"Total Processes: {self.total_processes}",
            f"Completed Processes: {self.completed_processes}",
            f"Total Execution Time: {self.total_execution_time:.3f}s",
            f"",
            f"Average Metrics:",
            f"  - Waiting Time:    {self.avg_waiting_time:.3f}s",
            f"  - Turnaround Time: {self.avg_turnaround_time:.3f}s",
            f"  - Response Time:   {self.avg_response_time:.3f}s",
            f"{'='*60}",
        ]
        return '\n'.join(lines)
    
    def get_detailed_report(self) -> str:
        """Get a detailed report with per-process metrics."""
        lines = [self.get_summary(), "\nPer-Process Metrics:"]
        lines.append(f"{'PID':<5} {'Name':<15} {'Pri':<4} {'Burst':<8} {'Wait':<8} {'Turn':<8} {'Resp':<8}")
        lines.append("-" * 60)
        
        for pm in self.process_metrics:
            lines.append(
                f"{pm['pid']:<5} {pm['name']:<15} {pm['priority']:<4} "
                f"{pm['burst_time']:<8.3f} {pm['waiting_time']:<8.3f} "
                f"{pm['turnaround_time']:<8.3f} {pm['response_time'] or 0:<8.3f}"
            )
        
        return '\n'.join(lines)


class BaseScheduler(ABC):
    """Abstract base class for schedulers."""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the scheduler.
        
        Args:
            callback: Optional callback function for status updates
        """
        self.processes: List[Process] = []
        self.completed: List[Process] = []
        self.current_process: Optional[Process] = None
        self.running = False
        self.paused = False
        self.metrics = SchedulerMetrics()
        self.callback = callback or print
        self._lock = threading.Lock()
        self._start_time: float = 0.0
        self._next_pid = 1
    
    @abstractmethod
    def schedule_next(self) -> Optional[Process]:
        """Select the next process to run. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def add_process(self, process: Process):
        """Add a process to the scheduler. Must be implemented by subclasses."""
        pass
    
    def generate_pid(self) -> int:
        """Generate a unique process ID."""
        pid = self._next_pid
        self._next_pid += 1
        return pid
    
    def create_process(self, name: str, burst_time: float, priority: int = 0) -> Process:
        """
        Create and add a new process.
        
        Args:
            name: Process name
            burst_time: CPU burst time in seconds
            priority: Process priority (lower = higher priority)
            
        Returns:
            The created process
        """
        process = Process(
            pid=self.generate_pid(),
            name=name,
            burst_time=burst_time,
            priority=priority,
            arrival_time=time.time()
        )
        self.add_process(process)
        return process
    
    def log(self, message: str):
        """Log a message and add to metrics."""
        self.metrics.add_event(message)
        if self.callback:
            self.callback(message)
    
    def get_all_processes(self) -> List[Process]:
        """Get all processes (pending and completed)."""
        return self.processes + self.completed
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
    
    def pause(self):
        """Pause the scheduler."""
        self.paused = True
    
    def resume(self):
        """Resume the scheduler."""
        self.paused = False


class RoundRobinScheduler(BaseScheduler):
    """
    Round-Robin Scheduler implementation.
    
    Each process gets a fixed time quantum. After the quantum expires,
    the process is moved to the back of the queue and the next process runs.
    """
    
    def __init__(self, time_quantum: float = 1.0, 
                 callback: Optional[Callable[[str], None]] = None):
        """
        Initialize Round-Robin scheduler.
        
        Args:
            time_quantum: Time slice for each process in seconds
            callback: Optional callback for status updates
        """
        super().__init__(callback)
        self.time_quantum = time_quantum
        self.ready_queue: deque = deque()
        self.metrics.algorithm = f"Round-Robin (quantum={time_quantum}s)"
    
    def set_time_quantum(self, quantum: float):
        """Set a new time quantum."""
        self.time_quantum = quantum
        self.metrics.algorithm = f"Round-Robin (quantum={quantum}s)"
        self.log(f"Time quantum set to {quantum}s")
    
    def add_process(self, process: Process):
        """Add a process to the ready queue."""
        with self._lock:
            process.state = ProcessState.READY
            self.processes.append(process)
            self.ready_queue.append(process)
            self.metrics.total_processes += 1
            self.log(f"Process added: {process.name} (PID: {process.pid}, Burst: {process.burst_time}s)")
    
    def schedule_next(self) -> Optional[Process]:
        """Get the next process from the front of the queue."""
        with self._lock:
            while self.ready_queue:
                process = self.ready_queue.popleft()
                if not process.is_complete():
                    return process
            return None
    
    def run(self, blocking: bool = True):
        """
        Run the Round-Robin scheduler.
        
        Args:
            blocking: If True, blocks until all processes complete
        """
        self.running = True
        self._start_time = time.time()
        self.log(f"Starting Round-Robin Scheduler (quantum={self.time_quantum}s)")
        
        def scheduler_loop():
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Get next process
                process = self.schedule_next()
                
                if process is None:
                    if not self.ready_queue:
                        # All processes completed
                        break
                    time.sleep(0.1)
                    continue
                
                self.current_process = process
                current_time = time.time()
                
                # Start/resume process execution
                process.start_execution(current_time)
                self.log(f"Running: {process.name} (PID: {process.pid}, Remaining: {process.remaining_time:.2f}s)")
                
                # Execute for time quantum or until completion
                executed_time = process.execute(self.time_quantum)
                
                current_time = time.time()
                
                if process.is_complete():
                    # Process completed
                    process.complete(current_time)
                    self.completed.append(process)
                    self.log(f"Completed: {process.name} (PID: {process.pid})")
                else:
                    # Process preempted, add back to queue
                    process.state = ProcessState.READY
                    with self._lock:
                        self.ready_queue.append(process)
                    self.log(f"Preempted: {process.name} (PID: {process.pid}, Remaining: {process.remaining_time:.2f}s)")
                
                self.current_process = None
            
            # Calculate final metrics
            self.metrics.total_execution_time = time.time() - self._start_time
            self.metrics.calculate_averages(self.processes)
            self.running = False
            self.log("Round-Robin Scheduler finished")
        
        if blocking:
            scheduler_loop()
        else:
            thread = threading.Thread(target=scheduler_loop, daemon=True)
            thread.start()
            return thread


class PriorityScheduler(BaseScheduler):
    """
    Priority-Based Scheduler implementation with preemption.
    
    Processes are scheduled based on priority (lower number = higher priority).
    Higher priority processes preempt lower priority ones.
    """
    
    def __init__(self, preemptive: bool = True,
                 callback: Optional[Callable[[str], None]] = None):
        """
        Initialize Priority scheduler.
        
        Args:
            preemptive: If True, higher priority processes preempt running ones
            callback: Optional callback for status updates
        """
        super().__init__(callback)
        self.preemptive = preemptive
        self.priority_queue: List[Process] = []  # Min-heap
        self.metrics.algorithm = f"Priority-Based ({'Preemptive' if preemptive else 'Non-preemptive'})"
        self._preempt_flag = False
        self._check_interval = 0.1  # How often to check for preemption
    
    def add_process(self, process: Process):
        """Add a process to the priority queue."""
        with self._lock:
            process.state = ProcessState.READY
            self.processes.append(process)
            heapq.heappush(self.priority_queue, process)
            self.metrics.total_processes += 1
            self.log(f"Process added: {process.name} (PID: {process.pid}, Priority: {process.priority}, Burst: {process.burst_time}s)")
            
            # Check if we need to preempt current process
            if (self.preemptive and self.current_process and 
                process.priority < self.current_process.priority):
                self._preempt_flag = True
                self.log(f"Preemption triggered: {process.name} (Pri: {process.priority}) > {self.current_process.name} (Pri: {self.current_process.priority})")
    
    def schedule_next(self) -> Optional[Process]:
        """Get the highest priority process."""
        with self._lock:
            while self.priority_queue:
                process = heapq.heappop(self.priority_queue)
                if not process.is_complete():
                    return process
            return None
    
    def _should_preempt(self) -> bool:
        """Check if current process should be preempted."""
        if not self.preemptive or not self.current_process:
            return False
        
        with self._lock:
            if self.priority_queue:
                highest_priority = self.priority_queue[0]
                return highest_priority.priority < self.current_process.priority
        return False
    
    def run(self, blocking: bool = True):
        """
        Run the Priority scheduler.
        
        Args:
            blocking: If True, blocks until all processes complete
        """
        self.running = True
        self._start_time = time.time()
        self.log(f"Starting Priority Scheduler ({'Preemptive' if self.preemptive else 'Non-preemptive'})")
        
        def scheduler_loop():
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Get next process
                process = self.schedule_next()
                
                if process is None:
                    if not self.priority_queue:
                        # All processes completed
                        break
                    time.sleep(0.1)
                    continue
                
                self.current_process = process
                self._preempt_flag = False
                current_time = time.time()
                
                # Start/resume process execution
                process.start_execution(current_time)
                self.log(f"Running: {process.name} (PID: {process.pid}, Priority: {process.priority}, Remaining: {process.remaining_time:.2f}s)")
                
                # Execute in small intervals to allow preemption checking
                while process.remaining_time > 0 and self.running:
                    if self._preempt_flag or self._should_preempt():
                        # Preempt current process
                        process.preempt()
                        with self._lock:
                            heapq.heappush(self.priority_queue, process)
                        self.log(f"Preempted: {process.name} (PID: {process.pid})")
                        self._preempt_flag = False
                        break
                    
                    # Execute for a small interval
                    exec_time = min(self._check_interval, process.remaining_time)
                    time.sleep(exec_time)
                    process.remaining_time -= exec_time
                    process.metrics.remaining_time = process.remaining_time
                
                current_time = time.time()
                
                if process.is_complete():
                    # Process completed
                    process.complete(current_time)
                    self.completed.append(process)
                    self.log(f"Completed: {process.name} (PID: {process.pid})")
                
                self.current_process = None
            
            # Calculate final metrics
            self.metrics.total_execution_time = time.time() - self._start_time
            self.metrics.calculate_averages(self.processes)
            self.running = False
            self.log("Priority Scheduler finished")
        
        if blocking:
            scheduler_loop()
        else:
            thread = threading.Thread(target=scheduler_loop, daemon=True)
            thread.start()
            return thread


def create_scheduler(scheduler_type: SchedulerType, **kwargs) -> BaseScheduler:
    """
    Factory function to create a scheduler.
    
    Args:
        scheduler_type: Type of scheduler to create
        **kwargs: Additional arguments for the scheduler
        
    Returns:
        A scheduler instance
    """
    if scheduler_type == SchedulerType.ROUND_ROBIN:
        return RoundRobinScheduler(**kwargs)
    elif scheduler_type == SchedulerType.PRIORITY:
        return PriorityScheduler(**kwargs)
    else:
        raise ValueError(f"Unknown scheduler type: {scheduler_type}")
