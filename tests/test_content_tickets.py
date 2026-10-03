import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
import json

from characters_unlimited.application import CharacterApplication
from characters_unlimited.coverage import SourceInventory


class ContentTicketCoverageTests(unittest.TestCase):
    def test_every_audited_identity_has_a_real_bounded_owning_ticket(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
        self.assertEqual(view['summary']['canonical_options'], 718)
        self.assertEqual(view['summary']['unassigned_options'], 0)
        self.assertEqual(view['summary']['mechanically_reviewed'], 0)
        self.assertEqual(view['summary']['fully_automated'], 0)
        owners: dict[str, str] = {}
        root = Path(__file__).resolve().parents[1]
        for ticket in view['content_tickets']:
            self.assertTrue((root / ticket['path']).is_file(), ticket['id'])
            self.assertLessEqual(len(ticket['option_ids']), 12)
            for identifier in ticket['option_ids']:
                self.assertNotIn(identifier, owners)
                owners[identifier] = ticket['id']
        self.assertEqual(set(owners), {entry['id'] for entry in view['options']})
        self.assertEqual(owners['rue-vagabond'], '05b-complete-rifts-skill-path')
        issues = root / '.scratch' / 'character-creator' / 'issues'
        for prerequisite in view['prerequisite_tickets']:
            self.assertTrue((issues / f'{prerequisite}.md').is_file()
                            or list(issues.glob(f'{prerequisite}-*.md')), prerequisite)
        for entry in view['options']:
            self.assertEqual(entry['tickets'], [owners[entry['id']]])
            self.assertEqual(entry['mechanical_review'], 'pending')
            self.assertEqual(entry['dependency_review'], 'pending')

    def test_inconsistent_ticket_ownership_and_prerequisites_are_rejected(self):
        data = Path(__file__).resolve().parents[1] / 'characters_unlimited' / 'data'
        inventory = json.loads((data / 'source-inventory.json').read_text(encoding='utf-8'))
        catalog = json.loads((data / 'canonical-options.json').read_text(encoding='utf-8'))
        manifest = json.loads((data / 'content-tickets.json').read_text(encoding='utf-8'))
        mutations = []
        missing = deepcopy(manifest)
        missing['tickets'].pop()
        mutations.append(missing)
        duplicate = deepcopy(manifest)
        duplicate['tickets'][1]['option_ids'].append(duplicate['tickets'][0]['option_ids'][0])
        mutations.append(duplicate)
        unknown = deepcopy(manifest)
        unknown['tickets'][0]['dependencies'].append('unknown-prerequisite')
        mutations.append(unknown)
        traversal = deepcopy(manifest)
        traversal['tickets'][0]['path'] = '../outside.md'
        mutations.append(traversal)
        linked = next(ticket for ticket in manifest['tickets']
                      if any(dep in {item['id'] for item in manifest['tickets']}
                             for dep in ticket['dependencies']))
        omitted = deepcopy(manifest)
        next(item for item in omitted['tickets'] if item['id']==linked['id'])['dependencies'] = []
        mutations.append(omitted)
        for invalid in mutations:
            with self.subTest(manifest=invalid['tickets'][0]['id']):
                with self.assertRaises(ValueError):
                    SourceInventory.with_catalog(inventory, catalog, invalid)
        altered = deepcopy(catalog)
        altered['entries'][0]['tickets'] = ['unknown-owner']
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            SourceInventory.with_catalog(inventory, altered, manifest)

        mixed = deepcopy(manifest)
        combined = mixed['tickets'][0]
        books = {entry['id']: entry['book_id'] for entry in catalog['entries']}
        other = next(ticket for ticket in mixed['tickets'] if len(ticket['option_ids'])==1
                     and books[ticket['option_ids'][0]] != books[combined['option_ids'][0]])
        combined['option_ids'].extend(other['option_ids'])
        mixed['tickets'].remove(other)
        altered = deepcopy(catalog)
        for entry in altered['entries']:
            if entry['id'] in other['option_ids']:
                entry['tickets'] = [combined['id']]
        with self.assertRaisesRegex(ValueError, 'one source book'):
            SourceInventory.with_catalog(inventory, altered, mixed)
