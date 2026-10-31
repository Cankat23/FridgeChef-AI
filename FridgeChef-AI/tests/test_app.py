import copy
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app
from preferences import parse_preferences, conflicts
from photos import recipe_photo


def prefs(**kwargs):
    return parse_preferences(kwargs)


def recipe(**kwargs):
    r = {'name': 'Green Tomato Salad', 'time': '15 min', 'servings': 2,
         'description': 'A simple green salad.', 'ingredients': ['100 g spinach', '2 tomatoes'],
         'additional': ['1 tbsp olive oil'], 'steps': ['Wash vegetables and toss with oil.']}
    r.update(kwargs)
    return r


class PreferenceRules(unittest.TestCase):
    def test_nine_allergen_categories(self):
        for key, sample in [('milk','feta'),('egg','mayonnaise'),('peanut','peanut butter'),('tree_nut','cashews'),('soy','tofu'),('wheat','couscous'),('sesame','tahini'),('fish','salmon'),('shellfish','prawns')]:
            with self.subTest(key=key): self.assertTrue(conflicts(sample, prefs(allergens=[key])))

    def test_vegetarian_and_vegan_differ(self):
        self.assertFalse(conflicts('2 eggs and 50 g cheese', prefs(diet='vegetarian')))
        for value in ['eggs', 'cheese', 'honey']:
            self.assertTrue(conflicts(value, prefs(diet='vegan')))
        for value in ['salmon', 'chicken broth', 'gelatin', 'shrimp']:
            self.assertTrue(conflicts(value, prefs(diet='vegetarian')))
        self.assertFalse(conflicts('eggplant and almond milk', prefs(diet='vegan')))
        self.assertTrue(conflicts('almond milk', prefs(diet='vegan', allergens=['tree_nut'])))

    def test_gluten_is_more_than_wheat(self):
        for food in ['barley', 'rye', 'malt', 'oats', 'pasta', 'soy sauce']:
            self.assertTrue(conflicts(food, prefs(gluten_free=True)), food)
        self.assertFalse(conflicts('certified gluten-free oats', prefs(gluten_free=True)))
        self.assertFalse(conflicts('rice noodles', prefs(gluten_free=True)))
        self.assertTrue(conflicts('gluten-free wheat starch', prefs(allergens=['wheat'])))
        self.assertTrue(conflicts('gluten-free soy sauce', prefs(allergens=['soy'])))

    def test_custom_exclusion(self):
        self.assertTrue(conflicts('Slice mushrooms.', prefs(exclusions=['mushroom'])))
        self.assertTrue(conflicts('Add strawberries.', prefs(exclusions=['strawberry'])))

    def test_plant_alternatives_not_blanket_exemptions(self):
        self.assertFalse(conflicts('almond milk', prefs(allergens=['milk'])))
        self.assertTrue(conflicts('almond milk and butter', prefs(allergens=['milk'])))
        self.assertFalse(conflicts('peanut butter', prefs(allergens=['milk'])))
        self.assertTrue(conflicts('peanut butter', prefs(allergens=['peanut'])))


class API(unittest.TestCase):
    def setUp(self): self.c = app.test_client()

    def test_conflicting_inputs_never_reach_model(self):
        with patch('app.ask_model') as model:
            result = self.c.post('/generate', json={'ingredients':'eggs, spinach','preferences':{'diet':'vegan'}})
            self.assertEqual(result.status_code, 422)
            self.assertEqual(result.json['conflicts'][0]['ingredient'], 'eggs')
            model.assert_not_called()

    def test_output_checked_in_steps_and_extras(self):
        batch = [recipe(), recipe(steps=['Add butter.']), recipe(additional=['1 egg'])]
        with patch('app.ask_model', return_value=(json.dumps({'recipes':batch}), None)) as model:
            r = self.c.post('/generate', json={'ingredients':'spinach, tomatoes', 'preferences':{'diet':'vegan'}})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(len(r.json['recipes']), 1)
            self.assertEqual(r.json['withheld'], 2)
            self.assertIn('"diet": "vegan"', model.call_args.args[0])
            self.assertIn('Vegan preference', r.json['recipes'][0]['badges'])

    def test_no_matching_recipes(self):
        with patch('app.ask_model', return_value=(json.dumps({'recipes':[recipe(steps=['Add honey.'])]*3}),None)):
            r=self.c.post('/generate',json={'ingredients':'spinach','preferences':{'diet':'vegan'}})
            self.assertEqual(r.status_code,422)
            self.assertNotIn('recipes',r.json)

    def test_servings_and_reconciliation(self):
        r=recipe(ingredients=['2 eggs'],additional=['1 lemon, juiced','20 g nuts','1 tbsp oil'])
        with patch('app.ask_model',return_value=(json.dumps({'recipes':[r]*3}),None)):
            result=self.c.post('/generate',json={'ingredients':'eggs, lemon, nuts','servings':2})
            self.assertEqual(result.status_code,200)
            self.assertIn('1 lemon, juiced',result.json['recipes'][0]['ingredients'])
            self.assertIn('20 g nuts',result.json['recipes'][0]['ingredients'])
        with patch('app.ask_model',return_value=(json.dumps({'recipes':[r]*3}),None)):
            self.assertEqual(self.c.post('/generate',json={'ingredients':'eggs','servings':4}).status_code,502)

    def test_validation_and_bad_requests(self):
        self.assertEqual(self.c.post('/generate',json={'ingredients':'rice','preferences':{'allergens':['invalid']}}).status_code,400)
        self.assertEqual(self.c.post('/generate',json={'ingredients':'rice','servings':0}).status_code,400)
        r=self.c.post('/validate',json={'ingredients':'rice, barley','preferences':{'gluten_free':True}})
        self.assertEqual(r.json['conflicts'][0]['ingredient'],'barley')
        self.assertEqual(len(self.c.get('/config').json['allergens']),9)

    def test_detection_preserved(self):
        with patch('app.ask_model',return_value=(json.dumps({'ingredients':['tomatoes','liquid'],'uncertain':['jar']}),None)):
            r=self.c.post('/detect',data={'image':(io.BytesIO(b'image'),'test.png')})
            self.assertEqual(r.status_code,200)
            self.assertEqual(r.json['ingredients'],'tomatoes')
            self.assertIn('liquid',r.json['uncertain'])

    def test_photos_are_local_and_fallback_is_honest(self):
        photo=recipe_photo(recipe(),prefs())
        self.assertTrue(photo['url'].startswith('/static/photos/'))
        with self.c.get(photo['url']) as result:
            self.assertEqual(result.status_code,200)
        self.assertIn('Serving suggestion',photo['label'])
        self.assertIsNone(recipe_photo(recipe(name='Unusual lentil stew'),prefs()))
        self.assertIsNone(recipe_photo(recipe(name='Tomato pasta'),prefs(gluten_free=True)))
        self.assertIsNone(recipe_photo(recipe(name='Tomato salad'),prefs(exclusions=['tomato'])))


if __name__ == '__main__': unittest.main()
