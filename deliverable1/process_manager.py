#!/usr/bin/env python3
"""
Process Manager Module

This module handles process management and job control for the shell,
including:
- Tracking foreground and background processes
- Job status management
- Signal handling for process control
"""

import os
import signal
import subprocess
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime


class JobStatus(Enum):
    """Enum representing possible job statuses."""
    RUNNING = "Running"
    STOPPED = "Stopped"
    COMPLETED = "Completed"
    TERMINATED = "Terminated"


@dataclass
class Job:
    """Represents a job (process) managed by the shell."""
    job_id: int
    pid: int
    command: str
    status: JobStatus
    process: subprocess.Popen
    is_foreground: bool = False
    start_time: datetime = field(default_factory=datetime.now)
    
    def __str__(self) -> str:
        """String representation of the job."""
        fg_indicator = "+" if self.is_foreground else "-"
        return f"[{self.job_id}]{fg_indicator} {self.pid} {self.status.value}\t{self.command}"


class ProcessManager:
    """Manages processes and job control for the shell."""
    
    def __init__(self):
        """Initialize the process manager."""
        self.jobs: Dict[int, Job] = {}
        self.next_job_id = 1
        self.current_foreground_job: Optional[int] = None
    
    def add_job(self, process: subprocess.Popen, command: str, 
                foreground: bool = False) -> int:
        """
        Add a new job to the job table.
        
        Args:
            process: The subprocess.Popen object
            command: The command string that was executed
            foreground: Whether this is a foreground job
            
        Returns:
            The job ID assigned to this job
        """
        job_id = self.next_job_id
        self.next_job_id += 1
        
        job = Job(
            job_id=job_id,
            pid=process.pid,
            command=command,
            status=JobStatus.RUNNING,
            process=process,
            is_foreground=foreground
        )
        
        self.jobs[job_id] = job
        
        if foreground:
            self.current_foreground_job = job_id
        
        return job_id
    
    def get_job(self, job_id: int) -> Optional[Job]:
        """
        Get a job by its ID.
        
        Args:
            job_id: The job ID
            
        Returns:
            The Job object or None if not found
        """
        return self.jobs.get(job_id)
    
    def get_job_by_pid(self, pid: int) -> Optional[Job]:
        """
        Get a job by its process ID.
        
        Args:
            pid: The process ID
            
        Returns:
            The Job object or None if not found
        """
        for job in self.jobs.values():
            if job.pid == pid:
                return job
        return None
    
    def list_jobs(self) -> List[Job]:
        """
        List all active jobs (not completed).
        
        Returns:
            List of active Job objects
        """
        self.update_job_statuses()
        return [job for job in self.jobs.values() 
                if job.status in (JobStatus.RUNNING, JobStatus.STOPPED)]
    
    def mark_job_completed(self, job_id: int):
        """
        Mark a job as completed.
        
        Args:
            job_id: The job ID to mark as completed
        """
        if job_id in self.jobs:
            self.jobs[job_id].status = JobStatus.COMPLETED
            if self.current_foreground_job == job_id:
                self.current_foreground_job = None
    
    def mark_job_stopped(self, job_id: int):
        """
        Mark a job as stopped.
        
        Args:
            job_id: The job ID to mark as stopped
        """
        if job_id in self.jobs:
            self.jobs[job_id].status = JobStatus.STOPPED
            self.jobs[job_id].is_foreground = False
            if self.current_foreground_job == job_id:
                self.current_foreground_job = None
    
    def mark_job_terminated(self, job_id: int):
        """
        Mark a job as terminated.
        
        Args:
            job_id: The job ID to mark as terminated
        """
        if job_id in self.jobs:
            self.jobs[job_id].status = JobStatus.TERMINATED
            if self.current_foreground_job == job_id:
                self.current_foreground_job = None
    
    def update_job_statuses(self):
        """Update the status of all jobs by polling their processes."""
        for job_id, job in list(self.jobs.items()):
            if job.status in (JobStatus.COMPLETED, JobStatus.TERMINATED):
                continue
            
            # Check if process is still running
            poll_result = job.process.poll()
            
            if poll_result is not None:
                # Process has terminated
                if poll_result == 0:
                    if job.status != JobStatus.COMPLETED:
                        print(f"\n[{job_id}]+ Done\t\t{job.command}")
                    job.status = JobStatus.COMPLETED
                else:
                    if job.status != JobStatus.TERMINATED:
                        print(f"\n[{job_id}]+ Exit {poll_result}\t{job.command}")
                    job.status = JobStatus.TERMINATED
    
    def reap_children(self):
        """Reap any zombie child processes."""
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                    
                job = self.get_job_by_pid(pid)
                if job:
                    if os.WIFEXITED(status):
                        job.status = JobStatus.COMPLETED
                    elif os.WIFSIGNALED(status):
                        job.status = JobStatus.TERMINATED
                    elif os.WIFSTOPPED(status):
                        job.status = JobStatus.STOPPED
        except ChildProcessError:
            # No child processes
            pass
    
    def stop_foreground_job(self):
        """Stop the current foreground job (Ctrl+Z handler)."""
        if self.current_foreground_job is not None:
            job = self.jobs.get(self.current_foreground_job)
            if job and job.status == JobStatus.RUNNING:
                try:
                    os.kill(job.pid, signal.SIGTSTP)
                    job.status = JobStatus.STOPPED
                    job.is_foreground = False
                    print(f"\n[{job.job_id}]+ Stopped\t{job.command}")
                    self.current_foreground_job = None
                except OSError as e:
                    print(f"myshell: error stopping job: {e}")
    
    def bring_to_foreground(self, job_id: int) -> bool:
        """
        Bring a job to the foreground.
        
        Args:
            job_id: The job ID to bring to foreground
            
        Returns:
            True if successful, False otherwise
        """
        job = self.jobs.get(job_id)
        if not job:
            print(f"myshell: fg: {job_id}: no such job")
            return False
        
        if job.status == JobStatus.COMPLETED:
            print(f"myshell: fg: job has already completed")
            return False
        
        if job.status == JobStatus.TERMINATED:
            print(f"myshell: fg: job has been terminated")
            return False
        
        print(f"{job.command}")
        
        # Resume if stopped
        if job.status == JobStatus.STOPPED:
            try:
                os.kill(job.pid, signal.SIGCONT)
                job.status = JobStatus.RUNNING
            except OSError as e:
                print(f"myshell: fg: error resuming job: {e}")
                return False
        
        # Set as foreground job
        job.is_foreground = True
        self.current_foreground_job = job_id
        
        # Wait for the job to complete or stop
        try:
            job.process.wait()
            self.mark_job_completed(job_id)
        except KeyboardInterrupt:
            # User pressed Ctrl+C
            try:
                os.kill(job.pid, signal.SIGINT)
                job.process.wait()
                self.mark_job_completed(job_id)
            except:
                pass
            print()
        
        return True
    
    def send_to_background(self, job_id: int) -> bool:
        """
        Resume a stopped job in the background.
        
        Args:
            job_id: The job ID to send to background
            
        Returns:
            True if successful, False otherwise
        """
        job = self.jobs.get(job_id)
        if not job:
            print(f"myshell: bg: {job_id}: no such job")
            return False
        
        if job.status == JobStatus.COMPLETED:
            print(f"myshell: bg: job has already completed")
            return False
        
        if job.status == JobStatus.TERMINATED:
            print(f"myshell: bg: job has been terminated")
            return False
        
        if job.status == JobStatus.RUNNING:
            print(f"myshell: bg: job {job_id} already in background")
            return True
        
        # Resume if stopped
        if job.status == JobStatus.STOPPED:
            try:
                os.kill(job.pid, signal.SIGCONT)
                job.status = JobStatus.RUNNING
                job.is_foreground = False
                print(f"[{job_id}]+ {job.command} &")
            except OSError as e:
                print(f"myshell: bg: error resuming job: {e}")
                return False
        
        return True
    
    def kill_job(self, pid: int, sig: int = signal.SIGTERM) -> bool:
        """
        Send a signal to a process.
        
        Args:
            pid: The process ID
            sig: The signal to send (default: SIGTERM)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.kill(pid, sig)
            
            # Update job status if this is a tracked job
            job = self.get_job_by_pid(pid)
            if job:
                if sig in (signal.SIGTERM, signal.SIGKILL):
                    job.status = JobStatus.TERMINATED
                elif sig == signal.SIGSTOP:
                    job.status = JobStatus.STOPPED
                elif sig == signal.SIGCONT:
                    job.status = JobStatus.RUNNING
            
            return True
        except ProcessLookupError:
            print(f"myshell: kill: ({pid}) - No such process")
            return False
        except PermissionError:
            print(f"myshell: kill: ({pid}) - Operation not permitted")
            return False
        except OSError as e:
            print(f"myshell: kill: ({pid}) - {e}")
            return False
    
    def get_most_recent_job(self) -> Optional[Job]:
        """
        Get the most recent job (highest job ID).
        
        Returns:
            The most recent Job or None if no jobs
        """
        active_jobs = self.list_jobs()
        if not active_jobs:
            return None
        return max(active_jobs, key=lambda j: j.job_id)
    
    def cleanup(self):
        """Clean up all jobs before shell exit."""
        for job in self.jobs.values():
            if job.status == JobStatus.RUNNING:
                try:
                    job.process.terminate()
                    job.process.wait(timeout=1)
                except:
                    try:
                        job.process.kill()
                    except:
                        pass
