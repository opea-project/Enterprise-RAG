#!/usr/bin/env python3
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Transform Helm manifest files for comparison - extracts ConfigMap data and normalizes content."""

import re
import sys
from collections import deque

import yaml


def sanitize_yaml_content(content):
    if content.startswith('"') and content.endswith('"'):
        content = content[1:-1]
    content = content.replace('\\n', '\n')
    return content

def transform_lines(content):
    lines = content.split('\n')
    processed_lines = []
    for line in lines:
        line = line.rstrip()
        if not line or line.isspace():
            continue
        if line.strip().startswith('#'):
            continue
        if '#' in line:
            in_quotes = False
            quote_char = None
            for i, char in enumerate(line):
                if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    if not in_quotes:
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        in_quotes = False
                        quote_char = None
                elif char == '#' and not in_quotes:
                    line = line[:i].rstrip()
                    break
        if line:
            processed_lines.append(line)
    return '\n'.join(processed_lines)

def normalize_key(filename):
    base = filename.lower()
    normalized = re.sub(r'[^a-z0-9]', '-', base)
    normalized = re.sub(r'-+', '-', normalized).strip('-')
    return normalized

def is_file_data_key(key):
    return '.' in key and not key.startswith('.')

def is_yaml_file(key):
    return key.lower().endswith(('.yaml', '.yml'))

def has_document_separators(content):
    return '---' in content

def sort_yaml_keys(content):
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            return yaml.dump(data, default_flow_style=False, sort_keys=True)
        return content
    except (yaml.YAMLError, ValueError, TypeError):
        return content

def has_file_keys(configmap_data):
    if not configmap_data:
        return False
    return any(is_file_data_key(key) for key in configmap_data.keys())

def parse_yaml_documents(content):
    try:
        docs = list(yaml.safe_load_all(content))
        return [doc for doc in docs if doc is not None]
    except (yaml.YAMLError, ValueError, TypeError):
        return []

def process_file(filepath):
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, list):
        data = [data] if data else []
    resource_queue = deque(data)
    result = {}
    while resource_queue:
        resource = resource_queue.popleft()
        if not resource or resource.get('kind') != 'ConfigMap':
            continue
        configmap_name = resource.get('metadata', {}).get('name', 'unknown')
        configmap_data = resource.get('data', {})
        if not configmap_data:
            continue
        if has_file_keys(configmap_data):
            has_nested_configmaps = False
            for key, value in configmap_data.items():
                if is_file_data_key(key):
                    if key.lower().endswith('.sh'):
                        continue
                    if is_yaml_file(key):
                        sanitized_content = sanitize_yaml_content(value)
                        if has_document_separators(sanitized_content):
                            nested_resources = parse_yaml_documents(sanitized_content)
                            for nested_resource in nested_resources:
                                if nested_resource and nested_resource.get('kind') == 'ConfigMap':
                                    resource_queue.append(nested_resource)
                                    has_nested_configmaps = True
                            if not has_nested_configmaps:
                                normalized_key = normalize_key(key)
                                combined_key = f'{configmap_name}-{normalized_key}'
                                transformed_content = transform_lines(sanitized_content)
                                final_content = sort_yaml_keys(transformed_content)
                                result[combined_key] = final_content
                        else:
                            normalized_key = normalize_key(key)
                            combined_key = f'{configmap_name}-{normalized_key}'
                            transformed_content = transform_lines(sanitized_content)
                            final_content = sort_yaml_keys(transformed_content)
                            result[combined_key] = final_content
                    else:
                        normalized_key = normalize_key(key)
                        combined_key = f'{configmap_name}-{normalized_key}'
                        final_content = transform_lines(value)
                        result[combined_key] = final_content
        else:
            config_lines = []
            for key, value in sorted(configmap_data.items()):
                transformed_value = transform_lines(str(value))
                config_lines.append(f'{key}: {transformed_value}')
            if config_lines:
                result[configmap_name] = '\n'.join(config_lines)
    return result

def dict_to_yaml_list(data_dict):
    yaml_lines = []
    for key, value in sorted(data_dict.items()):
        yaml_lines.append(f'- {key}: |')
        for line in value.split('\n'):
            if line.strip():
                yaml_lines.append(f'    {line}')
    return '\n'.join(yaml_lines)

def normalize_quotes(content):
    """Normalize quotes in YAML content to use double quotes consistently.

    This prevents formatting differences between single and double quotes
    from causing false positives in diff detection.
    """
    lines = content.split('\n')
    normalized_lines = []

    for line in lines:
        # Skip lines that don't contain quotes
        if "'" not in line and '"' not in line:
            normalized_lines.append(line)
            continue

        # Process the line to normalize quotes
        # Handle YAML values with single quotes - convert to double quotes
        # Pattern: key: 'value' -> key: "value"
        # Also handle: - 'value' -> - "value"

        # Find the colon or list marker position
        if ': ' in line:
            prefix_end = line.index(': ') + 2
            prefix = line[:prefix_end]
            value_part = line[prefix_end:]
        elif line.lstrip().startswith('- '):
            prefix = line[:line.index('- ') + 2]
            value_part = line[len(prefix):]
        else:
            normalized_lines.append(line)
            continue

        # Normalize quotes in value part only
        # Replace 'value' with "value" while preserving escaped quotes
        if value_part.strip().startswith("'") and value_part.strip().endswith("'"):
            # Simple single-quoted string
            value_content = value_part.strip()[1:-1]
            normalized_value = f'"{value_content}"'
            normalized_line = prefix + value_part.replace(value_part.strip(), normalized_value, 1)
            normalized_lines.append(normalized_line)
        else:
            normalized_lines.append(line)

    return '\n'.join(normalized_lines)

def main():
    if len(sys.argv) != 5:
        print("Usage: manifest_transformer.py <manifest_file> <upgrade_file> <manifest_output> <upgrade_output>", file=sys.stderr)
        sys.exit(1)
    manifest_file = sys.argv[1]
    upgrade_file = sys.argv[2]
    manifest_output = sys.argv[3]
    upgrade_output = sys.argv[4]
    manifest_result = process_file(manifest_file)
    upgrade_result = process_file(upgrade_file)

    # Convert to YAML and normalize quotes
    manifest_yaml = normalize_quotes(dict_to_yaml_list(manifest_result))
    upgrade_yaml = normalize_quotes(dict_to_yaml_list(upgrade_result))

    with open(manifest_output, 'w') as f:
        f.write(manifest_yaml)
    with open(upgrade_output, 'w') as f:
        f.write(upgrade_yaml)
    print('Files processed successfully')

if __name__ == '__main__':
    main()
