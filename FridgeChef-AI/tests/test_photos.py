import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from photos import CATALOG, BASE, recipe_photo
from preferences import parse_preferences


def result(name, ingredients, **preferences):
    return recipe_photo({'name':name,'ingredients':ingredients,'additional':[]},parse_preferences(preferences))


class PhotoMatching(unittest.TestCase):
    def test_library_contains_22_licensed_local_photos(self):
        self.assertEqual(len(CATALOG),22)
        for photo in CATALOG.values():
            with self.subTest(photo=photo['file']):
                self.assertTrue((BASE/photo['file']).is_file())
                self.assertTrue(photo['source'].startswith('https://commons.wikimedia.org/'))
                self.assertTrue(photo['credit'])
                self.assertTrue(photo['license'].startswith('http'))
                self.assertLess((BASE/photo['file']).stat().st_size,600000)
                with (BASE/photo['file']).open('rb') as image:
                    self.assertEqual(image.read(2),b'\xff\xd8')

    def test_dish_and_main_ingredients_must_agree(self):
        self.assertIsNone(result('Tomato soup',['broccoli','cream']))
        self.assertIsNone(result('Pasta salad',['spinach','tomatoes','pasta']))
        self.assertIsNone(result('Salmon salad',['salmon','spinach','tomatoes']))
        self.assertIsNone(result('Fruit salad',['spinach','tomatoes']))
        self.assertIsNone(result('Mushroom risotto',['rice','mushroom']))

    def test_matching_coverage(self):
        examples=[
            ('Green salad',['spinach','tomatoes'],'salad.jpg'),
            ('Brown lentil soup',['lentils','carrot'],'lentil-soup.jpg'),
            ('Chickpea salad',['chickpeas','carrot'],'chickpea-salad.jpg'),
            ('Mixed bean salad',['kidney beans'],'bean-salad.jpg'),
            ('Vegetable stir fry noodles',['noodles','carrot'],'vegetable-noodles.jpg'),
            ('Egg fried rice',['rice','egg'],'fried-rice.jpg'),
            ('Grilled chicken',['chicken','lemon'],'chicken.jpg'),
            ('Hummus',['chickpeas','tahini'],'hummus.jpg'),
            ('Avocado toast',['avocado','bread'],'avocado-toast.jpg'),
            ('Blueberry pancakes',['flour','blueberries'],'pancakes.jpg'),
            ('Potato and chickpea curry',['potatoes','chickpeas'],'chickpea-curry.jpg'),
            ('Ratatouille',['zucchini','eggplant','tomatoes'],'ratatouille.jpg'),
            ('Fruit salad',['oranges','strawberries'],'fruit-salad.jpg'),
            ('Broccoli soup',['broccoli','cream'],'broccoli-soup.jpg'),
            ('Pesto pasta',['pasta','basil'],'pesto-pasta.jpg'),
            ('Greek salad',['feta','cucumber','tomatoes'],'greek-salad.jpg'),
            ('Shakshuka',['egg','tomatoes'],'shakshuka.jpg'),
        ]
        for name,ingredients,photo in examples:
            with self.subTest(dish=name):
                data=result(name,ingredients)
                self.assertIsNotNone(data)
                self.assertTrue(data['url'].endswith('/'+photo))

    def test_no_explicitly_conflicting_serving_photos(self):
        self.assertIsNone(result('Broccoli soup',['broccoli'],diet='vegan'))
        self.assertIsNone(result('Avocado toast',['avocado','gluten-free bread'],gluten_free=True))
        self.assertIsNone(result('Hummus',['chickpeas'],allergens=['sesame']))
        self.assertIsNone(result('Green salad',['spinach','tomato'],exclusions=['onion']))
        self.assertIsNone(result('Grilled chicken',['chicken'],diet='vegetarian'))
        self.assertIsNone(result('Pesto pasta',['pasta','basil'],allergens=['tree_nut']))

    def test_plant_and_gluten_preferences_still_have_photo_coverage(self):
        self.assertIsNotNone(result('Hummus',['chickpeas'],diet='vegan',gluten_free=True))
        self.assertIsNotNone(result('Chickpea salad',['chickpeas'],diet='vegan',gluten_free=True))
        self.assertIsNotNone(result('Ratatouille',['zucchini','eggplant','tomatoes'],diet='vegan',gluten_free=True))
        self.assertIsNotNone(result('Fruit salad',['oranges','strawberries'],diet='vegan',gluten_free=True))


if __name__=='__main__':unittest.main()
