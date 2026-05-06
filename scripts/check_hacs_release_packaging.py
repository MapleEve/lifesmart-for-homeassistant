#!/usr/bin/env python3
"""Guard against HACS release packaging regressions.

This repository should be consumed by HACS from the GitHub source archive.
Do not re-enable hacs.json zip_release/filename or publish a custom
lifesmart.zip release asset unless a separate validated packaging flow is
introduced. The v2026.05.2 incident combined those settings with a custom zip
asset and made HACS install the integration under a nested path.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
HACS_JSON = ROOT / "hacs.json"
MANIFEST_JSON = ROOT / "custom_components" / "lifesmart" / "manifest.json"
WORKFLOW_DIR = ROOT / ".github" / "workflows"
RELEASE_WORKFLOW_NAMES = {"release.yml", "release.yaml"}
FORBIDDEN_HACS_KEYS = {"zip_release", "filename"}
FORBIDDEN_RELEASE_ASSET_PATTERNS = {
    "lifesmart.zip": re.compile(r"lifesmart\.zip", re.IGNORECASE),
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        fail(f"required file is missing: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"{path.relative_to(ROOT)} is not valid JSON: {exc}")


def iter_release_workflows() -> Iterable[Path]:
    if not WORKFLOW_DIR.is_dir():
        fail("required workflow directory is missing: .github/workflows")

    for workflow in sorted(WORKFLOW_DIR.iterdir()):
        if workflow.name in RELEASE_WORKFLOW_NAMES:
            yield workflow


def check_hacs_json() -> None:
    hacs = load_json(HACS_JSON)

    forbidden = sorted(FORBIDDEN_HACS_KEYS.intersection(hacs))
    if forbidden:
        fail(
            "hacs.json must not enable custom zip releases; remove forbidden "
            f"key(s): {', '.join(forbidden)}"
        )

    if hacs.get("content_in_root") is not False:
        fail("hacs.json must keep content_in_root=false for custom_components/lifesmart layout")

    if "homeassistant" not in hacs:
        fail("hacs.json must declare the minimum supported Home Assistant version")


def check_manifest_layout() -> None:
    manifest = load_json(MANIFEST_JSON)

    if manifest.get("domain") != "lifesmart":
        fail("custom_components/lifesmart/manifest.json must declare domain=lifesmart")

    if not (ROOT / "custom_components" / "lifesmart" / "__init__.py").is_file():
        fail("custom_components/lifesmart/__init__.py is missing")


def check_release_workflows() -> None:
    workflows = list(iter_release_workflows())
    if not workflows:
        fail("release workflow is missing; keep the disabled legacy release guard in place")

    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN_RELEASE_ASSET_PATTERNS.items():
            if pattern.search(text):
                fail(
                    f"{workflow.relative_to(ROOT)} must not publish or reference "
                    f"a custom {label} release asset"
                )


def main() -> None:
    check_hacs_json()
    check_manifest_layout()
    check_release_workflows()
    print("HACS release packaging guardrail passed")


if __name__ == "__main__":
    main()
