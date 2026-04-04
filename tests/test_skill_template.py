"""
Tests for SKILL.md Jinja2 template rendering.

Verifies that the template renders correctly with minimal, full, and
partial data, and that the YAML frontmatter is well-formed.

Run with: pytest tests/test_skill_template.py -v
"""

from pathlib import Path

import pytest

try:
    from jinja2 import Environment, FileSystemLoader
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
TEMPLATE_PATH = TEMPLATE_DIR / "SKILL.md.template"


def _render(**context) -> str:
    """Render the SKILL.md template with given context variables."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("SKILL.md.template")
    return template.render(**context)


def _minimal_context() -> dict:
    """Return the minimal set of variables needed by the template."""
    return dict(
        skill_name="cli-anything-testapp",
        skill_description="CLI for TestApp - a test application.",
        software_name="testapp",
        skill_intro="A test application for demonstration.",
        version="1.0.0",
        system_package=None,
        command_groups=[],
        examples=[],
    )


def _full_context() -> dict:
    """Return a full context with all optional sections populated."""
    return dict(
        skill_name="cli-anything-gimp",
        skill_description="CLI for GIMP - GNU Image Manipulation Program.",
        software_name="gimp",
        skill_intro="GIMP is a cross-platform image editor.",
        version="2.10.36",
        system_package="apt install gimp",
        command_groups=[
            {
                "name": "Export",
                "description": "Export commands for various formats.",
                "commands": [
                    {"name": "pdf", "description": "Export as PDF"},
                    {"name": "png", "description": "Export as PNG"},
                    {"name": "svg", "description": "Export as SVG"},
                ],
            },
            {
                "name": "Edit",
                "description": "Image editing operations.",
                "commands": [
                    {"name": "crop", "description": "Crop image to selection"},
                    {"name": "resize", "description": "Resize image"},
                ],
            },
        ],
        examples=[
            {
                "title": "Quick Export",
                "description": "Export current image to PNG.",
                "code": "cli-anything-gimp --json export png -o output.png",
            },
            {
                "title": "Batch Resize",
                "description": "Resize multiple images at once.",
                "code": "cli-anything-gimp batch resize --size 800x600 *.xcf",
            },
        ],
    )


# ─── Template Availability Tests ──────────────────────────────────────


class TestTemplateExists:
    def test_template_file_exists(self) -> None:
        assert TEMPLATE_PATH.exists(), f"Template not found at {TEMPLATE_PATH}"

    @pytest.mark.skipif(not HAS_JINJA2, reason="Jinja2 not installed")
    def test_jinja2_available(self) -> None:
        assert HAS_JINJA2


# ─── Minimal Render Tests ─────────────────────────────────────────────


@pytest.mark.skipif(not HAS_JINJA2, reason="Jinja2 not installed")
class TestMinimalRender:
    def test_renders_without_error(self) -> None:
        content = _render(**_minimal_context())
        assert isinstance(content, str)
        assert len(content) > 0

    def test_has_yaml_frontmatter(self) -> None:
        content = _render(**_minimal_context())
        assert content.startswith("---")
        # Find closing ---
        parts = content.split("---")
        assert len(parts) >= 3  # opening ---, yaml body, rest

    def test_yaml_contains_name(self) -> None:
        content = _render(**_minimal_context())
        assert "cli-anything-testapp" in content

    def test_yaml_contains_description(self) -> None:
        content = _render(**_minimal_context())
        assert "CLI for TestApp" in content

    def test_has_installation_section(self) -> None:
        content = _render(**_minimal_context())
        assert "## Installation" in content

    def test_has_version(self) -> None:
        content = _render(**_minimal_context())
        assert "1.0.0" in content

    def test_has_usage_section(self) -> None:
        content = _render(**_minimal_context())
        assert "## Usage" in content

    def test_has_agent_guidance(self) -> None:
        content = _render(**_minimal_context())
        assert "## For AI Agents" in content

    def test_no_command_groups_section(self) -> None:
        content = _render(**_minimal_context())
        assert "## Command Groups" not in content


# ─── Full Render Tests ────────────────────────────────────────────────


@pytest.mark.skipif(not HAS_JINJA2, reason="Jinja2 not installed")
class TestFullRender:
    def test_has_command_groups(self) -> None:
        content = _render(**_full_context())
        assert "## Command Groups" in content
        assert "### Export" in content
        assert "### Edit" in content

    def test_has_all_commands(self) -> None:
        content = _render(**_full_context())
        assert "`pdf`" in content
        assert "`png`" in content
        assert "`svg`" in content
        assert "`crop`" in content
        assert "`resize`" in content

    def test_has_system_package(self) -> None:
        content = _render(**_full_context())
        assert "apt install gimp" in content

    def test_has_examples(self) -> None:
        content = _render(**_full_context())
        assert "### Quick Export" in content
        assert "### Batch Resize" in content
        assert "cli-anything-gimp --json export png" in content

    def test_has_repl_mode_section(self) -> None:
        content = _render(**_full_context())
        assert "REPL" in content or "repl" in content.lower()


# ─── Partial Context Tests ────────────────────────────────────────────


@pytest.mark.skipif(not HAS_JINJA2, reason="Jinja2 not installed")
class TestPartialContext:
    def test_no_system_package(self) -> None:
        ctx = _minimal_context()
        ctx["system_package"] = None
        content = _render(**ctx)
        assert "apt install" not in content
        assert "brew install" not in content

    def test_empty_command_groups(self) -> None:
        ctx = _full_context()
        ctx["command_groups"] = []
        content = _render(**ctx)
        assert "## Command Groups" not in content

    def test_empty_examples(self) -> None:
        ctx = _full_context()
        ctx["examples"] = []
        content = _render(**ctx)
        assert isinstance(content, str)
        assert len(content) > 0
        # Template outputs "## Examples" heading unconditionally (outside the
        # {% for %} loop), so it appears even with an empty list.
        assert "## Examples" in content
        # But no example subheadings should appear
        assert "### Quick Export" not in content
        assert "### Batch Resize" not in content

    def test_single_command_group(self) -> None:
        ctx = _minimal_context()
        ctx["command_groups"] = [
            {
                "name": "General",
                "description": "General commands.",
                "commands": [
                    {"name": "help", "description": "Show help"},
                ],
            }
        ]
        content = _render(**ctx)
        assert "### General" in content
        assert "`help`" in content

    def test_brew_install_system_package(self) -> None:
        ctx = _minimal_context()
        ctx["system_package"] = "brew install ffmpeg"
        content = _render(**ctx)
        assert "brew install ffmpeg" in content

    def test_single_example(self) -> None:
        ctx = _minimal_context()
        ctx["examples"] = [
            {
                "title": "Get Started",
                "description": "Basic usage example.",
                "code": "cli-anything-testapp --help",
            }
        ]
        content = _render(**ctx)
        assert "### Get Started" in content


# ─── YAML Frontmatter Validation ──────────────────────────────────────


@pytest.mark.skipif(not HAS_JINJA2, reason="Jinja2 not installed")
class TestYamlFrontmatter:
    def test_starts_with_delimiter(self) -> None:
        content = _render(**_full_context())
        assert content.startswith("---\n")

    def test_name_in_yaml(self) -> None:
        content = _render(**_full_context())
        yaml_block = content.split("---")[1]
        assert "cli-anything-gimp" in yaml_block

    def test_description_in_yaml(self) -> None:
        content = _render(**_full_context())
        yaml_block = content.split("---")[1]
        assert "GIMP" in yaml_block

    def test_yaml_block_not_empty(self) -> None:
        content = _render(**_minimal_context())
        yaml_block = content.split("---")[1].strip()
        assert len(yaml_block) > 0

    def test_name_field_present(self) -> None:
        content = _render(**_minimal_context())
        yaml_block = content.split("---")[1]
        assert "name:" in yaml_block

    def test_description_field_present(self) -> None:
        content = _render(**_minimal_context())
        yaml_block = content.split("---")[1]
        assert "description:" in yaml_block
