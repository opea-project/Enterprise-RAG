#!/usr/bin/env python3
"""
Generate structured diff with hierarchical paths for configuration changes.

This script processes two text files (before/manifest and after/upgrade) and generates
a structured diff that shows:
1. Only the lines that actually changed (using difflib.unified_diff)
2. Hierarchical paths for context based on indentation
3. Smart grouping with flat-level diff handling:
   - Multiple lines at same indent level are grouped as flat-level diff
   - When followed by indented lines, a new block starts with path from context
   - Continue emitting nested block until indent reduces again
4. Separate blocks for removed (<<<) and added (>>>) lines

Output format:
  <<<:
  flat line 1
  flat line 2
  <<<path/to/nested:
  nested line 1
  nested line 2
  >>>path/to/nested:
  added line
  <<<>>>

Features:
- Plain text processing - no YAML parsing required
- Sequential line matching within diff hunks for accurate path resolution
- Flat-level and nested block separation
"""

import sys
import argparse
import difflib
import re
from typing import List, Tuple, Optional

# Compiled regex pattern for extracting valid keys from lines
# Key must:
# - Start and end with letter, digit, or underscore
# - May contain letters, digits, underscores, dashes, dots, colons, pipes, and spaces within
KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_](?:[a-zA-Z0-9_.\-:|\s]*[a-zA-Z0-9_])?$')

def get_line_indent(line: str) -> int:
    """Get indentation level of a line"""
    return len(line) - len(line.lstrip())

def extract_key_from_line(line: str) -> Optional[str]:
    """
    Extract key from a YAML-like line with robust validation.

    Valid keys must:
    - Start and end with letter, digit, or underscore
    - May contain letters, digits, underscores, dashes, dots, colons, pipes, and spaces within
    - All leading/trailing whitespace and invalid characters are stripped
    - Quoted keys (single or double quotes) are valid and returned unquoted

    Returns:
        The extracted key if valid, None otherwise
    """
    stripped = line.strip()

    # Find the position of the value separator (": " or ":\n")
    # This handles keys that contain colons by looking for ": " pattern
    separator_idx = -1
    if ': ' in stripped:
        separator_idx = stripped.index(': ')
    elif stripped.endswith(':'):
        separator_idx = len(stripped) - 1

    if separator_idx == -1:
        return None

    # Extract the part before the separator
    key_part = stripped[:separator_idx]

    # Strip leading list markers and whitespace
    key_part = key_part.lstrip('- \t')

    # Check if the key is quoted and extract it
    key_cleaned = key_part.strip()
    if (key_cleaned.startswith('"') and key_cleaned.endswith('"')) or \
       (key_cleaned.startswith("'") and key_cleaned.endswith("'")):
        # Remove quotes
        key_cleaned = key_cleaned[1:-1]

    # Strip all leading and trailing characters that are not letters, digits, underscores
    while key_cleaned and not (key_cleaned[0].isalnum() or key_cleaned[0] == '_'):
        key_cleaned = key_cleaned[1:]
    while key_cleaned and not (key_cleaned[-1].isalnum() or key_cleaned[-1] == '_'):
        key_cleaned = key_cleaned[:-1]

    # Validate the cleaned key against the pattern
    if key_cleaned and KEY_PATTERN.match(key_cleaned):
        return key_cleaned

    return None

def build_path_for_line_at_position(lines: List[str], line_idx: int) -> str:
    """
    Build hierarchical path for a line at a specific position in the content.

    Args:
        lines: All lines in the content (as list)
        line_idx: Index of the line to build path for

    Returns:
        Path string like "key1/key2/key3" or ":" for flat level
    """
    target_indent = get_line_indent(lines[line_idx])

    # Special case: if indent is 0, return empty path marker
    if target_indent == 0:
        return ":"

    # Build path by looking at parent keys
    path_parts = []
    current_indent = target_indent

    # Look backwards from target line to find parent keys
    for i in range(line_idx - 1, -1, -1):
        line = lines[i]
        if not line.strip():
            continue

        line_indent = get_line_indent(line)

        # If this line is less indented and has a key, it's a parent
        if line_indent < current_indent:
            key = extract_key_from_line(line)
            if key:
                path_parts.append(key)
                current_indent = line_indent

                # Stop at indent 0
                if line_indent == 0:
                    break

    # Reverse to get correct hierarchy (parent to child)
    if path_parts:
        return '/'.join(reversed(path_parts))
    else:
        return ":"

def find_line_in_content(lines: List[str], target_line: str, start_from: int = 0) -> int:
    """
    Find the index of a line in content, starting search from a given position.
    Returns -1 if not found.
    """
    for i in range(start_from, len(lines)):
        if lines[i] == target_line:
            return i
    return -1

def group_changed_lines_by_location(before_content: str, after_content: str) -> List[Tuple[List[Tuple[str, int, int]], List[Tuple[str, int, int]], int, int]]:
    """
    Group removed and added lines by their location in the diff.
    Returns list of (removed_lines, added_lines, before_line_num, after_line_num) tuples
    where each line is (content, indent_level, approx_line_number).
    """
    before_lines = before_content.split('\n')
    after_lines = after_content.split('\n')

    # Use unified_diff with n=0 to get minimal context
    diff = list(difflib.unified_diff(before_lines, after_lines, lineterm='', n=0))

    groups = []
    current_removed = []
    current_added = []
    current_before_line = 0
    current_after_line = 0
    hunk_before_line = 0
    hunk_after_line = 0

    for line in diff:
        if line.startswith('---') or line.startswith('+++'):
            continue
        elif line.startswith('@@'):
            # Parse hunk header to get line numbers
            # Format: @@ -start,count +start,count @@
            import re
            match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
            if match:
                hunk_before_line = int(match.group(1)) - 1  # Convert to 0-indexed
                hunk_after_line = int(match.group(2)) - 1  # Convert to 0-indexed

            # New hunk, save previous group if any
            if current_removed or current_added:
                groups.append((current_removed, current_added, current_before_line, current_after_line))
                current_removed = []
                current_added = []

            current_before_line = hunk_before_line
            current_after_line = hunk_after_line
        elif line.startswith('-'):
            actual_line = line[1:]
            if actual_line.strip():  # Skip empty lines
                current_removed.append((actual_line, get_line_indent(actual_line), current_before_line))
            current_before_line += 1
        elif line.startswith('+'):
            actual_line = line[1:]
            if actual_line.strip():  # Skip empty lines
                current_added.append((actual_line, get_line_indent(actual_line), current_after_line))
            current_after_line += 1
        elif line.startswith(' '):
            # Context line, advance both counters
            current_before_line += 1
            current_after_line += 1

    # Don't forget the last group
    if current_removed or current_added:
        groups.append((current_removed, current_added, current_before_line, current_after_line))

    return groups

def emit_block(changed_lines: List[Tuple[str, int, int]], content_lines: List[str], prefix: str) -> List[str]:
    """
    Emit a block of lines with intelligent path management.
    Returns list of output lines.

    Rules:
    - Indent 0 only = flat level (path is ":")
    - Any indent > 0 = nested level (build hierarchical path from parent keys)
    - Emit new path when:
      * First line of hunk
      * Returning to reference indent or shallower
      * Different context at same/shallower level

    Args:
        changed_lines: List of (content, indent_level, approx_line_number) tuples
        content_lines: The source content as list of lines
        prefix: Prefix for output ("<<<" or ">>>")
    """
    if not changed_lines:
        return []

    result = []

    # Track the reference indent level (from first line) - used for transition detection
    reference_indent = changed_lines[0][1]

    # Track current state
    current_path = None
    last_indent = None

    for line_content, line_indent, approx_line_num in changed_lines:
        # Find this line in content, searching near the approximate line number
        # Search FORWARD from the approximate location first, then backward
        # This ensures we find the correct occurrence when there are duplicates
        line_idx = -1

        # First, try exact position
        if approx_line_num < len(content_lines) and content_lines[approx_line_num] == line_content:
            line_idx = approx_line_num
        else:
            # Search forward first (more likely for additions/modifications)
            search_end = min(len(content_lines), approx_line_num + 10)
            for i in range(approx_line_num + 1, search_end):
                if content_lines[i] == line_content:
                    line_idx = i
                    break

            # If not found forward, search backward
            if line_idx == -1:
                search_start = max(0, approx_line_num - 5)
                for i in range(approx_line_num - 1, search_start - 1, -1):
                    if content_lines[i] == line_content:
                        line_idx = i
                        break

        if line_idx == -1:
            # Fallback: use empty path for indent 0, otherwise try to build from context
            path = ":" if line_indent == 0 else ":"
        else:
            # Build path based on actual position and indent
            if line_indent == 0:
                # Flat level - use empty path
                path = ":"
            else:
                # Nested level - build full hierarchical path
                path = build_path_for_line_at_position(content_lines, line_idx)

        # Determine if we need to emit a new path header
        need_new_path = False

        if current_path is None:
            # First line always needs path
            need_new_path = True
        elif last_indent is not None:
            # Check for transitions
            # 1. Leaving flat level (indent 0) to nested level
            #    This is the only case where indent increase should emit new path
            if reference_indent == 0 and last_indent == 0 and line_indent > 0:
                need_new_path = True
            # 2. Returning to reference indent or shallower
            elif line_indent <= reference_indent and last_indent > reference_indent:
                need_new_path = True
            # 3. Indent decreased (shallower) - always emit new path
            elif line_indent < last_indent:
                need_new_path = True

        if need_new_path:
            # Add colon suffix if path doesn't already end with it
            path_with_colon = path if path.endswith(':') else f'{path}:'
            result.append(f'{prefix}{path_with_colon}')
            current_path = path

        result.append(line_content)
        last_indent = line_indent

    return result

def generate_structured_diff(before_content: str, after_content: str) -> str:
    """Generate structured diff with smart context path management"""
    result_lines = []

    # Group changes by location
    groups = group_changed_lines_by_location(before_content, after_content)

    before_lines = before_content.split('\n')
    after_lines = after_content.split('\n')

    for removed_lines, added_lines, before_line_num, after_line_num in groups:
        # Emit removed block (use before_content)
        removed_output = emit_block(removed_lines, before_lines, '<<<')
        result_lines.extend(removed_output)

        # Emit added block (use after_content - important!)
        added_output = emit_block(added_lines, after_lines, '>>>')
        result_lines.extend(added_output)

    # Add final marker
    if result_lines:
        result_lines.append('<<<>>>')

    return '\n'.join(result_lines)

def main():
    parser = argparse.ArgumentParser(description='Generate structured diff with hierarchical paths')
    parser.add_argument('before_file', help='Path to before/manifest file')
    parser.add_argument('after_file', help='Path to after/upgrade file')
    parser.add_argument('output_file', help='Path to output diff file')

    args = parser.parse_args()

    try:
        # Load the files as plain text with UTF-8 encoding
        with open(args.before_file, 'r', encoding='utf-8') as f:
            before_content = f.read()

        with open(args.after_file, 'r', encoding='utf-8') as f:
            after_content = f.read()

        # Generate structured diff
        structured_diff = generate_structured_diff(before_content, after_content)

        # Write to output file with UTF-8 encoding
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(structured_diff)

        print('Structured diff generated successfully')

    except Exception as e:
        print(f'Error generating structured diff: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()