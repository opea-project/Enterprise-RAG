#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
Compare solution versions for upgrade mode detection.
Supports semantic versioning with build metadata handling.
Build metadata (text after '+') is stripped for comparison but preserved in output.
"""

from packaging import version
import sys
import json
import os
import re

def strip_build_metadata(ver_str):
    """Remove build metadata (part after +) for comparison purposes."""
    if '+' in ver_str:
        return ver_str.split('+')[0]
    return ver_str

def parse_version_parts(ver_str):
    """Extract major.minor.patch parts from version string."""
    clean = strip_build_metadata(ver_str)
    clean = re.split(r'[-+]', clean)[0]
    parts = clean.split('.')
    result = []
    for p in parts[:3]:
        try:
            result.append(int(re.match(r'\d+', p).group() if re.match(r'\d+', p) else 0))
        except (AttributeError, ValueError):
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return result

deployed_version = os.environ.get('DEPLOYED_VERSION', '')
installing_version = os.environ.get('INSTALLING_VERSION', '')

if not deployed_version or not installing_version:
    print(json.dumps({
        "error": "Missing DEPLOYED_VERSION or INSTALLING_VERSION environment variable",
        "mode": "invalid"
    }))
    sys.exit(1)

deployed_clean = strip_build_metadata(deployed_version)
installing_clean = strip_build_metadata(installing_version)

try:
    deployed = version.parse(deployed_clean)
    installing = version.parse(installing_clean)
except Exception as e:
    print(json.dumps({
        "error": f"Invalid version format: {e}",
        "mode": "invalid"
    }))
    sys.exit(1)

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

result = {
    "mode": mode,
    "deployed_version": deployed_version,
    "installing_version": installing_version,
    "deployed_clean": deployed_clean,
    "installing_clean": installing_clean
}
print(json.dumps(result))
