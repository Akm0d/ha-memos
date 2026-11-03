#!/usr/bin/env python3
"""CI-only stand-in for Home Assistant Supervisor ingress path forwarding.

The browser requests /api/hassio_ingress/ci_session/*; Supervisor would strip
that prefix and send X-Ingress-Path when forwarding to the private listener.
"""
from __future__ import annotations

from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

PREFIX = "/api/hassio_ingress/ci_session"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self.forward()

    def do_POST(self):
        self.forward()

    def do_PUT(self):
        self.forward()

    def do_PATCH(self):
        self.forward()

    def do_DELETE(self):
        self.forward()

    def do_OPTIONS(self):
        self.forward()

    def forward(self):
        parsed = urlsplit(self.path)
        if parsed.path != PREFIX and not parsed.path.startswith(PREFIX + "/"):
            self.send_error(404)
            return
        backend_path = parsed.path[len(PREFIX):] or "/"
        if parsed.query:
            backend_path += "?" + parsed.query
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else None
        headers = {
            key: value for key, value in self.headers.items()
            if key.lower() not in ("host", "connection", "content-length", "transfer-encoding")
        }
        headers["X-Ingress-Path"] = PREFIX + "/"

        connection = HTTPConnection("127.0.0.1", 8099, timeout=15)
        try:
            connection.request(self.command, backend_path, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read()
            self.send_response(response.status)
            for name, value in response.getheaders():
                if name.lower() not in ("transfer-encoding", "connection", "content-length"):
                    self.send_header(name, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (ConnectionError, TimeoutError, OSError) as error:
            self.send_error(502, str(error))
        finally:
            connection.close()


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 19899), Handler).serve_forever()
