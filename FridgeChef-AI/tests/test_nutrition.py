import sys,unittest,json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from nutrition import estimate,resolve,DATA
from app import app

class Nutrition(unittest.TestCase):
    def test_portions_and_all_ingredients(self):
        r={'ingredients':['100 g spinach','2 tomatoes'],'additional':['1 tbsp olive oil'],'servings':2}
        n=estimate(r)
        self.assertEqual(n['status'],'complete')
        self.assertEqual(n['coverage'],{'matched':3,'total':3})
        for key,value in n['whole_recipe'].items():self.assertAlmostEqual(n['per_serving'][key]*2,value)
        without=estimate({**r,'additional':[]})
        self.assertAlmostEqual(n['whole_recipe']['fat_g']-without['whole_recipe']['fat_g'],13.5)
        self.assertGreater(n['whole_recipe']['kcal'],without['whole_recipe']['kcal']+100)
        self.assertTrue(any('medium' in v for v in n['assumptions']))

    def test_unknowns_are_not_silently_zero(self):
        n=estimate({'ingredients':['100 g spinach','a handful of magic greens'],'additional':['salt to taste'],'servings':2})
        self.assertEqual(n['status'],'incomplete')
        self.assertEqual(len(n['missing']),2)
        self.assertEqual(n['coverage']['matched'],1)
        empty=estimate({'ingredients':['some mystery sauce'],'additional':[],'servings':2})
        self.assertEqual(empty['status'],'unavailable')
        self.assertTrue(all(v is None for v in empty['whole_recipe'].values()))

    def test_unknown_servings_and_state(self):
        n=estimate({'ingredients':['100 g spinach'],'additional':[],'servings':None})
        self.assertEqual(n['status'],'unavailable')
        self.assertIsNotNone(resolve('100 g rice')[1])
        self.assertNotEqual(resolve('100 g cooked rice')[0]['ndb_id'],resolve('100 g dry rice')[0]['ndb_id'])
        self.assertIsNotNone(resolve('100 g gluten-free pasta')[1])

    def test_supported_units(self):
        self.assertAlmostEqual(resolve('0.1 kg spinach')[0]['grams'],100)
        self.assertAlmostEqual(resolve('1/2 cup milk')[0]['grams'],122)
        self.assertAlmostEqual(resolve('2 large eggs')[0]['grams'],100)
        self.assertAlmostEqual(resolve('3 cloves garlic')[0]['grams'],9)
        self.assertAlmostEqual(resolve('50 ml water')[0]['grams'],50)
        self.assertTrue(resolve('50 ml olive oil')[0]['assumptions'])
        for value in ['100-200 g spinach','-20g spinach','0g spinach','1/0 g spinach']:
            self.assertIsNotNone(resolve(value)[1])

    def test_source_and_reference_values(self):
        self.assertEqual(len(DATA['foods']),71)
        spinach=next(v for v in DATA['foods'] if v['key']=='spinach')
        self.assertEqual(spinach['ndb_id'],'11457')
        self.assertEqual(spinach['per_100g']['kcal'],23)
        self.assertIn('2018',DATA['source'])
        self.assertEqual(len(DATA['download_sha256']),64)

    def test_api_nutrition_cannot_be_overridden_by_model(self):
        r={'name':'Spinach bowl','time':'10 min','servings':2,'description':'Simple spinach.','ingredients':['100 g spinach'],'additional':['1 tbsp olive oil'],'steps':['Cook spinach in oil.'],'nutrition':{'kcal':999999}}
        with patch('app.ask_model',return_value=(json.dumps({'recipes':[r]*3}),None)):
            result=app.test_client().post('/generate',json={'ingredients':'spinach, olive oil'})
            self.assertEqual(result.status_code,200)
            self.assertEqual(result.json['recipes'][0]['nutrition']['status'],'complete')
            self.assertLess(result.json['recipes'][0]['nutrition']['whole_recipe']['kcal'],200)

if __name__=='__main__':unittest.main()
