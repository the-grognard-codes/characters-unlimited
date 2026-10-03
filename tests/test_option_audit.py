import copy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.coverage import SourceInventory


class CanonicalOptionAuditWorkflowTests(unittest.TestCase):
    def test_powers_unlimited_three_preserves_animal_extensions_and_missing_page_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']:entry for entry in view['options']}
            extension = options['pu3-animal-abilities-new-types']
            self.assertEqual(extension['kind'], 'option-family')
            self.assertEqual(extension['dependencies'], ['hu2-animal-abilities'])
            self.assertEqual(extension['source']['printed_pages'], [4])
            self.assertEqual(extension['source']['pdf_pages'], [6, 51])
            self.assertEqual(options['pu3-animal-bat']['kind'], 'power')
            self.assertEqual(options['pu3-animal-bat']['dependencies'],
                             ['pu3-animal-abilities-new-types', 'hu2-flight-glide', 'pu1-sonar'])
            self.assertEqual(options['pu3-flesh-works']['source']['printed_pages'], [62])
            self.assertEqual(options['pu3-flesh-works']['source']['pdf_pages'], [62])
            for identifier in ('pu3-energy-conversion', 'pu3-energy-wings', 'pu3-enlarge-items'):
                entry = options[identifier]
                self.assertIn('d95e432f0efc5fa82e4c', entry['candidate_ids'])
                self.assertEqual(entry['source']['printed_pages'], [4])
                self.assertEqual(entry['source']['pdf_pages'], [6])
                self.assertTrue(any('60–61' in note and 'missing' in note.lower() for note in entry['findings']))
            entries = [item for item in options.values() if item['book_id']=='heroes-unlimited-powers-unlimited-3']
            self.assertEqual(len(entries), 137)
            self.assertEqual(sum(item['kind']=='power' for item in entries), 134)
            for entry in entries:
                self.assertEqual(entry['mechanical_review'], 'pending')
                self.assertEqual(entry['automation'], 'not-implemented')
                self.assertEqual(entry['game'], 'heroes-unlimited')

    def test_shared_heroes_animal_references_are_powers_and_not_creation_races(self):
        with tempfile.TemporaryDirectory() as directory:
            options = {entry['id']:entry for entry in CharacterApplication(directory).coverage()['options']}
            self.assertEqual(options['hu2-animal-abilities']['kind'], 'power')
            self.assertEqual(options['hu2-animal-abilities']['source']['pdf_pages'], [252])
            self.assertEqual(options['hu2-flight-glide']['source']['printed_pages'], [232])
            self.assertEqual(options['hu2-adhesion']['source']['printed_pages'], [228])
            self.assertEqual(options['hu2-flight-glide']['automation'], 'not-implemented')

    def test_powers_unlimited_one_keeps_rank_groups_and_body_psionics_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']:entry for entry in view['options']}
            self.assertEqual(options['pu1-abnormal-energy-sense']['source']['printed_pages'], [9])
            self.assertEqual(options['pu1-abnormal-energy-sense']['source']['pdf_pages'], [11])
            self.assertEqual(options['pu1-abnormal-energy-sense']['dependencies'], ['pu1-minor-super-abilities'])
            self.assertEqual(options['pu1-psionic-bio-alteration']['kind'], 'psionic')
            self.assertEqual(options['pu1-psionic-bio-alteration']['source']['pdf_pages'], [90])
            self.assertEqual(options['pu1-psionic-abilities']['dependencies'], ['hu2-psionics'])
            entries = [item for item in options.values() if item['book_id'] == 'heroes-unlimited-powers-unlimited-1']
            self.assertEqual(len(entries), 194)
            self.assertEqual(sum(item['kind'] == 'psionic' for item in entries), 21)
            for entry in entries:
                self.assertEqual(entry['mechanical_review'], 'pending')
                self.assertEqual(entry['automation'], 'not-implemented')
                self.assertEqual(entry['game'], 'heroes-unlimited')

    def test_remaining_alien_groups_keep_castes_shared_traits_and_generation_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']:entry for entry in view['options']}
            self.assertEqual(options['au-aluta']['source']['printed_pages'], [98])
            optional = options['au-optional-alien-generation']
            self.assertEqual(optional['source']['printed_pages'], [18,19])
            self.assertEqual(optional['source']['pdf_pages'], [19,20])
            self.assertTrue(any('Mantis' in note and 'Atorians' in note for note in optional['findings']))
            self.assertIn('83d4d40e813f41e95593', optional['candidate_ids'])
            self.assertIn('ef0271896bca9890ac66', optional['candidate_ids'])
            self.assertIn('Fehrans', options['au-atorians']['aliases'])
            self.assertIn('Darkan', options['au-darakan']['aliases'])
            self.assertEqual(options['au-hatha-cave-dweller']['dependencies'], ['au-hatha'])
            self.assertEqual(options['au-aborea']['dependencies'], ['au-naiden'])
            self.assertEqual(options['au-xippus-queen']['dependencies'], ['au-xippus'])
            self.assertNotIn('au-atorians', options['au-photins']['dependencies'])
            self.assertIn('au-mineral-standard', options['au-miceans']['dependencies'])
            self.assertIn('au-plant-standard', options['au-kisent']['dependencies'])
            self.assertEqual(options['au-jenjoran-anti-magic-warrior']['source']['printed_pages'], [136])
            self.assertEqual(options['au-ikta']['source']['pdf_pages'], [146,147])
            self.assertEqual(options['au-ikta']['candidate_ids'], ['194202d6777bd54f2ae2','8bc7b6f03ba0a1d368c4'])
            self.assertEqual(options['au-ikta']['dependencies'], ['au-sprekalians'])
            self.assertEqual(options['au-optional-alien-generation']['source']['pdf_pages'], [19,20])
            self.assertIn('19', ' '.join(options['au-optional-alien-generation']['findings']))
            self.assertEqual(options['au-dopplegangers']['kind'], 'option-family')
            self.assertEqual(options['au-reipoc']['dependencies'], ['au-dopplegangers'])
            self.assertNotIn('4a0acbd5c35667c1c9a1', options['au-dark-breeze']['candidate_ids'])
            self.assertIn('NPC', ' '.join(options['au-lotha']['findings']))
            self.assertEqual(options['au-vacuum-ghouls']['source']['pdf_pages'], [162])
            self.assertEqual(view['summary']['mechanically_reviewed'], 0)

    def test_aliens_species_keep_original_offsets_aliases_and_embedded_branches(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory)
            view = app.coverage()
            options = {entry['id']:entry for entry in view['options']}
            self.assertEqual(options['au-axolotl']['source']['printed_pages'], [50])
            self.assertEqual(options['au-axolotl']['source']['pdf_pages'], [51])
            self.assertEqual(options['au-darkith']['dependencies'], ['au-cameroon'])
            self.assertEqual(options['au-wardions']['kind'], 'option-family')
            self.assertEqual(options['au-wardions']['dependencies'], ['au-dergins'])
            self.assertEqual(options['au-wardions']['source']['printed_pages'], [83])
            self.assertIn('Nattereri', options['au-nattereris']['aliases'])
            self.assertIn('Dyteen', options['au-dyteens']['aliases'])
            self.assertIn('Timnehs', options['au-timneh']['aliases'])
            self.assertNotIn('Tagoniglomerate', options['au-tagonicans']['aliases'])
            self.assertEqual(options['au-linx']['source']['pdf_pages'], [95])
            aliens = [entry for entry in options.values() if entry['book_id'] == 'aliens-unlimited']
            self.assertEqual(len(aliens), 113)
            for entry in aliens:
                self.assertEqual(entry['game'], 'heroes-unlimited')
                self.assertEqual(entry['automation'], 'not-implemented')
                self.assertEqual(entry['mechanical_review'], 'pending')
            self.assertEqual([pack['classes'][0]['id'] for pack in app.catalog()['packs']], ['vagabond','mutant'])

    def test_pu2_branches_keep_shared_sources_modifiers_and_game_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']: entry for entry in view['options']}
            self.assertEqual(options['pu2-minor-hero']['kind'], 'rule')
            self.assertIn('modifier', ' '.join(options['pu2-minor-hero']['findings']))
            self.assertEqual(options['pu2-immortal-demigod']['source']['printed_pages'], [62])
            self.assertIn('hu2-mega-hero', options['pu2-immortal-demigod']['dependencies'])
            self.assertEqual(options['pu2-immortal-spirit']['candidate_ids'], options['pu2-immortal-golem']['candidate_ids'])
            self.assertEqual(options['pu2-gestalt-plant']['dependencies'], ['pu2-gestalt'])
            self.assertEqual(options['pu2-eugenic-construction']['kind'], 'construction')
            self.assertIn('Brain Impant Augmentation', options['pu2-supersoldier-brain-implant']['aliases'])
            self.assertIn('Chemical Enhanced Hero', options['pu2-supersoldier-chemical']['aliases'])
            self.assertIn('hu2-mega-hero', options['pu2-immortal-undead']['dependencies'])
            self.assertIn('hu2-aliens', options['pu2-immortal-alien']['dependencies'])
            self.assertIn('hu2-psionics', options['pu2-immortal-spirit']['dependencies'])
            self.assertEqual(options['pu2-spit-spikes']['source']['pdf_pages'], [96])
            for entry in options.values():
                if entry['id'].startswith('pu2-'):
                    self.assertEqual(entry['game'], 'heroes-unlimited')
                    self.assertEqual(entry['automation'], 'not-implemented')
                    self.assertEqual(entry['mechanical_review'], 'pending')
            self.assertEqual(len([entry for entry in options.values() if entry['id'].startswith('pu2-')]), 47)
            self.assertEqual([pack['classes'][0]['id'] for pack in CharacterApplication(directory).catalog()['packs']], ['vagabond', 'mutant'])

    def test_mercenary_and_sa2_paths_keep_heritages_offsets_and_blocked_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']: entry for entry in view['options']}
            self.assertEqual(view['summary']['canonical_options'], 718)
            self.assertEqual(view['summary']['unassigned_options'], 717)
            self.assertEqual(options['mercenaries-company-design']['kind'], 'construction')
            self.assertEqual(options['mercenaries-bounty-hunter']['source']['pdf_pages'], [21])
            self.assertIn('Special Forces Soldier', options['mercenaries-special-forces']['aliases'])
            self.assertIn('optional', ' '.join(options['mercenaries-lost-ones']['findings']).lower())
            self.assertEqual(options['merc-ops-auto-g']['source']['pdf_pages'], [49])
            self.assertEqual(options['sa2-true-inca-inti']['dependencies'], ['sa2-true-inca'])
            self.assertEqual(options['sa2-true-inca-inti']['source']['pdf_pages'], [21])
            self.assertEqual(options['sa2-pucara-mind-mage']['dependencies'], ['sa2-pucara-red-giant'])
            self.assertEqual(options['sa2-megaversal-ojahee-trooper']['dependencies'], ['sa2-ojahee'])
            self.assertEqual(options['sa2-duelist']['dependencies'], ['sa2-amaki-stone-man'])
            self.assertIn('Psi-Taur', options['sa2-equinoid']['aliases'])
            self.assertIn('6251b651ff5b0a3fcdec', options['sa2-destroyer-borg']['candidate_ids'])
            self.assertIn('blocked', ' '.join(options['sa2-destroyer-borg']['findings']).lower())
            damaged = next(c for c in view['candidates'] if c['id']=='6251b651ff5b0a3fcdec')
            self.assertEqual(damaged['status'], 'source-gap')
            self.assertEqual(view['summary']['source_gaps'], 4)
            for entry in options.values():
                if entry['id'].startswith(('sa2-', 'mercenaries-', 'merc-ops-')):
                    self.assertEqual(entry['mechanical_review'], 'pending')
                    self.assertEqual(entry['automation'], 'not-implemented')

    def test_atlantis_splynn_identities_preserve_variants_and_source_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']: entry for entry in view['options']}
            self.assertEqual(view['summary']['identity_confirmed'], 718)
            self.assertEqual(view['summary']['unassigned_options'], 717)
            self.assertEqual(options['atlantis-nomad']['dependencies'], ['atlantis-true-atlantean'])
            self.assertIn('True Atlantean Adventurer', options['atlantis-nomad']['aliases'])
            self.assertEqual(options['atlantis-undead-slayer']['source']['printed_pages'], [17, 97])
            self.assertEqual(options['atlantis-t-monster-man']['dependencies'], ['atlantis-tattooed-man'])
            self.assertEqual(options['atlantis-kittani-warrior']['kind'], 'rcc')
            self.assertIn('O.C.C.', ' '.join(options['atlantis-kittani-warrior']['findings']))
            self.assertEqual(options['splynn-staphra-warrior']['source']['printed_pages'], [92])
            self.assertEqual(options['splynn-staphra-warlord']['source']['pdf_pages'], [94])
            self.assertEqual(options['splynn-staphra-mystic']['source']['printed_pages'], [95])
            self.assertEqual(len(options['splynn-staphra-mystic']['candidate_ids']), 3)
            self.assertEqual(options['splynn-tattooed-archer']['source']['pdf_pages'], [109])
            self.assertEqual(options['splynn-monster-were-dragon']['kind'], 'rule')
            self.assertEqual(options['splynn-monster-were-dragon']['dependencies'], ['splynn-were-dragon'])
            self.assertIn('Translator/Interpreter', options['splynn-rulian-translator']['aliases'])
            self.assertNotEqual(options['splynn-true-bio-borg']['id'], options['splynn-partial-bio-borg']['id'])
            self.assertEqual(view['summary']['source_gaps'], 4)
            for entry in options.values():
                if entry['id'].startswith(('atlantis-', 'splynn-')):
                    self.assertEqual(entry['mechanical_review'], 'pending')
                    self.assertEqual(entry['automation'], 'not-implemented')
                    self.assertEqual(entry['game'], 'rifts')

    def test_supplement_identities_keep_source_aliases_and_shared_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']:entry for entry in view['options']}
            self.assertEqual(view['summary']['identity_confirmed'], 718)
            self.assertEqual(view['summary']['unassigned_options'], 717)
            self.assertEqual(options['sa1-ewaipanomas']['source']['printed_pages'], [102])
            self.assertEqual(options['sa1-shaydor-spherians']['source']['pdf_pages'], [104])
            self.assertIn('Amazon R.C.G', options['sa1-amazon']['aliases'])
            self.assertNotEqual(options['sa1-mutant-cat']['candidate_ids'], options['sa1-felinoid']['candidate_ids'])
            self.assertEqual(options['sa1-aunyain']['dependencies'], ['sa1-totem-warrior'])
            self.assertEqual(options['sa1-werepanther']['candidate_ids'], ['bbdd60a62fb5960464f4'])
            self.assertEqual(options['underseas-dolphin-pneuma-biform']['dependencies'], ['underseas-whale-singer'])
            self.assertTrue(any('does not require' in note for note in options['underseas-dolphin-pneuma-biform']['findings']))
            self.assertEqual(options['underseas-rurlel-warrior']['dependencies'], ['underseas-rurlel'])
            self.assertEqual(options['underseas-naut-yll-soldier']['dependencies'], ['underseas-naut-yll'])
            self.assertEqual(options['underseas-naut-yll-koral-shaper']['source']['pdf_pages'], [149])
            self.assertIn('Ocean Mage', options['underseas-ocean-wizard']['aliases'])
            self.assertEqual(options['underseas-horune-pirate']['source']['pdf_pages'], [163])
            self.assertEqual(options['underseas-salvage-expert']['source']['pdf_pages'], [132])
            self.assertIn('NPC', ' '.join(options['underseas-servants-of-the-deep']['findings']))
            for prefix in ('sa1-', 'underseas-'):
                for entry in options.values():
                    if entry['id'].startswith(prefix):
                        self.assertEqual(entry['mechanical_review'], 'pending')
                        self.assertEqual(entry['automation'], 'not-implemented')
            self.assertEqual(view['summary']['source_gaps'], 4)
            self.assertEqual(view['summary']['mechanically_reviewed'], 0)

    def test_coverage_distinguishes_confirmed_identities_from_mechanical_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            self.assertEqual(view['summary']['identity_confirmed'], 718)
            self.assertEqual(view['summary']['fully_automated'], 0)
            self.assertEqual(view['summary']['books_reviewed'], 0)
            vagabond = next(entry for entry in view['options'] if entry['id'] == 'rue-vagabond')
            self.assertEqual(vagabond['identity_review'], 'confirmed')
            self.assertEqual(vagabond['mechanical_review'], 'pending')
            self.assertEqual(vagabond['automation'], 'partial')
            self.assertEqual(vagabond['tickets'], ['05b-complete-rifts-skill-path'])
            self.assertTrue(vagabond['findings'])
            self.assertEqual(vagabond['source']['pdf_pages'], [46])

    def test_racial_variants_and_heroes_categories_keep_separate_source_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']:entry for entry in view['options']}
            self.assertEqual(options['rue-wild-psi-stalker']['dependencies'], ['rue-psi-stalker'])
            self.assertEqual(options['rue-civilized-psi-stalker']['source']['printed_pages'], [154])
            self.assertEqual(options['rue-flame-wind-hatchling']['dependencies'], ['rue-dragon-hatchling-rules'])
            self.assertEqual(options['rue-flame-wind-hatchling']['game'], 'rifts')
            self.assertEqual(options['hu2-experiment']['game'], 'heroes-unlimited')
            self.assertEqual(options['hu2-experiment']['kind'], 'power-category')
            self.assertEqual(options['hu2-experiment']['source']['pdf_pages'], [21])
            self.assertEqual(options['hu2-mega-hero']['kind'], 'rule')
            self.assertTrue(any('modifier' in finding for finding in options['hu2-mega-hero']['findings']))
            self.assertEqual(view['summary']['unassigned_options'], 717)
            self.assertEqual([pack['classes'][0]['id'] for pack in CharacterApplication(directory).catalog()['packs']], ['vagabond', 'mutant'])

    def test_heroes_named_paths_link_to_categories_and_shared_robot_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            view = CharacterApplication(directory).coverage()
            options = {entry['id']: entry for entry in view['options']}
            self.assertEqual(options['hu2-hardware-electrical']['dependencies'], ['hu2-hardware'])
            self.assertIn('Manhunter', options['hu2-special-hunter']['aliases'])
            self.assertEqual(options['hu2-robot-true']['source']['printed_pages'], [194, 196])
            self.assertIn('hu2-robot-vehicle', options['hu2-robot-exoskeleton']['dependencies'])
            self.assertIn('hu2-robot-construction', options['hu2-robot-android']['dependencies'])
            self.assertEqual(options['hu2-robot-construction']['kind'], 'construction')
            self.assertEqual(options['hu2-special-stage-magician']['automation'], 'not-implemented')
            self.assertEqual(options['hu2-hardware-super-vehicle']['mechanical_review'], 'pending')
            self.assertEqual(view['summary']['canonical_options'], 718)
            self.assertEqual(view['summary']['fully_automated'], 0)

    def test_dependency_links_cannot_join_games_or_reference_missing_entries(self):
        inventory, catalog = self.fixture()
        catalog['entries'][0]['dependencies'] = ['missing-option']
        with self.assertRaisesRegex(ValueError, 'dependency is missing'):
            SourceInventory.with_catalog(inventory, catalog)
        other = copy.deepcopy(catalog['entries'][0])
        other.update(id='hu-scout', book_id='hu', candidate_ids=['hu-candidate'], dependencies=['rue-scout'])
        catalog['entries'][0]['dependencies'] = []
        catalog['entries'].append(other)
        inventory['books'].append({'id':'hu','sha256':'md','pdf_sha256':'pdf','game':'heroes-unlimited'})
        inventory['candidates'].append({'id':'hu-candidate','book_id':'hu','source_sha256':'md'})
        with self.assertRaisesRegex(ValueError, 'own game'):
            SourceInventory.with_catalog(inventory, catalog)

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
