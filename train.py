"""Train a reproducible CPU baseline on IBM's official quality-ranking splits."""
import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import Ridge
import sklearn

ROOT = Path(__file__).resolve().parent

def read(name):
    with (ROOT / 'data' / f'{name}.csv').open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def metrics(y, p):
    return {'mae': float(np.mean(np.abs(y-p))),
            'rmse': float(np.sqrt(np.mean((y-p)**2))),
            'pearson': float(pearsonr(y,p).statistic) if np.std(p)>1e-12 else None,
            'spearman': float(spearmanr(y,p).statistic) if np.std(p)>1e-12 else None}

def main():
    rows = {s: read(s) for s in ['train','dev','test']}
    # Do not use the alternative argument_topic configuration or mix the official splits.
    x = {s: [r['argument'] for r in rr] for s,rr in rows.items()}
    y = {s: np.array([float(r['WA']) for r in rr]) for s,rr in rows.items()}
    features = FeatureUnion([
        ('word', TfidfVectorizer(ngram_range=(1,2), min_df=3, max_features=40000, sublinear_tf=True, dtype=np.float32)),
        ('char', TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), min_df=5, max_features=40000, sublinear_tf=True, dtype=np.float32))])
    matrices = {'train': features.fit_transform(x['train'])}
    matrices['dev'] = features.transform(x['dev'])
    candidates=[]
    best=None
    for alpha in [1.,10.,100.]:
        model=Ridge(alpha=alpha, solver='lsqr', tol=1e-5)
        model.fit(matrices['train'], y['train'])
        result=metrics(y['dev'], np.clip(model.predict(matrices['dev']),0,1))
        candidates.append({'alpha':alpha, **result})
        print(json.dumps(candidates[-1]), flush=True)
        if best is None or result['rmse']<best[0]: best=(result['rmse'], model)
    pipeline=Pipeline([('features', features), ('regressor',best[1])])
    # Test is accessed for evaluation only, after hyperparameter selection is frozen.
    pred=np.clip(pipeline.predict(x['test']),0,1)
    mean=float(y['train'].mean())
    audit={}
    for a,b in [('train','dev'),('train','test'),('dev','test')]:
        audit[f'{a}_{b}']={'exact_argument_overlap':len(set(x[a]) & set(x[b])),
                          'topic_overlap':len({r['topic'] for r in rows[a]} & {r['topic'] for r in rows[b]})}
    report={'target':'WA', 'scale':'0 to 1; multiply by 100 only for display',
        'input':'argument text only', 'selection':'minimum development RMSE; no refit on dev',
        'counts':{s:len(rr) for s,rr in rows.items()}, 'split_audit':audit,
        'development_candidates':candidates, 'selected_alpha':best[1].alpha,
        'test':metrics(y['test'], pred),
        'test_train_mean_baseline':metrics(y['test'],np.full_like(y['test'],mean)),
        'test_by_topic':{t:metrics(y['test'][idx],pred[idx]) for t in sorted({r['topic'] for r in rows['test']})
             for idx in [[i for i,r in enumerate(rows['test']) if r['topic']==t]]},
        'versions':{'numpy':np.__version__,'sklearn':sklearn.__version__},
        'sha256':{s:hashlib.sha256((ROOT/'data'/f'{s}.csv').read_bytes()).hexdigest() for s in rows},
        'limitations':['Not four-criterion supervision.', 'No conversation or rationale supervision.',
                      'No validated individual confidence interval.', 'Lexical baseline; not a factual verifier.']}
    (ROOT/'weights').mkdir(exist_ok=True)
    joblib.dump(pipeline,ROOT/'weights'/'ibm-quality.joblib',compress=3)
    (ROOT/'evaluation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'test':report['test'],'baseline':report['test_train_mean_baseline']}),flush=True)

if __name__=='__main__': main()
