from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

SOURCE = {'book':'Synthetic creation fixture', 'section':'Reviewed race/class pairings'}


def paired_core():
    core = RuleArchive.load().active('rifts-core')
    race = deepcopy(core['races'][0])
    race.update(id='synthetic-nonhuman', name='Synthetic nonhuman',
                source=deepcopy(SOURCE),
                attribute_pools={'SPD':{'count':2,'sides':6,'multiplier':10,'constant':33}})
    # This numerical expression is also used by Forest Runner Dragon Hatchlings.
    # The fixture's class pairing is synthetic, not a Dragon O.C.C. entitlement.
    race['attribute_sources'] = {'SPD':{'book':'Rifts - Ultimate Edition',
        'section':'Forest Runner Dragon Hatchling, Attributes'}}
    core['races'].append(race)
    core['creation_profile_format'] = 'paired-v1'
    core['creation_profiles'] = [
        {'race':'human','classes':[row['id'] for row in core['classes']],'source':deepcopy(SOURCE)},
        {'race':race['id'],'classes':['city-rat'],'source':deepcopy(SOURCE)}]
    return core


def archive_with(core):
    installed = RuleArchive.load()
    return RuleArchive([core if (row['id'],row['version']) == (core['id'],core['version']) else row
                        for row in installed.definitions()],installed.active_versions())


class CreationProfileTests(unittest.TestCase):
    def test_race_default_and_multiplied_pool_keep_class_receipts_and_exact_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4, rule_archive=archive_with(paired_core()))
            hero = app.create(race='synthetic-nonhuman', generation={'extra_die':True})
            self.assertEqual(hero['character_class'],'city-rat')
            # 2 retained D6 x10 +33, City Rat 1D6+1, and automatic Running 4D4.
            self.assertEqual(hero['attributes']['SPD']['base'],113)
            self.assertEqual(hero['attributes']['SPD']['value'],134)
            self.assertEqual(hero['attributes']['SPD']['kept'],[4,4])
            self.assertEqual(hero['attributes']['SPD']['discarded'],[4])
            self.assertEqual(hero['attributes']['SPD']['explanation']['formula'],'2D6 × 10+33')
            class_receipt = deepcopy(hero['attributes']['SPD']['modifiers'])
            skills = app.skill_view(hero['id'])
            hero = app.reroll(hero['id'],revision=hero['revision'],attribute='SPD')
            self.assertEqual(hero['attributes']['SPD']['modifiers'],class_receipt)
            self.assertEqual(app.skill_view(hero['id']),skills)
            app.die = lambda sides:self.fail('Portable replay must not draw dice')
            restored = app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['attributes'],hero['attributes'])
            self.assertEqual(restored['roll_history'],hero['roll_history'])
            fields = PdfReader(BytesIO(app.export_pdf(restored['id']))).get_fields()
            assert fields is not None
            self.assertEqual(fields['SPD']['/V'],'134')

    def test_incompatible_pair_rejects_before_dice_and_cannot_be_portably_forged(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:self.fail('Invalid pair drew dice'),
                                       rule_archive=archive_with(paired_core()))
            with self.assertRaisesRegex(ValueError,'compatible'):
                app.create(race='synthetic-nonhuman',character_class='vagabond')
            self.assertEqual(app.list(),[])
            app.die = lambda sides:4
            hero = app.create(character_class='vagabond')
            bundle = app.export_character(hero['id'])
            bundle['character']['race'] = 'synthetic-nonhuman'
            # Must reject the pair, even before checking the now-incompatible dice.
            with self.assertRaisesRegex(ValueError,'compatible'):
                app.import_character(bundle)
            self.assertEqual(len(app.list()),1)

    def test_all_unselected_profiles_and_core_formulas_preflight_before_dice(self):
        for defect in ('format','missing-race','duplicate','unknown-class','source','unreachable',
                       'unselected-pool','unselected-class','multiplier-bool','multiplier-overflow',
                       'exceptional-overflow','exceptional-unbounded'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as directory:
                core = paired_core()
                if defect == 'format': core['creation_profile_format'] = 'unknown'
                elif defect == 'missing-race': core['creation_profiles'].pop()
                elif defect == 'duplicate': core['creation_profiles'].append(deepcopy(core['creation_profiles'][0]))
                elif defect == 'unknown-class': core['creation_profiles'][1]['classes'] = ['missing']
                elif defect == 'source': core['creation_profiles'][1]['source'] = {}
                elif defect == 'unreachable':
                    for row in core['creation_profiles']: row['classes'] = ['vagabond']
                elif defect == 'unselected-pool': core['races'][1]['attribute_pools']['SPD']['sides'] = 0
                elif defect == 'unselected-class': core['classes'][1]['attribute_bonuses']['BAD'] = {'count':1,'sides':6}
                elif defect == 'multiplier-bool': core['races'][1]['attribute_pools']['SPD']['multiplier'] = True
                elif defect == 'multiplier-overflow':
                    core['races'][1]['attribute_pools']['SPD']['multiplier'] = 9007199254740991
                else:
                    core['races'][1]['attribute_pools']['SPD'] = {
                        'count':1,'sides':2,'multiplier':4503599627370495,
                        'exceptional':{'thresholds':[9007199254740990],
                                       'max_bonus_dice':None if defect == 'exceptional-unbounded' else 1}}
                app = CharacterApplication(directory,die=lambda sides:self.fail('Bad catalog drew dice'),
                                           rule_archive=archive_with(core))
                with self.assertRaises(ValueError): app.create()
                self.assertEqual(app.list(),[])

    def test_heroes_pairings_use_same_contract_and_legacy_cross_product_is_preserved(self):
        core = RuleArchive.load().active('heroes-core')
        core['creation_profile_format'] = 'paired-v1'
        core['creation_profiles'] = [{'race':'human','classes':[core['classes'][0]['id']],
                                     'source':deepcopy(SOURCE)}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(core))
            hero = app.create(game='heroes-unlimited')
            self.assertEqual(app.import_character(app.export_character(hero['id']))['attributes'],hero['attributes'])
        legacy = paired_core()
        del legacy['creation_profile_format']
        del legacy['creation_profiles']
        legacy['races'][1]['attribute_pools']['SPD'].pop('multiplier')
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(legacy))
            self.assertEqual(app.create(race='synthetic-nonhuman')['character_class'],'vagabond')
