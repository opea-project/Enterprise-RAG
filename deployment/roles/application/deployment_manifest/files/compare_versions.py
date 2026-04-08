#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Compare versions for upgrade mode detection and constraint checking.

Modes:
1. Version comparison (default): Compare DEPLOYED_VERSION and INSTALLING_VERSION
2. Constraint check: Check if source satisfies upgrade constraint (set UPGRADE_CONSTRAINT)

Build metadata (after '+') is stripped for comparison but preserved in output.
"""

from packaging import version
from packaging.specifiers import SpecifierSet, InvalidSpecifier
import sys
import json
import os
import re

def strip_build_metadata(ver_str):
    """Remove build metadata (after +) for comparison."""
    if '+' in ver_str:
        return ver_str.split('+')[0]
    return ver_str

def parse_version_parts(ver_str):
    """Extract major.minor.patch parts."""
    clean = strip_build_metadata(ver_str)
    clean = re.split(r'[-+]', clean)[0]
    parts = clean.split('.')
    parsed = []
    for p in parts[:3]:
        try:
            parsed.append(int(re.match(r'\d+', p).group() if re.match(r'\d+', p) else 0))
        except (AttributeError, ValueError):
            parsed.append(0)
    while len(parsed) < 3:
        parsed.append(0)
    return parsed

def check_upgrade_constraint(source_version, target_version, upgrade_constraint):
    """
    Check if source version satisfies upgrade constraint.
    Supports PEP440 expressions: >=, >, ==, <=, <, ~=, !=

    Returns dict with 'allowed', 'reason', and metadata.
    """
    result = {
        'source_version': source_version,
        'target_version': target_version,
        'upgrade_constraint': upgrade_constraint,
        'allowed': False,
        'reason': ''
    }

    if not upgrade_constraint or upgrade_constraint.strip() == '':
        result['allowed'] = True
        result['reason'] = 'No constraint specified'
        return result

    if upgrade_constraint.lower() == 'unsupported':
        result['allowed'] = False
        result['reason'] = f'Target {target_version} does not support upgrades'
        return result

    try:
        source_clean = strip_build_metadata(source_version)
        target_clean = strip_build_metadata(target_version)

        source_ver = version.parse(source_clean)
        target_ver = version.parse(target_clean)
    except version.InvalidVersion as e:
        result['allowed'] = False
        result['reason'] = f'Invalid version format: {e}'
        return result

    if source_ver >= target_ver:
        result['allowed'] = False
        result['reason'] = f'Downgrade not allowed: {source_version} >= {target_version}'
        return result

    constraint_expr = upgrade_constraint.strip()
    if not re.match(r'^[><=!~]+\d', constraint_expr):
        constraint_expr = f'>={constraint_expr}'

    upper_bound = f'<{target_clean}'
    combined = f'{constraint_expr},{upper_bound}'

    try:
        specifier = SpecifierSet(combined)
        base_specifier = SpecifierSet(constraint_expr)
    except InvalidSpecifier as e:
        result['allowed'] = False
        result['reason'] = f'Invalid constraint: {upgrade_constraint} ({e})'
        return result

    if source_ver in specifier:
        result['allowed'] = True
        result['reason'] = f'{source_version} satisfies {upgrade_constraint} and < {target_version}'
    else:
        result['allowed'] = False
        if source_ver not in base_specifier:
            result['reason'] = f'{source_version} does not satisfy {upgrade_constraint}'
        else:
            result['reason'] = f'{source_version} >= {target_version}'

    result['constraint_parsed'] = combined

    return result

def compare_versions(deployed_version, installing_version):
    """Compare versions and determine upgrade mode."""
    deployed_clean = strip_build_metadata(deployed_version)
    installing_clean = strip_build_metadata(installing_version)

    try:
        deployed = version.parse(deployed_clean)
        installing = version.parse(installing_clean)
    except version.InvalidVersion as e:
        return {
            "error": f"Invalid version format: {e}",
            "mode": "invalid"
        }

    deployed_parts = parse_version_parts(deployed_version)
    installing_parts = parse_version_parts(installing_version)

    if installing > deployed:
        if installing_parts[0] > deployed_parts[0]:
            mode = "major_upgrade"
        elif installing_parts[1] > deployed_parts[1]:
            mode = "minor_upgrade"
        else:
            mode = "patch_upgrade"
    elif installing < deployed:
        mode = "downgrade"
    else:
        mode = "refresh"

    return {
        "mode": mode,
        "deployed_version": deployed_version,
        "installing_version": installing_version,
        "deployed_clean": deployed_clean,
        "installing_clean": installing_clean
    }

if __name__ == '__main__':
    if 'UPGRADE_CONSTRAINT' in os.environ:
        upgrade_constraint = os.environ.get('UPGRADE_CONSTRAINT', '')
        source_version = os.environ.get('SOURCE_VERSION', '')
        target_version = os.environ.get('TARGET_VERSION', '')

        if not source_version:
            print(json.dumps({
                'error': 'Missing SOURCE_VERSION environment variable',
                'allowed': False
            }))
            sys.exit(1)

        if not target_version:
            print(json.dumps({
                'error': 'Missing TARGET_VERSION environment variable',
                'allowed': False
            }))
            sys.exit(1)

        result = check_upgrade_constraint(source_version, target_version, upgrade_constraint)
        print(json.dumps(result, indent=2))

        if not result['allowed']:
            sys.exit(1)
    else:
        deployed_version = os.environ.get('DEPLOYED_VERSION', '')
        installing_version = os.environ.get('INSTALLING_VERSION', '')

        if not deployed_version or not installing_version:
            print(json.dumps({
                "error": "Missing DEPLOYED_VERSION or INSTALLING_VERSION environment variable",
                "mode": "invalid"
            }))
            sys.exit(1)

        result = compare_versions(deployed_version, installing_version)
        print(json.dumps(result))

        if result.get('mode') == 'invalid':
            sys.exit(1)
