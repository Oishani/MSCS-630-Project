#!/usr/bin/env python3
"""
Interactive Demo Script for MyShell

This script provides an interactive walkthrough of all the features
implemented in the shell for Deliverable 1.
"""

import os
import sys
import time
import subprocess
import signal

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


def print_header(text):
    """Print a section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_subheader(text):
    """Print a subsection header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- {text} ---{Colors.END}\n")


def print_command(cmd):
    """Print a command being demonstrated."""
    print(f"{Colors.GREEN}Command:{Colors.END} {Colors.BOLD}{cmd}{Colors.END}")


def print_info(text):
    """Print informational text."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def wait_for_user():
    """Wait for user to press Enter."""
    input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")


def run_shell_command(shell_process, command, wait_time=0.5):
    """Send a command to the shell and display output."""
    print_command(command)
    shell_process.stdin.write(command + '\n')
    shell_process.stdin.flush()
    time.sleep(wait_time)


def demo_section(title, description, demo_func):
    """Run a demo section with error handling."""
    print_header(title)
    print_info(description)
    wait_for_user()
    try:
        demo_func()
    except Exception as e:
        print(f"{Colors.RED}Error during demo: {e}{Colors.END}")
    print_success(f"Completed: {title}")


def main():
    """Main demo function."""
    print_header("MyShell - Interactive Demo")
    print(f"""
{Colors.BOLD}Welcome to the MyShell Interactive Demo!{Colors.END}

This demo will walk you through all the features implemented
in Deliverable 1 of the Advanced Shell Simulation project.

{Colors.CYAN}Features covered:{Colors.END}
  1. Built-in Commands (cd, pwd, exit, echo, clear, ls, etc.)
  2. File Operations (cat, mkdir, rmdir, rm, touch)
  3. Process Management (foreground/background execution)
  4. Job Control (jobs, fg, bg, kill)
  5. Error Handling

{Colors.YELLOW}Note: Some demos will launch the actual shell for you to interact with.{Colors.END}
""")
    
    wait_for_user()
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Create a demo directory
    demo_dir = os.path.join(script_dir, 'demo_workspace')
    if os.path.exists(demo_dir):
        import shutil
        shutil.rmtree(demo_dir)
    os.makedirs(demo_dir)
    os.chdir(demo_dir)
    
    # ==================== DEMO 1: Directory Commands ====================
    print_header("Demo 1: Directory Commands")
    print_info("Demonstrating: pwd, cd, mkdir, rmdir, ls")
    wait_for_user()
    
    print_subheader("pwd - Print Working Directory")
    print_command("pwd")
    print(f"Output: {os.getcwd()}")
    
    print_subheader("mkdir - Create Directory")
    print_command("mkdir test_dir")
    os.makedirs("test_dir", exist_ok=True)
    print_success("Created directory 'test_dir'")
    
    print_command("mkdir nested/deep/dir (without -p would fail)")
    print_warning("This demonstrates error handling - cannot create nested dirs without parent")
    
    print_subheader("ls - List Directory Contents")
    print_command("ls")
    print("Output:", os.listdir('.'))
    
    print_subheader("cd - Change Directory")
    print_command("cd test_dir")
    os.chdir("test_dir")
    print(f"Now in: {os.getcwd()}")
    
    print_command("cd ..")
    os.chdir("..")
    print(f"Back to: {os.getcwd()}")
    
    print_subheader("rmdir - Remove Empty Directory")
    print_command("rmdir test_dir")
    os.rmdir("test_dir")
    print_success("Removed directory 'test_dir'")
    
    wait_for_user()
    
    # ==================== DEMO 2: File Commands ====================
    print_header("Demo 2: File Commands")
    print_info("Demonstrating: touch, cat, rm")
    wait_for_user()
    
    print_subheader("touch - Create File")
    print_command("touch hello.txt")
    open("hello.txt", 'a').close()
    print_success("Created file 'hello.txt'")
    
    # Write some content
    with open("hello.txt", 'w') as f:
        f.write("Hello, World!\nThis is a test file.\n")
    
    print_subheader("cat - Display File Contents")
    print_command("cat hello.txt")
    with open("hello.txt", 'r') as f:
        print(f"Output:\n{f.read()}")
    
    print_subheader("rm - Remove File")
    print_command("rm hello.txt")
    os.remove("hello.txt")
    print_success("Removed file 'hello.txt'")
    
    print_subheader("Error Handling - File Not Found")
    print_command("cat nonexistent.txt")
    print(f"{Colors.RED}myshell: cat: nonexistent.txt: No such file or directory{Colors.END}")
    print_info("Shell gracefully handles missing files")
    
    wait_for_user()
    
    # ==================== DEMO 3: Echo and Clear ====================
    print_header("Demo 3: Output Commands")
    print_info("Demonstrating: echo, clear")
    wait_for_user()
    
    print_subheader("echo - Print Text")
    print_command("echo Hello World")
    print("Output: Hello World")
    
    print_command("echo -n No newline")
    print("Output: No newline", end='')
    print(f" {Colors.YELLOW}(no newline at end){Colors.END}")
    
    print_command('echo "Text with spaces"')
    print('Output: Text with spaces')
    
    print_subheader("clear - Clear Screen")
    print_command("clear")
    print_info("This command clears the terminal screen using ANSI escape codes")
    
    wait_for_user()
    
    # ==================== DEMO 4: Process Management ====================
    print_header("Demo 4: Process Management")
    print_info("Demonstrating: foreground/background execution")
    wait_for_user()
    
    print_subheader("Foreground Execution")
    print_command("sleep 2")
    print_info("Running a command in foreground blocks the shell until completion")
    print_info("The shell uses subprocess.Popen and waits for the process")
    
    print_subheader("Background Execution")
    print_command("sleep 10 &")
    print_info("Appending '&' runs the command in the background")
    print_info("Output: [1] 12345  (job number and PID)")
    print_info("The shell immediately returns to the prompt")
    
    print_subheader("Process Tracking")
    print_info("""
The shell tracks processes using:
- Job ID: Sequential identifier for each job
- PID: Process ID from the operating system
- Status: Running, Stopped, Completed, or Terminated
- Command: The original command string
""")
    
    wait_for_user()
    
    # ==================== DEMO 5: Job Control ====================
    print_header("Demo 5: Job Control Commands")
    print_info("Demonstrating: jobs, fg, bg, kill")
    wait_for_user()
    
    print_subheader("jobs - List Background Jobs")
    print_command("jobs")
    print("""Output example:
[1]- 12345 Running    sleep 30 &
[2]+ 12346 Stopped    vim file.txt
""")
    
    print_subheader("fg - Bring to Foreground")
    print_command("fg 1")
    print_info("Brings job 1 to the foreground")
    print_info("If job was stopped, it resumes execution")
    
    print_subheader("bg - Resume in Background")
    print_command("bg 2")
    print_info("Resumes a stopped job in the background")
    print_info("Job continues executing without blocking the shell")
    
    print_subheader("kill - Terminate Process")
    print_command("kill 12345")
    print_info("Sends SIGTERM to process 12345")
    
    print_command("kill -9 12345")
    print_info("Sends SIGKILL (force kill) to process 12345")
    
    print_command("kill -STOP 12345")
    print_info("Sends SIGSTOP to pause the process")
    
    wait_for_user()
    
    # ==================== DEMO 6: Error Handling ====================
    print_header("Demo 6: Error Handling")
    print_info("Demonstrating graceful error handling")
    wait_for_user()
    
    print_subheader("Invalid Commands")
    print_command("nonexistent_command")
    print(f"{Colors.RED}myshell: nonexistent_command: command not found{Colors.END}")
    
    print_subheader("Invalid Arguments")
    print_command("cd /nonexistent/path")
    print(f"{Colors.RED}myshell: cd: /nonexistent/path: No such file or directory{Colors.END}")
    
    print_command("cd")
    print_info("With no argument, cd goes to HOME directory")
    
    print_subheader("Permission Errors")
    print_command("cat /etc/shadow")
    print(f"{Colors.RED}myshell: cat: /etc/shadow: Permission denied{Colors.END}")
    
    print_subheader("Directory vs File Errors")
    print_command("cat some_directory/")
    print(f"{Colors.RED}myshell: cat: some_directory/: Is a directory{Colors.END}")
    
    print_command("rmdir non_empty_dir")
    print(f"{Colors.RED}myshell: rmdir: failed to remove 'non_empty_dir': Directory not empty{Colors.END}")
    
    print_subheader("Process Errors")
    print_command("kill 99999")
    print(f"{Colors.RED}myshell: kill: (99999) - No such process{Colors.END}")
    
    print_command("fg 99")
    print(f"{Colors.RED}myshell: fg: 99: no such job{Colors.END}")
    
    wait_for_user()
    
    # ==================== DEMO 7: Signal Handling ====================
    print_header("Demo 7: Signal Handling")
    print_info("Demonstrating Ctrl+C and Ctrl+Z handling")
    wait_for_user()
    
    print_subheader("Ctrl+C (SIGINT)")
    print_info("""
When Ctrl+C is pressed:
- If a foreground process is running, SIGINT is sent to it
- The process typically terminates
- The shell remains running and shows a new prompt
""")
    
    print_subheader("Ctrl+Z (SIGTSTP)")
    print_info("""
When Ctrl+Z is pressed:
- The foreground process receives SIGTSTP
- The process is stopped (paused)
- The job is moved to background with 'Stopped' status
- Use 'fg' to resume in foreground or 'bg' to resume in background
""")
    
    print_subheader("Ctrl+D (EOF)")
    print_info("""
When Ctrl+D is pressed at an empty prompt:
- The shell interprets this as end-of-input
- The shell exits gracefully (same as 'exit' command)
""")
    
    wait_for_user()
    
    # ==================== DEMO 8: Interactive Shell ====================
    print_header("Demo 8: Interactive Shell Session")
    print_info("Now launching the actual shell for you to try!")
    print()
    print(f"{Colors.BOLD}Suggested commands to try:{Colors.END}")
    print("""
  1. help              - View all available commands
  2. pwd               - Print current directory
  3. mkdir mydir       - Create a directory
  4. cd mydir          - Change to the directory
  5. touch file.txt    - Create a file
  6. echo "Hello" > test.txt  - (Note: redirection not implemented)
  7. ls -la            - List with details
  8. sleep 30 &        - Start background job
  9. jobs              - View background jobs
  10. fg 1             - Bring job to foreground
  11. Ctrl+Z           - Stop the foreground job
  12. bg 1             - Resume in background
  13. kill <pid>       - Terminate a process
  14. exit             - Exit the shell
""")
    
    print_warning("Type 'exit' to return to this demo script")
    wait_for_user()
    
    # Launch the shell
    os.chdir(script_dir)
    shell_path = os.path.join(script_dir, 'shell.py')
    
    try:
        subprocess.run([sys.executable, shell_path])
    except KeyboardInterrupt:
        print("\nShell interrupted")
    
    # ==================== Cleanup ====================
    print_header("Demo Complete!")
    print()
    print(f"{Colors.GREEN}{Colors.BOLD}Congratulations!{Colors.END}")
    print("""
You have completed the interactive demo of MyShell.

{bold}Summary of Features Implemented:{end}

{cyan}Built-in Commands:{end}
  ✓ cd, pwd - Directory navigation
  ✓ echo, clear - Output commands
  ✓ ls, cat - File viewing
  ✓ mkdir, rmdir - Directory management
  ✓ touch, rm - File management
  ✓ kill - Process termination

{cyan}Process Management:{end}
  ✓ Foreground execution (blocking)
  ✓ Background execution (& suffix)
  ✓ Process status tracking

{cyan}Job Control:{end}
  ✓ jobs - List background jobs
  ✓ fg - Bring to foreground
  ✓ bg - Resume in background

{cyan}Error Handling:{end}
  ✓ Invalid commands
  ✓ File/directory not found
  ✓ Permission denied
  ✓ Invalid arguments

{cyan}Signal Handling:{end}
  ✓ Ctrl+C (SIGINT)
  ✓ Ctrl+Z (SIGTSTP)
  ✓ Ctrl+D (EOF)

""".format(bold=Colors.BOLD, end=Colors.END, cyan=Colors.CYAN))
    
    # Cleanup demo workspace
    os.chdir(script_dir)
    if os.path.exists(demo_dir):
        import shutil
        shutil.rmtree(demo_dir)
    
    print_info("Demo workspace cleaned up.")
    print(f"\n{Colors.BOLD}To run the shell directly:{Colors.END}")
    print(f"  python3 {shell_path}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user.{Colors.END}")
        sys.exit(0)
