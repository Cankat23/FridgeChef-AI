# FridgeChef AI — nutrition, themes and saved recipes
A local Flask + Ollama application with fridge-photo analysis and real AI recipe generation. The existing Gemma setup is preserved. No paid API, API key, frontend framework or runtime image service is required.

## Windows quick start
1. Extract the entire ZIP into a NEW folder. Do not run files inside the ZIP.
2. Stop your previous Flask server with Ctrl+C. Keep Ollama running.
3. Double-click START_WINDOWS.bat. Python must be available as `python`.
4. Open http://127.0.0.1:5000 and press Ctrl+F5 to refresh cached styles/scripts.
5. Keep the terminal open; Ctrl+C stops the website.

First launch creates a Python virtual environment and installs Flask/requests; this needs internet. The launcher skips installation if dependencies already import successfully. The installed model must already be downloaded. The website, photo library and inference then run locally.

## Latest visual and usability update
- Clear all beside the ingredient counter. Disabled for an empty list. An 8-second Undo restores the list without resetting dietary preferences or the photo. If new ingredients were added after clearing, Undo merges them with the original list.
- Clear all marks earlier recipes as stale. Photo recognition never automatically repopulates a cleared list.
- More consistent card spacing, clearer cooking-step disclosures, purposeful hover/focus states and picture/text skeletons.
- Previous recipe cards remain visible during regeneration and remain available after a generation failure. The saved preference summary stays with those previous results.
- Copy recipe shows clipboard feedback; preference updates and ingredient changes have concise status messages.
- 22 manually reviewed local serving photos. Matching requires dish-title and ingredient evidence and rejects explicit dietary conflicts. Different local vector illustrations cover soups, salads, pasta, grains, eggs/skillets, toast and sweets when there is no suitable match.
- Photo assets were optimized to about 3 MB total; no runtime image service is required.

## Preserved features
- No preference, Vegetarian and Vegan eating styles.
- Independent Gluten-free preference.
- Nine selectable allergen groups: Milk, Eggs, Peanuts, Tree nuts, Soy, Wheat, Sesame, Fish and Shellfish.
- Custom ingredient exclusions with removable tags; clear preferences; active selection summary.
- Shared server-side ingredient checks: conflicting inputs are highlighted and generation is blocked. Client bypasses still encounter server validation.
- Preferences are included in the real model prompt. Returned names, descriptions, ingredients, additional ingredients and steps are screened. Conflicting ideas are withheld. If none pass, no recipe cards are returned; restrictions are not silently relaxed.
- 1–8 servings, included in the AI request and checked on returned recipes.
- 22 optimized local serving-photo categories, including salads, soups, pasta/noodles, rice, legumes, eggs, chicken and fish with conservative matching and visible source/license credits. Other dishes show a local illustration. Some restricted selections use an illustration instead of a potentially misleading stock photo. No runtime network image lookup and no image-generation claim.
- Lazy-loading photos with fixed ratio and error fallback; Copy recipe button; stale recipe warning when ingredients/preferences/servings change.

## Using preferences
Choose eating style, optionally Gluten-free, and open Allergies & exclusions. Select groups or add an English ingredient name. Review red-highlighted conflicting ingredients and edit/remove them before generating. Choosing Vegetarian allows dairy and eggs; Vegan also excludes dairy, eggs, honey and other animal products. Gluten-free checks additional cereals and common products, not just wheat.

Photo results merge with your ingredient list. Always review detected foods. You can change/remove the photo and edit/remove ingredient tags. Removing a photo keeps your reviewed list. A changed preference marks old recipes as previous results and disables copying until recipes are regenerated or the exact original choices are restored.

## Important limits
This is a hackathon cooking assistant, not an allergen-safety certification. AI and keyword screening can miss ingredients, synonyms, hidden derivatives, brands, compound products, preparation details or cross-contact. Rules use English words and conservative matching; false positives are possible. Explicit alternative names such as almond milk are handled separately, but all actual product labels still need review. The UI does not claim a dish is allergy-safe. Check product labels and prevent cross-contact. Vegan selection does not guarantee allergen absence.

Custom exclusions match English names and common plural forms; they do not provide a complete synonym ontology. Nutritional content, cooking completion and consistency of every model-suggested quantity are not independently calculated. Servings are validated; the model is instructed to supply metric quantities and Celsius for the requested servings.

Photo coverage is limited to bundled categories. Serving images can differ in garnish/appearance; they are not exact or personalized photographs. The app uses the recipe title and ingredient list to choose a related photo. It never substitutes a random remote image.

Guidance used when designing the reminder and screening categories:
- https://www.food.gov.uk/business-guidance/allergen-guidance-for-food-businesses
- https://www.food.gov.uk/safety-hygiene/vegan-food-and-allergens
- https://food.ec.europa.eu/food-safety/campaign-2026/allergies_en
See PHOTO_CREDITS.md for all photograph licenses and sources.

## Manual setup
```powershell
python -m pip install -r requirements.txt
python app.py
```
Default model: `gemma4:e2b`, matching your earlier setup. Check `ollama list`. To use a different installed Gemma tag:
```powershell
$env:OLLAMA_MODEL="your-installed-model-tag"
python app.py
```
The selected model must support vision for photo analysis. Photos are processed via the local Ollama endpoint; this app makes no cloud inference calls.

## Troubleshooting
- Connection failure: open Ollama and confirm the model tag.
- Port 5000 already in use: stop the older server.
- Incomplete AI format: generate again; the model must return three structured recipes including the chosen servings.
- No matching recipes: try other ingredients. Conflicting model results are withheld.
- Slow inference: initial loading may take several minutes; smaller photos can help.
- Ingredient checking unavailable: restart the server and refresh the page; generation stays blocked until validation returns.
- No photo: this dish has no suitable bundled match or the file is unavailable; the illustration is intentional.

## Earlier verification
Passed: Python compilation, JavaScript syntax, 12 Python test cases covering all allergen groups, vegetarian/vegan distinctions, gluten beyond wheat, custom exclusions, input rejection before AI, output filtering including steps, servings, photo matching, and detection preservation. DOM behavior tests covered preference controls, conflict blocking, removing ingredients, clearing preferences, request payload, stale-result warnings, copying and image-error fallback using simulated responses.

The latest update adds real-browser desktop/mobile visual checks (see below). Windows execution and live Gemma behavior remain to be tested on your computer.

Run backend tests:
```powershell
python -m unittest discover -s tests -v
```
Test fixtures use mocked Ollama responses; they are never served as real recipes in the app.

## Verification for the latest update
Passed 17 Python test cases, including the existing allergy/dietary checks and new tests for photo matching evidence, all 22 licensed files, wrong-dish rejection, explicit photo conflicts, and plant/gluten-free photo coverage. JavaScript syntax and DOM behavior tests passed, including Clear all/Undo, expiration, preserving preferences/photo, merging later additions on Undo, stale warnings, preserving old cards during loading/error, copy feedback and image fallback.

Desktop and 390px mobile layout were visually checked in a real browser using a separate internal QA preview with clearly labelled simulated API responses. No horizontal overflow was found in the mobile preview. That QA preview and its simulated recipes are NOT in this ZIP or the runtime app.

Still not verified here: Windows batch execution and live Gemma generation/recognition quality or latency on your machine. All actual application recipe requests still go to your real local Ollama; no recipe fixtures are served by the app.

Optional UI behavior tests (Node.js needed only for these development tests):
```powershell
npm install --prefix tests
node tests/test_ui.cjs
```
The main app still requires only Python, Flask, requests and your installed Ollama model.

## Nutrition, theme and saved recipes update
- Every new recipe receives a local ingredient-based nutrition calculation. Cards show estimated kcal, protein, carbs, fat and fiber, with Per serving / Whole recipe controls. Expand How this was estimated for reference IDs, portion assumptions and unmatched ingredients.
- The offline table covers 71 reference foods from USDA SR Legacy 2018. Both available and additional ingredient quantities are counted, including oil. This is NOT an AI nutrient guess or a complete branded-food database. Unknown food types/states or amounts produce Incomplete estimate / Unavailable. Incomplete values are explicitly known-ingredient subtotals only. See NUTRITION_SOURCES.md.
- Copy recipe includes both nutrition bases, method, missing ingredients and portion assumptions.
- Top-right Theme control: System, Light, Dark. The first paint respects system/stored choice; only the chosen theme setting is persisted.
- Sort: original order, quickest (unknown times last) and highest estimated protein. Only complete protein estimates are ranked numerically; incomplete/unknown estimates remain at the end. Protein sort is disabled when no complete values exist.
- Save recipe stores the recipe, original nutrition, servings and generation preferences in this browser's localStorage (maximum 50). The Saved recipes tab supports removal. No account or cloud storage is involved. Clearing browser site data removes these saved recipes.
- A saved recipe whose original dietary preferences differ from the current choices shows a review/regeneration warning and disables copying. It is not automatically certified as suitable under the new preferences. Its original portions are preserved.
- All previous allergy checks, photographs, Clear all/Undo, real Ollama generation and image detection remain.

For a clean update: stop the old server, extract this ZIP to a NEW folder, launch START_WINDOWS.bat, then open http://127.0.0.1:5000 and refresh with Ctrl+F5. No new runtime dependency or API key is required. Initial Python dependencies/model downloads still need internet; all nutrition/photographs/inference subsequently run locally.

Latest checks: 23 Python test cases passed, including oil/extra ingredient inclusion, per-serving division, unknown amounts/states, invalid numeric quantities, reference data provenance, and rejecting AI nutrition overrides. Expanded DOM tests passed for nutrition toggles/copy, incomplete estimates, sorting unknown values, saving/removal, saved preference warnings, persisted/pre-CSS theme and the earlier Clear all/Undo/conflict/image/error paths. Light/dark layouts were inspected in a real browser using a separate clearly labelled fixture preview; mobile width had no horizontal overflow. Preview fixtures are never packaged or served by the actual app.

Still not verified here: executing the batch launcher on Windows and live Gemma output quality, speed, and ingredient-quantity consistency on your machine. Generic reference estimates cannot establish actual nutrition or allergen safety. LocalStorage persistence can be unavailable in restricted/private browser environments; the app reports failed saves.
