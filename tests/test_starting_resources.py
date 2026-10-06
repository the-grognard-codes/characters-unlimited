import tempfile
import unittest
from copy import deepcopy
from io import BytesIO

from pypdf import PdfReader

from characters_unlimited.application import CharacterApplication
from characters_unlimited.storage import SaveConflict
from characters_unlimited.rules import RuleArchive


class StartingResourceWorkflowTests(unittest.TestCase):
    def test_starting_resources_record_class_and_physical_dice_and_effective_pe(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(generation={'reroll_ones':True,'extra_die':True})
            self.assertFalse(app.resource_view(hero['id'])['generated'])
            hero = app.set_attribute(hero['id'],revision=0,attribute='PE',mode='fixed',value=20)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'athletics','pool':'related'}, {'skill_id':'body-building','pool':'related'}])
            calls: list[int] = []
            def resource_die(sides):
                calls.append(sides)
                return 1
            app.die = resource_die
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual(calls,[6]*5)
            view = app.resource_view(hero['id'])
            self.assertEqual(view['resources']['SDC']['value'],40)
            self.assertEqual(view['resources']['HP']['value'],21)
            combat = app.combat_view(hero['id'])
            self.assertEqual(combat['saving_bonuses']['psionics']['value'],1)
            self.assertEqual(combat['saving_bonuses']['possession']['value'],1)
            self.assertEqual(combat['saving_bonuses']['horror_factor']['value'],2)
            self.assertEqual(combat['class_bonuses']['perception']['value'],4)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.resource_view(imported['id']),view)
            self.assertEqual(CharacterApplication(directory).resource_view(hero['id']),view)
            self.assertEqual(calls,[6]*5)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='PE',mode='fixed',value=30)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],21)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],26)
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],21)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['HIT POINTS']['/V'],'21')
            self.assertIn('21',[field.get('/V') for field in fields.values()])
            self.assertIn('26',[field.get('/V') for field in fields.values()])

    def test_resource_edits_bad_dice_stale_requests_and_portable_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            for face in (True,0,7):
                app.die = lambda sides:face
                with self.assertRaises(ValueError):
                    app.generate_resources(hero['id'],revision=0)
                self.assertEqual(app.get(hero['id']),hero)
            app.die = lambda sides:4
            hero = app.generate_resources(hero['id'],revision=0)
            with self.assertRaises(ValueError):
                app.generate_resources(hero['id'],revision=hero['revision'])
            with self.assertRaises(SaveConflict):
                app.generate_resources(hero['id'],revision=0)
            hero = app.set_resource(hero['id'],revision=hero['revision'],resource='SDC',mode='adjustment',value=5)
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],43)
            hero = app.set_resource(hero['id'],revision=hero['revision'],resource='SDC',mode='fixed',value=100)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[{'skill_id':'body-building','pool':'related'}])
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],100)
            hero = app.set_resource(hero['id'],revision=hero['revision'],resource='SDC',mode='calculated')
            self.assertEqual(app.resource_view(hero['id'])['resources']['SDC']['value'],48)
            bundle = app.export_character(hero['id'])
            for mutate in ('die','pe','source'):
                bad = deepcopy(bundle)
                record = bad['character']
                if mutate == 'die':
                    record['resources']['SDC']['contributions'][0]['rolls'][0]=7
                elif mutate == 'pe':
                    record['resource_attribute_snapshot']['PE']['value']+=1
                else:
                    record['resources']['SDC']['contributions'][0]['source']['pages']=[287.0]
                with self.assertRaises(ValueError):
                    app.import_character(bad)
                self.assertEqual(app.get(hero['id']),hero)

    def test_older_pins_require_explicit_update_before_generating_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = RuleArchive.load()
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.0.0'}))
            hero = app.create()
            current = CharacterApplication(directory,die=lambda sides:4)
            self.assertFalse(current.resource_view(hero['id'])['supported'])
            with self.assertRaises(ValueError):
                current.generate_resources(hero['id'],revision=0)
            preview = current.preview_rule_upgrade(hero['id'])
            hero = current.apply_rule_upgrade(hero['id'],revision=0,token=preview['token'])['character']
            hero = current.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual(current.resource_view(hero['id'])['resources']['HP']['value'],18)
            self.assertEqual(current.resource_view(hero['id'])['resources']['SDC']['value'],38)

    def test_rerolls_and_compatible_updates_preserve_resource_snapshots_and_changed_rules_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            draws = iter([4,4,4,4,7])
            app.die = lambda sides:next(draws)
            with self.assertRaises(ValueError):
                app.generate_resources(hero['id'],revision=0)
            self.assertEqual(app.get(hero['id']),hero)
            app.die = lambda sides:4
            hero = app.generate_resources(hero['id'],revision=0)
            snapshot = deepcopy(hero['resource_attribute_snapshot'])
            hero = app.reroll(hero['id'],revision=hero['revision'],attribute='PE')
            self.assertEqual(hero['resource_attribute_snapshot'],snapshot)
            archive = RuleArchive.load()
            compatible = archive.active('rifts-domestic-skills')
            compatible['version']='99.1.0'
            next(skill for skill in compatible['skills'] if skill['id']=='cook')['base']+=1
            next(grant for grant in compatible['class_profiles']['wilderness-scout']['required']['grants'] if grant.get('catalog_skill_id')=='cook')['base']+=1
            newer = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),compatible],
                {**archive.active_versions(),'rifts-domestic-skills':'99.1.0'}))
            preview = newer.preview_rule_upgrade(hero['id'])
            updated = newer.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['resources'],hero['resources'])
            self.assertEqual(updated['resource_attribute_snapshot'],snapshot)
            correction = deepcopy(compatible)
            correction['version']='99.1.1'
            correction['class_profiles']['vagabond']['resources']['definitions'][0]['contributions'][0]['formula']['bonus']+=1
            changed = CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),compatible,correction],
                {**archive.active_versions(),'rifts-domestic-skills':'99.1.1'}))
            with self.assertRaisesRegex(ValueError,'Resource migration'):
                changed.preview_rule_upgrade(hero['id'])
            self.assertEqual(changed.get(hero['id']),updated)
            self.assertEqual(changed.import_character(changed.export_character(hero['id']))['resources'],updated['resources'])


if __name__ == '__main__':
    unittest.main()
