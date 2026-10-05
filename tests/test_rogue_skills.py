from copy import deepcopy
from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive
from characters_unlimited.recorded_formulas import MAX_INTEGER
from characters_unlimited.portability import export_bundle
from tests.test_owned_class_profiles import owned_pack, archive_with


class RogueSkillWorkflowTests(unittest.TestCase):
    def test_fixed_grants_receive_attribute_contributions(self):
        pack = owned_pack()
        pack['class_profiles']['vagabond']['fixed_domestic_grants'] = [{'id':'seduction','bonus':4}]
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4, rule_archive=archive_with(pack))
            hero = app.create()
            for attribute,value in [('MA',24),('PB',23)]:
                hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute=attribute,mode='fixed',value=value)
            grant = next(row for row in app.skill_view(hero['id'])['grants'] if row['id']=='seduction')
            self.assertEqual(grant['contributions']['Attribute: M.A. attraction'],4)
            self.assertEqual(grant['contributions']['Attribute: P.B. attraction'],3)
            self.assertEqual(grant['percentage'],31)

    def test_attribute_bonus_overflow_rejects_before_save_or_portable_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            hero = app.select_skills(hero['id'],revision=0,selections=[{'skill_id':'seduction','pool':'related'}])
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='MA',mode='fixed',value=MAX_INTEGER-100)
            before = deepcopy(hero)
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                app.set_attribute(hero['id'],revision=hero['revision'],attribute='PB',mode='fixed',value=MAX_INTEGER-100)
            self.assertEqual(app.get(hero['id']),before)
            invalid = deepcopy(hero)
            invalid['attributes']['PB']['fixed'] = MAX_INTEGER-100
            invalid['attributes']['PB']['value'] = MAX_INTEGER-100
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                export_bundle(invalid, app.rule_archive.definitions())
            bundle = app.export_character(hero['id'])
            bundle['character'] = invalid
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                app.import_character(bundle)
            self.assertEqual(app.list(),[before])

    def test_attribute_bonus_overflow_rejects_learning_after_attribute_edits(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            for attribute in ('MA','PB'):
                hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute=attribute,mode='fixed',value=MAX_INTEGER-100)
            before = deepcopy(hero)
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                app.select_skills(hero['id'],revision=hero['revision'],selections=[{'skill_id':'seduction','pool':'related'}])
            self.assertEqual(app.get(hero['id']),before)
            self.assertFalse(app.skill_view(hero['id'])['selected'])

    def test_attribute_bonus_overflow_rejects_explicit_earlier_learned_level(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create(level=3)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='MA',mode='fixed',value=MAX_INTEGER-16)
            before = deepcopy(hero)
            with self.assertRaisesRegex(ValueError, 'exact integer range'):
                app.select_skills(hero['id'],revision=hero['revision'],learned_level=1,selections=[{'skill_id':'seduction','pool':'related'}])
            self.assertEqual(app.get(hero['id']),before)
            hero = app.select_skills(hero['id'],revision=hero['revision'],learned_level=3,selections=[{'skill_id':'seduction','pool':'related'}])
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],98)

    def test_source_reviewed_catalog_and_separate_voice_percentages(self):
        # UE printed pp.320-321, plus cross-references pp.309 and317.
        expected = {'cardsharp': (24,4), 'computer-hacking': (20,5), 'concealment': (20,4),
            'find-contraband': (26,4), 'gambling-standard': (30,5), 'gambling-dirty-tricks': (20,4),
            'identify-undercover': (30,4), 'imitate-voices': (42,4), 'palming': (20,5),
            'pick-locks': (30,5), 'pick-pockets': (25,5), 'prowl': (25,5), 'roadwise': (26,4),
            'safe-cracking': (20,4), 'seduction': (20,3), 'streetwise': (20,4), 'tailing': (30,5)}
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            catalog = {row['id']:row for row in app.skill_view(hero['id'])['catalog'] if row.get('category') == 'rogue'}
            self.assertEqual({key:(row['base'],row['per_level']) for key,row in catalog.items()}, expected)
            self.assertTrue(all(row['description'] and row['source']['pdf_pages'] for row in catalog.values()))
            app.select_skills(hero['id'], revision=0, selections=[{'skill_id':'imitate-voices','pool':'related'}])
            skill = app.skill_view(hero['id'])['selected'][0]
            self.assertEqual((skill['percentage'],skill['additional_checks'][0]['percentage']), (46,40))

    def test_vagabond_synergies_apply_once_to_shared_required_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            selections = [{'skill_id':name,'pool':'related'} for name in
                ('cardsharp','palming','gambling-dirty-tricks','seduction','find-contraband','find-contraband')]
            app.select_skills(hero['id'],revision=0,selections=selections)
            view = app.skill_view(hero['id'])
            selected = {row['id']:row for row in view['selected']}
            grants = {row['id']:row for row in view['grants']}
            # 24 base +4 class +10 Eyeball +5 Palming +6 Dirty Tricks +5 Seduction.
            self.assertEqual(selected['cardsharp']['percentage'],54)
            self.assertEqual(selected['palming']['percentage'],28)
            # 30 base +10 class +10 Eyeball +10 Streetwise +10 Find Contraband.
            self.assertEqual(grants['identify-undercover']['percentage'],70)
            self.assertEqual(len([row for row in view['grants'] if row['id']=='identify-undercover']),1)
            self.assertEqual(selected['gambling-dirty-tricks']['percentage'],34)

    def test_current_attribute_bonuses_thresholds_caps_and_editable_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory, die=lambda sides:4)
            hero = app.create()
            for attribute,value in [('MA',24),('PB',23),('ME',14)]:
                hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute=attribute,mode='fixed',value=value)
            hero = app.select_skills(hero['id'],revision=hero['revision'],selections=[
                {'skill_id':'seduction','pool':'related'}, {'skill_id':'safe-cracking','pool':'related'}])
            selected = app.skill_view(hero['id'])['selected']
            self.assertEqual([row['percentage'] for row in selected],[41,14])
            fields = PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            self.assertIsNotNone(fields)
            values = ' '.join(str(row.get('/V','')) for row in (fields or {}).values())
            self.assertIn('M.A. attraction', values)
            self.assertIn('Safe-Cracking', values)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='ME',mode='fixed',value=15)
            self.assertEqual(app.skill_view(hero['id'])['selected'][1]['percentage'],24)
            for attribute,value in [('MA',20),('PB',18)]:
                hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute=attribute,mode='fixed',value=value)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],35)
            hero = app.set_attribute(hero['id'],revision=hero['revision'],attribute='MA',mode='fixed',value=200)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],98)
            imported = app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(imported['id'])['selected'],app.skill_view(hero['id'])['selected'])

    def test_city_rat_grants_and_secondary_honor_system_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create(character_class='city-rat')
            app.select_skills(hero['id'],revision=0,selections=[
                {'skill_id':'prowl','pool':'related'}, {'skill_id':'tailing','pool':'related'},
                {'skill_id':'gambling-standard','pool':'secondary'}, {'skill_id':'palming','pool':'secondary'}])
            view = app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']], [40,50,30,20])
            self.assertEqual(next(row for row in view['grants'] if row['id']=='tailing')['percentage'],55)
            self.assertEqual(next(row for row in view['grants'] if row['id']=='math-basic')['percentage'],60)
            self.assertTrue(any('Palming: not available' in note for note in view['warnings']))
            self.assertFalse(any('Gambling (Standard): not available' in note for note in view['warnings']))

    def test_hacking_prerequisites_synergies_and_unconditional_theft_percentages(self):
        with tempfile.TemporaryDirectory() as directory:
            app = CharacterApplication(directory,die=lambda sides:4)
            hero = app.create()
            selections = [{'skill_id':name,'pool':'related'} for name in
                ('computer-hacking','cryptography','surveillance','palming','pick-pockets','seduction')]
            hero = app.select_skills(hero['id'],revision=0,selections=selections)
            view = app.skill_view(hero['id'])
            self.assertTrue(any('Computer Hacking: missing prerequisite' in note for note in view['warnings']))
            selected = {row['id']:row for row in view['selected']}
            self.assertEqual(selected['cryptography']['contributions']['computer_hacking'],5)
            self.assertEqual(selected['surveillance']['contributions']['computer_hacking'],5)
            self.assertEqual(selected['pick-pockets']['percentage'],34)  # 25+4+5, no victim-specific Seduction bonus.
            selections += [{'skill_id':name,'pool':'related'} for name in ('computer-operation','computer-programming','math-basic')]
            selections.append({'skill_id':'literacy-other','pool':'related','specialty':'Dragonese'})
            app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
            self.assertFalse(any('Computer Hacking: missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))

    def test_late_acquisition_progression_reopen_and_exact_old_pins(self):
        archive = RuleArchive.load()
        old = RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.12.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier = CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero = earlier.create(level=3)
            app = CharacterApplication(directory,die=lambda sides:4)
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),73)
            preview = app.preview_rule_upgrade(hero['id'])
            hero = app.apply_rule_upgrade(hero['id'],revision=0,token=preview['token'])['character']
            hero = app.select_skills(hero['id'],revision=hero['revision'],learned_level=3,selections=[
                {'skill_id':'pick-locks','pool':'related'}, {'skill_id':'safe-cracking','pool':'related'},
                {'skill_id':'roadwise','pool':'related','specialty':'Chi-Town / Illinois'}])
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],39)
            hero = app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],44)
            reopened = CharacterApplication(directory)
            imported = reopened.import_character(app.export_character(hero['id']))
            self.assertEqual(reopened.skill_view(imported['id'])['selected'],app.skill_view(hero['id'])['selected'])
            self.assertEqual(reopened.skill_view(imported['id'])['selected'][2]['specialty'],'Chi-Town / Illinois')

    def test_malformed_attribute_declarations_reject_even_when_unselected(self):
        archive = RuleArchive.load()
        for mutation in ('unknown-operation','boolean-step','missing-source'):
            pack = archive.active('rifts-domestic-skills')
            pack['version'] = '99.13.0'
            rule = next(row for row in pack['skills'] if row['id']=='seduction')['attribute_bonuses'][0]
            if mutation == 'unknown-operation':
                rule['operation'] = 'eval'
            elif mutation == 'boolean-step':
                rule['step'] = True
            else:
                del rule['source']
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                app = CharacterApplication(directory,die=lambda sides:4,rule_archive=RuleArchive(
                    [*archive.definitions(),deepcopy(pack)],{**archive.active_versions(),pack['id']:pack['version']}))
                with self.assertRaises(ValueError):
                    hero = app.create()
                    app.skill_view(hero['id'])
