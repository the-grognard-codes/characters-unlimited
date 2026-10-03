import copy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.coverage import SourceInventory


class CanonicalOptionAuditWorkflowTests(unittest.TestCase):
    def test_coverage_distinguishes_confirmed_identities_from_mechanical_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            self.assertEqual(view['summary']['identity_confirmed'], 30)
            self.assertEqual(view['summary']['fully_automated'], 0)
            self.assertEqual(view['summary']['books_reviewed'], 0)
            vagabond = next(entry for entry in view['options'] if entry['id'] == 'rue-vagabond')
            self.assertEqual(vagabond['identity_review'], 'confirmed')
            self.assertEqual(vagabond['mechanical_review'], 'pending')
            self.assertEqual(vagabond['automation'], 'partial')
            self.assertEqual(vagabond['tickets'], ['05b-complete-rifts-skill-path'])
            self.assertTrue(vagabond['findings'])
            self.assertEqual(vagabond['source']['pdf_pages'], [46])

    def test_changed_source_cannot_inherit_identity_review(self):
        inventory, catalog = self.fixture()
        inventory['books'][0]['sha256'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            SourceInventory.with_catalog(inventory, catalog)

    def test_alias_candidate_must_belong_to_the_option_source(self):
        inventory, catalog = self.fixture()
        inventory['candidates'][0]['book_id'] = 'another-book'
        with self.assertRaisesRegex(ValueError, 'candidate'):
            SourceInventory.with_catalog(inventory, catalog)

    def test_catalog_cannot_claim_automation_or_duplicate_identities(self):
        inventory, catalog = self.fixture()
        catalog['entries'][0]['automation'] = 'fully-automated'
        with self.assertRaisesRegex(ValueError, 'automation'):
            SourceInventory.with_catalog(inventory, catalog)
        inventory, catalog = self.fixture()
        catalog['entries'].append(copy.deepcopy(catalog['entries'][0]))
        with self.assertRaisesRegex(ValueError, 'unique'):
            SourceInventory.with_catalog(inventory, catalog)

    def test_missing_ticket_and_dependency_review_remain_visible(self):
        inventory, catalog = self.fixture()
        view = SourceInventory.with_catalog(inventory, catalog)
        self.assertEqual(view['summary']['unassigned_options'], 1)
        self.assertEqual(view['options'][0]['dependency_review'], 'pending')
        self.assertEqual(view['summary']['mechanically_reviewed'], 0)

    def test_confirmed_identity_requires_a_source_section_link(self):
        inventory, catalog = self.fixture()
        catalog['entries'][0]['candidate_ids'] = []
        with self.assertRaisesRegex(ValueError, 'candidate source evidence'):
            SourceInventory.with_catalog(inventory, catalog)

    def test_duplicate_identity_cannot_inflate_audit_counts_under_a_new_id(self):
        inventory, catalog = self.fixture()
        duplicate = copy.deepcopy(catalog['entries'][0])
        duplicate.update(id='rue-another-scout', name='  SCOUT  ')
        catalog['entries'].append(duplicate)
        with self.assertRaisesRegex(ValueError, 'identities must be unique'):
            SourceInventory.with_catalog(inventory, catalog)

    @staticmethod
    def fixture():
        inventory = {'books': [{'id':'rue', 'sha256':'md', 'pdf_sha256':'pdf', 'game':'rifts'}],
                     'candidates': [{'id':'candidate', 'book_id':'rue', 'source_sha256':'md'}],
                     'summary': {'books':1, 'candidates':1, 'books_reviewed':0, 'fully_automated':0}}
        catalog = {'schema_version':1, 'findings':['Other options remain to be audited.'], 'entries': [{
            'id':'rue-scout', 'name':'Scout', 'kind':'occ', 'book_id':'rue', 'aliases':[],
            'candidate_ids':['candidate'], 'source':{'markdown_sha256':'md','pdf_sha256':'pdf','printed_pages':[43],'pdf_pages':[46]},
            'identity_review':'confirmed', 'mechanical_review':'pending', 'dependency_review':'pending',
            'automation':'not-implemented', 'tickets':[], 'dependencies':[], 'findings':['Mechanics and dependencies require review.']}]}
        return inventory, catalog
