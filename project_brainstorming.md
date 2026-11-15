# Argument Assessment — Product Brief

## Vision

A simple web app that helps general users compare the quality of arguments in a conversation. The first version should focus on informal disagreements between friends or family. It evaluates arguments, not people, and should help users understand why an argument is strong or weak without proclaiming a debate winner.

## Intended users and use

- **Audience:** General users comparing arguments.
- **Initial conversation type:** Informal disagreements between friends or family.
- **Input:** Users paste a free-form transcript. The app detects speakers and turns, then lets users review and correct the transcript structure before analysis.
- **Participants:** Support any number.
- **Context:** Offer an optional field for topic or other missing context.
- **Language:** English for the first version.
- **Platform:** A simple web app. Technology stack and hosting are undecided.

## What gets assessed

- Identify complete arguments within individual speaker turns. Do not combine turns into a single argument; if one turn contains multiple distinct arguments, split them and score each separately.
- Use surrounding turns to understand context and replies, but score only the argument made in the turn being assessed.
- Mark greetings, questions, unsupported assertions, and other turns without a clear assessable argument as **not assessable**, with an explanation rather than a numeric score.

## Scoring

Score each assessable argument from 0 to 100 using four equally weighted criteria:

1. Logical quality
2. Evidence quality and factual support
3. Relevance
4. Handling of counterarguments

Show an overall score, criterion subscores, a brief rationale, relevant excerpts from the transcript, and a brief suggestion for strengthening the argument. Calculate the overall score as the arithmetic mean of the four criterion subscores.

If the conversation contains no relevant counterargument for an argument to address, use a neutral score of 50 for counterargument handling.

Use five clear, documented bands from **very weak** to **very strong**. Calibrate the band boundaries against synthetic test conversations before treating them as final. Scores should not imply more certainty than the transcript supports.

### Factual and value claims

- Do not browse or externally verify claims in the first version.
- Flag factual claims that cannot be checked from the transcript as unverified/unsupported; do not assume they are false.
- Distinguish factual claims from value judgments. Assess value-based arguments for clarity, internal consistency, and support for their stated values; disagreement about values alone is not a factual error.

### Uncertainty

Show an uncertainty/confidence indicator and explain missing evidence. If sarcasm or ambiguous wording makes the intended meaning unclear, flag that uncertainty rather than confidently guessing.

## Participant and conversation results

- Each participant's score is the simple average of their assessable argument scores. Weight each argument equally.
- If a participant has no assessable arguments, show **not enough assessable arguments** instead of a numeric score.
- If only one argument is assessable, show its score as the participant average and flag the limited sample.
- Do not rank participants or declare a winner.
- Include key points of disagreement and each side's strongest argument in the conversation summary.

## User experience and privacy

- Let users correct detected speakers, turns, and argument groupings before analysis.
- Set a visible transcript length limit. Ask users to shorten an over-limit transcript instead of silently analyzing only part of it.
- Let users optionally redact names or other identifying details before analysis.
- Process transcripts without saving them. Results are private to the submitting user; the app does not require an account.
- Make the analysis copyable.
- Let users challenge an assessment. Show original and revised assessments side by side and explain any changes.

## Success and validation

The primary success criterion is that scores feel fair and are well explained. Initial validation should use synthetic conversation examples reviewed by the project owner. Use a fixed rubric and aim for consistent assessments of the same transcript.

The initial provider-neutral model contract is in [model/argument-assessment.prompt.md](./model/argument-assessment.prompt.md), with its response format in [model/assessment-response.schema.json](./model/assessment-response.schema.json). The model returns per-argument assessments; application code must validate score arithmetic and calculate participant averages rather than relying on model-generated math.

## Open decisions

- Technology stack and hosting.
- Final numeric boundaries and detailed descriptors for the five score bands, to be calibrated with test conversations.