"""Public mixed class-bonus/floor receipts without changing archived classes."""
from copy import deepcopy
import tempfile
import unittest

from characters_unlimited.application import CharacterApplication
from characters_unlimited.attribute_modifiers import attribute_value
from characters_unlimited.rules import RuleArchive


class ClassAttributeMinimumTests(unittest.TestCase):
    archive = staticmethod(RuleArchive.load)
    source = {'book':'Synthetic framework fixture','section':'Class minimum receipt contract'}

    def fixture(self,mutation=None):
        original = self.archive()
        core = original.active('rifts-core')
        core['version'] = 'class-minima-fixture'
        selected = next(row for row in core['classes'] if row['id'] == 'vagabond')
        selected['attribute_bonuses']['ME'] = {'count':1,'sides':4,'constant':0}
        selected['attribute_minima'] = {key:{'value':11,'source':deepcopy(self.source)} for key in ('ME','PE','IQ')}
        if mutation:
            mutation(core)
        return RuleArchive([*original.definitions(),core],{**original.active_versions(),'rifts-core':core['version']})

    def no_roll(self,sides):
        self.fail('Retained class minima and portable replay must not draw dice')

    def test_mixed_and_floor_only_totals_keep_original_dice_and_manual_ordering(self):
        draws = []
        def die(sides):
            draws.append(sides)
            return 1 if sides == 4 else 3
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=die,rule_archive=self.fixture())
            hero = app.create()
            self.assertEqual((draws.count(6),draws.count(4)),(24,2))
            self.assertEqual([hero['attributes'][key]['value'] for key in ('ME','PE','IQ')],[11,11,11])
            self.assertEqual([row['id'] for row in hero['attributes']['ME']['modifiers']],
                             ['class:vagabond','class-minimum:vagabond'])
            self.assertEqual(hero['attributes']['IQ']['modifiers'][0]['rolls'],[])
            retained = deepcopy(hero['attributes']['ME']['modifiers'])
            app.die = self.no_roll
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='ME',mode='adjustment',value=2)
            self.assertEqual(hero['attributes']['ME']['value'],13)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='ME',mode='fixed',value=9)
            self.assertEqual(hero['attributes']['ME']['value'],9)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='ME',mode='calculated')
            self.assertEqual(hero['attributes']['ME']['value'],11)
            self.assertEqual(hero['attributes']['ME']['modifiers'],retained)
            def racial_only(sides):
                self.assertEqual(sides,6)
                return 4
            app.die = racial_only
            hero = app.reroll(hero['id'],revision=hero['revision'],attribute='ME')
            self.assertEqual(hero['attributes']['ME']['value'],13)
            self.assertEqual(hero['attributes']['ME']['modifiers'],retained)

    def test_resources_partial_history_and_forged_floor_receipts_replay_exactly(self):
        with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
            archive = self.fixture()
            app = CharacterApplication(directory,die=lambda sides:1 if sides == 4 else 3,rule_archive=archive)
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'running','pool':'related','specialty':''}])
            self.assertEqual(hero['attributes']['PE']['value'],12)
            hero = app.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual(app.resource_view(hero['id'])['resources']['HP']['value'],15)
            snapshot = deepcopy(hero['resource_attribute_snapshot'])
            app.die = lambda sides:4
            hero = app.reroll(hero['id'],revision=hero['revision'],attribute='PE')
            self.assertEqual(hero['resource_attribute_snapshot'],snapshot)
            bundle = app.export_character(hero['id'])
            other = CharacterApplication(copied,die=self.no_roll,rule_archive=archive)
            restored = other.import_character(bundle)
            ignored = {'id','revision','updated_at','copied_from'}
            self.assertEqual({key:value for key,value in restored.items() if key not in ignored},
                             {key:value for key,value in hero.items() if key not in ignored})
            self.assertEqual(CharacterApplication(directory,die=self.no_roll,rule_archive=archive).get(hero['id']),hero)
            for location in ('attributes','resource_attribute_snapshot','history'):
                for fault in ('missing','duplicate','value','source','operation'):
                    with self.subTest(location=location,fault=fault):
                        tampered = deepcopy(bundle)
                        character = tampered['character']
                        record = (character['roll_history'][-1]['attributes']['PE'] if location == 'history'
                                  else character[location]['PE'])
                        floor = next(row for row in record['modifiers'] if row['id'].startswith('class-minimum:'))
                        if fault == 'missing':
                            record['modifiers'].remove(floor)
                        elif fault == 'duplicate':
                            record['modifiers'].append(deepcopy(floor))
                        elif fault == 'value':
                            floor['value'] = 12
                        elif fault == 'source':
                            floor['source']['section'] = 'Forged evidence'
                        else:
                            floor['operation'] = 'add'
                        record['value'] = attribute_value(record)
                        with self.assertRaises(ValueError):
                            other.import_character(tampered)
                        self.assertEqual(len(other.list()),1)

    def test_class_and_natural_psychic_snapshots_bind_the_same_minimum(self):
        def bind(core):
            selected = next(row for row in core['classes'] if row['id'] == 'vagabond')
            selected['ability_path'] = {'id':'rifts-operator-psionics','version':'1.0.0'}
        archive = self.fixture(bind)
        with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
            app = CharacterApplication(directory,die=lambda sides:1 if sides == 4 else 3,rule_archive=archive)
            hero = app.create()
            app.die = lambda sides:15 if sides == 100 else 2
            hero = app.select_psionics(hero['id'],revision=hero['revision'],roll=True)
            bundle = app.export_character(hero['id'])
            other = CharacterApplication(copied,die=self.no_roll,rule_archive=archive)
            restored = other.import_character(bundle)
            self.assertEqual(restored['class_psionics'],hero['class_psionics'])
            self.assertEqual(restored['psionics'],hero['psionics'])
            for path in ('class_psionics','psionics'):
                snapshot = hero[path]['resource_record']['resource_attribute_snapshot']
                self.assertEqual(snapshot['ME']['value'],11)
                self.assertTrue(any(row['id']=='class-minimum:vagabond' for row in snapshot['ME']['modifiers']))
                for fault in ('missing','duplicate','value','source','operation'):
                    with self.subTest(path=path,fault=fault):
                        tampered = deepcopy(bundle)
                        record = tampered['character'][path]['resource_record']['resource_attribute_snapshot']['ME']
                        floor = next(row for row in record['modifiers'] if row['id'].startswith('class-minimum:'))
                        if fault == 'missing':
                            record['modifiers'].remove(floor)
                        elif fault == 'duplicate':
                            record['modifiers'].append(deepcopy(floor))
                        elif fault == 'value':
                            floor['value'] = 12
                        elif fault == 'source':
                            floor['source']['section'] = 'Forged evidence'
                        else:
                            floor['operation'] = 'add'
                        record['value'] = attribute_value(record)
                        with self.assertRaises(ValueError):
                            other.import_character(tampered)
                        self.assertEqual(len(other.list()),1)

    def test_invalid_inactive_minima_reject_before_any_dice_or_save(self):
        mutations = [
            lambda row:row.update(value=True),lambda row:row.update(value=0),
            lambda row:row.update(value=1001),lambda row:row.update(source=None),
            lambda row:row.update(source={'book':'Fixture'}),lambda row:row.update(extra='unsupported')]
        for mutation in mutations:
            def mutate(core):
                inactive = next(row for row in core['classes'] if row['id'] != 'vagabond')
                inactive['attribute_minima'] = {'ME':{'value':11,'source':deepcopy(self.source)}}
                mutation(inactive['attribute_minima']['ME'])
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory,die=self.no_roll,rule_archive=self.fixture(mutate))
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(),[])

    def test_older_pin_rejects_injected_floor_without_changing_old_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.archive())
            hero = app.create()
            bundle = app.export_character(hero['id'])
            tampered = deepcopy(bundle)
            record = tampered['character']['attributes']['ME']
            record.setdefault('modifiers',[]).append({'id':'class-minimum:vagabond','value':11,'rolls':[],
                'operation':'minimum','source':deepcopy(self.source)})
            record['value'] = attribute_value(record)
            with self.assertRaises(ValueError):
                app.import_character(tampered)
            self.assertEqual(app.get(hero['id']),hero)
