#!/usr/bin/env python3
#
# Copyright (c) 2025-2026 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Fix missing type annotations in the auto-generated api_response.py file.

OpenAPI Generator creates an ApiResponse class with an __init__ method that
lacks type annotations, which causes mypy errors with the no-untyped-def check.

This script adds proper type annotations to the __init__ method.
"""

import argparse
import re
import sys
from pathlib import Path


def fix_api_response_init(api_response_path: Path) -> bool:
    """
    Fix the __init__ method in api_response.py to include type annotations.
    
    Returns True if a fix was applied, False otherwise.
    """
    if not api_response_path.exists():
        print(f"Warning: {api_response_path} not found, skipping api_response fix")
        return False
    
    with open(api_response_path, 'r') as f:
        content = f.read()
    
    # Pattern to match the untyped __init__ method (flexible with whitespace)
    # Matches: def __init__(self, status_code=None, headers=None, data=None, raw_data=None):
    # with flexible whitespace handling
    pattern = re.compile(
        r'(\s+)def\s+__init__\s*\(\s*self\s*,\s*status_code\s*=\s*None\s*,\s*headers\s*=\s*None\s*,\s*data\s*=\s*None\s*,\s*raw_data\s*=\s*None\s*\)\s*:',
        re.MULTILINE
    )
    
    # Check if the pattern exists
    match = pattern.search(content)
    if not match:
        # Check if it's already typed (look for type annotations in __init__)
        if re.search(r'def\s+__init__\s*\([^)]*:\s*Optional', content):
            print("api_response.py __init__ method already has type annotations")
            return False
        else:
            print("Warning: api_response.py __init__ method has unexpected format, skipping")
            return False
    
    # Replace with properly typed version (preserve the original indentation)
    replacement = r'\1def __init__(self, status_code: Optional[StrictInt] = None, headers: Optional[Dict[StrictStr, StrictStr]] = None, data: Optional[Any] = None, raw_data: Optional[Any] = None) -> None:'
    
    fixed_content = pattern.sub(replacement, content)
    
    # Write the fixed content back
    with open(api_response_path, 'w') as f:
        f.write(fixed_content)
    
    print("✓ Fixed api_response.py __init__ method with proper type annotations")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Fix missing type annotations in api_response.py'
    )
    parser.add_argument(
        '--api-response-file',
        type=Path,
        required=True,
        help='Path to the generated api_response.py file'
    )
    
    args = parser.parse_args()
    
    fix_applied = fix_api_response_init(args.api_response_file)
    
    # Always return success - if the file is already fixed or has an unexpected
    # format, we don't want to fail the entire generation process
    return 0


if __name__ == '__main__':
    sys.exit(main())
