#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os

import requests
from tests.e2e.validation.constants import ERAG_AUTH_DOMAIN, VITE_KEYCLOAK_CLIENT_ID, VITE_KEYCLOAK_REALM


logger = logging.getLogger(__name__)
DEFAULT_CREDENTIALS_PATH = "../../deployment/ansible-logs/default_credentials.txt"


class CredentialsNotFound(Exception):
    pass


class KeycloakHelper:

    def __init__(self, credentials_file, k8s_helper):
        credentials = self.get_credentials(credentials_file)
        self.erag_admin_username = credentials["KEYCLOAK_ERAG_ADMIN_USERNAME"]
        self.erag_admin_password = credentials["KEYCLOAK_ERAG_ADMIN_PASSWORD"]
        self.erag_user_username = credentials["KEYCLOAK_ERAG_USER_USERNAME"]
        self.erag_user_password = credentials["KEYCLOAK_ERAG_USER_PASSWORD"]
        self.k8s_helper = k8s_helper
        self._access_token = None
        self._admin_access_token = None
        self._admin_pass = self.k8s_helper.retrieve_admin_password(secret_name="keycloak", namespace="auth")

    @property
    def access_token(self):
        return self.get_access_token()

    @property
    def admin_access_token(self):
        return self.get_admin_access_token()

    def get_access_token(self, as_user=False):
        """
        Get the access token for the erag-admin user.
        User's required actions need to be temporarily removed in order to obtain the token.
        """
        if as_user:
            return self.get_user_access_token(self.erag_user_username, self.erag_user_password)
        return self.get_user_access_token(self.erag_admin_username, self.erag_admin_password)

    def get_credentials(self, credentials_file):
        if credentials_file:
            if os.path.exists(credentials_file):
                logger.debug(f"Loading {credentials_file} in order to obtain ERAG admin credentials")
                return self._parse_credentials_file(credentials_file)
            else:
                logger.warning(f"Provided credentials file (--credentials-file={credentials_file}) does not exist. "
                               f"Proceeding with default_credentials.txt")

        if os.path.exists(DEFAULT_CREDENTIALS_PATH):
            logger.debug("Loading default_credentials.txt in order to obtain ERAG admin credentials")
            return self._parse_credentials_file(DEFAULT_CREDENTIALS_PATH)
        else:
            logger.error(f"Path to default credentials file not found: {DEFAULT_CREDENTIALS_PATH}")
            raise CredentialsNotFound()

    def _parse_credentials_file(self, file_path):
        """Parse the credentials file and return a corresponding dictionary"""
        credentials = {}
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore empty lines and comments
                    key, value = line.split("=", 1)
                    credentials[key] = value.strip('"')
        return credentials

    def get_admin_access_token(self):
        """Get the access token for the admin user. It is needed in order to obtain erag-admin user_id"""
        return self._obtain_access_token("master", "admin", self._admin_pass, "admin-cli")

    def get_user_access_token(self, username, password):
        """Get the access token for the erag-admin user"""
        return self._obtain_access_token(VITE_KEYCLOAK_REALM,
                                         username,
                                         password,
                                         VITE_KEYCLOAK_CLIENT_ID)

    def _obtain_access_token(self, realm, username, password, client_id):
        logger.debug(f"Obtaining access token for user '{username}'")
        token_url = f"{ERAG_AUTH_DOMAIN}/realms/{realm}/protocol/openid-connect/token"
        data = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": client_id,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(token_url, data=data, headers=headers, verify=False)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception(f"Failed to get access token for user '{username}'. Response: {response.text}")

    def read_current_required_actions(self, admin_access_token, user):
        """Read the required actions for the user. We need to revert them back after obtaining the token."""
        logger.debug("Checking if there are any required actions for the user")
        user_id = self._get_user_id(admin_access_token, user)
        headers = {
            "Authorization": f"Bearer {admin_access_token}",
            "Content-Type": "application/json"
        }

        url = f"{ERAG_AUTH_DOMAIN}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}"
        response = requests.get(url, headers=headers, verify=False)
        return response.json().get("requiredActions", [])

    def remove_required_actions(self, admin_access_token, user):
        """Remove required actions from the user. Otherwise, we'll get 'Account is not fully set up' error."""
        logger.debug("Temporarily removing actions required for the user in order to obtain the token")
        user_id = self._get_user_id(admin_access_token, user)
        self._set_required_actions([], admin_access_token, user_id)

    def revert_required_actions(self, required_actions, admin_token, user):
        """Revert required actions back to the original state"""
        logger.debug("Reverting required actions back to the original state")
        user_id = self._get_user_id(admin_token, user)
        self._set_required_actions(required_actions, admin_token, user_id)

    def _get_user_id(self, admin_access_token, username):
        """Get user_id of erag-admin user"""
        logger.debug(f"Obtaining user_id for user '{username}'")
        url = f"{ERAG_AUTH_DOMAIN}/admin/realms/{VITE_KEYCLOAK_REALM}/users?username={username}"
        headers = {
            "Authorization": f"Bearer {admin_access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            users = response.json()
            return users[0].get('id')

    def _set_required_actions(self, required_actions, admin_token, user_id):
        url = f"{ERAG_AUTH_DOMAIN}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        payload = {"requiredActions": required_actions}
        response = requests.put(url, json=payload, headers=headers, verify=False)
        assert response.status_code == 204, f"Failed to remove required actions. Status code: {response.status_code}"

    def set_brute_force_detection(self, enabled: bool):
        """
        Enable or disable brute force detection for the Keycloak realm.
        :param enabled: True to enable, False to disable
        """
        logger.info(f"{'Enabling' if enabled else 'Disabling'} brute force detection for the Keycloak realm")
        url = f"{ERAG_AUTH_DOMAIN}/admin/realms/{VITE_KEYCLOAK_REALM}"
        headers = {
            "Authorization": f"Bearer {self.admin_access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch realm settings (status {response.status_code}): {response.text}")
        realm_settings = response.json()
        realm_settings["bruteForceProtected"] = enabled
        response = requests.put(url, json=realm_settings, headers=headers, verify=False)
        if response.status_code != 204:
            raise Exception(f"Failed to update brute force detection (status {response.status_code}): {response.text}")
