"""Source-defined free knife through existing equipment and combat workflows."""

from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


class CityRatStartingKnifeTests(unittest.TestCase):
    def test_free_knife_is_independent_and_does_not_grant_training(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(character_class='city-rat')
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            hero=app.generate_starting_funds(hero['id'],revision=hero['revision'])
            hero=app.grant_starting_gear(hero['id'],revision=hero['revision'])
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='armor',selection='urban-warrior')
            before=deepcopy(hero)
            before_combat=app.combat_view(hero['id'])
            app.die=lambda sides:self.fail('Knife grant must not roll dice')
            hero=app.grant_starting_group(hero['id'],revision=hero['revision'],group_id='knife',selection='knife-large')
            self.assertEqual(hero['equipment']['credits'],2400)
            self.assertEqual(len(hero['equipment']['items']),8)
            for field in ('attributes','resources','starting_funds','starting_gear'):
                self.assertEqual(hero.get(field),before.get(field))
            self.assertEqual(app.combat_view(hero['id']),before_combat)
            self.assertEqual(hero['starting_equipment_groups']['armor'],before['starting_equipment_groups']['armor'])
            receipt=hero['starting_equipment_groups']['knife']
            self.assertEqual(receipt['selection'],'knife-large')
            self.assertEqual(receipt['source']['pages'],[89])
            view=app.equipment_view(hero['id'])
            self.assertEqual(view['carried_weight_lbs'],11)
            self.assertEqual(view['unknown_carried_weight_quantity'],8)
            self.assertTrue(any('S.D.C. handgun and M.D. pistol' in note for note in view['starting_gear']['guidance']))
            self.assertFalse(any('starting armor, weapons' in note for note in view['starting_gear']['guidance']))
            inventory=deepcopy(hero['equipment']);inventory['items'][-1]['equipped']=True
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            attack=app.equipment_view(hero['id'])['melee_attacks'][0]
            self.assertIn('1D6',attack['damage'])
            self.assertEqual(attack['parry']['value'],0)
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            values=' '.join(str(field.get('/V','')) for field in fields.values())
            self.assertIn('Large Knife',values)
            self.assertIn('Original starting knife',values)
            app.die=lambda sides:4
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=3)
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual(hero['starting_equipment_groups']['knife'],receipt)
            inventory=deepcopy(hero['equipment']);inventory['items']=inventory['items'][:-1]
            hero=app.set_equipment(hero['id'],revision=hero['revision'],inventory=inventory)
            reopened=CharacterApplication(directory)
            imported=reopened.import_character(reopened.export_character(hero['id']))
            self.assertEqual(imported['starting_equipment_groups']['knife'],receipt)
            with self.assertRaises(ValueError):
                reopened.grant_starting_group(hero['id'],revision=hero['revision'],group_id='knife',selection='knife-large')

    def test_old_armor_pin_upgrades_without_granting_knife_and_groups_work_in_reverse_order(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=RuleArchive.load()
            old=RuleArchive(archive.definitions(),{**archive.active_versions(),'rifts-equipment':'1.9.0'})
            previous=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=previous.create(character_class='city-rat')
            hero=previous.grant_starting_group(hero['id'],revision=hero['revision'],group_id='armor',selection='plastic-man')
            current=CharacterApplication(directory,die=lambda sides:self.fail('Upgrade/grant must not roll'))
            with self.assertRaises(ValueError):
                current.grant_starting_group(hero['id'],revision=hero['revision'],group_id='knife',selection='knife-large')
            preview=current.preview_rule_upgrade(hero['id'])
            updated=current.apply_rule_upgrade(hero['id'],revision=hero['revision'],token=preview['token'])['character']
            self.assertEqual(updated['equipment'],hero['equipment'])
            self.assertEqual(updated['starting_equipment_groups'],hero['starting_equipment_groups'])
            with self.assertRaises(ValueError):
                current.grant_starting_group(hero['id'],revision=updated['revision'],group_id='knife',selection='knife-small')
            updated=current.grant_starting_group(hero['id'],revision=updated['revision'],group_id='knife',selection='knife-large')
            current.die=lambda sides:4
            reverse=current.create(character_class='city-rat')
            reverse=current.grant_starting_group(reverse['id'],revision=reverse['revision'],group_id='knife',selection='knife-large')
            reverse=current.grant_starting_group(reverse['id'],revision=reverse['revision'],group_id='armor',selection='huntsman')
            self.assertEqual([item['item_id'] for item in reverse['equipment']['items']],['knife-large','huntsman'])
            self.assertEqual(reverse['equipment']['credits'],0)
            vag=current.create()
            with self.assertRaises(ValueError):
                current.grant_starting_group(vag['id'],revision=vag['revision'],group_id='knife',selection='knife-large')
