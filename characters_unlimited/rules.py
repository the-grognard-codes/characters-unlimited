"""Accepted rule definitions, resolved by exact version and immutable content."""

import hashlib
import json
from pathlib import Path

from .portability import canonical


class RuleArchive:
    def __init__(self, definitions, active):
        self._definitions: dict[tuple[str, str], bytes] = {}
        for definition in definitions:
            if not isinstance(definition, dict) or any(not isinstance(definition.get(key), str) or not definition[key] for key in ('id', 'version')):
                raise ValueError('Accepted rules need an identity and version')
            key = (definition['id'], definition['version'])
            if key in self._definitions:
                raise ValueError(f'Duplicate accepted rule version: {key[0]} {key[1]}')
            self._definitions[key] = canonical(definition)
        if not isinstance(active, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in active.items()):
            raise ValueError('Active rules must identify accepted versions')
        self._active = dict(active)
        for identifier, version in self._active.items():
            self.resolve(identifier, version)

    @classmethod
    def load(cls, directory=None):
        root = Path(directory) if directory is not None else Path(__file__).parent / 'packs'
        manifest = json.loads((root / 'accepted.json').read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or type(manifest.get('schema_version')) is not int or manifest['schema_version'] != 1 or not isinstance(manifest.get('definitions'), list):
            raise ValueError('Unsupported accepted-rule manifest')
        definitions = []
        for entry in manifest['definitions']:
            if not isinstance(entry, dict):
                raise ValueError('Invalid accepted-rule manifest entry')
            filename = entry.get('filename')
            if not isinstance(filename, str) or '/' in filename or '\\' in filename or Path(filename).name != filename:
                raise ValueError('Accepted rule files must be inside the pack directory')
            definition = json.loads((root / filename).read_text(encoding='utf-8'))
            if not isinstance(definition, dict):
                raise ValueError(f'Accepted rule definition must be an object: {filename}')
            if hashlib.sha256(canonical(definition)).hexdigest() != entry.get('sha256'):
                raise ValueError(f'Accepted rule content changed: {filename}')
            if (definition.get('id'), definition.get('version')) != (entry.get('id'), entry.get('version')):
                raise ValueError(f'Accepted rule identity changed: {filename}')
            definitions.append(definition)
        return cls(definitions, manifest.get('active'))

    def resolve(self, identifier, version):
        encoded = self._definitions.get((identifier, version))
        if encoded is None:
            raise ValueError(f'Unsupported rule version: {identifier} {version}')
        return json.loads(encoded)

    def active(self, identifier):
        if identifier not in self._active:
            raise ValueError(f'No active accepted rule pack: {identifier}')
        return self.resolve(identifier, self._active[identifier])

    def active_versions(self):
        return dict(self._active)

    def definitions(self):
        return [json.loads(encoded) for encoded in self._definitions.values()]
