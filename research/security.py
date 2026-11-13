"""URL safety checks for fetch_page (protection against SSRF).

The model decides which URLs get downloaded. Once this runs as a web service, a user
(or a prompt-injected web page) could point it at http://localhost, a router admin page
or a cloud metadata address. Only public internet addresses are allowed here.
"""

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    pass


def assert_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError("URL must start with http:// or https://")
    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no host name.")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Cannot resolve host: {host}") from exc

    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.version == 6 and ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        if not ip.is_global:
            raise UnsafeURLError("Blocked: this address is not on the public internet.")
