# Codex Instructions

## Product purpose

Build a web app that helps general users assess the strengths and weaknesses of arguments in pasted conversations, especially informal disagreements between friends or family. Score arguments from 0 to 100 and, when the conversation is finished, report each participant's average argument-quality score. This is an assessment aid, not a debate-winner detector.

## Product requirements

- Accept free-form pasted transcripts. Let users review and correct detected speakers, turns, and argument groupings before analysis.
- Score complete arguments within a single speaker turn. Do not combine arguments across turns; split distinct arguments within one turn. Use the surrounding conversation for context while assessing only the argument in that turn.
- Assess logic, evidence quality, relevance, and handling of counterarguments. Give the criteria equal weight; show criterion subscores and calculate the overall argument score as their arithmetic mean.
- Explain scores briefly, cite relevant transcript excerpts, and offer a brief way to strengthen each argument. Use five documented score bands from very weak to very strong; calibrate their boundaries with test conversations rather than implying unsupported precision.
- Mark turns with no clear assessable argument as “not assessable,” with an explanation. Do not give them a numeric score.
- Keep participant scores about argument quality only. Calculate each participant's score as the simple average of their assessable argument scores, with each argument weighted equally. If a participant has no assessable arguments, show “not enough assessable arguments.” If they have only one, show the average and flag the limited sample. Do not declare a winner.
- Summarize key disagreements and each side's strongest argument. Support any number of participants.
- Do not browse or otherwise externally verify factual claims. Flag claims that cannot be verified from the transcript as unverified/unsupported, not automatically false. Distinguish factual claims from value judgments; assess value arguments for clarity, internal consistency, and support for their stated values rather than treating value disagreement as factual error.
- Show uncertainty and missing evidence explicitly. Flag unclear sarcasm or ambiguous wording instead of confidently guessing the intended meaning.
- Let users optionally provide context and redact identifying details. Process transcripts without saving them; results are private to the submitting user. Provide a copyable analysis.
- Allow users to challenge an assessment. Show the original and revised assessments side by side and explain changes.
- Keep a visible transcript length limit and ask users to shorten over-limit transcripts; do not silently imply complete analysis of a partial transcript.

## Development guidance

- Treat [project_brainstorming.md](./project_brainstorming.md) as the current product brief.
- Use [model/argument-assessment.prompt.md](./model/argument-assessment.prompt.md) and [model/assessment-response.schema.json](./model/assessment-response.schema.json) as the initial provider-neutral model contract.
- Do not assume a technology stack, hosting provider, or unrecorded scoring behavior. Ask before making consequential product decisions not covered by the brief.
- Keep changes focused, follow established repository conventions, and update relevant tests and documentation.
- Validate scoring, aggregation, uncertainty, and transcript handling against the exact product requirements above.
- Use synthetic conversations for initial assessment testing. Prioritize fair, well-explained results and consistency under a fixed rubric.
