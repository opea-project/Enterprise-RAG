#!/bin/bash

SRC_DIR="../../src"
TARGET_DIR="helm/envs/src"

mkdir -p "$TARGET_DIR"

find "$SRC_DIR" -type f -regex '.*\.env\(\.[^/]*\)?' | while read -r env_file; do
    relative_path="${env_file#$SRC_DIR/}"


    mkdir -p "$TARGET_DIR/$(dirname "$relative_path")"

    # ls $env_file "$TARGET_DIR/$relative_path"
    ln -srf $env_file "$TARGET_DIR/$relative_path"
done
