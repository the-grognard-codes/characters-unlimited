from io import BytesIO
import tempfile
import unittest

from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive


def selections(*identities,pool='related'):
    return [{'skill_id':identity,'pool':pool} for identity in identities]


class WildernessEspionageWorkflowTests(unittest.TestCase):
    def test_source_reviewed_normal_catalog_and_paired_percentages(self):
        expected={'boat-building':(25,5),'carpentry':(25,5),'dowsing':(20,5),'fasting':(40,3),
            'identify-plants-fruit':(25,5),'land-navigation':(36,4),'preserve-food':(30,5),
            'skin-prepare-hides':(30,5),'spelunking':(35,5),'track-trap-animals':(20,5),
            'wilderness-survival':(30,5),'detect-ambush':(30,5),'detect-concealment':(25,5),
            'disguise':(25,5),'escape-artist':(30,5),'forgery':(20,5),'impersonation':(30,4),
            'intelligence':(32,4),'interrogation':(30,5),'tracking':(25,5),'undercover-ops':(30,5)}
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            catalog={row['id']:row for row in app.skill_view(hero['id'])['catalog']
                     if row.get('category') in ('wilderness','espionage') and row.get('kind') != 'training'}
            self.assertEqual({key:(row['base'],row['per_level']) for key,row in catalog.items()},expected)
            self.assertTrue(all(row['description'] and row['source']['pdf_pages'] for row in catalog.values()))
            app.select_skills(hero['id'],revision=0,selections=selections('track-trap-animals','impersonation','land-navigation','fasting'))
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[20,30,36,40])
            self.assertEqual([view['selected'][index]['additional_checks'][0]['percentage'] for index in (0,1)],[30,16])
            hero=app.get(hero['id'])
            app.set_attribute(hero['id'],revision=hero['revision'],attribute='IQ',mode='fixed',value=16)
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[22,32,38,42])
            self.assertEqual([view['selected'][index]['additional_checks'][0]['percentage'] for index in (0,1)],[32,18])

    def test_class_and_secondary_permissions_retain_exception_choices(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            for path in ('vagabond','city-rat'):
                hero=app.create(character_class=path)
                app.select_skills(hero['id'],revision=0,selections=selections('land-navigation','detect-ambush'))
                view=app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],[36,30])
                self.assertEqual(sum('not available in the related' in note for note in view['warnings']),1 if path=='vagabond' else 2)
                hero=app.get(hero['id'])
                app.select_skills(hero['id'],revision=hero['revision'],selections=selections(
                    'carpentry','dowsing','boat-building','spelunking','detect-ambush',pool='secondary'))
                view=app.skill_view(hero['id'])
                self.assertEqual([row['percentage'] for row in view['selected']],[25,20,35,35,30])
                self.assertEqual(sum('not available in the secondary' in note for note in view['warnings']),3)

    def test_normal_synergies_apply_once_and_recalculate_after_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            targets=('boat-building','camouflage','impersonation','undercover-ops','forgery','pick-locks','sewing','leather-working')
            parents=('carpentry','detect-concealment','disguise','escape-artist','art','skin-prepare-hides')
            app.select_skills(hero['id'],revision=0,selections=selections(*targets,*parents,'disguise','skin-prepare-hides'))
            rows={row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual([rows[key]['percentage'] for key in targets],[35,25,35,45,30,39,55,50])
            self.assertEqual(rows['impersonation']['additional_checks'][0]['percentage'],21)
            hero=app.get(hero['id'])
            app.select_skills(hero['id'],revision=hero['revision'],selections=selections(*targets))
            rows={row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual([rows[key]['percentage'] for key in targets],[25,20,30,40,20,34,50,45])

    def test_existing_source_training_grants_new_targets_once_and_removes_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create()
            targets=('impersonation','undercover-ops','identify-plants-fruit','preserve-food')
            parents=('research','performance','imitate-voices','holistic-medicine')
            hero=app.select_skills(hero['id'],revision=0,selections=selections(*targets,*parents,*parents))
            view=app.skill_view(hero['id'])
            rows={row['id']:row for row in view['selected']}
            self.assertEqual([rows[key]['percentage'] for key in targets],[45,45,35,40])
            self.assertEqual(rows['impersonation']['additional_checks'][0]['percentage'],31)
            imported=app.import_character(app.export_character(hero['id']))
            self.assertEqual(app.skill_view(imported['id'])['selected'],view['selected'])
            app.select_skills(hero['id'],revision=hero['revision'],selections=selections(*targets))
            rows={row['id']:row for row in app.skill_view(hero['id'])['selected']}
            self.assertEqual([rows[key]['percentage'] for key in targets],[30,40,25,30])
            self.assertEqual(rows['impersonation']['additional_checks'][0]['percentage'],16)

    def test_late_learning_import_reselection_and_undo_retain_both_normal_ages(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(level=3)
            hero=app.select_skills(hero['id'],revision=0,selections=selections('track-trap-animals','impersonation'))
            hero=app.advance(hero['id'],revision=hero['revision'],method='level',value=4)
            view=app.skill_view(hero['id'])
            self.assertEqual([row['percentage'] for row in view['selected']],[25,34])
            self.assertEqual([row['additional_checks'][0]['percentage'] for row in view['selected']],[35,20])
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=[])
            hero=app.select_skills(hero['id'],revision=hero['revision'],selections=selections('track-trap-animals','impersonation'))
            imported=app.import_character(app.export_character(hero['id']))
            reopened=CharacterApplication(directory)
            self.assertEqual(reopened.skill_view(imported['id'])['selected'],view['selected'])
            hero=app.undo_advancement(hero['id'],revision=hero['revision'])['character']
            self.assertEqual([row['percentage'] for row in app.skill_view(hero['id'])['selected']],[20,30])

    def test_old_archive_requires_explicit_catalog_upgrade(self):
        installed=RuleArchive.load()
        old=RuleArchive(installed.definitions(),{**installed.active_versions(),'rifts-domestic-skills':'2.17.0'})
        with tempfile.TemporaryDirectory() as directory:
            earlier=CharacterApplication(directory,die=lambda sides:4,rule_archive=old)
            hero=earlier.create()
            earlier.select_skills(hero['id'],revision=0,selections=selections('camouflage',pool='secondary'))
            app=CharacterApplication(directory)
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),141)
            before=app.get(hero['id'])
            with self.assertRaises(ValueError):
                app.select_skills(hero['id'],revision=before['revision'],selections=selections('detect-concealment'))
            self.assertEqual(app.get(hero['id']),before)
            preview=app.preview_rule_upgrade(hero['id'])
            self.assertEqual(preview['changes'][0]['to'],'2.26.0')
            hero=app.apply_rule_upgrade(hero['id'],revision=before['revision'],token=preview['token'])['character']
            self.assertEqual(len(app.skill_view(hero['id'])['catalog']),206)
            app.select_skills(hero['id'],revision=hero['revision'],selections=[*selections('camouflage',pool='secondary'),*selections('detect-concealment')])
            self.assertEqual(app.skill_view(hero['id'])['selected'][0]['percentage'],25)

    def test_editable_pdf_retains_normal_pairs_and_descriptive_source_rules(self):
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4)
            hero=app.create(name='Wilderness investigator')
            app.select_skills(hero['id'],revision=0,selections=selections('track-trap-animals','impersonation','disguise','fasting'))
            reader=PdfReader(BytesIO(app.export_pdf(hero['id'])))
            fields=reader.get_fields() or {}
            text=' '.join(str(row.get('/V','')) for row in fields.values())
            for phrase in ('Track & Trap Animals','Trapping animals','Specific individual','Fasting','temporary attribute loss'):
                self.assertIn(phrase,text)
            self.assertTrue(any(page.get('/Annots') for page in reader.pages))
