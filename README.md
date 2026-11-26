# Argument Assessment

## Website on GitHub Pages

**[Open the browser edition](https://skyleriscool.github.io/argument-assessment/)**

Type a short English argument and click **Score my argument**. The trained IBM
TF-IDF/Ridge model runs in JavaScript on your device. The site downloads about
2.6 MB of model weights on the first request; your text stays in the browser.
There is no installation, account, paid API, or transcript storage.

This public edition gives one overall IBM quality estimate. It does not run
Python or Qwen, generate explanations, or provide the four rubric subscores.
The full local app is retained below. See [MODEL_CARD.md](MODEL_CARD.md) for scope,
attribution and limitations, and [browser-validation.json](browser-validation.json)
for Python/JavaScript prediction parity results.

GitHub Pages serves `main` → `/ (root)`. The static entry point is `index.html`,
with relative asset paths and `.nojekyll`; future commits to the publishing branch
redeploy the site. To preview the static site, run `python -m http.server 8000`
from the repository root and visit `http://localhost:8000`.

To regenerate the browser weights after training, run `python export_browser_model.py`.
Run `node --test test_browser_score.cjs` for engine checks and
`python validate_browser_model.py` for parity against the original Python model
and downloaded test CSV. These checks do not establish better model accuracy.

A local research prototype for assessing arguments, with a trained IBM-quality
baseline and an experimental Qwen adapter for the four-criterion model contract.
**It includes a local web interface, but the model remains experimental and does
not yet meet the full product brief.**

## Type first, then analyze

After installing dependencies, run `python web_app.py` (or `.\run.ps1 ui`) and open
**http://127.0.0.1:8765**. Running `run.ps1` without arguments now starts the web
server. It prints the URL; it does not automatically score anything.

1. Type or paste a conversation, or choose a quick single-argument IBM score.
   Nothing is scored while you type; results start hidden.
2. For conversations, correct detected speakers and turns. Add/remove turns,
   optionally set exact argument groups, and confirm your review.
3. Click Analyze to see scores, reasoning, quotations, uncertainty and participant
   averages. Editing the input hides obsolete results.

The responsive page includes optional context, a 4,000-character limit, example,
clear and copy buttons, loading/error states, and side-by-side challenge results.
Full conversations require `.\run.ps1 server` in another terminal after model setup
below. Quick scores require training the IBM model first. Missing services produce
an actionable error while keeping your input; there are no invented fallback scores.

The UI uses a local Python standard-library HTTP server and plain HTML/CSS/JS.
It saves no transcripts, uses no browser storage, and accepts only same-origin
local API requests. It is not a public or multi-user hosting server.

All **24 Python tests pass**, including nine HTTP tests covering input/review
gating, offline errors, challenges and cross-origin rejection. Browser checks
verified blank state, review gating, offline recovery, a real IBM prediction after
clicking, stale-result clearing and narrow-screen layout. Model judgment quality
has not been revalidated by those interface checks.

## What works, and what remains uncertain

- Word/character TF-IDF + Ridge regression predicts IBM's overall `WA` label.
  On 6,315 held-out arguments, MAE was **15.05/100**, versus **15.75** for a
  constant baseline; Pearson correlation was **0.379**.
- The local rubric assessor returns logic, evidence, relevance and counterargument
  scores. Application code validates quotations and identities, recalculates
  means, and produces participant averages without ranking participants.
- **24 application tests passed.** The larger local model previously passed two of three
  coarse smoke cases but missed a reasoned argument in the embedded-instruction
  case. Correct JSON does not establish fair or reliable judgment.
- IBM labels do not supervise the four separate criteria, conversation structure
  or explanations. Qwen was not fine-tuned on IBM data. The IBM prediction stays
  separate from rubric scores. Score bands remain unset pending owner calibration.

See [evaluation.json](evaluation.json), [local-evaluation.json](local-evaluation.json),
[validation-summary.json](validation-summary.json), and the detailed
[research notes](RESEARCH_NOTES.txt). Review the eight
[synthetic cases](examples/review-cases.json) before defining score-band boundaries.

## Setup and reproduce the baseline

Use Python 3.12. The recorded dependency versions are in `requirements.txt`.
The repository contains source, synthetic examples and evaluation records; it
does not include the dataset CSVs, installed packages, runtime binaries or model
weights. The downloader verifies recorded SHA-256 hashes and refuses to overwrite
existing files. Training regenerates `weights/ibm-quality.joblib`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe download_assets.py
.\run.ps1 train
.\run.ps1 test
'We should walk because the park is nearby.' | .\run.ps1 quality
```

The portable Python equivalents are `python train.py`,
`python -m unittest discover -s . -p 'test_*.py' -v`, and
`python assess.py quality` (argument text on stdin). Activate your environment
first. Model training uses only the official training split; alpha selection
uses development RMSE. The test split is evaluated after selection.

## Run the experimental rubric assessor

Download the optional model (about 1.1 GB):

```powershell
.\.venv\Scripts\python.exe download_assets.py --model
```

Download the Windows CPU x64 ZIP from the
[llama.cpp b12657 release](https://github.com/ggml-org/llama.cpp/releases/tag/b12657)
and extract its files into `runtime/` so `runtime/llama-server.exe` exists.
Keep the runtime's licenses with it. On other platforms, use an equivalent
llama.cpp build with the server settings in `run.ps1`.

Start `.\run.ps1 server` in one terminal. In another:

```powershell
Get-Content -Raw examples\reviewed.json | .\run.ps1 assess
.\.venv\Scripts\python.exe evaluate_local.py
```

Inference may be slow and memory-constrained on a laptop. Ctrl+C stops the server.
The local server uses loopback only, disables logging, and runs offline. Do not
expose it as a multi-user or public service.

## Review and privacy

Redact identifying details before submitting. `prepare` accepts one `Speaker: text`
turn per line and returns draft JSON with `reviewed: false`. Review speaker IDs,
turns and argument groupings, then set `reviewed: true`. Optional `argument_groups`
must be exact excerpts within their turn; an empty list means not assessable.
Without reviewed groups, model-detected groupings require human review afterward.
An explicit empty `counterargument_turn_ids` list enforces neutral handling of 50.

The limit is 4,000 characters across transcript text and context. The model also
has an 8,192-token context limit including instructions and output. Invalid or
incomplete responses fail rather than silently returning partial assessments.
The application does not save real transcripts or results; manual files, terminal
history and OS paging are outside that guarantee. Saved examples are synthetic.

For `challenge`, submit JSON with `input` (reviewed input), `original` (previous
output), and `challenge` (your concern). The response includes both assessments
and changes. A revised answer is not automatically more correct. The CLI returns
JSON; the web interface displays original and revised assessments side by side.

## Attribution and next work

Dataset: [IBM Argument Quality Ranking 30k](https://huggingface.co/datasets/ibm-research/argument_quality_ranking_30k),
Gretz et al., [2019 paper](https://arxiv.org/abs/1911.11408).
The preserved [dataset card](data/DATASET_CARD.md) contains inconsistent
CC-BY-3.0 versus CC-BY-SA-3.0 license statements; clarify with the publisher before
broader redistribution. Downloading the public files does not resolve that issue.
The local model is [Qwen3-1.7B, quantized by Unsloth](https://huggingface.co/unsloth/Qwen3-1.7B-GGUF);
consult its upstream license when distributing weights.

Next work is human review and rubric labeling, calibration, stronger model
evaluation, and usability testing of the review and challenge workflows. The product
brief and provider-neutral model contract remain the source of requirements.

Drafted with Codex (OpenAI), based on the author's direction.
Saved local-model assessments were generated with the Qwen models identified in
the research notes; they are experimental outputs, not human ground truth.

