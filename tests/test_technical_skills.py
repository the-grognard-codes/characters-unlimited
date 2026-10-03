import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class TechnicalSkillWorkflowTests(unittest.TestCase):
    def test_research_applies_once_to_both_history_checks_and_law(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            app.select_skills(character['id'], revision=0, selections=[
                {'skill_id':'research','pool':'related'},
                {'skill_id':'research','pool':'secondary'},
                {'skill_id':'law','pool':'related'},
                {'skill_id':'history-pre','pool':'related','specialty':'North America'},
                {'skill_id':'history-post','pool':'secondary','specialty':'Coalition'}])
            skills = {skill['id']:skill for skill in app.skill_view(character['id'])['selected']}
            self.assertEqual(skills['law']['percentage'],45)
            self.assertEqual(skills['history-pre']['percentage'],42)
            self.assertEqual(skills['history-pre']['additional_checks'][0]['percentage'],34)
            self.assertEqual(skills['history-post']['percentage'],40)
            self.assertEqual(skills['history-post']['additional_checks'][0]['percentage'],35)
            self.assertEqual(skills['law']['contributions']['research'],5)

    def test_blank_literacy_does_not_satisfy_computer_prerequisites(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            character = app.create()
            selections=[{'skill_id':'literacy-other','pool':'secondary','specialty':''},
                        {'skill_id':'computer-operation','pool':'related'},
                        {'skill_id':'computer-programming','pool':'related'}]
            app.select_skills(character['id'],revision=0,selections=selections)
            view=app.skill_view(character['id'])
            self.assertTrue(any('Computer Programming' in warning and 'prerequisite' in warning for warning in view['warnings']))
            selections[0]['specialty']='Dragonese'
            app.select_skills(character['id'],revision=1,selections=selections)
            self.assertFalse(app.skill_view(character['id'])['warnings'])

    def test_art_quality_and_history_specialties_survive_portable_reopening(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as other:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            app.select_skills(character['id'],revision=0,selections=[
                {'skill_id':'art','pool':'related'}, {'skill_id':'art','pool':'secondary'},
                {'skill_id':'history-pre','pool':'secondary','specialty':' Military history '}])
            reopened=CharacterApplication(other)
            imported=reopened.import_character(app.export_character(character['id']))
            skills=reopened.skill_view(imported['id'])['selected']
            self.assertEqual([(skill['percentage'],skill['quality']) for skill in skills[:2]],[(40,'professional'),(35,'amateur')])
            self.assertEqual(skills[2]['specialty'],'Military history')
            self.assertEqual(skills[2]['additional_checks'][0]['percentage'],24)

    def test_secondary_history_checks_are_capped_and_included_in_upgrade_preview(self):
        archive=RuleArchive.load()
        corrected=archive.resolve('rifts-domestic-skills','1.4.0')
        corrected['version']='1.4.1'
        definition=next(skill for skill in corrected['skills'] if skill['id']=='history-pre')
        definition['additional_checks'][0]['base']=27
        active=archive.active_versions()
        active['rifts-domestic-skills']='1.4.1'
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            app.select_skills(character['id'],revision=0,selections=[
                {'skill_id':'history-pre','pool':'secondary','specialty':'North America'}])
            later=CharacterApplication(directory,rule_archive=RuleArchive([*archive.definitions(),corrected],active))
            preview=later.preview_rule_upgrade(character['id'])
            check=next(row for row in preview['skills'] if 'Specific region or subject' in row['name'])
            self.assertEqual((check['before'],check['after']),(24,27))
            app.set_attribute(character['id'],revision=1,attribute='IQ',mode='fixed',value=300)
            skill=app.skill_view(character['id'])['selected'][0]
            self.assertEqual((skill['percentage'],skill['additional_checks'][0]['percentage']),(98,98))
            self.assertEqual(skill['additional_checks'][0]['uncapped_percentage'],148)

    def test_earlier_rules_keep_their_catalog_until_explicit_upgrade(self):
        archive=RuleArchive.load()
        active=archive.active_versions()
        active['rifts-domestic-skills']='1.3.0'
        with tempfile.TemporaryDirectory() as directory:
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(archive.definitions(),active))
            character=earlier.create()
            current=CharacterApplication(directory)
            self.assertEqual(len(current.skill_view(character['id'])['catalog']),18)
            preview=current.preview_rule_upgrade(character['id'])
            upgraded=current.apply_rule_upgrade(character['id'],revision=0,token=preview['token'])['character']
            self.assertEqual(len(current.skill_view(upgraded['id'])['catalog']),72)
            self.assertEqual(upgraded['attributes'],character['attributes'])

    def test_ineligible_art_pool_does_not_claim_professional_quality(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            character=app.create()
            app.select_skills(character['id'],revision=0,selections=[{'skill_id':'art','pool':'domestic'}])
            view=app.skill_view(character['id'])
            self.assertEqual((view['selected'][0]['percentage'],view['selected'][0]['quality']),(35,'trained'))
            self.assertTrue(any('Art' in warning and 'domestic' in warning for warning in view['warnings']))
