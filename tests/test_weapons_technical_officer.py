"""Weapons MOS source counts, issued identities and modern training behavior."""
from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.advancement import learning_key


class WeaponsTechnicalOfficerTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)
    modern = ('rifles','shotgun','submachine-gun','heavy-military',
              'military-flamethrowers','harpoon-spear-gun','heavy-mega-damage')

    def app(self, directory):
        return CharacterApplication(directory,die=lambda sides:3,rule_archive=self.archive())

    def no_roll(self, sides):
        self.fail('Recorded acquisition, source issue and portability must not roll')

    def test_fixed_source_grants_distinct_four_modern_choices_and_related_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-weapons')
            grants = {row['id']:row['percentage'] for row in app.skill_view(hero['id'])['grants'] if 'percentage' in row}
            self.assertEqual([grants[key] for key in ('math-advanced','demolitions','demolitions-disposal')], [60,70,75])
            self.assertEqual(hero['attributes']['IQ']['value'],9)
            app.die = self.no_roll
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'basic','ancient':[], 'modern':['energy-pistol','energy-rifle','rifles','rifles']})
            self.assertEqual(app.combat_view(hero['id'])['remaining']['modern'],3)
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'basic','ancient':[], 'modern':list(self.modern[:4])})
            self.assertEqual(app.combat_view(hero['id'])['remaining']['modern'],0)
            self.assertEqual(app.combat_view(hero['id'])['related_cost'],0)
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'expert','ancient':['knife'], 'modern':list(self.modern[:5])})
            self.assertEqual(app.combat_view(hero['id'])['related_cost'],3)
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],0)
            styles = app.combat_view(hero['id'])['catalog']['hand_to_hand']
            self.assertEqual({row['id'] for row in styles}, {'basic','expert'})

    def test_source_progression_initial_and_later_ages_preserve_old_family_values(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-weapons')
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.advance(hero['id'],revision=hero['revision'],method='xp',value=4241)
            app.die = self.no_roll
            hero = app.select_combat(hero['id'],revision=hero['revision'],learned_level=1,choices={
                'hand_to_hand':'basic','ancient':[], 'modern':list(self.modern[:4])})
            shooting = {row['id']:row for row in app.combat_view(hero['id'])['shooting']}
            self.assertEqual([shooting[key]['single']['value'] for key in self.modern[:4]], [2,2,None,2])
            self.assertEqual(shooting['energy-pistol']['single']['value'],2)
            self.assertEqual(shooting['energy-rifle']['single']['value'],1)
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'basic','ancient':[], 'modern':[*self.modern[:4],'military-flamethrowers']})
            self.assertEqual(hero['learning_levels'][learning_key('weapon','rifles')],1)
            self.assertEqual(hero['learning_levels'][learning_key('weapon','military-flamethrowers')],3)
            shooting = {row['id']:row for row in app.combat_view(hero['id'])['shooting']}
            self.assertEqual(shooting['military-flamethrowers']['single']['value'],0)

    def test_all_seven_source_weapons_have_matching_issue_and_exact_no_roll_portability(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as copied:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-weapons')
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            app.die = self.no_roll
            hero = app.select_combat(hero['id'],revision=hero['revision'],choices={
                'hand_to_hand':'basic','ancient':[], 'modern':list(self.modern)})
            self.assertEqual(app.skill_view(hero['id'])['remaining']['related'],0)
            items = ('gaw-m16a2-20','wi-gl8-shotgun','gaw-smg-30','gaw-light-mg-200',
                     'merc-portable-flamethrower','nautyll-harpoon-20','cs-c27')
            groups = app.equipment_view(hero['id'])['starting_groups']['groups']
            elective = [row for row in groups if row['id'].startswith('elective-weapon-')]
            self.assertEqual(len(elective),7)
            for group,item in zip(elective,items):
                hero = app.grant_starting_group(hero['id'],revision=hero['revision'],group_id=group['id'],selection=item)
            inventory = {row['item_id']:row for row in hero['equipment']['items']}
            self.assertEqual([inventory[key]['shots'] for key in items], [20,60,30,200,None,20,10])
            self.assertEqual(inventory['cs-c27-canister']['quantity'],4)
            self.assertEqual(inventory['cs-c27-canister']['shots'],10)
            equipped = deepcopy(hero['equipment'])
            for possession in equipped['items']:
                if possession['item_id'] in ('gaw-smg-30','gaw-light-mg-200','gaw-m16a2-20'):
                    possession['equipped'] = True
            hero = app.set_equipment(hero['id'],revision=hero['revision'],inventory=equipped)
            view = app.equipment_view(hero['id'])
            self.assertEqual([row['item_id'] for row in view['attacks']], ['gaw-m16a2-20'])
            self.assertEqual(view['attacks'][0]['single']['value'],1)
            for name in ('GAW 9mm Submachine Gun','GAW .30 Caliber Light Machine-Gun'):
                self.assertTrue(any(name in note and 'burst fire only' in note for note in view['guidance']))
            self.assertEqual([row['shots'] for row in hero['equipment']['items']
                              if row['item_id'] in ('gaw-smg-30','gaw-light-mg-200')], [30,200])
            other = CharacterApplication(copied,die=self.no_roll,rule_archive=self.archive())
            restored = other.import_character(app.export_character(hero['id']))
            ignored = {'id','revision','updated_at','copied_from'}
            self.assertEqual({key:value for key,value in restored.items() if key not in ignored},
                             {key:value for key,value in hero.items() if key not in ignored})
            self.assertEqual(CharacterApplication(directory,die=self.no_roll,rule_archive=self.archive()).get(hero['id']), hero)
            self.assertNotIn('proficiency', next(row for row in app.equipment_view(hero['id'])['catalog']
                if row['id']=='merc-portable-flamethrower'))
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values = [str(row.get('/V','')) for row in fields.values()]
            smg_lines = [line for value in values for line in value.splitlines()
                         if 'Submachine' in line and ' - burst:' in line]
            self.assertTrue(smg_lines)
            self.assertFalse(any('single:' in line or 'aimed:' in line or 'wild:' in line for line in smg_lines))
            self.assertTrue(any('burst fire only' in value for value in values))

    def test_all_seven_original_progression_endpoints_and_source_xp_ceiling(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-weapons')
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            hero = app.advance(hero['id'],revision=hero['revision'],method='xp',value=329961)
            self.assertEqual(hero['level'],15)
            app.die = self.no_roll
            hero = app.select_combat(hero['id'],revision=hero['revision'],learned_level=1,choices={
                'hand_to_hand':'basic','ancient':[], 'modern':list(self.modern)})
            shooting = {row['id']:row for row in app.combat_view(hero['id'])['shooting']}
            self.assertEqual([shooting[key]['single']['contributions']['weapon_proficiency'] for key in self.modern], [7,5,6,5,4,5,5])
            smg = shooting['submachine-gun']
            self.assertTrue(smg['burst_only'])
            self.assertEqual(smg['burst']['value'],3)
            for context in ('single','aimed','wild'):
                self.assertIsNone(smg[context]['value'])
            self.assertEqual(shooting['energy-pistol']['single']['value'],8)
            self.assertEqual(shooting['energy-rifle']['single']['value'],7)
            self.assertEqual(shooting['heavy-military']['burst']['value'],2)
            self.assertEqual(shooting['heavy-military']['aimed']['value'],7)

    def test_declared_heavy_untrained_penalty_and_invalid_inactive_declarations_reject_before_dice(self):
        original = self.archive()
        with tempfile.TemporaryDirectory() as directory:
            app = self.app(directory)
            hero = app.create(character_class='coalition-technical-officer-weapons')
            shooting = {row['id']:row for row in app.combat_view(hero['id'])['shooting']}
            self.assertEqual(shooting['heavy-military']['burst']['value'],-5)
            self.assertEqual(shooting['handguns']['burst']['value'],-3)
            self.assertIsNone(shooting['heavy-military']['aimed']['value'])
        for invalid in (True, -5.0, '-5', 1, -1001):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                definitions = deepcopy(original.definitions())
                active_version = original.active_versions()['rifts-domestic-skills']
                pack = next(row for row in definitions if row['id']=='rifts-domestic-skills' and row['version']==active_version)
                modern = pack['class_profiles']['coalition-technical-officer-weapons']['combat']['modern']
                next(row for row in modern if row['id']=='heavy-military')['untrained_burst'] = invalid
                archive = RuleArchive(definitions, original.active_versions())
                app = CharacterApplication(directory,die=self.no_roll,rule_archive=archive)
                with self.assertRaisesRegex(ValueError,'Untrained burst'):
                    app.create(character_class='vagabond')
                self.assertEqual(app.list(), [])

    def test_invalid_inactive_burst_only_declarations_reject_before_dice(self):
        original = self.archive()
        invalid_values: tuple[object, ...] = (0, 1, 'true', None, [])
        for family in ('rifts-domestic-skills','rifts-equipment'):
            for invalid in invalid_values:
                with self.subTest(family=family, invalid=invalid), tempfile.TemporaryDirectory() as directory:
                    definitions = deepcopy(original.definitions())
                    version = original.active_versions()[family]
                    pack = next(row for row in definitions if row['id']==family and row['version']==version)
                    if family == 'rifts-domestic-skills':
                        rows = pack['class_profiles']['coalition-technical-officer-weapons']['combat']['modern']
                        row = next(row for row in rows if row['id']=='submachine-gun')
                    else:
                        row = next(row for row in pack['items'] if row['id']=='gaw-light-mg-200')
                    row['burst_only'] = invalid
                    archive = RuleArchive(definitions, original.active_versions())
                    app = CharacterApplication(directory,die=self.no_roll,rule_archive=archive)
                    with self.assertRaisesRegex(ValueError,'Burst-only'):
                        app.create(character_class='vagabond')
                    self.assertEqual(app.list(), [])

    def test_honor_system_energy_choices_retain_four_compatible_extra_clips(self):
        for weapon in ('wilks-320','wilks-447'):
            with self.subTest(weapon=weapon), tempfile.TemporaryDirectory() as directory:
                app = self.app(directory)
                hero = app.create(character_class='coalition-technical-officer-weapons')
                app.die = self.no_roll
                hero = app.grant_starting_group(hero['id'],revision=hero['revision'],
                                               group_id='elective-weapon-1',selection=weapon)
                inventory = {row['item_id']:row for row in hero['equipment']['items']}
                self.assertEqual(inventory['standard-e-clip']['quantity'],4)
                self.assertEqual(inventory['standard-e-clip']['shots'],20)
                view = app.equipment_view(hero['id'])
                group = next(row for row in view['starting_groups']['groups'] if row['id']=='elective-weapon-1')
                self.assertFalse(group['option_requirements'][weapon][0]['satisfied'])
                self.assertTrue(view['warnings'])
