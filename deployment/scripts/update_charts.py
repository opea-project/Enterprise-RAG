#!/usr/bin/env python3
# Copyright (C) 2025-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Component Version Updater

Updates appVersion and optionally chart version for ERAG application components.
"""

import argparse
import re
import subprocess  # nosec B404: subprocess is used with controlled input without relaying user input to shell
import sys
from functools import cache
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


VERSION_FILE = "version.yaml"
APP_VERSION_KEY = "solution_version"

script_dir = Path(__file__).parent.resolve()


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
    version_path = script_dir.parent / VERSION_FILE
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
    parser = argparse.ArgumentParser(
        description='Update appVersion and chart version for ERAG components'
    )
    if (default_version := default_app_version()) is not None:
        parser.add_argument(
            '--app-version',
            required=False,
            default=default_version,
            help=f'New appVersion to for all components, default: {default_version}'
        )
    else:
        parser.add_argument(
            '--app-version',
            required=True,
            help='New appVersion to set for all components, no default available'
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
        help='Run helm dependency update for charts with dependencies (default: true)'
    )
    parser.add_argument(
        '--no-dep-update',
        dest='dep_update',
        action='store_false',
        help='Do not run helm dependency update'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without making changes'
    )
    parser.add_argument(
        '--chart-dir',
        type=Path,
        default=Path(__file__).parent.parent.parent/'deployment/components',
        help='Chart directory of the charts in repository (default: ../../deployment/components relative to scripts dir)'
    )
    parser.add_argument("--dirs", nargs="?", type=value_list, default=[], help="Optional list of chart dirs (dirname of Chart.yaml) to update")
    parser.add_argument("--charts", nargs="?", type=value_list, default=[], help="Optional list of chart names (top-level name in Chart.yaml) to update")
    parser.add_argument(
        '--skip-refresh',
        action='store_true',
        help='Skip refreshing helm repositories (helm option: --skip-refresh)'
    )

    args = parser.parse_args()

    chart_dir = args.chart_dir.resolve()

    if not chart_dir.exists():
        print(f"Error: Chart directory does not exist: {chart_dir}", file=sys.stderr)
        sys.exit(1)

    print("Chart updater")
    print(f"{'=' * 60}")
    print(f"App Version: {args.app_version}")
    print(f"Increment Chart Version: {args.increment_chart_version}")
    print(f"Dependency Update: {args.dep_update}")
    print(f"Dry Run: {args.dry_run}")
    print(f"Chart Directory: {chart_dir}")
    print(f"{'=' * 60}\n")

    results = []
    errors = []

    # while calling subprocess under the hood, no user input is passed to the shell
    all_chart_files = grep_pattern(r'app.kubernetes.io/part-of:\s*ERAG', chart_dir, 'Chart.yaml')
    chart_files = []
    if args.dirs or args.charts:
        if args.dirs:
            chart_files.extend([n for n in all_chart_files if Path(n).parent.name in args.dirs])
        if args.charts:
            # scan all chart files for name and add matching ones to the list for update
            for chart_file in all_chart_files:
                _, chart_data = load_chart(chart_file)
                if chart_data.get("name", "") in args.charts:
                    chart_files.append(chart_file)
        chart_files = sorted(set(chart_files))
    else:
        chart_files = sorted(all_chart_files[:])

    # Phase 1: Update all Chart.yaml files (versions)
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

    # Phase 2: Update dependencies (after all versions are incremented)
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

    print(f"\n{'=' * 60}")
    print(f"Summary: {len(results)} charts {'would be ' if args.dry_run else ''}updated")

    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    if args.dry_run:
        print("\nThis was a dry run. Use without --dry-run to apply changes.")

    sys.exit(0)


if __name__ == '__main__':
    main()
