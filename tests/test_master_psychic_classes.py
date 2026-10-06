"""Source values for Human Burster and Mind Melter public workflows."""

from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class MasterPsychicClassTests(unittest.TestCase):
    def no_roll(self, sides):
        self.fail('Retained source choices must not reroll')

    def test_source_required_percentages_master_reserve_and_physical_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, math, street, languages in [('burster', 60, 30, ['Spanish']),
                    ('mind-melter', 65, 35, ['Spanish', 'French'])]:
                hero = app.create(character_class=identity)
                self.assertEqual({key: hero['attributes'][key]['value'] for key in ('IQ', 'ME', 'PS', 'PP')},
                                 {'IQ': 9, 'ME': 9, 'PS': 10, 'PP': 9})
                hero = app.select_required_skills(hero['id'], revision=hero['revision'], choices={
                    'native_language': 'English', 'other_languages': languages,
                    'pilot': ['automobile', 'airplane']})
                rows = {row['id']: row for row in app.skill_view(hero['id'])['grants']}
                self.assertEqual({key: rows[key]['percentage'] for key in
                    ('native-language', 'math-basic', 'streetwise', 'land-navigation', 'automobile', 'airplane')},
                    {'native-language': 98, 'math-basic': math, 'streetwise': street,
                     'land-navigation': 46, 'automobile': 70, 'airplane': 60})
                self.assertEqual(rows['other-language']['percentage'], 80)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                resources = app.resource_view(hero['id'])['resources']
                self.assertEqual((resources['SDC']['value'], resources['HP']['value']), (21, 12))
                psychic = app.psionic_view(hero['id'])
                self.assertEqual(psychic['effective']['save_target'], 10)
                self.assertEqual({key: row['value'] for key, row in psychic['effective']['resources'].items()},
                                 {'ISP': 99, 'PPE': 6})
                self.assertEqual(app.skill_view(hero['id'])['remaining'], {'related': 6, 'secondary': 6})

    def test_known_grants_catalog_and_cumulative_burster_weighted_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            hero = app.create(character_class='burster')
            view = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual((len(view['catalog']), len(view['known_abilities'])), (24, 7))
            self.assertEqual(view['learning_awards']['remaining'], 3)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'],
                                            selections=['empathy', 'telepathy'])
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'],
                selections=['empathy', 'telepathy', 'psychic-body-field'])
            view = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual([row['credited'] for row in view['learning_awards']['awards']], [3, 1])
            self.assertEqual(view['learning_awards']['unallocated'], {})
            self.assertEqual(hero['class_psionics']['learning_levels']['psychic-body-field'], 3)
            app.die = self.no_roll
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=[])
            self.assertEqual(len(hero['class_psionics']['abilities']['selections']), 7)
            self.assertEqual(app.import_character(app.export_character(hero['id']))['class_psionics'], hero['class_psionics'])

    def test_mind_melter_known_powers_and_original_learning_tier_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            hero = app.create(character_class='mind-melter')
            initial = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual(len(initial['catalog']), 85)
            self.assertEqual(sum('Super' in row['tags'] for row in initial['catalog']), 29)
            self.assertEqual(set(initial['known_abilities']), {'alter-aura', 'mind-block', 'see-aura', 'sixth-sense'})
            self.assertEqual(initial['learning_awards']['remaining'], 12)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['mind-wipe'])
            self.assertTrue(any('source minimum learning level 3' in row
                for row in app.psionic_view(hero['id'])['class_entitlement']['guidance']))
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=3)
            view = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual(sum(row['count'] for row in view['learning_awards']['awards']), 20)
            self.assertTrue(any('source minimum learning level 3' in row for row in view['guidance']))
            self.assertEqual(view['resources']['ISP']['value'], 119)
            self.assertEqual(view['resources']['PPE']['value'], 6)
            self.assertEqual(hero['class_psionics']['learning_levels']['mind-wipe'], 1)

    def test_source_advancement_skill_awards_xp_and_horror_milestones(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, xp, horror, power_count in [('burster', 8251, 3, 4), ('mind-melter', 8961, 3, 22)]:
                hero = app.create(character_class=identity)
                hero = app.generate_resources(hero['id'], revision=hero['revision'])
                hero = app.advance(hero['id'], revision=hero['revision'], method='level', value=4)
                self.assertEqual(hero['experience'], xp)
                self.assertEqual(app.skill_view(hero['id'])['remaining'], {'related': 7, 'secondary': 8})
                psychic = app.psionic_view(hero['id'])['class_entitlement']
                self.assertEqual(sum(row['count'] for row in psychic['learning_awards']['awards']), power_count)
                self.assertEqual(psychic['resources']['ISP']['value'], 129)
                self.assertEqual(app.combat_view(hero['id'])['saving_bonuses']['horror_factor']['value'], horror)
                app.die = self.no_roll
                restored = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
                self.assertEqual(restored['level'], 3)
                self.assertEqual(app.psionic_view(restored['id'])['class_entitlement']['resources']['ISP']['value'], 119)
                app.die = lambda sides: 3

    def test_source_equipment_funds_and_exact_editable_portable_output(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, goods, kit in [('burster', 12000, 8), ('mind-melter', 6000, 9)]:
                hero = app.create(character_class=identity)
                hero = app.generate_starting_funds(hero['id'], revision=hero['revision'])
                self.assertEqual(hero['equipment']['credits'], 1200)
                self.assertEqual(hero['starting_funds']['saleable_goods']['value'], goods)
                hero = app.grant_starting_gear(hero['id'], revision=hero['revision'])
                self.assertEqual(len(hero['starting_gear']['grants']), kit)
                if identity == 'mind-melter':
                    hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='knife', selection='knife-large')
                hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='armor', selection='plastic-man')
                hero = app.grant_starting_group(hero['id'], revision=hero['revision'], group_id='transport',
                                               selection=identity+'-car')
                app.die = self.no_roll
                imported = app.import_character(app.export_character(hero['id']))
                self.assertEqual(imported['equipment'], hero['equipment'])
                self.assertEqual(CharacterApplication(directory).psionic_view(imported['id']), app.psionic_view(hero['id']))
                fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
                assert fields is not None
                text = ' '.join(str(row.get('/V', '')) for row in fields.values())
                self.assertIn('Always known class grant', text)
                self.assertIn('Learned at level 1', text)
                app.die = lambda sides: 3

    def test_inactive_source_learning_corruption_fails_before_acquisition_dice(self):
        archive = RuleArchive.load()
        pack = archive.active('rifts-burster-psionics')
        pack['version'] = 'bad-source-witness'
        pack['paths'][0]['allowances']['class']['costs']['telepathy'] = 0
        core = archive.active('rifts-core')
        core['version'] = 'bad-source-witness'
        next(row for row in core['classes'] if row['id'] == 'burster')['ability_path']['version'] = pack['version']
        active = archive.active_versions()
        active[core['id']] = core['version']
        broken = RuleArchive([*archive.definitions(), core, pack], active)
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=self.no_roll, rule_archive=broken)
            with self.assertRaises(ValueError):
                app.create(character_class='burster')
            with self.assertRaises(ValueError):
                app.catalog()
            self.assertEqual(app.list(), [])

    def test_source_related_category_bonuses_and_shared_weapon_allowance_cost(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            hero = app.create(character_class='mind-melter')
            hero = app.select_skills(hero['id'], revision=hero['revision'], selections=[
                {'skill_id': key, 'pool': 'related'} for key in
                ('math-advanced', 'seduction', 'pick-pockets', 'field-armorer', 'submersible')])
            rows = {row['id']: row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual({key: row['percentage'] for key, row in rows.items()},
                {'math-advanced': 60, 'seduction': 30, 'pick-pockets': 27, 'field-armorer': 40, 'submersible': 45})
            for style, choices, cost in [('basic', ['knife'], 0), ('expert', ['knife'], 1),
                                        ('basic', ['knife', 'sword'], 1), ('martial-arts', ['knife', 'sword'], 3)]:
                hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                    'hand_to_hand': style, 'ancient': choices, 'modern': []})
                self.assertEqual(app.combat_view(hero['id'])['related_cost'], cost)
            # Duplicate entries do not spend another skill or multiply training.
            hero = app.select_combat(hero['id'], revision=hero['revision'], choices={
                'hand_to_hand': 'basic', 'ancient': ['knife', 'knife'], 'modern': []})
            self.assertEqual(app.combat_view(hero['id'])['related_cost'], 0)

    def test_higher_creation_retains_full_source_awards_and_master_growth(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            hero = app.create(character_class='mind-melter', level=15)
            psychic = app.psionic_view(hero['id'])['class_entitlement']
            self.assertEqual(sum(row['count'] for row in psychic['learning_awards']['awards']), 44)
            self.assertEqual(psychic['resources']['ISP']['value'], 239)
            self.assertEqual(psychic['resources']['PPE']['value'], 6)
            self.assertEqual(app.skill_view(hero['id'])['remaining'], {'related': 9, 'secondary': 14})
            self.assertEqual(app.combat_view(hero['id'])['saving_bonuses']['horror_factor']['value'], 10)
            hero = app.select_class_psionics(hero['id'], revision=hero['revision'], selections=['psi-sword'])
            self.assertEqual(hero['class_psionics']['learning_levels']['psi-sword'], 15)
            app.die = self.no_roll
            self.assertEqual(app.import_character(app.export_character(hero['id']))['class_psionics'], hero['class_psionics'])

    def test_assassin_thrown_strike_and_training_keep_class_source(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 3)
            for identity, page, name in [('burster', 142, 'Burster'), ('mind-melter', 151, 'Mind Melter')]:
                with self.subTest(character_class=identity):
                    hero = app.create(character_class=identity, level=5)
                    hero = app.select_combat(hero['id'], revision=hero['revision'], learned_level=1,
                        choices={'hand_to_hand': 'assassin', 'ancient': ['knife'], 'modern': []})
                    view = app.combat_view(hero['id'])
                    self.assertEqual(view['totals']['thrown_strike']['value'], 2)
                    knife = next(row for row in view['melee'] if row['id'] == 'knife')
                    self.assertEqual(knife['thrown']['value'], 4)
                    sources = view['totals']['thrown_strike']['sources']
                    self.assertEqual(sum(row.get('pages') == [page] for row in sources), 1)
                    pack = app.character_skill_pack(hero)
                    for style in pack['combat']['hand_to_hand']:
                        self.assertEqual(style['source']['pages'][0], page)
                        self.assertEqual(style['source']['pdf_pages'][0], page + 3)
                        self.assertTrue(style['source']['section'].startswith(name + ' Hand to Hand'))
