from copy import deepcopy
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

FIELDS = ('source', 'starting_funds', 'starting_gear', 'starting_choices', 'starting_groups')

def owned_equipment():
    pack = RuleArchive.load().active('rifts-equipment')
    default = {field: deepcopy(pack.get(field, {})) for field in FIELDS}
    city = {field: deepcopy(pack.get('class_profiles', {})['city-rat'].get(field, {})) for field in FIELDS}
    city['source'] = deepcopy(city['starting_gear']['source'])
    pack.update(class_profile_format='owned-v1', default_class='vagabond',
                class_profiles={'vagabond': default, 'city-rat': city})
    return pack

def archive_with(pack):
    archive = RuleArchive.load()
    return RuleArchive([pack if (row['id'], row['version']) == (pack['id'], pack['version']) else row
                        for row in archive.definitions()], archive.active_versions())

class OwnedEquipmentProfileTests(unittest.TestCase):
    def test_explicit_empty_profile_does_not_inherit_default_equipment(self):
        pack = owned_equipment()
        for field in FIELDS[1:]:
            pack['class_profiles']['vagabond'][field] = {}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4, rule_archive=archive_with(pack))
            hero = app.create()
            view = app.equipment_view(hero['id'])
            for field in FIELDS[1:]:
                self.assertFalse(view[field]['supported'])
            app.die = lambda sides:self.fail('No entitlement should draw money dice')
            with self.assertRaises(ValueError):
                app.generate_starting_funds(hero['id'], revision=0)
            self.assertEqual(app.get(hero['id']), hero)

    def test_malformed_unselected_equipment_rejects_before_initial_dice(self):
        pack = owned_equipment()
        pack['class_profiles']['city-rat']['starting_groups']['groups']['armor']['options'] = ['missing-item']
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:self.fail('Invalid import drew dice'),
                                       rule_archive=archive_with(pack))
            with self.assertRaisesRegex(ValueError, 'city-rat.*starting_groups'):
                app.create()
            self.assertEqual(app.list(), [])

    def test_book_class_grants_keep_exact_receipts_and_skill_values(self):
        pack = owned_equipment()
        # Owned classes must ignore even unusable root mechanics.
        pack['starting_funds'] = {'callback':'not a rule'}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4, rule_archive=archive_with(pack))
            for identity, credits in [('vagabond',800), ('city-rat',2400)]:
                with self.subTest(identity=identity):
                    hero = app.create(character_class=identity)
                    attributes = deepcopy(hero['attributes'])
                    skills = app.skill_view(hero['id'])
                    hero = app.generate_starting_funds(hero['id'], revision=0)
                    hero = app.grant_starting_gear(hero['id'], revision=hero['revision'])
                    self.assertEqual(hero['equipment']['credits'], credits)
                    self.assertEqual(hero['attributes'], attributes)
                    self.assertEqual(app.skill_view(hero['id']), skills)
                    if identity == 'city-rat':
                        self.assertFalse(app.equipment_view(hero['id'])['starting_choices']['supported'])
                        hero = app.grant_starting_group(hero['id'], revision=hero['revision'],
                                                       group_id='armor', selection='urban-warrior')
                    app.die = lambda sides:self.fail('Reopening rerolled starting equipment')
                    restored = app.import_character(app.export_character(hero['id']))
                    self.assertEqual(restored['starting_funds'], hero['starting_funds'])
                    self.assertEqual(restored['starting_gear'], hero['starting_gear'])
                    self.assertEqual(restored['equipment'], hero['equipment'])
                    self.assertEqual(app.equipment_view(restored['id']), app.equipment_view(hero['id']))
                    self.assertEqual(app.get(hero['id']), hero)
                    app.die = lambda sides:4

    def test_shared_catalog_and_choices_use_declared_owner_without_class_dispatch(self):
        pack = owned_equipment()
        city = pack['class_profiles']['city-rat']
        pack['profile_catalogs'] = {'common-groups': {'field':'starting_groups',
            'value':{'groups':deepcopy(city['starting_groups']['groups'])}, 'source':deepcopy(city['source'])}}
        city['starting_groups'] = {'catalog_ref':'common-groups', 'values':{'character_class':'city-rat'}}
        # Synthetic entitlement: not a claim that the book grants these choices to City Rat.
        city['starting_choices'] = deepcopy(pack['class_profiles']['vagabond']['starting_choices'])
        city['starting_choices']['character_class'] = 'city-rat'
        city['starting_choices']['source'] = {'book':'Synthetic ownership fixture', 'section':'Common choices'}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4, rule_archive=archive_with(pack))
            hero = app.create(character_class='city-rat')
            self.assertTrue(app.equipment_view(hero['id'])['starting_choices']['supported'])
            hero = app.grant_starting_choices(hero['id'], revision=0, choices={
                'armor':'plastic-man', 'gun':'wilks-320', 'knife':'knife-large',
                'transport':'vagabond-basic-horse'})
            self.assertEqual(len(hero['starting_choices']['grants']),5)
            self.assertEqual(hero['equipment']['credits'],0)
            hero = app.grant_starting_group(hero['id'], revision=hero['revision'],
                                            group_id='armor', selection='huntsman')
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['starting_choices'], hero['starting_choices'])
            self.assertEqual(restored['starting_equipment_groups'], hero['starting_equipment_groups'])

    def test_invalid_ownership_or_sources_reject_without_dice_or_save(self):
        for defect in ('missing','owner','source','reference','funds-boolean','funds-overflow','format'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as directory:
                pack = owned_equipment()
                city = pack['class_profiles']['city-rat']
                if defect == 'missing':
                    del city['starting_choices']
                elif defect == 'owner':
                    city['starting_funds']['character_class'] = 'vagabond'
                elif defect == 'source':
                    city['starting_funds']['definitions'][0]['source'] = {}
                elif defect == 'reference':
                    city['starting_gear'] = {'catalog_ref':'missing', 'values':{}}
                elif defect == 'funds-boolean':
                    city['starting_funds']['definitions'][0]['constant'] = True
                elif defect == 'funds-overflow':
                    city['starting_funds']['definitions'][0]['constant'] = 9007199254740991
                else:
                    pack['class_profile_format'] = 'unknown'
                app = CharacterApplication(directory, die=lambda sides:self.fail('Invalid import drew dice'),
                                           rule_archive=archive_with(pack))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(), [])

    def test_credits_only_constant_grant_uses_common_formula_without_dice(self):
        pack = owned_equipment()
        funds = pack['class_profiles']['vagabond']['starting_funds']
        definition = deepcopy(funds['definitions'][0])
        definition.update(count=0, sides=0, multiplier=1, constant=1500,
                          source={'book':'Synthetic ownership fixture', 'section':'Fixed starting credits'})
        funds['definitions'] = [definition]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4, rule_archive=archive_with(pack))
            hero = app.create(generation={'reroll_ones':True, 'extra_die':True})
            app.die = lambda sides:self.fail('Fixed funds must not draw dice')
            hero = app.generate_starting_funds(hero['id'], revision=0)
            self.assertEqual(hero['equipment']['credits'],1500)
            self.assertEqual(set(hero['starting_funds']),{'credits'})
            self.assertEqual(hero['starting_funds']['credits']['rolls'],[])
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['starting_funds'],hero['starting_funds'])
            self.assertEqual(app.equipment_view(restored['id'])['starting_funds']['funds'],hero['starting_funds'])

            from io import BytesIO
            from pypdf import PdfReader
            fields = PdfReader(BytesIO(app.export_pdf(restored['id']))).get_fields()
            assert fields is not None
            values = ' '.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('1500 credits',values)
            self.assertIn('Fixed starting credits',values)
            self.assertNotIn('saleable goods',values.lower())
