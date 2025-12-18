# --- Nutanix NAI metrics auto-fix (Python with Kubernetes library) ---
#
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
#
# Description:
# This script uses the Kubernetes Python client to fix Prometheus monitoring for Nutanix AI (NAI).
# It finds key services, applies the correct labels, and ensures ServiceMonitors
# can discover them across all namespaces.
#
# Requires a valid kubeconfig file configured for cluster access

import sys
import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# --- Configuration ---
# Namespace where the NAI ServiceMonitors are located.
NAI_SYSTEM_NAMESPACE = "nai-system"
# Namespace where inference engine services (NIM, TGI, vLLM) are located.
NAI_ADMIN_NAMESPACE = "nai-admin"


def patch_servicemonitor_namespace(custom_api: client.CustomObjectsApi, name: str):
    """Patches a ServiceMonitor to scan all namespaces using Kubernetes API."""
    print(f"ℹ️  Attempting to patch ServiceMonitor/{name}...")
    patch = {"spec": {"namespaceSelector": {"any": True}}}
    try:
        custom_api.patch_namespaced_custom_object(
            group="monitoring.coreos.com",
            version="v1",
            namespace=NAI_SYSTEM_NAMESPACE,
            plural="servicemonitors",
            name=name,
            body=patch
        )
        print(f"✅ Patched ServiceMonitor/{name} to scan all namespaces.")
    except ApiException as e:
        print(f"❌ Error patching ServiceMonitor/{name}: {e.reason}")


def label_service(core_api: client.CoreV1Api, service: dict, labels: dict):
    """Applies a set of labels to a given service using Kubernetes API."""
    ns = service['metadata']['namespace']
    name = service['metadata']['name']
    
    print(f"ℹ️  Attempting to label service {ns}/{name}...")
    
    try:
        # Get current service to preserve existing labels
        current_service = core_api.read_namespaced_service(name=name, namespace=ns)
        if current_service.metadata.labels is None:
            current_service.metadata.labels = {}
        
        # Update with new labels
        current_service.metadata.labels.update(labels)
        
        # Patch the service
        core_api.patch_namespaced_service(
            name=name,
            namespace=ns,
            body=current_service
        )
        label_log_str = ", ".join([f"{k}={v}" for k, v in labels.items()])
        print(f"✅ Labeled service {ns}/{name} with: {label_log_str}")
    except ApiException as e:
        print(f"❌ Error labeling service {ns}/{name}: {e.reason}")


def ensure_port_name(core_api: client.CoreV1Api, service: dict, target_port: int, desired_name: str):
    """Ensures a service port has the correct name using Kubernetes API."""
    ns = service['metadata']['namespace']
    name = service['metadata']['name']
    
    ports = service.get('spec', {}).get('ports', [])
    if not ports:
        return

    for i, port in enumerate(ports):
        # target_port from JSON can be an int or a string
        if str(port.get('targetPort')) == str(target_port):
            if port.get('name') != desired_name:
                print(f"ℹ️  Renaming port on {ns}/{name} (targetPort={target_port}) to '{desired_name}'...")
                try:
                    # Get current service
                    current_service = core_api.read_namespaced_service(name=name, namespace=ns)
                    # Update the port name
                    current_service.spec.ports[i].name = desired_name
                    # Patch the service
                    core_api.patch_namespaced_service(
                        name=name,
                        namespace=ns,
                        body=current_service
                    )
                    print(f"✅ Renamed port on {ns}/{name}.")
                except ApiException as e:
                    print(f"❌ Error renaming port on {ns}/{name}: {e.reason}")
            else:
                print(f"✅ Port name on {ns}/{name} is already correct ('{desired_name}').")
            return
            
    print(f"ℹ️  Skipped port rename on {ns}/{name} (no port found with targetPort={target_port}).")


def main():
    """Main execution function."""
    print("✅ Verifying Kubernetes connection to the cluster...")
    try:
        config.load_kube_config()

        # Configure proxy if environment variables are set
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('HTTP_PROXY')
        if proxy:
            print(f"ℹ️  Found proxy configuration in environment: {proxy}")
            client_config = client.Configuration.get_default_copy()
            client_config.proxy = proxy
            client.Configuration.set_default(client_config)
            print("✅ Applied proxy settings to Kubernetes client.")

        core_api = client.CoreV1Api()
        custom_api = client.CustomObjectsApi()
        
        # Test connection
        print("ℹ️  Testing API access...")
        core_api.get_api_resources()
        print("✅ Successfully connected to Kubernetes cluster.")
    except Exception as e:
        print(f"❌ Could not connect to Kubernetes cluster: {e}")
        sys.exit(1)

    print("\n--- Step 1: Patching ServiceMonitors to be Cluster-Wide ---")
    monitors_to_patch = ['nai-gpu-monitor', 'nai-node-exporter-monitor', 'nai-iep-monitor']
    for sm_name in monitors_to_patch:
        patch_servicemonitor_namespace(custom_api, sm_name)

    print("\n--- Step 2: Fetching All Cluster Services ---")
    try:
        services_response = core_api.list_service_for_all_namespaces()
        all_services = [core_api.api_client.sanitize_for_serialization(svc) for svc in services_response.items]
        print(f"✅ Found {len(all_services)} services in the cluster.")
    except ApiException as e:
        print(f"❌ Error fetching services: {e.reason}")
        sys.exit(1)

    print("\n--- Step 3: Finding and Labeling DCGM Exporter ---")
    dcgm_candidates = [
        s for s in all_services if 'dcgm' in s['metadata']['name'] or
        any(p.get('port') == 9400 or p.get('targetPort') == 9400 for p in s.get('spec', {}).get('ports', []))
    ]
    if len(dcgm_candidates) == 1:
        label_service(core_api, dcgm_candidates[0], {'app': 'nvidia-dcgm-exporter'})
    elif len(dcgm_candidates) > 1:
        names = [f"{s['metadata']['namespace']}/{s['metadata']['name']}" for s in dcgm_candidates]
        print(f"⚠️  Found multiple DCGM-like services; not labeling automatically: {names}")
    else:
        print("⚠️  No DCGM-like service found (name contains 'dcgm' or uses port 9400).")

    print("\n--- Step 4: Finding and Labeling Node Exporter ---")
    node_exp_candidates = [
        s for s in all_services if 'node-exporter' in s['metadata']['name'] or
        any(p.get('port') == 9100 or p.get('targetPort') == 9100 for p in s.get('spec', {}).get('ports', []))
    ]
    if node_exp_candidates:
        pref_order = ['monitoring', 'kube-prometheus-stack', 'kube-system']
        node_exp_candidates.sort(key=lambda s: pref_order.index(s['metadata']['namespace']) if s['metadata']['namespace'] in pref_order else 99)
        chosen_node_svc = node_exp_candidates[0]
        
        labels_to_apply = {'app.kubernetes.io/name': 'prometheus-node-exporter', 'app.kubernetes.io/component': 'metrics'}
        label_service(core_api, chosen_node_svc, labels_to_apply)
        ensure_port_name(core_api, chosen_node_svc, target_port=9100, desired_name='http-metrics')
    else:
        print("⚠️  No node-exporter-like service found (name contains 'node-exporter' or uses port 9100).")

    # The logic for steps 5 and 6 remains the same, just operating on dictionaries.
    print("\n--- Step 5: Finding and Labeling IEP Service ---")
    iep_candidates = [
        s for s in all_services if ('nai' in s['metadata']['name'] or 'iep' in s['metadata']['name']) and
        any(p.get('port') == 8080 or p.get('targetPort') == 8080 for p in s.get('spec', {}).get('ports', []))
    ]
    if len(iep_candidates) == 1:
        label_service(core_api, iep_candidates[0], {'nai-monitoring': 'nai-prometheus'})
    else:
        print("⚠️  No IEP-like service found (name contains 'nai'/'iep' and uses port 8080).")

    print(f"\n--- Step 6: Finding and Labeling Endpoints in '{NAI_ADMIN_NAMESPACE}' ---")
    endpoints_to_find = [{'engine': 'nim', 'port': 8000}, {'engine': 'tgi', 'port': 8080}, {'engine': 'vllm', 'port': 8080}]
    nai_admin_services = [s for s in all_services if s['metadata']['namespace'] == NAI_ADMIN_NAMESPACE]

    for endpoint in endpoints_to_find:
        engine, port = endpoint['engine'], endpoint['port']
        candidates = [
            s for s in nai_admin_services if engine in s['metadata']['name'] or
            any(p.get('port') == port or p.get('targetPort') == port for p in s.get('spec', {}).get('ports', []))
        ]
        if len(candidates) == 1:
            label_service(core_api, candidates[0], {'endpoint.iep.nai.nutanix.com/engine': engine})
        elif len(candidates) > 1:
            names = [s['metadata']['name'] for s in candidates]
            print(f"⚠️  Multiple '{engine}' candidates in '{NAI_ADMIN_NAMESPACE}'; not labeling automatically: {names}")
        else:
            print(f"⚠️  No clear '{engine}' endpoint service found in '{NAI_ADMIN_NAMESPACE}'.")
            
    print("\n======================= Done =======================")
    print("Next steps:")
    print("1. Check the Prometheus UI to see if the new targets are appearing.")
    print("   You can port-forward to it using a command like:")
    print("   kubectl -n monitoring port-forward svc/kube-prometheus-stack-prometheus 9090:9090")
    print("\n2. If any warnings above mentioned multiple candidates, you may need to label the correct service manually.")

if __name__ == "__main__":
    main()
