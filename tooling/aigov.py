#!/usr/bin/env python3
"""
aigov: deploy this starter kit's AI governance assets into a project repo.

    python tooling/aigov.py install  [--output DIR] [--templates UI ...]
    python tooling/aigov.py sync     [--output DIR] [--force]
    python tooling/aigov.py migrate  [--output DIR] [--yes] [--force]
    python tooling/aigov.py status   [--output DIR]

Rules this tool follows (see TARGETS.md for the full path map):

  * There's no tool to choose. Always-on rules go to AGENTS.md, which GitHub
    Copilot and Claude Code both read; everything else is written for both
    tools, only to the paths those tools document.
  * It never guesses. If a choice hasn't been made, or a run would overwrite or
    delete something it can't prove it wrote, it stops and tells you why.
    Nothing is changed until every check passes.
  * Every file it writes is recorded in .ai-governance.json with a content
    fingerprint. That record is how sync cleans up and how migrate knows what
    it may delete. Files the tool didn't write are never touched.

Zero dependencies (Python 3.9+ standard library only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_DIR = KIT_ROOT / "global"
TEMPLATES_DIR = KIT_ROOT / "templates"
CONFIG_NAME = ".ai-governance.json"
CONFIG_VERSION = 3
CATEGORIES = ("instructions", "prompts", "agents", "skills", "hooks", "workflows")

# Every run writes for all of these. The label groups the report and the record in
# .ai-governance.json; it is not a choice.
TOOLS = {
    "shared": "Both tools (AGENTS.md and skills are read by Copilot and Claude Code)",
    "copilot": "GitHub Copilot (VS Code, Visual Studio, github.com, Copilot CLI)",
    "claude-code": "Claude Code",
}

# If any of these exists, Claude Code reads it instead of AGENTS.md (by default).
CLAUDE_MD_FILES = ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md")

# Files this tool treats as documentation, never as deployable assets.
DOC_FILES = {"readme.md"}


class Refusal(Exception):
    """Raised when a run would require guessing. Nothing has been changed."""


# --------------------------------------------------------------------------- helpers

def kit_version() -> str:
    version_file = KIT_ROOT / "VERSION"
    return version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown"


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n")


def fingerprint(data: str) -> str:
    """Hash with line endings normalized, so a CRLF checkout on Windows still matches."""
    return hashlib.sha256(normalize(data).encode("utf-8")).hexdigest()


def read_text(path: Path) -> str:
    return normalize(path.read_text(encoding="utf-8"))


def is_doc(path: Path) -> bool:
    return path.name.lower() in DOC_FILES


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def first_heading(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            return re.sub(r"^System Prompt:\s*", "", title)
    return ""


def split_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    """Minimal frontmatter reader for simple `key: value` lines."""
    if not markdown.startswith("---\n"):
        return {}, markdown
    end = markdown.find("\n---", 4)
    if end == -1:
        return {}, markdown
    meta = {}
    for line in markdown[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("'\"")
    body = markdown[end + 4:].lstrip("\n")
    return meta, body


def yaml_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def parse_agent_yml(text: str, source: Path) -> dict[str, str]:
    """Reads the kit's agent .yml shape: agent.name, agent.description, agent.system_prompt (block).

    Deliberately strict: anything it doesn't recognize is a refusal, not a guess.
    """
    lines = normalize(text).split("\n")
    out: dict[str, str] = {}
    i = 0
    in_agent = False
    while i < len(lines):
        line = lines[i]
        if line.startswith("agent:"):
            in_agent = True
        elif in_agent and re.match(r"^  (name|description):", line):
            key, _, value = line.strip().partition(":")
            out[key] = value.strip().strip('"').strip("'")
        elif in_agent and re.match(r"^  system_prompt:\s*\|\s*$", line):
            block = []
            i += 1
            while i < len(lines) and (lines[i].startswith("    ") or lines[i].strip() == ""):
                block.append(lines[i][4:] if lines[i].startswith("    ") else "")
                i += 1
            out["system_prompt"] = "\n".join(block).strip() + "\n"
            continue
        i += 1
    missing = [k for k in ("name", "description", "system_prompt") if k not in out]
    if missing:
        raise Refusal(f"{source} is missing {', '.join(missing)} under `agent:`. "
                      f"Fix the source file; aigov won't guess an agent's definition.")
    return out


def slug(stem: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", stem.lower()).strip("-")


# --------------------------------------------------------------------------- config

def empty_categories() -> dict[str, list[str]]:
    return {c: [] for c in CATEGORIES}


def load_config(project: Path) -> dict | None:
    path = project / CONFIG_NAME
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))  # tolerate a BOM (Windows PowerShell 5.1)
    except json.JSONDecodeError as e:
        raise Refusal(f"{CONFIG_NAME} isn't valid JSON ({e}). Fix it by hand; aigov won't overwrite it.")


def save_config(project: Path, config: dict) -> None:
    (project / CONFIG_NAME).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")


def available_templates() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(d.name for d in TEMPLATES_DIR.iterdir() if d.is_dir())


# --------------------------------------------------------------------------- source collection

def sources_for(category: str, config: dict, project: Path) -> list[tuple[str, Path]]:
    """Returns (layer, dir) pairs in precedence order: global, templates, project-local."""
    dirs: list[tuple[str, Path]] = [("global", GLOBAL_DIR / category)]
    for tmpl in config.get("templates", []):
        dirs.append((f"template:{tmpl}", TEMPLATES_DIR / tmpl / category))
    for local in config.get("local_dirs", {}).get(category, []):
        dirs.append(("local", project / local))
    return [(layer, d) for layer, d in dirs if d.is_dir()]


def excluded(f: Path, excl: set[str]) -> bool:
    """hooks and workflows can be excluded by filename or by stem (`lint-before-finish`)."""
    return f.name.lower() in excl or f.stem.lower() in excl


def collect_hooks(config: dict, project: Path) -> dict[str, list[dict]]:
    """Builds `.claude/settings.json`'s `hooks` block from every hook fragment.

    Each fragment names one `event` and one `hook` object, the exact shape Claude Code
    expects inside `hooks.<event>`. An identical entry from two layers is kept once.
    """
    excl = {n.lower() for n in config.get("exclude", {}).get("hooks", [])}
    hooks: dict[str, list[dict]] = {}
    for _layer, d in sources_for("hooks", config, project):
        for f in sorted(d.glob("*.json")):
            if excluded(f, excl):
                continue
            try:
                fragment = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                raise Refusal(f"{f} isn't valid JSON ({e}). Fix the source file.")
            event, entry = fragment.get("event"), fragment.get("hook")
            if not event or not isinstance(entry, dict):
                raise Refusal(f"{f} needs an `event` and a `hook` object. See global/hooks/readme.md.")
            if entry not in hooks.setdefault(event, []):
                hooks[event].append(entry)
    return hooks


def collect_workflows(config: dict, project: Path) -> list[Path]:
    excl = {n.lower() for n in config.get("exclude", {}).get("workflows", [])}
    return [f for _layer, d in sources_for("workflows", config, project)
            for f in sorted(d.iterdir())
            if f.is_file() and f.suffix.lower() in (".yml", ".yaml") and not excluded(f, excl)]


def factory_files() -> list[Path]:
    """The engine ships whole, readme included: it's the operator's guide to `.factory/`."""
    source = GLOBAL_DIR / "factory"
    if not source.is_dir():
        return []
    return [f for f in sorted(source.rglob("*")) if f.is_file() and "__pycache__" not in f.parts]


def overlay_apply_to(template: str) -> str | None:
    meta_file = TEMPLATES_DIR / template / "overlay.json"
    if meta_file.exists():
        return json.loads(meta_file.read_text(encoding="utf-8")).get("applyTo")
    return None


# --------------------------------------------------------------------------- planning

class Plan:
    """Every file a run intends to write: relative path -> (tool, content)."""

    def __init__(self) -> None:
        self.files: dict[str, tuple[str, str]] = {}
        self.notes: list[str] = []

    def add(self, path: str, tool: str, content: str) -> None:
        if path in self.files and self.files[path][1] != normalize(content):
            raise Refusal(f"Two sources want to write different content to {path}. "
                          f"Rename one of them; aigov won't pick a winner.")
        self.files[path] = (tool, normalize(content))


def build_plan(config: dict, project: Path) -> Plan:
    excl = {c: {n.lower() for n in config.get("exclude", {}).get(c, [])} for c in CATEGORIES}
    header = (f"<!-- Generated by ai-governance-starter-kit v{kit_version()}. Do not edit; "
              f"change the kit (or this repo's local_dirs) and run `aigov.py sync`. -->\n\n")
    plan = Plan()

    # ---- instructions
    always_on: list[tuple[str, str]] = []           # (source name, text) for every tool
    overlays: list[tuple[str, str, str]] = []        # (template, file stem, text)
    for layer, d in sources_for("instructions", config, project):
        for f in sorted(d.glob("*.md")):
            if is_doc(f) or f.name.lower() in excl["instructions"]:
                continue
            text = read_text(f)
            if layer.startswith("template:"):
                overlays.append((layer.split(":", 1)[1], f.stem, text))
            else:
                always_on.append((f.name, text))

    def joined(parts: list[tuple[str, str]]) -> str:
        return header + "\n\n".join(f"<!-- Source: {name} -->\n\n{text.strip()}" for name, text in parts) + "\n"

    # One always-on file both tools read. Overlays stay out of it: AGENTS.md can't be scoped
    # to file types, so each tool gets them in its own path-scoped format instead.
    plan.add("AGENTS.md", "shared", joined(always_on))
    for tmpl, stem, text in overlays:
        apply_to = overlay_apply_to(tmpl)
        if apply_to is None:
            plan.notes.append(f"templates/{tmpl} has no overlay.json applyTo; its rules load on every "
                              f"request. Add templates/{tmpl}/overlay.json to scope them.")
        name = f"{slug(tmpl)}-{slug(stem)}"
        plan.add(f".github/instructions/{name}.instructions.md", "copilot",
                 f"---\napplyTo: {yaml_string(apply_to or '**')}\n---\n\n{header}{text.strip()}\n")
        scope = f"---\npaths: {yaml_string(apply_to)}\n---\n\n" if apply_to else ""
        plan.add(f".claude/rules/{name}.md", "claude-code", f"{scope}{header}{text.strip()}\n")

    # ---- prompts
    for _layer, d in sources_for("prompts", config, project):
        for f in sorted(d.glob("*.md")):
            if is_doc(f) or f.name.lower() in excl["prompts"]:
                continue
            text = read_text(f)
            name = f.name[: -len(".prompt.md")] if f.name.endswith(".prompt.md") else f.stem
            meta, body = split_frontmatter(text)
            description = meta.get("description") or first_heading(body) or name
            plan.add(f".github/prompts/{name}.prompt.md", "copilot",
                     f"---\ndescription: {yaml_string(description)}\n---\n\n{body.strip()}\n")
            plan.add(f".claude/commands/{name}.md", "claude-code",
                     f"---\ndescription: {yaml_string(description)}\n---\n\n{body.strip()}\n")

    # ---- agents
    for _layer, d in sources_for("agents", config, project):
        for f in sorted(d.iterdir()):
            if not f.is_file() or is_doc(f) or f.name.lower() in excl["agents"]:
                continue
            if f.suffix in (".yml", ".yaml"):
                agent = parse_agent_yml(f.read_text(encoding="utf-8"), f)
                stem, name, desc, prompt = f.stem, agent["name"], agent["description"], agent["system_prompt"]
                copilot_text = None
            elif f.name.endswith(".agent.md"):
                meta, body = split_frontmatter(read_text(f))
                stem = f.name[: -len(".agent.md")]
                name, desc, prompt = meta.get("name", stem), meta.get("description", ""), body
                copilot_text = read_text(f)  # already in Copilot's format: copy as-is
            else:
                raise Refusal(f"{f} isn't an agent format aigov understands (.yml or .agent.md).")
            plan.add(f".github/agents/{slug(stem)}.agent.md", "copilot", copilot_text or
                     f"---\nname: {yaml_string(name)}\ndescription: {yaml_string(desc)}\n---\n\n{prompt.strip()}\n")
            plan.add(f".claude/agents/{slug(stem)}.md", "claude-code",
                     f"---\nname: {slug(stem)}\ndescription: {yaml_string(desc)}\n---\n\n{prompt.strip()}\n")

    # ---- skills: written once to .claude/skills/, which Copilot reads too
    for _layer, d in sources_for("skills", config, project):
        for skill in sorted(p for p in d.iterdir() if p.is_dir()):
            if skill.name.lower() in excl["skills"] or not (skill / "SKILL.md").exists():
                continue
            for f in sorted(p for p in skill.rglob("*") if p.is_file()):
                if "__pycache__" in f.parts:
                    continue
                plan.add(f".claude/skills/{skill.name}/{rel(f, skill)}", "shared", read_text(f))

    # ---- hooks (Claude Code). aigov owns the whole file, so a hand-written settings.json is
    # refused like any other file aigov didn't write, rather than merged into.
    hooks = collect_hooks(config, project)
    if hooks:
        plan.add(".claude/settings.json", "claude-code", json.dumps({"hooks": hooks}, indent=2) + "\n")
        plan.notes.append(".claude/settings.json is generated from hook fragments. Keep personal settings "
                          "in .claude/settings.local.json, or exclude the hooks to manage settings.json yourself.")

    # ---- workflows + factory engine (Claude Code: the shipped workflows run claude-code-action
    # and the factory skills). Each workflow is recorded by name, so a repo's own CI beside it
    # is never touched. The engine ships only when a factory-* workflow does.
    workflows = collect_workflows(config, project)
    for f in workflows:
        plan.add(f".github/workflows/{f.name}", "claude-code", read_text(f))
    if any(f.name.startswith("factory-") for f in workflows):
        for f in factory_files():
            plan.add(f".factory/{rel(f, GLOBAL_DIR / 'factory')}", "claude-code", read_text(f))

    # ---- MCP servers
    mcp_source = GLOBAL_DIR / "mcp" / "mcp-servers.json"
    if mcp_source.exists():
        servers = json.loads(mcp_source.read_text(encoding="utf-8")).get("mcpServers", {})
        plan.add(".vscode/mcp.json", "copilot", json.dumps({"servers": servers}, indent=2) + "\n")
        plan.notes.append("Copilot's cloud agent on github.com doesn't read MCP servers from a file. "
                          "Configure them in the repo's Settings > Copilot > MCP servers.")
        plan.add(".mcp.json", "claude-code", json.dumps({"mcpServers": servers}, indent=2) + "\n")

    return plan


def summarize(paths) -> list[str]:
    """Collapses files inside a skill folder into one line per folder, for readable output."""
    lines, folders = [], {}
    for path in sorted(paths):
        m = re.match(r"^(.*/skills/[^/]+)/", path)
        if m:
            folders.setdefault(m.group(1), 0)
            folders[m.group(1)] += 1
        else:
            lines.append(path)
    return lines + [f"{folder}/  ({n} file{'s' if n != 1 else ''})" for folder, n in folders.items()]


# --------------------------------------------------------------------------- apply

def check_and_apply(project: Path, config: dict, plan: Plan, *, force: bool, dry_run: bool = False,
                    adopt: dict[str, str] | None = None) -> dict[str, list[str]]:
    """Validates the whole run first, then writes. Returns what changed."""
    recorded: dict[str, dict] = config.get("generated", {})
    adopt = adopt or {}
    problems: list[str] = []

    for path in plan.files:
        target_file = project / path
        if not target_file.exists():
            continue
        current = fingerprint(target_file.read_text(encoding="utf-8"))
        if path in recorded:
            if current != recorded[path]["sha256"] and not force:
                problems.append(f"{path} was edited by hand since aigov wrote it.")
        elif path in adopt:
            pass  # a v1 output that migrate has verified and the user approved replacing
        else:
            problems.append(f"{path} already exists and wasn't written by aigov.")

    stale = [p for p in recorded if p not in plan.files]
    for path in stale:
        target_file = project / path
        if target_file.exists() and fingerprint(target_file.read_text(encoding="utf-8")) != recorded[path]["sha256"] and not force:
            problems.append(f"{path} is no longer needed but was edited by hand, so it won't be deleted.")

    if problems:
        raise Refusal("Nothing was changed. Resolve these first:\n  - " + "\n  - ".join(problems) +
                      "\n\nMove or rename files you want to keep. To discard hand edits to files aigov wrote, "
                      "re-run with --force (it never touches files it didn't write).")

    changes = {"written": [], "unchanged": [], "removed": []}
    if dry_run:
        return changes

    for path, (_tool, content) in sorted(plan.files.items()):
        target_file = project / path
        if target_file.exists() and target_file.read_text(encoding="utf-8").replace("\r\n", "\n") == content:
            changes["unchanged"].append(path)
        else:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text(content, encoding="utf-8", newline="\n")
            changes["written"].append(path)
    for path in stale + [p for p in adopt if p not in plan.files]:
        target_file = project / path
        if target_file.exists():
            target_file.unlink()
            changes["removed"].append(path)
        remove_empty_parents(target_file.parent, project)

    config["generated"] = {p: {"tool": t, "sha256": fingerprint(c)} for p, (t, c) in sorted(plan.files.items())}
    config["kit_version"] = kit_version()
    save_config(project, config)
    seed_learnings(project)
    shadowing = [p for p in CLAUDE_MD_FILES if (project / p).exists()]
    if shadowing:
        plan.notes.append(f"{', '.join(shadowing)} exists, so Claude Code reads it instead of AGENTS.md. "
                          f"Add a line `@AGENTS.md` at the top of it so Claude Code gets the kit's rules too.")
    return changes


def remove_empty_parents(folder: Path, stop: Path) -> None:
    while folder != stop and folder.is_dir() and not any(folder.iterdir()):
        folder.rmdir()
        folder = folder.parent


def seed_learnings(project: Path) -> None:
    """LEARNINGS.md holds project knowledge: created once, never tracked, never deleted."""
    dest = project / "LEARNINGS.md"
    src = GLOBAL_DIR / "LEARNINGS.template.md"
    if not dest.exists() and src.exists():
        shutil.copy(src, dest)
        print("  [+] LEARNINGS.md (seeded once; aigov never overwrites or deletes it)")


def report(plan: Plan, changes: dict[str, list[str]]) -> None:
    by_tool: dict[str, list[str]] = {}
    for path, (tool, _c) in plan.files.items():
        by_tool.setdefault(tool, []).append(path)
    for tool in TOOLS:
        paths = sorted(by_tool.get(tool, []))
        if not paths:
            continue
        print(f"\n{TOOLS[tool]}: {len(paths)} file(s)   [+] written  [=] already current")
        skills: dict[str, list[str]] = {}
        for path in paths:
            m = re.match(r"^(.*/skills/[^/]+)/", path)
            if m:
                skills.setdefault(m.group(1), []).append(path)
                continue
            print(f"  [{'+' if path in changes['written'] else '='}] {path}")
        for folder, files in skills.items():
            mark = "+" if any(f in changes["written"] for f in files) else "="
            print(f"  [{mark}] {folder}/  ({len(files)} file{'s' if len(files) != 1 else ''})")
    if changes["removed"]:
        print("\nRemoved:")
        for line in summarize(changes["removed"]):
            print(f"  [-] {line}")
    for note in plan.notes:
        print(f"\nNote: {note}")


# --------------------------------------------------------------------------- v1 detection (for migrate)

V1_HEADER = "Generated by ai-governance-starter-kit v1."


def detect_v1_outputs(project: Path, config: dict) -> tuple[dict[str, str], list[str]]:
    """Finds files a v1 sync wrote. Returns (verified: path -> sha, unverified: paths).

    A file counts as verified only if its content proves v1 wrote it: the v1 header for
    generated markdown, or a byte-for-byte match with the kit source it was copied from.
    """
    verified: dict[str, str] = {}
    unverified: list[str] = []

    def consider(path: str, proof: bool) -> None:
        f = project / path
        if f.exists():
            (verified.__setitem__(path, fingerprint(f.read_text(encoding="utf-8"))) if proof else unverified.append(path))

    for path in (".github/copilot-instructions.md", "CLAUDE.md"):
        f = project / path
        if f.exists():
            consider(path, V1_HEADER in f.read_text(encoding="utf-8")[:200])

    copies = {".vscode/prompts": "prompts", ".copilot/agents": "agents"}
    for out_dir, category in copies.items():
        folder = project / out_dir
        if not folder.is_dir():
            continue
        sources = {f.name: f for _l, d in sources_for(category, config, project) for f in d.iterdir() if f.is_file()}
        for f in sorted(folder.iterdir()):
            if f.is_file():
                src = sources.get(f.name)
                consider(rel(f, project), bool(src) and read_text(src) == read_text(f))

    skills_out = project / ".claude" / "skills"
    if skills_out.is_dir() and "generated" not in config:
        skill_sources = {p.name: p for _l, d in sources_for("skills", config, project) for p in d.iterdir() if p.is_dir()}
        for f in sorted(p for p in skills_out.rglob("*") if p.is_file()):
            parts = f.relative_to(skills_out).parts
            src = skill_sources.get(parts[0])
            src_file = src.joinpath(*parts[1:]) if src else None
            consider(rel(f, project), bool(src_file) and src_file.exists() and read_text(src_file) == read_text(f))

    # v1.6 copied workflows and the factory engine verbatim, and merged hooks into settings.json.
    for f in collect_workflows(config, project):
        out = project / ".github" / "workflows" / f.name
        if out.exists():
            consider(rel(out, project), read_text(out) == read_text(f))
    factory_out = project / ".factory"
    if factory_out.is_dir():
        for f in sorted(p for p in factory_out.rglob("*") if p.is_file()):
            src = GLOBAL_DIR / "factory" / f.relative_to(factory_out)
            consider(rel(f, project), src.exists() and read_text(src) == read_text(f))
    settings = project / ".claude" / "settings.json"
    if settings.exists():
        try:
            consider(".claude/settings.json",
                     json.loads(settings.read_text(encoding="utf-8")) == {"hooks": collect_hooks(config, project)})
        except (json.JSONDecodeError, Refusal):
            consider(".claude/settings.json", False)

    for path in (".vscode/mcp.json", ".copilot/mcp.json"):
        f = project / path
        if f.exists():
            mcp_source = GLOBAL_DIR / "mcp" / "mcp-servers.json"
            servers = json.loads(mcp_source.read_text(encoding="utf-8")) if mcp_source.exists() else {}
            v1 = {"servers": servers.get("mcpServers", {})} if path.startswith(".vscode") else servers
            try:
                consider(path, json.loads(f.read_text(encoding="utf-8")) == v1)
            except json.JSONDecodeError:
                consider(path, False)
    return verified, unverified


# --------------------------------------------------------------------------- commands

def ask_templates() -> list[str]:
    available = available_templates()
    if not available:
        return []
    if not sys.stdin.isatty():
        raise Refusal("Domain overlays haven't been chosen and there's no terminal to ask in. "
                      "Pass --templates (with no names for none).")
    print("\nDomain overlays to add on top of the Global rules:")
    print("  [0] none")
    for i, name in enumerate(available, 1):
        print(f"  [{i}] {name}")
    answer = input("Your selection (e.g. '1 2', Enter for none): ").strip()
    if answer in ("", "0"):
        return []
    return [available[int(a) - 1] for a in answer.replace(",", " ").split() if a.isdigit() and 1 <= int(a) <= len(available)]


def resolve_project(output: str | None) -> Path:
    project = Path(output).resolve() if output else Path.cwd()
    if not project.is_dir():
        raise Refusal(f"{project} isn't a folder.")
    if project == KIT_ROOT:
        raise Refusal("That's the starter kit itself. Run aigov from (or --output to) the project repo.")
    return project


def ignore_targets(args) -> None:
    """--targets was how v2 chose a tool. Accepted so old scripts keep working, and ignored."""
    if getattr(args, "targets", None) is not None:
        print("Note: --targets is no longer used. aigov writes AGENTS.md plus both tools' files; ignoring it.",
              file=sys.stderr)


def cmd_install(args) -> None:
    ignore_targets(args)
    project = resolve_project(args.output)
    config = load_config(project) or {}
    if config.get("version", CONFIG_VERSION) < CONFIG_VERSION or config.get("targets"):
        raise Refusal("This repo was set up with an older version of the kit. Run `migrate` instead; it "
                      "shows what it will replace and asks first.")
    if "generated" in config:
        raise Refusal(f"{project.name} is already installed. Use `sync` to update it.")
    v1_verified, _ = detect_v1_outputs(project, config)
    if v1_verified:
        raise Refusal("This repo was set up with the v1 kit. Run `migrate` instead; it checks each v1 "
                      "file before replacing it.")
    if args.templates is not None:
        templates = args.templates
    elif "templates" in config:
        templates = config["templates"]          # pre-seeded in .ai-governance.json: respect it
    else:
        templates = ask_templates()
    config = {
        "version": CONFIG_VERSION,
        "templates": templates,
        "exclude": {**empty_categories(), **config.get("exclude", {})},
        "local_dirs": {**empty_categories(), **config.get("local_dirs", {})},
    }
    unknown = [t for t in config["templates"] if t not in available_templates()]
    if unknown:
        raise Refusal(f"Unknown template(s): {', '.join(unknown)}. Available: {', '.join(available_templates()) or 'none'}.")
    plan = build_plan(config, project)
    changes = check_and_apply(project, config, plan, force=False)
    print(f"\nInstalled ai-governance-starter-kit v{kit_version()} into {project}")
    report(plan, changes)


def cmd_sync(args) -> None:
    project = resolve_project(args.output)
    config = load_config(project)
    current = bool(config) and config.get("version", 1) >= CONFIG_VERSION and "generated" in config
    if (config and config.get("version", 1) < CONFIG_VERSION) or (not current and detect_v1_outputs(project, config or {})[0]):
        raise Refusal("This repo was set up with an older version of the kit. Run `migrate` once to move "
                      "it to AGENTS.md; it shows what it will replace and asks first.")
    if not current:
        raise Refusal(f"{project.name} isn't installed yet. Run `install` first.")
    plan = build_plan(config, project)
    changes = check_and_apply(project, config, plan, force=args.force, dry_run=args.check)
    if args.check:
        drift = [p for p, (_t, c) in plan.files.items()
                 if not (project / p).exists() or normalize((project / p).read_text(encoding="utf-8")) != c]
        drift += [p for p in config["generated"] if p not in plan.files and (project / p).exists()]
        if drift:
            raise Refusal("Out of date with the kit. Run `sync`:\n  - " + "\n  - ".join(sorted(drift)))
        print("Up to date with the kit.")
        return
    print(f"\nSynced {project.name} with ai-governance-starter-kit v{kit_version()}")
    report(plan, changes)


def cmd_migrate(args) -> None:
    ignore_targets(args)
    project = resolve_project(args.output)
    config = load_config(project) or {}
    if config.get("version") == CONFIG_VERSION and "generated" in config:
        raise Refusal(f"{project.name} is already on the current layout. Use `sync` to update it.")
    old_targets = config.pop("targets", [])

    adopt: dict[str, str] = {}
    if "generated" not in config:
        verified, unverified = detect_v1_outputs(project, config)
        if unverified and not args.force:
            raise Refusal("These are in v1 kit locations, but their content doesn't match the kit's copy. "
                          "Either someone edited them, or the kit's copy changed after this repo last synced:"
                          "\n  - " + "\n  - ".join(unverified) +
                          "\n\nNothing was changed. Compare each with the kit, keep anything you need "
                          "elsewhere, then re-run with --force to replace them.")
        adopt = verified
        if args.force:
            adopt.update({p: "" for p in unverified})
        if adopt:
            print("\nv1 kit files found (verified as written by the v1 kit):")
            for line in summarize(adopt):
                print(f"  - {line}")

    config.update({
        "version": CONFIG_VERSION,
        "templates": config.get("templates", []),
        "exclude": {**empty_categories(), **config.get("exclude", {})},
        "local_dirs": {**empty_categories(), **config.get("local_dirs", {})},
        "generated": config.get("generated", {}),
    })
    plan = build_plan(config, project)
    check_and_apply(project, config, plan, force=args.force, dry_run=True, adopt=adopt)

    removing = sorted({p for p in config["generated"] if p not in plan.files} | {p for p in adopt if p not in plan.files})
    before = f"v2 layout ({', '.join(old_targets)})" if old_targets else "v1 layout"
    print(f"\nMigrating {project.name}: {before} -> AGENTS.md plus both tools' files")
    print(f"  {len(plan.files)} file(s) to write, {len(removing)} file(s) to remove.")
    for line in summarize(removing):
        print(f"  [-] {line}")
    if not args.yes:
        if not sys.stdin.isatty():
            raise Refusal("migrate needs confirmation. Re-run with --yes to proceed without a prompt.")
        if input("\nProceed? [y/N] ").strip().lower() != "y":
            raise Refusal("Cancelled. Nothing was changed.")
    changes = check_and_apply(project, config, plan, force=args.force, adopt=adopt)
    report(plan, changes)


def cmd_status(args) -> None:
    project = resolve_project(args.output)
    config = load_config(project)
    if not config or "generated" not in config:
        print(f"{project.name}: not installed. Run `install`.")
        return
    if config.get("version", 1) < CONFIG_VERSION:
        print(f"{project.name}: on an older kit layout. Run `migrate` to move it to AGENTS.md.")
    print(f"{project.name}: written by kit v{config.get('kit_version', '?')} (this kit is v{kit_version()})")
    for path, meta in sorted(config.get("generated", {}).items()):
        f = project / path
        state = "missing" if not f.exists() else (
            "ok" if fingerprint(f.read_text(encoding="utf-8")) == meta["sha256"] else "edited")
        print(f"  {state:8} {meta.get('tool', meta.get('target', '')):12} {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy AI governance assets into a project repo.")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, targets=False):
        p.add_argument("-o", "--output", help="Project repo to write into (default: current folder).")
        if targets:  # v2's tool choice: still accepted so old scripts run, then ignored
            p.add_argument("--targets", nargs="*", help=argparse.SUPPRESS)
        return p

    p = common(sub.add_parser("install", help="First-time setup: choose overlays and write the files."), True)
    p.add_argument("--templates", nargs="*", help="Domain overlays (none if given with no names).")
    p.set_defaults(func=cmd_install)
    p = common(sub.add_parser("sync", help="Re-apply the kit's current rules. Never asks questions."))
    p.add_argument("--force", action="store_true", help="Overwrite hand edits to files aigov wrote.")
    p.add_argument("--check", action="store_true", help="Change nothing; fail if files are out of date.")
    p.set_defaults(func=cmd_sync)
    p = common(sub.add_parser("migrate", help="Move a v1 or v2 repo to the current layout (AGENTS.md)."), True)
    p.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    p.add_argument("--force", action="store_true", help="Replace files even if they were edited by hand.")
    p.set_defaults(func=cmd_migrate)
    p = common(sub.add_parser("status", help="Show the state of every file aigov wrote."))
    p.set_defaults(func=cmd_status)

    args = parser.parse_args()
    try:
        args.func(args)
    except Refusal as e:
        print(f"\naigov stopped: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
