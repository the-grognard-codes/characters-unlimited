import tempfile
import unittest
from pathlib import Path

from characters_unlimited.coverage import SourceInventory


class CoverageWorkflowTests(unittest.TestCase):
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
