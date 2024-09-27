#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -e
set -o pipefail

# !TODO install gaudi drivers & plugin

# Prepare directories & permissions
sudo mkdir -p /mnt/opea-models
sudo chmod 755 /mnt/opea-models

# Increate inotify_instances for telemetry
sudo sysctl -w fs.inotify.max_user_instances=8192
