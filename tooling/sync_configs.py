#!/usr/bin/env python3
"""
Multi-Target AI Configuration Deployment Engine
Author: Andrew J. Siebert (@Siebe41)

Merges core `global/` AI assets with dynamic domain templates (`templates/<domain>`)
and builds target configs for .github, .vscode, and .copilot.
"""

import argparse
import json
import os
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


def get_available_templates() -> list[str]:
    """Scans the templates directory for selectable subfolders."""
    if not TEMPLATES_DIR.exists():
        return []
    return sorted([d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir()])


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


def collect_markdown_files(sources: list[Path]) -> str:
    """Combines all markdown instructions into a single unified stream."""
    combined_content = []
    for source in sources:
        if source.exists() and source.is_dir():
            for file_path in sorted(source.glob("*.md")):
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


def build_vscode_target(dest_dir: Path, prompt_sources: list[Path]):
    """Builds .vscode/ target configuration (Prompts and Workspace Settings)."""
    vscode_dir = dest_dir / ".vscode"
    prompts_dest = vscode_dir / "prompts"
    prompts_dest.mkdir(parents=True, exist_ok=True)

    for source in prompt_sources:
        if source.exists() and source.is_dir():
            for prompt_file in source.glob("*.md"):
                if prompt_file.stem.lower() == "readme":
                    continue
                shutil.copy(prompt_file, prompts_dest / prompt_file.name)
                print(f"  [+] Copied VS Code Prompt: {prompt_file.name}")


def build_copilot_target(dest_dir: Path, agent_sources: list[Path]):
    """Builds .copilot/ target configuration for custom agent definitions."""
    copilot_dir = dest_dir / ".copilot" / "agents"
    copilot_dir.mkdir(parents=True, exist_ok=True)

    for source in agent_sources:
        if source.exists() and source.is_dir():
            for item in source.glob("*.*"):
                if item.stem.lower() == "readme":
                    continue
                shutil.copy(item, copilot_dir / item.name)
                print(f"  [+] Copied Copilot Agent: {item.name}")


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


def sync(selected_templates: list[str], output_dir: Path):
    """Main execution pipeline."""
    print(f"\n🚀 Starting AI Configuration Sync...")
    print(f"📍 Target Output: {output_dir.resolve()}")
    print(f"🎨 Selected Templates: {', '.join(selected_templates) if selected_templates else 'None (Global Only)'}\n")

    instruction_paths = [GLOBAL_DIR / "instructions"]
    prompt_paths = [GLOBAL_DIR / "prompts"]
    agent_paths = [GLOBAL_DIR / "agents"]

    for tmpl in selected_templates:
        tmpl_path = TEMPLATES_DIR / tmpl
        if not tmpl_path.exists():
            print(f"⚠️  Warning: Template '{tmpl}' not found under {TEMPLATES_DIR}. Skipping.")
            continue
        instruction_paths.append(tmpl_path / "instructions")
        prompt_paths.append(tmpl_path / "prompts")
        agent_paths.append(tmpl_path / "agents")

    # 1. Gather combined markdown instructions
    combined_instructions = collect_markdown_files(instruction_paths)

    # 2. Deploy Target Configurations
    print("📦 Deploying .github Configuration...")
    build_github_target(output_dir, combined_instructions)

    print("\n📦 Deploying .vscode Configuration...")
    build_vscode_target(output_dir, prompt_paths)

    print("\n📦 Deploying .copilot Configuration...")
    build_copilot_target(output_dir, agent_paths)

    print("\n📦 Deploying Global MCP Servers...")
    build_mcp_targets(output_dir)

    print("\n📦 Seeding Learnings Log...")
    build_learnings_log_target(output_dir)

    print("\n✅ AI Configuration Sync Completed Successfully!\n")


def main():
    available = get_available_templates()
    
    parser = argparse.ArgumentParser(
        description="Sync and build multi-target AI configurations for .github, .vscode, and .copilot."
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

    args = parser.parse_args()

    # Trigger interactive menu if no --templates flag is passed
    if args.templates is None:
        selected = prompt_user_template_selection(available)
    else:
        selected = args.templates

    sync(selected, Path(args.output))


if __name__ == "__main__":
    main()