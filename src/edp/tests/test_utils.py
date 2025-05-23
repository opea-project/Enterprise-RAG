from unittest.mock import patch
from app.utils import get_http_client
from urllib3 import ProxyManager, PoolManager
import os

def test_hostname_with_http_proxy_with_no_proxy():
    # lower case proxy settings take precedence over upper case
    combinations = [
        {
            'hostname': 'http://example1.com',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': 'example.com'
            },
            'check_cert': True,
            'result_proxy_addr': 'proxy.example.com',
            'result_check_cert': 'CERT_REQUIRED',
            'result_class': ProxyManager
        },
        {
            'hostname': 'https://example2.com',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': 'example.com'
            },
            'check_cert': True,
            'result_proxy_addr': 'sproxy.example.com',
            'result_check_cert': 'CERT_REQUIRED',
            'result_class': ProxyManager
        },
        {
            'hostname': 'example3.com',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': ''
            },
            'check_cert': False,
            'result_proxy_addr': 'proxy.example.com',
            'result_check_cert': 'CERT_NONE',
            'result_class': ProxyManager
        },
        # now without any proxy
        {
            'hostname': 'example.com',
            'env': {
                'http_proxy': '',
                'https_proxy': '',
                'no_proxy': ''
            },
            'check_cert': True,
            'result_check_cert': 'CERT_REQUIRED',
            'result_class': PoolManager
        },
        {
            'hostname': 'example.com',
            'env': {
                'http_proxy': '',
                'https_proxy': '',
                'no_proxy': ''
            },
            'check_cert': False,
            'result_check_cert': 'CERT_NONE',
            'result_class': PoolManager
        },
        # proxy but with no_proxy set to the same domain
        {
            'hostname': 'http://example.com',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': 'example.com'
            },
            'check_cert': False,
            'result_check_cert': 'CERT_NONE',
            'result_class': PoolManager
        },
        {
            'hostname': 'https://example.com',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': 'example.com'
            },
            'check_cert': True,
            'result_check_cert': 'CERT_REQUIRED',
            'result_class': PoolManager
        },
        {
            'hostname': 'http://127.10.20.30',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': 'example.com'
            },
            'check_cert': True,
            'result_check_cert': 'CERT_REQUIRED',
            'result_class': ProxyManager,
            'result_proxy_addr': 'proxy.example.com',
        },
        {
            'hostname': 'https://127.10.20.30',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': 'example.com'
            },
            'check_cert': True,
            'result_check_cert': 'CERT_REQUIRED',
            'result_class': ProxyManager,
            'result_proxy_addr': 'sproxy.example.com',
        },
        {
            'hostname': 'http://127.10.20.30',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': '127.10.20.30'
            },
            'check_cert': True,
            'result_check_cert': 'CERT_REQUIRED',
            'result_class': PoolManager
        },
        # wildcard noproxy
        {
            'hostname': '127.10.20.30',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': '*'
            },
            'check_cert': False,
            'result_check_cert': 'CERT_NONE',
            'result_class': PoolManager
        },
        {
            'hostname': 'http://example.com',
            'env': {
                'http_proxy': 'http://proxy.example.com:8080',
                'https_proxy': 'http://sproxy.example.com:8080',
                'no_proxy': '*'
            },
            'check_cert': False,
            'result_check_cert': 'CERT_NONE',
            'result_class': PoolManager
        },
    ]

    for settings in combinations:
        with patch.dict(os.environ, settings['env'], clear=True):
            assert os.getenv('http_proxy') == settings['env']['http_proxy']
            client = get_http_client(endpoint=settings['hostname'], cert_check=settings['check_cert'])
            assert isinstance(client, settings['result_class']), f"Assertion failed for settings: {settings}"
            if isinstance(client, ProxyManager):
                assert client.proxy.host == settings['result_proxy_addr'], f"Assertion failed for settings: {settings}"
            assert client.connection_pool_kw.get('cert_reqs') == settings['result_check_cert'], f"Assertion failed for settings: {settings}"
