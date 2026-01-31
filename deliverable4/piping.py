#!/usr/bin/env python3
"""
Piping Module for Deliverable 4
"""

import os
import subprocess
import shlex
import re
from typing import List, Tuple, Callable
from dataclasses import dataclass


class PipeError(Exception):
    pass


@dataclass
class PipeCommand:
    command: str
    args: List[str]
    raw: str
    def __str__(self) -> str:
        return self.raw


@dataclass
class PipeResult:
    success: bool
    output: str
    error: str
    commands: List[str]
    exit_codes: List[int]
    def __str__(self) -> str:
        return self.output if self.success else self.error


class PipeExecutor:
    def __init__(self, callback: Callable = None):
        self.callback = callback or print
        self.pipeable_builtins = {'cat', 'echo', 'ls', 'grep', 'sort', 'head', 'tail', 'wc', 'uniq', 'tr', 'cut', 'pwd'}
        self.total_pipes_executed = 0
        self.successful_pipes = 0
    
    def is_piped_command(self, command_line: str) -> bool:
        in_single = in_double = False
        for char in command_line:
            if char == "'" and not in_double: in_single = not in_single
            elif char == '"' and not in_single: in_double = not in_double
            elif char == '|' and not in_single and not in_double: return True
        return False
    
    def parse_pipeline(self, command_line: str) -> List[PipeCommand]:
        commands = []
        current = ""
        in_single = in_double = False
        
        for char in command_line:
            if char == "'" and not in_double:
                in_single = not in_single
                current += char
            elif char == '"' and not in_single:
                in_double = not in_double
                current += char
            elif char == '|' and not in_single and not in_double:
                current = current.strip()
                if current:
                    args = shlex.split(current)
                    commands.append(PipeCommand(command=args[0] if args else "", args=args, raw=current))
                current = ""
            else:
                current += char
        
        current = current.strip()
        if current:
            args = shlex.split(current)
            commands.append(PipeCommand(command=args[0] if args else "", args=args, raw=current))
        return commands
    
    def execute_builtin(self, cmd: PipeCommand, input_data: str = "") -> Tuple[str, str, int]:
        command, args = cmd.command, cmd.args
        try:
            if command == 'echo':
                return ' '.join(args[1:]) + '\n', "", 0
            
            elif command == 'cat':
                if len(args) > 1:
                    output = ""
                    for filepath in args[1:]:
                        try:
                            with open(filepath, 'r') as f: output += f.read()
                        except FileNotFoundError:
                            return "", f"cat: {filepath}: No such file\n", 1
                    return output, "", 0
                return input_data, "", 0
            
            elif command == 'grep':
                if len(args) < 2: return "", "grep: missing pattern\n", 1
                pattern = args[1]
                text = input_data
                if len(args) > 2:
                    try:
                        with open(args[2], 'r') as f: text = f.read()
                    except FileNotFoundError:
                        return "", f"grep: {args[2]}: No such file\n", 1
                
                ignore_case = '-i' in args
                try:
                    regex = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
                except re.error as e:
                    return "", f"grep: invalid pattern: {e}\n", 1
                
                matches = [l for l in text.split('\n') if regex.search(l)]
                output = '\n'.join(matches)
                if output and not output.endswith('\n'): output += '\n'
                return output, "", 0
            
            elif command == 'sort':
                text = input_data
                if len(args) > 1 and not args[1].startswith('-'):
                    try:
                        with open(args[1], 'r') as f: text = f.read()
                    except FileNotFoundError:
                        return "", f"sort: {args[1]}: No such file\n", 1
                reverse = '-r' in args
                lines = [l for l in text.split('\n') if l]
                lines.sort(reverse=reverse)
                output = '\n'.join(lines)
                if output: output += '\n'
                return output, "", 0
            
            elif command == 'head':
                text, n = input_data, 10
                for i, arg in enumerate(args[1:], 1):
                    if arg == '-n' and i + 1 < len(args):
                        try: n = int(args[i + 1])
                        except: pass
                    elif not arg.startswith('-'):
                        try:
                            with open(arg, 'r') as f: text = f.read()
                        except FileNotFoundError:
                            return "", f"head: {arg}: No such file\n", 1
                lines = text.split('\n')[:n]
                output = '\n'.join(lines)
                if output and not output.endswith('\n'): output += '\n'
                return output, "", 0
            
            elif command == 'tail':
                text, n = input_data, 10
                for i, arg in enumerate(args[1:], 1):
                    if arg == '-n' and i + 1 < len(args):
                        try: n = int(args[i + 1])
                        except: pass
                    elif not arg.startswith('-'):
                        try:
                            with open(arg, 'r') as f: text = f.read()
                        except FileNotFoundError:
                            return "", f"tail: {arg}: No such file\n", 1
                lines = text.rstrip('\n').split('\n')[-n:]
                output = '\n'.join(lines)
                if output and not output.endswith('\n'): output += '\n'
                return output, "", 0
            
            elif command == 'wc':
                text = input_data
                if len(args) > 1 and not args[1].startswith('-'):
                    try:
                        with open(args[1], 'r') as f: text = f.read()
                    except FileNotFoundError:
                        return "", f"wc: {args[1]}: No such file\n", 1
                lines, words, chars = text.count('\n'), len(text.split()), len(text)
                if '-l' in args: output = f"{lines}\n"
                elif '-w' in args: output = f"{words}\n"
                elif '-c' in args: output = f"{chars}\n"
                else: output = f"  {lines}  {words}  {chars}\n"
                return output, "", 0
            
            elif command == 'uniq':
                text = input_data
                lines, result, prev = text.split('\n'), [], None
                for line in lines:
                    if line != prev:
                        if prev is not None: result.append(prev)
                        prev = line
                if prev: result.append(prev)
                output = '\n'.join(result)
                if output and not output.endswith('\n'): output += '\n'
                return output, "", 0
            
            elif command == 'ls':
                path = '.' if len(args) == 1 else args[1]
                try:
                    entries = os.listdir(path)
                    return '\n'.join(entries) + '\n', "", 0
                except FileNotFoundError:
                    return "", f"ls: {path}: No such directory\n", 1
            
            elif command == 'pwd':
                return os.getcwd() + '\n', "", 0
            
            else:
                return "", f"Builtin '{command}' not supported\n", 1
        except Exception as e:
            return "", f"{command}: error: {e}\n", 1
    
    def execute_external(self, cmd: PipeCommand, input_data: str = "") -> Tuple[str, str, int]:
        try:
            process = subprocess.Popen(cmd.args, stdin=subprocess.PIPE if input_data else None,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input=input_data if input_data else None)
            return stdout, stderr, process.returncode
        except FileNotFoundError:
            return "", f"{cmd.command}: command not found\n", 127
        except Exception as e:
            return "", f"{cmd.command}: {e}\n", 1
    
    def execute_pipeline(self, command_line: str, use_builtins: bool = True) -> PipeResult:
        self.total_pipes_executed += 1
        try:
            commands = self.parse_pipeline(command_line)
        except Exception as e:
            return PipeResult(success=False, output="", error=str(e), commands=[command_line], exit_codes=[1])
        
        if not commands:
            return PipeResult(success=False, output="", error="Empty pipeline", commands=[], exit_codes=[])
        
        current_input = ""
        exit_codes = []
        command_strs = [str(cmd) for cmd in commands]
        self.callback(f"\n[Executing: {' | '.join(command_strs)}]")
        
        for i, cmd in enumerate(commands):
            self.callback(f"  Stage {i+1}: {cmd.command}")
            if use_builtins and cmd.command in self.pipeable_builtins:
                output, error, code = self.execute_builtin(cmd, current_input)
            else:
                output, error, code = self.execute_external(cmd, current_input)
            
            exit_codes.append(code)
            if code != 0:
                return PipeResult(success=False, output=current_input, error=error,
                                 commands=command_strs, exit_codes=exit_codes)
            current_input = output
        
        self.successful_pipes += 1
        return PipeResult(success=True, output=current_input, error="", commands=command_strs, exit_codes=exit_codes)
    
    def get_stats(self) -> dict:
        return {
            'total_executed': self.total_pipes_executed,
            'successful': self.successful_pipes,
            'failed': self.total_pipes_executed - self.successful_pipes,
            'success_rate': (self.successful_pipes / self.total_pipes_executed * 100 
                           if self.total_pipes_executed > 0 else 0)
        }


def create_pipe_executor(callback: Callable = None) -> PipeExecutor:
    return PipeExecutor(callback=callback)
