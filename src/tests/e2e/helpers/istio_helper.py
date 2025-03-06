#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import logging
import re
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, IntEnum, auto

import kr8s
from kr8s._exceptions import ExecError
from kr8s.objects import Namespace, Pod, objects_from_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
state_logger = logger.getChild("state")


ISTIO_NS_PREFIX = "istio-test-"
ERROR_LOG_TIMEOUT_SEC = 20
MAX_RUNNING_QUERIES = 8 # how many query pods can be actively tracked at the same time
DEF_LOOP_INTERVAL_SEC = 0.5
MAX_RETRY_COUNT = 2 # number of retries allowed for query after first TIMEOUT or ERROR state
RETRY_BACKOFF_SEC = 2 # time before query in RETRY state is restored to NEW state


class ConnectionType(Enum):
    HTTP = "http"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    REDIS = "redis"


class QueryState(IntEnum):
    NEW = auto()
    RETRY= auto()
    SELECTED = auto()
    PREPARING = auto()
    READY = auto()
    EXECUTED = auto()
    # final states
    TIMEOUT = auto()
    BLOCKED = auto()
    UNBLOCKED = auto()
    ERROR = auto() # command execution failed

    def is_selected(self):
        return self not in (QueryState.NEW, QueryState.RETRY)


@dataclass(frozen=True)
class ServiceQueryKey:
    connection_type: ConnectionType
    endpoint: str


class ServiceQuery():

    def __init__(self, connection_type: ConnectionType, endpoint: str, state: QueryState = None, state_start: float = None, deadline: float = None, deadline_state: QueryState = None):
        self.query_key = ServiceQueryKey(connection_type, endpoint)
        self.state: QueryState = state
        self.state_start: float = state_start
        self.deadline: float = deadline
        self.deadline_state: QueryState = deadline_state
        self.last_state: QueryState = None
        if self.state is None:
            self.set_state(QueryState.NEW)

    def set_state(self, state: QueryState, deadline_sec: float = None, deadline_state: QueryState = QueryState.TIMEOUT):
        self.last_state = self.state
        self.state = state
        state_logger.debug("query %s: %s => %s", self, (self.last_state.name if self.last_state else 'None'), self.state.name)
        self.state_start = time.time()
        if deadline_sec is not None:
            self.deadline_state = deadline_state
            self.deadline = self.state_start + deadline_sec
        else:
            self.deadline = None

    def __str__(self):
        return f'{{{self.query_key.connection_type.name}, "{self.query_key.endpoint}", {self.state.name}}}'


class TestNamespace():

    def __init__(self, prefix=ISTIO_NS_PREFIX, inmesh=True):
        self.inmesh = inmesh
        self.namespace_name = f"{prefix}{'inmesh' if self.inmesh else 'outofmesh'}-{str(uuid.uuid4())[:-8]}"

    def create(self):
        namespace_manifest = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": self.namespace_name,
                "labels": {}
            }
        }
        if self.inmesh:
            namespace_manifest["metadata"]["labels"]["istio.io/dataplane-mode"] = "ambient"
        logger.info(f"Creating namespace: {self.namespace_name}, inmesh: {self.inmesh}")
        namespace = Namespace(namespace_manifest)
        namespace.create()
        if self.inmesh:
            self.enable_peer_authentication()

    def enable_peer_authentication(self):
        yaml_file_path = "files/istio_peer_auth.yaml"
        resources = objects_from_files(yaml_file_path)
        for resource in resources:
            resource.metadata.namespace = self.namespace_name
            resource.create()
        logger.info(f"Applied '{yaml_file_path}' to namespace '{self.namespace_name}'.")

    def count_pods(self):
        return len(list(kr8s.get("pods", namespace=self.namespace_name)))

    def delete(self):
        try:
            namespace = Namespace.get(self.namespace_name)
            logger.info(f"Deleting namespace: {self.namespace_name}")
            namespace.delete()

            logger.info(f"Waiting for namespace {self.namespace_name} to be deleted...")
            while True:
                try:
                    Namespace.get(self.namespace_name)
                    time.sleep(2)
                except Exception:
                    logger.info(f"Namespace {self.namespace_name} deleted successfully!")
                    break
        except Exception as e:
            logger.info(f"Error while deleting namespace {self.namespace_name}: {e}")


class TestPod():
    pod_ip_ptrn = re.compile(r"POD_IP=(?P<pod_ip>[0-9.]+);")

    def __init__(self, connection_type, namespace_name):
        self.connection_type = connection_type
        self.namespace_name = namespace_name
        if connection_type == ConnectionType.REDIS:
            self.image = "redis/redis-stack:7.2.0-v9"
        elif connection_type == ConnectionType.POSTGRESQL:
            self.image = "bitnami/postgresql:16.3.0-debian-12-r23"
        elif connection_type == ConnectionType.MONGODB:
            self.image = "mongo:5.0.6"
        elif connection_type == ConnectionType.HTTP:
            self.image = "curlimages/curl:8.11.1"
        else:
            logger.info(f"unset connection type defaults to {ConnectionType.HTTP}")
            self.image = "curlimages/curl:8.11.1"
        self.pod_name = f"test-{connection_type.value}-inst-{str(uuid.uuid4())[-8:]}"
        self.pod = None
        self.pod_ip = None
        self.ready = False

    def create(self):
        pod_spec = {
            "metadata": {"name": self.pod_name, "namespace": self.namespace_name},
            "spec": {
                "containers": [
                    {
                        "name": "test-container",
                        "image": self.image,
                        "command": ["/bin/sh", "-c"],
                        "args": ['trap exit TERM; sleep 300 & wait']
                    }
                ],
            },
        }
        self.pod = Pod(pod_spec)
        self.pod.create()
        # trigger once to warm up pod creation
        self.pod.ready()

    def delete(self):
        self.pod.delete()

    def get_ready(self):
        if self.ready:
            return True
        if self.pod.ready() is True:
            self.ready = True
            self.query_pod_ip()
            return True
        state_logger.debug("Pod %s not ready yet", self)
        return False

    def pod_exec(self, command):
        command_list = command.split(" ") if type(command) is str else command
        try:
            output = self.pod.exec(command_list)
            return output.stdout.decode()
        except ExecError:
            return None

    def query_pod_ip(self):
        pod_ip_output = self.pod_exec(['sh', '-c', 'printf "POD_IP=$(hostname -i);\\n"'])
        if pod_ip_output is not None and (m := TestPod.pod_ip_ptrn.match(pod_ip_output)) is not None:
            self.pod_ip = m.groupdict()["pod_ip"]
        else:
            self.pod_ip = None

    def __str__(self):
        return f"(name: {self.pod_name}, ip: {self.pod_ip}, namespace: {self.namespace_name})"


class LogWatcher(threading.Thread):

    def __init__(self):
        super().__init__(daemon=True)
        self.lock: threading.RLock = threading.RLock()
        self.stop_flag = False
        self.watch_patterns: list[str] = []
        self.buffer: list[str] = []

    def stop(self):
        with self.lock:
            self.stop_flag = True

    def snapshot(self):
        with self.lock:
            snapshot = [*self.buffer]
            return snapshot

    def run(self):
        ztunnel_namespace = "istio-system"
        ztunnel_label_selector = "app=ztunnel"

        # Fetch all ztunnel pods
        pods = kr8s.get("pods", namespace=ztunnel_namespace, label_selector=ztunnel_label_selector)
        ztunnel_pod : Pod = pods[0]
        for log_line in ztunnel_pod.logs(since_seconds=None, follow=True):
            with self.lock:
                if self.stop_flag:
                    return
                self.buffer.append(log_line)


class IstioHelper:

    def __init__(self):
        self.namespace_name = None
        self.pod = None
        self.pod_ip = None
        self.connection_type = None
        self.namespace = None
        self.max_running_queries = MAX_RUNNING_QUERIES
        self.loop_interval = DEF_LOOP_INTERVAL_SEC
        self.query_list: list[ServiceQuery] = []
        self.query_pods: dict[tuple[ConnectionType, str], TestPod] = {}
        self.log_snapshot: list[str] = []
        self.endpoint_retries: dict[str, int] = defaultdict(lambda: MAX_RETRY_COUNT)

    def create_namespace(self, inmesh=True):
        self.namespace = TestNamespace(inmesh=inmesh)
        self.namespace.create()

    def delete_namespace(self):
        self.namespace.delete()

    def prepare_query(self, query: ServiceQuery):
        pod: TestPod = TestPod(query.query_key.connection_type, self.namespace.namespace_name)
        self.query_pods[query.query_key] = pod
        pod.create()

    def execute_query(self, query: ServiceQuery):
        pod = self.query_pods[query.query_key]
        logger.debug(f"Executing query {query.query_key} using pod {pod}")
        if not self.run_query_test(query.query_key, pod):
            logger.info(f"Couldn't execute command for query {query.query_key}")
            query.set_state(QueryState.ERROR)

    def verify_query_blocked(self, query: ServiceQuery):
        query_key = query.query_key
        query_pod = self.query_pods[query.query_key]
        pod_ip = query_pod.pod_ip
        if pod_ip is None:
            # maybe another time
            return
        pod_addr_key = f"src.addr={pod_ip}:"
        for log_line in self.log_snapshot:
            if "connection complete" not in log_line:
                continue
            if query_pod.namespace_name in log_line and pod_addr_key in log_line:
                if "error" in log_line:
                    logger.debug("Query %s verified blocked with log line: '%s'", query_key, log_line)
                    query.set_state(QueryState.BLOCKED)
                    return
                if "info" in log_line and "error" not in log_line:
                    logger.debug("Query %s detected unblocked with log line: '%s'", query_key, log_line)
                    query.set_state(QueryState.UNBLOCKED)
                    return

    def retire_query(self, query: ServiceQuery):
        # release resources related to query
        query_key = query.query_key
        logger.info(f"Query at {query_key.connection_type.value} endpoint {query_key.endpoint} result: {query.state.name}")
        test_pod = self.query_pods.pop(query_key)
        test_pod.delete()

    def handle_query_state_deadline(self, query: ServiceQuery):
        if query.deadline is not None and query.deadline_state is not None:
            if time.time() > query.deadline:
                query.set_state(query.deadline_state)
                return True
        return False

    def process_query(self, query: ServiceQuery):
        start_state = query.state
        # test if query has changed state due to timeout
        if self.handle_query_state_deadline(query):
            return
        match start_state:
            case QueryState.SELECTED:
                self.prepare_query(query)
                query.set_state(QueryState.PREPARING)
            case QueryState.PREPARING:
                pod = self.query_pods[query.query_key]
                if pod.get_ready():
                    logger.info(f"Pod is ready for query {query.query_key}; pod_ip is {pod.pod_ip}")
                    query.set_state(QueryState.READY)
            case QueryState.READY:
                self.execute_query(query)
                if query.state == start_state: # unchanged by method
                    query.set_state(QueryState.EXECUTED, ERROR_LOG_TIMEOUT_SEC)
            case QueryState.EXECUTED:
                self.verify_query_blocked(query)
            case QueryState.NEW|QueryState.RETRY:
                # handled in query loop
                return
            case _:
                logger.info(f"Unhandled query state: {query.state}")

    def query_endpoints(self, connection_type: ConnectionType, endpoints: list[str]):
        self.query_multiple_endpoints({e: connection_type for e in endpoints})

    def query_multiple_endpoints(self, endpoints: dict[str, ConnectionType]):
        connections_not_blocked : list[str] = []
        self.query_list.clear()
        self.log_snapshot.clear()
        log_watcher: LogWatcher = LogWatcher()
        log_watcher.start()
        self.endpoint_retries.clear()
        for endpoint, connection_type in endpoints.items():
            self.query_list.append(ServiceQuery(connection_type, endpoint))
        while self.query_list:
            self.log_snapshot = log_watcher.snapshot()
            i = 0
            while i < len(self.query_list):
                query = self.query_list[i]
                query_key = query.query_key
                self.process_query(query)
                if query.state in [QueryState.ERROR, QueryState.TIMEOUT]:
                    # retry query
                    if self.endpoint_retries[query_key.endpoint] > 0:
                        self.endpoint_retries[query_key.endpoint] -= 1
                        self.retire_query(query)
                        logger.info(f"Will retry query at {query_key.connection_type.value} endpoint {query_key.endpoint}")
                        query.set_state(QueryState.RETRY, RETRY_BACKOFF_SEC, QueryState.NEW)
                        self.query_list.append(self.query_list.pop(i))
                        continue
                if query.state in [QueryState.BLOCKED, QueryState.UNBLOCKED, QueryState.TIMEOUT, QueryState.ERROR]:
                    if query.state != QueryState.BLOCKED:
                        connections_not_blocked.append(query.query_key.endpoint)
                    self.retire_query(query)
                    del self.query_list[i]
                else:
                    i += 1
            # select NEW queries for running
            num_running = max(sum(query.state.is_selected() for query in self.query_list), self.namespace.count_pods())
            num_to_select = (self.max_running_queries if self.max_running_queries > 0 else len(self.query_list)) - num_running
            i = 0
            while num_to_select > 0 and i < len(self.query_list):
                query = self.query_list[i]
                if query.state == QueryState.NEW:
                    query.set_state(QueryState.SELECTED)
                    num_to_select -= 1
                i += 1
            time.sleep(self.loop_interval)
        log_watcher.stop()
        return connections_not_blocked

    def build_test_command(self, query_key: ServiceQueryKey):
        match query_key.connection_type:
            case ConnectionType.HTTP:
                command = f"curl -s -o /dev/null -w '%{{http_code}}' {query_key.endpoint}"
            case ConnectionType.REDIS:
                redis_port = query_key.endpoint.split(":")[-1]
                host = query_key.endpoint.split(":")[0]
                command = f"redis-cli -h {host} -p {redis_port} QUIT"
            case ConnectionType.POSTGRESQL:
                port = query_key.endpoint.split(":")[-1]
                host = query_key.endpoint.split(":")[0]
                command = f'psql -h {host} -p {port} -U postgres'
            case ConnectionType.MONGODB:
                host = query_key.endpoint.split(":")[0]
                port = query_key.endpoint.split(":")[-1]
                command = f"mongo --host {host} --port {port} --eval 'db.runCommand({{connectionStatus: 1}})'"
            case _:
                logger.info(f"Error: unsupported connection type {query_key.connection_type} to {query_key.endpoint}")
                return None
        return command

    def run_query_test(self, query_key: ServiceQueryKey, pod: TestPod):
        logger.info(f"Making {query_key.connection_type} request to endpoint: {query_key.endpoint} from pod {pod}")
        command = self.build_test_command(query_key)
        if command is not None:
            pod.pod_exec(command)
            return True
        return False
