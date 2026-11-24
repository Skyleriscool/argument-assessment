# Argument Assessment

A local research prototype for assessing arguments, with a trained IBM-quality
baseline and an experimental Qwen adapter for the four-criterion model contract.
**It does not yet meet the full product brief and is not a completed web app.**

## What works, and what remains uncertain

- Word/character TF-IDF + Ridge regression predicts IBM's overall `WA` label.
  On 6,315 held-out arguments, MAE was **15.05/100**, versus **15.75** for a
  constant baseline; Pearson correlation was **0.379**.
- The local rubric assessor returns logic, evidence, relevance and counterargument
  scores. Application code validates quotations and identities, recalculates
  means, and produces participant averages without ranking participants.
- **15 application tests passed.** The larger local model passed two of three
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
and changes. A revised answer is not automatically more correct. This is a CLI
comparison, not the graphical side-by-side interface proposed in the brief.

## Attribution and next work

Dataset: [IBM Argument Quality Ranking 30k](https://huggingface.co/datasets/ibm-research/argument_quality_ranking_30k),
Gretz et al., [2019 paper](https://arxiv.org/abs/1911.11408).
The preserved [dataset card](data/DATASET_CARD.md) contains inconsistent
CC-BY-3.0 versus CC-BY-SA-3.0 license statements; clarify with the publisher before
broader redistribution. Downloading the public files does not resolve that issue.
The local model is [Qwen3-1.7B, quantized by Unsloth](https://huggingface.co/unsloth/Qwen3-1.7B-GGUF);
consult its upstream license when distributing weights.

Next work is human review and rubric labeling, calibration, stronger model
evaluation, and the web application's review and challenge workflows. The product
brief and provider-neutral model contract remain the source of requirements.

Drafted with Codex (OpenAI), based on the author's direction.
Saved local-model assessments were generated with the Qwen models identified in
the research notes; they are experimental outputs, not human ground truth.
