"""
Tiny local HTTP file server to serve HTML assets over http://127.0.0.1:<port>.
Used to avoid file:// origin issues for embedded gateways.
"""

import http.server
import socket
import socketserver
import threading
from pathlib import Path
from typing import Optional


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):  # noqa: A003 - match base signature
        pass


class LocalFileServer:
    """Start/stop a simple HTTP server in a background thread."""

    def __init__(
        self, root_dir: Path, host: str = "127.0.0.1", port: Optional[int] = None
    ):
        self.root_dir = Path(root_dir)
        self.host = host
        self.port = port or self._find_free_port(host)
        self._httpd: Optional[socketserver.TCPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        handler_cls = _QuietHandler

        # Change working directory context for handler
        def handler_factory(*args, **kwargs):
            return handler_cls(*args, directory=str(self.root_dir), **kwargs)

        self._httpd = socketserver.TCPServer((self.host, self.port), handler_factory)
        self._httpd.allow_reuse_address = True

        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self._httpd:
            try:
                self._httpd.shutdown()
                self._httpd.server_close()
            finally:
                self._httpd = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @staticmethod
    def _find_free_port(host: str) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, 0))
            return s.getsockname()[1]
