#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest
import kr8s

from tests.e2e.helpers.istio_helper import ConnectionType
from tests.e2e.validation.buildcfg import cfg

# Skip all tests if istio is not deployed
istio_enabled = cfg.get("istio", {}).get("enabled")
if not istio_enabled:
    pytestmark = pytest.mark.skip(reason="Istio is not deployed")

logger = logging.getLogger(__name__)


# List of endpoints to test
http_endpoints = [
    # Ingress endpoints - allowed from anywhere
    # "ingress-nginx-controller.ingress-nginx.svc.cluster.local:80",
    # "ingress-nginx-controller-admission.ingress-nginx.svc.cluster.local:443",
    # # Rag-ui endpoints
    "ui-chart.rag-ui.svc.cluster.local:4173"
    # System endpoints
    # disabled because gmc needs to be open to connections from kube-apiserver
    # "gmc-controller.system.svc.cluster.local:9443"
]

chatqa_endpoints = [
    "embedding-svc.chatqa.svc.cluster.local:6000",
    "fgp-svc.chatqa.svc.cluster.local:6012",
    "input-scan-svc.chatqa.svc.cluster.local:8050",
    "llm-svc.chatqa.svc.cluster.local:9000",
    # Output guards disabled
    # "output-scan-svc.chatqa.svc.cluster.local:8060",
    "prompt-template-svc.chatqa.svc.cluster.local:7900",
    # "redis-vector-db.chatqa.svc.cluster.local:6379",
    "reranking-svc.chatqa.svc.cluster.local:8000",
    "retriever-svc.chatqa.svc.cluster.local:6620",
    "router-service.chatqa.svc.cluster.local:8080",
    "torchserve-reranking-svc.chatqa.svc.cluster.local:8090",
    "torchserve-embedding-svc.chatqa.svc.cluster.local:8090",
    # vllm endpoint name is different depending on the platform
    # "vllm-service-m.chatqa.svc.cluster.local:8000"
]
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "chatqa":
        http_endpoints.extend(chatqa_endpoints)

edp_endpoints = [
    "edp-text-extractor.edp.svc.cluster.local:9398",
    "edp-text-compression.edp.svc.cluster.local:9397",
    "edp-text-splitter.edp.svc.cluster.local:9399",
    "edp-ingestion.edp.svc.cluster.local:6120",
    "edp-backend.edp.svc.cluster.local:5000",
    "edp-celery.edp.svc.cluster.local:5000",
    "edp-flower.edp.svc.cluster.local:5555",
    "edp-minio.edp.svc.cluster.local:9000"
]
if cfg.get("edp", {}).get("enabled"):
    http_endpoints.extend(edp_endpoints)

fingerprint_endpoints = [
    "fingerprint-svc.fingerprint.svc.cluster.local:6012",
]
if cfg.get("fingerprint", {}).get("enabled"):
    http_endpoints.extend(fingerprint_endpoints)

docsum_endpoints = [
    "docsum-svc.docsum.svc.cluster.local:9001",
    "llm-svc.docsum.svc.cluster.local:9000",
    "router-service.docsum.svc.cluster.local:8080",
    "text-compression-svc.docsum.svc.cluster.local:9397",
    "text-extractor-svc.docsum.svc.cluster.local:9398",
    "text-splitter-svc.docsum.svc.cluster.local:9399"
]
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "docsum":
        http_endpoints.extend(docsum_endpoints)

telemetry_endpoints = [
    # # Monitoring-traces endpoints
    "otelcol-traces-collector.monitoring-traces.svc.cluster.local:4318",
    "otelcol-traces-collector-monitoring.monitoring-traces.svc.cluster.local:8888",
    "telemetry-traces-otel-operator.monitoring-traces.svc.cluster.local:8080",
    "telemetry-traces-otel-operator-webhook.monitoring-traces.svc.cluster.local:443",
    "telemetry-traces-tempo.monitoring-traces.svc.cluster.local:4318",
    # # Monitoring endpoints
    "alertmanager-operated.monitoring.svc.cluster.local:9094",
    "loki-canary.monitoring.svc.cluster.local:3500",
    "loki-memberlist.monitoring.svc.cluster.local:7946",
    "prometheus-operated.monitoring.svc.cluster.local:9090",
    "telemetry-grafana.monitoring.svc.cluster.local:80",
    "telemetry-kube-prometheus-alertmanager.monitoring.svc.cluster.local:8080",
    "telemetry-kube-prometheus-operator.monitoring.svc.cluster.local:443",
    "telemetry-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090",
    "telemetry-kube-state-metrics.monitoring.svc.cluster.local:8080",
    "telemetry-logs-loki.monitoring.svc.cluster.local:9095",
    "telemetry-logs-loki-chunks-cache.monitoring.svc.cluster.local:11211",
    "telemetry-logs-loki-gateway.monitoring.svc.cluster.local:80",
    "telemetry-logs-loki-results-cache.monitoring.svc.cluster.local:11211",
    "telemetry-logs-minio.monitoring.svc.cluster.local:9000",
    "telemetry-logs-minio-console.monitoring.svc.cluster.local:9001",
    "telemetry-logs-minio-svc.monitoring.svc.cluster.local:9000",
    # Node exporter access cannot be restricted
    # "telemetry-prometheus-node-exporter.monitoring.svc.cluster.local:9100",
    "telemetry-prometheus-redis-exporter.monitoring.svc.cluster.local:9121"
]
if cfg.get("telemetry", {}).get("enabled"):
    http_endpoints.extend(telemetry_endpoints)

redis_endpoints = [
    # gets populated within prepare_tests fixture
]

postgres_endpoints = [
    "keycloak-postgresql.auth.svc.cluster.local:5432"
]
if cfg.get("edp", {}).get("enabled"):
    postgres_endpoints.append("edp-postgresql.edp.svc.cluster.local:5432")


mongodb_endpoints = []
if cfg.get("fingerprint", {}).get("enabled"):
    mongodb_endpoints = ["fingerprint-mongodb.fingerprint.svc.cluster.local:27017"]

istio_test_data = {
    ConnectionType.HTTP: http_endpoints,
    ConnectionType.REDIS: redis_endpoints,
    ConnectionType.MONGODB: mongodb_endpoints,
    ConnectionType.POSTGRESQL: postgres_endpoints
}


def get_vector_db_endpoints():
    if not cfg.get("vector_databases", {}).get("enabled"):
        return []

    # Check for redis-cluster implementation first
    try:
        services = kr8s.get("services", "vdb-redis-cluster-headless", namespace="vdb")
        if len(services) == 1:
            service = services[0]
            logger.info("Found redis-cluster vector DB service: %s", service.name)
            return [f"{service.name}.vdb.svc.cluster.local:6379"]
    except (RuntimeError, ValueError, AttributeError):
        pass

    # Check for redis implementation
    try:
        services = kr8s.get("services", "vdb-redis-headless", namespace="vdb")
        if len(services) == 1:
            service = services[0]
            logger.info("Found redis vector DB service: %s", service.name)
            return [f"{service.name}.vdb.svc.cluster.local:6379"]
    except (RuntimeError, ValueError, AttributeError):
        pass

    raise RuntimeError("No vector database services found with expected names (vdb-redis-cluster or vdb-redis)")


def get_edp_redis_endpoints():
    if cfg.get("edp", {}).get("enabled"):
        return ["edp-redis-master.edp.svc.cluster.local:6379"]
    return []


@pytest.fixture(scope="module", autouse=True)
def prepare_tests(istio_helper):
    logger.info("============= Prepare Istio Authorization tests =====================")

    # Dynamically populate redis endpoints
    redis_endpoints.extend(get_edp_redis_endpoints())
    redis_endpoints.extend(get_vector_db_endpoints())

    istio_helper.create_namespace(inmesh=True)
    endpoints = {endpoint: connection_type for connection_type, endpoint_list in istio_test_data.items() for endpoint in endpoint_list}
    sample_endpoints = dict(list(endpoints.items())[:7])
    istio_helper.sample_log_timestamp_offsets()
    istio_helper.query_multiple_endpoints(dict(sample_endpoints))
    log_ts_offset = istio_helper.apply_log_timestamp_offsets()
    if log_ts_offset < 0:
        logger.warning("Detected negative time offset %s sec between kubernetes log and test host", log_ts_offset)
    else:
        logger.info("Detected time offset %s sec between kubernetes log and test host", log_ts_offset)
    istio_helper.delete_namespace()
    yield


class TestIstioInMesh:

    @pytest.fixture(autouse=True, scope="class")
    def cleanup(self, istio_helper):
        logger.info("============= TestIstioInMesh setup =====================")
        istio_helper.create_namespace(inmesh=True)
        yield
        istio_helper.delete_namespace()

    @pytest.mark.xfail(reason="Fix to be implemented")
    @allure.testcase("IEASG-T142")
    def test_authorization_gets_connections_blocked(self, istio_helper):
        endpoints = {endpoint: connection_type for connection_type, endpoint_list in istio_test_data.items() for endpoint in endpoint_list}
        connections_not_blocked = check_if_connections_blocked(istio_helper, endpoints)
        assert connections_not_blocked == []


class TestIstioOutOfMesh:

    @pytest.fixture(autouse=True, scope="class")
    def cleanup(self, istio_helper):
        logger.info("============= TestIstioOutOfMesh setup =====================")
        istio_helper.create_namespace(inmesh=False)
        yield
        istio_helper.delete_namespace()

    @allure.testcase("IEASG-T146")
    def test_authorization_gets_connections_blocked(self, istio_helper):
        endpoints = {endpoint: connection_type for connection_type, endpoint_list in istio_test_data.items() for endpoint in endpoint_list}
        connections_not_blocked = check_if_connections_blocked(istio_helper, endpoints)
        assert connections_not_blocked == []


def check_if_connections_blocked(istio_helper, endpoints: dict[str, ConnectionType]):
    return istio_helper.query_multiple_endpoints(endpoints)
