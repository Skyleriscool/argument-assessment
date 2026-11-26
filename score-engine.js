/* Browser port of the fitted word/char_wb TF-IDF + Ridge pipeline. */
(function(root) {
  'use strict';
  const whitespace = /[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/u;
  function frequencies(text, group) {
    const result = new Map();
    const add = token => { if(Object.hasOwn(group.vocabulary, token)) result.set(token,(result.get(token)||0)+1); };
    const [min,max] = group.ngram_range;
    if(group.analyzer === 'word') {
      const words = text.match(/[\p{L}\p{N}_]{2,}/gu) || [];
      for(let n=min;n<=max;n++) for(let i=0;i+n<=words.length;i++) add(words.slice(i,i+n).join(' '));
    } else if(group.analyzer === 'char_wb') {
      for(const word of text.split(whitespace).filter(Boolean)) {
        const chars = Array.from(' '+word+' ');
        for(let n=min;n<=max;n++) {
          add(chars.slice(0,n).join(''));
          let offset=0;
          while(offset+n<chars.length) {offset++;add(chars.slice(offset,offset+n).join(''));}
          if(offset===0)break;
        }
      }
    } else throw new Error('Unsupported model analyzer.');
    return result;
  }
  function predict(model, text) {
    if(model.format!==1 || !Array.isArray(model.groups))throw new Error('Unsupported model format.');
    if(typeof text!=='string' || !text.trim())throw new Error('Type an argument first.');
    if(Array.from(text).length>4000)throw new Error('Please shorten your argument to 4,000 characters.');
    let value=model.intercept, matchedFeatures=0;
    for(const group of model.groups) {
      let squaredNorm=0, dot=0;
      const counts=frequencies(text.toLowerCase(),group);
      matchedFeatures+=counts.size;
      for(const [term,count] of counts) {
        const [idf,coefficient]=group.vocabulary[term];
        const weight=(1+Math.log(count))*idf;
        squaredNorm+=weight*weight;dot+=weight*coefficient;
      }
      if(squaredNorm)value+=dot/Math.sqrt(squaredNorm);
    }
    return {score:100*Math.max(0,Math.min(1,value)),matchedFeatures};
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={predict};
  else root.ArgumentScorer={predict};
})(typeof globalThis!=='undefined'?globalThis:this);
