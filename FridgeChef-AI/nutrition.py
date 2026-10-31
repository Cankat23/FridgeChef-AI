"""Offline ingredient arithmetic from a curated USDA SR Legacy subset.
No AI-generated nutrient numbers; unresolved entries are reported, never silently zeroed.
"""
import json
import re
from fractions import Fraction
from pathlib import Path

DATA=json.loads((Path(__file__).parent/'nutrition_foods.json').read_text())
FIELDS=('kcal','protein_g','carbs_g','fat_g','fiber_g')
ALIASES={a:food for food in DATA['foods'] for a in food['aliases']}
NUMBER=r'(?:\d+\s+\d+/\d+|\d+/\d+|\d+(?:\.\d+)?)'
UNITS=r'(?:kilograms?|kg|grams?|g|milliliters?|millilitres?|ml|liters?|litres?|l|tablespoons?|tbsp|teaspoons?|tsp|cups?|ounces?|oz|pounds?|lb|cloves?|slices?)'


def number(text):
    return float(sum((Fraction(x) for x in text.split()),Fraction()))


def normal(text):
    return re.sub(r'\s+',' ',re.sub(r'[^a-z ]',' ',text.lower())).strip()


def ingredient_name(text):
    text=normal(text)
    text=re.sub(r'\b(?:fresh|finely|roughly|chopped|diced|sliced|grated|peeled|washed|rinsed|minced|crushed|extra|virgin|about|approximately|large|medium|small|whole|to taste|for cooking|for frying|of)\b',' ',text)
    return re.sub(r'\s+',' ',text).strip()


def measure(food, predicate):
    return next((m for m in food['measures'] if predicate(m['measure'].lower())),None)


def resolve(line):
    original=line
    # Do not turn a numeric range into a chosen quantity or a negative into a positive.
    if re.search(r'\d\s*[-–]\s*\d',line) or re.match(r'\s*-\d',line):
        return None,'Ambiguous or negative quantity.'
    for symbol,value in [('½',' 1/2'),('¼',' 1/4'),('¾',' 3/4')]:line=line.replace(symbol,value)
    line=line.strip()
    matched=re.search(r'('+NUMBER+r')\s*('+UNITS+r')\b',line,re.I)
    if matched:
        
        try:quantity=number(matched[1])
        except (ValueError,ZeroDivisionError):return None,'Invalid numeric quantity.'
        unit=matched[2].lower()
        name=line[:matched.start()]+' '+line[matched.end():]
    else:
        count=re.match(r'^('+NUMBER+r')\s+(.+)$',line)
        if not count:return None,'No supported amount; use grams, ml or a counted reference portion.'
        
        try:quantity=number(count[1])
        except (ValueError,ZeroDivisionError):return None,'Invalid numeric quantity.'
        unit='count';name=count[2]
    if quantity<=0 or quantity>100000:return None,'Quantity is outside the supported range.'
    name=ingredient_name(name)
    food=ALIASES.get(name)
    # Counted garlic/bread portions can be written "2 cloves garlic" / "2 slices bread".
    if food is None:return None,'No matching reference food or food state. Use a specific English name and raw/cooked state.'
    notes=[]
    if unit in ('g','gram','grams'):grams=quantity
    elif unit in ('kg','kilogram','kilograms'):grams=quantity*1000
    elif unit in ('oz','ounce','ounces'):grams=quantity*28.349523125
    elif unit in ('lb','pound','pounds'):grams=quantity*453.59237
    elif unit=='count' or unit.startswith('clove') or unit.startswith('slice'):
        requested=('clove' if unit.startswith('clove') else 'slice' if unit.startswith('slice') else None)
        if requested is None:
            size=next((s for s in ('extra large','jumbo','large','medium','small') if re.search(r'\b'+s+r'\b',original.lower())),None)
            requested=size or food['default_count_measure']
        if not requested:return None,'Counted portion has no supported reference weight; supply grams.'
        portion=measure(food,lambda label:label.startswith(requested))
        if not portion:return None,'No matching USDA portion weight; supply grams.'
        grams=quantity*portion['grams']/portion['amount']
        notes.append(f'{original}: used USDA portion "{portion["measure"]}" ({portion["grams"]/portion["amount"]:g} g each).')
    else:
        kind='tbsp' if unit.startswith(('tbsp','tablespoon')) else 'tsp' if unit.startswith(('tsp','teaspoon')) else 'cup' if unit.startswith('cup') else 'ml'
        labels={'tbsp':('tbsp','tablespoon'),'tsp':('tsp','teaspoon'),'cup':('cup',)}
        portion=measure(food,lambda label:any(label==v for v in labels.get(kind,())))
        if portion:
            grams=quantity*portion['grams']/portion['amount']
            notes.append(f'{original}: used USDA {portion["measure"]} reference weight.')
        elif kind=='ml' and food['key']=='water':
            grams=quantity*(1000 if unit in ('l','liter','liters','litre','litres') else 1)
            notes.append(f'{original}: water approximated as 1 g/ml.')
        elif kind=='ml' and food['key'] in ('milk','olive_oil','canola_oil','lemon_juice','lime_juice','soy_sauce','honey'):
            cup=measure(food,lambda label:label=='cup')
            if not cup:return None,'No supported ml-to-weight conversion; supply grams.'
            grams=quantity*(1000 if unit in ('l','liter','liters','litre','litres') else 1)*cup['grams']/cup['amount']/240
            notes.append(f'{original}: volume converted using USDA cup weight and an approximate 240 ml cup.')
        else:return None,'No exact household measure/density match; supply grams.'
    return {'ingredient':original,'grams':grams,'ndb_id':food['ndb_id'],'reference':food['description'],'values':food['per_100g'],'assumptions':notes},None


def estimate(recipe):
    lines=recipe['ingredients']+recipe['additional']
    totals={k:0.0 for k in FIELDS};missing=[];matched=[];notes=[];nutrient_missing=set()
    for line in lines:
        resolved,error=resolve(line)
        if error:
            missing.append({'ingredient':line,'reason':error});continue
        matched.append({k:resolved[k] for k in ('ingredient','grams','ndb_id','reference')})
        notes+=resolved['assumptions']
        for nutrient in FIELDS:
            value=resolved['values'].get(nutrient)
            if value is None:nutrient_missing.add(nutrient)
            else:totals[nutrient]+=value*resolved['grams']/100
    servings=recipe.get('servings')
    if type(servings) is not int or servings<=0:
        return {'status':'unavailable','whole_recipe':{k:None for k in FIELDS},'per_serving':{k:None for k in FIELDS},'missing':[{'ingredient':'Servings','reason':'Unknown portion count.'}],'coverage':{'matched':0,'total':len(lines)},'assumptions':[],'method':'Local USDA SR Legacy ingredient calculation'}
    for key in FIELDS:
        totals[key]=round(totals[key],6) if matched and key not in nutrient_missing else None
    status='unavailable' if not matched else 'incomplete' if missing or nutrient_missing else 'complete'
    return {'status':status,'whole_recipe':totals,'per_serving':{k:(v/servings if v is not None else None) for k,v in totals.items()},'coverage':{'matched':len(matched),'total':len(lines)},'missing':missing,'missing_nutrients':sorted(nutrient_missing),'assumptions':notes,'references':matched,'method':'Local USDA SR Legacy ingredient calculation','source_url':'https://fdc.nal.usda.gov/','note':'Estimated nutrition. Generic reference foods and portion conversions can differ from actual products. Incomplete estimates show known-ingredient subtotals only; omitted ingredients are listed.'}
