#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import allure
import logging
import pytest
from helpers.istio_helper import ConnectionType

logger = logging.getLogger(__name__)

# List of endpoints to test
http_endpoints = [
    # ChatQA endpoints
    "embedding-svc.chatqa.svc.cluster.local:6000",
    "fgp-svc.chatqa.svc.cluster.local:6012",
    "input-scan-svc.chatqa.svc.cluster.local:8050",
    "llm-svc.chatqa.svc.cluster.local:9000",
    "output-scan-svc.chatqa.svc.cluster.local:8060",
    "prompt-template-svc.chatqa.svc.cluster.local:7900",
    "redis-vector-db.chatqa.svc.cluster.local:6379",
    "reranking-svc.chatqa.svc.cluster.local:8000",
    "retriever-svc.chatqa.svc.cluster.local:6620",
    "router-service.chatqa.svc.cluster.local:8080",
    "tei-reranking-svc.chatqa.svc.cluster.local:80",
    "torchserve-embedding-svc.chatqa.svc.cluster.local:8090",
    # vllm endpoint name is different depending on the platform
    # "vllm-service-m.chatqa.svc.cluster.local:8000",
    # Dataprep endpoints
    "dataprep-svc.dataprep.svc.cluster.local:9399",
    "embedding-svc.dataprep.svc.cluster.local:6000",
    "ingestion-svc.dataprep.svc.cluster.local:6120",
    "router-service.dataprep.svc.cluster.local:8080",
    # EDP endpoints
    "edp-backend.edp.svc.cluster.local:5000",
    "edp-celery.edp.svc.cluster.local:5000",
    "edp-flower.edp.svc.cluster.local:5555",
    "edp-minio.edp.svc.cluster.local:9000",
    # Fingerprint endpoints
    "fingerprint-svc.fingerprint.svc.cluster.local:6012",
    # Ingress endpoints - allowed from anywhere
    # "ingress-nginx-controller.ingress-nginx.svc.cluster.local:80",
    # "ingress-nginx-controller-admission.ingress-nginx.svc.cluster.local:443",
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
    "telemetry-prometheus-redis-exporter.monitoring.svc.cluster.local:9121",
    # # Rag-ui endpoints
    "ui-chart.rag-ui.svc.cluster.local:4173",
    # System endpoints
    "gmc-contoller.system.svc.cluster.local:9443",
]

redis_endpoints = [
    "redis-vector-db.chatqa.svc.cluster.local:6379",
    "edp-redis-master.edp.svc.cluster.local:6379"
]

postgres_endpoints = [
    "keycloak-postgresql.auth.svc.cluster.local:5432",
    "edp-postgresql.edp.svc.cluster.local:5432",
]

mongodb_endpoints = [
    "fingerprint-mongodb.fingerprint.svc.cluster.local:27017",
]

istio_test_data = {
    ConnectionType.HTTP: http_endpoints,
    ConnectionType.REDIS: redis_endpoints,
    ConnectionType.MONGODB: mongodb_endpoints,
    ConnectionType.POSTGRESQL: postgres_endpoints
}


class TestIstioInMesh:

    @pytest.fixture(autouse=True, scope="class")
    def cleanup(self, istio_helper):
        logger.info("============= TestIstioInMesh setup =====================")
        istio_helper.create_namespace(inmesh=True)
        yield
        istio_helper.delete_namespace()

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
