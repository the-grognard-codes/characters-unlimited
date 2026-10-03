"""Loopback-only browser adapter for the character application."""

import argparse
import json
import os
import secrets
import sqlite3
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
                try:
                    self.respond(200, application.coverage())
                except (ValueError, OSError) as error:
                    self.respond(400, {"error": f"Source audit unavailable: {error}"})
            elif path.startswith("/api/characters/"):
                try:
                    parts = path.strip('/').split('/')
                    if len(parts) == 4 and parts[3] == 'skills':
                        self.respond(200, application.skill_view(parts[2]))
                    elif len(parts) == 4 and parts[3] == 'export':
                        self.respond(200, application.export_character(parts[2]))
                    else:
                        self.respond(200, application.get(path.rsplit("/", 1)[-1]))
                except KeyError:
                    self.respond(404, {"error": "Character not found"})
                except ValueError as error:
                    self.respond(400, {"error": str(error)})
            elif path in ("/", "/app.js", "/style.css", "/coverage.css", "/generation.css"):
                filename = "index.html" if path == "/" else path[1:]
                content_type = "text/html" if filename == "index.html" else "text/javascript" if filename.endswith(".js") else "text/css"
                self.respond(200, (assets / filename).read_bytes(), f"{content_type}; charset=utf-8")
            else:
                self.respond(404, {"error": "Not found"})

        def do_POST(self):
            if not self.allowed(mutation=True):
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 12_000_000:
                    raise ValueError("Request size must be between 1 and 12000000 bytes")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Request must be an object")
                path = urlsplit(self.path).path
                if path == "/api/characters":
                    self.respond(201, application.create(**data))
                elif path == '/api/import':
                    self.respond(201, application.import_character(data.get('bundle')))
                elif path == '/api/backups':
                    self.respond(201, application.backup())
                elif path.startswith("/api/characters/"):
                    parts = path.strip("/").split("/")
                    if len(parts) == 3:
                        self.respond(200, application.edit(parts[2], **data))
                    elif len(parts) == 4 and parts[3] == "reroll":
                        self.respond(200, application.reroll(parts[2], **data))
                    elif len(parts) == 4 and parts[3] == "attribute":
                        self.respond(200, application.set_attribute(parts[2], **data))
                    elif len(parts) == 4 and parts[3] == "skills":
                        self.respond(200, application.select_skills(parts[2], **data))
                    elif len(parts) == 4 and parts[3] == 'required-skills':
                        self.respond(200, application.select_required_skills(parts[2], **data))
                    elif len(parts) == 4 and parts[3] == 'duplicate':
                        self.respond(201, application.duplicate(parts[2]))
                    elif len(parts) == 4 and parts[3] == 'rule-preview':
                        self.respond(200, application.preview_rule_upgrade(parts[2]))
                    elif len(parts) == 4 and parts[3] == 'rule-upgrade':
                        self.respond(200, application.apply_rule_upgrade(parts[2], **data))
                    else:
                        self.respond(404, {"error": "Not found"})
                else:
                    self.respond(404, {"error": "Not found"})
            except SaveConflict as error:
                self.respond(409, {"error": str(error)})
            except (ValueError, TypeError) as error:
                self.respond(400, {"error": str(error)})
            except KeyError:
                self.respond(404, {"error": "Character not found"})
            except (OSError, RecursionError, sqlite3.Error):
                self.respond(400, {"error": "The local file operation could not complete. Existing saves and backups remain available."})

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
