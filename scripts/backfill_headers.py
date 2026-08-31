#!/usr/bin/env python3
"""Backfill missing `headers` and `header_order` in fingerprints.json from captures.

Usage:
    python scripts/backfill_headers.py \
        --registry cycletls/data/fingerprints.json \
        --capture /tmp/captured.json

For each captured fingerprint, the script computes the base name
``{browser}_{version}`` and updates every registry profile whose name starts
with that base and is missing ``headers``. This lets a single Linux capture
backfill the Windows and macOS variants of the same browser version.
"""

import argparse
import json
import sys
from pathlib import Path


def _base_name(name: str) -> str:
    """Return the platform-agnostic name prefix.

    chrome_152_0_0_0_linux -> chrome_152_0_0_0
    msedge_152_0_0_0_win   -> msedge_152_0_0_0
    chrome_android_113_0_0_0_android -> chrome_android_113_0_0_0
    """
    # The platform is always the last underscore-delimited token.
    # Only strip it when there are multiple tokens (names like firefox_linux
    # are intentionally treated as-is).
    parts = name.rsplit("_", 1)
    if (
        len(parts) == 2
        and "_" in parts[0]
        and parts[1] in ("linux", "mac", "win", "android", "windows")
    ):
        return parts[0]
    return name


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill missing headers from captured fingerprints."
    )
    parser.add_argument(
        "--registry",
        default="cycletls/data/fingerprints.json",
        help="Path to the fingerprint registry JSON.",
    )
    parser.add_argument(
        "--capture",
        required=True,
        help="Path to a captured fingerprints JSON file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes but do not write the registry.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing headers, not just backfill missing ones.",
    )
    args = parser.parse_args()

    registry_path = Path(args.registry)
    registry = _load_json(registry_path)
    capture = _load_json(Path(args.capture))

    if not isinstance(registry.get("fingerprints"), list):
        print(f"ERROR: no 'fingerprints' list in {registry_path}", file=sys.stderr)
        return 1

    if not isinstance(capture.get("fingerprints"), list):
        print(f"ERROR: no 'fingerprints' list in {args.capture}", file=sys.stderr)
        return 1

    registry_entries: list[dict] = registry["fingerprints"]
    captured_entries: list[dict] = capture["fingerprints"]

    updates: dict[str, list[str]] = {}

    for captured in captured_entries:
        captured_name = captured.get("name", "")
        if not captured_name:
            continue

        base = _base_name(captured_name)
        captured_headers = captured.get("headers")
        captured_header_order = captured.get("header_order")

        if not isinstance(captured_headers, dict) or not captured_header_order:
            print(f"[skip] {captured_name}: no headers/header_order in capture")
            continue

        for entry in registry_entries:
            entry_name = entry.get("name", "")
            if not entry_name.startswith(base + "_"):
                continue

            has_headers = "headers" in entry and isinstance(entry["headers"], dict)
            if has_headers and not args.force:
                continue

            if not has_headers:
                entry["headers"] = captured_headers

            has_header_order = "header_order" in entry and isinstance(entry["header_order"], list)
            if args.force or not has_header_order:
                entry["header_order"] = captured_header_order
            updates.setdefault(captured_name, []).append(entry_name)

    if not updates:
        print("No headers were backfilled.")
        return 0

    for captured_name, updated in sorted(updates.items()):
        print(f"[backfill] {captured_name} -> {', '.join(updated)}")

    if args.dry_run:
        print("Dry run: not writing changes.")
        return 0

    _save_json(registry_path, registry)
    print(f"\nWrote updated registry to {registry_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
