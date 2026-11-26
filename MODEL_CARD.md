# Browser scorer

This is the trained word/character TF-IDF + Ridge baseline from the original
local experiment, exported to JSON and evaluated with JavaScript. It predicts
IBM's `WA` argument-quality label, not the application's four-criterion rubric.
It is a lexical regression model, not a generative language model.

The page downloads weights from this repository. Text is processed in memory
on the visitor's device, is not added to requests, and is not stored by the app.
The app uses no analytics. GitHub handles ordinary static-site hosting requests.

## Training and limits

- Official splits: 20,974 training, 3,208 development and 6,315 test arguments.
- Development-selected Ridge alpha: 10. Input: argument text only.
- Test MAE: 15.05/100, compared with 15.75 for a constant baseline.
- Test Pearson: 0.379. These are modest baseline results.
- The training setting is short English arguments. Long text, other languages,
  sarcasm, and informal conversation context may be out of distribution.
- A high score does not establish truth, sound logic, or a person's credibility.
  The model can respond to superficial wording. No calibrated bands or individual
  confidence interval are available. Do not treat tiny differences as meaningful.
- The website does not produce four rubric scores, generated explanations,
  participant rankings or challenge revisions. Those features remain experimental
  in the separate local Qwen app.

Export with `python export_browser_model.py` after training. The JSON contains
fitted vocabularies, IDF values, coefficients and an intercept, not training rows.
The JavaScript implementation mirrors lowercase word/bigram and character-boundary
3–5 gram extraction, sublinear term frequency and separate L2 normalization.
Small differences from float32 Python arithmetic are expected.

## Sources and attribution

[IBM Argument Quality Ranking 30k](https://huggingface.co/datasets/ibm-research/argument_quality_ranking_30k),
Gretz et al. (2019), [A Large-scale Dataset for Argument Quality Ranking:
Construction and Analysis](https://arxiv.org/abs/1911.11408).
The upstream card's metadata says CC-BY-3.0 while its license text says
CC-BY-SA-3.0 and credits IBM/Wikipedia. The original card is preserved in
`data/DATASET_CARD.md`; no license discrepancy has been silently resolved.

Drafted with Codex (OpenAI), based on the author's direction.
