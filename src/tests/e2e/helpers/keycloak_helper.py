#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import re
import requests
import urllib.parse
from urllib.parse import urljoin

from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import VITE_KEYCLOAK_CLIENT_ID, VITE_KEYCLOAK_REALM

logger = logging.getLogger(__name__)

# Microsoft login endpoint
MSFT_LOGIN_URL = "https://login.microsoftonline.com"

# Determine the absolute path to the default credentials file
# This file is located relative to the src/tests/e2e/helpers directory
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_CREDENTIALS_RELATIVE = "../../../../deployment/ansible-logs/default_credentials.txt"

DEFAULT_CREDENTIALS_PATH = os.path.normpath(os.path.join(_CURRENT_DIR, _DEFAULT_CREDENTIALS_RELATIVE))


class CredentialsNotFound(Exception):
    pass


class KeycloakHelper:

    def __init__(self, credentials_file, k8s_helper):
        credentials = self.get_credentials(credentials_file)
        fqdn = cfg.get('FQDN', 'erag.com')
        routing_mode = cfg.get('routing_mode', 'subdomain')
        if routing_mode == 'path':
            self.erag_auth_domain = f"https://{fqdn}/auth"
        else:
            self.erag_auth_domain = f"https://auth.{fqdn}"
        self.erag_admin_username = credentials["KEYCLOAK_ERAG_ADMIN_USERNAME"]
        self.erag_admin_password = credentials["KEYCLOAK_ERAG_ADMIN_PASSWORD"]
        self.erag_user_username = credentials["KEYCLOAK_ERAG_USER_USERNAME"]
        self.erag_user_password = credentials["KEYCLOAK_ERAG_USER_PASSWORD"]
        self.erag_maintainer_username = credentials.get("KEYCLOAK_ERAG_MAINTAINER_USERNAME", "")
        self.erag_maintainer_password = credentials.get("KEYCLOAK_ERAG_MAINTAINER_PASSWORD", "")
        self.erag_sso_admin_username = os.getenv("KEYCLOAK_ERAG_SSO_ADMIN_USERNAME", "")
        self.erag_sso_admin_password = os.getenv("KEYCLOAK_ERAG_SSO_ADMIN_PASSWORD", "")
        self.erag_sso_user_username = os.getenv("KEYCLOAK_ERAG_SSO_USER_USERNAME", "")
        self.erag_sso_user_password = os.getenv("KEYCLOAK_ERAG_SSO_USER_PASSWORD", "")
        self.k8s_helper = k8s_helper
        self._access_token = None
        self._admin_access_token = None
        self._ci_username = None
        self._ci_password = None
        self._admin_pass = self.k8s_helper.retrieve_admin_password(secret_name="keycloak", namespace="auth")
        self._sso_admin_bootstrapped = False
        self._sso_user_bootstrapped = False

    @property
    def access_token(self):
        if self._ci_username is not None:
            return self.get_user_access_token(self._ci_username, self._ci_password)
        return self.get_access_token()

    @property
    def admin_access_token(self):
        return self.get_admin_access_token()

    def get_access_token(self, as_user=False):
        """
        Get the access token for the erag-admin user.
        User's required actions need to be temporarily removed in order to obtain the token.
        """
        if as_user == "sso" or as_user == "sso_admin":
            return self.get_sso_access_token("sso_admin")
        if as_user == "sso_user":
            return self.get_sso_access_token("sso_user")
        if as_user == "maintainer":
            return self.get_user_access_token(self.erag_maintainer_username, self.erag_maintainer_password)
        if as_user:
            # For user tokens, don't cache to avoid complexity
            return self.get_user_access_token(self.erag_user_username, self.erag_user_password)

        return self.get_user_access_token(self.erag_admin_username, self.erag_admin_password)

    def _follow_form_redirects(self, session, resp, max_hops=10):
        """
        Follow HTML form-based auto-submit redirects (POST forms with hidden fields).
        Some IdPs (like Microsoft Entra ID) use these instead of HTTP 3xx redirects.
        Returns the final response after all form redirects have been followed.
        """
        for _ in range(max_hops):
            # Check if response contains an auto-submit form
            form_action_match = re.search(r'<form[^>]*method="POST"[^>]*action="([^"]+)"', resp.text, re.IGNORECASE)
            if not form_action_match:
                break

            form_action = form_action_match.group(1).replace("&amp;", "&")
            logger.debug(f"SSO flow: following form redirect to {form_action}")

            # Extract all hidden input fields
            form_data = {}
            for input_match in re.finditer(
                r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', resp.text, re.IGNORECASE
            ):
                form_data[input_match.group(1)] = input_match.group(2)

            # Also match inputs where value comes before name
            for input_match in re.finditer(
                r'<input[^>]*type="hidden"[^>]*value="([^"]*)"[^>]*name="([^"]+)"', resp.text, re.IGNORECASE
            ):
                form_data[input_match.group(2)] = input_match.group(1)

            if not form_data:
                logger.debug("SSO flow: form found but no hidden fields, stopping")
                break

            resp = session.post(form_action, data=form_data, allow_redirects=True)

        return resp

    def _extract_all_form_fields(self, html):
        """Extract all input fields (hidden, text, email, etc.) from HTML form(s)."""
        form_data = {}
        # Match all <input> elements with a name attribute
        for m in re.finditer(r'<input[^>]*>', html, re.IGNORECASE):
            tag = m.group(0)
            name_match = re.search(r'name="([^"]+)"', tag, re.IGNORECASE)
            if not name_match:
                continue
            name = name_match.group(1)
            value_match = re.search(r'value="([^"]*)"', tag, re.IGNORECASE)
            value = value_match.group(1) if value_match else ""
            form_data[name] = value
        return form_data

    def _handle_keycloak_broker_pages(self, session, resp, sso_username, max_pages=10):
        """
        Handle Keycloak's first-broker-login / update-profile / confirm-link pages
        that appear when a federated (SSO) user logs in for the first time or
        when Keycloak needs to link/confirm the external identity.

        Returns the final response after all broker pages have been handled.
        """
        for iteration in range(max_pages):
            # Check if we're on a Keycloak login-actions page
            if "login-actions" not in resp.url:
                break

            logger.debug(f"SSO flow: handling Keycloak broker page (iteration {iteration}) at {resp.url}")
            logger.debug(f"SSO flow: page title: {re.search(r'<title>([^<]*)</title>', resp.text, re.IGNORECASE)}")

            # Find all forms with POST method
            # Try multiple form patterns to be robust
            form_action = None

            # Pattern 1: form with id containing "kc-"
            m = re.search(r'<form[^>]*id="kc-[^"]*"[^>]*action="([^"]+)"', resp.text, re.IGNORECASE)
            if m:
                form_action = m.group(1).replace("&amp;", "&")
            else:
                # Pattern 2: form with action and method=POST (action first)
                m = re.search(r'<form[^>]*action="([^"]+)"[^>]*method="[Pp][Oo][Ss][Tt]"', resp.text, re.IGNORECASE)
                if m:
                    form_action = m.group(1).replace("&amp;", "&")
                else:
                    # Pattern 3: form with method=POST and action (method first)
                    m = re.search(r'<form[^>]*method="[Pp][Oo][Ss][Tt]"[^>]*action="([^"]+)"', resp.text, re.IGNORECASE)
                    if m:
                        form_action = m.group(1).replace("&amp;", "&")

            if not form_action:
                logger.debug("SSO flow: no POST form found on Keycloak broker page, stopping")
                break

            logger.debug(f"SSO flow: Keycloak broker form action: {form_action}")

            # Extract all form fields (hidden + visible inputs)
            form_data = self._extract_all_form_fields(resp.text)

            # Determine what kind of broker page this is and fill in accordingly
            page_type = "unknown"

            if "update-profile" in resp.url or "idp-review-user-profile" in resp.url:
                page_type = "update-profile"
            elif "first-broker-login" in resp.url:
                # Could be update-profile or confirm-link — check page content
                if any(field in resp.text for field in ['name="firstName"', 'name="lastName"', 'name="email"']):
                    page_type = "update-profile"
                elif 'name="submitAction"' in resp.text:
                    page_type = "confirm-link"
                else:
                    page_type = "update-profile"  # Default to profile update

            logger.debug(f"SSO flow: detected broker page type: {page_type}")

            if page_type == "update-profile":
                # Fill in profile fields with defaults if they are empty
                profile_defaults = {
                    "email": sso_username,
                    "firstName": sso_username.split("@")[0],
                    "lastName": "SSO",
                    "username": sso_username,
                }
                for field_name, default_value in profile_defaults.items():
                    if field_name in form_data:
                        if not form_data[field_name]:
                            form_data[field_name] = default_value
                    elif f'name="{field_name}"' in resp.text:
                        form_data[field_name] = default_value

            elif page_type == "confirm-link":
                # Look for submitAction buttons — prefer "linkAccount" over "updateProfile"
                # to link to an existing account rather than creating a new one
                submit_values = re.findall(
                    r'(?:button|input)[^>]*name="submitAction"[^>]*value="([^"]+)"',
                    resp.text, re.IGNORECASE
                )
                if submit_values:
                    # Prefer linkAccount if available
                    if "linkAccount" in submit_values:
                        form_data["submitAction"] = "linkAccount"
                    else:
                        form_data["submitAction"] = submit_values[0]
                    logger.debug(f"SSO flow: submitAction={form_data['submitAction']} (available: {submit_values})")

            logger.debug(f"SSO flow: submitting Keycloak broker form with fields: {list(form_data.keys())}")

            resp = session.post(form_action, data=form_data, allow_redirects=True)

            # Follow any HTML form redirects that may follow
            resp = self._follow_form_redirects(session, resp)

        return resp

    def bootstrap_sso_user(self, sso_role="sso_admin"):
        """
        Perform the SSO login flow once to ensure the federated user is created
        and linked in Keycloak. This handles the first-broker-login pages
        (review profile, account linking) that Keycloak shows on the first
        federated login.

        Args:
            sso_role: "sso_admin" or "sso_user"
        """
        if sso_role == "sso_admin":
            if self._sso_admin_bootstrapped:
                return
            username = self.erag_sso_admin_username
            password = self.erag_sso_admin_password
        elif sso_role == "sso_user":
            if self._sso_user_bootstrapped:
                return
            username = self.erag_sso_user_username
            password = self.erag_sso_user_password
        else:
            raise ValueError(f"Unknown SSO role: {sso_role}")

        if not password:
            logger.warning(f"SSO password not set for {sso_role} ({username}) — skipping bootstrap")
            return

        logger.info(f"Bootstrapping SSO {sso_role} user '{username}' — performing initial login")

        try:
            self._perform_sso_login(username, password)
            logger.info(f"SSO {sso_role} user '{username}' bootstrapped successfully")
        except Exception as e:
            logger.error(f"Failed to bootstrap SSO {sso_role} user '{username}': {e}")
            raise

        if sso_role == "sso_admin":
            self._sso_admin_bootstrapped = True
        else:
            self._sso_user_bootstrapped = True

    def get_sso_access_token(self, sso_role="sso_admin"):
        """
        Get access token for the SSO user. If the user hasn't been bootstrapped yet,
        perform the initial login (handling broker pages) first.

        Args:
            sso_role: "sso_admin" or "sso_user"
        """
        if sso_role == "sso_admin":
            if not self._sso_admin_bootstrapped:
                self.bootstrap_sso_user("sso_admin")
            return self._perform_sso_login(self.erag_sso_admin_username, self.erag_sso_admin_password)
        elif sso_role == "sso_user":
            if not self._sso_user_bootstrapped:
                self.bootstrap_sso_user("sso_user")
            return self._perform_sso_login(self.erag_sso_user_username, self.erag_sso_user_password)
        else:
            raise ValueError(f"Unknown SSO role: {sso_role}")

    def _perform_sso_login(self, sso_username, sso_password):
        """
        Authenticate an SSO (federated) user by simulating the browser-based OIDC login flow:
        1. Initiate Keycloak auth code flow
        2. Follow redirect to the external IdP (Microsoft Entra ID)
        3. Submit username to Microsoft (step 1 of 2)
        4. Submit password to Microsoft (step 2 of 2)
        5. Follow form-based redirects back to Keycloak
        6. Handle any Keycloak broker pages (first-broker-login, profile update, etc.)
        7. Exchange the auth code for a Keycloak access token
        """
        oidc_cfg = cfg.get("keycloak", {}).get("oidc", {})
        tenant_id = oidc_cfg.get("tenant_id")
        idp_alias = oidc_cfg.get("alias", "oidc")

        if not tenant_id:
            raise RuntimeError("OIDC configuration (tenant_id) is required for SSO authentication")

        redirect_uri = f"https://{cfg.get('FQDN')}"
        keycloak_auth_url = (
            f"{self.erag_auth_domain}/realms/{VITE_KEYCLOAK_REALM}/protocol/openid-connect/auth"
            f"?client_id={VITE_KEYCLOAK_CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(redirect_uri, safe='')}"
            f"&response_type=code"
            f"&scope=openid"
            f"&kc_idp_hint={idp_alias}"
        )

        session = requests.Session()
        session.verify = False

        logger.debug(f"SSO flow: initiating auth code flow for user '{sso_username}'")

        # Step 1: Hit Keycloak auth endpoint - it will redirect to Microsoft login
        resp = session.get(keycloak_auth_url, allow_redirects=True)
        if resp.status_code != 200:
            raise RuntimeError(
                f"SSO flow: failed to reach Microsoft login page. "
                f"Status: {resp.status_code}, URL: {resp.url}"
            )

        # Capture the base URL of the Microsoft login page for resolving relative URLs
        msft_base_url = f"{urllib.parse.urlparse(resp.url).scheme}://{urllib.parse.urlparse(resp.url).netloc}"

        # Step 2: Extract the login form tokens from Microsoft's login page
        flow_token_match = re.search(r'"sFT"\s*:\s*"([^"]+)"', resp.text)
        ctx_match = re.search(r'"sCtx"\s*:\s*"([^"]+)"', resp.text)
        post_url_match = re.search(r'"urlPost"\s*:\s*"([^"]+)"', resp.text)

        if not all([flow_token_match, ctx_match, post_url_match]):
            raise RuntimeError(
                f"SSO flow: could not extract login form tokens from Microsoft page. URL: {resp.url}\n"
                f"Page snippet: {resp.text[:2000]}"
            )

        flow_token = flow_token_match.group(1)
        ctx = ctx_match.group(1)
        post_url = post_url_match.group(1)

        # Resolve relative URL against the Microsoft login base URL
        if not post_url.startswith("http"):
            post_url = urljoin(msft_base_url, post_url)

        # Also extract the original canary value if available
        canary_match = re.search(r'"canary"\s*:\s*"([^"]+)"', resp.text)
        canary = canary_match.group(1) if canary_match else ""

        # Step 3: Call GetCredentialType to advance Microsoft's two-step login
        logger.debug(f"SSO flow: calling GetCredentialType for user '{sso_username}'")

        get_cred_type_url = f"{msft_base_url}/{tenant_id}/GetCredentialType?mkt=en-US"
        get_cred_type_payload = {
            "username": sso_username,
            "isOtherIdpSupported": True,
            "checkPhones": False,
            "isRemoteNGCSupported": True,
            "isCookieBannerShown": False,
            "isFidoSupported": True,
            "originalRequest": ctx,
            "country": "US",
            "forceotclogin": False,
            "isExternalFederationDisallowed": False,
            "isRemoteConnectSupported": False,
            "federationFlags": 0,
            "isSignup": False,
            "flowToken": flow_token,
            "isAccessPassSupported": True,
        }

        cred_resp = session.post(
            get_cred_type_url,
            json=get_cred_type_payload,
            headers={"Content-Type": "application/json"},
        )
        logger.debug(f"SSO flow: GetCredentialType status={cred_resp.status_code}")

        # Extract updated flow token from GetCredentialType response
        try:
            cred_data = cred_resp.json()
            updated_flow_token = cred_data.get("FlowToken", flow_token)
        except Exception:
            updated_flow_token = flow_token

        # Step 4: Submit username + password to Microsoft
        logger.debug(f"SSO flow: submitting credentials to Microsoft for user '{sso_username}'")

        login_data = {
            "i13": "0",
            "login": sso_username,
            "loginfmt": sso_username,
            "type": "11",
            "LoginOptions": "3",
            "lrt": "",
            "lrtPartition": "",
            "hisRegion": "",
            "hisScaleUnit": "",
            "passwd": sso_password,
            "ps": "2",
            "psRNGCDefaultType": "",
            "psRNGCEntropy": "",
            "psRNGCSLK": "",
            "canary": canary,
            "ctx": ctx,
            "hpgrequestid": "",
            "flowToken": updated_flow_token,
            "PPSX": "",
            "NewUser": "1",
            "FoundMSAs": "",
            "fspost": "0",
            "i21": "0",
            "CookieDisclosure": "0",
            "IsFidoSupported": "1",
            "isSignupPost": "0",
            "i19": "0",
        }

        resp = session.post(post_url, data=login_data, allow_redirects=True)

        # Check if Microsoft returned an error (e.g. wrong password)
        error_code_match = re.search(r'"sErrorCode"\s*:\s*"([^"]*)"', resp.text)
        if error_code_match and error_code_match.group(1):
            error_msg_match = re.search(r'"sErrTxt"\s*:\s*"([^"]*)"', resp.text)
            error_msg = error_msg_match.group(1) if error_msg_match else "unknown"
            raise RuntimeError(
                f"SSO flow: Microsoft login error. Code: {error_code_match.group(1)}, "
                f"Message: {error_msg}\nURL: {resp.url}"
            )

        # Follow any form-based redirects after credential submission
        resp = self._follow_form_redirects(session, resp)

        # Step 5: Handle "Stay signed in?" (KMSI) prompt if present
        if "kmsi" in resp.url.lower() or "KmsiInterrupt" in resp.text:
            logger.debug("SSO flow: handling 'Stay signed in?' prompt")
            flow_token_match = re.search(r'"sFT"\s*:\s*"([^"]+)"', resp.text)
            ctx_match = re.search(r'"sCtx"\s*:\s*"([^"]+)"', resp.text)
            post_url_match = re.search(r'"urlPost"\s*:\s*"([^"]+)"', resp.text)

            if flow_token_match and ctx_match and post_url_match:
                kmsi_post_url = post_url_match.group(1)
                if not kmsi_post_url.startswith("http"):
                    kmsi_post_url = urljoin(msft_base_url, kmsi_post_url)
                kmsi_data = {
                    "LoginOptions": "1",
                    "type": "28",
                    "ctx": ctx_match.group(1),
                    "flowToken": flow_token_match.group(1),
                }
                resp = session.post(kmsi_post_url, data=kmsi_data, allow_redirects=True)

                # Follow any form-based redirects after KMSI
                resp = self._follow_form_redirects(session, resp)

        # Step 6: Handle Keycloak first-broker-login / update-profile / confirm-link pages
        if "login-actions" in resp.url:
            logger.debug("SSO flow: detected Keycloak broker login page, handling it")
            resp = self._handle_keycloak_broker_pages(session, resp, sso_username)

        # Step 7: Check if we ended up at the redirect URI with a code
        final_url = resp.url
        parsed = urllib.parse.urlparse(final_url)
        query_params = urllib.parse.parse_qs(parsed.query)

        if "code" not in query_params:
            # One more attempt: check for form-based redirect with code
            resp = self._follow_form_redirects(session, resp)
            final_url = resp.url
            parsed = urllib.parse.urlparse(final_url)
            query_params = urllib.parse.parse_qs(parsed.query)

        if "code" not in query_params:
            # Also check fragment (some flows use fragment instead of query)
            fragment_params = urllib.parse.parse_qs(parsed.fragment)
            if "code" in fragment_params:
                query_params = fragment_params

        if "code" not in query_params:
            # Try to find if an error occurred
            error_match = re.search(r'"strServiceExceptionMessage"\s*:\s*"([^"]+)"', resp.text)
            error_msg = error_match.group(1) if error_match else "unknown error"
            error_code_match = re.search(r'"sErrorCode"\s*:\s*"([^"]*)"', resp.text)
            error_code = error_code_match.group(1) if error_code_match else ""
            raise RuntimeError(
                f"SSO flow: did not receive authorization code after login. "
                f"Final URL: {final_url}\n"
                f"Microsoft error: {error_msg}\n"
                f"Microsoft error code: {error_code}\n"
                f"Page snippet: {resp.text[:2000]}"
            )

        auth_code = query_params["code"][0]
        logger.debug("SSO flow: received authorization code, exchanging for token")

        # Step 8: Exchange auth code for Keycloak token
        token_url = f"{self.erag_auth_domain}/realms/{VITE_KEYCLOAK_REALM}/protocol/openid-connect/token"
        token_data = {
            "grant_type": "authorization_code",
            "client_id": VITE_KEYCLOAK_CLIENT_ID,
            "code": auth_code,
            "redirect_uri": redirect_uri,
        }
        token_resp = session.post(token_url, data=token_data)
        if token_resp.status_code != 200:
            raise RuntimeError(
                f"SSO flow: failed to exchange auth code for token. "
                f"HTTP status: {token_resp.status_code}\nResponse: {token_resp.text}"
            )

        access_token = token_resp.json().get("access_token")
        logger.debug(f"SSO flow: successfully obtained Keycloak access token for '{sso_username}'")
        return access_token

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
        """
        Proper error handling and troubleshooting information is essential here as authentication
        failures can impact accuracy evaluator scripts and other tools that need to authenticate with the RAG system via keycloak helper.
        """
        logger.debug(f"Obtaining access token for user '{username}'")
        token_url = f"{self.erag_auth_domain}/realms/{realm}/protocol/openid-connect/token"
        data = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": client_id,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Common troubleshooting instructions
        troubleshooting = (
            "\nTroubleshooting:\n"
            f"1. Verify that the Keycloak domain is reachable. Current auth domain: {self.erag_auth_domain}\n"
            "   Check /etc/hosts has the correct entry for your FQDN.\n\n"
            "2. Check connectivity with a simple request:\n"
            f"   curl -v -k {token_url}\n"
            "   Expected: an HTTP response of any kind, indicating that the endpoint is reachable\n\n"
        )

        try:
            response = requests.post(token_url, data=data, headers=headers, verify=False, timeout=10)
            response.raise_for_status()  # Raises HTTPError for non-200 response

            return response.json().get("access_token")

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error while obtaining access token for user '{username}'. Error: {e}\n{troubleshooting}")
            raise e
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to get access token for user '{username}'. HTTP status: {response.status_code}\n"
                f"Response: {response.text}\n{troubleshooting}"
            )
            raise e
        except Exception as e:
            logger.error(f"Unexpected error while obtaining access token for user '{username}'. Error: {e}\n{troubleshooting}")
            raise e

    def read_current_required_actions(self, admin_access_token, user):
        """Read the required actions for the user. We need to revert them back after obtaining the token."""
        logger.debug("Checking if there are any required actions for the user")
        user_id = self._get_user_id(admin_access_token, user)
        headers = {
            "Authorization": f"Bearer {admin_access_token}",
            "Content-Type": "application/json"
        }

        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}"
        response = requests.get(url, headers=headers, verify=False)
        return response.json().get("requiredActions", [])

    def remove_required_actions(self, admin_access_token, user):
        """Remove required actions from the user. Otherwise, we'll get 'Account is not fully set up' error."""
        logger.debug(f"Temporarily removing actions required for the user {user} in order to obtain the token")
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
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/users?username={username}"
        headers = {
            "Authorization": f"Bearer {admin_access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            users = response.json()
            return users[0].get('id')

    def _set_required_actions(self, required_actions, admin_token, user_id):
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}"
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
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}"
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

    def add_user(self, username, password, first_name="", last_name="", email=""):
        """Add a new user to Keycloak"""
        logger.info(f"Adding new user '{username}' to Keycloak")
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/users"
        headers = {
            "Authorization": f"Bearer {self.admin_access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "username": username,
            "enabled": True,
            "emailVerified": True,
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "requiredActions": [],
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False
            }]
        }
        response = requests.post(url, json=payload, headers=headers, verify=False)
        if response.status_code != 201:
            raise Exception(f"Failed to add user '{username}' (status {response.status_code}): {response.text}")
        logger.info(f"User '{username}' added successfully")

    def user_exists(self, username):
        """Check if a user exists in Keycloak"""
        logger.info(f"Checking if user '{username}' exists in Keycloak")
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/users?username={username}"
        headers = {
            "Authorization": f"Bearer {self.admin_access_token}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to check user existence (status {response.status_code}): {response.text}")
        users = response.json()
        exists = len(users) > 0
        logger.info(f"User '{username}' exists: {exists}")
        return exists

    def assign_client_role(self, username, role_name, client_name):
        """Assign a client role to a user"""
        logger.info(f"Assigning client role '{role_name}' ({client_name}) to user '{username}'")
        admin_token = self.admin_access_token
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/clients?clientId={client_name}"
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200 or not response.json():
            raise Exception(f"Failed to find client '{client_name}' (status {response.status_code})")
        client_uuid = response.json()[0]["id"]
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/clients/{client_uuid}/roles/{role_name}"
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code != 200:
            raise Exception(f"Failed to find role '{role_name}' in client '{client_name}' (status {response.status_code})")
        role = response.json()
        user_id = self._get_user_id(admin_token, username)
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}/role-mappings/clients/{client_uuid}"
        response = requests.post(url, json=[role], headers=headers, verify=False)
        if response.status_code != 204:
            raise Exception(f"Failed to assign role '{role_name}' to user '{username}' (status {response.status_code}): {response.text}")
        logger.info(f"Role '{role_name}' ({client_name}) assigned to user '{username}'")

    def delete_user(self, username):
        """Delete a user from Keycloak"""
        logger.info(f"Deleting user '{username}' from Keycloak")
        admin_token = self.admin_access_token
        user_id = self._get_user_id(admin_token, username)
        url = f"{self.erag_auth_domain}/admin/realms/{VITE_KEYCLOAK_REALM}/users/{user_id}"
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        response = requests.delete(url, headers=headers, verify=False)
        if response.status_code != 204:
            raise Exception(f"Failed to delete user '{username}' (status {response.status_code}): {response.text}")
        logger.info(f"User '{username}' deleted successfully")
