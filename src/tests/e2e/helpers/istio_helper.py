#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from functools import reduce
import logging
import operator
import re
import threading
import time
from typing import Optional
import uuid
from collections import defaultdict
from dataclasses import dataclass
import datetime
from enum import Enum, IntEnum, auto

import kr8s
from kr8s._exceptions import ExecError
from kr8s.objects import Namespace, Pod, objects_from_files

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
state_logger = logger.getChild("state")


ISTIO_NS_PREFIX = "istio-test-"
ERROR_LOG_TIMEOUT_SEC = 20
MAX_RUNNING_QUERIES = 10  # how many query pods can be actively tracked at the same time
DEF_LOOP_INTERVAL_SEC = 0.25
MAX_RETRY_COUNT = 3 # number of retries allowed for query after first TIMEOUT or ERROR state
RETRY_BACKOFF_SEC = 2 # time before query in RETRY state is restored to NEW state
FILES_DIR = "e2e/files"
DEF_LOG_TS_MARGIN_SEC = 0.5 # default timestamp offset to add to log statements for correction


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
        # timestamp the query got state QueryState.READY
        self.ready_start: float = None
        if self.state is None:
            self.set_state(QueryState.NEW)

    def set_state(self, state: QueryState, deadline_sec: float = None, deadline_state: QueryState = QueryState.TIMEOUT):
        self.last_state = self.state
        self.state = state
        state_logger.debug("query %s: %s => %s", self, (self.last_state.name if self.last_state else 'None'), self.state.name)
        self.state_start = time.time()
        if state == QueryState.READY:
            self.ready_start = self.state_start
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
        yaml_file_path = f"{FILES_DIR}/istio_peer_auth.yaml"
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
            self.image = "bitnamilegacy/postgresql:16.3.0-debian-12-r23"
        elif connection_type == ConnectionType.MONGODB:
            self.image = "mongo:5.0.6"
        elif connection_type == ConnectionType.HTTP:
            self.image = "python:3.11"
        else:
            logger.info(f"unset connection type defaults to {ConnectionType.HTTP}")
            self.image = "python:3.11"
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


class DebugPod:

    def __init__(self):
        self.pod = None

    def create(self):
        pod_spec = {
            "metadata": {
                "name": f"inotify-check-{str(uuid.uuid4())[-8:]}",
                "namespace": "default",
            },
            "spec": {
                "hostPID": True,
                "containers": [
                    {
                        "name": "inotify-check",
                        "image": "ubuntu:22.04",
                        "command": ["/bin/sh", "-c"],
                        "args": ['trap exit TERM; sleep 300 & wait'],
                        "securityContext": {"privileged": True},
                        "volumeMounts": [
                            {"name": "proc", "mountPath": "/host/proc"},
                            {"name": "sys", "mountPath": "/host/sys"},
                        ],
                    }
                ],
                "volumes": [
                    {"name": "proc", "hostPath": {"path": "/proc"}},
                    {"name": "sys", "hostPath": {"path": "/sys"}},
                ],
                "restartPolicy": "Never",
            },
        }
        self.pod = Pod(pod_spec)
        self.pod.create()

    def delete(self):
        self.pod.delete()
        self.pod = None

    def pod_exec(self, command):
        command_list = command.split(" ") if type(command) is str else command
        try:
            output = self.pod.exec(command_list)
            return output.stdout.decode()
        except ExecError:
            return None

    def read_inotify_info(self):
        inotify_info_raw = self.pod_exec(
            [
                "bash",
                "-c",
                'printf "user_root_inst_num=%s total_inst_num=%s max_inst_num=%s\\n" $(find /proc/*/fd -lname anon_inode:inotify -user root 2>/dev/null |wc -l) $(find /proc/*/fd -lname anon_inode:inotify 2>/dev/null | wc -l) $(sysctl -n fs.inotify.max_user_instances)',
            ]
        )
        inotify_info = {
            kv[0]: int(kv[1])
            for kv in map(lambda n: n.split("="), inotify_info_raw.split())
            if kv[1].isdigit()
        }
        return inotify_info, inotify_info_raw


class LogWatcher(threading.Thread):

    INITIALIZE_WAIT_TIME_SEC = 10
    INITIALIZE_INTERVAL_SEC = 3
    INITIALIZE_RETRIES = 3

    def __init__(self):
        super().__init__(daemon=True)
        self.lock: threading.RLock = threading.RLock()
        self.stop_flag = False
        self.watch_patterns: list[str] = []
        self.buffer: list[str] = []
        self._initialize: Optional[bool] = None
        self.first_read_ts: Optional[str] = None
        self.last_read_ts: Optional[str] = None
        self.exit_ts: Optional[str] = None

    @staticmethod
    def current_datetime():
        return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00","Z")

    def stop(self):
        with self.lock:
            self.stop_flag = True

    def snapshot(self):
        with self.lock:
            snapshot = [*self.buffer]
            return snapshot

    def initialized(self) -> Optional[bool]:
        with self.lock:
            return self._initialized

    def get_lifecycle_tstamps(self):
        with self.lock:
            return dict(first_read_ts = self.first_read_ts, last_read_ts = self.last_read_ts, exit_ts = self.exit_ts)

    def run(self):
        ztunnel_namespace = "istio-system"
        ztunnel_label_selector = "app=ztunnel"

        # Fetch all ztunnel pods
        initialize_stop = time.time() + LogWatcher.INITIALIZE_WAIT_TIME_SEC
        initialize_retries = 0
        while time.time() < initialize_stop and initialize_retries < LogWatcher.INITIALIZE_RETRIES:
            pods = kr8s.get("pods", namespace=ztunnel_namespace, label_selector=ztunnel_label_selector)
            if len(pods) >= 1:
                break
            initialize_retries += 1
            time.sleep(LogWatcher.INITIALIZE_INTERVAL_SEC)
        if len(pods) < 1:
            with self.lock:
                self._initialized = False
            logger.warning("Couldn't access ztunnel pod for monitoring, LogWatcher not initialized; Logs won't be available")
            return
        ztunnel_pod : Pod = pods[0]
        with self.lock:
            self._initialized = True
        # we don't want logs from the start of service, but need to request 60 seconds to verify logging works (btw. 0 will break the kr8s client)
        for log_line in ztunnel_pod.logs(since_seconds=60, follow=True):
            with self.lock:
                if self.first_read_ts is None:
                    self.first_read_ts = LogWatcher.current_datetime()
                self.last_read_ts = LogWatcher.current_datetime()
                if self.stop_flag:
                    self.exit_ts = LogWatcher.current_datetime()
                    return
                self.buffer.append(log_line)
        with self.lock:
            self.exit_ts = LogWatcher.current_datetime()


class QueryWorkloadLookup:
    """Lookup workloads targeted by service endpoint.
    """

    endpoint_ptrn = re.compile(r"^(?P<service>[^.]+)\.(?P<namespace>[^.]+)\.svc.+")
    cache_ttl_sec = 60

    def __init__(self):
        self.workload_cache: dict[str, tuple[float, list[str]]] = dict()
        self.endpoints_without_istio: set[str] = set()

    def clear(self):
        self.workload_cache.clear()
        self.endpoints_without_istio.clear()

    def lookup_workloads_for_endpoint(self, endpoint: str) -> list[str]:
        if (workloads_with_expiry := self.workload_cache.get(endpoint, None)) is not None:
            workloads, expiry_ts = workloads_with_expiry
            if time.time() < expiry_ts:
                return workloads
            self.workload_cache.pop(endpoint)
        if (m := self.endpoint_ptrn.match(endpoint)) is not None:
            service, namespace = m.group("service"), m.group("namespace")
            services = kr8s.get("services", service, namespace=namespace)
            if len(services) == 0:
                workloads = []
            else:
                ready_pods = services[0].ready_pods()
                workloads = [pod.name for pod in ready_pods]
                try:
                    annotation_keys = [pod.annotations.keys() for pod in ready_pods]
                    if 'ambient.istio.io/redirection' in annotation_keys:
                        self.endpoints_without_istio.add(endpoint)
                except Exception as e:
                    logger.warning(f"Couldn't identify annotations on pod running for {endpoint}: {e}")
            if workloads == []:
                logger.warning(f"Found no workloads for service {service}.{namespace}")
            else:
                logger.debug("[monitoring] Found workloads for service %s.%s: %s", service, namespace, workloads)
            self.workload_cache[endpoint] = (workloads, time.time() + self.cache_ttl_sec)
            return workloads
        return []

@dataclass
class LogCheck:
    result: bool
    details: str


class IstioHelper:

    dst_workload_ptrn = re.compile(r'\Wdst.workload="(?P<workload>[^"]+)"')
    test_query_ts_ptrn = re.compile(r'ts:(?P<ts>[0-9]+\.[0-9]*)\n')
    query_blocked_ptrn = re.compile(r'\berror\s+access\s+connection\s+complete\b')
    query_unblocked_ptrn = re.compile(r'\binfo\s+access\s+connection\s+complete\b')


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
        self.first_log_ts: float = None
        self.workloads_lookup: QueryWorkloadLookup = QueryWorkloadLookup()
        self._sample_log_timestamp_offsets = False
        self._timestamp_offsets: list[float] = []
        self._log_timestamp_fix: float = DEF_LOG_TS_MARGIN_SEC

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
        logger.info(f"Executing query {query.query_key}@{query.state_start} using pod {pod}, pod_ip: {pod.pod_ip}")
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
        i = 0
        valid_src_count = 0
        while i < len(self.log_snapshot):
            log_line = self.log_snapshot[i]
            try:
                logline_ts = datetime.datetime.fromisoformat(log_line.split(maxsplit=1)[0]).timestamp()
                if self.first_log_ts is None:
                    self.first_log_ts = logline_ts
                    logger.debug("[monitoring] Observed log timestamps start at %s", self.first_log_ts)
            except ValueError:
                logline_ts = None

            # we're only interested in log statements that confirm blocking queries or letting them through
            query_blocked_check = self.query_blocked_ptrn.search(log_line) is not None
            query_unblocked_check = not query_blocked_check and self.query_unblocked_ptrn.search(log_line) is not None
            if not query_blocked_check and not query_unblocked_check:
                # delete log irrelevant to queries from snapshot
                del self.log_snapshot[i]
                continue
            # validate the access - first it must be coming from correct source - the query_pod
            valid_source_check = LogCheck(query_pod.namespace_name in log_line and pod_addr_key in log_line, "")
            if not valid_source_check.result:
                i += 1
                continue
            valid_src_count += 1
            valid_dest_check = LogCheck(False, "")
            query_workloads = self.workloads_lookup.lookup_workloads_for_endpoint(query_key.endpoint)
            m = self.dst_workload_ptrn.search(log_line)
            if m is not None and m.group("workload") in query_workloads:
                valid_dest_check = LogCheck(True, "")
            elif m is None:
                valid_dest_check = LogCheck(False, "no workload in log line")
            elif query_workloads == []:
                valid_dest_check = LogCheck(False, "no workloads found for query endpoint")
            elif m.group("workload") not in query_workloads:
                valid_dest_check = LogCheck(False, f"workload {m.group("workload")} not in valid workloads for query {query_workloads}")
            valid_logline_ts_check = LogCheck(False, "")
            if logline_ts is None:
                valid_logline_ts_check = LogCheck(False, "no timestamp in log line")
            else:
                ts_delta = logline_ts - query.ready_start
                valid_logline_ts_check = LogCheck(ts_delta + self._log_timestamp_fix > 0, f"timestamp delta: {ts_delta} corrected to {ts_delta + self._log_timestamp_fix}")
            # decide if query was verified
            if valid_dest_check.result and (valid_logline_ts_check.result or self._sample_log_timestamp_offsets):
                logger.debug("Query %s verified %s with log line: '%s'; timestamp_check: %s", query_key, ("blocked" if query_blocked_check else "unblocked"), log_line, valid_logline_ts_check)
                if query_blocked_check:
                    query.set_state(QueryState.BLOCKED)
                else:
                    query.set_state(QueryState.UNBLOCKED)
                # record offset between query execution start and the timestamp in logs
                if logline_ts is not None and self._sample_log_timestamp_offsets:
                    self._timestamp_offsets.append(logline_ts - query.ready_start)
                # remove line that was taken so that it won't confuse further queries
                del self.log_snapshot[i]
                return
            i += 1

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
                    logger.debug(f"Pod is ready for query {query.query_key}; pod_ip is {pod.pod_ip}")
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

    # Start sampling timestamp offset between log statements and query execution start
    def sample_log_timestamp_offsets(self):
        self._sample_log_timestamp_offsets = True
        self._timestamp_offsets.clear()

    # Finish sampling timestamp offsets and apply timestamp correction fix
    def apply_log_timestamp_offsets(self) -> float:
        self._sample_log_timestamp_offsets = False
        # rule out case of negative time offset
        if len(self._timestamp_offsets) > 2:
            sorted_offsets = sorted(self._timestamp_offsets)[1:-1]
            avg_offset = reduce(operator.add, sorted_offsets) / len(sorted_offsets)
            if avg_offset < 0:
                self._log_timestamp_fix = -1 * avg_offset + DEF_LOG_TS_MARGIN_SEC
            else:
                self._log_timestamp_fix = DEF_LOG_TS_MARGIN_SEC
            return avg_offset
        return 0

    def query_multiple_endpoints(self, endpoints: dict[str, ConnectionType]):
        debug_pod = DebugPod()
        debug_pod.create()
        # make sure if there are enough inotify watches, otherwise getting logs won't be possible
        try:
            inotify_info, _ = debug_pod.read_inotify_info()
            if "user_root_inst_num" in inotify_info and "max_inst_num" in inotify_info:
                user_root_inst_num = inotify_info["user_root_inst_num"]
                max_inst_num = inotify_info["max_inst_num"]
                # observed number of required inotify watches: 2 * the number of running queries + 1 for LogWatcher
                needed_inst_num = 2 * MAX_RUNNING_QUERIES + 1 + dict(arbitrary=8)["arbitrary"]
                if user_root_inst_num + needed_inst_num > max_inst_num:
                    logger.warning(f"Too low limit of inotify max_user_instances might result in query TIMEOUTs; need at least fs.inotify_max_user_instances={user_root_inst_num + needed_inst_num}")
        finally:
            debug_pod.delete()
        connections_not_blocked : list[str] = []
        self.query_list.clear()
        self.log_snapshot.clear()
        log_watcher: LogWatcher = LogWatcher()
        log_watcher.start()
        self.workloads_lookup.clear()
        self.endpoint_retries.clear()
        mon_endpoint_retries: dict[str, int] = defaultdict(int)
        mon_unblocked_endpoints: list[str] = []
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
                        mon_endpoint_retries[query_key.endpoint] += 1
                        self.retire_query(query)
                        logger.info(f"Will retry query at {query_key.connection_type.value} endpoint {query_key.endpoint}")
                        query.set_state(QueryState.RETRY, RETRY_BACKOFF_SEC, QueryState.NEW)
                        self.query_list.append(self.query_list.pop(i))
                        continue
                if query.state in [QueryState.BLOCKED, QueryState.UNBLOCKED, QueryState.TIMEOUT, QueryState.ERROR]:
                    if query.state != QueryState.BLOCKED:
                        connections_not_blocked.append(query_key.endpoint)
                        if query.state == QueryState.UNBLOCKED:
                            mon_unblocked_endpoints.append(query_key.endpoint)
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
        last_snapshot = log_watcher.snapshot()
        logger.info("[monitoring] Collected number of log statements: %s; timestamps: %s", (len(last_snapshot) or '(ZERO)'), log_watcher.get_lifecycle_tstamps())
        if not log_watcher.initialized():
            logger.warning("Log watcher did NOT initialize")
        logger.info("[monitoring] UNBLOCKED endpoints: %s", sorted(mon_unblocked_endpoints))
        logger.info("[monitoring] endpoint retries (max is %d): %s", MAX_RETRY_COUNT, dict(sorted(mon_endpoint_retries.items(), key=lambda k: (-k[1], k[0]))))
        if self.workloads_lookup.endpoints_without_istio:
            logger.warning("Found endpoints without applied Istio: %s", self.workloads_lookup.endpoints_without_istio)
        return connections_not_blocked

    def build_test_command(self, query_key: ServiceQueryKey):
        match query_key.connection_type:
            case ConnectionType.HTTP:
                command = ['sh', '-c', 'echo "ts:$(date +%s.%N)"; echo; '+ f"curl -s -o /dev/null -w '%{{http_code}}' {query_key.endpoint} >/dev/null 2>&1 || true"]
            case ConnectionType.REDIS:
                redis_port = query_key.endpoint.split(":")[-1]
                host = query_key.endpoint.split(":")[0]
                command = ['sh', '-c', 'echo "ts:$(date +%s.%N)"; echo; '+ f"redis-cli -h {host} -p {redis_port} QUIT >/dev/null 2>&1 || true"]
            case ConnectionType.POSTGRESQL:
                port = query_key.endpoint.split(":")[-1]
                host = query_key.endpoint.split(":")[0]
                command = ['sh', '-c', 'echo "ts:$(date +%s.%N)"; echo; '+ f"psql -h {host} -p {port} -U postgres >/dev/null 2>&1 || true"]
            case ConnectionType.MONGODB:
                host = query_key.endpoint.split(":")[0]
                port = query_key.endpoint.split(":")[-1]
                command = ['sh', '-c', 'echo "ts:$(date +%s.%N)"; echo; '+ f"mongo --host {host} --port {port} --eval 'db.runCommand({{connectionStatus: 1}})' >/dev/null 2>&1 || true"]
            case _:
                logger.info(f"Error: unsupported connection type {query_key.connection_type} to {query_key.endpoint}")
                return None
        return command

    def run_query_test(self, query_key: ServiceQueryKey, pod: TestPod):
        logger.info(f"Making {query_key.connection_type} request @{time.time()} to endpoint: {query_key.endpoint} from pod {pod}")
        command = self.build_test_command(query_key)
        ts = None
        if command is not None:
            output = pod.pod_exec(command)
            if output is not None and (m := IstioHelper.test_query_ts_ptrn.search(output)) is not None:
                ts = m.group("ts")
            logger.debug("[monitoring] Executed %s request @%s to endpoint: %s from pod %s", query_key.connection_type, ts, query_key.endpoint, pod)
            return True
        return False
