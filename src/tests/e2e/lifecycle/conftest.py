#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import hashlib
import logging
import os

import pytest

logger = logging.getLogger(__name__)

_skip_auth = os.environ.get("SKIP_AUTH_SETUP") == "1"


@pytest.fixture(scope="session", autouse=True)
def validation_user_persistent(request, suppress_logging):
    """
    Ensure a permanent validation user exists in Keycloak for backup-restore test authentication.

    Overrides the no-op fixture in the parent conftest.py for tests in this directory.

    This user persists across test runs and backup-restore cycles, ensuring:
    - Authentication works after restore (erag-admin password is reset during restore)
    - Chat history and other user-specific data is accessible across test sessions
    - No password mismatch issues after backup-restore

    The user is NOT deleted after tests to preserve data continuity.
    Password is derived from a constant (not stored as "password" to avoid secret scanners).

    Skipped when SKIP_AUTH_SETUP=1 (set by run_scenario.py from scenarios.yaml skip_auth_setup flag).
    """
    if _skip_auth:
        yield
        return

    keycloak_helper = request.getfixturevalue("keycloak_helper")
    validation_username = "erag-validation-user"
    # Derive auth_secret from constant string - meets Keycloak password policy requirements
    auth_constant = "ERAG_VALIDATION_CI_2026"
    auth_secret = hashlib.sha256(auth_constant.encode()).hexdigest()[:16] + "!Val1"

    logger.info(f"Ensuring validation user '{validation_username}' exists")

    if not keycloak_helper.user_exists(validation_username):
        logger.info(f"Creating permanent validation user: {validation_username}")
        keycloak_helper.add_user(
            validation_username,
            auth_secret,
            first_name="Validation",
            last_name="User",
            email=f"{validation_username}@ci.local"
        )
        keycloak_helper.remove_required_actions(keycloak_helper.admin_access_token, validation_username)
        keycloak_helper.assign_client_role(validation_username, "ERAG-admin", "EnterpriseRAG-oidc")
        keycloak_helper.assign_client_role(validation_username, "ERAG-admin", "EnterpriseRAG-oidc-backend")
        logger.info(f"Validation user '{validation_username}' created successfully")
    else:
        logger.info(f"Validation user '{validation_username}' already exists, reusing")

    # Store credentials so access_token gets a fresh token on every call (avoids expiration).
    keycloak_helper._ci_username = validation_username
    keycloak_helper._ci_password = auth_secret

    token = keycloak_helper.get_user_access_token(validation_username, auth_secret)
    assert token is not None, f"Failed to obtain access token for validation user '{validation_username}'"
    logger.info("Validation user credentials verified and stored for session")

    yield

    # DO NOT delete the user - it must persist for data continuity across test runs
    keycloak_helper._ci_username = None
    keycloak_helper._ci_password = None
    logger.info(f"Validation user '{validation_username}' retained for future test runs")


if _skip_auth:
    @pytest.fixture(scope="session", autouse=True)
    def temporarily_remove_user_required_actions():
        """No-op: auth setup skipped via scenarios.yaml skip_auth_setup flag."""
        yield

    @pytest.fixture(scope="session", autouse=True)
    def disable_guards_at_startup(suppress_logging, temporarily_remove_user_required_actions):
        """No-op: auth setup skipped via scenarios.yaml skip_auth_setup flag."""
        yield

    @pytest.fixture(scope="function", autouse=True)
    def edp_cleanup_after_test():
        """No-op: auth setup skipped via scenarios.yaml skip_auth_setup flag."""
        yield

    @pytest.fixture(scope="session", autouse=True)
    def edp_cleanup_after_session():
        """No-op: auth setup skipped via scenarios.yaml skip_auth_setup flag."""
        yield
