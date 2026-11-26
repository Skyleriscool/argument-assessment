'use strict';
const $=id=>document.getElementById(id);
let modelPromise=null, pending=false, resultText='';
function update() {
  const length=Array.from($('argument').value).length;
  $('counter').textContent=`${length.toLocaleString()} / 4,000`;
  $('counter').classList.toggle('over',length>4000);
  $('score').disabled=pending||!$('argument').value.trim()||length>4000;
}
function resetResult(){ $('result').hidden=true;$('error').hidden=true;$('status').textContent='';resultText='';update(); }
$('argument').addEventListener('input',resetResult);
$('example').onclick=()=>{$('argument').value='We should take the bus because parking costs more than the fare.';resetResult();$('argument').focus();};
$('clear').onclick=()=>{$('argument').value='';resetResult();$('argument').focus();};
async function loadModel(){
  if(!modelPromise)modelPromise=fetch('./browser-model.json').then(r=>{if(!r.ok)throw new Error('Model download failed. Check your connection and try again.');return r.json();}).catch(e=>{modelPromise=null;throw e;});
  return modelPromise;
}
$('score').onclick=async()=>{
  if(pending)return;
  const text=$('argument').value;
  if(!text.trim()||Array.from(text).length>4000)return;
  pending=true;resetResult();$('argument').disabled=true;$('clear').disabled=true;$('example').disabled=true;
  $('status').textContent=modelPromise?'Scoring in your browser…':'Loading the model into your browser. Your text stays on this device…';
  try{
    const model=await loadModel();const prediction=ArgumentScorer.predict(model,text);
    if(!prediction.matchedFeatures)throw new Error('The model does not recognize enough of this text to provide a useful estimate. Try a short English argument.');
    const displayed=prediction.score.toFixed(1);$('value').textContent=displayed;$('meter').value=prediction.score;
    const length=Array.from(text).length;
    $('warning').hidden=length>=35&&length<=245;
    $('warning').textContent='This input is outside the short-argument length range. Treat the estimate with extra caution.';
    $('result').hidden=false;$('status').textContent='Scored locally. No argument text was sent to a server.';
    resultText=`IBM argument-quality estimate: ${displayed}/100\n\n${text}\n\nExperimental speech-suitability estimate, not a factual check or four-criterion assessment. Average held-out error: about 15/100.`;
    $('result-title').focus();$('result').scrollIntoView({behavior:'smooth',block:'nearest'});
  }catch(e){$('error').textContent=e.message||'Could not score this argument. Please try again.';$('error').hidden=false;$('status').textContent='';}
  finally{pending=false;$('argument').disabled=false;$('clear').disabled=false;$('example').disabled=false;update();}
};
$('copy').onclick=async()=>{try{await navigator.clipboard.writeText(resultText);$('status').textContent='Result copied.';}catch{$('error').textContent='Clipboard access was blocked. You can select and copy the result manually.';$('error').hidden=false;}};
update();
