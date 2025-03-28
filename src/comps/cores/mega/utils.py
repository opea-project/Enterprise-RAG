# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import ipaddress
import multiprocessing
import os
import random
from socket import AF_INET, SOCK_STREAM, socket
from typing import List, Union
import logging
import requests
from .logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_token")

def is_port_free(host: str, port: int) -> bool:
    """Check if a given port on a host is free.

    :param host: The host to check.
    :param port: The port to check.
    :return: True if the port is free, False otherwise.
    """
    with socket(AF_INET, SOCK_STREAM) as session:
        return session.connect_ex((host, port)) != 0


def check_ports_availability(host: Union[str, List[str]], port: Union[int, List[int]]) -> bool:
    """Check if one or more ports on one or more hosts are free.

    :param host: The host(s) to check.
    :param port: The port(s) to check.
    :return: True if all ports on all hosts are free, False otherwise.
    """
    hosts = [host] if isinstance(host, str) else host
    ports = [port] if isinstance(port, int) else port

    return all(is_port_free(h, p) for h in hosts for p in ports)


def get_public_ip(timeout: float = 0.3):
    """Return the public IP address of the gateway in the public network."""
    import urllib.request

    def _get_public_ip(url):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as fp: # nosec B310
                _ip = fp.read().decode().strip()
                return _ip
        except Exception as e:
            logging.warning(f"got exception: {e} \ncan not get public ip from {url}")


    ip_lookup_services = [
        "https://api.ipify.org",
        "https://ident.me",
        "https://checkip.amazonaws.com/",
    ]

    for _, url in enumerate(ip_lookup_services):
        ip = _get_public_ip(url)
        if ip:
            return ip


def typename(obj):
    """Get the typename of object."""
    if not isinstance(obj, type):
        obj = obj.__class__
    try:
        return f"{obj.__module__}.{obj.__name__}"
    except AttributeError:
        return str(obj)


def get_event(obj) -> multiprocessing.Event:
    if isinstance(obj, multiprocessing.Process) or isinstance(obj, multiprocessing.context.ForkProcess):
        return multiprocessing.Event()
    elif isinstance(obj, multiprocessing.context.SpawnProcess):
        return multiprocessing.get_context("spawn").Event()
    else:
        raise TypeError(f'{obj} is not an instance of "multiprocessing.Process"')


def in_docker():
    """Checks if the current process is running inside Docker."""
    path = "/proc/self/cgroup"
    if os.path.exists("/.dockerenv"):
        return True
    if os.path.isfile(path):
        with open(path,  mode='r', encoding="utf-8") as file:
            return any("docker" in line for line in file)
    return False


def host_is_local(hostname):
    """Check if hostname is point to localhost."""
    import socket

    fqn = socket.getfqdn(hostname)
    if fqn in ("localhost", "0.0.0.0") or hostname == "0.0.0.0":
        return True

    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


assigned_ports = set()
unassigned_ports = []
DEFAULT_MIN_PORT = 49153
MAX_PORT = 65535


def reset_ports():
    def _get_unassigned_ports():
        # if we are running out of ports, lower default minimum port
        if MAX_PORT - DEFAULT_MIN_PORT - len(assigned_ports) < 100:
            min_port = int(os.environ.get("JINA_RANDOM_PORT_MIN", "16384"))
        else:
            min_port = int(os.environ.get("JINA_RANDOM_PORT_MIN", str(DEFAULT_MIN_PORT)))
        max_port = int(os.environ.get("JINA_RANDOM_PORT_MAX", str(MAX_PORT)))
        return set(range(min_port, max_port + 1)) - set(assigned_ports)

    unassigned_ports.clear()
    assigned_ports.clear()
    unassigned_ports.extend(_get_unassigned_ports())
    random.shuffle(unassigned_ports)

def get_access_token(token_url: str, client_id: str, client_secret: str) -> str:
    """Get access token using OAuth client credentials flow."""
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.post(token_url, data=data, headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the response status code is 4xx/5xx
        logger.info("Successfully retrieved access token")
        token_info = response.json()
        return token_info.get('access_token', '')
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to retrieve access token: {e}")
        return ''

class SafeContextManager:
    """This context manager ensures that the `__exit__` method of the
    sub context is called, even when there is an Exception in the
    `__init__` method."""

    def __init__(self, context_to_manage):
        self.context_to_manage = context_to_manage

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.context_to_manage.__exit__(exc_type, exc_val, exc_tb)
