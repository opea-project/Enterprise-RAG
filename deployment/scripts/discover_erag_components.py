#!/usr/bin/env python3
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Discover ERAG components from deployment/components/ directory tree.

Scans for Chart.yaml files with annotation 'app.kubernetes.io/part-of: ERAG'
and outputs the list of expected components for deployment manifest tracking.
Excludes charts marked with 'dependency-only: true' annotation.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml


def load_chart_yaml(chart_path: Path) -> Optional[Dict]:
    """Load and parse a Chart.yaml file."""
    try:
        with open(chart_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        print(f"Warning: Failed to load {chart_path}: {e}", file=sys.stderr)
        return None


def is_erag_component(chart_data: Dict) -> bool:
    """Check if chart has ERAG part-of annotation."""
    annotations = chart_data.get('annotations', {})
    return annotations.get('app.kubernetes.io/part-of') == 'ERAG'


def is_dependency_only(chart_data: Dict) -> bool:
    """Check if chart is marked as dependency-only."""
    annotations = chart_data.get('annotations', {})
    return annotations.get('dependency-only') == 'true'


def discover_components(components_dir: Path) -> List[Dict[str, str]]:
    """
    Discover ERAG components by scanning for Chart.yaml files.
    Excludes charts marked with dependency-only annotation.

    Returns:
        List of component dictionaries with name, appVersion, chartVersion
    """
    components = []

    for chart_path in components_dir.rglob('Chart.yaml'):
        chart_data = load_chart_yaml(chart_path)

        if not chart_data:
            continue

        if not is_erag_component(chart_data):
            continue

        if is_dependency_only(chart_data):
            continue

        component = {
            'name': chart_data.get('name', 'unknown'),
            'appVersion': chart_data.get('appVersion', 'unknown'),
            'chartVersion': chart_data.get('version', 'unknown'),
            'chart_path': str(chart_path.parent)
        }

        components.append(component)

    return components


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <components_directory>", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print(f"  {sys.argv[0]} /path/to/deployment/components", file=sys.stderr)
        sys.exit(1)

    components_dir = Path(sys.argv[1])

    if not components_dir.exists():
        print(f"Error: Directory not found: {components_dir}", file=sys.stderr)
        sys.exit(1)

    if not components_dir.is_dir():
        print(f"Error: Not a directory: {components_dir}", file=sys.stderr)
        sys.exit(1)

    # Discover components
    components = discover_components(components_dir)

    # Sort by name for consistent output
    components.sort(key=lambda x: x['name'])

    # Output as JSON
    print(json.dumps(components, indent=2))

    # Summary to stderr
    print("", file=sys.stderr)
    print(f"Discovered {len(components)} ERAG components", file=sys.stderr)


if __name__ == '__main__':
    main()
