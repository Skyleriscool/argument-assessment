'use strict';
const $ = id => document.getElementById(id);
let turns = [], submitted = null, original = null, latest = null, busy = false;
const count = text => Array.from(text).length;
const names = {logic:'Logic', evidence:'Evidence', relevance:'Relevance', counterargument_handling:'Counterarguments'};
function node(tag, text, className) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(className)n.className=className; return n; }
function progress(step) { for(const s of ['write','review','results']) { const e=$('step-'+s); e.removeAttribute('aria-current'); if(s===step)e.setAttribute('aria-current','step'); } }
function hideResults() { $('results').hidden=true; $('comparison').replaceChildren(); submitted=null; original=null; latest=null; }
function error(message) { $('error').textContent=message; $('error').hidden=!message; }
function updateCount() {
  const size=count($('transcript').value)+($('mode').value==='conversation'?count($('context').value):0);
  $('counter').textContent=`${size.toLocaleString()} / 4,000`; $('counter').classList.toggle('over',size>4000);
  $('continue').disabled=busy || !$('transcript').value.trim() || size>4000;
}
function edited() { hideResults(); $('review').hidden=true; $('confirmed').checked=false; error(''); $('status').textContent=''; progress('write'); updateCount(); }
function inputData() {
  const speakers=new Map();
  return {reviewed:$('confirmed').checked,context:$('context').value,turns:turns.map((t,i)=>{
    const label=t.label.trim(); if(!speakers.has(label))speakers.set(label,`s${speakers.size+1}`);
    const out={turn_id:`t${i+1}`,speaker_id:speakers.get(label),speaker_label:label,text:t.text};
    if(t.groupMode==='none')out.argument_groups=[];
    if(t.groupMode==='manual')out.argument_groups=t.groups.split(/\n\s*\n/).map(x=>x.trim()).filter(Boolean);
    return out;
  })};
}
function reviewValid() {
  const size=turns.reduce((n,t)=>n+count(t.text),count($('context').value));
  $('review-counter').textContent=`Reviewed text and context: ${size.toLocaleString()} / 4,000 characters`;
  const groupsOK=turns.every(t=>t.groupMode!=='manual'||(t.groups.trim() && t.groups.split(/\n\s*\n/).every(g=>g.trim()&&t.text.includes(g.trim()))));
  $('analyze').disabled=busy||!$('confirmed').checked||!turns.length||size>4000||!groupsOK||turns.some(t=>!t.text.trim()||!t.label.trim());
}
function reviewEdited() { hideResults(); $('confirmed').checked=false; $('status').textContent=''; error(''); progress('review'); reviewValid(); }
function renderTurns() {
  $('turns').replaceChildren();
  turns.forEach((turn,i)=>{
    const card=node('div',undefined,'turn'), heading=node('header'); heading.append(node('h3',`Turn ${i+1}`));
    const remove=node('button','Remove','text-button'); remove.type='button'; remove.setAttribute('aria-label',`Remove turn ${i+1}`);remove.onclick=()=>{turns.splice(i,1);reviewEdited();renderTurns();};heading.append(remove);card.append(heading);
    function field(tag,key,labelText) { const id=`turn-${i}-${key}`,label=node('label',labelText);label.htmlFor=id; const input=node(tag);input.id=id;input.value=turn[key];if(tag==='input')input.type='text';else input.rows=3; input.oninput=()=>{turn[key]=input.value;reviewEdited();};card.append(label,input);return input; }
    field('input','label','Speaker');field('textarea','text','Turn text');
    const label=node('label','Argument grouping');label.htmlFor=`group-${i}`;const select=node('select');select.id=`group-${i}`;
    for(const [value,text] of [['auto','Let the model identify arguments'],['manual','Set argument groups'],['none','No assessable argument']]){const opt=node('option',text);opt.value=value;select.append(opt);}select.value=turn.groupMode;card.append(label,select);
    const groupBox=node('div');const gl=node('label','Exact excerpts, separated by a blank line');gl.htmlFor=`excerpts-${i}`;const area=node('textarea');area.id=`excerpts-${i}`;area.rows=4;area.value=turn.groups;area.oninput=()=>{turn.groups=area.value;reviewEdited();};groupBox.append(gl,area,node('p','Each excerpt must appear in this turn exactly as written.','hint'));groupBox.hidden=turn.groupMode!=='manual';card.append(groupBox);
    select.onchange=()=>{turn.groupMode=select.value;if(select.value==='manual'&&!turn.groups){turn.groups=turn.text;area.value=turn.groups;}groupBox.hidden=select.value!=='manual';reviewEdited();};
    $('turns').append(card);
  });reviewValid();
}
function detect(text) {
  const result=[];
  for(const line of text.split('\n')) {
    if(!line.trim())continue;
    const match=line.match(/^([^:\n]{1,60}):\s*(.*)$/);
    if(match)result.push({label:match[1].trim(),text:match[2]});
    else if(result.length)result[result.length-1].text+='\n'+line;
    else result.push({label:'You',text:line});
  }
  return result.map(t=>({...t,groupMode:'auto',groups:''}));
}
async function request(path,payload) {
  busy=true;error(''); const controls=[...document.querySelectorAll('button,input,textarea,select')].map(e=>[e,e.disabled]);controls.forEach(([e])=>e.disabled=true);
  $('status').textContent=path==='/api/quality'?'Scoring your argument…':'Assessing your conversation locally. This can take a few minutes. Please keep this page open.';
  try { const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await response.json();if(!response.ok)throw new Error(data.error||'The request could not be completed.');return data; }
  catch(e){error(e.message==='Failed to fetch'?'The app lost its connection to the local service. Restart the web app, then try again. Your input is still in this page.':e.message);return null;}
  finally{busy=false;controls.forEach(([e,disabled])=>e.disabled=disabled);$('status').textContent='';updateCount();reviewValid();}
}
function score(value) { const p=node('div',undefined,'score');p.append(document.createTextNode(Number(value).toFixed(2).replace(/\.00$/,'')),node('small',' / 100'));return p; }
function renderAssessment(data,input,container) {
  container.replaceChildren();const labels=Object.fromEntries(input.turns.map(t=>[t.speaker_id,t.speaker_label]));
  container.append(node('h3','Participant averages'));
  const people=node('div');for(const p of data.participants){const card=node('div',undefined,'participant');card.append(node('h3',labels[p.speaker_id]||p.speaker_id));card.append(p.average===null?node('p','Not enough assessable arguments','hint'):score(p.average));card.append(node('p',p.limited_sample?'One argument · limited sample':`${p.assessable_arguments} assessable arguments`,'hint'));people.append(card);}container.append(people);
  const summary=data.assessment.conversation_summary;container.append(node('h3','Points of disagreement'));
  if(!summary.key_disagreements.length)container.append(node('p','No clear disagreement identified.'));
  else {const ul=node('ul');summary.key_disagreements.forEach(t=>ul.append(node('li',t)));container.append(ul);}
  if(summary.strongest_arguments.length){container.append(node('h3','Strongest argument from each participant'));for(const a of summary.strongest_arguments)container.append(node('p',`${labels[a.speaker_id]||a.speaker_id}: ${a.explanation}`));}
  data.assessment.turns.forEach((turn,i)=>{
    const section=node('section',undefined,'argument');section.append(node('h3',`${labels[turn.speaker_id]||turn.speaker_id} · Turn ${i+1}`));
    if(turn.status==='not_assessable'){section.append(node('p','Not assessable'),node('p',turn.reason,'hint'));}
    else for(const a of turn.arguments){section.append(node('blockquote',a.argument_excerpt),score(a.overall_score));const criteria=node('div',undefined,'criteria');for(const [key,value] of Object.entries(a.criterion_scores)){const row=node('div',undefined,'criterion');row.append(node('span',names[key]||key),node('strong',String(value)));criteria.append(row);}section.append(criteria,node('p',a.rationale),node('h3','A way to strengthen it'),node('p',a.improvement_suggestion));for(const e of a.evidence)section.append(node('p',`${names[e.criterion]} · ${e.role}: “${e.quote}”`,'hint'));const u=node('div',`Uncertainty: ${a.uncertainty.level}. ${a.uncertainty.reasons.join(' ')}`,'uncertainty');section.append(u);}
    container.append(section);
  });
  if(data.arithmetic_adjustments?.length){container.append(node('p',data.arithmetic_adjustments.join(' '),'hint'));}
}
function showResults() { $('results').hidden=false;progress('results');$('results-title').focus();$('results').scrollIntoView({behavior:'smooth',block:'start'}); }
$('transcript').oninput=edited;$('context').oninput=edited;
$('mode').onchange=()=>{const quick=$('mode').value==='quality';$('context-wrap').hidden=quick;document.querySelector('label[for=transcript]').textContent=quick?'Your argument':'Your conversation';$('continue').textContent=quick?'Score this argument':'Review conversation';$('mode-help').textContent=quick?'A quick IBM speech-suitability estimate, not the four-criterion conversation assessment.':'Use a speaker label for each turn, like “Alex: We should take the bus because…”';edited();};
$('example').onclick=()=>{ $('transcript').value=$('mode').value==='quality'?'We should take the bus because parking costs more than the fare.':"Alex: Let's meet at the library because it's free.\nBlair: I'd prefer the cafe because the library closes early.";edited();$('transcript').focus();};
$('clear').onclick=()=>{$('transcript').value='';$('context').value='';$('challenge').value='';turns=[];edited();$('transcript').focus();};
$('continue').onclick=async()=>{
  hideResults();error('');
  if($('mode').value==='quality'){const r=await request('/api/quality',{text:$('transcript').value});if(!r)return;latest=r;$('result-body').replaceChildren(node('h3','IBM argument-quality estimate'),score(r.display_score),node('p',r.notice));if(r.distribution_warning)$('result-body').append(node('p',r.distribution_warning,'hint'));$('challenge-wrap').hidden=true;showResults();return;}
  turns=detect($('transcript').value);$('confirmed').checked=false;renderTurns();$('review').hidden=false;progress('review');$('review-title').focus();$('review').scrollIntoView({behavior:'smooth',block:'start'});
};
$('back').onclick=()=>{edited();$('transcript').focus();};
$('add-turn').onclick=()=>{turns.push({label:'',text:'',groupMode:'auto',groups:''});reviewEdited();renderTurns();$(`turn-${turns.length-1}-label`).focus();};
$('confirmed').onchange=reviewValid;
$('analyze').onclick=async()=>{const input=inputData();hideResults();const result=await request('/api/assess',input);if(!result)return;submitted=structuredClone(input);original=result;latest=result;renderAssessment(result,submitted,$('result-body'));$('challenge-wrap').hidden=false;$('challenge').value='';showResults();};
$('reconsider').onclick=async()=>{if(!$('challenge').value.trim()){error('Describe what you would like reconsidered first.');$('challenge').focus();return;}if(!submitted||!original)return;const result=await request('/api/challenge',{input:submitted,original,challenge:$('challenge').value});if(!result)return;latest=result;const box=$('comparison');box.replaceChildren(node('h3','Original and revised assessments'));box.append(node('p','A revision may still be wrong. Compare the reasoning, not just the numbers.','hint'));if(!result.changes.length)box.append(node('p','No changes were made.'));for(const c of result.changes)box.append(node('p',`${c.turn_id}: ${c.explanation}`));const columns=node('div',undefined,'comparison');for(const [key,title] of [['original','Original'],['revised','Revised']]){const col=node('div');col.append(node('h2',title));const body=node('div');renderAssessment(result[key],submitted,body);col.append(body);columns.append(col);}box.append(columns);box.scrollIntoView({behavior:'smooth',block:'start'});};
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText($('result-body').innerText+($('comparison').innerText?'\n\n'+$('comparison').innerText:''));$('status').textContent='Analysis copied.';}catch{error('Clipboard access was blocked. Select the assessment text and copy it manually.');}};
fetch('/api/status').then(r=>r.json()).then(s=>{$('availability').textContent=(s.model_ready?'Conversation model ready.':'Conversation model offline. Start run.ps1 server for full assessments.')+' '+(s.baseline_ready?'Quick scorer ready.':'Quick scorer needs setup: download_assets.py, then train.py.');}).catch(()=>{$('availability').textContent='Local service unavailable. Start the web app to continue.';});
updateCount();
