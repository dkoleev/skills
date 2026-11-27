#!/usr/bin/env python3
"""Deterministic documentation, ADR, glossary, and skill checks for dkoleev/skills."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VALID_ADR_STATUSES = {"accepted", "proposed", "deprecated", "superseded"}
ALLOWED_GLOSSARY_CANONICAL = {
    "status pane",
    "summary pane",
    "review gate",
    "approval gate",
}
GENERIC_SINGLE_WORDS = {
    "model",
    "turn",
    "attempt",
    "retry",
    "metadata",
    "transport",
    "supervisor",
    "multiplexer",
    "manager",
    "orchestrator",
    "implementer",
    "coder",
    "executor",
    "verifier",
    "auditor",
}
CONFLICT_RE = re.compile(r"^(<{7}|={7}|>{7})(?: |$)")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
GLOSSARY_ENTRY_RE = re.compile(r"^\*\*([^*]+)\*\*:\s*$")
ADR_FILE_RE = re.compile(r"^(\d{4})-[a-z0-9-]+\.md$")


def strip_fenced_blocks(lines: list[str]) -> list[tuple[int, str]]:
    """Return (1-based line number, line) tuples outside fenced code blocks."""
    out: list[tuple[int, str]] = []
    fence_char: str | None = None
    fence_len = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        m = re.match(r"^(`{3,}|~{3,})", stripped)
        if m:
            marker = m.group(1)
            if fence_char is None:
                fence_char = marker[0]
                fence_len = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len and stripped[len(marker):].strip() == "":
                fence_char = None
                fence_len = 0
            continue
        if fence_char is None:
            out.append((idx, line))
    return out


def github_slug(heading_text: str) -> str:
    """Approximate GitHub-flavored Markdown heading anchor slug."""
    text = heading_text.strip().lower()
    # Strip inline markdown links [label](url) -> label and backticks
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("`", "")
    # Remove punctuation except spaces and hyphens
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text).strip("-")


def extract_anchors(path: Path) -> set[str]:
    """Extract GitHub-style heading anchors from a Markdown file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for _, line in strip_fenced_blocks(lines):
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = github_slug(m.group(2))
        if not base:
            continue
        n = counts.get(base, 0)
        slug = base if n == 0 else f"{base}-{n}"
        counts[base] = n + 1
        anchors.add(slug)
    return anchors


def git_tracked_markdown() -> list[Path]:
    res = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "*.md"],
        capture_output=True,
        text=True,
        check=True,
    )
    files = [ROOT / line.strip() for line in res.stdout.splitlines() if line.strip()]
    # Include untracked new .md files in working tree as well (excluding ignored)
    res_untracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard", "*.md"],
        capture_output=True,
        text=True,
        check=True,
    )
    for line in res_untracked.stdout.splitlines():
        if line.strip():
            p = ROOT / line.strip()
            if p not in files:
                files.append(p)
    return sorted(set(p for p in files if p.exists()))


def check_conflict_markers_and_whitespace(md_files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in md_files:
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if CONFLICT_RE.match(line):
                errors.append(f"{path.relative_to(ROOT)}:{idx}: Git conflict marker found")

    res = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--check"],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        errors.append(f"git diff --check failed:\n{res.stdout}{res.stderr}".strip())
    return errors


def check_links(md_files: list[Path]) -> list[str]:
    errors: list[str] = []
    anchor_cache: dict[Path, set[str]] = {}

    for path in md_files:
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx, line in strip_fenced_blocks(lines):
            # Ignore inline code spans when scanning links
            clean_line = re.sub(r"`[^`]*`", "", line)
            for m in LINK_RE.finditer(clean_line):
                raw_target = m.group(1).strip()
                if not raw_target or raw_target.startswith(("http://", "https://", "mailto:", "file://")):
                    continue
                target_part, _, fragment = raw_target.partition("#")
                target_path = path if not target_part else (path.parent / target_part).resolve()
                try:
                    target_path.relative_to(ROOT.resolve())
                except ValueError:
                    errors.append(f"{path.relative_to(ROOT)}:{idx}: link escapes repository root: {raw_target}")
                    continue
                if not target_path.exists():
                    errors.append(f"{path.relative_to(ROOT)}:{idx}: broken relative link target: {raw_target}")
                    continue
                if fragment and target_path.is_file() and target_path.suffix.lower() == ".md":
                    if target_path not in anchor_cache:
                        anchor_cache[target_path] = extract_anchors(target_path)
                    if fragment.lower() not in anchor_cache[target_path]:
                        errors.append(
                            f"{path.relative_to(ROOT)}:{idx}: broken heading anchor '#{fragment}' in {target_path.relative_to(ROOT)}"
                        )
    return errors


def check_adrs() -> list[str]:
    errors: list[str] = []
    adr_dir = ROOT / "docs" / "adr"
    if not adr_dir.is_dir():
        return ["Missing docs/adr directory"]

    adr_files = sorted(adr_dir.glob("*.md"))
    if not adr_files:
        return ["No ADR markdown files found in docs/adr/"]

    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    numbers: list[int] = []

    for path in adr_files:
        m = ADR_FILE_RE.match(path.name)
        if not m:
            errors.append(f"{path.relative_to(ROOT)}: filename must match NNNN-<kebab-case>.md")
        else:
            numbers.append(int(m.group(1)))

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            errors.append(f"{path.relative_to(ROOT)}: missing opening YAML frontmatter '---'")
        else:
            try:
                end_idx = lines.index("---", 1)
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: unclosed YAML frontmatter")
                end_idx = 0
            if end_idx > 0:
                fm = "\n".join(lines[1:end_idx])
                status_m = re.search(r"^status:\s*(\S+)\s*$", fm, re.MULTILINE)
                if not status_m:
                    errors.append(f"{path.relative_to(ROOT)}: frontmatter missing 'status:'")
                elif status_m.group(1).lower() not in VALID_ADR_STATUSES:
                    errors.append(
                        f"{path.relative_to(ROOT)}: invalid ADR status '{status_m.group(1)}'"
                    )

        if not re.search(r"^#\s+\S+", text, re.MULTILINE):
            errors.append(f"{path.relative_to(ROOT)}: missing H1 title")
        if "## Considered Options" not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing '## Considered Options'")
        if "## Consequences" not in text:
            errors.append(f"{path.relative_to(ROOT)}: missing '## Consequences'")

        rel_link = f"docs/adr/{path.name}"
        if rel_link not in readme_text:
            errors.append(f"README.md: missing link to {rel_link}")

    if numbers and numbers != list(range(1, len(numbers) + 1)):
        errors.append(f"docs/adr/: ADR numbering must be contiguous starting at 0001, got {numbers}")

    return errors


def check_glossary(md_files: list[Path]) -> list[str]:
    errors: list[str] = []
    glossary_path = ROOT / "GLOSSARY.md"
    if not glossary_path.exists():
        return ["Missing GLOSSARY.md"]

    lines = glossary_path.read_text(encoding="utf-8").splitlines()
    avoid_phrases: list[tuple[str, str]] = []
    i = 0
    while i < len(lines):
        m = GLOSSARY_ENTRY_RE.match(lines[i].strip())
        if m:
            term = m.group(1).strip()
            if i + 2 >= len(lines):
                errors.append(f"GLOSSARY.md:{i+1}: incomplete entry for '{term}'")
                break
            defn = lines[i + 1].strip()
            avoid_line = lines[i + 2].strip()
            if not defn:
                errors.append(f"GLOSSARY.md:{i+2}: empty definition for '{term}'")
            am = re.match(r"^_Avoid_:\s*(.+)$", avoid_line)
            if not am:
                errors.append(f"GLOSSARY.md:{i+3}: expected '_Avoid_: ...' line for '{term}'")
            else:
                for raw in am.group(1).split(","):
                    phrase = raw.strip().lower()
                    if not phrase:
                        continue
                    # Only enforce unambiguous multi-word avoided synonyms that aren't another canonical term
                    if " " in phrase and phrase not in ALLOWED_GLOSSARY_CANONICAL and phrase not in GENERIC_SINGLE_WORDS:
                        avoid_phrases.append((term, phrase))
            i += 3
            continue
        i += 1

    if not avoid_phrases:
        errors.append("GLOSSARY.md: no glossary entries parsed")
        return errors

    for path in md_files:
        if path.resolve() == glossary_path.resolve():
            continue
        # Only scan README.md, docs/adr/*.md, and skills/**/*.md
        rel = path.relative_to(ROOT).as_posix()
        if not (rel == "README.md" or rel.startswith("docs/adr/") or rel.startswith("skills/")):
            continue
        for idx, line in strip_fenced_blocks(path.read_text(encoding="utf-8").splitlines()):
            # Strip inline code spans so CLI flags/filenames aren't flagged
            prose = re.sub(r"`[^`]*`", "", line)
            for term, phrase in avoid_phrases:
                if re.search(rf"(?<![\w-]){re.escape(phrase)}(?![\w-])", prose, re.IGNORECASE):
                    errors.append(
                        f"{rel}:{idx}: uses avoided glossary synonym '{phrase}' (use '{term}' instead)"
                    )

    return errors


def check_skills() -> list[str]:
    errors: list[str] = []
    skills_dir = ROOT / "skills"
    if not skills_dir.is_dir():
        return ["Missing skills/ directory"]

    skill_mds = sorted(skills_dir.glob("*/SKILL.md"))
    if not skill_mds:
        return ["No skills/*/SKILL.md files found"]

    for path in skill_mds:
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or lines[0].strip() != "---":
            errors.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
            continue
        try:
            end_idx = lines.index("---", 1)
        except ValueError:
            errors.append(f"{path.relative_to(ROOT)}: unclosed YAML frontmatter")
            continue
        fm = "\n".join(lines[1:end_idx])
        name_m = re.search(r"^name:\s*(\S+)\s*$", fm, re.MULTILINE)
        desc_m = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        if not name_m:
            errors.append(f"{path.relative_to(ROOT)}: frontmatter missing 'name:'")
        elif name_m.group(1) != path.parent.name:
            errors.append(
                f"{path.relative_to(ROOT)}: frontmatter name '{name_m.group(1)}' != dir '{path.parent.name}'"
            )
        if not desc_m or not desc_m.group(1).strip():
            errors.append(f"{path.relative_to(ROOT)}: frontmatter missing 'description:'")
    return errors


def main() -> int:
    md_files = git_tracked_markdown()
    checks = [
        ("conflict-markers & git diff --check", check_conflict_markers_and_whitespace(md_files)),
        ("markdown links & heading anchors", check_links(md_files)),
        ("ADR structure, numbering & README index", check_adrs()),
        ("GLOSSARY structure & avoided synonyms", check_glossary(md_files)),
        ("skills/*/SKILL.md frontmatter", check_skills()),
    ]
    total_errors = 0
    for label, errs in checks:
        if errs:
            print(f"[FAIL] {label} ({len(errs)}):")
            for err in errs:
                print(f"  - {err}")
            total_errors += len(errs)
        else:
            print(f"[PASS] {label}")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
