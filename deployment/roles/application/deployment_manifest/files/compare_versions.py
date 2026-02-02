#!/usr/bin/env python3
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from packaging import version
import sys
import json
import os

deployed_version = os.environ.get('DEPLOYED_VERSION', '')
installing_version = os.environ.get('INSTALLING_VERSION', '')

if not deployed_version or not installing_version:
    print(json.dumps({
        "error": "Missing DEPLOYED_VERSION or INSTALLING_VERSION environment variable",
        "mode": "invalid"
    }))
    sys.exit(1)

try:
    deployed = version.parse(deployed_version)
    installing = version.parse(installing_version)
except Exception as e:
    print(json.dumps({
        "error": f"Invalid version format: {e}",
        "mode": "invalid"
    }))
    sys.exit(1)

if installing > deployed:
    deployed_parts = str(deployed).split('.')
    installing_parts = str(installing).split('.')

    max_len = max(len(deployed_parts), len(installing_parts))
    deployed_parts += ['0'] * (max_len - len(deployed_parts))
    installing_parts += ['0'] * (max_len - len(installing_parts))

    if len(deployed_parts) >= 1 and len(installing_parts) >= 1:
        if int(installing_parts[0]) > int(deployed_parts[0]):
            mode = "major_upgrade"
        elif len(deployed_parts) >= 2 and len(installing_parts) >= 2 and int(installing_parts[1]) > int(deployed_parts[1]):
            mode = "minor_upgrade"
        else:
            mode = "patch_upgrade"
    else:
        mode = "patch_upgrade"
elif installing < deployed:
    mode = "downgrade"
else:
    mode = "refresh"

result = {
    "mode": mode,
    "deployed_version": deployed_version,
    "installing_version": installing_version
}
print(json.dumps(result))
