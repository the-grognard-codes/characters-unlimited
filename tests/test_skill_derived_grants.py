from copy import deepcopy
from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.advancement import learning_key
from characters_unlimited.rules import RuleArchive
from characters_unlimited.recorded_formulas import MAX_INTEGER
from characters_unlimited.portability import export_bundle
from tests.test_owned_class_profiles import owned_pack, archive_with


def selections(*identities):
    return [{'skill_id': identifier, 'pool': 'related', 'specialty': ''} for identifier in identities]


class SkillDerivedGrantWorkflowTests(unittest.TestCase):
    def test_source_values_grant_once_and_optional_duplicates_use_highest_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            for path, auto in [('vagabond',40),('city-rat',45)]:
                hero = app.create(character_class=path)
                hero = app.select_skills(hero['id'],revision=0,selections=selections(
                    'vehicle-armorer','vehicle-armorer','basic-mechanics','automotive-mechanics'))
                view = app.skill_view(hero['id'])
                grant = next(row for row in view['grants'] if row['id']=='basic-mechanics')
                selected = {row['id']:row for row in view['selected']}
                self.assertEqual(grant['percentage'],50)
                self.assertEqual(len(grant['grant_origins']),1)
                self.assertEqual(grant['grant_origins'][0]['source']['pages'],[312,313])
                self.assertEqual([selected[key]['percentage'] for key in
                    ('vehicle-armorer','basic-mechanics','automotive-mechanics')],[30,50,auto])
                self.assertEqual(view['remaining']['related'],app.character_skill_pack(hero)['pools']['related']['count']-4)
                hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections('basic-mechanics','automotive-mechanics'))
                view = app.skill_view(hero['id'])
                self.assertFalse(any(row['id']=='basic-mechanics' for row in view['grants']))
                self.assertEqual([row['percentage'] for row in view['selected']], [35,30] if path=='vagabond' else [40,35])

    def test_grant_satisfies_prerequisite_and_secondary_exceptions_remain_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=0,selections=[
                {'skill_id':'vehicle-armorer','pool':'secondary'},
                *selections('math-basic','basic-electronics','electricity-generation')])
            view = app.skill_view(hero['id'])
            self.assertEqual(next(row for row in view['grants'] if row['id']=='basic-mechanics')['percentage'],50)
            self.assertFalse(any('Electricity Generation: missing prerequisite' in note for note in view['warnings']))
            self.assertTrue(any('Vehicle Armorer: not available in the secondary' in note for note in view['warnings']))

    def test_late_grant_age_progress_removal_reselection_and_portable_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(level=3)
            hero = app.select_skills(hero['id'],revision=0,selections=selections('vehicle-armorer'))
            key = learning_key('skill','basic-mechanics')
            self.assertEqual(hero['learning_levels'][key],3)
            self.assertEqual(next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='basic-mechanics')['percentage'],50)
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],35)
            self.assertEqual(next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='basic-mechanics')['percentage'],55)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual(hero['learning_levels'][key],3)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=selections('vehicle-armorer'))
            imported = app.import_character(app.export_character(hero['id']))
            reopened = CharacterApplication(directory)
            self.assertEqual(reopened.skill_view(imported['id'])['grants'],app.skill_view(hero['id'])['grants'])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            text = ' '.join(str(row.get('/V','')) for row in (fields or {}).values())
            self.assertIn('Basic Mechanics',text)
            self.assertIn('Vehicle Armorer',text)
            self.assertTrue(any(str(row.get('/V',''))=='55' for row in (fields or {}).values()))

    def test_explicit_earlier_parent_age_and_preexisting_target_age_survive_undo(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(level=3)
            hero = app.select_skills(hero['id'],revision=0,learned_level=1,selections=selections('vehicle-armorer'))
            self.assertEqual(hero['learning_levels'][learning_key('skill','basic-mechanics')],1)
            self.assertEqual(next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='basic-mechanics')['percentage'],60)
            other = app.create(level=3)
            other = app.select_skills(other['id'],revision=0,learned_level=2,selections=selections('basic-mechanics'))
            other = app.select_skills(other['id'],revision=other['revision'],selections=selections('vehicle-armorer'))
            self.assertEqual(other['learning_levels'][learning_key('skill','basic-mechanics')],2)
            self.assertEqual(next(row for row in app.skill_view(other['id'])['grants'] if row['id']=='basic-mechanics')['percentage'],55)
            other = app.advance(other['id'],revision=other['revision'],method='level',value=4)
            other = app.undo_advancement(other['id'],revision=other['revision'])['character']
            self.assertEqual(other['learning_levels'][learning_key('skill','basic-mechanics')],2)
            app.export_character(other['id'])

    def test_unknown_cycles_specialties_and_malformed_unselected_grants_reject_before_dice(self):
        base = owned_pack()
        for invalid in ('unknown','cycle','specialty','physical','bonus','source','fields'):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                pack = deepcopy(base)
                parent = next(row for row in pack['skills'] if row['id']=='vehicle-armorer')
                declaration = parent['granted_skills'][0]
                if invalid=='unknown': declaration['skill_id']='missing'
                if invalid=='cycle': declaration['skill_id']='vehicle-armorer'
                if invalid=='specialty': declaration['skill_id']='literacy-other'
                if invalid=='physical': declaration['skill_id']='running'
                if invalid=='bonus': declaration['bonus']=True
                if invalid=='source': declaration['source']={}
                if invalid=='fields': declaration['conditional']=True
                calls = []
                def die(sides):
                    calls.append(sides)
                    return 4
                app = CharacterApplication(directory,die=die,rule_archive=archive_with(pack))
                with self.assertRaisesRegex(ValueError,'Skill-derived grants'):
                    app.create()
                self.assertEqual(calls,[])
                self.assertEqual(app.list(),[])

    def test_chained_grants_use_shared_training_and_learning_rules(self):
        pack = owned_pack()
        basic = next(row for row in pack['skills'] if row['id']=='basic-mechanics')
        source = {'book':'Synthetic grant fixture','section':'Chained acquisition'}
        basic['granted_skills']=[{'skill_id':'automotive-mechanics','bonus':12,'source':source}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(pack))
            hero = app.create(level=3)
            hero = app.select_skills(hero['id'],revision=0,learned_level=2,selections=selections('vehicle-armorer'))
            grants = {row['id']:row for row in app.skill_view(hero['id'])['grants']}
            self.assertEqual(grants['basic-mechanics']['percentage'],55)
            self.assertEqual(grants['automotive-mechanics']['percentage'],52)
            self.assertEqual(hero['learning_levels'][learning_key('skill','automotive-mechanics')],2)
            app.export_character(hero['id'])
            # This fixture validates the engine, not an additional accepted source grant.
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertFalse(any(row['id']=='automotive-mechanics' for row in app.skill_view(hero['id'])['grants']))

    def test_existing_class_grant_and_optional_target_use_highest_training_once(self):
        pack = owned_pack()
        basic = deepcopy(next(row for row in pack['skills'] if row['id']=='basic-mechanics'))
        basic['class_bonus']=40
        pack['class_profiles']['vagabond']['required']['grants'].append(basic)
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(pack))
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=0,selections=selections('vehicle-armorer','basic-mechanics'))
            view = app.skill_view(hero['id'])
            self.assertEqual(next(row for row in view['grants'] if row['id']=='basic-mechanics')['percentage'],70)
            self.assertEqual(next(row for row in view['selected'] if row['id']=='basic-mechanics')['percentage'],70)
            self.assertEqual(sum(row['id']=='basic-mechanics' for row in view['grants']),1)

    def test_fixed_class_grant_receives_vehicle_armorer_synergy_once(self):
        pack = owned_pack()
        pack['class_profiles']['vagabond']['fixed_domestic_grants']=[{'id':'automotive-mechanics','bonus':5}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(pack))
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=0,selections=selections('vehicle-armorer','vehicle-armorer'))
            grant = next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='automotive-mechanics')
            self.assertEqual(grant['percentage'],40)
            self.assertEqual(grant['contributions']['vehicle_armorer'],10)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            self.assertEqual(next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='automotive-mechanics')['percentage'],30)
            app.export_character(hero['id'])

    def test_training_overflow_is_atomic_at_selection_and_portable_boundaries(self):
        pack = owned_pack()
        parent = next(row for row in pack['skills'] if row['id']=='vehicle-armorer')
        parent['granted_skills'][0]['bonus']=MAX_INTEGER-35
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(pack))
            hero = app.create(level=3)
            before = deepcopy(hero)
            with self.assertRaisesRegex(ValueError,'exact integer range'):
                app.select_skills(hero['id'],revision=0,learned_level=1,selections=selections('vehicle-armorer'))
            self.assertEqual(app.get(hero['id']),before)
            invalid = deepcopy(hero)
            invalid['skill_selections']=selections('vehicle-armorer')
            for identifier in ('vehicle-armorer','basic-mechanics'):
                invalid['learning_levels'][learning_key('skill',identifier)]=1
            with self.assertRaisesRegex(ValueError,'exact integer range'):
                export_bundle(invalid,app.rule_archive.definitions())
            bundle = app.export_character(hero['id'])
            bundle['character']=invalid
            with self.assertRaisesRegex(ValueError,'exact integer range'):
                app.import_character(bundle)
            self.assertEqual(app.list(),[before])

    def test_parent_and_additional_check_totals_reject_overflow_atomically(self):
        for additional in (False,True):
            with self.subTest(additional=additional), tempfile.TemporaryDirectory() as directory:
                pack = owned_pack()
                parent = next(row for row in pack['skills'] if row['id']=='vehicle-armorer')
                if additional:
                    parent['additional_checks']=[{'name':'Synthetic ordinary check','base':MAX_INTEGER-8}]
                else:
                    parent['base']=MAX_INTEGER-8
                app = CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(pack))
                hero = app.create(level=3)
                with self.assertRaisesRegex(ValueError,'exact integer range'):
                    app.select_skills(hero['id'],revision=0,learned_level=1,selections=selections('vehicle-armorer'))
                self.assertEqual(app.get(hero['id']),hero)

    def test_old_exact_pin_and_explicit_upgrade_preserve_selected_skills(self):
        archive = RuleArchive.load()
        old = RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.14.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero = earlier.create()
            earlier.select_skills(hero['id'],revision=0,selections=selections('basic-mechanics','automotive-mechanics'))
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.get(hero['id'])
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),99)
            preview = app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'],'2.28.0')
            hero = app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),208)
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[35,30])
            self.assertEqual(hero['skill_selections'],selections('basic-mechanics','automotive-mechanics'))
