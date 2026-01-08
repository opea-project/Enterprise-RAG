#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import base64
import logging

import kr8s

logger = logging.getLogger(__name__)


class K8sHelper:

    def retrieve_admin_password(self, secret_name, namespace):
        """Retrieve the admin password from the keycloak secret"""
        logger.debug(f"Retrieving the admin password from the '{secret_name}' secret")
        secrets = kr8s.get("secrets", namespace=namespace)
        for secret in secrets:
            if secret.name == secret_name:
                # Extract and decode the base64-encoded password
                encoded_password = secret.data.get("admin-password")
                return base64.b64decode(encoded_password).decode().strip()

    def list_namespaces(self):
        """List all namespaces in the Kubernetes cluster"""
        namespaces = kr8s.get("namespaces")
        return [ns.name for ns in namespaces]

    def list_pods(self, namespace):
        """List all pods in the specified namespace"""
        pods = kr8s.get("pods", namespace=namespace)
        return [pod.name for pod in pods]

    def get_pods_by_label(self, namespace, label_selector):
        """Get a list of kr8s Pod objects matching a label selector in a namespace"""
        logger.debug(f"Getting pods with label selector '{label_selector}' in namespace '{namespace}'")
        return kr8s.get("pods", namespace=namespace, label_selector=label_selector)

    def exec_in_pod(self, pod, command):
        """Execute a command in a pod's container"""
        logger.debug(f"Executing command '{command}' in pod '{pod.name}'")
        try:
            return pod.exec(command)
        except Exception as e:
            logger.error(f"Failed to execute command in pod '{pod.name}': {e}")
            raise  # Re-raise the exception to fail the test
