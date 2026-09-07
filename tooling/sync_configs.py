#!/usr/bin/env python3
"""
Multi-Target AI Configuration Deployment Engine
Author: Andrew J. Siebert (@Siebe41)

Merges core `global/` AI assets with dynamic domain templates (`templates/<domain>`)
and builds target configs for .github, CLAUDE.md, .vscode, .copilot, .claude/skills,
and .claude/settings.json (hooks).

Selection is persisted per target repo in `.ai-governance.json`: which domain
templates are active, which individual instructions/prompts/agents/skills/hooks are
excluded, and which project-local folders should be merged in as "bring your
own" additions. See CATEGORIES below for the fixed set of asset categories.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# Base Paths (Resolves relative to this script location)
SCRIPT_DIR = Path(__file__).parent.resolve()

# DEFAULT: Assumes script lives in `tooling/` inside standalone repo
# IF EMBEDDED as sub-repo/submodule (e.g. `vendor/ai-governance/tooling/`),
# change to: REPO_ROOT = SCRIPT_DIR.parent.parent.parent
REPO_ROOT = SCRIPT_DIR.parent

GLOBAL_DIR = REPO_ROOT / "global"
TEMPLATES_DIR = REPO_ROOT / "templates"

CONFIG_FILENAME = ".ai-governance.json"
CATEGORIES = ("instructions", "prompts", "agents", "skills", "hooks")


def get_kit_version() -> str:
    """Reads the starter kit's own VERSION file, stamped into every generated output."""
    version_file = REPO_ROOT / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def get_available_templates() -> list[str]:
    """Scans the templates directory for selectable subfolders."""
    if not TEMPLATES_DIR.exists():
        return []
    return sorted([d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir()])


def _empty_category_map() -> dict[str, list[str]]:
    return {category: [] for category in CATEGORIES}


def load_selection_config(output_dir: Path) -> dict | None:
    """Loads a target repo's saved include/exclude/local-dirs selection, if one exists."""
    config_file = output_dir / CONFIG_FILENAME
    if not config_file.exists():
        return None

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"⚠️  Could not parse {CONFIG_FILENAME} ({e}). Ignoring saved selection.")
        return None

    # Backfill missing keys so a hand-edited or older config stays forward-compatible.
    config = {
        "version": 1,
        "templates": data.get("templates", []),
        "exclude": {**_empty_category_map(), **data.get("exclude", {})},
        "local_dirs": {**_empty_category_map(), **data.get("local_dirs", {})},
    }
    return config


def save_selection_config(output_dir: Path, config: dict):
    """Persists the resolved selection so future syncs reuse it without re-prompting."""
    config_file = output_dir / CONFIG_FILENAME
    config_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(
        f"  [+] Saved selection to {CONFIG_FILENAME} — edit `exclude` to drop individual "
        f"assets, or `local_dirs` to add your own, then re-run the sync."
    )


def prompt_user_template_selection(available: list[str]) -> list[str]:
    """Interactive menu allowing the user to select any combination of templates or none."""
    if not available:
        print("ℹ️  No sub-templates found in `templates/`. Proceeding with `global/` only.\n")
        return []

    print("\n========================================================")
    print(" 🛠️  AI Configuration Deployment Menu")
    print("========================================================\n")
    print("Available Domain Templates:")
    print("  [0] None (Deploy Global configuration only)")
    for idx, tmpl in enumerate(available, start=1):
        print(f"  [{idx}] {tmpl}")

    print("\nSelect templates to overlay on top of Global.")
    print("  • Enter numbers separated by spaces or commas (e.g. '1, 3' or '1 2')")
    print("  • Press ENTER or type '0' for Global only\n")

    try:
        user_input = input("Your selection: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled.")
        sys.exit(0)

    if not user_input or user_input == "0":
        return []

    raw_choices = user_input.replace(",", " ").split()
    selected_templates = []

    for choice in raw_choices:
        if choice.isdigit():
            val = int(choice)
            if val == 0:
                return []
            elif 1 <= val <= len(available):
                selected_name = available[val - 1]
                if selected_name not in selected_templates:
                    selected_templates.append(selected_name)
            else:
                print(f"⚠️  Ignoring invalid option number: {val}")

    return selected_templates


def collect_markdown_files(sources: list[Path], exclude: set[str] = frozenset()) -> str:
    """Combines all markdown instructions into a single unified stream, skipping excluded files."""
    exclude_lower = {name.lower() for name in exclude}
    combined_content = []
    for source in sources:
        if source.exists() and source.is_dir():
            for file_path in sorted(source.glob("*.md")):
                if file_path.name.lower() in exclude_lower:
                    continue
                header = f"\n\n<!-- === Source: {file_path.name} === -->\n\n"
                combined_content.append(header + file_path.read_text(encoding="utf-8"))
    return "".join(combined_content).strip()


def build_github_target(dest_dir: Path, combined_instructions: str):
    """Builds .github/ target configuration (Copilot Instructions)."""
    github_dir = dest_dir / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)

    copilot_file = github_dir / "copilot-instructions.md"
    copilot_file.write_text(combined_instructions, encoding="utf-8")
    print(f"  [+] Generated: {copilot_file.relative_to(dest_dir) if dest_dir in copilot_file.parents else copilot_file}")


def build_claude_target(dest_dir: Path, combined_instructions: str):
    """Builds CLAUDE.md at the target repo root for Claude Code / Claude Agent SDK."""
    claude_file = dest_dir / "CLAUDE.md"
    claude_file.write_text(combined_instructions, encoding="utf-8")
    print(f"  [+] Generated: {claude_file.relative_to(dest_dir) if dest_dir in claude_file.parents else claude_file}")


def build_vscode_target(dest_dir: Path, prompt_sources: list[Path], exclude: set[str] = frozenset()):
    """Builds .vscode/ target configuration (Prompts and Workspace Settings)."""
    vscode_dir = dest_dir / ".vscode"
    prompts_dest = vscode_dir / "prompts"
    prompts_dest.mkdir(parents=True, exist_ok=True)
    exclude_lower = {name.lower() for name in exclude}

    for source in prompt_sources:
        if source.exists() and source.is_dir():
            for prompt_file in source.glob("*.md"):
                if prompt_file.stem.lower() == "readme":
                    continue
                if prompt_file.name.lower() in exclude_lower:
                    continue
                shutil.copy(prompt_file, prompts_dest / prompt_file.name)
                print(f"  [+] Copied VS Code Prompt: {prompt_file.name}")


def build_copilot_target(dest_dir: Path, agent_sources: list[Path], exclude: set[str] = frozenset()):
    """Builds .copilot/ target configuration for custom agent definitions."""
    copilot_dir = dest_dir / ".copilot" / "agents"
    copilot_dir.mkdir(parents=True, exist_ok=True)
    exclude_lower = {name.lower() for name in exclude}

    for source in agent_sources:
        if source.exists() and source.is_dir():
            for item in source.glob("*.*"):
                if item.stem.lower() == "readme":
                    continue
                if item.name.lower() in exclude_lower:
                    continue
                shutil.copy(item, copilot_dir / item.name)
                print(f"  [+] Copied Copilot Agent: {item.name}")


def build_skills_target(dest_dir: Path, skill_sources: list[Path], exclude: set[str] = frozenset()):
    """Builds .claude/skills/<name>/ for Claude Code's native Skills system.

    Unlike prompts/agents (single files), each skill is a folder — SKILL.md plus
    any co-located reference files — so exclusion and copying operate on the
    folder name, and each skill folder is copied wholesale.
    """
    skills_dir = dest_dir / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    exclude_lower = {name.lower() for name in exclude}

    for source in skill_sources:
        if source.exists() and source.is_dir():
            for skill_folder in sorted(p for p in source.iterdir() if p.is_dir()):
                if skill_folder.name.lower() in exclude_lower:
                    continue
                dest_folder = skills_dir / skill_folder.name
                if dest_folder.exists():
                    shutil.rmtree(dest_folder)
                shutil.copytree(skill_folder, dest_folder)
                print(f"  [+] Copied Claude Skill: {skill_folder.name}/")


def build_hooks_target(dest_dir: Path, hook_sources: list[Path], exclude: set[str] = frozenset()):
    """Merges global/hooks/*.json fragments into .claude/settings.json's `hooks` block.

    Unlike every other category, `.claude/settings.json` is a single file a target
    repo may already have hand-edited content in (permissions, env vars, other
    hooks) — so this MERGES rather than overwrites: existing top-level keys are
    left untouched, and a fragment is appended to its `hooks.<event>` array only
    if an identical entry isn't already there (safe/idempotent to re-run).

    Each fragment names one `event` (e.g. "Stop") and one `hook` object — exactly
    the shape Claude Code expects inside `settings.json`'s `hooks.<event>` array
    (an optional `matcher` plus a required `hooks: [...]` list of commands).
    """
    claude_dir = dest_dir / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_file = claude_dir / "settings.json"
    exclude_lower = {name.lower() for name in exclude}

    if settings_file.exists():
        try:
            settings = json.loads(settings_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(
                f"  [!] {settings_file} is not valid JSON ({e}). Skipping hook "
                f"deployment rather than risk corrupting a hand-edited file — "
                f"fix it and re-run."
            )
            return
    else:
        settings = {}

    settings.setdefault("hooks", {})
    merged = []
    for source in hook_sources:
        if not (source.exists() and source.is_dir()):
            continue
        for fragment_path in sorted(source.glob("*.json")):
            if fragment_path.stem.lower() in exclude_lower:
                continue
            try:
                fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"  [!] Skipping malformed hook fragment {fragment_path.name}: {e}")
                continue

            event = fragment.get("event")
            hook_entry = fragment.get("hook")
            if not event or not isinstance(hook_entry, dict):
                print(f"  [!] Skipping {fragment_path.name}: missing 'event' or 'hook' object.")
                continue

            event_list = settings["hooks"].setdefault(event, [])
            if hook_entry in event_list:
                continue  # already present from a previous sync — no-op
            event_list.append(hook_entry)
            merged.append(f"{event}: {fragment.get('name', fragment_path.stem)}")

    settings_file.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    if merged:
        for entry in merged:
            print(f"  [+] Merged hook into .claude/settings.json — {entry}")
    else:
        print("  [i] .claude/settings.json hooks already up to date.")


def build_mcp_targets(dest_dir: Path):
    """Deploys global MCP server configurations to client-specific directories."""
    mcp_source = GLOBAL_DIR / "mcp" / "mcp-servers.json"

    if not mcp_source.exists():
        print("  [!] No global mcp-servers.json found. Skipping MCP deployment.")
        return

    mcp_data = json.loads(mcp_source.read_text(encoding="utf-8"))

    # 1. VS Code Target (.vscode/mcp.json)
    vscode_mcp_dir = dest_dir / ".vscode"
    vscode_mcp_dir.mkdir(parents=True, exist_ok=True)

    # Ensures compatibility with VS Code MCP schema
    vscode_mcp_config = {
        "servers": mcp_data.get("mcpServers", mcp_data.get("servers", {}))
    }

    vscode_mcp_file = vscode_mcp_dir / "mcp.json"
    vscode_mcp_file.write_text(json.dumps(vscode_mcp_config, indent=2), encoding="utf-8")
    print(f"  [+] Generated VS Code MCP Config: {vscode_mcp_file.relative_to(dest_dir) if dest_dir in vscode_mcp_file.parents else vscode_mcp_file}")

    # 2. Copilot Agent / Generic Target (.copilot/mcp.json)
    copilot_mcp_dir = dest_dir / ".copilot"
    copilot_mcp_dir.mkdir(parents=True, exist_ok=True)

    copilot_mcp_file = copilot_mcp_dir / "mcp.json"
    copilot_mcp_file.write_text(json.dumps(mcp_data, indent=2), encoding="utf-8")
    print(f"  [+] Generated Copilot Agent MCP Config: {copilot_mcp_file.relative_to(dest_dir) if dest_dir in copilot_mcp_file.parents else copilot_mcp_file}")


def build_learnings_log_target(dest_dir: Path):
    """Seeds LEARNINGS.md at the target repo root, without ever overwriting an existing log."""
    dest_file = dest_dir / "LEARNINGS.md"

    if dest_file.exists():
        print(f"  [i] LEARNINGS.md already exists — leaving accumulated entries untouched.")
        return

    template_source = GLOBAL_DIR / "LEARNINGS.template.md"
    if not template_source.exists():
        print("  [!] No LEARNINGS.template.md found in global/. Skipping learnings log seed.")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(template_source, dest_file)
    print(f"  [+] Seeded: {dest_file.relative_to(dest_dir) if dest_dir in dest_file.parents else dest_file}")


def sync(cli_templates: list[str] | None, output_dir: Path, reconfigure: bool, available_templates: list[str]):
    """Main execution pipeline."""
    print(f"\n🚀 Starting AI Configuration Sync...")
    print(f"📍 Target Output: {output_dir.resolve()}")

    saved_config = None if reconfigure else load_selection_config(output_dir)
    templates_explicit = cli_templates is not None

    if templates_explicit:
        selected_templates = cli_templates
    elif saved_config is not None:
        selected_templates = saved_config["templates"]
        print(
            f"ℹ️  Reusing saved template selection from {CONFIG_FILENAME} "
            f"(pass --templates to change it, or --reconfigure to re-select from scratch)."
        )
    else:
        selected_templates = prompt_user_template_selection(available_templates)

    exclude = saved_config["exclude"] if saved_config else _empty_category_map()
    local_dirs_cfg = saved_config["local_dirs"] if saved_config else _empty_category_map()

    print(f"🎨 Selected Templates: {', '.join(selected_templates) if selected_templates else 'None (Global Only)'}\n")

    instruction_paths = [GLOBAL_DIR / "instructions"]
    prompt_paths = [GLOBAL_DIR / "prompts"]
    agent_paths = [GLOBAL_DIR / "agents"]
    skill_paths = [GLOBAL_DIR / "skills"]
    hook_paths = [GLOBAL_DIR / "hooks"]

    for tmpl in selected_templates:
        tmpl_path = TEMPLATES_DIR / tmpl
        if not tmpl_path.exists():
            print(f"⚠️  Warning: Template '{tmpl}' not found under {TEMPLATES_DIR}. Skipping.")
            continue
        instruction_paths.append(tmpl_path / "instructions")
        prompt_paths.append(tmpl_path / "prompts")
        agent_paths.append(tmpl_path / "agents")
        skill_paths.append(tmpl_path / "skills")
        hook_paths.append(tmpl_path / "hooks")

    # "Bring your own": project-local folders (outside this vendored kit) layer in last,
    # so they survive re-vendoring the canonical source via subtree/submodule updates.
    instruction_paths += [output_dir / d for d in local_dirs_cfg["instructions"]]
    prompt_paths += [output_dir / d for d in local_dirs_cfg["prompts"]]
    agent_paths += [output_dir / d for d in local_dirs_cfg["agents"]]
    skill_paths += [output_dir / d for d in local_dirs_cfg["skills"]]
    hook_paths += [output_dir / d for d in local_dirs_cfg["hooks"]]

    # 1. Gather combined markdown instructions, stamped with the source kit's version
    #    so a downstream repo can tell which version of the org's rules it's running.
    version_header = (
        f"<!-- Generated by ai-governance-starter-kit v{get_kit_version()} — "
        f"do not edit directly; edit global/ (and any selected templates/ or "
        f"local_dirs/) and re-run tooling/sync_configs.py -->\n"
    )
    combined_instructions = version_header + "\n" + collect_markdown_files(
        instruction_paths, exclude=set(exclude["instructions"])
    )

    # 2. Deploy Target Configurations
    print("📦 Deploying .github Configuration...")
    build_github_target(output_dir, combined_instructions)

    print("\n📦 Deploying Claude Code Configuration...")
    build_claude_target(output_dir, combined_instructions)

    print("\n📦 Deploying .vscode Configuration...")
    build_vscode_target(output_dir, prompt_paths, exclude=set(exclude["prompts"]))

    print("\n📦 Deploying .copilot Configuration...")
    build_copilot_target(output_dir, agent_paths, exclude=set(exclude["agents"]))

    print("\n📦 Deploying Claude Skills...")
    build_skills_target(output_dir, skill_paths, exclude=set(exclude["skills"]))

    print("\n📦 Deploying Claude Code Hooks...")
    build_hooks_target(output_dir, hook_paths, exclude=set(exclude["hooks"]))

    print("\n📦 Deploying Global MCP Servers...")
    build_mcp_targets(output_dir)

    print("\n📦 Seeding Learnings Log...")
    build_learnings_log_target(output_dir)

    save_selection_config(output_dir, {
        "version": 1,
        "templates": selected_templates,
        "exclude": exclude,
        "local_dirs": local_dirs_cfg,
    })

    print("\n✅ AI Configuration Sync Completed Successfully!\n")


def main():
    available = get_available_templates()

    parser = argparse.ArgumentParser(
        description="Sync and build multi-target AI configurations for .github, CLAUDE.md, .vscode, .copilot, .claude/skills, and .claude/settings.json (hooks)."
    )
    parser.add_argument(
        "-t", "--templates",
        nargs="*",
        default=None,
        choices=available if available else None,
        help=f"Select domain templates to overlay on top of Global. Options: {', '.join(available)}"
    )
    parser.add_argument(
        "-o", "--output",
        default=str(REPO_ROOT),
        help="Target repository directory to output configs into (defaults to repo root)."
    )
    parser.add_argument(
        "--reconfigure",
        action="store_true",
        help=f"Ignore any saved {CONFIG_FILENAME} in the output directory and re-run interactive "
             f"template selection from scratch, overwriting it. Excludes/local_dirs are reset to empty."
    )

    args = parser.parse_args()

    sync(args.templates, Path(args.output), args.reconfigure, available)


if __name__ == "__main__":
    main()
