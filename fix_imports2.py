"""Batch-fix broken relative imports in sprintcycle source tree."""

import re
from pathlib import Path

BASE = Path("/Users/liangzai/CursorProjects/sprintcycle/sprintcycle")

_FLAT_REMAP = {
    "config":             "infrastructure.config",
    "evolution":          "application.evolution",
    "release_plan":       "application.release_plan",
    "persistence":        "infrastructure.persistence",
    "governance":         "governance",
    "orchestration":      "application.orchestration",
    "prompt_sources":     "domain.support_legacy.prompt_sources",
    "diagnostic":         "observability.diagnostics",
    "mq":                 "infrastructure.mq",
    "integrations":       "infrastructure.integrations",
    "platform":           "domain.platform",
    "dashboard":          "presentation",
    "versioning":         "governance.versioning",
    "services":           "application.services",
    "cache":              "infrastructure.cache",
    "hitl":               "governance.hitl",
    "intent":             "domain.intent",
    "quality_spec":       "domain.quality_spec",
    "verification":       "domain.verification",
    "execution_core":     "execution.core",
    "run_workspace":      "execution.run_workspace",
}

_TOP_PACKAGES = [
    "domain", "execution", "governance", "observability",
    "application", "infrastructure", "presentation",
]

REMAP = {}
for flat, correct in _FLAT_REMAP.items():
    REMAP[f"sprintcycle.{flat}"] = f"sprintcycle.{correct}"
    for pkg in _TOP_PACKAGES:
        REMAP[f"sprintcycle.{pkg}.{flat}"] = f"sprintcycle.{correct}"


def module_exists(module_path: str) -> bool:
    parts = module_path.split(".")
    p = BASE
    for part in parts:
        p = p / part
    if (p / "__init__.py").exists():
        return True
    p2 = BASE
    for part in parts[:-1]:
        p2 = p2 / part
    if (p2 / (parts[-1] + ".py")).exists():
        return True
    return False


def resolve_abs(file_pkg: str, dots: str, rel_path: str) -> str:
    level = len(dots)
    pkg_parts = file_pkg.split(".")
    up = level - 1
    base_parts = pkg_parts[:len(pkg_parts) - up] if up > 0 else pkg_parts
    return ".".join(base_parts + (rel_path.split(".") if rel_path else []))


def to_relative(file_pkg: str, target: str) -> str:
    fp = file_pkg.split(".")
    tp = target.split(".")
    common = sum(1 for a, b in zip(fp, tp) if a == b)
    # stop at first mismatch
    for i, (a, b) in enumerate(zip(fp, tp)):
        if a != b:
            common = i
            break
    up = len(fp) - common
    rem = ".".join(tp[common:])
    return ("." * (up + 1) + rem) if up else ("." + rem)


def remap(abs_module: str) -> str | None:
    if module_exists(abs_module):
        return None
    parts = abs_module.split(".")
    for n in range(len(parts), 0, -1):
        prefix = ".".join(parts[:n])
        if prefix in REMAP:
            suffix = parts[n:]
            new = REMAP[prefix] + ("." + ".".join(suffix) if suffix else "")
            return new
    return None


def fix_file(filepath: Path) -> list[str]:
    changes = []
    lines = filepath.read_text(encoding="utf-8").split("\n")
    new_lines = []

    parts = list(filepath.relative_to(BASE).parts)
    file_pkg = "sprintcycle." + ".".join(parts[:-1])

    for i, line in enumerate(lines):
        m = re.match(r'^(\s*)from (\.\.+)([\w.]*)\s+import\s+(.+)$', line)
        if not m:
            new_lines.append(line)
            continue

        indent, dots, rel_path, imports = m.groups()
        abs_mod = resolve_abs(file_pkg, dots, rel_path)
        new_abs = remap(abs_mod)

        if new_abs is None or new_abs == abs_mod:
            new_lines.append(line)
            continue

        new_rel = to_relative(file_pkg, new_abs)
        new_line = f"{indent}from {new_rel} import {imports}"
        new_lines.append(new_line)
        changes.append(f"  L{i+1}: {dots}{rel_path} -> {new_rel}  ({abs_mod} -> {new_abs})")

    if changes:
        filepath.write_text("\n".join(new_lines), encoding="utf-8")
    return changes


def main():
    total = 0
    for py_file in sorted(BASE.rglob("*.py")):
        if "__pycache__" in str(py_file) or py_file.name.startswith("fix_imports"):
            continue
        ch = fix_file(py_file)
        if ch:
            total += len(ch)
            print(f"\n{py_file.relative_to(BASE)}:")
            for c in ch:
                print(c)
    print(f"\n\nTotal: {total} changes")


if __name__ == "__main__":
    main()
