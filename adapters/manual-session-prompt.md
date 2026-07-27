# Manual Session Prompt

Use this prompt at the beginning of a new conversation when the AI tool has no persistent project instructions:

~~~text
Before working on this project, check for `.project-memory/`.

If it exists, read `INDEX.md` and `STATUS.md` first, then load only the overview, implemented decisions, or recent change entries relevant to my request. Verify important saved claims against the current project.

If my coding task leaves persistent changes, automatically initialize or update project memory after implementation and verification. Save only implemented or directly observable facts with concise evidence. Do not save plans, speculation, AI tool/model information, prompts, or hidden reasoning.

Keep project memory local-private in Git projects unless I explicitly authorize version control. End your response by stating whether project memory was initialized, updated, not updated, or could not be updated.
~~~
