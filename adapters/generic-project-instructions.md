# Generic Project Instructions

Copy the instruction block below into the project-level rules or custom instructions supported by the AI coding tool.

~~~text
Maintain platform-neutral project memory in `.project-memory/`.

If the maintain-project-memory package is available, read its `SKILL.md` and the referenced document schema and update policy. If it is not available, use the minimal document set `config.json`, `INDEX.md`, `OVERVIEW.md`, `STATUS.md`, `DECISIONS.md`, `CHANGELOG.md`, and `archive/`.

At the start of a coding task:
1. If `.project-memory/` exists, read `INDEX.md` and `STATUS.md`.
2. Read `OVERVIEW.md`, `DECISIONS.md`, and recent `CHANGELOG.md` entries only as needed.
3. Verify any saved claim that materially affects the task against current code, configuration, tests, runtime output, or Git state.

After completing and verifying every coding task:
1. Decide whether the task left a material persistent change or a newly verified project fact.
2. If memory does not exist and the task left persistent changes, initialize it automatically.
3. Update only the affected memory documents.
4. Record only implemented or directly observable facts. Do not record plans, desired features, speculation, or unverified user statements.
5. Do not record the AI tool, model, prompt, conversation ID, or hidden reasoning.
6. For Git projects, keep `.project-memory/` local-private and ignored unless the user explicitly opts in to version control. Never stage, commit, publish, untrack, or rewrite history for project memory automatically.
7. If persistent changes remain but validation fails, record the actual changes and failure as `not-verified`; do not claim the intended behavior is implemented.
8. State in the final response whether project memory was initialized, updated, not updated, or could not be updated.

When initializing without the package:
1. Determine the Git top-level directory or explicit local project directory.
2. In a Git project, verify that `/.project-memory/` is ignored before creating files. Prefer `.git/info/exclude` and fall back to `.gitignore`. Refuse initialization if privacy cannot be verified.
3. Use Markdown for documents and JSON for configuration.
4. Keep `INDEX.md` concise, store stable implemented facts in `OVERVIEW.md`, current verified state in `STATUS.md`, implemented decisions in `DECISIONS.md`, and one task-level entry per coding task in `CHANGELOG.md`.
5. Do not overwrite an existing memory file merely to initialize the remaining files.
~~~
