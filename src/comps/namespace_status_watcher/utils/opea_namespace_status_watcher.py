# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Dict
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from comps import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEANamespaceStatusWatcher:
    """OPEA Namespace Status Watcher utility class for querying Kubernetes resources."""

    def __init__(self, target_namespace: str):
        """
        Initialize the OPEANamespaceStatusWatcher instance.

        Args:
            target_namespace: The Kubernetes namespace to monitor

        Raises:
            ConnectionError: If unable to connect to Kubernetes cluster
        """
        self._target_namespace = target_namespace
        self._init_kubernetes_client()
        logger.info(f"OPEANamespaceStatusWatcher initialized for namespace: {self._target_namespace}")

    def _init_kubernetes_client(self):
        """Initialize Kubernetes client."""
        try:
            config.load_incluster_config()
            logger.info("Loaded in-cluster Kubernetes configuration")
        except config.ConfigException:
            try:
                config.load_kube_config()
                logger.info("Loaded kubeconfig configuration")
            except config.ConfigException as e:
                logger.error(f"Failed to load Kubernetes configuration: {e}")
                raise ConnectionError(f"Failed to connect to Kubernetes cluster: {e}")

    @staticmethod
    def _format_deployment_status(deployment) -> str:
        """Format deployment status with replica counts and conditions."""
        status = deployment.status
        ready = "Ready" if status.ready_replicas == status.replicas else "Not ready"

        replicas_info = (
            f"Replicas: {status.replicas or 0} desired | "
            f"{status.ready_replicas or 0} ready | "
            f"{status.available_replicas or 0} available | "
            f"{status.updated_replicas or 0} updated"
        )

        conditions_info = ""
        if status.conditions:
            conditions_info = "\n" + "\n".join([
                f"  Type: {c.type}\n"
                f"  Status: {c.status}\n"
                f"  Reason: {c.reason}\n"
                f"  Message: {c.message}"
                for c in status.conditions
            ])

        return f"{ready}; {replicas_info}{conditions_info}\n"

    @staticmethod
    def _format_statefulset_status(sts) -> str:
        """Format statefulset status with replica counts."""
        status = sts.status
        ready = "Ready" if status.ready_replicas == status.replicas else "Not ready"

        replicas_info = (
            f"Replicas: {status.replicas or 0} desired | "
            f"{status.ready_replicas or 0} ready | "
            f"{status.current_replicas or 0} current"
        )

        return f"{ready}; {replicas_info}\n"

    def get_namespace_resources(self) -> Dict[str, str]:
        """
        Query all resources in the namespace and return annotations dict.

        Returns:
            Dict with resource annotations in GMC format
        """
        annotations = {}

        try:
            # Initialize API clients
            core_v1 = client.CoreV1Api()
            apps_v1 = client.AppsV1Api()
            autoscaling_v2 = client.AutoscalingV2Api()

            # Query ConfigMaps
            try:
                config_maps = core_v1.list_namespaced_config_map(namespace=self._target_namespace)
                for cm in config_maps.items:
                    key = f"ConfigMap:v1:{cm.metadata.name}:{self._target_namespace}"
                    annotations[key] = "provisioned"
            except ApiException as e:
                logger.warning(f"Failed to list ConfigMaps: {e}")

            # Query Services
            try:
                services = core_v1.list_namespaced_service(namespace=self._target_namespace)
                for svc in services.items:
                    key = f"Service:v1:{svc.metadata.name}:{self._target_namespace}"
                    # Build service URL
                    port = svc.spec.ports[0].port if svc.spec.ports else "unknown"
                    path = svc.metadata.annotations.get("service.path", "") if svc.metadata.annotations else ""
                    url = f"http://{svc.metadata.name}.{self._target_namespace}.svc:{port}{path}"
                    annotations[key] = url
            except ApiException as e:
                logger.warning(f"Failed to list Services: {e}")

            # Query Deployments
            try:
                deployments = apps_v1.list_namespaced_deployment(namespace=self._target_namespace)
                for deploy in deployments.items:
                    key = f"Deployment:apps/v1:{deploy.metadata.name}:{self._target_namespace}"
                    annotations[key] = self._format_deployment_status(deploy)
            except ApiException as e:
                logger.warning(f"Failed to list Deployments: {e}")

            # Query StatefulSets
            try:
                statefulsets = apps_v1.list_namespaced_stateful_set(namespace=self._target_namespace)
                for sts in statefulsets.items:
                    key = f"StatefulSet:apps/v1:{sts.metadata.name}:{self._target_namespace}"
                    annotations[key] = self._format_statefulset_status(sts)
            except ApiException as e:
                logger.warning(f"Failed to list StatefulSets: {e}")

            # Query ServiceAccounts
            try:
                service_accounts = core_v1.list_namespaced_service_account(namespace=self._target_namespace)
                for sa in service_accounts.items:
                    # Skip default service account
                    if sa.metadata.name != "default":
                        key = f"ServiceAccount:v1:{sa.metadata.name}:{self._target_namespace}"
                        annotations[key] = "provisioned"
            except ApiException as e:
                logger.warning(f"Failed to list ServiceAccounts: {e}")

            # Query PersistentVolumeClaims
            try:
                pvcs = core_v1.list_namespaced_persistent_volume_claim(namespace=self._target_namespace)
                for pvc in pvcs.items:
                    key = f"PersistentVolumeClaim:v1:{pvc.metadata.name}:{self._target_namespace}"
                    annotations[key] = "provisioned"
            except ApiException as e:
                logger.warning(f"Failed to list PersistentVolumeClaims: {e}")

            # Query HorizontalPodAutoscalers
            try:
                hpas = autoscaling_v2.list_namespaced_horizontal_pod_autoscaler(namespace=self._target_namespace)
                for hpa in hpas.items:
                    key = f"HorizontalPodAutoscaler:autoscaling/v2:{hpa.metadata.name}:{self._target_namespace}"
                    annotations[key] = "provisioned"
            except ApiException as e:
                logger.warning(f"Failed to list HorizontalPodAutoscalers: {e}")

        except Exception as e:
            logger.error(f"Error querying namespace resources: {e}")
            raise

        return annotations

    @staticmethod
    def compute_overall_status(annotations: Dict[str, str]) -> tuple[str, str, str]:
        """
        Compute overall status based on resource annotations.

        Returns:
            Tuple of (status, condition_type, condition_message)
        """
        failed_deployments = []
        failed_statefulsets = []
        total_deployments = 0
        ready_deployments = 0

        for key, value in annotations.items():
            if key.startswith("Deployment:"):
                total_deployments += 1
                if value.startswith("Ready;"):
                    ready_deployments += 1
                else:
                    resource_name = key.split(":")[2]
                    failed_deployments.append(resource_name)

            elif key.startswith("StatefulSet:"):
                if not value.startswith("Ready;"):
                    resource_name = key.split(":")[2]
                    failed_statefulsets.append(resource_name)

        # Determine overall status
        if failed_deployments or failed_statefulsets:
            status = "Failed"
            condition_type = "Failed"
            failed_resources = failed_deployments + failed_statefulsets
            condition_message = f"Some resources are not ready: {', '.join(failed_resources)}"
        elif total_deployments > 0 and ready_deployments == total_deployments:
            status = "Ready"
            condition_type = "Success"
            condition_message = f"All {total_deployments} deployments are ready"
        else:
            status = "Unknown"
            condition_type = "Unknown"
            condition_message = "Unable to determine status"

        return status, condition_type, condition_message
