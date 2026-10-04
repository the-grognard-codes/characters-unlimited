import tempfile
import unittest
from io import BytesIO

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication


class CityRatWorkflowTests(unittest.TestCase):
    def test_class_and_automatic_running_bonuses_are_distinct_from_vagabond(self):
        # City Rat p.88: SPD+D6+1, SDC+2D4; Running p.317: PE+1, SPD+4D4, SDC+D6.
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(character_class='city-rat')
            self.assertEqual({key:hero['attributes'][key]['value'] for key in ('MA','PS','PE','SPD')},
                             {'MA':12,'PS':12,'PE':13,'SPD':33})
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining'],{'related':10,'secondary':8})
            self.assertEqual(view['combat']['class_bonuses']['perception']['value'],3)
            self.assertEqual(view['combat']['saving_bonuses']['psionics']['contributions'].get('O.C.C.',0),0)
            self.assertEqual(len([item for item in view['grants'] if item['id']=='running']),1)
            self.assertEqual(next(item for item in view['grants'] if item['id']=='running')['quality'],'trained')
            self.assertNotIn('cook',[item['id'] for item in view['grants']])
            grants = {item['id']:item for item in view['grants']}
            self.assertEqual(grants['native-language']['percentage'],92)
            self.assertEqual(grants['literacy-native']['percentage'],55)
            self.assertEqual(grants['barter']['percentage'],49)
            self.assertEqual(grants['tailing']['percentage'],50)
            hero = app.generate_resources(hero['id'], revision=hero['revision'])
            resources = app.resource_view(hero['id'])['resources']
            self.assertEqual(resources['HP']['value'],17)
            self.assertEqual(resources['SDC']['value'],32)
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['OCC']['/V'],'City Rat')
            self.assertEqual(app.import_character(app.export_character(hero['id']))['physical_acquisitions'],hero['physical_acquisitions'])

    def test_class_choices_and_progression_use_city_rat_allowances(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(character_class='city-rat', level=3)
            hero = app.select_required_skills(hero['id'], revision=hero['revision'], choices={
                'native_language':'English','other_languages':['French'],'vehicle':'hovercycle'})
            hero = app.select_combat(hero['id'], revision=hero['revision'],
                choices={'hand_to_hand':'basic','ancient':['knife']}, learned_level=1)
            view = app.skill_view(hero['id'])
            self.assertEqual(view['remaining'],{'related':11,'secondary':9})
            self.assertTrue(all(value==0 for value in view['required_remaining'].values()))
            self.assertEqual(view['combat']['remaining'],{'proficiencies':0})
            self.assertEqual(next(item for item in view['grants'] if item['id']=='hovercycle')['percentage'],86)
            copy = app.import_character(app.export_character(hero['id']))
            self.assertEqual(copy['learning_levels'],hero['learning_levels'])
            hero = app.undo_advancement(hero['id'], revision=hero['revision'])['character']
            self.assertEqual(hero['level'],2)
            self.assertEqual(app.skill_view(hero['id'])['remaining'],{'related':11,'secondary':8})

    def test_optional_skills_do_not_inherit_vagabond_class_abilities(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(character_class='city-rat')
            hero = app.select_skills(hero['id'], revision=hero['revision'],
                selections=[{'skill_id':'barter','pool':'related'}])
            barter = app.skill_view(hero['id'])['selected'][0]
            self.assertEqual(barter['percentage'],44)  # base30 + Related10 + Math/Literacy4
            self.assertNotIn('class_ability',barter['contributions'])
            self.assertTrue(any('already granted' in item for item in app.skill_view(hero['id'])['warnings']))
