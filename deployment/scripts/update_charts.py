#!/usr/bin/env python3
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Component Version Updater

Updates appVersion and optionally chart version for ERAG application components.
Also supports updating pyproject.toml versions and regenerating uv.lock files.
"""

import argparse
import hashlib
import re
import subprocess  # nosec B404: subprocess is used with controlled input without relaying user input to shell
import sys
import tomllib
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

VERSION_FILE = "version.yaml"
APP_VERSION_KEY = "solution_version"
PYPROJECT_NAME_PREFIX = "Intel-Enterprise-RAG-"
UV_LOCK_MAX_ITERATIONS = 10
UV_LOCK_INFINITE_LOOP_THRESHOLD = 3


class UnsupportedLocation:
    """Marker class for unsupported working directory locations."""
    def __str__(self):
        return "<UNSUPPORTED_LOCATION>"
    def __repr__(self):
        return "UnsupportedLocation()"


UNSUPPORTED_LOCATION = UnsupportedLocation()


def detect_project_root() -> Path | UnsupportedLocation:
    """
    Detect the project root directory based on current working directory.

    Returns:
        Path to project root if detectable, UNSUPPORTED_LOCATION otherwise.

    Detection logic:
        - If cwd is deployment/: project root is parent
        - If cwd has deployment/ and src/ subdirs: project root is cwd
        - If cwd is src/ (parent has deployment/ and src/): project root is parent
        - Otherwise: UNSUPPORTED_LOCATION
    """
    cwd = Path.cwd()

    if cwd.name == "deployment" and (cwd.parent / "src").exists():
        return cwd.parent

    if (cwd / "deployment").exists() and (cwd / "src").exists():
        return cwd

    if cwd.name == "src" and (cwd.parent / "deployment").exists():
        return cwd.parent

    return UNSUPPORTED_LOCATION


def grep_pattern(pattern: str, root_dir: str ="deployment/components", file_mask: str ="Chart.yaml") -> list[str]:
    try:
        # inputs safety under control of caller
        result = subprocess.run(
            ['grep', '-r', root_dir, '--include', file_mask, '-le', pattern],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:  # No matches found
            return []
        print(f"ERROR: grep command failed with exit code {e.returncode}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: grep command not found", file=sys.stderr)
        sys.exit(1)


@cache
def default_app_version() -> str|None:
    project_root = detect_project_root()
    if isinstance(project_root, UnsupportedLocation):
        return None

    version_path = project_root / 'deployment' / VERSION_FILE
    if version_path.exists():
        with version_path.open('r', encoding='utf-8') as f:
            version_data = yaml.safe_load(f)
            if isinstance(version_data, dict):
                return version_data.get(APP_VERSION_KEY, None)
            return None
    return None


@cache
def load_chart(chart_path: Path) -> Tuple[str, Dict[str, Any]]:
    with open(chart_path, 'r', encoding='utf-8') as f:
        contents = f.read()
        return contents, yaml.safe_load(contents)


def save_chart(chart_path: Path, contents: str, chart_data: Dict[str, Any]) -> None:
    updated_contents = contents
    for key, value in [(k,v) for (k,v) in chart_data.items() if k in ["appVersion", "version"]]:
        item_ptrn = rf'^({key}\s*:\s*)([\"\']?)(?:[^\"\'\n\r]+)([\"\']?\s*)$'
        updated_contents = re.sub(item_ptrn, rf'\g<1>\g<2>{value}\g<3>', updated_contents, flags=re.MULTILINE)
    with open(chart_path, 'w', encoding='utf-8') as f:
        f.write(updated_contents)

def increment_version(version: str) -> str:
    """Increment patch version (e.g., 1.0.0 -> 1.0.1)."""
    parts = version.split('.')
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
        return '.'.join(parts)
    return version


def helm_dependency_update(
    chart_path: Path, dry_run: bool, skip_refresh: bool
) -> Tuple[bool, str, str]:
    """Run helm dependency update for a chart. Returns (success, message, stderr)."""
    chart_dir = chart_path.parent

    if dry_run:
        return True, "Skipped (dry-run)", ""

    try:
        # no user input allowed here
        subprocess.run(
            (
                ["helm", "dependency", "update", str(chart_dir)]
                + (["--skip-refresh"] if skip_refresh else [])
            ),
            capture_output=True,
            text=True,
            check=True,
        )
        return True, "Success", ""
    except subprocess.CalledProcessError as e:
        return False, f"Failed: {e.stderr.strip()}", e.stderr
    except FileNotFoundError:
        return False, "helm command not found", ""


def value_list(arg: str) -> list[str]:
    return [n.strip() for n in arg.split(",") if n.strip()]


def match_patterns(value: str, patterns: List[str], case_sensitive: bool = False) -> bool:
    """
    Check if value matches any of the wildcard patterns.
    Supports ** for recursive matching with implicit prefix/suffix.
    Pattern 'comps/**/mosec' matches 'comps/a/b/mosec/c/d'.
    """
    if not patterns:
        return False

    value_to_match = value if case_sensitive else value.lower()

    for pattern in patterns:
        pattern_to_match = pattern if case_sensitive else pattern.lower()

        regex_pattern = pattern_to_match
        regex_pattern = regex_pattern.replace('\\', '/')
        regex_pattern = re.escape(regex_pattern)
        regex_pattern = regex_pattern.replace(r'\*\*', '.*')
        regex_pattern = regex_pattern.replace(r'\*', '[^/]*')
        regex_pattern = regex_pattern.replace(r'\?', '.')

        if not regex_pattern.startswith('.*'):
            regex_pattern = '(?:^|.*/)' + regex_pattern
        if not regex_pattern.endswith('.*'):
            regex_pattern = regex_pattern + '(?:/.*|$)'

        if re.search(regex_pattern, value_to_match):
            return True

    return False


def find_files_by_pattern(root_dir: Path, filename: str, dir_patterns: List[str] = None) -> List[Path]:
    """Find files matching filename, optionally filtered by directory patterns."""
    if not root_dir.exists():
        return []

    all_files = list(root_dir.rglob(filename))

    if not dir_patterns:
        return all_files

    filtered_files = []
    for file_path in all_files:
        rel_path = file_path.relative_to(root_dir)
        rel_dir = str(rel_path.parent)

        if match_patterns(rel_dir, dir_patterns, case_sensitive=False):
            filtered_files.append(file_path)

    return filtered_files


def compute_file_hash(file_path: Path) -> Optional[str]:
    """Compute SHA256 hash of a file. Returns None if file doesn't exist."""
    if not file_path.exists():
        return None

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_pyproject(pyproject_path: Path) -> Tuple[str, Dict[str, Any]]:
    """Load pyproject.toml file and parse it."""
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        contents = f.read()

    data = tomllib.loads(contents)
    return contents, data


def get_local_packages_from_lock(lock_path: Path) -> List[str]:
    """Extract local Intel-Enterprise-RAG package names from uv.lock file."""
    if not lock_path.exists():
        return []

    packages = []
    name_pattern = re.compile(r'^name\s*=\s*"(intel-enterprise-rag[^"]+)"', re.IGNORECASE)

    with open(lock_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = name_pattern.match(line.strip())
            if match:
                packages.append(match.group(1))

    return packages


def save_pyproject(pyproject_path: Path, contents: str, version: str) -> None:
    """Update version in pyproject.toml file contents."""
    version_pattern = r'^(version\s*=\s*)([\"\'])([^\"\'\n\r]+)([\"\'])(\s*)$'
    updated_contents = re.sub(
        version_pattern,
        rf'\g<1>\g<2>{version}\g<4>\g<5>',
        contents,
        flags=re.MULTILINE,
        count=1
    )
    with open(pyproject_path, 'w', encoding='utf-8') as f:
        f.write(updated_contents)


def update_pyproject_version(
    pyproject_path: Path,
    pyproject_rel_path: str,
    app_version: str,
    dry_run: bool
) -> Dict[str, Any]:
    """Update version in pyproject.toml file."""
    print(f"\nProcessing: {pyproject_rel_path}")

    contents, pyproject_data = load_pyproject(pyproject_path)

    project_info = pyproject_data.get('project', {})
    project_name = project_info.get('name', 'N/A')
    old_version = project_info.get('version', 'N/A')

    if not dry_run:
        save_pyproject(pyproject_path, contents, app_version)

    status = "Would update" if dry_run else "Updated"
    print(f"  {status} pyproject.toml:")
    print(f"    Project: {project_name}")
    print(f"    Version: {old_version} -> {app_version}")

    return {
        'path': str(pyproject_path),
        'rel_path': pyproject_rel_path,
        'project_name': project_name,
        'old_version': old_version,
        'new_version': app_version,
    }


def run_uv_lock_upgrade(
    pyproject_dir: Path,
    dry_run: bool,
    use_uv_cache: bool = False,
    uv_path: str = "uv",
    full_upgrade: bool = False,
    local_packages: List[str] = None
) -> Tuple[bool, str]:
    """Run uv lock upgrade for a project directory.

    If full_upgrade is True, runs 'uv lock --upgrade' to upgrade all packages.
    Otherwise, runs 'uv lock --upgrade-package <pkg>' for each local package.
    """
    if dry_run:
        return True, "Skipped (dry-run)"

    cache_args = [] if use_uv_cache else ["--no-cache"]

    if full_upgrade:
        cmd = [uv_path, "lock", "--upgrade"] + cache_args
    else:
        if not local_packages:
            cmd = [uv_path, "lock"] + cache_args
        else:
            upgrade_args = []
            for pkg in local_packages:
                upgrade_args.extend(["--upgrade-package", pkg])
            cmd = [uv_path, "lock"] + upgrade_args + cache_args

    try:
        subprocess.run(
            cmd,
            cwd=str(pyproject_dir),
            capture_output=True,
            text=True,
            check=True,
        )
        return True, "Success"
    except subprocess.CalledProcessError as e:
        return False, f"Failed: {e.stderr.strip()}"
    except FileNotFoundError:
        return False, "uv command not found"


def update_uv_locks(
    pyproject_paths: List[Path],
    source_dir: Path,
    dry_run: bool,
    dep_update: bool,
    use_uv_cache: bool,
    uv_path: str = "uv",
    full_upgrade: bool = False
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Phase 2: Regenerate uv.lock files and iterate until stable.

    If full_upgrade is False (default), only upgrades local Intel-Enterprise-RAG packages.
    If full_upgrade is True, performs full dependency upgrade.
    Returns (results, errors).
    """
    print("\n" + "=" * 60)
    print("PHASE 2: Regenerating uv.lock files")
    print("=" * 60)

    if full_upgrade:
        print("Mode: Full upgrade (all dependencies)")
    else:
        print("Mode: Local packages only")

    if not dep_update:
        print("\nSkipped (not requested)")
        return [], []

    if dry_run:
        print("\nSkipped (dry-run)")
        return [], []

    project_locks = {}
    for pyproject_path in pyproject_paths:
        pyproject_dir = pyproject_path.parent
        lock_path = pyproject_dir / "uv.lock"
        project_locks[str(pyproject_dir)] = {
            'lock_path': lock_path,
            'hash': compute_file_hash(lock_path)
        }

    iteration = 0
    changed_count_history = []
    errors = []
    results = []

    while iteration < UV_LOCK_MAX_ITERATIONS:
        iteration += 1
        print(f"\nIteration {iteration}:")

        for project_dir in project_locks.keys():
            pyproject_dir = Path(project_dir)
            rel_path = pyproject_dir.relative_to(source_dir)
            lock_path = project_locks[project_dir]['lock_path']

            local_packages = [] if full_upgrade else get_local_packages_from_lock(lock_path)

            print(f"  Upgrading: {rel_path}")
            if not full_upgrade and local_packages:
                print(f"    Local packages: {', '.join(local_packages)}")

            success, msg = run_uv_lock_upgrade(
                pyproject_dir, dry_run, use_uv_cache, uv_path,
                full_upgrade=full_upgrade,
                local_packages=local_packages
            )

            if not success:
                error_msg = f"UV lock upgrade failed for {rel_path}: {msg}"
                errors.append(error_msg)
                print(f"    ERROR: {msg}")
            else:
                print(f"    {msg}")

        new_hashes = {
            proj: compute_file_hash(info['lock_path'])
            for proj, info in project_locks.items()
        }

        changed_after = []
        for proj, new_hash in new_hashes.items():
            if new_hash != project_locks[proj]['hash']:
                changed_after.append(proj)

        changed_count = len(changed_after)
        changed_count_history.append(changed_count)

        print(f"  Projects with changed locks: {changed_count}")
        if changed_count > 0:
            for proj in changed_after:
                print(f"    - {Path(proj).relative_to(source_dir)}")

        for proj in changed_after:
            project_locks[proj]['hash'] = new_hashes[proj]

        if changed_count == 0:
            print(f"\nStable state reached after {iteration} iteration(s)")
            break

        if len(changed_count_history) >= UV_LOCK_INFINITE_LOOP_THRESHOLD:
            recent_counts = changed_count_history[-UV_LOCK_INFINITE_LOOP_THRESHOLD:]
            if len(set(recent_counts)) == 1 and recent_counts[0] == changed_count:
                error_msg = f"Infinite loop detected: {changed_count} projects changed in last {UV_LOCK_INFINITE_LOOP_THRESHOLD} iterations"
                errors.append(error_msg)
                print(f"\nERROR: {error_msg}", file=sys.stderr)
                break

    if iteration >= UV_LOCK_MAX_ITERATIONS:
        error_msg = f"Maximum iterations ({UV_LOCK_MAX_ITERATIONS}) reached without stabilization"
        errors.append(error_msg)
        print(f"\nERROR: {error_msg}", file=sys.stderr)

    for project_dir in project_locks.keys():
        results.append({
            'project_dir': project_dir,
            'lock_path': str(project_locks[project_dir]['lock_path']),
            'final_hash': project_locks[project_dir]['hash']
        })

    return results, errors


def update_chart_versions(
    chart_path: Path,
    chart_rel_path: str,
    app_version: str,
    increment_chart_version: bool,
    dry_run: bool
) -> Dict[str, Any]:
    """Phase 1: Update appVersion and chart version in Chart.yaml"""
    print(f"\nProcessing: {chart_rel_path}")

    chart_contents, chart_data = load_chart(chart_path)

    old_app_version = chart_data.get('appVersion', 'N/A')
    old_chart_version = chart_data.get('version', 'N/A')

    chart_data['appVersion'] = app_version

    new_chart_version = old_chart_version
    if increment_chart_version and 'version' in chart_data:
        new_chart_version = increment_version(chart_data['version'])
        chart_data['version'] = new_chart_version

    if not dry_run:
        save_chart(chart_path, chart_contents, chart_data)

    status = "Would update" if dry_run else "Updated"
    print(f"  {status} Chart.yaml:")
    print(f"    Chart version: {old_chart_version} -> {new_chart_version}")
    print(f"    App version: {old_app_version} -> {app_version}")

    return {
        'path': str(chart_path),
        'rel_path': chart_rel_path,
        'old_app_version': old_app_version,
        'new_app_version': app_version,
        'old_chart_version': old_chart_version,
        'new_chart_version': new_chart_version,
        'chart_version_changed': increment_chart_version and old_chart_version != new_chart_version,
        'has_dependencies': bool(chart_data.get('dependencies'))
    }


def update_chart_dependencies(
    chart_path: Path,
    chart_rel_path: str,
    dry_run: bool,
    skip_refresh: bool
) -> Tuple[bool, str]:
    """Phase 2: Update dependencies after all chart versions are incremented"""
    print(f"\nUpdating dependencies: {chart_rel_path}")

    success, msg, stderr = helm_dependency_update(chart_path, dry_run, skip_refresh)
    if not success:
        print(f"\nERROR: Helm dependency update failed for {chart_path}", file=sys.stderr)
        print(f"Message: {msg}", file=sys.stderr)
        if stderr:
            print(f"Output:\n{stderr}", file=sys.stderr)
        return False, msg

    print(f"  Dependency update: {msg}")
    return True, msg


def main():
    project_root = detect_project_root()

    if isinstance(project_root, UnsupportedLocation):
        default_chart_root = UNSUPPORTED_LOCATION
        default_source_root = UNSUPPORTED_LOCATION
    else:
        default_chart_root = project_root / 'deployment' / 'components'
        default_source_root = project_root / 'src'

    parser = argparse.ArgumentParser(
        description='Update appVersion and chart version for ERAG components, and/or update pyproject.toml versions and uv.lock files. ' \
        'Tool is supposed to be run from project root, deployment/ or src/ directories.'
    )

    parser.add_argument(
        'mode',
        nargs='?',
        choices=['chart', 'pyproject', 'all'],
        default='all',
        help='Operation mode: chart (helm charts only), pyproject (Python projects only), or all (both). Default: all'
    )

    if (default_version := default_app_version()) is not None:
        parser.add_argument(
            '--app-version',
            required=False,
            default=default_version,
            help=f'New appVersion/version to set for all components, default: {default_version}'
        )
    else:
        parser.add_argument(
            '--app-version',
            required=True,
            help='New appVersion/version to set for all components, no default available'
        )

    parser.add_argument(
        '--increment-chart-version', '--inc',
        action='store_true',
        default=True,
        help='Increment chart version (default: true)'
    )
    parser.add_argument(
        '--no-increment-chart-version', '--no-inc',
        dest='increment_chart_version',
        action='store_false',
        help='Do not increment chart version'
    )
    parser.add_argument(
        '--dep-update',
        action='store_true',
        default=True,
        help='Run dependency updates: helm dependency update for charts and uv lock --upgrade for pyprojects (default: true)'
    )
    parser.add_argument(
        '--no-dep-update',
        dest='dep_update',
        action='store_false',
        help='Do not run dependency updates (helm or uv lock)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )

    parser.add_argument(
        '--chart-root',
        type=Path,
        default=default_chart_root,
        help='Root directory of the charts in repository (default: deployment/components relative to repo root)'
    )
    parser.add_argument(
        '--chart-dir',
        type=Path,
        dest='chart_root',
        help='DEPRECATED: Use --chart-root instead'
    )
    parser.add_argument(
        '--source-root',
        type=Path,
        default=default_source_root,
        help='Root directory for searching pyproject.toml files (default: src relative to repo root)'
    )

    parser.add_argument(
        "--dirs",
        nargs="?",
        type=value_list,
        default=[],
        help="Optional list of directory patterns (supports **) to filter both charts and pyprojects when mode is 'all'"
    )
    parser.add_argument(
        "--chart-dirs",
        nargs="?",
        type=value_list,
        default=[],
        help="Optional list of directory patterns (supports **) to filter charts by their directory paths"
    )
    parser.add_argument(
        "--py-dirs",
        nargs="?",
        type=value_list,
        default=[],
        help="Optional list of directory patterns (supports **) to filter pyprojects by their directory paths"
    )

    parser.add_argument(
        "--charts",
        nargs="?",
        type=value_list,
        default=[],
        help="Optional list of chart names (top-level name in Chart.yaml) to update"
    )
    parser.add_argument(
        "--projs",
        nargs="?",
        type=value_list,
        default=[],
        help="Optional list of project name patterns (supports wildcards) to filter pyprojects"
    )

    parser.add_argument(
        '--skip-refresh',
        action='store_true',
        help='Skip refreshing helm repositories (helm option: --skip-refresh)'
    )

    parser.add_argument(
        '--use-uv-cache',
        action='store_true',
        help='Do not bypass uv cache (may be faster) for upgrading uv lock files (run without --no-cache)'
    )

    parser.add_argument(
        '--full-upgrade',
        action='store_true',
        help='Perform full uv lock upgrade of all dependencies (default: only upgrade local project references)'
    )

    parser.add_argument(
        '--uv-path',
        type=str,
        default='uv',
        help='Path to uv binary (default: uv)'
    )

    args = parser.parse_args()

    if '--chart-dir' in sys.argv:
        print("WARNING: --chart-dir is deprecated, use --chart-root instead", file=sys.stderr)

    mode_chart = args.mode in ['chart', 'all']
    mode_pyproject = args.mode in ['pyproject', 'all']

    if mode_chart and isinstance(args.chart_root, UnsupportedLocation):
        print("ERROR: Unable to detect project root from current working directory.", file=sys.stderr)
        print("Please run this script from one of the following locations:", file=sys.stderr)
        print("  - Project root (directory containing deployment/ and src/)", file=sys.stderr)
        print("  - deployment/ directory", file=sys.stderr)
        print("  - src/ directory", file=sys.stderr)
        print("Or specify --chart-root explicitly.", file=sys.stderr)
        sys.exit(1)

    if mode_pyproject and isinstance(args.source_root, UnsupportedLocation):
        print("ERROR: Unable to detect project root from current working directory.", file=sys.stderr)
        print("Please run this script from one of the following locations:", file=sys.stderr)
        print("  - Project root (directory containing deployment/ and src/)", file=sys.stderr)
        print("  - deployment/ directory", file=sys.stderr)
        print("  - src/ directory", file=sys.stderr)
        print("Or specify --source-root explicitly.", file=sys.stderr)
        sys.exit(1)

    chart_dir = args.chart_root if isinstance(args.chart_root, UnsupportedLocation) else args.chart_root.resolve()
    source_dir = args.source_root if isinstance(args.source_root, UnsupportedLocation) else args.source_root.resolve()

    if mode_chart and not chart_dir.exists():
        print(f"Error: Chart directory does not exist: {chart_dir}", file=sys.stderr)
        sys.exit(1)

    if mode_pyproject and not source_dir.exists():
        print(f"Error: Source directory does not exist: {source_dir}", file=sys.stderr)
        sys.exit(1)

    # Report uv version when processing Python projects
    if mode_pyproject:
        try:
            result = subprocess.run(
                [args.uv_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            uv_version = result.stdout.strip()
            print(f"Using uv: {uv_version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: Could not determine uv version", file=sys.stderr)

    print("Component Version Updater")
    print(f"{'=' * 60}")
    print(f"Mode: {args.mode}")
    print(f"App Version: {args.app_version}")
    if mode_chart:
        print(f"Increment Chart Version: {args.increment_chart_version}")
        print(f"Chart Directory: {chart_dir}")
    if mode_pyproject:
        print(f"Source Directory: {source_dir}")
    print(f"Dependency Update: {args.dep_update}")
    print(f"Dry Run: {args.dry_run}")
    print(f"{'=' * 60}\n")

    all_results = {}
    all_errors = []

    if mode_chart:
        chart_results, chart_errors = process_charts(
            args, chart_dir
        )
        all_results['charts'] = chart_results
        all_errors.extend(chart_errors)

    if mode_pyproject:
        pyproject_results, pyproject_errors = process_pyprojects(
            args, source_dir
        )
        all_results['pyprojects'] = pyproject_results
        all_errors.extend(pyproject_errors)

    print(f"\n{'=' * 60}")
    print("Summary:")
    if mode_chart and 'charts' in all_results:
        print(f"  Charts {'would be ' if args.dry_run else ''}updated: {len(all_results['charts'])}")
    if mode_pyproject and 'pyprojects' in all_results:
        print(f"  Pyprojects {'would be ' if args.dry_run else ''}updated: {len(all_results['pyprojects'])}")

    if all_errors:
        print(f"\nErrors: {len(all_errors)}")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)

    if args.dry_run:
        print("\nThis was a dry run. Use without --dry-run to apply changes.")

    sys.exit(0)


def process_charts(args, chart_dir: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Process helm charts: update versions and dependencies."""
    results = []
    errors = []

    chart_dir_patterns = list(args.chart_dirs or [])
    if args.dirs:
        chart_dir_patterns.extend(args.dirs)

    all_chart_files = grep_pattern(r'app.kubernetes.io/part-of:\s*ERAG', str(chart_dir), 'Chart.yaml')
    chart_files = []

    if chart_dir_patterns or args.charts:
        if chart_dir_patterns:
            for chart_file in all_chart_files:
                chart_path = Path(chart_file)
                try:
                    rel_path = chart_path.relative_to(chart_dir)
                    rel_dir = str(rel_path.parent)
                    if match_patterns(rel_dir, chart_dir_patterns):
                        chart_files.append(chart_file)
                except ValueError:
                    continue

        if args.charts:
            for chart_file in all_chart_files:
                _, chart_data = load_chart(Path(chart_file))
                if chart_data.get("name", "") in args.charts:
                    chart_files.append(chart_file)

        chart_files = sorted(set(chart_files))
    else:
        chart_files = sorted(all_chart_files[:])

    print("\n" + "=" * 60)
    print("PHASE 1: Updating chart versions")
    print("=" * 60)

    for chart_rel_path in chart_files:
        chart_path = chart_dir / chart_rel_path

        if not chart_path.exists():
            error_msg = f"Chart not found: {chart_path}"
            errors.append(error_msg)
            print(f"WARNING: {error_msg}")
            continue

        try:
            result = update_chart_versions(
                chart_path,
                chart_rel_path,
                args.app_version,
                args.increment_chart_version,
                args.dry_run
            )
            results.append(result)

        except Exception as e:
            error_msg = f"Error updating {chart_rel_path}: {e}"
            errors.append(error_msg)
            print(f"ERROR: {error_msg}", file=sys.stderr)

    if args.dep_update:
        print("\n" + "=" * 60)
        print("PHASE 2: Updating chart dependencies")
        print("=" * 60)

        charts_with_deps = [r for r in results if r['has_dependencies']]

        if charts_with_deps:
            for result in charts_with_deps:
                chart_path = Path(result['path'])
                chart_rel_path = result['rel_path']

                try:
                    success, msg = update_chart_dependencies(
                        chart_path,
                        chart_rel_path,
                        args.dry_run,
                        args.skip_refresh
                    )
                    result['dep_update_success'] = success
                    result['dep_update_msg'] = msg

                    if not success:
                        errors.append(f"Dependency update failed for {chart_rel_path}: {msg}")

                except Exception as e:
                    error_msg = f"Error updating dependencies for {chart_rel_path}: {e}"
                    errors.append(error_msg)
                    print(f"ERROR: {error_msg}", file=sys.stderr)
                    result['dep_update_success'] = False
                    result['dep_update_msg'] = str(e)
        else:
            print("\nNo charts with dependencies found.")
    else:
        for result in results:
            result['dep_update_success'] = True
            result['dep_update_msg'] = "Skipped (not requested)"

    return results, errors


def process_pyprojects(args, source_dir: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Process Python projects: update pyproject.toml versions and regenerate uv.lock files."""
    results = []
    errors = []

    py_dir_patterns = list(args.py_dirs or [])
    if args.dirs:
        py_dir_patterns.extend(args.dirs)

    all_pyproject_files = find_files_by_pattern(source_dir, "pyproject.toml", py_dir_patterns)

    pyproject_files = []
    for pyproject_path in all_pyproject_files:
        try:
            _, pyproject_data = load_pyproject(pyproject_path)
            project_name = pyproject_data.get('project', {}).get('name', '')

            name_variations = [
                project_name,
                project_name.replace('_', '-'),
                project_name.replace('-', '_')
            ]

            matches_prefix = any(
                name.lower().startswith(PYPROJECT_NAME_PREFIX.lower())
                for name in name_variations
            )

            if not matches_prefix:
                continue

            if args.projs:
                if match_patterns(project_name, args.projs, case_sensitive=False):
                    pyproject_files.append(pyproject_path)
            else:
                pyproject_files.append(pyproject_path)

        except Exception as e:
            print(f"Warning: Could not parse {pyproject_path}: {e}")
            continue

    pyproject_files = sorted(set(pyproject_files))

    print("\n" + "=" * 60)
    print("PHASE 1: Updating pyproject.toml versions")
    print("=" * 60)

    print(f"\nFound {len(pyproject_files)} matching pyproject.toml files")

    for pyproject_path in pyproject_files:
        try:
            rel_path = pyproject_path.relative_to(source_dir)
        except ValueError:
            rel_path = pyproject_path

        try:
            result = update_pyproject_version(
                pyproject_path,
                str(rel_path),
                args.app_version,
                args.dry_run
            )
            results.append(result)
        except Exception as e:
            error_msg = f"Error updating {rel_path}: {e}"
            errors.append(error_msg)
            print(f"ERROR: {error_msg}", file=sys.stderr)

    if pyproject_files:
        _, lock_errors = update_uv_locks(
            pyproject_files, source_dir, args.dry_run, args.dep_update,
            args.use_uv_cache, args.uv_path, args.full_upgrade
        )
        errors.extend(lock_errors)

    return results, errors


if __name__ == '__main__':
    main()
