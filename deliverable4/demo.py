#!/usr/bin/env python3
"""
Interactive Demo Script for Deliverable 4

This script provides an interactive walkthrough of:
- Command Piping functionality
- User Authentication system
- File Permissions handling
- Integration with previous deliverables
"""

import os
import sys
import time
from typing import List, Callable

# Ensure we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deliverable1'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deliverable2'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'deliverable3'))

from authentication import AuthenticationManager, UserRole, create_auth_manager
from permissions import FilePermissionManager, Permission, create_permission_manager
from piping import PipeExecutor, create_pipe_executor

# Try to import from previous deliverables
try:
    from memory_manager import create_memory_manager
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False

try:
    from scheduler import RoundRobinScheduler, PriorityScheduler
    from process import Process
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False


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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")


def print_subheader(text: str):
    """Print a subsection header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- {text} ---{Colors.END}\n")


def print_info(text: str):
    """Print informational text."""
    print(f"{Colors.BLUE}ℹ  {text}{Colors.END}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓  {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠  {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗  {text}{Colors.END}")


def print_command(cmd: str):
    """Print a command being executed."""
    print(f"{Colors.MAGENTA}>>> {cmd}{Colors.END}")


def print_output(text: str):
    """Print command output."""
    for line in text.split('\n'):
        print(f"    {line}")


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
        print_error("Invalid choice. Please try again.")


def demo_piping():
    """Demonstrate command piping functionality."""
    print_header("DEMO 1: Command Piping")
    
    print_info("Command piping allows the output of one command to be used as")
    print_info("input for another command, using the '|' (pipe) symbol.")
    print_info("This enables powerful command chaining for text processing.\n")
    
    # Create pipe executor with visible callback
    pipe = create_pipe_executor(callback=lambda x: print(f"  {Colors.GRAY}{x}{Colors.END}"))
    
    # Create a test file for piping demos
    test_file = "/tmp/demo_pipe_test.txt"
    test_content = """apple
banana
cherry
apple
date
elderberry
apple
fig
grape
"""
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    print_subheader("Example 1: Simple Pipe (echo | grep)")
    print_info("Piping echo output to grep to filter lines")
    
    wait_for_user("Press Enter to execute: echo 'hello world' | grep 'world'")
    
    print_command("echo 'hello world' | grep 'world'")
    result = pipe.execute_pipeline("echo 'hello world' | grep 'world'")
    print_output(result.output)
    print_success("Output passed through pipe successfully!")
    
    print_subheader("Example 2: Multi-stage Pipe (cat | grep | sort)")
    print_info("Reading a file, filtering, and sorting")
    
    wait_for_user(f"Press Enter to execute: cat {test_file} | grep 'a' | sort")
    
    print_command(f"cat {test_file} | grep 'a' | sort")
    result = pipe.execute_pipeline(f"cat {test_file} | grep 'a' | sort")
    print_output(result.output)
    print_success("Multi-stage pipeline executed successfully!")
    
    print_subheader("Example 3: Count with Pipe (cat | grep | wc)")
    print_info("Counting lines matching a pattern")
    
    wait_for_user(f"Press Enter to execute: cat {test_file} | grep 'apple' | wc -l")
    
    print_command(f"cat {test_file} | grep 'apple' | wc -l")
    result = pipe.execute_pipeline(f"cat {test_file} | grep 'apple' | wc -l")
    print_output(f"Count: {result.output.strip()}")
    print_success("Word count through pipe completed!")
    
    print_subheader("Example 4: Remove Duplicates (cat | sort | uniq)")
    print_info("Sorting and removing duplicate lines")
    
    wait_for_user(f"Press Enter to execute: cat {test_file} | sort | uniq")
    
    print_command(f"cat {test_file} | sort | uniq")
    result = pipe.execute_pipeline(f"cat {test_file} | sort | uniq")
    print_output(result.output)
    print_success("Duplicates removed successfully!")
    
    print_subheader("Example 5: Head/Tail with Pipe")
    print_info("Getting first or last lines of piped output")
    
    wait_for_user(f"Press Enter to execute: cat {test_file} | head -n 3")
    
    print_command(f"cat {test_file} | head -n 3")
    result = pipe.execute_pipeline(f"cat {test_file} | head -n 3")
    print_output(result.output)
    print_success("Head command in pipeline executed!")
    
    # Show statistics
    print_subheader("Piping Statistics")
    stats = pipe.get_stats()
    print_info(f"Total pipelines executed: {stats['total_executed']}")
    print_info(f"Successful: {stats['successful']}")
    print_info(f"Success rate: {stats['success_rate']:.1f}%")
    
    # Cleanup
    try:
        os.remove(test_file)
    except:
        pass
    
    wait_for_user()


def demo_authentication():
    """Demonstrate user authentication system."""
    print_header("DEMO 2: User Authentication")
    
    print_info("The authentication system provides:")
    print_info("  • User login with username and password")
    print_info("  • Different permission levels (admin, standard, guest)")
    print_info("  • Session management")
    print_info("  • Password hashing for security\n")
    
    # Create auth manager with visible callback
    auth = create_auth_manager(callback=lambda x: print(f"  {Colors.GRAY}{x}{Colors.END}"))
    
    print_subheader("Available Users")
    print_info("Default users in the system:")
    print("  ┌──────────────┬────────────┬─────────────┐")
    print("  │ Username     │ Password   │ Role        │")
    print("  ├──────────────┼────────────┼─────────────┤")
    print("  │ admin        │ admin123   │ admin       │")
    print("  │ user1        │ password1  │ standard    │")
    print("  │ user2        │ password2  │ standard    │")
    print("  │ guest        │ guest      │ guest       │")
    print("  └──────────────┴────────────┴─────────────┘")
    
    print_subheader("Test 1: Failed Login Attempt")
    wait_for_user("Press Enter to try logging in with wrong password")
    
    print_command("login('user1', 'wrongpassword')")
    session = auth.login("user1", "wrongpassword")
    if session:
        print_error("Login should have failed!")
    else:
        print_success("Login correctly rejected with wrong password")
    
    print_subheader("Test 2: Successful Login (Standard User)")
    wait_for_user("Press Enter to login as user1")
    
    print_command("login('user1', 'password1')")
    session = auth.login("user1", "password1")
    if session:
        print_success(f"Logged in as: {session.user.username}")
        print_info(f"Role: {session.user.role.value}")
        print_info(f"Session ID: {session.session_id}")
    else:
        print_error("Login failed!")
    
    print_subheader("Test 3: Check Current User")
    print_command("whoami()")
    user = auth.get_current_user()
    if user:
        print_output(f"Current user: {user.username} (Role: {user.role.value})")
    
    print_subheader("Test 4: Logout")
    wait_for_user("Press Enter to logout")
    
    print_command("logout()")
    auth.logout()
    print_success("Logged out successfully")
    
    print_subheader("Test 5: Admin Login")
    wait_for_user("Press Enter to login as admin")
    
    print_command("login('admin', 'admin123')")
    session = auth.login("admin", "admin123")
    if session:
        print_success(f"Logged in as: {session.user.username}")
        print_info(f"Role: {session.user.role.value} (has full access)")
    
    print_subheader("Test 6: Create New User (Admin Only)")
    wait_for_user("Press Enter to create a new user 'testuser'")
    
    print_command("register_user('testuser', 'testpass', UserRole.STANDARD)")
    if auth.register_user("testuser", "testpass", UserRole.STANDARD):
        print_success("User 'testuser' created successfully")
    
    print_subheader("Test 7: List All Users")
    print_command("list_users()")
    users = auth.list_users()
    print("\n  All registered users:")
    for u in users:
        print(f"    • {u['username']} ({u['role']})")
    
    print_subheader("Test 8: Delete User (Admin Only)")
    wait_for_user("Press Enter to delete 'testuser'")
    
    print_command("delete_user('testuser')")
    if auth.delete_user("testuser"):
        print_success("User 'testuser' deleted successfully")
    
    print_subheader("Authentication Log")
    print_info("Recent authentication events:")
    for event in auth.get_auth_log(5):
        print(f"    {event}")
    
    wait_for_user()


def demo_file_permissions():
    """Demonstrate file permissions handling."""
    print_header("DEMO 3: File Permissions")
    
    print_info("The file permission system implements Unix-like permissions:")
    print_info("  • Read (r), Write (w), Execute (x) permissions")
    print_info("  • Owner, Group, Others permission levels")
    print_info("  • System file protection")
    print_info("  • Permission checking based on user roles\n")
    
    # Create managers
    auth = create_auth_manager(callback=lambda x: None)
    perm = create_permission_manager(callback=lambda x: print(f"  {Colors.GRAY}{x}{Colors.END}"))
    
    print_subheader("Simulated File System Structure")
    print_info("The demo uses a simulated file system with these paths:")
    print("""
    /
    ├── etc/
    │   ├── passwd      (644, system file)
    │   ├── shadow      (600, system file)
    │   └── config      (644, system file)
    ├── home/
    │   ├── admin/      (700)
    │   ├── user1/
    │   │   ├── document.txt   (644)
    │   │   ├── private.txt    (600)
    │   │   └── script.sh      (755)
    │   └── user2/
    │       ├── notes.txt      (644)
    │       └── secret.txt     (600)
    └── tmp/
        └── shared.txt  (666)
    """)
    
    print_subheader("Test 1: Read Public File as Standard User")
    wait_for_user("Press Enter to login as user1 and read a public file")
    
    auth.login("user1", "password1")
    user = auth.get_current_user()
    print_command(f"cat /home/user1/document.txt (as {user.username})")
    
    content = perm.read_file(user, "/home/user1/document.txt")
    if content:
        print_output(content)
        print_success("Successfully read public file")
    
    print_subheader("Test 2: Read Private File (Permission Denied)")
    wait_for_user("Press Enter to try reading user2's private file")
    
    print_command(f"cat /home/user2/secret.txt (as {user.username})")
    content = perm.read_file(user, "/home/user2/secret.txt")
    if content is None:
        print_success("Access correctly denied - file is private (600)")
    
    print_subheader("Test 3: Read Own Private File")
    wait_for_user("Press Enter to read user1's own private file")
    
    print_command(f"cat /home/user1/private.txt (as {user.username})")
    content = perm.read_file(user, "/home/user1/private.txt")
    if content:
        print_output(content)
        print_success("Owner can read their own private file")
    
    print_subheader("Test 4: Write to System File (Permission Denied)")
    wait_for_user("Press Enter to try modifying a system file")
    
    print_command(f"write /etc/passwd 'hacked' (as {user.username})")
    result = perm.write_file(user, "/etc/passwd", "hacked")
    if not result:
        print_success("System file correctly protected - standard users cannot modify")
    
    print_subheader("Test 5: Write to Shared File")
    wait_for_user("Press Enter to write to a shared file (666 permissions)")
    
    print_command(f"write /tmp/shared.txt 'Hello from user1!' (as {user.username})")
    if perm.write_file(user, "/tmp/shared.txt", "Hello from user1!"):
        print_success("Successfully wrote to shared file")
    
    auth.logout()
    
    print_subheader("Test 6: Admin Access")
    wait_for_user("Press Enter to login as admin and access protected files")
    
    auth.login("admin", "admin123")
    admin = auth.get_current_user()
    print_command(f"cat /etc/shadow (as {admin.username})")
    
    content = perm.read_file(admin, "/etc/shadow")
    if content:
        print_output(content[:50] + "...")
        print_success("Admin can read protected system files")
    
    print_subheader("Test 7: Change Permissions (chmod)")
    wait_for_user("Press Enter to change file permissions")
    
    print_command(f"chmod 755 /home/user1/document.txt (as {admin.username})")
    if perm.chmod(admin, "/home/user1/document.txt", "755"):
        print_success("Permissions changed successfully")
        info = perm.get_file_info("/home/user1/document.txt")
        print_info(f"New permissions: {info['permissions']} ({info['octal']})")
    
    print_subheader("Test 8: Change Ownership (chown)")
    wait_for_user("Press Enter to change file ownership")
    
    print_command(f"chown admin /home/user1/document.txt (as {admin.username})")
    if perm.chown(admin, "/home/user1/document.txt", "admin"):
        print_success("Ownership changed successfully")
        info = perm.get_file_info("/home/user1/document.txt")
        print_info(f"New owner: {info['owner']}")
    
    print_subheader("Test 9: View File Details (stat)")
    print_command("stat /home/user1/script.sh")
    print(perm.visualize_permissions("/home/user1/script.sh"))
    
    print_subheader("Access Log")
    print_info("Recent file access events:")
    for entry in perm.get_access_log(5):
        status = "✓" if entry['allowed'] else "✗"
        print(f"    {status} {entry['user']} ({entry['role']}) -> {entry['action']} {entry['path']}")
    
    wait_for_user()


def demo_integration():
    """Demonstrate integration with previous deliverables."""
    print_header("DEMO 4: Integration with Previous Deliverables")
    
    print_info("The integrated shell combines all components:")
    print_info("  • Deliverable 1: Basic shell and process management")
    print_info("  • Deliverable 2: Process scheduling algorithms")
    print_info("  • Deliverable 3: Memory management and synchronization")
    print_info("  • Deliverable 4: Piping, authentication, and permissions\n")
    
    print_subheader("Integration with Deliverable 2: Scheduling")
    
    if HAS_SCHEDULER:
        print_info("Demonstrating Round-Robin Scheduler:")
        
        scheduler = RoundRobinScheduler(time_quantum=2, callback=lambda x: print(f"    {Colors.GRAY}{x}{Colors.END}"))
        
        # Add some processes
        processes = [
            Process(name="Process_A", burst_time=5, priority=3),
            Process(name="Process_B", burst_time=3, priority=1),
            Process(name="Process_C", burst_time=4, priority=2),
        ]
        
        for p in processes:
            scheduler.add_process(p)
            print_info(f"Added: {p.name} (burst={p.burst_time}, priority={p.priority})")
        
        wait_for_user("Press Enter to run the scheduler")
        
        print_command("scheduler.run()")
        scheduler.run()
        
        print("\n" + scheduler.metrics.get_summary())
        print_success("Scheduling complete!")
    else:
        print_warning("Scheduler module not available (deliverable2 not found)")
    
    print_subheader("Integration with Deliverable 3: Memory Management")
    
    if HAS_MEMORY:
        print_info("Demonstrating Memory Manager with FIFO page replacement:")
        
        mm = create_memory_manager(4, 'fifo', callback=lambda x: print(f"    {Colors.GRAY}{x}{Colors.END}"))
        
        # Allocate pages for multiple processes
        allocations = [
            (1, 0), (1, 1), (2, 0), (2, 1),  # Fill memory
            (3, 0),  # Trigger page replacement
        ]
        
        wait_for_user("Press Enter to allocate pages and trigger page replacement")
        
        for pid, page in allocations:
            print_command(f"alloc process={pid}, page={page}")
            mm.allocate_page(pid, page)
        
        print(mm.visualize_memory())
        print_info(f"Page faults: {mm.metrics.total_page_faults}")
        print_info(f"Page replacements: {mm.metrics.page_replacements}")
        print_success("Memory management demonstration complete!")
    else:
        print_warning("Memory module not available (deliverable3 not found)")
    
    print_subheader("Full Integration Demo")
    print_info("To see all components working together, run the integrated shell:")
    print(f"\n    {Colors.CYAN}python3 integrated_shell.py{Colors.END}\n")
    print_info("In the shell, you can:")
    print("    • Login as different users (admin, user1, user2, guest)")
    print("    • Use piped commands (ls | grep txt | sort)")
    print("    • Access files based on permissions")
    print("    • Initialize and use the scheduler")
    print("    • Manage memory with page allocation")
    
    wait_for_user()


def demo_combined_scenario():
    """Run a combined scenario showing all features."""
    print_header("DEMO 5: Combined Scenario")
    
    print_info("This scenario demonstrates a real-world usage pattern:")
    print_info("A user logs in, works with files, uses piping, and the system")
    print_info("enforces permissions throughout.\n")
    
    auth = create_auth_manager(callback=lambda x: None)
    perm = create_permission_manager(callback=lambda x: None)
    pipe = create_pipe_executor(callback=lambda x: None)
    
    print_subheader("Scenario: Data Processing Workflow")
    
    # Step 1: Login
    print(f"{Colors.CYAN}Step 1: User logs in{Colors.END}")
    session = auth.login("user1", "password1")
    print_success(f"Logged in as {session.user.username}")
    user = auth.get_current_user()
    
    # Step 2: Check access to files
    print(f"\n{Colors.CYAN}Step 2: Check file access{Colors.END}")
    
    files_to_check = [
        "/home/user1/document.txt",
        "/home/user2/secret.txt",
        "/etc/passwd",
        "/tmp/shared.txt"
    ]
    
    for f in files_to_check:
        can_read = perm.can_read(user, f)
        can_write = perm.can_write(user, f)
        status_r = f"{Colors.GREEN}✓{Colors.END}" if can_read else f"{Colors.RED}✗{Colors.END}"
        status_w = f"{Colors.GREEN}✓{Colors.END}" if can_write else f"{Colors.RED}✗{Colors.END}"
        print(f"    {f}: read={status_r} write={status_w}")
    
    # Step 3: Create a work file
    print(f"\n{Colors.CYAN}Step 3: Create a work file{Colors.END}")
    work_file = "/tmp/demo_work.txt"
    work_content = """error: connection failed
info: starting process
error: timeout occurred
debug: variable x = 5
error: file not found
info: process completed
warning: low memory
error: permission denied
"""
    
    with open(work_file, 'w') as f:
        f.write(work_content)
    print_success(f"Created work file with log entries")
    
    # Step 4: Use piping to process the file
    print(f"\n{Colors.CYAN}Step 4: Use piping to analyze logs{Colors.END}")
    
    print_command(f"cat {work_file} | grep 'error' | wc -l")
    result = pipe.execute_pipeline(f"cat {work_file} | grep 'error' | wc -l")
    print_output(f"Number of errors: {result.output.strip()}")
    
    print_command(f"cat {work_file} | grep 'error' | sort")
    result = pipe.execute_pipeline(f"cat {work_file} | grep 'error' | sort")
    print_output("Sorted errors:\n" + result.output)
    
    # Step 5: Try to access protected resources
    print(f"\n{Colors.CYAN}Step 5: Try to access protected system file{Colors.END}")
    content = perm.read_file(user, "/etc/shadow")
    if content is None:
        print_success("Access to /etc/shadow correctly denied (600 permissions)")
    
    # Step 6: Logout and login as admin
    print(f"\n{Colors.CYAN}Step 6: Escalate to admin{Colors.END}")
    auth.logout()
    session = auth.login("admin", "admin123")
    admin = auth.get_current_user()
    print_success(f"Now logged in as {admin.username} (role: {admin.role.value})")
    
    # Step 7: Admin accesses protected file
    print(f"\n{Colors.CYAN}Step 7: Admin reads protected file{Colors.END}")
    content = perm.read_file(admin, "/etc/shadow")
    if content:
        print_success("Admin successfully read /etc/shadow")
        print_output(content[:50] + "...")
    
    # Cleanup
    try:
        os.remove(work_file)
    except:
        pass
    
    print(f"\n{Colors.GREEN}{'='*70}{Colors.END}")
    print(f"{Colors.GREEN}Combined scenario completed successfully!{Colors.END}")
    print(f"{Colors.GREEN}{'='*70}{Colors.END}")
    
    wait_for_user()


def main():
    """Main function to run the interactive demo."""
    print_header("DELIVERABLE 4: INTERACTIVE DEMO")
    
    print(f"""
{Colors.CYAN}This demo will walk you through all features implemented in Deliverable 4:{Colors.END}

  {Colors.GREEN}1.{Colors.END} Command Piping
     • Chaining commands with | (pipe)
     • Multi-stage pipelines
     • Output as input processing

  {Colors.GREEN}2.{Colors.END} User Authentication
     • Login/logout system
     • Different user roles (admin, standard, guest)
     • Session management

  {Colors.GREEN}3.{Colors.END} File Permissions
     • Read/Write/Execute permissions
     • Owner/Group/Others access levels
     • System file protection

  {Colors.GREEN}4.{Colors.END} Integration with Previous Deliverables
     • Process scheduling (Deliverable 2)
     • Memory management (Deliverable 3)

  {Colors.GREEN}5.{Colors.END} Combined Scenario
     • Real-world usage example

  {Colors.GREEN}6.{Colors.END} Run Integrated Shell
     • Launch the full interactive shell
""")
    
    while True:
        choice = get_user_choice("Select a demo to run:", [
            "Command Piping Demo",
            "User Authentication Demo",
            "File Permissions Demo",
            "Integration with Previous Deliverables",
            "Combined Scenario",
            "Run Integrated Shell",
            "Run All Demos",
            "Exit"
        ])
        
        if choice == 1:
            demo_piping()
        elif choice == 2:
            demo_authentication()
        elif choice == 3:
            demo_file_permissions()
        elif choice == 4:
            demo_integration()
        elif choice == 5:
            demo_combined_scenario()
        elif choice == 6:
            print_info("Launching integrated shell...")
            print_info("Type 'help' for commands, 'exit' to return to demo menu.\n")
            try:
                from integrated_shell import IntegratedShell
                shell = IntegratedShell()
                shell.run()
            except Exception as e:
                print_error(f"Error launching shell: {e}")
        elif choice == 7:
            demo_piping()
            demo_authentication()
            demo_file_permissions()
            demo_integration()
            demo_combined_scenario()
            print_header("ALL DEMOS COMPLETED")
            print_success("All Deliverable 4 features have been demonstrated!")
        elif choice == 8:
            print_info("Thank you for using the Deliverable 4 Demo!")
            break
    
    print_header("DEMO COMPLETE")
    print_success("All features of Deliverable 4 have been demonstrated.")
    print_info("To run the full integrated shell, use: python3 integrated_shell.py")


if __name__ == "__main__":
    main()
