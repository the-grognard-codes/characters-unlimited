"""Transactional local saves, independent of the application's installation folder."""

import json
import sqlite3
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class SaveConflict(ValueError):
    """The submitted changes are based on an older saved character."""


class CharacterStore:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.database = self.directory / "characters.sqlite3"
        with self.connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS characters "
                "(id TEXT PRIMARY KEY, document TEXT NOT NULL)"
            )

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.database, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def put(self, character: dict):
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO characters(id, document) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET document=excluded.document",
                (character["id"], json.dumps(character, ensure_ascii=False)),
            )

    def get(self, identifier: str) -> dict:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT document FROM characters WHERE id=?", (identifier,)
            ).fetchone()
        if row is None:
            raise KeyError("Character not found")
        return json.loads(row[0])

    def backup(self):
        directory = self.directory / 'backups'
        directory.mkdir(exist_ok=True)
        descriptor, filename = tempfile.mkstemp(prefix='backup-', suffix='.tmp', dir=directory)
        os.close(descriptor)
        temporary = Path(filename)
        destination = directory / (temporary.stem + '.sqlite3')
        try:
            target = sqlite3.connect(temporary)
            try:
                with self.connect() as connection:
                    connection.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('The backup did not pass its integrity check')
            finally:
                target.close()
            with temporary.open('r+b') as saved:
                os.fsync(saved.fileno())
            os.replace(temporary, destination)
            return destination
        finally:
            temporary.unlink(missing_ok=True)

    def list(self) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute("SELECT document FROM characters").fetchall()
        return sorted(
            (json.loads(row[0]) for row in rows),
            key=lambda character: character["updated_at"],
            reverse=True,
        )

    def update(self, identifier: str, changes: dict, revision: int) -> dict:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT document FROM characters WHERE id=?", (identifier,)
            ).fetchone()
            if row is None:
                raise KeyError("Character not found")
            character = json.loads(row[0])
            current_revision = character.get("revision", 0)
            if revision != current_revision:
                raise SaveConflict("This character changed in another tab. Your edits remain here. Copy them, then reload and reopen the saved character before retrying.")
            character.update(changes)
            character["revision"] = current_revision + 1
            character["updated_at"] = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "UPDATE characters SET document=? WHERE id=?",
                (json.dumps(character, ensure_ascii=False), identifier),
            )
        return character

    def restore(self, identifier: str, restored: dict, recovery: dict, revision: int) -> dict:
        """Atomically retain the current state as a new save and restore a snapshot."""
        with self.connect() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute('SELECT document FROM characters WHERE id=?', (identifier,)).fetchone()
            if row is None:
                raise KeyError('Character not found')
            current = json.loads(row[0])
            if revision != current['revision']:
                raise SaveConflict('This character changed. Reopen it before undoing advancement.')
            restored = {**restored, 'id': identifier, 'revision': revision + 1,
                        'updated_at': datetime.now(timezone.utc).isoformat()}
            connection.execute('INSERT INTO characters(id, document) VALUES (?, ?)',
                               (recovery['id'], json.dumps(recovery, ensure_ascii=False)))
            connection.execute('UPDATE characters SET document=? WHERE id=?',
                               (json.dumps(restored, ensure_ascii=False), identifier))
        return {'character': restored, 'recovery': recovery}
