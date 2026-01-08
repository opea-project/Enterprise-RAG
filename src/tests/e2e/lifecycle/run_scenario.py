#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import logging
import sys
import yaml
import pytest
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
    """
    Runs pytest for a given set of paths and arguments by calling it internally.
    Returns the pytest exit code.
    """
    if not test_paths:
        logger.debug("No test paths provided, skipping this pytest run.")
        return 0

    pytest_args = [
        "-vv",
        "-s",
        "--capture=tee-sys",
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

    # Pytest exits with 5 if no tests are collected. This is not a failure.
    if exit_code not in [0, 5]:
        logger.error(f"Pytest run failed with exit code {exit_code} for paths: {test_paths}")

    return int(exit_code)


def main():
    script_dir = Path(__file__).resolve().parent
    cfg_path = script_dir / "scenarios.yaml"

    scenarios = load_scenarios_config(cfg_path)
    available_scenarios = list(scenarios.keys())

    parser = argparse.ArgumentParser(
        description="Scenario to run.",
        epilog=f"Available scenarios: {', '.join(available_scenarios)}"
    )
    parser.add_argument(
        "scenario_name",
        metavar="SCENARIO",
        help="Name of the scenario to run.",
        choices=available_scenarios,
    )
    args, passthrough_args = parser.parse_known_args()

    scenario_config = scenarios[args.scenario_name]

    lifecycle_paths = [f"e2e/lifecycle/{file}" for file in scenario_config.get("lifecycle", [])]

    validation_paths = []
    val_cfg = scenario_config.get("validation", {})
    markers = scenario_config.get("markers")

    if markers and not val_cfg:
        logger.debug("Markers are defined but no 'validation' section found. Defaulting to 'e2e/validation' directory.")
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
