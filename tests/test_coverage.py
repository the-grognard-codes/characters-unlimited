import tempfile
import unittest
from pathlib import Path

from characters_unlimited.coverage import SourceInventory


class CoverageWorkflowTests(unittest.TestCase):
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
