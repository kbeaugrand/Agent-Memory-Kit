"""Validate generated Kiro and GitHub Copilot project knowledge artifacts."""

from __future__ import annotations

import json

from aimem.templates.loader import load_template

NATIVE_GUIDANCE_TEMPLATES = (
    "copilot/aimem_memory.instructions.md",
    "copilot/instructions_block.md",
    "copilot/project_knowledge.instructions.md",
    "copilot/project_knowledge_block.md",
    "kiro/steering_aimem_memory.md",
    "kiro/steering_project_knowledge.md",
    "skills/generate_project_instructions.md",
    "skills/lesson_learning.md",
)

UNSUPPORTED_MEMORY_ACTIONS = (
    "{{PROJECT_MEMORY}}",
    "{{USER_MEMORY}}",
    "{{SESSION_MEMORY}}",
    "{{AGENTS_MEMORY_DIR}}",
    ".aimem/memory",
    ".aimem/index",
    "record_memory.py",
    "manage_memory.py",
)


def test_native_guidance_has_platform_frontmatter(make_project) -> None:
    root = make_project("--both")
    kiro = (root / ".kiro/steering/aimem-memory.md").read_text(encoding="utf-8")
    copilot = (root / ".github/instructions/aimem-memory.instructions.md").read_text(
        encoding="utf-8"
    )

    assert kiro.startswith("---\ninclusion: always\n---")
    assert copilot.startswith('---\napplyTo: "**"\n---')


def test_source_guidance_references_only_native_knowledge_actions() -> None:
    for template in NATIVE_GUIDANCE_TEMPLATES:
        guidance = load_template(template)
        assert not any(action in guidance for action in UNSUPPORTED_MEMORY_ACTIONS), template


def test_guidance_uses_native_storage_only(make_project) -> None:
    root = make_project("--both")
    guidance = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            root / ".kiro/steering/aimem-memory.md",
            root / ".github/copilot-instructions.md",
            root / ".github/instructions/aimem-memory.instructions.md",
        )
    )

    assert ".kiro/steering" in guidance or "Kiro steering" in guidance
    assert ".github/instructions" in guidance
    assert ".aimem/memory" not in guidance
    assert ".aimem/index" not in guidance
    assert "{{" not in guidance


def test_guidance_uses_lesson_learning_to_maintain_knowledge(make_project) -> None:
    root = make_project("--both")
    guidance_paths = (
        root / ".github/copilot-instructions.md",
        root / ".github/instructions/aimem-memory.instructions.md",
        root / ".kiro/steering/aimem-memory.md",
    )

    for path in guidance_paths:
        text = path.read_text(encoding="utf-8")
        assert "lesson-learning" in text
        assert "completed work" in text or "completing work" in text
        assert "If no durable lesson emerged" in text


def test_skills_use_native_project_knowledge_only(make_project) -> None:
    root = make_project("--both")
    skill_paths = (
        root / ".github/skills/lesson-learning/SKILL.md",
        root / ".github/skills/generate-project-instructions/SKILL.md",
        root / ".kiro/skills/lesson-learning/SKILL.md",
        root / ".kiro/skills/generate-project-instructions/SKILL.md",
    )

    for path in skill_paths:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\nname:")
        assert "user-invocable: true" in text
        assert ".aimem/" not in text
        assert "{{" not in text


def test_lesson_learning_scopes_knowledge_to_effective_targets(make_project) -> None:
    root = make_project("--both")
    skill_paths = (
        root / ".github/skills/lesson-learning/SKILL.md",
        root / ".kiro/skills/lesson-learning/SKILL.md",
    )

    for path in skill_paths:
        text = path.read_text(encoding="utf-8")
        assert "exact applicability" in text
        assert "narrowest accurate" in text
        assert 'Reserve `applyTo: "**"`' in text
        assert "inclusion: fileMatch" in text
        assert "fileMatchPattern" in text
        assert "Split a file" in text
        assert "context bounded" in text


def test_end_hooks_steer_agents_toward_lesson_learning(make_project) -> None:
    root = make_project("--both")
    kiro = json.loads(
        (root / ".kiro/hooks/lesson-learning.kiro.hook").read_text(encoding="utf-8")
    )
    copilot = json.loads((root / ".github/hooks/lesson-learning.json").read_text(encoding="utf-8"))

    assert kiro["enabled"] is True
    assert kiro["version"] == "1"
    assert kiro["when"]["type"] == "agentStop"
    assert kiro["then"]["type"] == "askAgent"
    assert "lesson-learning" in kiro["then"]["prompt"]

    copilot_hook = copilot["hooks"]["Stop"][0]
    assert copilot_hook["type"] == "command"
    assert "printf" in copilot_hook["command"]
    assert "Write-Output" in copilot_hook["windows"]
    assert "lesson-learning" in copilot_hook["command"]
    assert "lesson-learning" in copilot_hook["windows"]
    assert not (root / ".github/hooks/lesson-learning.py").exists()


def test_project_instruction_generation_uses_lesson_learning_scope_rules(make_project) -> None:
    root = make_project("--both")
    skill_paths = (
        root / ".github/skills/generate-project-instructions/SKILL.md",
        root / ".kiro/skills/generate-project-instructions/SKILL.md",
    )

    for path in skill_paths:
        text = path.read_text(encoding="utf-8")
        assert "lesson-learning scope rules" in text
        assert "exact applicability" in text
        assert "Split rules into separate files" in text
        assert "every rule applies to every listed target" in text
        assert 'Reserve\n     `applyTo: "**"`' in text
        assert "inclusion: fileMatch" in text
        assert "fileMatchPattern" in text
        assert "inclusion: always" in text


def test_project_instruction_generation_requires_custom_kiro_steering(make_project) -> None:
    root = make_project("--both")
    skill_paths = (
        root / ".github/skills/generate-project-instructions/SKILL.md",
        root / ".kiro/skills/generate-project-instructions/SKILL.md",
    )

    for path in skill_paths:
        text = path.read_text(encoding="utf-8")
        assert "For every distinct non-global applicability, create a custom steering" in text
        assert 'fileMatchPattern: "<narrowest workspace-relative glob>"' in text
        assert "Do not finish with only `product.md`, `tech.md`, and `structure.md`" in text


def test_project_instruction_generation_honors_enabled_platforms(make_project) -> None:
    root = make_project("--copilot")
    skill = (root / ".github/skills/generate-project-instructions/SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "Generate guidance only for enabled platforms" in skill
    assert "Never create configuration" in skill
    assert "platform that is not already enabled" in skill
    assert not (root / ".kiro").exists()


def test_seed_steering_files_have_expected_sections(make_project) -> None:
    root = make_project("--kiro")
    expected = {
        "product.md": "# Product Overview",
        "tech.md": "# Technology Stack",
        "structure.md": "# Project Structure",
    }
    for name, heading in expected.items():
        text = (root / ".kiro/steering" / name).read_text(encoding="utf-8")
        assert text.startswith("---\ninclusion: always\n---")
        assert heading in text
