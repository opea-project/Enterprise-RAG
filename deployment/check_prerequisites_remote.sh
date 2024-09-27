#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


GAUDI_DRIVER_VERSION=${1:"1.17.1"}
CSI_MNT_DIR=/mnt
DESIRED_INOTIFY_INSTANCES=8192
CSI_MNT_DIR_PERMISSION=755

all_requirements_met=true

# Verify if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Print error msg & set flag
print_err() {
    echo "Error: $1"; all_requirements_met=false
}


# Check Gaudi drivers installation
if command_exists hl-smi; then
    current_gaudi_driver_version=$(hl-smi -v | awk '{print $3}'2>&1)
    if [[ "$current_gaudi_driver_version" =~ $GAUDI_DRIVER_VERSION ]]; then
        echo "Gaudi driver installation is correct."
    else
        print_err "Gaudi driver version is not $GAUDI_DRIVER_VERSION. Current version: $current_gaudi_driver_version."
    fi
else
    print_err "Gaudi driver is not installed."
fi

# Check fs.inotify.max_user_instances
current_inotify_instances=$(sysctl -n fs.inotify.max_user_instances)
if [ "$current_inotify_instances" -ge "$DESIRED_INOTIFY_INSTANCES" ]; then
    echo "The current value of fs.inotify.max_user_instances $current_inotify_instances is correct."
else
    print_err "The current value of fs.inotify.max_user_instances $current_inotify_instances higher than $DESIRED_INOTIFY_INSTANCES."
fi

# Check directories & permissions
if [ -d "$CSI_MNT_DIR" ]; then
    permissions=$(stat -c "%a" "$CSI_MNT_DIR")
    if [ "$permissions" -eq $CSI_MNT_DIR_PERMISSION ]; then
        echo "Directory $CSI_MNT_DIR has the correct permissions $CSI_MNT_DIR_PERMISSION."
    else
        print_err "Directory $CSI_MNT_DIR does not have the correct permissions. Current permissions: $permissions should be 777."
    fi
else
    print_err "Directory $CSI_MNT_DIR does not exist."
fi

# Return code
if ! $all_requirements_met; then
    exit 1
fi
