const {parseHTML}=require('linkedom'),fs=require('fs'),vm=require('vm'),assert=require('assert');
const root=require('path').resolve(__dirname,'..');
const {window}=parseHTML(fs.readFileSync(root+'/templates/index.html','utf8'));
const doc=window.document;
// linkedom does not implement layout or native form defaults; supply select/checkbox semantics.
Object.defineProperty(window.HTMLSelectElement.prototype,'value',{get(){return this.querySelector('option[selected]')?.getAttribute('value')||this.querySelector('option[selected]')?.textContent||this.querySelector('option')?.getAttribute('value')||this.querySelector('option')?.textContent||''},set(v){this.querySelectorAll('option').forEach(o=>{if((o.getAttribute('value')||o.textContent)===String(v))o.setAttribute('selected','');else o.removeAttribute('selected');});}});
window.HTMLElement.prototype.scrollIntoView=function(){};window.HTMLElement.prototype.focus=function(){};
const storage=new Map(),localStorage={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,String(v))};let copied='',generateBody,deferGenerate=false,releaseGenerate,failNextGenerate=false;const undoCallbacks=[],undoHandles=[];const schedule=(fn,ms)=>{const h=setTimeout(fn,ms);if(ms===8000){undoCallbacks.push(fn);undoHandles.push(h);}return h;};const event=(node,name)=>node.dispatchEvent(new window.Event(name,{bubbles:true,cancelable:true}));
const recipe={name:'Green Tomato Salad',time:'15 min',servings:2,description:'A bright salad.',ingredients:['100 g spinach','2 tomatoes'],additional:['1 tbsp olive oil'],steps:['Wash and toss.'],badges:[],photo:{url:'/static/photos/salad.jpg',alt:'Serving suggestion',label:'Serving suggestion',credit:'CC0',source:'https://commons.wikimedia.org/wiki/File:Vegetable_Salad_(Unsplash).jpg'}};
const allergenIds=['milk','egg','peanut','tree_nut','soy','wheat','sesame','fish','shellfish'];
let mockRecipes=[recipe];
const fetch=async(url,opts)=>{
 const body=opts?.body?JSON.parse(opts.body):{};
 if(url==='/config')return {ok:true,json:async()=>({allergens:allergenIds.map(id=>({id,label:id==='egg'?'Eggs':id}))})};
 if(url==='/validate')return {ok:true,json:async()=>({conflicts:body.preferences.diet==='vegan'&&body.ingredients.includes('eggs')?[{ingredient:'eggs',reasons:['Vegan preference']}]:[]})};
 if(url==='/generate'){generateBody=body;if(deferGenerate)await new Promise(r=>releaseGenerate=r);if(failNextGenerate){failNextGenerate=false;return {ok:false,json:async()=>({error:'Simulated generation failure'})};}return {ok:true,json:async()=>({recipes:mockRecipes,withheld:0})};}
 throw Error('Unexpected URL '+url);
};
const context=vm.createContext({document:doc,window,fetch,console,setTimeout:schedule,clearTimeout,matchMedia:()=>({matches:true}),localStorage,navigator:{clipboard:{writeText:async s=>{copied=s;}}},URL,FormData});
vm.runInContext(fs.readFileSync(root+'/static/theme-init.js','utf8'),context);vm.runInContext(fs.readFileSync(root+'/static/features.js','utf8'),context);vm.runInContext(fs.readFileSync(root+'/static/script.js','utf8'),context);
const $=id=>doc.getElementById(id),tick=()=>new Promise(r=>setTimeout(r,240));
(async()=>{
 await tick();assert.equal(doc.querySelectorAll('.allergen-choice').length,9);assert.equal($('generate').disabled,false);
 $('ingredient-input').value='eggs, spinach';event($('add-form'),'submit');await tick();
 $('diet').value='vegan';event($('diet'),'change');await tick();assert.equal($('conflict-box').hidden,false);assert.equal($('generate').disabled,true);
 doc.querySelector('[aria-label="Remove eggs"]').click();await tick();assert.equal($('conflict-box').hidden,true);assert.equal($('generate').disabled,false);
 $('exclusion-input').value='mushrooms';event($('exclusion-form'),'submit');await tick();assert.ok($('preference-summary').textContent.includes('mushrooms'));
 $('clear-preferences').click();await tick();assert.equal(doc.querySelectorAll('#exclusion-chips .chip').length,0);
 $('generate').click();await tick();assert.equal(generateBody.servings,2);assert.equal(generateBody.preferences.diet,'none');assert.equal(doc.querySelectorAll('.recipe').length,1);
 const copy=doc.querySelector('.copy-recipe');assert.equal(copy.disabled,false);copy.click();await tick();assert.ok(copied.includes('Cooking steps'));assert.ok(copied.includes('100 g spinach'));
 const img=doc.querySelector('.recipe-media img');event(img,'error');assert.equal(doc.querySelector('.recipe-media img'),null);assert.ok(doc.querySelector('.photo-caption').textContent.includes('illustration'));
 $('gluten-free').checked=true;event($('gluten-free'),'change');await tick();assert.equal($('stale-results').hidden,false);assert.equal(copy.disabled,true);
 $('servings').value='4';event($('servings'),'change');await tick();assert.ok($('preference-summary').textContent.includes('4 servings'));
 $('diet').value='vegan';event($('diet'),'change');await tick();
 $('preview').src='test-preview.jpg';$('preview').hidden=false;
 $('clear-ingredients').click();await tick();assert.equal($('ingredient-count').textContent,'0 items');assert.equal($('clear-ingredients').disabled,true);assert.equal($('undo-notice').hidden,false);assert.equal($('diet').value,'vegan');assert.ok($('preview').src.includes('test-preview.jpg'));assert.equal($('stale-results').hidden,false);
 $('undo-clear').click();await tick();assert.equal($('ingredient-count').textContent,'1 item');assert.equal($('undo-notice').hidden,true);assert.equal($('diet').value,'vegan');
 $('ingredient-input').value='tomatoes';event($('add-form'),'submit');await tick();$('clear-ingredients').click();await tick();$('ingredient-input').value='rice';event($('add-form'),'submit');await tick();$('undo-clear').click();await tick();assert.equal($('ingredient-count').textContent,'3 items');
 const prior=doc.querySelector('.recipe'),priorSummary=$('result-preferences').textContent;deferGenerate=true;failNextGenerate=true;$('generate').click();await tick();assert.equal(doc.querySelector('#output .recipe'),prior);assert.equal($('loading-recipes').hidden,false);assert.equal(doc.querySelectorAll('#loading-recipes .skeleton').length,3);releaseGenerate();await tick();assert.equal(doc.querySelector('#output .recipe'),prior);assert.equal($('loading-recipes').hidden,true);assert.ok($('status').textContent.includes('previous recipes'));assert.equal($('result-preferences').textContent,priorSummary);
 $('clear-ingredients').click();await tick();undoCallbacks.at(-1)();assert.equal($('undo-notice').hidden,true);$('undo-clear').click();await tick();assert.equal($('ingredient-count').textContent,'0 items');undoHandles.forEach(clearTimeout);

 // Nutrition, sort and browser-local saved recipe fixtures; never runtime recipes.
 const nutrition={status:'complete',method:'Local USDA SR Legacy ingredient calculation',whole_recipe:{kcal:420,protein_g:40,carbs_g:20,fat_g:20,fiber_g:4},per_serving:{kcal:210,protein_g:20,carbs_g:10,fat_g:10,fiber_g:2},coverage:{matched:3,total:3},missing:[],missing_nutrients:[],assumptions:[],references:[]};
 mockRecipes=[{...recipe,name:'Slow Garden Bowl',time:'40 min',nutrition},{...recipe,name:'Quick Tomato Bowl',time:'10 min',nutrition:{...nutrition,per_serving:{...nutrition.per_serving,protein_g:5}}},{...recipe,name:'Unknown Bowl',time:'Unknown',nutrition:{...nutrition,status:'incomplete',missing:[{ingredient:'Unknown sauce',reason:'No reference food'}],coverage:{matched:2,total:3},per_serving:{...nutrition.per_serving,protein_g:100}}}];
 deferGenerate=false;$('clear-preferences').click();$('servings').value='2';event($('servings'),'change');$('ingredient-input').value='spinach, tomatoes';event($('add-form'),'submit');await tick();$('generate').click();await tick();assert.equal(doc.querySelectorAll('.recipe').length,3);
 const panel=doc.querySelector('.nutrition-panel');assert.ok(panel.textContent.includes('~210'));panel.querySelectorAll('.nutrition-toggle button')[1].click();assert.ok(panel.textContent.includes('~420'));assert.ok(panel.textContent.includes('whole recipe'));assert.ok(doc.querySelectorAll('.nutrition-panel')[2].textContent.includes('Incomplete estimate'));
 $('recipe-sort').value='quickest';event($('recipe-sort'),'change');assert.equal(doc.querySelector('.recipe h3').textContent,'Quick Tomato Bowl');
 $('recipe-sort').value='protein';event($('recipe-sort'),'change');assert.equal(doc.querySelector('.recipe h3').textContent,'Slow Garden Bowl');assert.equal(doc.querySelectorAll('.recipe h3')[2].textContent,'Unknown Bowl');
 doc.querySelector('.copy-recipe').click();await tick();assert.ok(copied.includes('Estimated nutrition'));assert.ok(copied.includes('Per serving'));assert.ok(copied.includes('Whole recipe'));
 doc.querySelector('.save-recipe').click();assert.equal($('saved-count').textContent,'1');assert.equal(JSON.parse(storage.get('fridgechef.saved.v1'))[0].recipe.servings,2);
 $('saved-tab').click();assert.equal(doc.querySelectorAll('.recipe').length,1);assert.equal(doc.querySelector('.saved-warning').hidden,true);
 $('diet').value='vegan';event($('diet'),'change');await tick();assert.equal(doc.querySelector('.saved-warning').hidden,false);assert.equal(doc.querySelector('.copy-recipe').disabled,true);assert.ok(doc.querySelector('.saved-origin').textContent.includes('No dietary restrictions'));
 doc.querySelector('.save-recipe').click();assert.equal($('saved-count').textContent,'0');assert.ok(outputText().includes('Keep your kitchen favourites'));
 $('theme-choice').value='dark';event($('theme-choice'),'change');assert.equal(doc.documentElement.dataset.theme,'dark');assert.equal(storage.get('fridgechef.theme'),'dark');$('theme-choice').value='light';event($('theme-choice'),'change');assert.equal(doc.documentElement.dataset.theme,'light');
 // A stored selection is applied by the pre-CSS script, before main UI initialization.
 storage.set('fridgechef.theme','dark');vm.runInContext(fs.readFileSync(root+'/static/theme-init.js','utf8'),context);assert.equal(doc.documentElement.dataset.theme,'dark');
 console.log('PASS: nutrition basis/copy, incomplete status, stable sorting with unknown values, saved/remove/preferences warning, persisted theme; existing Clear all/Undo and conflict/photo checks');
 function outputText(){return $('output').textContent;}
})();
