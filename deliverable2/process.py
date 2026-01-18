#!/usr/bin/env python3
"""
Process Module for Deliverable 2

This module defines the Process class and related data structures
for process scheduling simulation.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import time


class ProcessState(Enum):
    """Enum representing possible process states."""
    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    COMPLETED = "Completed"
    PREEMPTED = "Preempted"


@dataclass
class ProcessMetrics:
    """Tracks performance metrics for a process."""
    arrival_time: float = 0.0          # When the process arrived in the system
    start_time: Optional[float] = None  # When the process first started executing
    completion_time: Optional[float] = None  # When the process completed
    total_burst_time: float = 0.0      # Total CPU time needed
    remaining_time: float = 0.0        # Remaining CPU time needed
    
    # Calculated metrics
    waiting_time: float = 0.0          # Time spent waiting in ready queue
    turnaround_time: float = 0.0       # Total time from arrival to completion
    response_time: Optional[float] = None  # Time from arrival to first execution
    
    def calculate_metrics(self):
        """Calculate derived metrics after process completion."""
        if self.completion_time is not None and self.arrival_time is not None:
            self.turnaround_time = self.completion_time - self.arrival_time
            self.waiting_time = self.turnaround_time - self.total_burst_time
        
        if self.start_time is not None and self.arrival_time is not None:
            self.response_time = self.start_time - self.arrival_time


@dataclass
class Process:
    """Represents a process in the scheduling simulation."""
    pid: int
    name: str
    burst_time: float  # Total CPU time needed (in seconds)
    priority: int = 0  # Lower number = higher priority (0 is highest)
    arrival_time: float = field(default_factory=time.time)
    
    # State tracking
    state: ProcessState = ProcessState.NEW
    remaining_time: float = field(init=False)
    
    # Metrics
    metrics: ProcessMetrics = field(default_factory=ProcessMetrics)
    
    # Internal tracking
    _first_run: bool = field(default=True, repr=False)
    _last_scheduled: float = field(default=0.0, repr=False)
    
    def __post_init__(self):
        """Initialize derived fields after dataclass initialization."""
        self.remaining_time = self.burst_time
        self.metrics.arrival_time = self.arrival_time
        self.metrics.total_burst_time = self.burst_time
        self.metrics.remaining_time = self.burst_time
    
    def start_execution(self, current_time: float):
        """Called when the process starts or resumes execution."""
        self.state = ProcessState.RUNNING
        self._last_scheduled = current_time
        
        if self._first_run:
            self.metrics.start_time = current_time
            self._first_run = False
    
    def execute(self, time_slice: float) -> float:
        """
        Simulate process execution for a given time slice.
        
        Args:
            time_slice: Maximum time to execute
            
        Returns:
            Actual time executed
        """
        execution_time = min(time_slice, self.remaining_time)
        
        # Simulate execution
        time.sleep(execution_time)
        
        self.remaining_time -= execution_time
        self.metrics.remaining_time = self.remaining_time
        
        return execution_time
    
    def complete(self, current_time: float):
        """Called when the process completes execution."""
        self.state = ProcessState.COMPLETED
        self.metrics.completion_time = current_time
        self.metrics.calculate_metrics()
    
    def preempt(self):
        """Called when the process is preempted."""
        self.state = ProcessState.PREEMPTED
    
    def is_complete(self) -> bool:
        """Check if the process has completed execution."""
        return self.remaining_time <= 0
    
    def __lt__(self, other: 'Process') -> bool:
        """Compare processes by priority (for heap operations)."""
        if self.priority == other.priority:
            # FCFS for same priority
            return self.arrival_time < other.arrival_time
        return self.priority < other.priority
    
    def __str__(self) -> str:
        """String representation of the process."""
        return (f"PID: {self.pid} | {self.name} | Priority: {self.priority} | "
                f"Burst: {self.burst_time:.2f}s | Remaining: {self.remaining_time:.2f}s | "
                f"State: {self.state.value}")
    
    def get_status_line(self) -> str:
        """Get a formatted status line for display."""
        progress = ((self.burst_time - self.remaining_time) / self.burst_time) * 100
        bar_length = 20
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        return (f"[{self.pid}] {self.name:<15} Pri:{self.priority} "
                f"[{bar}] {progress:5.1f}% | {self.state.value}")
