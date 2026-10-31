"""Conservative English ingredient screening, not a food-safety certification.
Rules intentionally prefer withholding an uncertain result over presenting a conflict.
"""
import re

ALLERGENS = {
    'milk': ('Milk', ['milk', 'butter', 'cheese', 'cream', 'yogurt', 'yoghurt', 'whey', 'casein', 'ghee', 'paneer', 'feta', 'parmesan', 'mozzarella', 'ricotta', 'buttermilk']),
    'egg': ('Eggs', ['egg', 'eggs', 'mayonnaise', 'mayo', 'albumen', 'meringue']),
    'peanut': ('Peanuts', ['peanut', 'peanuts', 'groundnut', 'groundnuts', 'arachis', 'satay']),
    'tree_nut': ('Tree nuts', ['almond', 'almonds', 'walnut', 'walnuts', 'cashew', 'cashews', 'pecan', 'pecans', 'pistachio', 'pistachios', 'hazelnut', 'hazelnuts', 'macadamia', 'brazil nut', 'pine nut', 'nuts', 'nut butter', 'marzipan', 'pesto', 'praline']),
    'soy': ('Soy', ['soy', 'soya', 'soybean', 'soybeans', 'tofu', 'tempeh', 'edamame', 'miso', 'tamari']),
    'wheat': ('Wheat', ['wheat', 'spelt', 'semolina', 'bulgur', 'couscous', 'farro', 'durum', 'seitan', 'flour', 'bread', 'pasta', 'noodles', 'breadcrumbs', 'panko', 'tortilla']),
    'sesame': ('Sesame', ['sesame', 'tahini', 'benne']),
    'fish': ('Fish', ['fish', 'salmon', 'tuna', 'cod', 'haddock', 'trout', 'anchovy', 'anchovies', 'sardine', 'sardines', 'mackerel', 'bonito', 'worcestershire', 'dashi']),
    'shellfish': ('Shellfish', ['shellfish', 'shrimp', 'prawn', 'prawns', 'crab', 'lobster', 'crayfish', 'mussel', 'mussels', 'clam', 'clams', 'oyster', 'oysters', 'scallop', 'scallops', 'squid', 'octopus']),
}
MEAT = ['meat', 'beef', 'pork', 'chicken', 'turkey', 'lamb', 'duck', 'bacon', 'ham', 'sausage', 'sausages', 'salami', 'pepperoni', 'prosciutto', 'gelatin', 'gelatine', 'lard', 'tallow', 'beef broth', 'chicken stock', 'bone broth']
GLUTEN = ['wheat', 'spelt', 'barley', 'rye', 'triticale', 'semolina', 'bulgur', 'couscous', 'farro', 'durum', 'seitan', 'malt', 'flour', 'bread', 'pasta', 'noodles', 'breadcrumbs', 'panko', 'tortilla', 'soy sauce', 'oat', 'oats', 'oatmeal', 'beer']
PLANT_MILK = r'\b(?:almond|oat|coconut|soy|soya|rice|cashew|pea|hemp)\s+(?:milk|cream|yogurt|yoghurt)\b'
PLANT_DAIRY = r'\b(?:vegan|plant based|dairy free)\s+(?:butter|cheese|cream|yogurt|yoghurt|milk|mayo|mayonnaise)\b'


def normalized(text):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', text.casefold())).strip()


def has(text, phrase):
    pattern = re.escape(phrase).replace(r'\ ', r'\s+')
    if phrase.endswith('y') and len(phrase)>1 and phrase[-2] not in 'aeiou':
        pattern = re.escape(phrase[:-1]).replace(r'\ ', r'\s+') + r'(?:y|ies)'
    elif not phrase.endswith('s'):
        pattern += r'(?:s|es)?'
    return bool(re.search(r'\b' + pattern + r'\b', text))


def parse_preferences(data):
    if not isinstance(data, dict):
        raise ValueError('Preferences must be an object.')
    diet = data.get('diet', 'none')
    gf = data.get('gluten_free', False)
    allergy = data.get('allergens', [])
    custom = data.get('exclusions', [])
    if diet not in ('none', 'vegetarian', 'vegan') or type(gf) is not bool:
        raise ValueError('Invalid dietary preferences.')
    if not isinstance(allergy, list) or not all(isinstance(x, str) and x in ALLERGENS for x in allergy):
        raise ValueError('Choose valid allergens.')
    if not isinstance(custom, list) or len(custom) > 20 or not all(isinstance(x, str) and 0 < len(x.strip()) <= 80 for x in custom):
        raise ValueError('Use up to 20 exclusions, each under 80 characters.')
    if any(not re.search('[a-zA-Z]', x) for x in custom):
        raise ValueError('Write ingredient exclusions using English names.')
    return {'diet': diet, 'gluten_free': gf, 'allergens': list(dict.fromkeys(allergy)), 'exclusions': list(dict.fromkeys(x.strip() for x in custom))}


def clean_for_group(text, group):
    text = normalized(text)
    if group in ('milk', 'vegan'):
        text = re.sub(PLANT_MILK, ' plant drink ', text)
        text = re.sub(PLANT_DAIRY, ' plant alternative ', text)
        text = re.sub(r'\bcoconut\s+(?:butter|cream)\b', ' coconut ', text)
        text = re.sub(r'\b(?:peanut|almond|cashew|hazelnut|sunflower)\s+butter\b', ' plant spread ', text)
        text = re.sub(r'\bcocoa\s+butter\b', ' cocoa ', text)
    if group == 'egg':
        text = re.sub(r'\b(?:vegan|egg free)\s+(?:mayo|mayonnaise)\b', ' plant spread ', text)
    if group in ('wheat', 'gluten'):
        text = re.sub(r'\b(?:rice|corn|maize|chickpea|almond|coconut|buckwheat|potato|tapioca)\s+(?:flour|noodles|pasta|tortilla|tortillas)\b', ' alternative grain ', text)
        # A gluten-free claim does not override a wheat allergy (e.g. wheat starch).
        text = re.sub(r'\bgluten\s+free\s+(?:bread|pasta|noodles|breadcrumbs|flour|oats|oatmeal|tortilla|soy sauce)\b', ' labelled alternative ', text)
    return text


def conflicts(text, prefs):
    found = []
    for key in prefs['allergens']:
        label, terms = ALLERGENS[key]
        if any(has(clean_for_group(text, key), term) for term in terms):
            found.append(label)
    if prefs['gluten_free'] and any(has(clean_for_group(text, 'gluten'), t) for t in GLUTEN):
        found.append('Gluten-free preference')
    if prefs['diet'] in ('vegetarian', 'vegan'):
        animal = MEAT + ALLERGENS['fish'][1] + ALLERGENS['shellfish'][1]
        if any(has(normalized(text), t) for t in animal):
            found.append(prefs['diet'].capitalize() + ' preference')
    if prefs['diet'] == 'vegetarian' and has(normalized(text), 'parmesan') and not has(normalized(text), 'vegetarian parmesan'):
        found.append('Vegetarian preference (check rennet)')
    if prefs['diet'] == 'vegan':
        vegan_terms = ALLERGENS['milk'][1] + ALLERGENS['egg'][1] + ['honey', 'beeswax', 'rennet']
        if any(has(clean_for_group(text, 'vegan'), t) for t in vegan_terms):
            found.append('Vegan preference')
    for exclusion in prefs['exclusions']:
        phrase = normalized(exclusion)
        # Common plural spelling, plus exact multiword phrases. Not a full ontology.
        variants = [phrase, phrase + 's', phrase + 'es']
        if phrase.endswith('y'):
            variants.append(phrase[:-1] + 'ies')
        if phrase.endswith('s'):
            variants.append(phrase[:-1])
        if phrase.endswith('ies'):
            variants.append(phrase[:-3] + 'y')
        if any(has(normalized(text), v) for v in variants):
            found.append('Exclude ' + exclusion)
    return list(dict.fromkeys(found))


def input_conflicts(ingredients, prefs):
    return [{'ingredient': v.strip(), 'reasons': reasons}
            for v in re.split(r'[,;\n]', ingredients) if v.strip()
            if (reasons := conflicts(v, prefs))]


def preference_badges(prefs):
    result = []
    if prefs['diet'] != 'none': result.append(prefs['diet'].capitalize() + ' preference')
    if prefs['gluten_free']: result.append('Gluten-free preference')
    if prefs['allergens'] or prefs['exclusions']: result.append('Exclusions requested')
    return result
