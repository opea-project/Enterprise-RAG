#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Enterprise RAG Debug Tool
Collects comprehensive diagnostic information from a Kubernetes cluster including pod logs,
resource descriptions, version info, and deployment configuration (with sensitive data redacted).
"""

import subprocess # nosec B404
import os
import datetime
import tarfile
import json
import re
import argparse
import logging
import sys
import shutil
import yaml


class EnterpriseRAGDebugger:
    # Line width for error/warning messages
    LINE_WIDTH = 60

    # Resource types collected in kubectl_get, kubectl_getyaml and kubectl_describe
    KUBECTL_RESOURCES = [
        # Workloads (explicit instead of 'all')
        "pods", "daemonsets", "deployments", "replicasets", "statefulsets", "jobs", "cronjobs",
        # Networking
        "services", "ingress", "networkpolicies",
        # Storage
        "pv", "pvc", "sc",
        # Config & access
        "sa",
        # Cluster
        "nodes", "namespaces", "events", "noderesourcetopology",
        # Trident
        "tridentbackendconfigs",
    ]

    # Resources collected only via 'kubectl get' (no yaml/describe) due to sensitive data
    SENSITIVE_RESOURCES = ["cm", "secret"]

    # Keys considered sensitive - values will be redacted
    SENSITIVE_KEYS = re.compile(
        r'(token|password|passwd|secret|key|credential|auth|api_key|apikey|access_key|private_key)',
        re.IGNORECASE
    )

    # Keys that match SENSITIVE_KEYS pattern but should NOT be redacted
    SENSITIVE_KEYS_EXCLUSIONS = re.compile(
        r'\b(keycloak|maxNewTokens|vault_password_file)\b',
        re.IGNORECASE
    )

    def __init__(self, output_dir="debug_bundle", config_path=None):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_path = f"{output_dir}_{self.timestamp}"
        self.logs_path = os.path.join(self.base_path, "kubectl_logs")
        self.kubectl_get_path = os.path.join(self.base_path, "kubectl_get")
        self.kubectl_getyaml_path = os.path.join(self.base_path, "kubectl_getyaml")
        self.kubectl_describe_path = os.path.join(self.base_path, "kubectl_describe")
        self.config_path = config_path
        self.config_data = None
        self.kubeconfig_path = None
        self.logger = None

    def setup_logging(self):
        """Setup logging to both console and file."""
        # Create base directory first
        os.makedirs(self.base_path, exist_ok=True)

        # Setup logger
        self.logger = logging.getLogger("EnterpriseRAGDebugger")
        self.logger.setLevel(logging.DEBUG)

        # Console handler with custom formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)

        # File handler - save script output
        log_file = os.path.join(self.base_path, "debug_tool_execution.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

        self.logger.info(f"[*] Logging initialized. Output saved to: {log_file}")

    def run_command(self, cmd, ignore_errors=False):
        """Helper to execute shell commands and return output."""
        try:
            # Set up environment with kubeconfig if available
            env = os.environ.copy()
            if self.kubeconfig_path:
                env["KUBECONFIG"] = self.kubeconfig_path

            result = subprocess.run(
                cmd, shell=True, check=True, capture_output=True, text=True, env=env
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if ignore_errors:
                self.logger.debug(f"  [!] Command failed (ignored): {cmd} -> {e.stderr.strip()}")
                return None
            self.logger.error(f"  [!] Command failed: {cmd}")
            self.logger.error(f"  [!] Error: {e.stderr.strip()}")
            return None

    def _log_error(self, message):
        """Log an error message surrounded by separator lines."""
        self.logger.error("=" * self.LINE_WIDTH)
        self.logger.error(message)
        self.logger.error("=" * self.LINE_WIDTH)

    def _log_section(self, message):
        """Log a message surrounded by separator lines."""
        self.logger.info("=" * self.LINE_WIDTH)
        self.logger.info(message)
        self.logger.info("=" * self.LINE_WIDTH)

    def _load_config_file(self, config_path):
        """Load and parse a YAML config file.
        
        Args:
            config_path: Path to the config file (can be relative or absolute)
            
        Returns:
            Parsed config data as dict, or None if file doesn't exist
            
        Raises:
            SystemExit: If file doesn't exist or is invalid YAML
        """
        config_path = os.path.abspath(config_path)

        if not os.path.exists(config_path):
            self._log_error(f"  [!] CONFIG ERROR: Config file not found: {config_path}\n  [!] Provide a valid path via --config /path/to/config.yaml")
            sys.exit(1)

        try:
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            if not config_data or not isinstance(config_data, dict):
                self._log_error("  [!] CONFIG ERROR: Config file is empty, invalid YAML, or not a valid dictionary")
                sys.exit(1)

            return config_data

        except yaml.YAMLError as e:
            self._log_error(f"  [!] CONFIG ERROR: Failed to parse config file as YAML: {e}")
            sys.exit(1)
        except Exception as e:
            self._log_error(f"  [!] CONFIG ERROR: Unexpected error reading config file: {e}")
            sys.exit(1)

    def collect_config(self):
        """Load config file, extract kubeconfig path, and save redacted config."""
        if not self.config_path:
            self.logger.info("[*] No config file provided (--config not specified), skipping")
            return

        self.logger.info(f"[*] Loading config file: {os.path.abspath(self.config_path)}")

        self.config_data = self._load_config_file(self.config_path)

        # Extract and validate kubeconfig
        kubeconfig = self.config_data.get("kubeconfig", None)

        if not kubeconfig:
            self._log_error("  [!] CONFIG ERROR: 'kubeconfig' variable not found in config file\n  [!] Please add 'kubeconfig: /path/to/kubeconfig' to your config file")
            sys.exit(1)

        # Resolve relative paths relative to the config file directory
        if not os.path.isabs(kubeconfig):
            config_dir = os.path.dirname(os.path.abspath(self.config_path))
            kubeconfig = os.path.join(config_dir, kubeconfig)

        kubeconfig = os.path.abspath(kubeconfig)

        if not os.path.exists(kubeconfig):
            self._log_error(f"  [!] CONFIG ERROR: kubeconfig file not found at: {kubeconfig}\n  [!] Configured path in {os.path.abspath(self.config_path)}: {self.config_data.get('kubeconfig')}\n  [!] Please verify the 'kubeconfig' path in your configuration file")
            sys.exit(1)

        self.kubeconfig_path = kubeconfig
        self.logger.info(f"  [+] kubeconfig resolved to: {self.kubeconfig_path}")

        # Save redacted config
        try:
            redacted = self._redact_sensitive(self.config_data)

            out_file = os.path.join(self.base_path, "config_redacted.yaml")
            with open(out_file, "w") as f:
                yaml.dump(redacted, f, default_flow_style=False, sort_keys=False)

            self.logger.info("  [+] Saved redacted config to config_redacted.yaml")
        except Exception as e:
            self.logger.error(f"  [!] Unexpected error processing config file: {e}")

    def setup_workspace(self):
        """Create directory structure for the diagnostic bundle."""
        os.makedirs(self.logs_path, exist_ok=True)
        os.makedirs(self.kubectl_get_path, exist_ok=True)
        os.makedirs(self.kubectl_getyaml_path, exist_ok=True)
        os.makedirs(self.kubectl_describe_path, exist_ok=True)
        self.logger.info(f"[*] Workspace created: {self.base_path}")

    def get_all_namespaces(self):
        """Get list of all namespaces in the cluster."""
        cmd = "kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'"
        output = self.run_command(cmd)
        return output.split() if output else []

    def get_nodes(self):
        """Get list of all node names in the cluster."""
        cmd = "kubectl get nodes -o jsonpath='{.items[*].metadata.name}'"
        output = self.run_command(cmd)
        return output.split() if output else []

    def get_pods(self, namespace=None):
        """Get list of all pod names, optionally filtered by namespace."""
        if namespace:
            cmd = f"kubectl get pods -n {namespace} -o jsonpath='{{.items[*].metadata.name}}'"
        else:
            cmd = "kubectl get pods --all-namespaces -o json"
            result = self.run_command(cmd)
            if result:
                data = json.loads(result)
                return [(item['metadata']['namespace'], item['metadata']['name']) for item in data['items']]
            return []

        output = self.run_command(cmd)
        return [(namespace, pod) for pod in output.split()] if output else []

    def collect_pod_logs(self):
        """Collect current and previous logs for all pods across all namespaces."""
        self.logger.info("[*] Collecting pod logs from all namespaces...")
        pods = self.get_pods()

        for namespace, pod in pods:
            ns_log_path = os.path.join(self.logs_path, namespace)
            os.makedirs(ns_log_path, exist_ok=True)

            # Collecting current logs
            self._save_pod_logs(namespace, pod, ns_log_path, is_previous=False)

            # AC: Restart logs and crash loop backoff (collecting previous logs)
            self._save_pod_logs(namespace, pod, ns_log_path, is_previous=True)

    def _save_pod_logs(self, namespace, pod_name, log_path, is_previous=False):
        suffix = "previous" if is_previous else "current"
        prev_flag = "--previous" if is_previous else ""

        cmd = f"kubectl logs {pod_name} -n {namespace} {prev_flag} --all-containers"

        try:
            # Set up environment with kubeconfig if available
            env = os.environ.copy()
            if self.kubeconfig_path:
                env["KUBECONFIG"] = self.kubeconfig_path

            process = subprocess.run(cmd, shell=True, capture_output=True, env=env)
            if process.returncode == 0 and len(process.stdout) > 0:
                filename = f"{pod_name}_{suffix}.log"
                full_path = os.path.join(log_path, filename)

                with open(full_path, "wb") as f:
                    f.write(process.stdout)

                log_size = len(process.stdout)
                self.logger.info(f"  [+] Saved {namespace}/{filename} ({log_size / 1024:.2f} KB)")
            elif process.returncode != 0:
                if is_previous:
                    # Expected - pod may have never been restarted
                    pass
                else:
                    self.logger.warning(f"  [!] Failed to collect current logs for {namespace}/{pod_name}: {process.stderr.decode().strip()}")
        except Exception as e:
            self.logger.error(f"  [!] Unexpected error collecting logs for {namespace}/{pod_name}: {e}")

    def collect_kubectl_get(self):
        """Collect 'kubectl get -o wide' output for each resource type into separate files."""
        self.logger.info("[*] Collecting kubectl get (table format) per resource type...")
        all_resources = self.KUBECTL_RESOURCES + self.SENSITIVE_RESOURCES

        for resource in all_resources:
            output = self.run_command(f"kubectl get {resource} -A -o wide", ignore_errors=True)
            if output:
                resource_file = os.path.join(self.kubectl_get_path, f"{resource}.txt")
                with open(resource_file, "w") as f:
                    f.write(output)
                self.logger.info(f"  [+] Saved kubectl get {resource}")
            else:
                self.logger.warning(f"  [!] No output for kubectl get {resource} - skipping")

    def collect_kubectl_getyaml(self):
        """Collect 'kubectl get -o yaml' output for each resource type into separate files."""
        self.logger.info("[*] Collecting kubectl get -o yaml per resource type...")

        for resource in self.KUBECTL_RESOURCES:
            output = self.run_command(f"kubectl get {resource} -A -o yaml", ignore_errors=True)
            if output:
                resource_file = os.path.join(self.kubectl_getyaml_path, f"{resource}.txt")
                with open(resource_file, "w") as f:
                    f.write(output)
                self.logger.info(f"  [+] Saved kubectl get -o yaml {resource}")
            else:
                self.logger.warning(f"  [!] No output for kubectl get -o yaml {resource} - skipping")

    def collect_kubectl_describe(self):
        """Collect 'kubectl describe' output for each resource type into separate files."""
        self.logger.info("[*] Collecting kubectl describe per resource type...")

        for resource in self.KUBECTL_RESOURCES:
            output = self.run_command(f"kubectl describe {resource} -A", ignore_errors=True)
            if output:
                resource_file = os.path.join(self.kubectl_describe_path, f"{resource}.txt")
                with open(resource_file, "w") as f:
                    f.write(output)
                self.logger.info(f"  [+] Saved kubectl describe {resource}")
            else:
                self.logger.warning(f"  [!] No output for kubectl describe {resource} - skipping")

    def _redact_sensitive(self, data):
        """Recursively redact sensitive values in a dict/list structure."""
        if isinstance(data, dict):
            return {
                k: "<REDACTED>" if (
                    self.SENSITIVE_KEYS.search(k)
                    and not self.SENSITIVE_KEYS_EXCLUSIONS.search(k)
                    and v
                ) else self._redact_sensitive(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._redact_sensitive(item) for item in data]
        return data

    def collect_topology_preview(self):
        """Run ansible-playbook topology-preview and save the output."""
        self.logger.info("[*] Collecting topology preview...")

        if not self.config_path:
            self.logger.warning("  [!] No config file provided (--config), skipping topology preview")
            return

        config_path = os.path.abspath(self.config_path)
        if not os.path.exists(config_path):
            self.logger.warning(f"  [!] Config file not found: {config_path}, skipping topology preview")
            return

        # Playbook is in deployment/playbooks/ relative to this script (tools/)
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        deployment_dir = os.path.normpath(os.path.join(tools_dir, ".."))
        playbook_path = os.path.join(deployment_dir, "playbooks", "application.yaml")

        if not os.path.exists(playbook_path):
            self.logger.warning(f"  [!] Playbook not found: {playbook_path}, skipping topology preview")
            return

        cmd = (
            f"ansible-playbook {playbook_path} "
            f"--tags topology-preview "
            f"-e @{config_path}"
        )

        self.logger.info(f"  [*] Running: {cmd}")

        try:
            # Inherit current environment and apply kubeconfig
            env = os.environ.copy()
            env["K8S_AUTH_VERIFY_SSL"] = "false"
            if self.kubeconfig_path:
                env["KUBECONFIG"] = self.kubeconfig_path

            process = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                cwd=deployment_dir, env=env
            )
            output = ""
            if process.stdout:
                output += process.stdout
            if process.stderr:
                output += "\n--- STDERR ---\n" + process.stderr

            if output.strip():
                out_file = os.path.join(self.base_path, "topology_preview.txt")
                with open(out_file, "w") as f:
                    f.write(output)
                self.logger.info("  [+] Saved topology preview output")
            else:
                self.logger.warning("  [!] Topology preview produced no output")

            if process.returncode != 0:
                self.logger.warning(f"  [!] Topology preview playbook exited with code {process.returncode}")
        except Exception as e:
            self.logger.error(f"  [!] Failed to run topology preview: {e}")

    def create_summary_report(self):
        """Generate SUMMARY.json."""
        self.logger.info("[*] Generating summary report...")

        summary = {
            "collection_info": {
                "timestamp": self.timestamp,
                "collection_date": datetime.datetime.now().isoformat(),
            },
            "namespaces": self.get_all_namespaces(),
            "total_pods": len(self.get_pods()),
            "node_count": len(self.get_nodes()),
        }

        summary_file = os.path.join(self.base_path, "SUMMARY.json")
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)

        self.logger.info("  [+] Summary report created")

        # Copy debug_tool.md into the bundle
        docs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
        debug_tool_md = os.path.join(docs_dir, "debug_tool.md")
        if os.path.exists(debug_tool_md):
            shutil.copy(debug_tool_md, os.path.join(self.base_path, "debug_tool.md"))
            self.logger.info("  [+] debug_tool.md copied into bundle")
        else:
            self.logger.warning(f"  [!] debug_tool.md not found at {debug_tool_md}, skipping")

    def create_archive(self):
        """Package the debug bundle into a compressed tar.gz archive."""
        self.logger.info("[*] Creating compressed archive...")
        archive_name = f"{self.base_path}.tar.gz"
        with tarfile.open(archive_name, "w:gz") as tar:
            tar.add(self.base_path, arcname=os.path.basename(self.base_path))

        # Calculate size
        size_mb = os.path.getsize(archive_name) / (1024 * 1024)
        self.logger.info(f"[*] Final bundle: {archive_name} ({size_mb:.2f} MB)")
        return archive_name

    def check_prerequisites(self):
        """Check that kubectl is available and properly configured with kubeconfig."""
        self.logger.info("[*] Checking prerequisites...")

        # Check if kubectl is installed
        result = subprocess.run("kubectl version --client", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            self._log_error("  [!] PREREQUISITE ERROR: kubectl is not installed or not in PATH.\n  [!] Please install kubectl: https://kubernetes.io/docs/tasks/tools/")
            sys.exit(1)

        # Check if kubeconfig is available and cluster is reachable
        env = os.environ.copy()
        if self.kubeconfig_path:
            env["KUBECONFIG"] = self.kubeconfig_path

        result = subprocess.run("kubectl cluster-info", shell=True, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            error_lines = ["  [!] PREREQUISITE ERROR: kubectl is not configured or cluster is unreachable."]
            if self.kubeconfig_path:
                error_lines.append(f"  [!] kubeconfig: {self.kubeconfig_path}")
                error_lines.append("  [!] Please verify the kubeconfig file is valid and accessible")
            else:
                error_lines.append("  [!] Ensure one of the following is set up:")
                error_lines.append("  [!]   - ~/.kube/config exists with valid cluster credentials")
                error_lines.append("  [!]   - KUBECONFIG environment variable points to a valid kubeconfig file")
                error_lines.append("  [!]   - Provide --config with 'kubeconfig' variable defined")
            error_lines.append(f"  [!] kubectl error: {result.stderr.strip()}")
            self._log_error("\n".join(error_lines))
            sys.exit(1)

        self.logger.info("  [+] kubectl is configured and cluster is reachable")

    def run(self):
        """Execute all debug collection steps and produce the final archive."""
        self.setup_logging()

        self._log_section("Enterprise RAG Debug Tool")

        self.setup_workspace()
        self.collect_config()
        self.check_prerequisites()
        self.collect_topology_preview()
        self.collect_pod_logs()
        self.collect_kubectl_get()
        self.collect_kubectl_getyaml()
        self.collect_kubectl_describe()
        self.create_summary_report()
        archive = self.create_archive()

        self._log_section("Debug collection complete!")
        self.logger.info(f"Archive: {archive}")
        self.logger.info("=" * self.LINE_WIDTH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enterprise RAG Debug Tool - Collect comprehensive diagnostic information"
    )
    parser.add_argument(
        "--output-dir",
        default="debug_bundle",
        help="Output directory for debug bundle (default: debug_bundle)"
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="PATH",
        help="Path to deployment config.yaml (optional). Must contain 'kubeconfig' variable. Sensitive values will be redacted."
    )

    args = parser.parse_args()

    debugger = EnterpriseRAGDebugger(
        output_dir=args.output_dir,
        config_path=args.config,
    )
    debugger.run()
