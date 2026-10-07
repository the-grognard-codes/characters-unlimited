"""Source minimums can qualify acquisition age and distinct specialties."""
import tempfile
import unittest
from characters_unlimited.application import CharacterApplication
from tests.test_owned_class_profiles import owned_pack, archive_with


class QualifiedSkillRequirementTests(unittest.TestCase):
    def fixture(self, mutation=None):
        pack = owned_pack()
        profile = pack['class_profiles']['vagabond']
        source = {'book':'Synthetic skill fixture','section':'Initial training and other languages'}
        profile['pools']['related']['requirements'] = [
            {'id':'initial-physical','name':'Initial Physical training','count':2,
             'selector':{'any_of':[{'ids':['athletics','running']}]},'before_level':2,'source':source},
            {'id':'other-languages','name':'Two distinct other languages','count':2,
             'selector':{'any_of':[{'ids':['language-other']}]},'counting':'distinct-specialties',
             'excluded_specialties':['American','Dragonese / Elven'],'source':source}]
        profile['selection_rules']['related']['physical'] = {'allow':'any','bonus':0}
        profile['selection_rules']['related']['communications'] = {'allow':'any','bonus':0}
        if mutation:
            mutation(profile['pools']['related']['requirements'])
        return archive_with(pack)

    def requirements(self, app, hero):
        return {row['id']:row for row in app.skill_view(hero['id'])['pool_requirements']}

    def test_late_physical_training_cannot_fill_initial_minimum(self):
        for initial in (True,False):
            with self.subTest(initial=initial),tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as copied:
                app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
                hero = app.create()
                choices = [{'skill_id':key,'pool':'related','specialty':''} for key in ('athletics','running')]
                if initial:
                    hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
                hero = app.generate_resources(hero['id'],revision=hero['revision'])
                hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
                if not initial:
                    hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
                self.assertEqual(self.requirements(app,hero)['initial-physical']['remaining'],0 if initial else 2)
                def no_roll(sides):
                    self.fail('Portable qualified minimums cannot reroll')
                other = CharacterApplication(copied,die=no_roll,rule_archive=self.fixture())
                restored = other.import_character(app.export_character(hero['id']))
                self.assertEqual(self.requirements(other,restored),self.requirements(app,hero))

    def test_specialty_exclusions_and_duplicates_remain_uncredited(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:3,rule_archive=self.fixture())
            hero = app.create()
            for specialties,remaining in [(['American',' Dragonese / Elven '],2),
                                           (['Spanish',' spanish '],1),(['Spanish','French'],0)]:
                choices = [{'skill_id':'language-other','pool':'related','specialty':name} for name in specialties]
                hero = app.select_skills(hero['id'],revision=hero['revision'],selections=choices)
                self.assertEqual(self.requirements(app,hero)['other-languages']['remaining'],remaining)

    def test_invalid_inactive_qualifiers_preflight_before_dice_or_save(self):
        mutations = [lambda rows:rows[0].update(before_level=True),lambda rows:rows[0].update(before_level=1),
                     lambda rows:rows[0].update(before_level=1001),lambda rows:rows[1].update(excluded_specialties=['Spanish',' spanish ']),
                     lambda rows:rows[1].update(excluded_specialties=[1]),lambda rows:rows[1].update(counting='distinct')]
        for mutation in mutations:
            with tempfile.TemporaryDirectory() as directory:
                def no_roll(sides):
                    self.fail('Invalid inactive qualification must preflight before dice')
                app = CharacterApplication(directory,die=no_roll,rule_archive=self.fixture(mutation))
                with self.assertRaises(ValueError):
                    app.create(character_class='city-rat')
                self.assertEqual(app.list(),[])
