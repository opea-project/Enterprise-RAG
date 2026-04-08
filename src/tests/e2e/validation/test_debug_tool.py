#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import subprocess # nosec B404
import os
import shutil
import allure
import logging
import glob
import json
from pathlib import Path

from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

DEBUG_TOOL_TIMEOUT_SECONDS = 600  # 10 minutes
DEBUG_BUNDLE_PATTERN = "debug_bundle_*"
DEFAULT_KUBECONFIG = "/root/.kube/config"

# Expected subdirectories in debug_bundle
EXPECTED_SUBDIRS = ["kubectl_logs", "kubectl_get", "kubectl_getyaml", "kubectl_describe"]

# Expected files in debug_bundle root
EXPECTED_FILES = ["config_redacted.yaml", "SUMMARY.json", "debug_tool_execution.log"]


def find_deployment_dir(start_path):
    """Recursively search upward from start_path to find the deployment directory."""
    current = Path(start_path).resolve()
    while current != current.parent:
        deployment_candidate = current / "deployment"
        if deployment_candidate.is_dir():
            logger.info(f"Found deployment directory: {deployment_candidate}")
            return deployment_candidate
        current = current.parent
    raise RuntimeError("Could not find 'deployment' directory in any parent directory")


def get_debug_bundle_dirs(deployment_dir):
    """Get all debug_bundle directories matching the pattern debug_bundle_*."""
    pattern = os.path.join(deployment_dir, DEBUG_BUNDLE_PATTERN)
    all_matches = glob.glob(pattern)
    return [m for m in all_matches if os.path.isdir(m)]


def get_kubeconfig_path():
    """Extract the kubeconfig path from the cfg dictionary."""
    kubeconfig = cfg.get("kubeconfig")
    if not kubeconfig:
        return None
    if not os.path.isabs(kubeconfig):
        kubeconfig = os.path.abspath(kubeconfig)
    return kubeconfig


def verify_debug_bundle_structure(bundle_path):
    """Verify the debug_bundle directory structure and content."""
    logger.info(f"Verifying debug_bundle structure at: {bundle_path}")

    # Check expected subdirectories
    for subdir in EXPECTED_SUBDIRS:
        subdir_path = os.path.join(bundle_path, subdir)
        assert os.path.isdir(subdir_path), f"Expected subdirectory '{subdir}' not found"
        contents = os.listdir(subdir_path)
        assert len(contents) > 0, f"Subdirectory '{subdir}' is empty"
        logger.info(f"  [+] Subdirectory '{subdir}' verified with {len(contents)} items")

    # Check expected files
    for expected_file in EXPECTED_FILES:
        file_path = os.path.join(bundle_path, expected_file)
        assert os.path.isfile(file_path), f"Expected file '{expected_file}' not found"
        file_size = os.path.getsize(file_path)
        assert file_size > 0, f"Expected file '{expected_file}' is empty"
        logger.info(f"  [+] File '{expected_file}' verified ({file_size} bytes)")

    # Verify SUMMARY.json is valid JSON
    summary_path = os.path.join(bundle_path, "SUMMARY.json")
    with open(summary_path, "r") as f:
        summary_data = json.load(f)
    assert "collection_info" in summary_data, "SUMMARY.json missing 'collection_info'"
    assert "namespaces" in summary_data, "SUMMARY.json missing 'namespaces'"
    assert "total_pods" in summary_data, "SUMMARY.json missing 'total_pods'"
    assert "node_count" in summary_data, "SUMMARY.json missing 'node_count'"
    logger.info(f"  [+] SUMMARY.json valid with {len(summary_data.get('namespaces', []))} namespaces")


def handle_kubeconfig(kubeconfig_path):
    """Handle kubeconfig file: copy if needed, return whether it was copied."""
    if not kubeconfig_path:
        return False

    if os.path.exists(kubeconfig_path):
        logger.info(f"kubeconfig already exists at {kubeconfig_path}")
        return False

    if not os.path.exists(DEFAULT_KUBECONFIG):
        logger.warning(f"Default kubeconfig not found at {DEFAULT_KUBECONFIG}, skipping copy")
        return False

    logger.info(f"Copying kubeconfig from {DEFAULT_KUBECONFIG} to {kubeconfig_path}")
    os.makedirs(os.path.dirname(kubeconfig_path), exist_ok=True)
    shutil.copy(DEFAULT_KUBECONFIG, kubeconfig_path)
    return True


def run_debug_tool(deployment_dir, build_config_file):
    """Execute debug_tool.py and verify it completes successfully."""
    os.chdir(deployment_dir)
    logger.info(f"Executing: python3 tools/debug_tool.py --config {build_config_file}")

    result = subprocess.run(
        ["python3", "tools/debug_tool.py", "--config", build_config_file],
        capture_output=True,
        text=True,
        timeout=DEBUG_TOOL_TIMEOUT_SECONDS
    )

    assert result.returncode == 0, (
        f"debug_tool.py failed with exit code {result.returncode}.\n"
        f"Stdout: {result.stdout}\n"
        f"Stderr: {result.stderr}"
    )


def verify_debug_bundle_created(deployment_dir, debug_bundles_before):
    """Verify debug_bundle was created with all required content."""
    debug_bundles_after = get_debug_bundle_dirs(deployment_dir)
    new_bundles = [b for b in debug_bundles_after if b not in debug_bundles_before]
    assert len(new_bundles) > 0, f"No new debug_bundle directory created in {deployment_dir}"

    debug_bundle_path = new_bundles[0]
    logger.info(f"Found new debug_bundle: {debug_bundle_path}")

    # Verify bundle structure
    verify_debug_bundle_structure(debug_bundle_path)

    # Check for topology_preview_report.yaml (warn if missing, don't fail)
    topology_report_path = os.path.join(debug_bundle_path, "topology_preview_report.yaml")
    if os.path.isfile(topology_report_path):
        logger.info(f"  [+] topology_preview_report.yaml found in bundle ({os.path.getsize(topology_report_path)} bytes)")
    else:
        warning_msg = "topology_preview_report.yaml not found in debug bundle - topology preview may not have been generated yet"
        logger.warning(f"  [!] {warning_msg}")

    # Check for ansible.log (warn if missing, don't fail)
    ansible_log_path = os.path.join(debug_bundle_path, "ansible.log")
    if os.path.isfile(ansible_log_path):
        logger.info(f"  [+] ansible.log found in bundle ({os.path.getsize(ansible_log_path)} bytes)")
    else:
        warning_msg = "ansible.log not found in debug bundle - deployment log may not have been generated yet"
        logger.warning(f"  [!] {warning_msg}")

    # Verify tar.gz file exists
    tar_gz_file = f"{debug_bundle_path}.tar.gz"
    assert os.path.isfile(tar_gz_file), f"debug_bundle tar.gz file not found at {tar_gz_file}"
    logger.info(f"debug_bundle tar.gz file verified: {tar_gz_file}")

    return debug_bundle_path


def cleanup_debug_bundle(deployment_dir, debug_bundles_before):
    """Clean up debug_bundle directories and tar.gz files created during test."""
    debug_bundles_final = get_debug_bundle_dirs(deployment_dir)
    for debug_bundle in debug_bundles_final:
        if debug_bundle not in debug_bundles_before:
            shutil.rmtree(debug_bundle)
            logger.info(f"Cleaned up debug_bundle directory: {debug_bundle}")

            tar_gz_file = f"{debug_bundle}.tar.gz"
            if os.path.isfile(tar_gz_file):
                os.remove(tar_gz_file)
                logger.info(f"Cleaned up tar.gz file: {tar_gz_file}")


def cleanup_kubeconfig(kubeconfig_path, was_copied):
    """Clean up kubeconfig file if it was copied during test."""
    if was_copied and kubeconfig_path and os.path.exists(kubeconfig_path):
        os.remove(kubeconfig_path)
        logger.info(f"Cleaned up kubeconfig file: {kubeconfig_path}")


@allure.testcase("IEASG-T522")
def test_debug_tool_execution(request):
    """Test that debug_tool.py runs successfully with the build config file."""
    build_config_file = os.path.abspath(request.config.getoption("--build-config-file"))
    logger.info(f"Build config file: {build_config_file}")

    test_file = Path(__file__).resolve()
    deployment_dir = find_deployment_dir(test_file)
    original_dir = os.getcwd()

    # Record debug_bundles before test
    debug_bundles_before = get_debug_bundle_dirs(deployment_dir)
    logger.info(f"debug_bundles existing before test: {debug_bundles_before}")

    # Get kubeconfig path
    kubeconfig_path = get_kubeconfig_path()
    kubeconfig_was_copied = False

    try:
        # Setup
        kubeconfig_was_copied = handle_kubeconfig(kubeconfig_path)

        # Execute
        run_debug_tool(deployment_dir, build_config_file)

        # Verify
        verify_debug_bundle_created(deployment_dir, debug_bundles_before)

    finally:
        # Cleanup
        cleanup_debug_bundle(deployment_dir, debug_bundles_before)
        cleanup_kubeconfig(kubeconfig_path, kubeconfig_was_copied)
        os.chdir(original_dir)
