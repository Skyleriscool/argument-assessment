const assert=require('node:assert/strict');
const {test}=require('node:test');
const fs=require('node:fs');
const {predict}=require('./score-engine.js');
const model=JSON.parse(fs.readFileSync(__dirname+'/browser-model.json','utf8'));
test('empty input rejected',()=>assert.throws(()=>predict(model,'   '),/Type/));
test('over limit rejected',()=>assert.throws(()=>predict(model,'a'.repeat(4001)),/shorten/));
test('no known features detected',()=>assert.equal(predict(model,'😀😃🙂').matchedFeatures,0));
test('case is normalized',()=>assert.equal(predict(model,'WHY should we walk?').score,predict(model,'why should we walk?').score));
test('prediction is deterministic and bounded',()=>{
  const text='We should take the bus because parking costs more than the fare.';
  const a=predict(model,text);assert.deepEqual(a,predict(model,text));
  assert.ok(a.score>=0&&a.score<=100&&a.matchedFeatures>0);
});
