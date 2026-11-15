# Project log

**Snapshot date:** 2026-11-15  
**Project:** Argument Assessment

## What the project is

The project brief describes a simple English-language web app for helping general users assess arguments in pasted conversations, initially informal disagreements between friends or family. It is intended to explain argument strengths and weaknesses, not judge participants or declare a debate winner.

## Recorded project decisions

- Users will paste a free-form transcript. The app should identify speakers and turns, then let users correct that structure and argument groupings before assessment.
- Assess each argument within its own turn, using the rest of the conversation for context. Split distinct arguments in a turn; never combine arguments across turns.
- Mark turns without a clear, reasoned argument as not assessable, without assigning a numeric score.
- Score assessable arguments from 0 to 100 on logic, evidence, relevance, and counterargument handling, with equal weighting. Use a neutral counterargument-handling score of 50 when no relevant counterargument is present.
- Explain each assessment, cite transcript excerpts, suggest an improvement, and report uncertainty. Do not externally verify factual claims; mark claims not verifiable from the transcript as unverified/unsupported. Assess value arguments on their own terms.
- The application, not the model, should validate score arithmetic and calculate participant averages. Each assessable argument counts equally; participants with no assessable arguments get no numeric average, and a one-argument average is flagged as a limited sample.
- Summarize key disagreements and the strongest arguments without ranking participants.
- Support optional context and redaction, a visible transcript length limit, copyable results, and challenges that show original and revised assessments side by side.
- Transcripts should not be saved; results should be private to the submitting user, with no account required.
- Use synthetic conversations for initial testing and calibrate the five score bands before treating their boundaries as final.
- The technology stack and hosting provider remain undecided.

## Files present in the inspected project

The project root contains:

- `AGENT.md` — development guidance and a concise statement of product requirements.
- `project_brainstorming.md` — the current product brief, including scope, user experience, validation goals, and open decisions.
- `model/argument-assessment.prompt.md` — provider-neutral assessment instructions, including transcript-handling rules, scoring procedure, uncertainty, and expected input.
- `model/assessment-response.schema.json` — JSON Schema Draft 2020-12 response contract, version `1.0`. It requires turn assessments and a conversation summary; it does not include participant averages, which are derived by the application.

The available filesystem timestamps show these files were last modified on 2026-10-31, between 10:43:58 PM and 10:44:36 PM. Those timestamps establish file metadata only; they do not establish when the project began or the complete sequence of work.

## Current known status

- The product brief and initial provider-neutral model contract are present.
- The response schema describes per-turn/per-argument assessments and a conversation summary.
- No application source code, tests, or other project files were present in the inspected project root and `model` directory.
- No Git metadata/history was found in the inspected project root, so earlier changes, authorship, and a complete activity timeline cannot be confirmed from the available materials.
- No additional project activity was documented in the files inspected.

## Log entry — 2026-11-15

Created this project log after inspecting the project brief, development guidance, model prompt, and response schema. This entry records the state evidenced by those files and their filesystem timestamps; it does not infer unrecorded development activity.

## Open decisions and next work implied by the brief

- Choose the technology stack and hosting approach.
- Define and calibrate score-band boundaries and descriptors using synthetic conversations.
- Implement the transcript review/editing flow, assessment, response validation, participant averages, privacy and length-limit behavior, copyable results, and assessment challenges.
- Add tests for scoring, aggregation, uncertainty, and transcript handling against the stated requirements.
