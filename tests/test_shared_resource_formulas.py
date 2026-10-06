from copy import deepcopy
from io import BytesIO
import tempfile
import unittest
from pypdf import PdfReader
from characters_unlimited.application import CharacterApplication
from characters_unlimited.rules import RuleArchive

class SharedResourceFormulaTests(unittest.TestCase):
    def test_rifts_ppe_isp_compose_scaled_dice_and_retained_effective_pe_without_house_options(self):
        installed=RuleArchive.load()
        pack=installed.active('rifts-domestic-skills')
        source={'book':'Synthetic framework fixture','pages':[1],'section':'Resource formula contract'}
        pack['class_profiles']['vagabond']['resources']['definitions'].extend([
            {'id':'PPE','name':'Synthetic P.P.E.','contributions':[
                {'id':'scaled-dice','formula':{'count':3,'sides':6,'bonus':0,'multiplier':10},'source':source},
                {'id':'initial-pe','attribute':'PE','source':source}]},
            {'id':'ISP','name':'Synthetic I.S.P.','contributions':[
                {'id':'fixed-term','formula':{'count':0,'sides':0,'bonus':5,'multiplier':2},'source':source}]}])
        archive=RuleArchive([pack if (row['id'],row['version'])==(pack['id'],pack['version']) else row
                            for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive)
            hero=app.create(generation={'reroll_ones':True,'extra_die':True})
            calls=[]
            def die(sides):
                calls.append(sides)
                return 1
            app.die=die
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            view=app.resource_view(hero['id'])['resources']
            self.assertEqual(view['PPE']['value'],44)
            self.assertEqual(view['PPE']['rolls']['scaled-dice'],[1,1,1])
            self.assertEqual(view['ISP']['value'],10)
            self.assertEqual(len(calls),8)
            snapshot=deepcopy(hero['resource_attribute_snapshot'])
            hero=app.set_attribute(hero['id'],revision=hero['revision'],attribute='PE',mode='fixed',value=30)
            self.assertEqual(app.resource_view(hero['id'])['resources']['PPE']['value'],44)
            self.assertEqual(hero['resource_attribute_snapshot'],snapshot)
            hero=app.set_resource(hero['id'],revision=hero['revision'],resource='PPE',mode='adjustment',value=3)
            self.assertEqual(app.resource_view(hero['id'])['resources']['PPE']['value'],47)
            bundle=app.export_character(hero['id'])
            tampered=deepcopy(bundle)
            tampered['character']['resources']['PPE']['contributions'][0]['value']=31
            with self.assertRaises(ValueError):
                app.import_character(tampered)
            restored=app.import_character(bundle)
            self.assertEqual(restored['resources'],hero['resources'])
            fields=PdfReader(BytesIO(app.export_pdf(hero['id']))).get_fields()
            assert fields is not None
            self.assertIn('Synthetic P.P.E.','\n'.join(str(row.get('/V','')) for row in fields.values()))

    def test_heroes_ppe_uses_shared_scaled_formula_and_original_replay(self):
        installed=RuleArchive.load()
        pack=installed.active('heroes-resources')
        definition=next(row for row in pack['resources']['definitions'] if row['id']=='PPE')
        definition['contributions'][0]['formula']['multiplier']=2
        archive=RuleArchive([pack if (row['id'],row['version'])==(pack['id'],pack['version']) else row
                            for row in installed.definitions()],installed.active_versions())
        with tempfile.TemporaryDirectory() as directory:
            app=CharacterApplication(directory,die=lambda sides:4,rule_archive=archive)
            hero=app.create(game='heroes-unlimited')
            hero=app.generate_resources(hero['id'],revision=hero['revision'])
            self.assertEqual(app.resource_view(hero['id'])['resources']['PPE']['value'],48)
            self.assertEqual(hero['resources']['PPE']['contributions'][0]['rolls'],[4]*6)
            app.die=lambda sides:self.fail('Portable replay must not draw dice')
            restored=app.import_character(app.export_character(hero['id']))
            self.assertEqual(restored['resources'],hero['resources'])

    def test_malformed_resource_formulas_and_unknown_attributes_reject_before_dice(self):
        mutations=[
            lambda row:row['contributions'][0]['formula'].update(multiplier=True),
            lambda row:row['contributions'][0]['formula'].update(multiplier=0),
            lambda row:row['contributions'][0]['formula'].update(bonus=9_007_199_254_740_991,multiplier=2),
            lambda row:row['contributions'][0]['formula'].update(expression='execute'),
            lambda row:row['contributions'][0].update(attribute='UNKNOWN'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as directory:
                installed=RuleArchive.load()
                pack=installed.active('rifts-domestic-skills')
                definition: dict = {'id':'ISP','name':'Synthetic I.S.P.','contributions':[
                    {'id':'term','formula':{'count':0,'sides':0,'bonus':5},
                     'source':{'book':'Synthetic framework fixture','pages':[1]}}]}
                mutation(definition)
                if 'attribute' in definition['contributions'][0]:
                    definition['contributions'][0].pop('formula')
                pack['class_profiles']['vagabond']['resources']['definitions'].append(definition)
                archive=RuleArchive([pack if (row['id'],row['version'])==(pack['id'],pack['version']) else row
                                    for row in installed.definitions()],installed.active_versions())
                app=CharacterApplication(directory,
                    die=lambda sides:self.fail('Malformed resource rule must not draw dice'),
                    rule_archive=archive)
                with self.assertRaises(ValueError):
                    app.create()
                self.assertEqual(app.list(),[])
