#!/bin/bash

# Simple script to create a slim release tag by keeping only deployment/terraform directory
# and the single file ibm_catalog.json
# Excludes everything except these to keep the release minimal

set -e

# Configuration
KEEP_DIR="deployment/terraform"
KEEP_FILE="ibm_catalog.json"
SLIM_SUFFIX="-slim"

# Usage
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <tag-name>"
    echo "Creates a slim version of the tag keeping only ${KEEP_DIR} and ${KEEP_FILE}"
    echo ""
    echo "Example: $0 release-1.5.0"
    echo "Creates: release-1.5.0-slim"
    exit 1
fi

TAG_NAME="$1"
SLIM_TAG_NAME="${TAG_NAME}${SLIM_SUFFIX}"

# Check if we're in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Change to git repository root directory
GIT_ROOT=$(git rev-parse --show-toplevel)
echo "Changing to git repository root: $GIT_ROOT"
cd "$GIT_ROOT" || {
    echo "Error: Failed to change to git repository root"
    exit 1
}

# Check if original tag exists
if ! git rev-parse --verify "refs/tags/$TAG_NAME" >/dev/null 2>&1; then
    echo "Error: Tag '$TAG_NAME' does not exist"
    exit 1
fi

# Check if slim tag already exists
if git rev-parse --verify "refs/tags/$SLIM_TAG_NAME" >/dev/null 2>&1; then
    echo "Error: Slim tag '$SLIM_TAG_NAME' already exists"
    echo "Delete it first with: git tag -d $SLIM_TAG_NAME"
    exit 1
fi

# --- LFS safety: make sure the tag has its LFS content available locally ---
if command -v git-lfs >/dev/null 2>&1; then
    git lfs install --local >/dev/null 2>&1 || true
    git lfs fetch --include="*" --exclude="" origin "$TAG_NAME" >/dev/null 2>&1 || true
fi
# --------------------------------------------------------------------------

echo "Creating slim tag '$SLIM_TAG_NAME' from '$TAG_NAME'..."
echo "Keeping only directory: $KEEP_DIR and file: $KEEP_FILE"

TEMP_BRANCH="temp-slim-$$"
git checkout -b "$TEMP_BRANCH" "$TAG_NAME"

# If LFS is available, materialize files in the working tree (keeps pointers consistent)
# (LFS checkout removed to avoid local changes error)
# if command -v git-lfs >/dev/null 2>&1; then
#     git lfs checkout >/dev/null 2>&1 || true
# fi

echo ""
echo "Debug: Analyzing top-level directory structure in $TAG_NAME..."
git ls-tree -r --name-only "$TAG_NAME" | cut -d'/' -f1 | sort -u | while read -r dir; do
    file_count=$(git ls-tree -r --name-only "$TAG_NAME" | grep "^$dir/" | wc -l)
    echo "Directory: $dir/ ($file_count files)"
done
echo ""

echo "Finding files to remove (everything except $KEEP_DIR and $KEEP_FILE)..."
REMOVED_FILES="/tmp/removed_files_$$"

git ls-tree -r --name-only "$TAG_NAME" | while read -r file; do
    if [[ "$file" == "$KEEP_FILE" || "$file" =~ ^${KEEP_DIR}/ ]]; then
        continue
    fi
    echo "$file" >> "$REMOVED_FILES"
    echo "Will remove: $file"
done

# Count how many files will be removed
if [[ -f "$REMOVED_FILES" ]]; then
    REMOVED_COUNT=$(wc -l < "$REMOVED_FILES")
    echo "Found $REMOVED_COUNT files to remove (keeping only $KEEP_DIR and $KEEP_FILE)"
    while read -r file; do
        if [[ -f "$file" ]]; then
            git rm "$file" 2>/dev/null || true
        fi
    done < "$REMOVED_FILES"

    # Remove empty directories
    find . -type d -empty -not -path "./.git*" -delete 2>/dev/null || true
else
    REMOVED_COUNT=0
    echo "No files to remove (only $KEEP_DIR and $KEEP_FILE found)"
fi

rm -f "$REMOVED_FILES"
echo "Processed files, removed: $REMOVED_COUNT"

# Commit changes if any files were removed
if ! git diff --cached --quiet; then
    git commit -m "Create slim release - keep only ${KEEP_DIR} and ${KEEP_FILE}

Original tag: $TAG_NAME
Only ${KEEP_DIR} directory and file ${KEEP_FILE} are included in this slim release.
For complete sources, use the original tag: $TAG_NAME"
    echo "Removed all files except those in $KEEP_DIR and $KEEP_FILE"
else
    echo "No files to remove (only $KEEP_DIR and $KEEP_FILE found)"
fi

# --- LFS cleanup: prune unreferenced LFS objects (optional but recommended) ---
# (LFS prune removed to avoid local changes error)
# if command -v git-lfs >/dev/null 2>&1; then
#     git lfs prune || true
# fi
# ------------------------------------------------------------------------------

# Create the slim tag
git tag -a "$SLIM_TAG_NAME" -m "Slim release based on $TAG_NAME

Contains only ${KEEP_DIR} directory and ${KEEP_FILE} for deployment purposes.
Original tag: $TAG_NAME"

# Clean up
git checkout -
git branch -D "$TEMP_BRANCH"

echo ""
echo "✓ Created slim tag: $SLIM_TAG_NAME"
echo "✓ Push with: git push origin $SLIM_TAG_NAME"

# Show size comparison
echo ""
echo "Size comparison:"

# Ensure we're in git root for archive operations
cd "$GIT_ROOT" || {
    echo "Warning: Failed to change to git root for size comparison"
}

original_size=$(git archive --format=tar "$TAG_NAME" | wc -c)
slim_size=$(git archive --format=tar "$SLIM_TAG_NAME" | wc -c)
original_kb=$((original_size / 1024))
slim_kb=$((slim_size / 1024))

echo "Original ($TAG_NAME): ${original_kb}KB"
echo "Slim ($SLIM_TAG_NAME): ${slim_kb}KB"

if (( slim_size < original_size )); then
    saved=$((original_size - slim_size))
    saved_kb=$((saved / 1024))
    echo "Saved: ${saved_kb}KB"
fi

# Show what's included in the slim release
echo ""
echo "Files included in slim release ($SLIM_TAG_NAME):"
git ls-tree -r --name-only "$SLIM_TAG_NAME" | while read -r file; do
    file_size=$(git cat-file -s "$SLIM_TAG_NAME:$file" 2>/dev/null || echo 0)
    size_kb=$((file_size / 1024))
    if (( size_kb > 0 )); then
        printf "%4dKB  %s\n" "$size_kb" "$file"
    else
        printf "%4dB   %s\n" "$file_size" "$file"
    fi
done | sort -nr

echo ""
echo "Slim release contains only the $KEEP_DIR directory and file $KEEP_FILE."
