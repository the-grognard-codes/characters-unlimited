import tempfile
import unittest
from characters_unlimited.application import CharacterApplication


class CommunicationsSkillWorkflowTests(unittest.TestCase):
    def test_public_speaking_adds_once_to_performance_without_a_class_bonus(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            app.select_skills(character['id'],revision=0,selections=[{'skill_id':'performance','pool':'related'},{'skill_id':'public-speaking','pool':'related'},{'skill_id':'public-speaking','pool':'secondary'}])
            view=app.skill_view(character['id'])
            self.assertEqual(view['selected'][0]['percentage'],35)
            self.assertEqual(view['selected'][0]['contributions']['public_speaking'],5)
            self.assertEqual(view['remaining']['related'],3)
            self.assertTrue(any('duplicate' in warning for warning in view['warnings']))

    def test_creative_writing_repetition_and_literacy_prerequisite(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            choices=[{'skill_id':'creative-writing','pool':'related'}]*3
            saved=app.select_skills(character['id'],revision=0,selections=choices)
            view=app.skill_view(saved['id'])
            self.assertEqual(view['selected'][0]['percentage'],35)
            self.assertEqual(view['selected'][0]['quality'],'professional')
            self.assertTrue(any('Literacy' in warning for warning in view['warnings']))
            self.assertTrue(any('repeated' in warning for warning in view['warnings']))
            choices.append({'skill_id':'literacy-native','pool':'related'})
            app.select_skills(saved['id'],revision=saved['revision'],selections=choices)
            self.assertFalse(any('missing prerequisite' in warning for warning in app.skill_view(saved['id'])['warnings']))

    def test_category_exceptions_and_granted_radio_prerequisite(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            choices=[{'skill_id':'electronic-countermeasures','pool':'related'},{'skill_id':'optic-systems','pool':'related'},{'skill_id':'tv-video','pool':'secondary'}]
            app.select_skills(character['id'],revision=0,selections=choices)
            view=app.skill_view(character['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[30,30,30])
            self.assertTrue(any('Optic Systems: not available' in warning for warning in view['warnings']))
            self.assertTrue(any('TV/Video: not available' in warning for warning in view['warnings']))
            self.assertFalse(any('missing prerequisite Radio' in warning for warning in view['warnings']))

    def test_conditional_checks_specialties_and_portable_reopening(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            choices=[{'skill_id':'cryptography','pool':'related'},{'skill_id':'sensory-equipment','pool':'secondary'},{'skill_id':'sign-language','pool':'related','specialty':'Military'},{'skill_id':'language-other','pool':'related','specialty':'Spanish'}]
            app.select_skills(character['id'],revision=0,selections=choices)
            view=app.skill_view(character['id'])
            self.assertEqual(view['selected'][0]['percentage'],25)
            self.assertEqual(view['selected'][0]['additional_checks'][0]['percentage'],-5)
            self.assertEqual(view['selected'][1]['additional_checks'][0]['percentage'],15)
            self.assertEqual(view['selected'][2]['specialty'],'Military')
            self.assertEqual(view['selected'][3]['percentage'],50)
            duplicate=app.import_character(app.export_character(character['id']))
            self.assertEqual(app.skill_view(duplicate['id'])['selected'],view['selected'])

    def test_selected_barter_and_unreviewed_laser_dependency_stay_explained(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            choices=[{'skill_id':'barter','pool':'related'},{'skill_id':'laser-communications','pool':'related'},{'skill_id':'surveillance','pool':'related'}]
            app.select_skills(character['id'],revision=0,selections=choices)
            view=app.skill_view(character['id'])
            self.assertEqual(view['selected'][0]['percentage'],56)  # required class16 + Eyeball10 + base30
            self.assertEqual(view['selected'][0]['contributions']['class_ability'],10)
            self.assertTrue(any('Electrical Engineer' in warning for warning in view['warnings']))
            self.assertTrue(any('Basic Electronics' in warning for warning in view['warnings']))
            self.assertTrue(any('already granted' in warning for warning in view['warnings']))

    def test_earlier_catalog_requires_explicit_update_and_caps_conditional_checks(self):
        from characters_unlimited.rules import RuleArchive
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            active=archive.active_versions(); active['rifts-domestic-skills']='1.5.0'
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),active))
            character=earlier.create()
            app=CharacterApplication(directory)
            self.assertNotIn('creative-writing',{row['id'] for row in app.skill_view(character['id'])['catalog']})
            preview=app.preview_rule_upgrade(character['id'])
            self.assertEqual(app.get(character['id'])['attributes'],character['attributes'])
            saved=app.apply_rule_upgrade(character['id'],revision=0,token=preview['token'])['character']
            self.assertIn('creative-writing',{row['id'] for row in app.skill_view(character['id'])['catalog']})
            saved=app.select_skills(saved['id'],revision=saved['revision'],selections=[{'skill_id':'cryptography','pool':'related'}])
            app.set_attribute(saved['id'],revision=saved['revision'],attribute='IQ',mode='fixed',value=1000)
            row=app.skill_view(saved['id'])['selected'][0]
            self.assertEqual(row['percentage'],98)
            self.assertEqual(row['additional_checks'][0]['percentage'],98)

    def test_optional_languages_warn_when_already_granted_and_retain_distinct_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            saved=app.select_required_skills(character['id'],revision=0,choices={'native_language':'American','other_languages':['Spanish','Dragonese']})
            saved=app.select_skills(saved['id'],revision=saved['revision'],selections=[{'skill_id':'language-other','pool':'related','specialty':'  spanish  '},{'skill_id':'language-other','pool':'secondary','specialty':'AMERICAN'},{'skill_id':'language-other','pool':'related','specialty':'Japanese'}])
            view=app.skill_view(saved['id'])
            self.assertEqual(len(view['selected']),3)
            self.assertEqual(view['remaining']['related'],3)
            self.assertEqual(view['remaining']['secondary'],7)
            warnings=[warning for warning in view['warnings'] if 'does not create another language' in warning]
            self.assertEqual(len(warnings),2)
            self.assertTrue(any('spanish' in warning for warning in warnings))
            self.assertFalse(any('Japanese' in warning for warning in warnings))
