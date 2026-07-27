# Project Memory Update Policy

Use this policy to make end-of-task update decisions and resolve evidence, privacy, or concurrency edge cases.

## Contents

1. End-of-task transaction
2. Evidence standard
3. Update decision matrix
4. Partial and failed work
5. Git privacy
6. Conflicts and concurrent edits
7. Sensitive information
8. Archive policy
9. Final receipt

## End-of-task transaction

Perform the memory workflow after implementation and verification but before the final response:

1. Inspect the actual persistent changes.
2. Exclude \`.project-memory/\` from the coding-task diff.
3. Collect validation evidence.
4. Decide whether a new verified fact exists.
5. Update only the documents affected by that fact.
6. Refresh the index if any memory document changed.
7. Validate structure, privacy, placeholders, and likely secrets.
8. Report the exact result.

Treat the document update as one transaction. If validation fails, repair it before claiming success. If safe repair is impossible, report \`unable to update\`.

## Evidence standard

Rank evidence from strongest to weakest:

1. Successful runtime observation or focused automated test.
2. Successful build, typecheck, migration, or static verification.
3. Current source code and configuration.
4. Git diff, status, commit, or blame.
5. Existing project documentation.
6. User statement.
7. Agent inference.

Use levels 1–4 to support implementation claims. Use existing documentation to locate evidence, not as sole proof that behavior exists. Do not persist levels 6–7 unless they are independently verified.

When validation cannot run, record only what the source or configuration directly proves. Do not promote inferred runtime behavior to verified behavior.

## Update decision matrix

Update \`OVERVIEW.md\` when stable implemented behavior, architecture, environment, interface, or constraint changed.

Update \`STATUS.md\` when the current verified implementation state, validation result, reproducible limitation, or persistent unverified work changed.

Append \`DECISIONS.md\` when a lasting choice is now implemented. Do not add a decision merely because it was discussed.

Append \`CHANGELOG.md\` when a coding task leaves a material persistent change. Use one entry for the whole task.

Update \`INDEX.md\` whenever any other memory document changes.

Do not update for:

- Analysis, explanation, or review without a new verified project fact.
- Read-only diagnostics that confirm exactly what memory already says.
- Formatting-only or temporary edits with no material effect.
- Experiments that were fully reverted.
- A user request that explicitly disables memory writes for the task.

## Partial and failed work

When persistent changes remain and verification fails:

- Record the actual retained changes.
- Record the failed command or observation without dumping long output.
- Use state \`not-verified\`.
- Do not add the intended capability to \`OVERVIEW.md\`.
- Add the current condition to \`STATUS.md\` only when it affects handoff.

When all experimental changes are reverted:

- Do not append a changelog entry.
- Update status only if the work produced a new reproducible fact about the unchanged project.

When validation was not attempted:

- State that it was not run and why.
- Do not use \`verified\`.

## Git privacy

Default Git storage to \`local-private\`.

Before first initialization:

1. Check whether \`.project-memory/\` is already tracked.
2. Prefer an existing ignore rule.
3. Otherwise add \`/.project-memory/\` to the repository-local Git exclude file.
4. Fall back to the project \`.gitignore\` only when the local exclude file cannot be written.
5. Verify ignore behavior before creating memory files.

Before every update:

- Check \`git ls-files\` for tracked memory files.
- Check the staged diff for memory files.
- Check ignore behavior.
- Stop and warn when local-private memory is tracked, staged, or not ignored.

Never automatically run \`git rm --cached\`, reset the index, rewrite history, or delete a remote copy.

Require explicit user consent before switching to \`tracked\`. Consent to work on the repository is not consent to publish memory. A repository that appears private still requires explicit consent.

## Conflicts and concurrent edits

Before writing:

- Re-read the target memory documents after completing the coding task.
- Preserve unrelated recent entries and user-authored facts.
- Avoid replacing the whole document when a narrow edit is sufficient.

When the document changed since it was first read:

- Merge non-conflicting facts.
- Do not overwrite ambiguous conflicting content.
- Report the conflict and leave the unresolved section unchanged.

Use ISO timestamps and Git revisions to make stale state visible. Do not introduce locks that could remain after an interrupted AI session.

## Sensitive information

Never write:

- Passwords, API keys, access tokens, cookies, private keys, or complete connection strings.
- Secret-bearing environment variable values.
- Personal data or raw user records.
- Full private logs, crash dumps, or database contents.
- Sensitive internal URLs when a neutral service label is sufficient.
- Absolute paths containing user or organization identifiers.

Use environment variable names, redacted labels, repository-relative paths, and short error summaries instead.

If sensitive content is found in existing memory:

- Do not repeat it in the response.
- Stop normal updating.
- Identify only the affected file and line.
- Ask the user to rotate exposed credentials when the content appears to be a real secret.

## Archive policy

Count task entries in \`CHANGELOG.md\`. When the count exceeds \`max_active_log_entries\`:

1. Keep the newest configured number of entries active.
2. Move older entries to \`archive/YYYY.md\`.
3. Preserve text, verification state, and chronological order.
4. Validate the active log and archive.

Do not summarize archived entries into new claims unless the summary is verified against the current project.

## Final receipt

Report one of four outcomes:

- \`initialized\`: memory was created, populated, privacy-checked, and validated.
- \`updated\`: existing memory was changed and validated.
- \`not updated\`: no update threshold was met.
- \`unable to update\`: an update was warranted but privacy, permissions, conflicts, or validation prevented a safe write.

List only the documents actually changed. State the evidence category without exposing sensitive output. Match the user's language and keep the receipt concise.
