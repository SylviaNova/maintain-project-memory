---
name: maintain-project-memory
description: Maintain concise, verified project background, current state, implemented decisions, and task-level change history in a local .project-memory directory for Git and non-Git projects. Use when an AI starts or resumes work in a project, needs to initialize or load project context, audits whether saved context is stale, completes a coding task and must automatically decide whether to update project memory, or prepares a handoff to another conversation or AI tool. Record only facts supported by code, configuration, tests, runtime output, or Git evidence; never record AI tool or model identity; keep memory local-private and Git-ignored unless the user explicitly opts in to version control.
---

# Maintain Project Memory

Maintain a platform-neutral project memory that another AI or developer can verify and use without relying on prior conversation history.

## Enforce the contract

- Store project memory in \`.project-memory/\` at the project root.
- Treat code, configuration, tests, runtime output, and Git state as evidence. Do not treat an earlier summary as proof.
- Record implemented or directly observable facts only. Exclude plans, desired features, speculative architecture, and unverified user statements.
- Do not record the AI product, model, conversation ID, prompt, or hidden reasoning.
- Default every Git project to \`local-private\`. Do not stage, commit, or publish project memory without explicit user consent.
- Evaluate memory after every coding task. Update it only when the task leaves a material, persistent, verifiable change or a persistent change with a verified failed validation.
- State the memory outcome in the final response: initialized, updated, not updated, or unable to update.

Read [references/update-policy.md](references/update-policy.md) before resolving ambiguous evidence, partial failures, privacy conflicts, concurrent edits, or archive decisions. Read [references/document-schema.md](references/document-schema.md) before initializing, repairing, or restructuring the document set.

## Locate the project

1. Use the Git top-level directory when the working directory is inside a Git repository.
2. Otherwise, use the explicit workspace or project directory supplied by the user.
3. Do not walk into an unrelated parent directory or write outside the active workspace.
4. If the root is ambiguous, do not initialize or update memory. Report the ambiguity.

Use the bundled inspector when Python 3 is available:

~~~text
python3 <skill-dir>/scripts/project_memory.py inspect --project <project-path>
~~~

Fall back to equivalent read-only filesystem and Git checks when the script cannot run.

## Start or resume a coding task

1. Inspect the project and memory status.
2. If \`.project-memory/\` exists, read \`INDEX.md\` and \`STATUS.md\` first.
3. Read \`OVERVIEW.md\` for project-wide behavior or architecture.
4. Read \`DECISIONS.md\` for implemented constraints relevant to the task.
5. Read only the recent or relevant entries in \`CHANGELOG.md\`; do not load the entire archive by default.
6. Verify any memory claim that materially affects the requested task against the repository.
7. Tell the user about material conflicts when they affect execution. Quietly repair minor stale metadata during the end-of-task update.

Do not make memory initialization a prerequisite for analysis-only work. Initialize automatically after the first coding task that leaves persistent project changes.

## Initialize memory

Use the bundled initializer unless it cannot run:

~~~text
python3 <skill-dir>/scripts/project_memory.py init --project <project-path>
~~~

The initializer must:

- Detect Git versus local mode.
- Establish a local Git exclusion before creating memory in a Git project.
- Prefer \`.git/info/exclude\`; fall back to \`.gitignore\`.
- Refuse local-private initialization if exclusion cannot be verified.
- Never untrack an already tracked memory directory.
- Copy the canonical templates without overwriting existing files.

After the script succeeds:

1. Inspect the project source, configuration, tests, and existing documentation.
2. Replace template placeholders with concise, verified facts.
3. Leave a section explicitly empty when no verified fact exists; do not invent content to make the document look complete.
4. Record the just-completed coding task in \`CHANGELOG.md\` when it meets the update threshold.
5. Refresh \`STATUS.md\` and \`INDEX.md\`.
6. Run strict validation.
7. Report the initialization and privacy result in the final response.

Do not silently initialize with \`tracked\` storage. Use tracked mode only after explicit user consent:

~~~text
python3 <skill-dir>/scripts/project_memory.py init \
  --project <project-path> \
  --storage-mode tracked \
  --confirm-publish
~~~

## Complete a coding task

After implementation and verification, perform one memory evaluation for the whole user task:

1. Inspect persistent source, configuration, dependency, schema, test, and documentation changes.
2. Exclude \`.project-memory/\` from the task-change summary.
3. Classify each verified fact:
   - Stable project behavior or structure: \`OVERVIEW.md\`.
   - Current verified implementation and validation state: \`STATUS.md\`.
   - Implemented decision with lasting consequences: \`DECISIONS.md\`.
   - This task's persistent changes and validation outcome: \`CHANGELOG.md\`.
   - Compact entry point and verification timestamp: \`INDEX.md\`.
4. Apply the smallest coherent update. Do not rewrite every file automatically.
5. Preserve valid user-authored facts and unrelated entries.
6. Re-read the changed memory files for internal consistency.
7. Run:

~~~text
python3 <skill-dir>/scripts/project_memory.py validate \
  --project <project-path> \
  --strict
~~~

8. Include a memory receipt in the final response.

## Decide whether to update

Update memory when at least one condition is true:

- Persistent code, configuration, dependency, schema, test, or user-facing behavior changed materially.
- A verified implementation capability or limitation changed.
- A lasting technical decision became embodied in the project.
- A coding attempt left persistent changes and the failed or incomplete verification result is itself confirmed.
- Existing memory materially disagrees with the current project and the discrepancy is verified.

Do not update memory when all conditions are true:

- The task was explanation, review, or analysis only.
- No persistent project state changed.
- Any experimental edits were fully reverted.
- No new verified fact was discovered that changes the saved current state.

Never create a success claim from a failed or missing validation. When persistent changes remain after a failed validation, record the actual changes and failure as \`not verified\`, not as an implemented capability.

## Write evidence-backed content

- Attach compact evidence pointers to important claims: file paths, test names, commands with outcomes, runtime observations, or Git revisions.
- Prefer runtime or test evidence over source inference.
- Mark the verification date and, in Git mode, the relevant commit or \`uncommitted\`.
- Avoid absolute local paths, full diffs, long command output, and copied source blocks.
- Do not use future-tense planning fields such as “next steps,” “roadmap,” or “planned.”
- Record a known limitation only when it is reproducible or directly supported by current code or tests.
- Record a decision only after it is implemented or enforced in the project.

## Keep Git memory private

For \`local-private\` storage:

- Verify that \`.project-memory/\` is ignored before and after updates.
- Check that no memory file is tracked or staged.
- Do not run commands that untrack, unstage, rewrite history, or remove files automatically.
- If memory is tracked or staged unexpectedly, stop the memory update and warn the user.
- If privacy verification fails, do not create new memory files.

Treat any transition to \`tracked\` as an explicit publishing decision. Re-scan for secrets and private information even after consent.

## Keep the memory bounded

- Keep \`INDEX.md\` concise enough to serve as a new-session entry point.
- Keep one main changelog entry per user coding task.
- Retain the configured number of active entries in \`CHANGELOG.md\`.
- Move older entries to \`archive/YYYY.md\` without changing their meaning.
- Do not archive the current status or currently enforced decisions.

## Report the outcome

End the user-facing response with one concise receipt:

~~~text
Project memory: initialized
- Storage: local-private
- Privacy: Git ignore verified
- Updated: INDEX, OVERVIEW, STATUS, CHANGELOG
~~~

~~~text
Project memory: updated
- Updated: STATUS, CHANGELOG, INDEX
- Evidence: source changes and passing tests
~~~

~~~text
Project memory: not updated
- Reason: analysis only; no persistent or newly verified project state
~~~

~~~text
Project memory: unable to update
- Reason: memory is unexpectedly tracked or privacy could not be verified
~~~

Match the response language to the user. Do not claim an update unless the files were written and validated.
