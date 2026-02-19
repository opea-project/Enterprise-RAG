#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import sys
import yaml
import pytest
import os
from pathlib import Path
from typing import Optional, List

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s [%(module)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_scenarios_config(config_path: Path) -> dict:
    """Loads and parses the YAML file with scenario configuration."""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return config.get("scenarios", {})
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        sys.exit(1)


def run_pytest(test_paths: List[str], extra_args: List[str], markers: Optional[str] = None,
               clean_alluredir: bool = False) -> int:
    """Runs pytest for a given set of paths and returns exit code."""
    if not test_paths:
        logger.debug("No test paths provided, skipping this pytest run.")
        return 0

    pytest_args = [
        "-vv", "-s", "--capture=tee-sys",
        "--alluredir", "allure-results",
    ]

    if clean_alluredir:
        pytest_args.append("--clean-alluredir")

    if markers:
        logger.info(f"Applying pytest markers: '{markers}' for paths: {test_paths}")
        pytest_args.extend(["-m", markers])

    final_args = pytest_args + extra_args + test_paths
    logger.info(f"Running pytest internally with args: {final_args}")

    exit_code = pytest.main(final_args)
    if exit_code not in [0, 5]:
        logger.error(f"Pytest run failed with exit code {exit_code} for paths: {test_paths}")

    return int(exit_code)


def main():
    script_dir = Path(__file__).resolve().parent
    cfg_path = script_dir / "scenarios.yaml"

    scenarios = load_scenarios_config(cfg_path)

    parser = argparse.ArgumentParser(description="Scenario runner (configured via env vars).")
    args, passthrough_args = parser.parse_known_args()

    scenario_name = os.environ.get("SCENARIO")
    cluster_state = os.environ.get("CLUSTER_STATE")

    if not scenario_name:
        logger.error("Environment variable 'SCENARIO' is not set.")
        logger.info(f"Available scenarios in YAML: {list(scenarios.keys())}")
        sys.exit(1)

    if scenario_name not in scenarios:
        logger.error(f"Scenario '{scenario_name}' not found in configuration.")
        logger.info(f"Available scenarios: {list(scenarios.keys())}")
        sys.exit(1)

    scenario_config = scenarios[scenario_name]
    raw_lifecycle = scenario_config.get("lifecycle", [])
    lifecycle_files = []

    # Logic for backup-restore scenario
    if scenario_name == "backup-restore":
        if not cluster_state:
            logger.error(f"Scenario '{scenario_name}' requires 'CLUSTER_STATE' environment variable.")
            if isinstance(raw_lifecycle, dict):
                logger.info(f"Available states for this scenario: {list(raw_lifecycle.keys())}")
            sys.exit(1)

        lifecycle_files = raw_lifecycle.get(cluster_state)

        if lifecycle_files is None:
            logger.error(f"Invalid CLUSTER_STATE='{cluster_state}' for scenario '{scenario_name}'.")
            logger.info(f"Available states: {list(raw_lifecycle.keys())}")
            sys.exit(1)

    # Logic for standard scenarios
    else:
        if cluster_state:
            logger.warning(f"CLUSTER_STATE='{cluster_state}' is set but ignored for scenario '{scenario_name}'.")

        if isinstance(raw_lifecycle, dict):
            logger.error(f"Scenario '{scenario_name}' has dict config but script treats it as list. check YAML.")
            sys.exit(1)

        lifecycle_files = raw_lifecycle

    # Prepare paths
    lifecycle_paths = [f"e2e/lifecycle/{file}" for file in lifecycle_files]

    validation_paths = []
    val_cfg = scenario_config.get("validation", {})
    markers = scenario_config.get("markers")

    if markers and not val_cfg:
        validation_paths.append("e2e/validation")
    elif val_cfg.get("all"):
        validation_paths.append("e2e/validation")
    else:
        for test in val_cfg.get("include", []):
            validation_paths.append(f"e2e/validation/{test}")

    lifecycle_exit_code = run_pytest(lifecycle_paths, passthrough_args, clean_alluredir=True)
    validation_exit_code = run_pytest(validation_paths, passthrough_args, markers=markers, clean_alluredir=False)

    final_exit_code = 0
    if lifecycle_exit_code not in [0, 5]:
        final_exit_code = lifecycle_exit_code
    elif validation_exit_code not in [0, 5]:
        final_exit_code = validation_exit_code

    logger.info(f"Script finished with final exit code: {final_exit_code}")
    sys.exit(final_exit_code)


if __name__ == "__main__":
    main()