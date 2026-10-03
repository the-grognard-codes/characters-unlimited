import json
from io import BytesIO
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.server import create_server


class LocalBackupAdapterTests(unittest.TestCase):
    def test_pdf_download_is_an_editable_document_and_preserves_saved_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create(name='Downloaded character')
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/api/characters/{character["id"]}/pdf', timeout=5) as response:
                    self.assertEqual(response.headers['Content-Type'], 'application/pdf')
                    reader = PdfReader(BytesIO(response.read()))
                    fields = reader.get_fields()
                    assert fields is not None
                    self.assertEqual(fields['NAME']['/V'], 'Downloaded character')
                self.assertEqual(app.get(character['id']), character)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)

    def test_invalid_source_audit_returns_diagnostic_without_affecting_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with patch.object(app, 'coverage', side_effect=ValueError('Source fingerprint changed')):
                    with self.assertRaises(HTTPError) as result:
                        urlopen(f'http://127.0.0.1:{server.server_port}/api/coverage', timeout=3)
                with result.exception as failure:
                    self.assertEqual(failure.code, 400)
                    self.assertIn('Source fingerprint changed', json.load(failure)['error'])
                self.assertEqual(app.get(character['id']), character)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)

    def test_sqlite_backup_failure_returns_a_controlled_error_and_preserves_the_save(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            server = create_server(app)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                address = f'http://127.0.0.1:{server.server_port}'
                with urlopen(address + '/api/bootstrap', timeout=3) as response:
                    token = json.load(response)['token']
                request = Request(address + '/api/backups', data=b'{}', headers={'X-Session-Token':token, 'Content-Type':'application/json'})
                with patch.object(app, 'backup', side_effect=sqlite3.OperationalError('Disk full')):
                    with self.assertRaises(HTTPError) as result:
                        urlopen(request, timeout=3)
                with result.exception as failure:
                    self.assertEqual(failure.code, 400)
                    self.assertIn('Existing saves and backups remain available', json.load(failure)['error'])
                self.assertEqual(app.get(character['id']), character)
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=3)
