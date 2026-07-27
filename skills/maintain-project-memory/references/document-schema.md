# Project Memory Document Schema

Use this schema when initializing, repairing, translating, or validating \`.project-memory/\`.

## Contents

1. Directory contract
2. Shared writing rules
3. Configuration
4. Index
5. Overview
6. Status
7. Decisions
8. Changelog
9. Archive

## Directory contract

Maintain this project-local structure:

~~~text
.project-memory/
├── config.json
├── INDEX.md
├── OVERVIEW.md
├── STATUS.md
├── DECISIONS.md
├── CHANGELOG.md
└── archive/
~~~

Keep the filenames stable across languages so any AI can locate them. Translate headings and prose when useful, but preserve the machine-readable marker at the top of each Markdown file:

~~~html
<!-- project-memory:document=index schema=1 -->
~~~

Valid document values are \`index\`, \`overview\`, \`status\`, \`decisions\`, and \`changelog\`.

## Shared writing rules

- Record facts only when evidence is available.
- Use concise prose and repository-relative paths.
- Distinguish passing verification from source-only inference.
- Write dates as \`YYYY-MM-DD\` and timestamps as ISO 8601.
- Use \`uncommitted\` when a fact belongs to a dirty Git worktree rather than a commit.
- Do not include plans, backlogs, desired features, or speculative next steps.
- Do not include AI tool names, model names, prompts, conversation identifiers, or hidden reasoning.
- Do not store credentials, personal data, raw private logs, or sensitive internal endpoints.
- Preserve prior facts that remain valid. Correct stale facts explicitly instead of layering contradictory summaries.

## Configuration

Store machine-readable policy in \`config.json\`:

~~~json
{
  "schema_version": 1,
  "language": "auto",
  "update_mode": "auto",
  "storage_mode": "local-private",
  "publish_policy": "explicit-opt-in",
  "max_active_log_entries": 30
}
~~~

Supported values:

- \`language\`: \`auto\` or a language tag such as \`zh-CN\` or \`en\`.
- \`update_mode\`: \`auto\` or \`manual\`.
- \`storage_mode\`: \`local-private\` or \`tracked\`.
- \`publish_policy\`: keep \`explicit-opt-in\` unless the user deliberately changes the policy.
- \`max_active_log_entries\`: a positive integer.

## Index

Use \`INDEX.md\` as the minimal new-session entry point. Keep it compact.

Required sections:

- Identity: project name, project kind, storage mode, last verification timestamp, and Git revision when applicable.
- Verified snapshot: a short summary of what the project currently does.
- Current condition: verified implementation and validation state only.
- Memory map: when to read each other document.
- Evidence basis: the sources used for the latest refresh.

Do not copy full architecture or changelog details into the index.

## Overview

Use \`OVERVIEW.md\` for stable, implemented project facts.

Recommended sections:

- Verified purpose: describe behavior demonstrated by the project, not aspirational product language.
- Implemented capabilities.
- Implemented architecture and data flow.
- Runtime, build, and test environment confirmed by configuration or successful commands.
- Important repository-relative paths.
- Active external interfaces and dependencies.
- Enforced constraints.
- Verification record.

Update this file only when stable facts change.

## Status

Use \`STATUS.md\` for the current verified state, not for planning.

Required sections:

- Verification context: date, commit or \`uncommitted\`, worktree state, and evidence used.
- Verified current state.
- Verification results.
- Verified limitations.
- Persistent unverified changes, only when such changes actually remain.

For an incomplete change, state exactly what exists and what failed. Do not describe the intended behavior as implemented.

## Decisions

Use \`DECISIONS.md\` only for decisions already embodied in code, configuration, schema, or enforced process.

Use this entry shape:

~~~markdown
## D-0001: Concise decision title

- Date: YYYY-MM-DD
- Status: implemented
- Context: verified condition that required the decision
- Decision: what the project now enforces
- Evidence: repository-relative files, tests, or commit
- Consequences: currently observable effects
- Supersedes: decision ID or none
~~~

Do not record brainstorms, alternatives under consideration, or decisions that have not been implemented. Mark a replaced decision as \`superseded\`; do not erase it.

## Changelog

Use one main entry per user coding task. Keep the configured newest entries active.

Use this entry shape:

~~~markdown
## YYYY-MM-DD: Task-level summary

- State: verified | not-verified
- Change: persistent changes that actually exist
- Files: concise repository-relative paths
- Verification: commands or observations and their outcomes
- Revision: commit, uncommitted, or local
- Memory impact: other memory files changed because of this task
~~~

Use \`verified\` only when the relevant validation passed or the observable result was confirmed. Use \`not-verified\` when persistent changes remain but validation failed or could not be completed. Do not create an entry for fully reverted experiments.

## Archive

Move older changelog entries to \`archive/YYYY.md\` when the active limit is exceeded.

- Preserve entry text and chronological order.
- Add \`<!-- project-memory:document=archive schema=1 -->\` at the top.
- Do not archive current status or implemented decisions.
- Read archives only when historical context is relevant.
