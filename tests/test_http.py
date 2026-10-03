import json
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from characters_unlimited.application import CharacterApplication
from characters_unlimited.server import create_server


class LocalBackupAdapterTests(unittest.TestCase):
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
