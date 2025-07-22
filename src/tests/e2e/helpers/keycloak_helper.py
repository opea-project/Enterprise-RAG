#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import logging
import os

import kr8s
import requests
from tests.e2e.validation.constants import (ERAG_AUTH_DOMAIN,
                                  INGRESS_NGINX_CONTROLLER_NS,
                                  INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR,
                                  VITE_KEYCLOAK_CLIENT_ID, VITE_KEYCLOAK_REALM)

from tests.e2e.helpers.api_request_helper import CustomPortForward

logger = logging.getLogger(__name__)
DEFAULT_CREDENTIALS_PATH = "../../deployment/ansible-logs/default_credentials.txt"


class CredentialsNotFound(Exception):
    pass


class KeycloakHelper:

    def __init__(self, credentials_file):
        self.credentials_file = credentials_file

    def get_access_token(self):
        """
        Get the access token for the erag-admin user.
        User's required actions need to be temporarily removed in order to obtain the token.
        """
        admin_token = self.get_admin_access_token()
        erag_admin_user, erag_admin_pass = self.get_erag_admin_credentials()
        user_id = self.get_user_id(admin_token, erag_admin_user)
        required_actions = self.read_current_required_actions(admin_token, user_id)
        if required_actions:
            self.remove_required_actions(admin_token, user_id)
        try:
            user_access_token = self.get_user_access_token(erag_admin_user, erag_admin_pass)
        finally:
            if required_actions:
                self.revert_required_actions(required_actions, admin_token, user_id)
        return user_access_token

    def get_erag_admin_credentials(self):
        if self.credentials_file:
            if os.path.exists(self.credentials_file):
                logger.debug(f"Loading {self.credentials_file} in order to obtain ERAG admin credentials")
                username, password = self._parse_credentials_file(self.credentials_file)
                if username and password:
                    return username, password
                else:
                    logger.warning(f"Failed to obtain ERAG admin credentials from {self.credentials_file}. "
                                   f"Proceeding with default_credentials.txt")
            else:
                logger.warning(f"Provided credentials file (--credentials-file={self.credentials_file}) does not exist. "
                               f"Proceeding with default_credentials.txt")

        if os.path.exists(DEFAULT_CREDENTIALS_PATH):
            logger.debug("Loading default_credentials.txt in order to obtain ERAG admin credentials")
            return self._parse_credentials_file(DEFAULT_CREDENTIALS_PATH)
        else:
            logger.error(f"Path to default credentials file not found: {DEFAULT_CREDENTIALS_PATH}")
            raise CredentialsNotFound()

    def _parse_credentials_file(self, file_path):
        erag_admin_username = ""
        erag_admin_password = ""
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore empty lines and comments
                    key, value = line.split("=", 1)
                    if key == "KEYCLOAK_ERAG_ADMIN_PASSWORD":
                        erag_admin_password = value.strip('"')
                    elif key == "KEYCLOAK_ERAG_ADMIN_USERNAME":
                        erag_admin_username = value.strip('"')
        return erag_admin_username, erag_admin_password

    def get_admin_access_token(self):
        """Get the access token for the admin user. It is needed in order to obtain erag-admin user_id"""
        admin_pass = self._retrieve_admin_password()
        return self._obtain_access_token("master", "admin", admin_pass, "admin-cli")

    def _retrieve_admin_password(self):
        """Retrieve the admin password from the keycloak secret"""
        keycloak_secret_name = "keycloak"
        logger.debug(f"Retrieving the admin password from the '{keycloak_secret_name}' secret")
        secrets = kr8s.get("secrets", namespace="auth")
        for secret in secrets:
            if secret.name == keycloak_secret_name:
                # Extract and decode the base64-encoded password
                encoded_password = secret.data.get("admin-password")
                return base64.b64decode(encoded_password).decode().strip()

    def get_user_id(self, admin_access_token, username):
        """Get user_id of erag-admin user"""
        logger.debug(f"Obtaining user_id for user '{username}'")
        url = f"{ERAG_AUTH_DOMAIN}/admin/realms/{VITE_KEYCLOAK_REALM}/users?username={username}"
        headers = {
            "Authorization": f"Bearer {admin_access_token}",
            "Content-Type": "application/json"
        }

        with CustomPortForward(443, INGRESS_NGINX_CONTROLLER_NS,
                               INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR, 443):
            response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            users = response.json()
            return users[0].get('id')

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

        with CustomPortForward(443, INGRESS_NGINX_CONTROLLER_NS,
                               INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR, 443):
            response = requests.post(token_url, data=data, headers=headers, verify=False)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception(f"Failed to get access token for user '{username}'. Response: {response.text}")

    def read_current_required_actions(self, admin_access_token, user_id):
        """Read the required actions for the user. We need to revert them back after obtaining the token."""
        logger.debug("Checking if there are any required actions for the user")
        headers = {
            "Authorization": f"Bearer {admin_access_token}",
            "Content-Type": "application/json"
        }

        url = f"{ERAG_AUTH_DOMAIN}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}"
        with CustomPortForward(443, INGRESS_NGINX_CONTROLLER_NS,
                               INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR, 443):
            response = requests.get(url, headers=headers, verify=False)
        return response.json().get("requiredActions", [])

    def remove_required_actions(self, admin_access_token, user_id):
        """Remove required actions from the user. Otherwise, we'll get 'Account is not fully set up' error."""
        logger.debug("Temporarily removing actions required for the user in order to obtain the token")
        self._set_required_actions([], admin_access_token, user_id)

    def revert_required_actions(self, required_actions, admin_token, user_id):
        """Revert required actions back to the original state"""
        logger.debug("Reverting required actions back to the original state")
        self._set_required_actions(required_actions, admin_token, user_id)

    def _set_required_actions(self, required_actions, admin_token, user_id):
        url = f"{ERAG_AUTH_DOMAIN}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        payload = {"requiredActions": required_actions}

        with CustomPortForward(443, INGRESS_NGINX_CONTROLLER_NS,
                               INGRESS_NGINX_CONTROLLER_POD_LABEL_SELECTOR, 443):
            response = requests.put(url, json=payload, headers=headers, verify=False)
        assert response.status_code == 204, f"Failed to remove required actions. Status code: {response.status_code}"
