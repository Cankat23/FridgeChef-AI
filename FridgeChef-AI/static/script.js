const $=id=>document.getElementById(id);
let items=[],working=false,previewURL;
let clearedSnapshot=null,undoTimer=null,generatedSummary='';
let allergens=[],exclusions=[],configReady=false,hasResults=false,generatedFingerprint=null;
let validationVersion=0,validationTimer=null,currentConflicts=[],validationPending=false;
const photo=$('photo'),output=$('output');
const motion=()=>matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth';
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function icon(name){const s=document.createElementNS('http://www.w3.org/2000/svg','svg'),u=document.createElementNS('http://www.w3.org/2000/svg','use');u.setAttribute('href','#'+name);s.setAttribute('aria-hidden','true');s.append(u);return s;}
function message(text,state='idle'){$('status').textContent=text;$('status-box').dataset.state=state;}
function busy(value){working=value;['generate','photo','choose-photo','remove-photo','ingredient-input','add-button','example','clear-ingredients','undo-clear','current-tab','saved-tab','recipe-sort'].forEach(id=>$(id).disabled=value);$('chips').querySelectorAll('button,input').forEach(n=>n.disabled=value);$('results').setAttribute('aria-busy',String(value));document.querySelectorAll('.preferences input,.preferences select,.preferences button').forEach(n=>n.disabled=value);updateGenerate();updateStale();updateClear();}
function add(value){value.split(/[,;\n]/).map(v=>v.trim()).filter(Boolean).forEach(v=>{if(!items.some(s=>s.toLowerCase()===v.toLowerCase()))items.push(v.slice(0,100));});renderChips();}
function renderChips(){
 $('chips').replaceChildren();$('ingredient-empty').hidden=items.length>0;$('ingredient-count').textContent=items.length+' item'+(items.length===1?'':'s');
 items.forEach((name,index)=>{const chip=el('span',undefined,'chip'),edit=el('button',name,'chip-name'),remove=el('button','×','chip-remove');edit.type=remove.type='button';edit.setAttribute('aria-label','Edit '+name);remove.setAttribute('aria-label','Remove '+name);edit.disabled=remove.disabled=working;
 edit.addEventListener('click',()=>{const field=el('input',undefined,'chip-edit');field.value=name;field.maxLength=100;field.setAttribute('aria-label','Edit ingredient');edit.replaceWith(field);field.focus();field.select();let finished=false;function finish(cancel=false){if(finished)return;finished=true;if(!cancel){const value=field.value.trim();if(value)items[index]=value;else items.splice(index,1);items=items.filter((v,i,a)=>a.findIndex(x=>x.toLowerCase()===v.toLowerCase())===i);}renderChips();}field.addEventListener('blur',()=>finish());field.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();finish();}if(e.key==='Escape')finish(true);});});
 remove.addEventListener('click',()=>{items.splice(index,1);renderChips();message(name+' removed from your list.');$('ingredient-input').focus();});chip.append(edit,remove);$('chips').append(chip);});
 updateClear();changed();
}
$('add-form').addEventListener('submit',e=>{e.preventDefault();if(working)return;const before=items.length;add($('ingredient-input').value);$('ingredient-input').value='';message(items.length>before?(items.length-before)+' ingredient'+(items.length-before===1?'':'s')+' added.':'That ingredient is already on your list.');$('ingredient-input').focus();});
$('example').addEventListener('click',()=>{add('eggs, tomatoes, spinach, cheese, lemon');message('Example ingredients added. Edit them or find your next meal.');});
async function send(url,options){const response=await fetch(url,options);let data;try{data=await response.json();}catch{throw Error('The server response could not be read. Restart the app and try again.');}if(!response.ok)throw Error(data.error||'Request failed. Please try again.');return data;}
function media(recipe){
 const wrapper=el('div',undefined,'recipe-media'),fallback=el('div',undefined,'photo-fallback');const art=icon(illustrationFor(recipe));art.classList.add('serving-art');fallback.append(art,el('span','A little serving inspiration'));wrapper.append(fallback);
 const caption=el('div',undefined,'photo-caption');
 if(recipe.photo){const img=el('img');img.alt=recipe.photo.alt;img.loading='lazy';img.decoding='async';img.width=640;img.height=400;img.src=recipe.photo.url;
 img.addEventListener('error',()=>{img.remove();caption.replaceChildren(el('span','Serving illustration · no matching photo available'));});wrapper.append(img);
 caption.append(el('span',recipe.photo.label+' · '));const credit=el('a',recipe.photo.credit);credit.href=recipe.photo.source;credit.target='_blank';credit.rel='noopener noreferrer';caption.append(credit,el('span',' · '));const license=el('a','License');license.href=recipe.photo.license;license.target='_blank';license.rel='noopener noreferrer';caption.append(license);
 }else caption.textContent='Serving illustration · no matching photo available';
 return [wrapper,caption];
}
function recipeText(r){return r.name+'\n'+r.time+' · '+r.servings+' servings\n'+r.badges.join(' · ')+'\n\n'+r.description+'\n\nFrom your fridge\n'+r.ingredients.join('\n')+'\n\nAlso needed\n'+(r.additional.join('\n')||'None')+'\n\nCooking steps\n'+r.steps.map((s,i)=>(i+1)+'. '+s).join('\n')+'\n\n'+nutritionText(r)+'\n\nAI suggestion: check labels, allergens and cross-contact.';}
function renderRecipes(recipes){currentRecipes=recipes;redrawRecipes();}
function buildRecipeCard(entry,i){
 const r=entry.recipe,card=el('article',undefined,'recipe');card.style.animationDelay=(i*70)+'ms';card.append(...media(r));
 const top=el('div',undefined,'recipe-top');top.append(icon('leaf'),el('span',(activeView==='saved'?'SAVED RECIPE':'IDEA 0'+(i+1)),'recipe-number'));
 const body=el('div',undefined,'recipe-body'),badges=el('div',undefined,'recipe-badges');r.badges.forEach(v=>badges.append(el('span',v)));if(r.badges.length)body.append(badges);
 if(activeView==='saved'){card.dataset.preferenceKey=preferenceKey(entry.preferences);body.append(el('p','Originally: '+entry.summary,'saved-origin'),el('p','Saved with different preferences. Review or regenerate this recipe before cooking.','saved-warning'));}
 const time=el('div',undefined,'time');time.append(icon('clock'),el('span',r.time+' · '+r.servings+' servings'));body.append(el('h3',r.name),time,el('p',r.description,'description'),nutritionPanel(r),el('h4','From your fridge'));
 const list=el('ul');r.ingredients.forEach(v=>list.append(el('li',v)));if(!r.ingredients.length)list.append(el('li','Review ingredients below.'));body.append(list);
 const extras=el('div',undefined,'extras'+(r.additional.length?'':' none'));extras.append(el('strong',r.additional.length?'Also needed':'All set'),el('span',r.additional.length?r.additional.join(' · '):'Everything is already on your list.'));body.append(extras);
 const details=el('details',undefined,'cooking-details'),summary=el('summary','Cooking steps · '+r.steps.length),steps=el('ol');r.steps.forEach(v=>steps.append(el('li',v)));details.append(summary,steps);body.append(details);
 const actions=el('div',undefined,'card-actions'),copy=el('button','Copy recipe','copy-recipe');copy.type='button';copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(recipeText(r));copy.textContent='Copied to clipboard';copy.classList.add('copied');message(r.name+' copied to clipboard.','success');setTimeout(()=>{copy.textContent='Copy recipe';copy.classList.remove('copied');},2000);}catch{message('Copy is unavailable in this browser. Select and copy the recipe text manually.','error');}});
 const key=recipeKey(r,entry.preferences),isSaved=savedRecipes.some(v=>v.key===key),save=el('button',isSaved?'Remove saved':'Save recipe','save-recipe');save.type='button';save.setAttribute('aria-pressed',String(isSaved));save.addEventListener('click',()=>toggleSaved(r,entry.preferences,entry.summary));actions.append(copy,save);body.append(actions);card.append(top,body);return card;
}
function skeleton(){const loading=$('loading-recipes');loading.replaceChildren();loading.hidden=false;for(let i=0;i<3;i++){const card=el('div',undefined,'recipe skeleton');for(let j=0;j<6;j++)card.append(el('span'));loading.append(card);}if(hasResults)output.classList.add('refreshing');else output.hidden=true;$('count').textContent=hasResults?'Refreshing your ideas…':'Cooking up ideas…';}
function finishSkeleton(){$('loading-recipes').hidden=true;$('loading-recipes').replaceChildren();output.hidden=false;output.classList.remove('refreshing');}
$('generate').addEventListener('click',async()=>{
 if(working)return;if(!configReady){message('Preferences are still loading. Refresh the page if this persists.','error');return;}
 add($('ingredient-input').value);$('ingredient-input').value='';commitExclusions();if(!items.length){message('Add at least one ingredient to get started.','error');$('ingredient-input').focus();return;}
 const ingredients=items.join(', ');if(ingredients.length>4000){message('Please shorten your ingredient list to under 4000 characters.','error');return;}
 busy(true);if(!await validateNow()){busy(false);message('Resolve ingredient conflicts before generating.','error');return;}
 const snapshot=fingerprint(),summarySnapshot=$('preference-summary').textContent,prefsSnapshot=JSON.parse(JSON.stringify(getPreferences()));if(activeView!=='current')showRecipeView('current');skeleton();$('generate').replaceChildren(el('span','Creating your recipes…'));message('Your local AI is creating ideas using your preferences. This can take a few minutes.','busy');
 try{const data=await send('/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ingredients,preferences:getPreferences(),servings:Number($('servings').value)})});hasResults=true;generatedFingerprint=snapshot;generatedSummary=summarySnapshot;generatedPreferences=data.preferences||prefsSnapshot;renderRecipes(data.recipes);$('result-preferences').hidden=false;$('result-preferences').textContent='Prepared with: '+generatedSummary;updateStale();message(data.withheld?data.recipes.length+' ideas shown. '+data.withheld+' conflicting ideas were withheld.':'Your recipes are ready. Review ingredients and labels before cooking.','success');$('results').scrollIntoView({behavior:motion(),block:'start'});}catch(e){$('count').textContent=hasResults?'Previous ideas':'Ready to try again';if(!hasResults){output.replaceChildren();const empty=el('div',undefined,'empty'),text=el('div');text.append(el('h3','Let’s try another way.'),el('p','Check the message above, adjust your ingredients or try generating again. Your preferences are kept.'));empty.append(icon('bowl'),text);output.append(empty);}message(e.message+(hasResults?' Your previous recipes are still below.':''),'error');}finally{finishSkeleton();busy(false);$('generate').replaceChildren(el('span','Find my next meal'),icon('arrow'));}
});
$('choose-photo').addEventListener('click',()=>photo.click());
function clearPhoto(){if(previewURL)URL.revokeObjectURL(previewURL);previewURL=null;photo.value='';$('preview').removeAttribute('src');$('preview').hidden=true;$('upload-intro').hidden=false;$('remove-photo').hidden=true;$('choose-photo').replaceChildren(el('span','Choose a photo'));$('file-info').textContent='JPG, PNG or WebP · up to 8 MB';}
$('remove-photo').addEventListener('click',()=>{clearPhoto();message('Photo removed. Your reviewed ingredient list is kept.');});
async function detect(file){
 if(!file||working)return;
 if(!['image/jpeg','image/png','image/webp'].includes(file.type)||!file.size||file.size>8*1024*1024){message('Choose a nonempty JPG, PNG or WebP under 8 MB.','error');photo.value='';return;}
 if(previewURL)URL.revokeObjectURL(previewURL);previewURL=URL.createObjectURL(file);$('preview').src=previewURL;$('preview').hidden=false;$('upload-intro').hidden=true;$('remove-photo').hidden=false;$('choose-photo').textContent='Change photo';$('file-info').textContent=file.name;
 busy(true);message('Looking for recognizable ingredients in your photo. This may take a few minutes.','busy');const form=new FormData();form.append('image',file);
 try{const data=await send('/detect',{method:'POST',body:form});add(data.ingredients);$('review').textContent=data.uncertain.length?'Not added — please identify these yourself: '+data.uncertain.join(', '):'Check the detected names and remove anything the AI misidentified.';message(data.ingredients?'Photo ingredients added to your list. Review them, then find your next meal.':'No clear ingredients found. Try a clearer photo or enter ingredients yourself.',data.ingredients?'success':'idle');}catch(e){message(e.message,'error');}finally{busy(false);}
}
photo.addEventListener('change',()=>detect(photo.files[0]));const zone=$('dropzone');['dragenter','dragover'].forEach(event=>zone.addEventListener(event,e=>{e.preventDefault();if(!working)zone.classList.add('drag');}));['dragleave','drop'].forEach(event=>zone.addEventListener(event,e=>{e.preventDefault();zone.classList.remove('drag');}));zone.addEventListener('drop',e=>detect(e.dataTransfer.files[0]));

function getPreferences(){return {diet:$('diet').value,gluten_free:$('gluten-free').checked,allergens:allergens,exclusions:exclusions};}
function fingerprint(){return JSON.stringify({items,preferences:getPreferences(),servings:$('servings').value});}
function updateGenerate(){$('generate').disabled=working||!configReady||validationPending||currentConflicts.length>0;}
function updateStale(){const stale=activeView==='current'&&hasResults&&fingerprint()!==generatedFingerprint;$('stale-results').hidden=!stale;output.classList.toggle('stale',stale);output.querySelectorAll('.recipe').forEach(card=>{const different=activeView==='saved'&&card.dataset.preferenceKey!==preferenceKey(getPreferences());const warning=card.querySelector('.saved-warning');if(warning)warning.hidden=!different;const copy=card.querySelector('.copy-recipe'),save=card.querySelector('.save-recipe');if(copy)copy.disabled=stale||different||working;if(save)save.disabled=(activeView==='current'&&stale)||working;});}
function changed(){updateStale();updateSummary();clearTimeout(validationTimer);validationPending=true;updateGenerate();validationTimer=setTimeout(validateNow,180);}
function updateSummary(){const p=getPreferences(),parts=[];if(p.diet!=='none')parts.push(p.diet[0].toUpperCase()+p.diet.slice(1));if(p.gluten_free)parts.push('Gluten-free preference');parts.push(...allergens.map(id=>document.querySelector('[data-allergen="'+id+'"]')?.textContent||id),...exclusions.map(v=>'Avoid '+v));$('preference-summary').textContent=(parts.join(' · ')||'No dietary restrictions selected')+' · '+$('servings').value+' servings';}
async function validateNow(){
 clearTimeout(validationTimer);const version=++validationVersion,snapshot=fingerprint();validationPending=true;updateGenerate();
 try{const data=await send('/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ingredients:items.join(', '),preferences:getPreferences()})});
 if(version!==validationVersion||snapshot!==fingerprint())return false;currentConflicts=data.conflicts;$('conflict-box').hidden=!currentConflicts.length;$('conflict-list').replaceChildren();currentConflicts.forEach(c=>$('conflict-list').append(el('li',c.ingredient+' — '+c.reasons.join(', '))));$('chips').querySelectorAll('.chip').forEach((chip,i)=>chip.classList.toggle('conflict',currentConflicts.some(c=>c.ingredient===items[i])));validationPending=false;updateGenerate();return !currentConflicts.length;
 }catch(e){if(version===validationVersion){validationPending=true;message('Ingredient checking is unavailable. '+e.message,'error');updateGenerate();}return false;}
}
function renderExclusions(){
 const box=$('exclusion-chips');box.replaceChildren();
 [...allergens.map(id=>({id,label:document.querySelector('[data-allergen="'+id+'"]')?.textContent||id})),...exclusions.map(v=>({custom:v,label:v}))].forEach(item=>{const chip=el('span',undefined,'chip'),remove=el('button','×','chip-remove');remove.type='button';remove.setAttribute('aria-label','Stop excluding '+item.label);remove.addEventListener('click',()=>{if(item.custom)exclusions=exclusions.filter(v=>v!==item.custom);else{allergens=allergens.filter(v=>v!==item.id);document.querySelector('input[value="'+item.id+'"]').checked=false;}renderExclusions();changed();});chip.append(el('span',item.label,'chip-name'),remove);box.append(chip);});$('exclusion-count').textContent=(allergens.length+exclusions.length)?(allergens.length+exclusions.length)+' selected':'None selected';
}
function commitExclusions(){const value=$('exclusion-input').value;value.split(',').map(v=>v.trim()).filter(Boolean).forEach(v=>{if(exclusions.length<20&&!exclusions.some(x=>x.toLowerCase()===v.toLowerCase()))exclusions.push(v);});$('exclusion-input').value='';renderExclusions();changed();}
$('exclusion-form').addEventListener('submit',e=>{e.preventDefault();commitExclusions();});
['diet','gluten-free','servings'].forEach(id=>$(id).addEventListener('change',()=>{changed();message(hasResults?'Preferences updated. Generate again to update your recipes.':'Preferences updated. Your next recipes will use these choices.');}));
$('clear-preferences').addEventListener('click',()=>{allergens=[];exclusions=[];$('diet').value='none';$('gluten-free').checked=false;$('exclusion-input').value='';document.querySelectorAll('.allergen-choice input').forEach(n=>n.checked=false);renderExclusions();changed();});
(async()=>{try{const data=await send('/config');data.allergens.forEach(a=>{const label=el('label',undefined,'allergen-choice'),input=el('input');input.type='checkbox';input.value=a.id;const text=el('span',a.label);text.dataset.allergen=a.id;input.addEventListener('change',()=>{allergens=input.checked?[...allergens,a.id]:allergens.filter(v=>v!==a.id);renderExclusions();changed();});label.append(input,text);$('allergen-options').append(label);});configReady=true;changed();}catch(e){message('Could not load dietary preferences. Refresh the page.','error');updateGenerate();}})();

function updateClear(){$('clear-ingredients').disabled=working||items.length===0;$('undo-clear').disabled=working;}
$('clear-ingredients').addEventListener('click',()=>{
 if(working||!items.length)return;clearTimeout(undoTimer);clearedSnapshot={items:[...items],draft:$('ingredient-input').value};items=[];$('ingredient-input').value='';renderChips();$('undo-notice').hidden=false;message('Ingredients cleared. Use Undo to restore your list.');
 undoTimer=setTimeout(()=>{clearedSnapshot=null;$('undo-notice').hidden=true;},8000);
});
$('undo-clear').addEventListener('click',()=>{
 if(working||!clearedSnapshot)return;clearTimeout(undoTimer);const restored=[...clearedSnapshot.items,...items];items=restored.filter((v,i,a)=>a.findIndex(x=>x.toLowerCase()===v.toLowerCase())===i);if(!$('ingredient-input').value)$('ingredient-input').value=clearedSnapshot.draft;clearedSnapshot=null;$('undo-notice').hidden=true;renderChips();message('Ingredient list restored.','success');$('ingredient-input').focus();
});
function illustrationFor(recipe){
 if(recipe.illustration)return 'dish-'+recipe.illustration;
 const name=recipe.name.toLowerCase();if(/soup|stew|curry/.test(name))return 'dish-soup';if(/salad/.test(name))return 'dish-salad';if(/pasta|spaghetti|noodle/.test(name))return 'dish-pasta';if(/toast|sandwich/.test(name))return 'dish-toast';if(/pancake|waffle|cake/.test(name))return 'dish-sweet';if(/rice|grain|oat|porridge/.test(name))return 'dish-grain';if(/egg|omelet|scramble|stir.fry/.test(name))return 'dish-skillet';return 'dish-plate';
}

initFeatures();
