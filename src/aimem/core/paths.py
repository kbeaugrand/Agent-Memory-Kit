"""Canonical, project-relative paths for every artifact aimem manages.

Paths are stored as POSIX-style, project-relative strings. They double as manifest keys
and as the literal paths embedded in generated hook commands, so keep them stable.
"""

from __future__ import annotations

# Root working directory for aimem state inside a project.
AIMEM_DIR = ".aimem"
CONFIG_FILE = ".aimem/config.json"
MANIFEST_FILE = ".aimem/manifest.json"
BACKUPS_DIR = ".aimem/backups"

# Canonical memory files.
PROJECT_MEMORY = ".aimem/memory/project.md"
SESSION_MEMORY_DIR = ".aimem/memory/session"
SESSION_MEMORY = ".aimem/memory/session/current.md"
USER_MEMORY = "~/.aimem/memory/user.md"

# Project-local, self-contained Python hook scripts.
HOOKS_DIR = ".aimem/hooks"
HOOK_COMMON = ".aimem/hooks/_common.py"
HOOK_INJECT = ".aimem/hooks/inject_memory.py"
HOOK_RECORD = ".aimem/hooks/record_memory.py"
HOOK_CONSOLIDATE = ".aimem/hooks/consolidate_memory.py"
HOOK_GUARD = ".aimem/hooks/guard_memory.py"

# Kiro artifacts.
KIRO_STEERING_MEMORY = ".kiro/steering/aimem-memory.md"
KIRO_STEERING_PRODUCT = ".kiro/steering/product.md"
KIRO_STEERING_TECH = ".kiro/steering/tech.md"
KIRO_STEERING_STRUCTURE = ".kiro/steering/structure.md"
KIRO_AGENT_CURATOR = ".kiro/agents/memory-curator.md"
KIRO_HOOK = ".kiro/hooks/aimem-memory.kiro.hook"

# GitHub Copilot artifacts.
COPILOT_INSTRUCTIONS = ".github/copilot-instructions.md"
COPILOT_MEMORY_INSTRUCTIONS = ".github/instructions/aimem-memory.instructions.md"
COPILOT_AGENT_CURATOR = ".github/agents/memory-curator.agent.md"
COPILOT_HOOK = ".github/hooks/aimem-memory.json"

# Cross-tool, shared files (managed via marker blocks).
AGENTS_FILE = "AGENTS.md"
GITIGNORE_FILE = ".gitignore"
