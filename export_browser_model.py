"""Export the trusted, locally trained sklearn baseline for static browser inference."""
import argparse
import json
from pathlib import Path
import joblib

def export(source, destination):
    pipeline = joblib.load(source)
    regression = pipeline.named_steps['regressor']
    offset = 0
    groups = []
    for name, vectorizer in pipeline.named_steps['features'].transformer_list:
        assert vectorizer.norm == 'l2' and vectorizer.sublinear_tf
        assert vectorizer.lowercase and vectorizer.strip_accents is None
        size = len(vectorizer.vocabulary_)
        vocabulary = {term: [float(vectorizer.idf_[index]), float(regression.coef_[offset+index])]
                      for term, index in vectorizer.vocabulary_.items()}
        groups.append({'name': name, 'analyzer': vectorizer.analyzer,
                       'ngram_range': list(vectorizer.ngram_range), 'vocabulary': vocabulary})
        offset += size
    assert offset == len(regression.coef_)
    model = {'format': 1, 'target': 'IBM WA', 'intercept': float(regression.intercept_),
             'groups': groups, 'source': 'https://huggingface.co/datasets/ibm-research/argument_quality_ranking_30k',
             'attribution': 'Trained using IBM Argument Quality Ranking 30k, Gretz et al. (2019). See MODEL_CARD.md.',
             'limitations': 'Lexical speech-suitability estimate; not factual verification or a four-criterion rubric.'}
    Path(destination).write_text(json.dumps(model, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default=str(Path(__file__).parent/'weights'/'ibm-quality.joblib'))
    parser.add_argument('--output', default=str(Path(__file__).parent/'browser-model.json'))
    args = parser.parse_args()
    export(args.source, args.output)
