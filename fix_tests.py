#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to add --no-download --no-extract to all workflow test commands
that don't already have them, to make tests run faster.
"""

import os
import re
from pathlib import Path

def fix_test_file(file_path):
    """Fix a single test file by adding --no-download --no-extract where needed."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find all workflow command invocations
    # Pattern: workflows', 'WORKFLOW_NAME', followed by optional parameters, ending with ])
    pattern = r"(\s*)(self\.runner\.invoke\(cli,\s*\[\s*[\'\"])([^]]+workflows[^]]+)([\'\"],?\s*\]\))"
    
    def replace_func(match):
        indent = match.group(1)
        prefix = match.group(2)
        command_content = match.group(3)
        suffix = match.group(4)
        
        # Skip if it's a help command
        if '--help' in command_content:
            return match.group(0)
        
        # Skip if it already has --no-download or --no-extract or special options
        if ('--no-download' in command_content or 
            '--no-extract' in command_content or
            '--list-only' in command_content or
            '--show-entries' in command_content or
            '--count' in command_content):
            return match.group(0)
        
        # Skip if it's explicitly using --download or --extract
        if '--download' in command_content or '--extract' in command_content:
            return match.group(0)
        
        # Add --no-download --no-extract before the closing bracket
        new_command = command_content + ",\n" + indent + "            '--no-download', '--no-extract'"
        
        return indent + prefix + new_command + suffix
    
    new_content = re.sub(pattern, replace_func, content, flags=re.MULTILINE | re.DOTALL)
    
    # Only write if there were changes
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed: {file_path}")
        return True
    else:
        print(f"No changes needed: {file_path}")
        return False

def main():
    """Fix all test files in the workflows directory."""
    test_dir = Path("tests/workflows")
    if not test_dir.exists():
        print("tests/workflows directory not found!")
        return
    
    fixed_count = 0
    for test_file in test_dir.glob("test_*.py"):
        if fix_test_file(test_file):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} test files.")

if __name__ == "__main__":
    main()