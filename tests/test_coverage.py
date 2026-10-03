import tempfile
import unittest
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from characters_unlimited.coverage import SourceInventory


class CoverageWorkflowTests(unittest.TestCase):
    def test_verified_locator_correction_replaces_the_same_gap_without_double_counting(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'Rifts - Damaged.md'
            source.write_text('# Book\n## Destroyer\n<!-- SOURCE GAP: Wrong printed page 107. -->\n## Other\n<!-- SOURCE GAP: Separate missing passage. -->\n', encoding='utf-8')
            (Path(directory) / 'Rifts - Damaged.pdf').write_bytes(b'original fixture')
            inventory = SourceInventory.scan(directory, directory)
            book = inventory['books'][0]
            record = {'book_id':book['id'], 'markdown_sha256':book['sha256'],
                      'pdf_sha256':book['pdf_sha256'], 'gap':{'line':3, 'end_line':3,
                      'description':'Verified PDF page 108 / printed page 108.'}}
            revised = SourceInventory.with_verified_gaps(inventory, [record])
            self.assertEqual(revised['summary']['source_gaps'], 2)
            destroyer = next(item for item in revised['candidates'] if item['title']=='Destroyer')
            self.assertEqual(destroyer['source_gaps'], [record['gap']])
            self.assertEqual(destroyer['status'], 'source-gap')
            self.assertEqual(revised['books'][0]['source_gaps'][1], book['source_gaps'][1])
            self.assertIn('107', book['source_gaps'][0]['description'])
            self.assertEqual(SourceInventory.with_verified_gaps(revised, [record]), revised)
            self.assertIn('107', source.read_text(encoding='utf-8'))
        active = SourceInventory.load()
        self.assertEqual(active['summary']['source_gaps'], 2)
        damaged = next(book for book in active['books'] if book['id']=='rifts-world-book-09-south-america-2')
        self.assertIn('printed page 108', damaged['source_gaps'][0]['description'])

    def test_verified_pdf_gap_survives_rescan_without_editing_the_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'Rifts - Example.md'
            source.write_text('# Book\n## Carrier\nPartial systems\n## Intact\nRules\n', encoding='utf-8')
            original = source.read_bytes()
            (Path(directory) / 'Rifts - Example.pdf').write_bytes(b'original pdf fixture')
            inventory = SourceInventory.scan(directory, directory)
            book = inventory['books'][0]
            record = {'book_id':book['id'], 'markdown_sha256':book['sha256'],
                      'pdf_sha256':book['pdf_sha256'], 'gap':{'line':2, 'end_line':3,
                      'description':'Printed page missing from supplied PDF.'}}
            records = [record]
            revised = SourceInventory.with_verified_gaps(inventory, records)
            self.assertEqual(revised['summary']['source_gaps'], 1)
            self.assertEqual(next(item for item in revised['candidates'] if item['title']=='Carrier')['status'], 'source-gap')
            self.assertEqual(next(item for item in revised['candidates'] if item['title']=='Intact')['status'], 'needs-review')
            self.assertEqual(inventory['summary']['source_gaps'], 0)
            self.assertEqual(SourceInventory.with_verified_gaps(revised, records), revised)
            rescanned = SourceInventory.with_verified_gaps(SourceInventory.scan(directory, directory), records)
            self.assertEqual(rescanned['books'][0]['source_gaps'], revised['books'][0]['source_gaps'])
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), hashlib.sha256(original).digest())
            for field in ('markdown_sha256','pdf_sha256','book_id'):
                altered = copy.deepcopy(records); altered[0][field] = 'changed'
                with self.assertRaisesRegex(ValueError, 'source'):
                    SourceInventory.with_verified_gaps(inventory, altered)
            malformed = copy.deepcopy(records); malformed[0]['gap']['line'] = 0
            with self.assertRaisesRegex(ValueError, 'range'):
                SourceInventory.with_verified_gaps(inventory, malformed)
            malformed = copy.deepcopy(records); malformed[0]['gap']['end_line'] = 999999
            with self.assertRaisesRegex(ValueError, 'range'):
                SourceInventory.with_verified_gaps(inventory, malformed)
            output = Path(directory) / 'scan.json'
            command = [sys.executable, '-m', 'characters_unlimited.coverage', directory, '--output', str(output)]
            custom = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(custom.returncode, 0, custom.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['summary']['source_gaps'], 0)
            registry = Path(directory) / 'gaps.json'
            registry.write_text(json.dumps(records), encoding='utf-8')
            verified = subprocess.run(command + ['--pdf-directory', directory, '--verified-gaps', str(registry)],
                                      capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['summary']['source_gaps'], 1)

    def test_underseas_missing_page_is_visible_without_certifying_mechanics(self):
        inventory = SourceInventory.load()
        self.assertEqual(inventory['summary']['source_gaps'], 2)
        carrier = next(item for item in inventory['candidates'] if item['id']=='061b098337365482e80c')
        self.assertEqual(carrier['status'], 'source-gap')
        self.assertIn('131', carrier['source_gaps'][0]['description'])
        self.assertEqual(inventory['summary']['mechanically_reviewed'], 0)

    def test_source_gaps_remain_visible_and_block_the_containing_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'Rifts - Damaged.md'
            source.write_text('# Book\n## Destroyer\nReadable rules\n<!-- SOURCE GAP: Missing\nabilities 2–4. -->\n## Intact\nRules\n', encoding='utf-8')
            inventory = SourceInventory.scan(directory)
            self.assertEqual(inventory['books'][0]['source_gaps'], [{'line': 4, 'end_line': 5, 'description': 'Missing abilities 2–4.'}])
            self.assertEqual(inventory['summary']['source_gaps'], 1)
            self.assertEqual(next(item for item in inventory['candidates'] if item['title'] == 'Destroyer')['status'], 'source-gap')
            self.assertEqual(next(item for item in inventory['candidates'] if item['title'] == 'Intact')['status'], 'needs-review')

    def test_changed_source_creates_new_candidate_identity_even_when_heading_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'Rifts - Example.md'
            source.write_text('# Scout\nIncorrect rule\n', encoding='utf-8')
            old = SourceInventory.scan(directory)
            source.write_text('# Scout\nCorrected rule\n', encoding='utf-8')
            corrected = SourceInventory.scan(directory)
            self.assertNotEqual(old['candidates'][0]['id'], corrected['candidates'][0]['id'])
            self.assertNotEqual(old['books'][0]['sha256'], corrected['books'][0]['sha256'])

    def test_source_inventory_records_candidates_without_claiming_automation(self):
        with tempfile.TemporaryDirectory() as directory:
            sources = Path(directory) / "sources"
            sources.mkdir()
            (sources / "Rifts - Example.md").write_text(
                "# Test book\n\n## Scout O.C.C.\nAn adventurer.\n\n## Nightfolk R.C.C.\nA racial class.\n",
                encoding="utf-8",
            )
            inventory = SourceInventory.scan(sources)
            self.assertEqual(inventory["books"][0]["game"], "rifts")
            scout = next(item for item in inventory["candidates"] if item["title"] == "Scout O.C.C.")
            self.assertEqual(scout["line"], 3)
            self.assertEqual(scout["kind"], "occ")
            self.assertEqual(scout["status"], "needs-review")
            self.assertEqual(inventory["summary"]["fully_automated"], 0)
            self.assertFalse(inventory["books"][0]["review_complete"])


if __name__ == "__main__":
    unittest.main()
