"""Validate generated Kiro and GitHub Copilot project knowledge artifacts."""

from __future__ import annotations


def test_native_guidance_has_platform_frontmatter(make_project) -> None:
    root = make_project("--both")
    kiro = (root / ".kiro/steering/aimem-memory.md").read_text(encoding="utf-8")
    copilot = (root / ".github/instructions/aimem-memory.instructions.md").read_text(
        encoding="utf-8"
    )

    assert kiro.startswith("---\ninclusion: always\n---")
    assert copilot.startswith('---\napplyTo: "**"\n---')


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
    assert "memory_propose" not in guidance
    assert "mcp-server" not in guidance
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
        assert "memory_propose" not in text
        assert "mcp-server" not in text
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
