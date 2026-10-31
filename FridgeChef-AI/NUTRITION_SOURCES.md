# Estimated nutrition: data and calculation

The application uses a curated offline subset of 71 USDA National Nutrient Database for Standard Reference, Legacy Release (April 2018) foods. The JSON table contains exact NDB identifiers, full reference descriptions, household-measure weights and values per 100 g edible portion. It is not a live product-label or restaurant database.

Official source archive:
https://www.ars.usda.gov/ARSUserFiles/80400525/Data/SR-Legacy/SR-Leg_ASC.zip

Official format documentation:
https://www.ars.usda.gov/arsuserfiles/80400525/data/sr-legacy/sr-legacy_doc.pdf

USDA FoodData Central, data types and public-domain/CC0 information:
https://fdc.nal.usda.gov/
https://fdc.nal.usda.gov/data-documentation/

Suggested attribution: U.S. Department of Agriculture, Agricultural Research Service. USDA National Nutrient Database for Standard Reference, Legacy Release, April 2018. Accessed 31 October 2026. Data made available through USDA ARS / FoodData Central.

## Extraction and units

The local `nutrition_foods.json` retains the SHA-256 of the downloaded source archive. Values were extracted from `NUT_DATA.txt` using nutrient IDs 208 (kcal), 203 (protein g), 205 (carbohydrate by difference g), 204 (total fat g), 291 (dietary fiber g). `FOOD_DES.txt` provides descriptions and `WEIGHT.txt` provides measured serving weights. Missing nutrient data remain null.

`nutrition.py` matches explicit English aliases, parses supported quantities and sums both recipe ingredient lists, including additional oil/sauce ingredients. Grams are multiplied by each reference value per 100 g. Per-serving values divide by the recipe's validated serving count. Kcal come from the USDA energy field, not a forced 4/4/9 approximation; food-specific energy factors and fiber can make those formulas differ.

Supported quantities include g, kg, oz, lb; exact USDA household cup/tbsp/tsp measures when present; ml for selected liquids using reference densities; and supported counted portions such as eggs or tomatoes. Default counted sizes are disclosed. Volume conversion to ml uses an approximate 240 ml cup where needed. Mass, density and count assumptions appear in the expandable explanation.

Dry/cooked rice, pasta, quinoa and legumes have separate records. Bare ambiguous terms such as `rice`, generic `cheese`, unsupported branded/alternative products, ranges, missing quantities, unrecognised portion sizes and zero/negative quantities are not silently assigned a reference value. Use specific food names and grams for better coverage. A juiced whole lemon without a specified juice weight is unresolved rather than treated as the whole fruit.

## Complete, incomplete, unavailable

- Complete/reference estimate: every ingredient line has a usable reference amount and the displayed nutrient exists for every matched food.
- Incomplete estimate: the UI shows known-ingredient subtotals, not a claimed whole-meal total. Unmatched lines and reasons are listed. A missing reference nutrient is displayed as unavailable rather than zero.
- Unavailable: no ingredient could be resolved, or servings are unknown. Values are null, not zeros.

These figures are generic estimates, not measurements of the food a user prepares. Ingredient quantities are still model-generated; actual brands, edible portions, cooking losses and oil retention vary. No AI-generated nutrient numbers are accepted. The server overwrites any model-supplied nutrition field with its own calculation. No daily needs, health scores, safety certifications or personalized dietary prescriptions are calculated.

Only complete per-serving protein estimates participate in protein sorting. Saved recipes retain their original calculated estimate; they are not silently recalculated when the user's preferences or servings change.
