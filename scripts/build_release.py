#!/usr/bin/env python3
"""Build the release artifact: the skill folder (+ LICENSE and third-party notices) as a deterministic zip and a SHA-256 file.

Deterministic = same bytes for the same inputs (fixed timestamps, sorted names, normalized permissions), so anyone can
rebuild from the tagged commit and compare the checksum. Does not publish anything.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

SKILL = "agent-handoff-manager"
EXTRA = ("LICENSE", "THIRD_PARTY_NOTICES.md")
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def core_version(root: Path) -> str:
    text = (root / "skills" / SKILL / "scripts" / "handoff.py").read_text(encoding="utf-8")
    m = re.search(r"^VERSION = '([^']+)'", text, re.M)
    if not m:
        raise ValueError("VERSION not found in handoff.py")
    return m.group(1)


def build(root: Path, out: Path) -> tuple[Path, Path]:
    root = Path(root)
    skill_dir = root / "skills" / SKILL
    if not (skill_dir / "SKILL.md").is_file():
        raise FileNotFoundError(f"{skill_dir / 'SKILL.md'} not found")
    entries: list[tuple[str, Path]] = []
    for path in sorted(skill_dir.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            entries.append((f"{SKILL}/{path.relative_to(skill_dir).as_posix()}", path))
    for name in EXTRA:
        if not (root / name).is_file():
            raise FileNotFoundError(f"{name} not found")
        entries.append((name, root / name))
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f"{SKILL}-{core_version(root)}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_STORED) as z:
        for arcname, path in sorted(entries):
            info = zipfile.ZipInfo(arcname, FIXED_TIME)
            info.compress_type = zipfile.ZIP_STORED  # stored: zlib output differs between platforms, stored bytes do not
            info.external_attr = 0o644 << 16
            data = path.read_bytes().replace(b"\r\n", b"\n")  # repo is LF (INDENTS.md); normalize checkouts with autocrlf
            z.writestr(info, data)
    sums = out / "SHA256SUMS"
    sums.write_text(f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n", encoding="utf-8", newline="\n")
    return archive, sums


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist")
    args = parser.parse_args(argv)
    try:
        archive, sums = build(Path(__file__).resolve().parent.parent, Path(args.out))
    except (OSError, ValueError) as exc:
        print(f"BUILD_FAILED: {exc}", file=sys.stderr)
        return 2
    print(archive)
    print(sums.read_text(encoding="utf-8").strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
