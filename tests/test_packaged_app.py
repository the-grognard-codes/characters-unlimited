import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.error import URLError
from urllib.request import Request, urlopen
import json
from io import BytesIO
from pypdf import PdfReader


@unittest.skipUnless(os.getenv('CHARACTERS_UNLIMITED_EXE'), 'Frozen executable checked by the packaging workflow')
class PackagedApplicationTests(unittest.TestCase):
    def test_frozen_app_works_without_developer_tools_and_reopens_saved_characters(self):
        executable = Path(os.environ['CHARACTERS_UNLIMITED_EXE']).resolve()
        self.assertTrue(executable.is_file(), 'Build the Windows package first')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            environment = dict(os.environ)
            environment['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
            with socket.socket() as probe:
                probe.bind(('127.0.0.1', 0))
                port = probe.getsockname()[1]
            url = f'http://127.0.0.1:{port}'
            def request(path, value=None, token=None):
                body = None if value is None else json.dumps(value).encode()
                headers = {'Content-Type':'application/json'}
                if token is not None:
                    headers['X-Session-Token'] = token
                with urlopen(Request(url + path, data=body, headers=headers), timeout=15) as response:
                    payload = response.read()
                    return payload if response.headers.get_content_type() == 'application/pdf' else json.loads(payload)
            def launch(gui=False):
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup.wShowWindow = subprocess.SW_HIDE
                process = subprocess.Popen([str(executable), '--no-browser' if gui else '--headless',
                                            '--port', str(port), '--data-dir', str(root / 'saves')],
                                           cwd=root, env=environment, startupinfo=startup)
                try:
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline:
                        if process.poll() is not None:
                            self.fail(f'Packaged app exited with {process.returncode}')
                        try:
                            return process, request('/api/bootstrap')
                        except URLError:
                            time.sleep(.1)
                    self.fail('Packaged app did not start within 30 seconds')
                except BaseException:
                    process.terminate(); process.wait(timeout=10)
                    raise
            process, bootstrap = launch()
            try:
                with urlopen(url, timeout=15) as page:
                    self.assertIn(b'Export editable PDF', page.read())
                token = bootstrap['token']
                character = request('/api/characters', {'name':'Packaged Rowan'}, token)
                identifier = character['id']
                self.assertEqual(len(character['attributes']), 8)
                self.assertEqual(request('/api/characters/' + identifier)['name'], 'Packaged Rowan')
                coverage = request('/api/coverage')
                self.assertIn('books', coverage)
                portable = request('/api/characters/' + identifier + '/export')
                imported = request('/api/import', {'bundle':portable}, token)
                self.assertNotEqual(imported['id'], identifier)
                reader = PdfReader(BytesIO(request('/api/characters/' + identifier + '/pdf')))
                fields = reader.get_fields()
                assert fields is not None
                self.assertEqual(fields['NAME']['/V'], 'Packaged Rowan')
                self.assertTrue(reader.pages[0].get('/Annots'))
            finally:
                process.terminate(); process.wait(timeout=10)
            with socket.socket() as occupied:
                occupied.bind(('127.0.0.1', 0))
                occupied.listen()
                failed = subprocess.Popen([str(executable), '--headless', '--port',
                                           str(occupied.getsockname()[1]), '--data-dir', str(root / 'saves')],
                                          cwd=root, env=environment)
                try:
                    self.assertEqual(failed.wait(timeout=15), 1)
                    self.assertIn('Traceback', (root / 'saves' / 'startup-error.log').read_text())
                finally:
                    if failed.poll() is None:
                        failed.terminate(); failed.wait(timeout=10)
            process, bootstrap = launch(gui=True)
            try:
                self.assertEqual(request('/api/characters/' + identifier)['name'], 'Packaged Rowan')
            finally:
                process.terminate(); process.wait(timeout=10)
            process, bootstrap = launch()
            try:
                self.assertEqual(request('/api/characters/' + identifier)['name'], 'Packaged Rowan')
                self.assertEqual(len(bootstrap['characters']), 2)
            finally:
                process.terminate(); process.wait(timeout=10)
