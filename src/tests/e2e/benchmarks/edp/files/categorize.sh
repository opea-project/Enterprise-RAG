#!/bin/bash

# List of prefixes and corresponding destination directories
prefixes=(
  "SS_simple_small" "SM_simple_medium" "SL_simple_large" "SXL_simple_xlarge"
  "MS_moderate_small" "MM_moderate_medium" "ML_moderate_large" "MXL_moderate_xlarge"

)

dest_dirs=(
  "simple_small" "simple_medium" "simple_large" "simple_xlarge"
  "moderate_small" "moderate_medium" "moderate_large" "moderate_xlarge"
)

# Iterate over files in the current directory
for file in *; do
    # Skip if not a regular file
    [ -f "$file" ] || continue

    for i in "${!prefixes[@]}"; do
        prefix="${prefixes[$i]}"
        dest="${dest_dirs[$i]}"
        if [[ "$file" == "$prefix"* ]]; then
            # Create destination directory if it doesn't exist
            mkdir -p "$dest"
            # Move the file
            mv "$file" "$dest/"
            break
        fi
    done
done