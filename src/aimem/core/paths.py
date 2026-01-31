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
INDEX_DIR = ".aimem/index"
PROJECT_INDEX = ".aimem/index/project.json"
VECTOR_INDEX = ".aimem/index/vector.json"
PROPOSALS_DIR = ".aimem/proposals"

# Canonical memory files.
MEMORY_TEMPLATE = ".aimem/memory/TEMPLATE.md"
PROJECT_MEMORY = ".aimem/memory/project.md"
SESSION_MEMORY_DIR = ".aimem/memory/session"
SESSION_MEMORY = ".aimem/memory/session/current.md"
USER_MEMORY = "~/.aimem/memory/user.md"

# Per-agent memory (coday-style agent-scoped memory), committed with the project.
AGENTS_MEMORY_DIR = ".aimem/memory/agents"
AGENTS_MEMORY_README = ".aimem/memory/agents/README.md"

# Project-local, self-contained Python hook scripts.
HOOKS_DIR = ".aimem/hooks"
HOOK_COMMON = ".aimem/hooks/_common.py"
HOOK_INJECT = ".aimem/hooks/inject_memory.py"
HOOK_RECORD = ".aimem/hooks/record_memory.py"
HOOK_CONSOLIDATE = ".aimem/hooks/consolidate_memory.py"
HOOK_GUARD = ".aimem/hooks/guard_memory.py"
HOOK_MANAGE = ".aimem/hooks/manage_memory.py"
HOOK_LEARN_SESSION = ".aimem/hooks/learn_session.py"

# Kiro artifacts.
KIRO_MCP_CONFIG = ".kiro/settings/mcp.json"
KIRO_STEERING_MEMORY = ".kiro/steering/aimem-memory.md"
KIRO_STEERING_PRODUCT = ".kiro/steering/product.md"
KIRO_STEERING_TECH = ".kiro/steering/tech.md"
KIRO_STEERING_STRUCTURE = ".kiro/steering/structure.md"
KIRO_AGENT_INITIALIZER = ".kiro/agents/memory-initializer.md"
KIRO_AGENT_CURATOR = ".kiro/agents/memory-curator.md"
KIRO_HOOK = ".kiro/hooks/aimem-memory.kiro.hook"
KIRO_SKILL_LESSON_LEARNING = ".kiro/skills/lesson-learning/SKILL.md"

# GitHub Copilot artifacts.
VSCODE_MCP_CONFIG = ".vscode/mcp.json"
COPILOT_INSTRUCTIONS = ".github/copilot-instructions.md"
COPILOT_MEMORY_INSTRUCTIONS = ".github/instructions/aimem-memory.instructions.md"
COPILOT_AGENT_INITIALIZER = ".github/agents/memory-initializer.agent.md"
COPILOT_AGENT_CURATOR = ".github/agents/memory-curator.agent.md"
COPILOT_HOOK = ".github/hooks/aimem-memory.json"
COPILOT_SKILL_LESSON_LEARNING = ".github/skills/lesson-learning/SKILL.md"

# Cross-tool, shared files (managed via marker blocks).
AGENTS_FILE = "AGENTS.md"
GITIGNORE_FILE = ".gitignore"
