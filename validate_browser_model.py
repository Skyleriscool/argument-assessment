"""Compare JavaScript predictions with the original trained Python model."""
import argparse
import csv
import json
import subprocess
from pathlib import Path
import joblib
import numpy as np

ROOT=Path(__file__).resolve().parent
SYNTHETIC=[
    'We should take the bus because parking costs more than the fare.',
    'A b c! Why? WHY? why?', 'Hello\tthere\nfriend.',
    'café naïve résumé İstanbul Straße αβγ １２３ ²³',
    '😀 😃 🙂 We should walk because it is free.',
    'one\u0085two\u001cthree\u3000four\ufefffive',
    'a'*4000, 'because '*100, '!!!', '1234567890',
]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',default=str(ROOT/'weights'/'ibm-quality.joblib'))
    parser.add_argument('--test-data',default=str(ROOT/'data'/'test.csv'))
    args=parser.parse_args()
    with open(args.test_data,encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    texts=SYNTHETIC+[rows[i]['argument'] for i in np.linspace(0,len(rows)-1,300,dtype=int)]
    model=joblib.load(args.source)
    expected=np.clip(model.predict(texts),0,1)*100
    code="const fs=require('fs'); const {predict}=require('./score-engine.js'); const model=JSON.parse(fs.readFileSync('browser-model.json','utf8')); const texts=JSON.parse(fs.readFileSync(0,'utf8')); process.stdout.write(JSON.stringify(texts.map(t=>predict(model,t).score)));"
    result=subprocess.run(['node','-e',code],cwd=ROOT,input=json.dumps(texts),text=True,capture_output=True,check=True)
    actual=np.array(json.loads(result.stdout))
    delta=np.abs(actual-expected)
    report={'cases':len(texts),'held_out_examples':300,'synthetic_edge_cases':len(SYNTHETIC),
        'max_absolute_difference_on_100_point_scale':float(delta.max()),
        'tolerance':0.001,'passed':bool(np.isfinite(actual).all() and np.all(delta<0.001)),
        'scope':'Implementation parity only; not new model-quality evidence.'}
    (ROOT/'browser-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
    if not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
