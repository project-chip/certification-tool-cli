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
Fix incorrect Optional type annotations with None defaults.

OpenAPI Generator v7.0.0 incorrectly generates fields with default values as:
    field_name: "Optional[type]" = Field(None, alias="field_name")

When they should be:
    field_name: type = Field(default_value, alias="field_name")

This script fixes these issues by:
1. Reading the OpenAPI spec to get the correct default values
2. Parsing the generated models file
3. Replacing incorrect Optional[T] = Field(None, ...) patterns with correct type = Field(default, ...)
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional


def load_openapi_spec(spec_path: Path) -> Dict[str, Any]:
    """Load and parse the OpenAPI specification file."""
    with open(spec_path, 'r') as f:
        return json.load(f)


def get_schema_defaults(openapi_spec: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract default values for all schema properties.
    
    Returns a nested dict: {schema_name: {property_name: {type, default}}}
    """
    schemas = openapi_spec.get('components', {}).get('schemas', {})
    defaults_map = {}
    
    for schema_name, schema_def in schemas.items():
        properties = schema_def.get('properties', {})
        schema_defaults = {}
        
        for prop_name, prop_def in properties.items():
            if 'default' in prop_def:
                prop_type = prop_def.get('type')
                default_value = prop_def['default']
                schema_defaults[prop_name] = {
                    'type': prop_type,
                    'default': default_value
                }
        
        if schema_defaults:
            defaults_map[schema_name] = schema_defaults
    
    return defaults_map


def python_value_repr(value: Any, type_hint: Optional[str] = None) -> str:
    """Convert a JSON value to its Python representation."""
    if value is None:
        return "None"
    elif isinstance(value, bool):
        return "True" if value else "False"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, dict):
        return "{}"
    elif isinstance(value, list):
        return "[]"
    else:
        return repr(value)


def get_python_type(json_type: str) -> str:
    """Map JSON schema types to Python type hints."""
    type_mapping = {
        'boolean': 'bool',
        'integer': 'int',
        'number': 'float',
        'string': 'str',
        'object': 'dict',
        'array': 'list'
    }
    return type_mapping.get(json_type, 'Any')


def fix_models_file(models_path: Path, defaults_map: Dict[str, Dict[str, Any]]) -> int:
    """
    Fix incorrect Optional type annotations in the models file.
    
    Returns the number of fixes applied.
    """
    with open(models_path, 'r') as f:
        content = f.read()
    
    original_content = content
    fixes_applied = 0
    
    # Pattern to match class definitions
    class_pattern = re.compile(r'^class\s+(\w+)\(', re.MULTILINE)
    
    # Pattern to match field definitions with Optional and None default
    # Example: certification_mode: "Optional[bool]" = Field(None, alias="certification_mode")
    field_pattern = re.compile(
        r'(\s+)(\w+):\s*"Optional\[([^\]]+)\]"\s*=\s*Field\(None,\s*alias="(\w+)"\)',
        re.MULTILINE
    )
    
    # Find all classes in the file
    current_class = None
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        class_match = class_pattern.match(line)
        if class_match:
            current_class = class_match.group(1)
            fixed_lines.append(line)
            continue
        
        # Check if this line has an Optional field with None default
        field_match = field_pattern.match(line)
        if field_match and current_class:
            indent = field_match.group(1)
            field_name = field_match.group(2)
            inner_type = field_match.group(3)
            alias_name = field_match.group(4)
            
            # Look up the default value in the schema
            if current_class in defaults_map and field_name in defaults_map[current_class]:
                schema_info = defaults_map[current_class][field_name]
                default_value = schema_info['default']
                json_type = schema_info['type']
                
                # Get the correct Python type
                python_type = get_python_type(json_type)
                
                # Format the default value for Python
                default_repr = python_value_repr(default_value, python_type)
                
                # Create the fixed line
                fixed_line = f'{indent}{field_name}: "{python_type}" = Field({default_repr}, alias="{alias_name}")'
                fixed_lines.append(fixed_line)
                fixes_applied += 1
                print(f"Fixed {current_class}.{field_name}: Optional[{inner_type}] = None -> {python_type} = {default_repr}")
                continue
        
        # No fix needed, keep the original line
        fixed_lines.append(line)
    
    # Write the fixed content back to the file
    if fixes_applied > 0:
        fixed_content = '\n'.join(fixed_lines)
        with open(models_path, 'w') as f:
            f.write(fixed_content)
    
    return fixes_applied


def main():
    parser = argparse.ArgumentParser(
        description='Fix incorrect Optional type annotations in generated models'
    )
    parser.add_argument(
        '--openapi-spec',
        type=Path,
        required=True,
        help='Path to the OpenAPI specification file'
    )
    parser.add_argument(
        '--models-file',
        type=Path,
        required=True,
        help='Path to the generated models.py file'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.openapi_spec.exists():
        print(f"Error: OpenAPI spec file not found: {args.openapi_spec}", file=sys.stderr)
        sys.exit(1)
    
    if not args.models_file.exists():
        print(f"Error: Models file not found: {args.models_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading OpenAPI spec from: {args.openapi_spec}")
    openapi_spec = load_openapi_spec(args.openapi_spec)
    
    print("Extracting default values from schema...")
    defaults_map = get_schema_defaults(openapi_spec)
    print(f"Found {len(defaults_map)} schemas with default values")
    
    print(f"Fixing models file: {args.models_file}")
    fixes_applied = fix_models_file(args.models_file, defaults_map)
    
    if fixes_applied > 0:
        print(f"✓ Applied {fixes_applied} fixes to Optional/default value issues")
    else:
        print("No fixes needed")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
