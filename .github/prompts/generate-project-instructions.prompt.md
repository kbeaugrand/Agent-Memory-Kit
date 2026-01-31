---
name: generate-project-instructions
description: Analyze repository coding practices and generate corresponding scoped instructions for GitHub Copilot and Kiro.
agent: agent
---

Invoke the `generate-project-instructions` skill for the current repository. Follow its evidence,
scope, platform-format, preservation, and validation requirements exactly.

Generate instructions only for practices supported by the repository. Create corresponding
GitHub Copilot and Kiro files, and report uncertain practices that were intentionally omitted.