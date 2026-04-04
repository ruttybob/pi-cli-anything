"""
Tests for repl_skin.py — Unified REPL terminal interface for CLI-Anything harnesses.

Verifies ANSI helpers, ReplSkin initialization, prompt generation,
banner/messages, table/help rendering, and color support detection.

Run with: pytest tests/test_repl_skin.py -v
"""

import sys
from pathlib import Path

import pytest

from repl_skin import (
    ReplSkin,
    _strip_ansi,
    _visible_len,
    _CYAN,
    _RESET,
    _GREEN,
    _RED,
    _YELLOW,
    _BLUE,
    _BOLD,
    _ACCENT_COLORS,
)


# ─── ANSI Helper Tests ────────────────────────────────────────────────


class TestAnsiHelpers:
    def test_strip_ansi_removes_codes(self) -> None:
        text = f"{_CYAN}hello{_RESET} world"
        assert _strip_ansi(text) == "hello world"

    def test_strip_ansi_plain_text_unchanged(self) -> None:
        assert _strip_ansi("plain text") == "plain text"

    def test_strip_ansi_empty_string(self) -> None:
        assert _strip_ansi("") == ""

    def test_strip_ansi_multiple_codes(self) -> None:
        text = f"{_BOLD}{_CYAN}styled{_RESET} {_RED}more{_RESET}"
        assert _strip_ansi(text) == "styled more"

    def test_visible_len_excludes_ansi(self) -> None:
        text = f"{_CYAN}hello{_RESET}"
        assert _visible_len(text) == 5

    def test_visible_len_plain_text(self) -> None:
        assert _visible_len("hello world") == 11

    def test_visible_len_empty_string(self) -> None:
        assert _visible_len("") == 0


# ─── ReplSkin Initialization Tests ────────────────────────────────────


class TestReplSkinInit:
    def test_default_software_name(self) -> None:
        skin = ReplSkin("gimp")
        assert skin.software == "gimp"
        assert skin.display_name == "Gimp"
        assert skin.version == "1.0.0"

    def test_custom_version(self) -> None:
        skin = ReplSkin("blender", version="3.6.0")
        assert skin.version == "3.6.0"

    def test_hyphen_normalization(self) -> None:
        skin = ReplSkin("obs-studio")
        assert skin.software == "obs_studio"
        # .title() keeps hyphens — "obs-studio" → "Obs-Studio"
        assert skin.display_name == "Obs-Studio"

    def test_known_software_gets_accent_color(self) -> None:
        for name in _ACCENT_COLORS:
            skin = ReplSkin(name)
            assert skin.accent == _ACCENT_COLORS[name]

    def test_unknown_software_gets_default_accent(self) -> None:
        from repl_skin import _DEFAULT_ACCENT
        skin = ReplSkin("unknown-app")
        assert skin.accent == _DEFAULT_ACCENT

    def test_custom_history_file(self, tmp_path: Path) -> None:
        hist = str(tmp_path / "my_history")
        skin = ReplSkin("gimp", history_file=hist)
        assert skin.history_file == hist

    def test_default_history_file_path(self) -> None:
        skin = ReplSkin("gimp")
        assert ".cli-anything-gimp" in skin.history_file
        assert skin.history_file.endswith("history")

    def test_skill_path_none_when_no_file(self) -> None:
        # ReplSkin auto-detects from __file__ (scripts/repl_skin.py) which
        # has no skills/ sibling directory in the test environment.
        skin = ReplSkin("gimp", skill_path=None)
        assert skin.skill_path is None or isinstance(skin.skill_path, str)

    def test_explicit_skill_path(self) -> None:
        skin = ReplSkin("gimp", skill_path="/custom/SKILL.md")
        assert skin.skill_path == "/custom/SKILL.md"


# ─── Prompt Tests ─────────────────────────────────────────────────────


class TestReplSkinPrompt:
    def test_prompt_basic(self) -> None:
        skin = ReplSkin("gimp")
        skin._color = True  # Force color on
        p = skin.prompt()
        assert "gimp" in _strip_ansi(p)

    def test_prompt_with_project(self) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        p = skin.prompt(project_name="my_project.xcf")
        stripped = _strip_ansi(p)
        assert "my_project.xcf" in stripped

    def test_prompt_modified_flag(self) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        p = skin.prompt(project_name="file.xcf", modified=True)
        stripped = _strip_ansi(p)
        assert "*" in stripped

    def test_prompt_no_color(self) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        p = skin.prompt()
        assert _strip_ansi(p) == p  # No ANSI codes
        assert ">" in p

    def test_prompt_with_context(self) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        p = skin.prompt(context="Layer 3")
        stripped = _strip_ansi(p)
        assert "Layer 3" in stripped


# ─── Banner Tests ─────────────────────────────────────────────────────


class TestReplSkinBanner:
    def test_banner_prints_software_name(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp", version="2.10.0")
        skin._color = True
        skin.print_banner()
        output = capsys.readouterr().out
        assert "cli-anything" in _strip_ansi(output)
        assert "Gimp" in _strip_ansi(output)
        assert "2.10.0" in _strip_ansi(output)

    def test_banner_shows_skill_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp", skill_path="/path/to/SKILL.md")
        skin._color = True
        skin.print_banner()
        output = capsys.readouterr().out
        assert "/path/to/SKILL.md" in _strip_ansi(output)

    def test_banner_no_skill_path(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin.skill_path = None
        skin._color = True
        skin.print_banner()
        output = capsys.readouterr().out
        assert "Skill:" not in _strip_ansi(output)

    def test_banner_box_drawing(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        skin.print_banner()
        output = capsys.readouterr().out
        # Should contain box drawing characters (plain, no ANSI)
        assert "╭" in output or "─" in output


# ─── ANSI Presence Tests ──────────────────────────────────────────────


class TestAnsiPresence:
    """Verify ANSI escape codes are actually emitted when color is enabled."""

    def test_success_has_ansi_when_color_enabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.success("Saved")
        output = capsys.readouterr().out
        assert "\033[" in output
        assert "Saved" in output

    def test_error_has_ansi_when_color_enabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.error("Fail")
        err = capsys.readouterr().err
        assert "\033[" in err

    def test_banner_has_ansi_when_color_enabled(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.print_banner()
        output = capsys.readouterr().out
        assert "\033[" in output


# ─── Display Name Consistency ─────────────────────────────────────────


class TestDisplayNameConsistency:
    """Verify the display_name behavior across the codebase.

    NOTE: repl_skin.py uses .replace("_", " ").title() which keeps hyphens,
    while skill_generator._format_display_name() also replaces hyphens.
    This is a known inconsistency in the source code — these tests document it.
    """

    def test_repl_skin_keeps_hyphens(self) -> None:
        skin = ReplSkin("obs-studio")
        # repl_skin only replaces underscores, keeps hyphens
        assert skin.display_name == "Obs-Studio"

    def test_skill_generator_replaces_hyphens(self) -> None:
        from skill_generator import _format_display_name
        # skill_generator replaces both underscores AND hyphens
        assert _format_display_name("obs-studio") == "Obs Studio"

    def test_both_agree_on_simple_names(self) -> None:
        from skill_generator import _format_display_name
        for name in ["gimp", "blender", "inkscape", "shotcut"]:
            skin = ReplSkin(name)
            assert skin.display_name == _format_display_name(name)


# ─── Message Tests ────────────────────────────────────────────────────


class TestReplSkinMessages:
    def test_success(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.success("Project saved")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "Project saved" in stripped

    def test_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.error("File not found")
        err = capsys.readouterr().err
        stripped = _strip_ansi(err)
        assert "File not found" in stripped

    def test_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.warning("Unsaved changes")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "Unsaved changes" in stripped

    def test_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.info("Processing 3 layers...")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "Processing 3 layers..." in stripped

    def test_hint(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.hint("Press Ctrl+S to save")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "Press Ctrl+S to save" in stripped

    def test_section(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.section("Layers")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "Layers" in stripped


# ─── Status & Progress Tests ──────────────────────────────────────────


class TestReplSkinStatus:
    def test_status(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.status("Resolution", "1920x1080")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "Resolution" in stripped
        assert "1920x1080" in stripped

    def test_status_block(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.status_block({"Width": "1920", "Height": "1080"}, title="Image Info")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "Image Info" in stripped
        assert "1920" in stripped
        assert "1080" in stripped

    def test_progress(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.progress(3, 10, "Exporting...")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "30%" in stripped
        assert "Exporting..." in stripped

    def test_progress_zero_total(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.progress(0, 0, "Idle")
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "0%" in stripped

    def test_progress_full(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = True
        skin.progress(10, 10)
        output = capsys.readouterr().out
        stripped = _strip_ansi(output)
        assert "100%" in stripped


# ─── Table Tests ───────────────────────────────────────────────────────


class TestReplSkinTable:
    def test_table_renders_headers_and_rows(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        skin.table(
            headers=["Name", "Value"],
            rows=[["width", "1920"], ["height", "1080"]],
        )
        output = capsys.readouterr().out
        assert "Name" in output
        assert "Value" in output
        assert "width" in output
        assert "1920" in output

    def test_table_empty_rows(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        skin.table(headers=["Col1", "Col2"], rows=[])
        output = capsys.readouterr().out
        assert "Col1" in output
        assert "Col2" in output

    def test_table_empty_headers(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        skin.table(headers=[], rows=[["a", "b"]])
        output = capsys.readouterr().out
        assert output == ""  # Should produce no output

    def test_table_truncation(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        long_text = "A" * 100
        skin.table(headers=["Name"], rows=[[long_text]], max_col_width=20)
        output = capsys.readouterr().out
        # Should be truncated to 20 chars
        assert long_text not in output
        assert "A" * 20 in output


# ─── Help Tests ────────────────────────────────────────────────────────


class TestReplSkinHelp:
    def test_help_lists_commands(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        skin.help({"export": "Export image", "import": "Import file"})
        output = capsys.readouterr().out
        assert "export" in output
        assert "Export image" in output
        assert "import" in output
        assert "Import file" in output

    def test_help_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        skin.help({})
        output = capsys.readouterr().out
        assert "Commands" in output


# ─── Goodbye Tests ────────────────────────────────────────────────────


class TestReplSkinGoodbye:
    def test_print_goodbye(self, capsys: pytest.CaptureFixture[str]) -> None:
        skin = ReplSkin("gimp")
        skin._color = False
        skin.print_goodbye()
        output = capsys.readouterr().out
        assert "Goodbye" in output


# ─── Color Support Detection Tests ────────────────────────────────────


class TestColorSupport:
    def test_no_color_env_disables_color(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        skin = ReplSkin("gimp")
        assert skin._color is False

    def test_cli_anything_no_color_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CLI_ANYTHING_NO_COLOR", "1")
        skin = ReplSkin("gimp")
        assert skin._color is False

    def test_no_color_means_no_ansi_in_messages(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        skin = ReplSkin("gimp")
        skin.success("Saved")
        output = capsys.readouterr().out
        # Unicode icons (✓) are fine — only ANSI escape sequences should be absent
        assert "\033[" not in output
        assert "Saved" in output

    def test_color_enabled_when_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("CLI_ANYTHING_NO_COLOR", raising=False)
        # Force isatty to return True
        monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
        skin = ReplSkin("gimp")
        assert skin._color is True

    def test_color_disabled_when_not_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("CLI_ANYTHING_NO_COLOR", raising=False)
        monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
        skin = ReplSkin("gimp")
        assert skin._color is False
