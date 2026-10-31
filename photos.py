"""Offline serving photos with explicit dish/ingredient evidence and honest fallback."""
import json
from pathlib import Path
from preferences import conflicts, normalized, has

BASE = Path(__file__).parent / 'static' / 'photos'
CATALOG = json.loads((Path(__file__).parent / 'photo_catalog.json').read_text(encoding='utf-8'))


def recipe_photo(recipe, prefs):
    name = normalized(recipe['name'])
    ingredients = normalized(' '.join(recipe['ingredients'] + recipe['additional']))
    evidence = name + ' ' + ingredients
    candidates = []
    for key, photo in CATALOG.items():
        rule = photo['match']
        if prefs['diet'] in rule['avoid_diets'] or (prefs['gluten_free'] and rule['avoid_gf']):
            continue
        if conflicts(rule['depicted'], prefs):
            continue
        if not all(any(has(name, term) for term in group) for group in rule['title_groups']):
            continue
        if not all(any(has(ingredients, term) for term in group) for group in rule['ingredient_groups']):
            continue
        if any(has(evidence, term) for term in rule['forbid']):
            continue
        if not (BASE / photo['file']).is_file():
            continue
        score = len(rule['title_groups']) + len(rule['ingredient_groups']) + rule['priority']
        candidates.append((score, key))
    if not candidates:
        return None
    _, key = max(candidates)
    source = CATALOG[key]
    return {k: source[k] for k in ('alt', 'credit', 'source', 'license', 'label')} | {'url': '/static/photos/' + source['file']}
