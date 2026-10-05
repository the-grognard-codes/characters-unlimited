from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.advancement import learning_key
from characters_unlimited.rules import RuleArchive
from tests.test_owned_class_profiles import owned_pack, archive_with


def choices(*identities,pool='related'):
    return [{'skill_id':identity,'pool':pool} for identity in identities]


class PilotSkillWorkflowTests(unittest.TestCase):
    def test_reviewed_catalog_and_both_normal_seamanship_checks(self):
        expected={'airplane':(50,4),'automobile':(60,2),'bicycle':(44,4),'motor-boat':(55,5),
            'paddle-boat':(50,5),'sail-boat':(60,5),'ships-seamanship':(45,5),'flight-system-combat':(40,5),
            'hover-craft':(50,5),'hovercycle':(70,3),'jet-aircraft':(40,4),'jet-pack':(42,4),
            'jump-bike-combat':(45,5),'combat-helicopter':(52,3),'jet-fighter':(40,4),
            'submersible':(40,4),'tanks-apcs':(36,4),'warship':(40,4),'motorcycle':(60,4),
            'robots-power-armor':(56,3),'tracked-construction':(40,4),'truck':(40,4),
            'water-scooter':(50,5),'water-skiing-surfing':(40,4)}
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            catalog={row['id']:row for row in app.skill_view(hero['id'])['catalog'] if row.get('category')=='pilot'}
            self.assertEqual({key:(row['base'],row['per_level']) for key,row in catalog.items()},expected)
            self.assertTrue(all(row['description'] and row['source']['pdf_pages'] for row in catalog.values()))
            hero=app.select_skills(hero['id'],revision=0,selections=choices('ships-seamanship','navigation','weapon-systems','rope-works'))
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[45,40,40,35])
            self.assertEqual(view['selected'][0]['additional_checks'][0]['percentage'],40)
            self.assertTrue(any('Boats: Ships/Seamanship: missing prerequisite Sewing' in note for note in view['warnings']))
            self.assertFalse(any('Boats: Ships/Seamanship: missing prerequisite Rope Works' in note for note in view['warnings']))
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices(
                'ships-seamanship','rope-works','sewing','navigation','math-basic','sensory-equipment','literacy-other'))
            self.assertTrue(any('Navigation: missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))
            selections=choices('ships-seamanship','rope-works','sewing','navigation','math-basic','sensory-equipment')
            selections.append({'skill_id':'literacy-other','pool':'secondary','specialty':'Dragonese'})
            app.select_skills(hero['id'],revision=hero['revision'],selections=selections)
            self.assertFalse(any('missing prerequisite' in note for note in app.skill_view(hero['id'])['warnings']))

    def test_class_and_secondary_permissions_keep_exceptions_and_normal_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            for path,expected in [('vagabond',[65,49,75,47,65,40,40]),('city-rat',[70,64,80,52,60,40,40])]:
                hero=app.create(character_class=path)
                hero=app.select_skills(hero['id'],revision=0,selections=choices(
                    'automobile','bicycle','hovercycle','jet-pack','sail-boat','navigation','jet-fighter'))
                view=app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],expected)
                self.assertTrue(any('Military: Jet Fighters: not available in the related' in note for note in view['warnings']))
                self.assertEqual(any('Navigation: not available in the related' in note for note in view['warnings']),path=='city-rat')
                app.select_skills(hero['id'],revision=hero['revision'],selections=choices(
                    'motorcycle','hover-craft','paddle-boat','water-scooter','airplane','jet-pack','navigation',pool='secondary'))
                view=app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],[60,50,50,50,50,42,40])
                self.assertEqual(len([note for note in view['warnings'] if 'not available in the secondary' in note]),3)

    def test_required_driving_choices_and_existing_grants_supply_highest_training_once(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            for path,group,motorcycle,barter in [('vagabond','pilot',72,56),('city-rat','vehicle',75,49)]:
                hero=app.create(character_class=path)
                hero=app.select_required_skills(hero['id'],revision=0,choices={group:'motorcycle'})
                hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('motorcycle','motorcycle','barter'))
                view=app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],[motorcycle,motorcycle,barter])
                self.assertEqual(next(row for row in view['grants'] if row['id']=='motorcycle')['percentage'],motorcycle)
                self.assertEqual(next(row for row in view['grants'] if row['id']=='barter')['percentage'],barter)
                self.assertEqual(hero['required_skill_choices'][group],'motorcycle')
                self.assertTrue(any('Motorcycles & Snowmobiles: already granted' in note for note in view['warnings']))
            hero=app.create()
            hero=app.select_required_skills(hero['id'],revision=0,choices={'pilot':'automobile'})
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('automobile'))
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],70)

    def test_other_owned_class_does_not_borrow_catalog_class_ability(self):
        pack=owned_pack()
        profile=pack['class_profiles']['city-rat']
        profile['required']['grants']=[row for row in profile['required']['grants'] if row['id']!='barter']
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive_with(pack))
            hero=app.create(character_class='city-rat')
            app.select_skills(hero['id'],revision=0,selections=choices('barter'))
            row=app.skill_view(hero['id'])['selected'][0]
            self.assertEqual(row['percentage'],44)
            self.assertNotIn('class_ability',row['contributions'])

    def test_old_pin_upgrade_retains_legacy_history_and_new_optional_overlap_age(self):
        archive=RuleArchive.load()
        old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-domestic-skills':'2.16.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=earlier.create(character_class='city-rat',level=3)
            old_view=earlier.skill_view(hero['id'])
            self.assertEqual(len(old_view['catalog']),114)
            self.assertEqual(next(row for row in old_view['grants'] if row['id']=='pilot-automobile')['percentage'],74)
            legacy=learning_key('skill','pilot-automobile')
            self.assertEqual(hero['learning_levels'][legacy],1)
            app=CharacterApplication(directory,die=lambda sides:4)
            self.assertEqual(app.skill_view(hero['id'])['grants'],old_view['grants'])
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'],'2.17.0')
            hero=app.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(hero['learning_levels'][legacy],1)
            hero=app.select_skills(hero['id'],revision=hero['revision'],learned_level=3,selections=choices('automobile','bicycle'))
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[74,72])
            self.assertEqual(hero['learning_levels'][legacy],1)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[76,76])
            imported=app.import_character(app.export_character(hero['id']))
            reopened=CharacterApplication(directory)
            self.assertEqual(reopened.skill_view(imported['id'])['selected'],app.skill_view(hero['id'])['selected'])
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[74,72])
            self.assertEqual(hero['learning_levels'][legacy],1)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields() or {}
            text=' '.join(str(row.get('/V','')) for row in fields.values())
            self.assertIn('Automobile',text)
            self.assertIn('Bicycling',text)

    def test_late_learning_uses_skill_age_for_both_ship_checks_and_retains_reselection(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(level=3)
            hero=app.select_skills(hero['id'],revision=0,selections=choices('ships-seamanship','rope-works','sewing'))
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],45)
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            row=app.skill_view(hero['id'])['selected'][0]
            self.assertEqual((row['percentage'],row['additional_checks'][0]['percentage']),(50,45))
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=choices('ships-seamanship'))
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['additional_checks'][0]['percentage'],45)

    def test_malformed_unselected_catalog_references_reject_before_dice(self):
        for invalid in ('unknown','type','physical','specialty','base','bonus','source','format','absent','unselected-choice'):
            with self.subTest(invalid=invalid),tempfile.TemporaryDirectory() as directory:
                pack=owned_pack()
                definition=next(row for row in pack['class_profiles']['city-rat']['required']['grants'] if row['id']=='pilot-automobile')
                if invalid=='unknown': definition['catalog_skill_id']='missing'
                if invalid=='type': definition['catalog_skill_id']={}
                if invalid=='physical': definition['catalog_skill_id']='running'
                if invalid=='specialty': definition['catalog_skill_id']='literacy-other'
                if invalid=='base': definition['base']=59
                if invalid=='bonus': definition['class_bonus']=True
                if invalid=='source': definition['source']={}
                if invalid=='format': pack['required_skill_training']['format']=True
                if invalid=='absent': del pack['required_skill_training']
                if invalid=='unselected-choice':
                    group=next(row for row in pack['class_profiles']['vagabond']['required']['groups'] if row['id']=='pilot')
                    group['options'][0]['catalog_skill_id']='missing'
                calls=[]
                def die(sides):
                    calls.append(sides)
                    return 4
                app=CharacterApplication(directory,die=die,rule_archive=archive_with(pack))
                with self.assertRaises(ValueError): app.create()
                self.assertEqual(calls,[])
                self.assertEqual(app.list(),[])

    def test_legacy_adapter_validates_unselected_root_and_profiles_before_dice(self):
        for owner in ('vagabond','city-rat'):
            for selected in ('vagabond','city-rat'):
                with self.subTest(owner=owner,selected=selected),tempfile.TemporaryDirectory() as directory:
                    pack=RuleArchive.load().active('rifts-domestic-skills')
                    required=pack['required'] if owner=='vagabond' else pack['class_profiles'][owner]['required']
                    if owner=='vagabond':
                        group=next(row for row in required['groups'] if row['id']=='pilot')
                        group['options'][0]['catalog_skill_id']='missing'
                    else:
                        required['grants'][0]['catalog_skill_id']='missing'
                    def die(sides):
                        self.fail('Malformed unselected required training must reject before dice')
                    app=CharacterApplication(directory,die=die,rule_archive=archive_with(pack))
                    with self.assertRaises(ValueError): app.create(character_class=selected)
                    self.assertEqual(app.list(),[])
