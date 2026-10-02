"""Loopback-only browser adapter for the character application."""

import argparse
import json
import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

from .application import CharacterApplication, SaveConflict


def create_server(application, port=0):
    assets = Path(__file__).parent / "web"
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def respond(self, status, value, content_type="application/json; charset=utf-8"):
            body = json.dumps(value, ensure_ascii=False).encode() if not isinstance(value, bytes) else value
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def allowed(self, mutation=False):
            port_number = cast(ThreadingHTTPServer, self.server).server_port
            host = self.headers.get("Host", "")
            if host not in (f"127.0.0.1:{port_number}", f"localhost:{port_number}"):
                self.respond(403, {"error": "Local access only"})
                return False
            origin = self.headers.get("Origin")
            if origin and origin != f"http://{host}":
                self.respond(403, {"error": "Cross-origin access is not allowed"})
                return False
            if mutation and self.headers.get("X-Session-Token") != token:
                self.respond(403, {"error": "Session token required"})
                return False
            return True

        def do_GET(self):
            if not self.allowed():
                return
            path = urlsplit(self.path).path
            if path == "/api/bootstrap":
                self.respond(200, {"token": token, "catalog": application.catalog(), "characters": application.list()})
            elif path == "/api/coverage":
                self.respond(200, application.coverage())
            elif path.startswith("/api/characters/"):
                try:
                    self.respond(200, application.get(path.rsplit("/", 1)[-1]))
                except KeyError:
                    self.respond(404, {"error": "Character not found"})
            elif path in ("/", "/app.js", "/style.css", "/coverage.css"):
                filename = "index.html" if path == "/" else path[1:]
                content_type = {"index.html": "text/html", "app.js": "text/javascript", "style.css": "text/css", "coverage.css": "text/css"}[filename]
                self.respond(200, (assets / filename).read_bytes(), f"{content_type}; charset=utf-8")
            else:
                self.respond(404, {"error": "Not found"})

        def do_POST(self):
            if not self.allowed(mutation=True):
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1_000_000:
                    raise ValueError("Request size must be between 1 and 1000000 bytes")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Request must be an object")
                path = urlsplit(self.path).path
                if path == "/api/characters":
                    self.respond(201, application.create(**data))
                elif path.startswith("/api/characters/"):
                    self.respond(200, application.edit(path.rsplit("/", 1)[-1], **data))
                else:
                    self.respond(404, {"error": "Not found"})
            except SaveConflict as error:
                self.respond(409, {"error": str(error)})
            except (ValueError, TypeError) as error:
                self.respond(400, {"error": str(error)})
            except KeyError:
                self.respond(404, {"error": "Character not found"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description="Characters Unlimited")
    parser.add_argument("--data-dir", type=Path, default=Path(os.getenv("LOCALAPPDATA", Path.home())) / "CharactersUnlimited")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args()
    server = create_server(CharacterApplication(arguments.data_dir), arguments.port)
    url = f"http://127.0.0.1:{server.server_address[1]}"
    print(f"Characters Unlimited: {url}\nCharacter data: {arguments.data_dir}", flush=True)
    if not arguments.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
