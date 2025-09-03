#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, check=False)


def repo_root() -> Path:
    p = run(["git", "rev-parse", "--show-toplevel"])
    if p.returncode != 0:
        print(p.stderr.decode() or "Not a git repository?", file=sys.stderr)
        sys.exit(2)
    return Path(p.stdout.decode().strip())


def is_tracked(path: str) -> bool:
    p = run(["git", "ls-files", "--error-unmatch", "--", path])
    return p.returncode == 0


def normalize_component(comp: str, internal_style: str) -> str:
    # Always trim leading/trailing ASCII spaces
    s = comp.strip(" ")

    if internal_style == "none":
        return s
    if internal_style == "collapse":
        out = []
        prev_space = False
        for ch in s:
            if ch == " ":
                if not prev_space:
                    out.append(" ")
                prev_space = True
            else:
                out.append(ch)
                prev_space = False
        return "".join(out)
    if internal_style == "underscore":
        return s.replace(" ", "_")
    if internal_style == "remove":
        return s.replace(" ", "")
    # Fallback to no-op if unknown (shouldn’t happen due to validation)
    return s


def normalize_path(path: str, internal_style: str) -> tuple[str | None, str | None]:
    parts = path.split("/")
    norm_parts = []
    for c in parts:
        nc = normalize_component(c, internal_style)
        if nc == "":
            return None, f"component '{c}' would become empty after normalization"
        norm_parts.append(nc)
    return "/".join(norm_parts), None


def ensure_parent(dst: str) -> None:
    Path(dst).parent.mkdir(parents=True, exist_ok=True)


def git_mv(src: str, dst: str) -> bool:
    if src == dst:
        return False
    ensure_parent(dst)
    mv = run(["git", "mv", "-f", "-k", "--", src, dst])
    if mv.returncode == 0:
        return True
    try:
        os.replace(src, dst)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"⚠️  Failed to move '{src}' -> '{dst}': {e}", file=sys.stderr)
        return False
    run(["git", "add", "--", dst])
    if is_tracked(src):
        run(["git", "rm", "--cached", "--quiet", "--force", "--", src])
    return True


def parse_args(argv: list[str]) -> tuple[str, list[str]]:
    internal_style = "none"
    files: list[str] = []
    for a in argv[1:]:
        if a.startswith("--internal-style="):
            internal_style = a.split("=", 1)[1]
            if internal_style not in ("none", "collapse", "underscore", "remove"):
                print(
                    f"Invalid --internal-style option: {internal_style}",
                    file=sys.stderr,
                )
                sys.exit(2)
        else:
            files.append(a)
    return internal_style, files


def main(argv: list[str] = None) -> int:
    if argv is None:
        argv = sys.argv
    _ = repo_root()  # validates we're in a repo
    internal_style, inputs = parse_args(argv)

    plan: list[tuple[str, str]] = []
    errors: list[str] = []
    desired_targets = {}

    for p in inputs:
        posix = Path(p).as_posix()
        dst, err = normalize_path(posix, internal_style)
        if err:
            errors.append(f"'{posix}': {err}")
            continue
        if posix == dst:
            continue
        if dst in desired_targets and desired_targets[dst] != posix:
            errors.append(
                f"Conflict: both '{desired_targets[dst]}' and '{posix}' would become '{dst}'"
            )
            continue
        desired_targets[dst] = posix
        plan.append((posix, dst))

    plan.sort(key=lambda t: t[0].count("/"), reverse=True)

    changed: list[tuple[str, str]] = []
    for src, dst in plan:
        ok = git_mv(src, dst)
        if ok:
            changed.append((src, dst))
        else:
            if src != dst:
                errors.append(f"Failed to move '{src}' -> '{dst}'")

    if changed:
        print(f"🔧 Renamed (internal-style={internal_style}):")
        for s, d in changed:
            print(f"  - '{s}' -> '{d}'")

    if errors:
        print("\n❌ Some paths could not be auto-fixed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            "\nPlease resolve conflicts or rename manually, then re-stage.",
            file=sys.stderr,
        )

    if errors:
        return 1
    if changed:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
