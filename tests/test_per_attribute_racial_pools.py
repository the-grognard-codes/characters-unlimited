from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

class PerAttributeRacialPoolTests(unittest.TestCase):
    def test_mixed_racial_pools_replay_each_attribute_and_retained_class_bonus(self):
        installed=RuleArchive.load()
        core=installed.active('rifts-core')
        race=deepcopy(core['races'][0])
        race['id']='synthetic-mixed-pool-race'
        race['name']='Synthetic mixed-pool race (not book content)'
        race['attribute_pools']={
            'ME':{'count':4,'sides':6,'constant':6},
            'PS':{'count':2,'sides':8,'constant':1},
            'IQ':{'count':0,'sides':6,'constant':12}}
        core['races'].append(race)
        archive=RuleArchive([core if (row['id'],row['version'])==(core['id'],core['version']) else row
                            for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive)
            hero=app.create(race=race['id'],generation={'reroll_ones':True,'extra_die':True})
            self.assertEqual(hero['attributes']['ME']['base'],22)
            self.assertEqual(hero['attributes']['ME']['rolls'],[4]*5)
            self.assertEqual(hero['attributes']['ME']['bonus_rolls'],[])
            self.assertEqual(hero['attributes']['PS']['value'],10)
            self.assertEqual(hero['attributes']['IQ']['rolls'],[])
            receipt=deepcopy(hero['attributes']['PS']['modifiers'])
            app.die=lambda sides:2
            hero=app.reroll(hero['id'],revision=hero['revision'],attribute='PS')
            self.assertEqual(hero['attributes']['PS']['base'],5)
            self.assertEqual(hero['attributes']['PS']['modifiers'],receipt)
            restored=app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['attributes'],hero['attributes'])
            self.assertEqual(restored['roll_history'],hero['roll_history'])
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['ME']['/V'],'22')

    def test_complete_pool_map_needs_no_default_and_caps_keep_raw_values_and_manual_values(self):
        installed=RuleArchive.load()
        core=installed.active('heroes-core')
        race=core['races'][0]
        race.pop('attributes')
        race['attribute_pools']={name:{'count':1,'sides':6,'constant':2}
                                 for name in ('IQ','ME','MA','PS','PP','PE','PB','SPD')}
        race['attribute_caps']={'IQ':5}
        archive=RuleArchive([core if (row['id'],row['version'])==(core['id'],core['version']) else row
                            for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive)
            hero=app.create(game='heroes-unlimited')
            self.assertEqual(hero['attributes']['IQ']['base'],6)
            self.assertEqual(hero['attributes']['IQ']['value'],5)
            self.assertEqual(hero['attributes']['ME']['base'],6)
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=40)
            self.assertEqual(hero['attributes']['IQ']['value'],40)
            self.assertEqual(app.import_character(app.export_character(hero['id']))['attributes'],hero['attributes'])

    def test_invalid_unrolled_pool_or_cap_rejects_before_first_die(self):
        mutations=[
            lambda race:race.update(attribute_pools={'UNKNOWN':{'count':3,'sides':6}}),
            lambda race:race.update(attribute_pools={'SPD':{'count':True,'sides':6}}),
            lambda race:race.update(attribute_pools={'SPD':{'count':3,'sides':6,'expression':'execute'}}),
            lambda race:race.update(attribute_pools={'SPD':{'count':3,'sides':6,'exceptional':{'thresholds':[True],'max_bonus_dice':2}}}),
            lambda race:race.update(attribute_caps={'UNKNOWN':20}),
            lambda race:race.update(attribute_caps={'SPD':True}),
            lambda race:race.update(attribute_pools={'SPD':{'count':1,'sides':1}}),
            lambda race:race.pop('attributes'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                installed=RuleArchive.load()
                core=installed.active('rifts-core')
                mutation(core['races'][0])
                archive=RuleArchive([core if (row['id'],row['version'])==(core['id'],core['version']) else row
                                    for row in installed.definitions()],installed.active_versions())
                app=CharacterApplication(directory,die=lambda sides:self.fail('Invalid race must reject before dice'),rule_archive=archive)
                with self.assertRaises(ValueError):
                    app.create(generation={'reroll_ones':True})
                self.assertEqual(app.list(),[])

    def test_single_attribute_reroll_does_not_apply_options_to_other_pools(self):
        installed=RuleArchive.load()
        core=installed.active('rifts-core')
        core['races'][0]['attribute_pools']={'SPD':{'count':1,'sides':1}}
        archive=RuleArchive([core if (row['id'],row['version'])==(core['id'],core['version']) else row
                            for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:1 if sides==1 else 4,rule_archive=archive)
            hero=app.create()
            before=deepcopy(hero)
            app.die=lambda sides:self.fail('Whole-profile impossible options must reject before dice')
            with self.assertRaises(ValueError):
                app.reroll(hero['id'],revision=hero['revision'],generation={'reroll_ones':True})
            self.assertEqual(app.get(hero['id']),before)
            app.die=lambda sides:4
            hero=app.reroll(hero['id'],revision=hero['revision'],attribute='IQ',generation={'reroll_ones':True})
            self.assertEqual(hero['attributes']['SPD'],before['attributes']['SPD'])
            self.assertEqual(app.import_character(app.export_character(hero['id']))['attributes'],hero['attributes'])
