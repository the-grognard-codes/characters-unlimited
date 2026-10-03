import tempfile
import unittest
from characters_unlimited.application import CharacterApplication


class ClassAttributeWorkflowTests(unittest.TestCase):
    def test_vagabond_bonuses_are_recorded_separately_and_drive_combat(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            self.assertEqual(character['attributes']['MA']['value'],16)
            self.assertEqual(character['attributes']['PS']['value'],13)
            self.assertEqual(character['attributes']['PE']['value'],14)
            self.assertEqual(character['attributes']['MA']['base'],12)
            self.assertEqual(character['attributes']['MA']['modifiers'][0]['rolls'],[4])
            self.assertEqual(character['attributes']['PS']['modifiers'][0]['rolls'],[])
            self.assertEqual(app.get(character['id'])['attributes'],character['attributes'])

    def test_fixed_and_additive_edits_and_rerolls_preserve_class_roll(self):
        with tempfile.TemporaryDirectory() as directory:
            draw=[4]
            app=CharacterApplication(directory,die=lambda sides:draw[0])
            character=app.create()
            character=app.set_attribute(character['id'],revision=0,attribute='MA',mode='adjustment',value=2)
            self.assertEqual(character['attributes']['MA']['value'],18)
            character=app.set_attribute(character['id'],revision=character['revision'],attribute='MA',mode='fixed',value=21)
            draw[0]=3
            character=app.reroll(character['id'],revision=character['revision'],attribute='MA')
            self.assertEqual(character['attributes']['MA']['value'],21)
            self.assertEqual(character['attributes']['MA']['modifiers'][0]['rolls'],[4])
            character=app.set_attribute(character['id'],revision=character['revision'],attribute='MA',mode='calculated')
            self.assertEqual(character['attributes']['MA']['value'],13)
            exported=app.export_character(character['id'])
            reopened=app.import_character(exported)
            self.assertEqual(reopened['attributes'],character['attributes'])

    def test_class_dice_ignore_racial_house_rules_and_reject_tampered_portable_modifiers(self):
        from copy import deepcopy
        with tempfile.TemporaryDirectory() as directory:
            calls=[]
            def die(sides):
                calls.append(sides)
                return 1 if sides==4 else 4
            app=CharacterApplication(directory,die=die)
            character=app.create(generation={'reroll_ones':True,'extra_die':True})
            self.assertEqual(calls.count(4),1)
            self.assertEqual(character['attributes']['MA']['value'],13)
            exported=app.export_character(character['id'])
            for mutation in ('missing','extra','roll','source'):
                bundle=deepcopy(exported)
                record=bundle['character']['attributes']['MA']
                if mutation=='missing': record['modifiers']=[]
                elif mutation=='extra': record['modifiers']*=2
                elif mutation=='roll': record['modifiers'][0]['rolls']=[5]
                else: record['modifiers'][0]['source']['pages']=[98]
                record['value']=record['base']+sum(item['value'] for item in record['modifiers'])
                with self.assertRaises(ValueError): app.import_character(bundle)
            self.assertEqual(len(app.list()),1)

    def test_earlier_primary_rules_reopen_without_silent_class_bonuses(self):
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            active=archive.active_versions()
            active['rifts-core']='1.0.0'
            active['rifts-domestic-skills']='1.4.0'
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),active))
            character=earlier.create()
            reopened=CharacterApplication(directory,die=lambda sides:4).get(character['id'])
            self.assertEqual(reopened['rules']['version'],'1.0.0')
            self.assertEqual(reopened['attributes']['MA']['value'],12)
            self.assertEqual(reopened['attributes']['PS']['value'],12)
            self.assertNotIn('modifiers',reopened['attributes']['MA'])
            self.assertTrue(any('class attribute bonuses' in gap for gap in CharacterApplication(directory).combat_view(character['id'])['gaps']))
            self.assertEqual(earlier.import_character(earlier.export_character(character['id']))['attributes'],character['attributes'])

    def test_class_strength_drives_damage_and_bad_class_die_saves_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:sides)
            character=app.create()
            self.assertEqual(character['attributes']['PS']['value'],31)
            self.assertEqual(app.combat_view(character['id'])['totals']['damage']['value'],16)
            self.assertFalse(any('class attribute bonuses' in gap.lower() for gap in app.combat_view(character['id'])['gaps']))
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:5 if sides==4 else 4)
            with self.assertRaises(ValueError): app.create()
            self.assertEqual(app.list(),[])
