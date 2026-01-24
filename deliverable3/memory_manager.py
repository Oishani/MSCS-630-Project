#!/usr/bin/env python3
"""
Memory Manager Module for Deliverable 3

This module implements a paging system with:
- Fixed-size page frames
- Page allocation and deallocation
- FIFO and LRU page replacement algorithms
- Page fault tracking
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Deque
from collections import deque, OrderedDict
import time
import threading


class PageReplacementAlgorithm(Enum):
    """Page replacement algorithm types."""
    FIFO = "First-In-First-Out"
    LRU = "Least Recently Used"


@dataclass
class Page:
    """Represents a memory page."""
    page_id: int
    process_id: int
    data: any = None
    loaded_time: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    
    def access(self):
        """Update last accessed time."""
        self.last_accessed = time.time()
    
    def __str__(self) -> str:
        return f"Page(id={self.page_id}, process={self.process_id})"


@dataclass
class PageFrame:
    """Represents a physical memory frame."""
    frame_id: int
    page: Optional[Page] = None
    is_free: bool = True
    
    def allocate(self, page: Page):
        """Allocate a page to this frame."""
        self.page = page
        self.is_free = False
    
    def deallocate(self) -> Optional[Page]:
        """Deallocate the page from this frame."""
        old_page = self.page
        self.page = None
        self.is_free = True
        return old_page
    
    def __str__(self) -> str:
        if self.is_free:
            return f"Frame[{self.frame_id}]: Empty"
        return f"Frame[{self.frame_id}]: {self.page}"


@dataclass
class MemoryMetrics:
    """Tracks memory management metrics."""
    total_page_faults: int = 0
    total_page_hits: int = 0
    total_allocations: int = 0
    total_deallocations: int = 0
    page_replacements: int = 0
    
    # Per-process metrics
    process_page_faults: Dict[int, int] = field(default_factory=dict)
    process_memory_usage: Dict[int, int] = field(default_factory=dict)
    
    # Event log
    events: List[str] = field(default_factory=list)
    
    def log_event(self, event: str):
        """Log a memory event."""
        timestamp = time.time()
        self.events.append(f"[{timestamp:.3f}] {event}")
    
    def record_page_fault(self, process_id: int):
        """Record a page fault for a process."""
        self.total_page_faults += 1
        self.process_page_faults[process_id] = self.process_page_faults.get(process_id, 0) + 1
    
    def record_page_hit(self):
        """Record a page hit."""
        self.total_page_hits += 1
    
    def update_memory_usage(self, process_id: int, pages: int):
        """Update memory usage for a process."""
        self.process_memory_usage[process_id] = pages
    
    def get_hit_ratio(self) -> float:
        """Calculate page hit ratio."""
        total = self.total_page_faults + self.total_page_hits
        if total == 0:
            return 0.0
        return self.total_page_hits / total
    
    def get_summary(self) -> str:
        """Get a summary of memory metrics."""
        lines = [
            "\n" + "=" * 55,
            "Memory Management Metrics Summary",
            "=" * 55,
            f"Total Page Faults:    {self.total_page_faults}",
            f"Total Page Hits:      {self.total_page_hits}",
            f"Page Hit Ratio:       {self.get_hit_ratio():.2%}",
            f"Page Replacements:    {self.page_replacements}",
            f"Total Allocations:    {self.total_allocations}",
            f"Total Deallocations:  {self.total_deallocations}",
            "-" * 55,
            "Per-Process Page Faults:",
        ]
        
        for pid, faults in self.process_page_faults.items():
            lines.append(f"  Process {pid}: {faults} faults")
        
        lines.append("-" * 55)
        lines.append("Per-Process Memory Usage (pages):")
        
        for pid, pages in self.process_memory_usage.items():
            lines.append(f"  Process {pid}: {pages} pages")
        
        lines.append("=" * 55)
        return '\n'.join(lines)


class MemoryManager:
    """
    Memory Manager implementing paging with page replacement.
    
    Supports FIFO and LRU page replacement algorithms.
    """
    
    def __init__(self, num_frames: int, page_size: int = 4096,
                 algorithm: PageReplacementAlgorithm = PageReplacementAlgorithm.FIFO,
                 callback: callable = None):
        """
        Initialize the memory manager.
        
        Args:
            num_frames: Number of physical memory frames
            page_size: Size of each page in bytes
            algorithm: Page replacement algorithm to use
            callback: Optional callback for logging events
        """
        self.num_frames = num_frames
        self.page_size = page_size
        self.algorithm = algorithm
        self.callback = callback or print
        
        # Physical memory (frames)
        self.frames: List[PageFrame] = [
            PageFrame(frame_id=i) for i in range(num_frames)
        ]
        
        # Page table: maps (process_id, page_id) -> frame_id
        self.page_table: Dict[Tuple[int, int], int] = {}
        
        # Process page tracking: process_id -> list of page_ids
        self.process_pages: Dict[int, List[int]] = {}
        
        # FIFO queue: order of page loading
        self.fifo_queue: Deque[Tuple[int, int]] = deque()
        
        # LRU tracking: OrderedDict maintains access order
        self.lru_order: OrderedDict[Tuple[int, int], float] = OrderedDict()
        
        # Metrics
        self.metrics = MemoryMetrics()
        
        # Thread safety
        self._lock = threading.Lock()
    
    def log(self, message: str):
        """Log an event."""
        self.metrics.log_event(message)
        if self.callback:
            self.callback(message)
    
    def get_free_frame(self) -> Optional[int]:
        """Find a free frame. Returns frame_id or None."""
        for frame in self.frames:
            if frame.is_free:
                return frame.frame_id
        return None
    
    def get_memory_usage(self) -> Tuple[int, int]:
        """Get current memory usage (used_frames, total_frames)."""
        used = sum(1 for f in self.frames if not f.is_free)
        return used, self.num_frames
    
    def is_memory_full(self) -> bool:
        """Check if all frames are occupied."""
        return all(not f.is_free for f in self.frames)
    
    def _select_victim_fifo(self) -> Tuple[int, int]:
        """Select victim page using FIFO algorithm."""
        return self.fifo_queue[0]  # First in
    
    def _select_victim_lru(self) -> Tuple[int, int]:
        """Select victim page using LRU algorithm."""
        # First item in OrderedDict is least recently used
        return next(iter(self.lru_order))
    
    def _select_victim(self) -> Tuple[int, int]:
        """Select a victim page for replacement based on algorithm."""
        if self.algorithm == PageReplacementAlgorithm.FIFO:
            return self._select_victim_fifo()
        else:  # LRU
            return self._select_victim_lru()
    
    def _evict_page(self, process_id: int, page_id: int) -> int:
        """
        Evict a page from memory.
        
        Args:
            process_id: Process ID of page to evict
            page_id: Page ID to evict
            
        Returns:
            Frame ID that was freed
        """
        key = (process_id, page_id)
        
        if key not in self.page_table:
            raise ValueError(f"Page {page_id} of process {process_id} not in memory")
        
        frame_id = self.page_table[key]
        frame = self.frames[frame_id]
        
        # Deallocate the frame
        evicted_page = frame.deallocate()
        
        # Remove from page table
        del self.page_table[key]
        
        # Remove from tracking structures
        if key in self.fifo_queue:
            self.fifo_queue.remove(key)
        if key in self.lru_order:
            del self.lru_order[key]
        
        # Update process pages
        if process_id in self.process_pages:
            if page_id in self.process_pages[process_id]:
                self.process_pages[process_id].remove(page_id)
        
        self.metrics.total_deallocations += 1
        self.log(f"Evicted: Page {page_id} of Process {process_id} from Frame {frame_id}")
        
        return frame_id
    
    def allocate_page(self, process_id: int, page_id: int, data: any = None) -> int:
        """
        Allocate a page for a process.
        
        Args:
            process_id: Process requesting the page
            page_id: Page number to allocate
            data: Optional data to store in the page
            
        Returns:
            Frame ID where page was allocated
        """
        with self._lock:
            key = (process_id, page_id)
            
            # Check if page is already in memory (page hit)
            if key in self.page_table:
                frame_id = self.page_table[key]
                frame = self.frames[frame_id]
                frame.page.access()
                
                # Update LRU order
                if key in self.lru_order:
                    self.lru_order.move_to_end(key)
                
                self.metrics.record_page_hit()
                self.log(f"Page Hit: Page {page_id} of Process {process_id} in Frame {frame_id}")
                return frame_id
            
            # Page fault - page not in memory
            self.metrics.record_page_fault(process_id)
            self.log(f"Page Fault: Page {page_id} of Process {process_id} not in memory")
            
            # Find a free frame or perform page replacement
            frame_id = self.get_free_frame()
            
            if frame_id is None:
                # Memory is full, need to replace a page
                victim_key = self._select_victim()
                self.log(f"Memory Full: Replacing Page {victim_key[1]} of Process {victim_key[0]}")
                frame_id = self._evict_page(victim_key[0], victim_key[1])
                self.metrics.page_replacements += 1
            
            # Create and allocate the new page
            page = Page(
                page_id=page_id,
                process_id=process_id,
                data=data
            )
            
            frame = self.frames[frame_id]
            frame.allocate(page)
            
            # Update page table
            self.page_table[key] = frame_id
            
            # Update tracking structures
            self.fifo_queue.append(key)
            self.lru_order[key] = time.time()
            
            # Update process pages
            if process_id not in self.process_pages:
                self.process_pages[process_id] = []
            self.process_pages[process_id].append(page_id)
            
            self.metrics.total_allocations += 1
            self.metrics.update_memory_usage(process_id, len(self.process_pages[process_id]))
            
            self.log(f"Allocated: Page {page_id} of Process {process_id} to Frame {frame_id}")
            return frame_id
    
    def access_page(self, process_id: int, page_id: int) -> bool:
        """
        Access a page (for LRU tracking).
        
        Args:
            process_id: Process ID
            page_id: Page ID to access
            
        Returns:
            True if page was in memory (hit), False if fault occurred
        """
        with self._lock:
            key = (process_id, page_id)
            
            if key in self.page_table:
                frame_id = self.page_table[key]
                frame = self.frames[frame_id]
                frame.page.access()
                
                # Update LRU order
                if key in self.lru_order:
                    self.lru_order.move_to_end(key)
                
                self.metrics.record_page_hit()
                return True
            else:
                # Page fault - need to load the page
                self.allocate_page(process_id, page_id)
                return False
    
    def deallocate_process_pages(self, process_id: int):
        """
        Deallocate all pages belonging to a process.
        
        Args:
            process_id: Process ID whose pages to deallocate
        """
        with self._lock:
            if process_id not in self.process_pages:
                return
            
            pages_to_remove = list(self.process_pages[process_id])
            
            for page_id in pages_to_remove:
                key = (process_id, page_id)
                if key in self.page_table:
                    frame_id = self.page_table[key]
                    self.frames[frame_id].deallocate()
                    del self.page_table[key]
                    
                    if key in self.fifo_queue:
                        self.fifo_queue.remove(key)
                    if key in self.lru_order:
                        del self.lru_order[key]
                    
                    self.metrics.total_deallocations += 1
            
            del self.process_pages[process_id]
            self.metrics.update_memory_usage(process_id, 0)
            self.log(f"Deallocated all pages for Process {process_id}")
    
    def get_page_data(self, process_id: int, page_id: int) -> Optional[any]:
        """Get data stored in a page."""
        with self._lock:
            key = (process_id, page_id)
            if key in self.page_table:
                frame_id = self.page_table[key]
                return self.frames[frame_id].page.data
            return None
    
    def set_page_data(self, process_id: int, page_id: int, data: any) -> bool:
        """Set data in a page."""
        with self._lock:
            key = (process_id, page_id)
            if key in self.page_table:
                frame_id = self.page_table[key]
                self.frames[frame_id].page.data = data
                return True
            return False
    
    def set_algorithm(self, algorithm: PageReplacementAlgorithm):
        """Change the page replacement algorithm."""
        self.algorithm = algorithm
        self.log(f"Page replacement algorithm changed to {algorithm.value}")
    
    def get_frame_status(self) -> List[str]:
        """Get status of all frames."""
        status = []
        for frame in self.frames:
            if frame.is_free:
                status.append(f"Frame {frame.frame_id}: [Empty]")
            else:
                page = frame.page
                status.append(f"Frame {frame.frame_id}: Process {page.process_id}, Page {page.page_id}")
        return status
    
    def visualize_memory(self) -> str:
        """Create a visual representation of memory."""
        lines = ["\n┌" + "─" * 40 + "┐"]
        lines.append(f"│{'Physical Memory':^40}│")
        lines.append("├" + "─" * 40 + "┤")
        
        used, total = self.get_memory_usage()
        lines.append(f"│ Used: {used}/{total} frames ({used/total*100:.1f}%)".ljust(41) + "│")
        lines.append(f"│ Algorithm: {self.algorithm.value}".ljust(41) + "│")
        lines.append("├" + "─" * 40 + "┤")
        
        for frame in self.frames:
            if frame.is_free:
                content = f"│ Frame {frame.frame_id}: [ Empty ]".ljust(41) + "│"
            else:
                page = frame.page
                content = f"│ Frame {frame.frame_id}: [P{page.process_id}:Pg{page.page_id}]".ljust(41) + "│"
            lines.append(content)
        
        lines.append("└" + "─" * 40 + "┘")
        return '\n'.join(lines)
    
    def reset(self):
        """Reset the memory manager to initial state."""
        with self._lock:
            for frame in self.frames:
                frame.deallocate()
            
            self.page_table.clear()
            self.process_pages.clear()
            self.fifo_queue.clear()
            self.lru_order.clear()
            self.metrics = MemoryMetrics()
            
            self.log("Memory manager reset")


def create_memory_manager(num_frames: int, algorithm: str = "fifo", 
                          callback: callable = None) -> MemoryManager:
    """
    Factory function to create a memory manager.
    
    Args:
        num_frames: Number of memory frames
        algorithm: "fifo" or "lru"
        callback: Optional logging callback
        
    Returns:
        MemoryManager instance
    """
    algo = PageReplacementAlgorithm.FIFO if algorithm.lower() == "fifo" else PageReplacementAlgorithm.LRU
    return MemoryManager(num_frames=num_frames, algorithm=algo, callback=callback)
