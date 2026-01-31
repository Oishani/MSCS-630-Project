#!/usr/bin/env python3
"""
File Permissions Module for Deliverable 4
"""

import os
import time
from enum import Flag, auto
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable
from datetime import datetime

try:
    from authentication import User, UserRole
except ImportError:
    from deliverable4.authentication import User, UserRole


class Permission(Flag):
    """File permission flags."""
    NONE = 0
    EXECUTE = auto()
    WRITE = auto()
    READ = auto()
    RX = READ | EXECUTE
    RW = READ | WRITE
    RWX = READ | WRITE | EXECUTE


@dataclass
class FilePermissions:
    """Represents permissions for a file/directory."""
    owner: Permission = Permission.RWX
    group: Permission = Permission.RX
    others: Permission = Permission.READ
    
    def __str__(self) -> str:
        def perm_str(p: Permission) -> str:
            r = 'r' if Permission.READ in p else '-'
            w = 'w' if Permission.WRITE in p else '-'
            x = 'x' if Permission.EXECUTE in p else '-'
            return f"{r}{w}{x}"
        return f"{perm_str(self.owner)}{perm_str(self.group)}{perm_str(self.others)}"
    
    def to_octal(self) -> str:
        def perm_val(p: Permission) -> int:
            val = 0
            if Permission.READ in p: val += 4
            if Permission.WRITE in p: val += 2
            if Permission.EXECUTE in p: val += 1
            return val
        return f"{perm_val(self.owner)}{perm_val(self.group)}{perm_val(self.others)}"
    
    @classmethod
    def from_octal(cls, octal: str) -> 'FilePermissions':
        def int_to_perm(val: int) -> Permission:
            p = Permission.NONE
            if val >= 4: p |= Permission.READ; val -= 4
            if val >= 2: p |= Permission.WRITE; val -= 2
            if val >= 1: p |= Permission.EXECUTE
            return p
        octal = octal.zfill(3)
        return cls(owner=int_to_perm(int(octal[0])), group=int_to_perm(int(octal[1])), 
                   others=int_to_perm(int(octal[2])))


@dataclass
class SimulatedFile:
    """Represents a file in the simulated file system."""
    name: str
    path: str
    owner: str
    group: str = "users"
    permissions: FilePermissions = field(default_factory=FilePermissions)
    is_directory: bool = False
    content: str = ""
    size: int = 0
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    is_system_file: bool = False
    
    def __post_init__(self):
        if not self.is_directory:
            self.size = len(self.content)
    
    def get_type_char(self) -> str:
        return 'd' if self.is_directory else '-'
    
    def __str__(self) -> str:
        return f"{self.get_type_char()}{self.permissions} {self.owner:8} {self.group:8} {self.size:6} {self.name}"


class FilePermissionManager:
    """Manages file permissions in a simulated file system."""
    
    def __init__(self, callback: Callable = None):
        self.callback = callback or print
        self.files: Dict[str, SimulatedFile] = {}
        self.access_log: List[Dict] = []
        self._create_simulated_filesystem()
    
    def _create_simulated_filesystem(self):
        """Create a simulated file system."""
        # System files
        self._add_file("/etc/passwd", "admin", "system", FilePermissions.from_octal("644"), False,
                      "root:x:0:0:root:/root\nadmin:x:1:1:admin:/home/admin", is_system=True)
        self._add_file("/etc/shadow", "admin", "system", FilePermissions.from_octal("600"), False,
                      "root:$encrypted$:19000:0", is_system=True)
        self._add_file("/etc/config", "admin", "system", FilePermissions.from_octal("644"), False,
                      "SHELL=/bin/myshell\nPATH=/usr/bin:/bin", is_system=True)
        
        # Directories
        self._add_file("/etc", "admin", "system", FilePermissions.from_octal("755"), True, is_system=True)
        self._add_file("/home", "admin", "users", FilePermissions.from_octal("755"), True)
        self._add_file("/home/admin", "admin", "admin", FilePermissions.from_octal("700"), True)
        self._add_file("/home/user1", "user1", "users", FilePermissions.from_octal("755"), True)
        self._add_file("/home/user2", "user2", "users", FilePermissions.from_octal("755"), True)
        self._add_file("/tmp", "admin", "users", FilePermissions.from_octal("777"), True)
        
        # User files
        self._add_file("/home/user1/document.txt", "user1", "users", FilePermissions.from_octal("644"), False,
                      "This is user1's document.\nIt contains some text.")
        self._add_file("/home/user1/private.txt", "user1", "users", FilePermissions.from_octal("600"), False,
                      "This is user1's private file.")
        self._add_file("/home/user1/script.sh", "user1", "users", FilePermissions.from_octal("755"), False,
                      "#!/bin/bash\necho 'Hello!'")
        self._add_file("/home/user2/notes.txt", "user2", "users", FilePermissions.from_octal("644"), False,
                      "User2's notes file.")
        self._add_file("/home/user2/secret.txt", "user2", "users", FilePermissions.from_octal("600"), False,
                      "User2's secret file.")
        self._add_file("/tmp/shared.txt", "admin", "users", FilePermissions.from_octal("666"), False,
                      "This is a shared file.")
    
    def _add_file(self, path: str, owner: str, group: str, permissions: FilePermissions, 
                  is_directory: bool, content: str = "", is_system: bool = False):
        name = os.path.basename(path) or path
        self.files[path] = SimulatedFile(name=name, path=path, owner=owner, group=group,
                                         permissions=permissions, is_directory=is_directory,
                                         content=content, is_system_file=is_system)
    
    def _log_access(self, user: User, path: str, action: str, allowed: bool, reason: str = ""):
        self.access_log.append({
            'timestamp': time.time(), 'user': user.username, 'role': user.role.value,
            'path': path, 'action': action, 'allowed': allowed, 'reason': reason
        })
    
    def _get_effective_permission(self, user: User, file: SimulatedFile) -> Permission:
        if user.role == UserRole.ADMIN:
            return Permission.RWX
        if file.owner == user.username:
            return file.permissions.owner
        if user.role == UserRole.STANDARD:
            return file.permissions.group
        return file.permissions.others
    
    def can_read(self, user: User, path: str) -> bool:
        if path not in self.files:
            return False
        file = self.files[path]
        effective = self._get_effective_permission(user, file)
        can = Permission.READ in effective
        self._log_access(user, path, "READ", can, "Granted" if can else "No permission")
        return can
    
    def can_write(self, user: User, path: str) -> bool:
        if path not in self.files:
            return False
        file = self.files[path]
        if file.is_system_file and user.role != UserRole.ADMIN:
            self._log_access(user, path, "WRITE", False, "System file")
            return False
        effective = self._get_effective_permission(user, file)
        can = Permission.WRITE in effective
        self._log_access(user, path, "WRITE", can, "Granted" if can else "No permission")
        return can
    
    def can_execute(self, user: User, path: str) -> bool:
        if path not in self.files:
            return False
        file = self.files[path]
        effective = self._get_effective_permission(user, file)
        can = Permission.EXECUTE in effective
        self._log_access(user, path, "EXECUTE", can, "Granted" if can else "No permission")
        return can
    
    def read_file(self, user: User, path: str) -> Optional[str]:
        if not self.can_read(user, path):
            self.callback(f"Permission denied: cannot read '{path}'")
            return None
        file = self.files[path]
        if file.is_directory:
            self.callback(f"Error: '{path}' is a directory")
            return None
        return file.content
    
    def write_file(self, user: User, path: str, content: str) -> bool:
        if path in self.files:
            if not self.can_write(user, path):
                self.callback(f"Permission denied: cannot write to '{path}'")
                return False
            file = self.files[path]
            if file.is_directory:
                self.callback(f"Error: '{path}' is a directory")
                return False
            file.content = content
            file.size = len(content)
            file.modified_at = time.time()
        else:
            name = os.path.basename(path)
            self.files[path] = SimulatedFile(name=name, path=path, owner=user.username,
                                            group="users", permissions=FilePermissions.from_octal("644"),
                                            content=content)
        return True
    
    def list_directory(self, user: User, path: str) -> Optional[List[SimulatedFile]]:
        if path not in self.files:
            self.callback(f"Error: '{path}' not found")
            return None
        file = self.files[path]
        if not file.is_directory:
            self.callback(f"Error: '{path}' is not a directory")
            return None
        if not self.can_execute(user, path):
            self.callback(f"Permission denied: cannot access '{path}'")
            return None
        
        contents = []
        prefix = path if path.endswith('/') else path + '/'
        for file_path, f in self.files.items():
            if file_path == path:
                continue
            if file_path.startswith(prefix):
                relative = file_path[len(prefix):]
                if '/' not in relative:
                    contents.append(f)
        return contents
    
    def chmod(self, user: User, path: str, mode: str) -> bool:
        if path not in self.files:
            self.callback(f"Error: '{path}' not found")
            return False
        file = self.files[path]
        if file.owner != user.username and user.role != UserRole.ADMIN:
            self.callback(f"Permission denied: only owner can change permissions")
            return False
        try:
            file.permissions = FilePermissions.from_octal(mode)
            self._log_access(user, path, "CHMOD", True, f"Changed to {mode}")
            return True
        except ValueError:
            self.callback(f"Error: invalid mode '{mode}'")
            return False
    
    def chown(self, user: User, path: str, new_owner: str) -> bool:
        if user.role != UserRole.ADMIN:
            self.callback("Permission denied: only admin can change ownership")
            return False
        if path not in self.files:
            self.callback(f"Error: '{path}' not found")
            return False
        self.files[path].owner = new_owner
        self._log_access(user, path, "CHOWN", True, f"New owner: {new_owner}")
        return True
    
    def get_file_info(self, path: str) -> Optional[Dict]:
        if path not in self.files:
            return None
        file = self.files[path]
        return {
            'name': file.name, 'path': file.path,
            'type': 'directory' if file.is_directory else 'file',
            'owner': file.owner, 'group': file.group,
            'permissions': str(file.permissions), 'octal': file.permissions.to_octal(),
            'size': file.size, 'system': file.is_system_file,
            'created': datetime.fromtimestamp(file.created_at).strftime('%Y-%m-%d %H:%M:%S'),
            'modified': datetime.fromtimestamp(file.modified_at).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def get_access_log(self, limit: int = 10) -> List[Dict]:
        return self.access_log[-limit:]
    
    def visualize_permissions(self, path: str) -> str:
        if path not in self.files:
            return f"File not found: {path}"
        file = self.files[path]
        p = file.permissions
        return f"\nFile: {path}\nType: {'Directory' if file.is_directory else 'File'}\nOwner: {file.owner}\nPermissions: {file.get_type_char()}{p} ({p.to_octal()})"


def create_permission_manager(callback: Callable = None) -> FilePermissionManager:
    """Factory function to create a file permission manager."""
    return FilePermissionManager(callback=callback)
