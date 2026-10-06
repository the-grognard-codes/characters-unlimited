import tempfile
import unittest
from copy import deepcopy
from io import BytesIO
from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication, SaveConflict
from characters_unlimited.rules import RuleArchive


class StartingChoicesWorkflowTests(unittest.TestCase):
    def test_free_choices_record_the_original_grant_and_cannot_regenerate_after_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides: 4)
            character = app.create()
            character = app.set_equipment(character['id'], revision=0,
                inventory={'credits': 500, 'items': []})
            choices = {'armor': 'plastic-man', 'gun': 'wilks-320',
                       'knife': 'knife-large', 'transport': 'vagabond-junker-car'}
            character = app.grant_starting_choices(character['id'], revision=character['revision'], choices=choices)
            self.assertEqual(character['equipment']['credits'], 500)
            self.assertEqual(len(character['equipment']['items']), 5)
            self.assertEqual(character['starting_choices']['choices'], choices)
            self.assertEqual(len(character['starting_choices']['grants']), 5)
            self.assertEqual(app.equipment_view(character['id'])['attacks'], [])
            inventory = deepcopy(character['equipment'])
            for item in inventory['items']: item['equipped'] = True
            character = app.set_equipment(character['id'], revision=character['revision'], inventory=inventory)
            view = app.equipment_view(character['id'])
            self.assertEqual(view['carried_weight_lbs'], 15)
            self.assertEqual(view['unknown_carried_weight_quantity'], 2)
            self.assertEqual(len(view['armor']), 1)
            self.assertEqual(len(view['attacks']), 1)
            self.assertEqual(len(view['melee_attacks']), 1)
            active_fields = PdfReader(BytesIO(app.export_pdf(character['id']))).get_fields()
            assert active_fields is not None
            self.assertEqual(active_fields['page1.cell437']['/V'], '-10')
            receipt = deepcopy(character['starting_choices'])
            character = app.set_equipment(character['id'], revision=character['revision'],
                inventory={'credits': 1234, 'items': []})
            with self.assertRaises(ValueError):
                app.grant_starting_choices(character['id'], revision=character['revision'], choices=choices)
            self.assertEqual(app.get(character['id']), character)
            self.assertEqual(CharacterApplication(directory).get(character['id'])['starting_choices'], receipt)
            imported = app.import_character(app.export_character(character['id']))
            self.assertEqual(imported['starting_choices'], receipt)
            self.assertTrue(app.equipment_view(imported['id'])['starting_choices']['generated'])
            fields = PdfReader(BytesIO(app.export_pdf(character['id']))).get_fields()
            assert fields is not None
            values = ' '.join(str(field.get('/V', '')) for field in fields.values())
            self.assertIn('Original free starting equipment choices', values)
            self.assertIn('junker', values)

    def test_old_pins_and_invalid_receipts_do_not_change_saved_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            old = CharacterApplication(directory, die=lambda sides: 4, rule_archive=RuleArchive(
                archive.definitions(), {**archive.active_versions(), 'rifts-equipment': '1.4.0'}))
            character = old.create()
            character = old.grant_starting_gear(character['id'], revision=0)
            choices = {'armor': 'plastic-man', 'gun': 'wilks-447',
                       'knife': 'knife-small', 'transport': 'vagabond-basic-horse'}
            current = CharacterApplication(directory)
            with self.assertRaises(ValueError):
                current.grant_starting_choices(character['id'], revision=character['revision'], choices=choices)
            preview = current.preview_rule_upgrade(character['id'])
            character = current.apply_rule_upgrade(character['id'], revision=character['revision'], token=preview['token'])['character']
            original = deepcopy(character)
            for invalid in [{}, {**choices, 'armor': 'wilks-320'}, {**choices, 'extra': 'knife-small'}]:
                with self.assertRaises(ValueError):
                    current.grant_starting_choices(character['id'], revision=character['revision'], choices=invalid)
                self.assertEqual(current.get(character['id']), original)
            with self.assertRaises(SaveConflict):
                current.grant_starting_choices(character['id'], revision=0, choices=choices)
            character = current.grant_starting_choices(character['id'], revision=character['revision'], choices=choices)
            self.assertEqual(character['starting_gear'], original['starting_gear'])
            for key, value in [('quantity', True), ('possession_id', 'invalid'), ('item_id', 'unknown')]:
                bundle = current.export_character(character['id'])
                bundle['character']['starting_choices']['grants'][0][key] = value
                with self.assertRaises(ValueError): current.import_character(bundle)
                self.assertEqual(current.get(character['id']), character)
            newer = archive.active('rifts-equipment'); newer['version'] = '99.0.0'
            newer['class_profiles']['vagabond']['starting_choices']['options']['gun'] = ['wilks-320']
            updated = CharacterApplication(directory, rule_archive=RuleArchive(
                [*archive.definitions(), newer], {**archive.active_versions(), 'rifts-equipment': '99.0.0'}))
            with self.assertRaises(ValueError): updated.preview_rule_upgrade(character['id'])
            self.assertEqual(updated.get(character['id']), character)
