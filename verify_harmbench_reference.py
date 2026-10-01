#!/usr/bin/env python3
"""Compare local HarmBench constants with a pinned official source, without executing it.

Run from the sst_v2 repository:
    python verify_harmbench_reference.py --repo-root .
    python verify_harmbench_reference.py --repo-root . \
        --write-fixture v4/tests/fixtures/harmbench_official.json

An offline source may be supplied with --reference-source. In that case, the
caller must verify that the file came from the pinned revision. This utility
does not load models, run generated code, or modify implementation files.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REVISION = "37150ed7d07f1db7639c9e3cfee3288391482503"
URL = (
    "https://raw.githubusercontent.com/centerforaisafety/HarmBench/"
    + REVISION + "/eval_utils.py"
)
MAX_BYTES = 2 * 1024 * 1024
TARGETS = {
    "HARMBENCH_LLAMA2_CLS_PROMPT": "prompt",
    "HARMBENCH_LLAMA2_CLS_PROMPT_CONTEXTUAL": "prompt_contextual",
}


def find_literal(source: str, name: str, *, recursive: bool = False) -> Any:
    """Read a literal assignment via AST. Never import or execute source code."""
    tree = ast.parse(source)
    nodes = ast.walk(tree) if recursive else iter(tree.body)
    values = []
    for node in nodes:
        if isinstance(node, ast.Assign):
            matches = any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            matches = isinstance(node.target, ast.Name) and node.target.id == name
            value = node.value
        else:
            continue
        if matches:
            if value is None:
                raise ValueError("Assignment has no value: " + name)
            values.append(ast.literal_eval(value))
    if len(values) != 1:
        raise ValueError(f"Expected exactly one literal {name}; found {len(values)}")
    return values[0]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compare(label: str, actual: Any, expected: str) -> dict[str, Any]:
    if not isinstance(actual, str):
        return {"name": label, "equal": False, "error": "Local value is not a string"}
    result = {
        "name": label,
        "equal": actual == expected,
        "local_characters": len(actual),
        "official_characters": len(expected),
        "local_sha256": sha256(actual.encode("utf-8")),
        "official_sha256": sha256(expected.encode("utf-8")),
    }
    if actual != expected:
        n = min(len(actual), len(expected))
        result["first_different_character"] = next(
            (i for i in range(n) if actual[i] != expected[i]), n
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--reference-source", type=Path)
    parser.add_argument("--write-fixture", type=Path)
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()

    try:
        if args.reference_source:
            raw = args.reference_source.read_bytes()
            retrieval = "local source; pinned revision must be verified by caller"
        else:
            req = urllib.request.Request(URL, headers={"User-Agent": "HarmBench-reference-check/1"})
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(MAX_BYTES + 1)
            retrieval = "downloaded from pinned official URL"
        if len(raw) > MAX_BYTES:
            raise ValueError("Reference source exceeds the maximum allowed size")
        official = find_literal(raw.decode("utf-8"), "LLAMA2_CLS_PROMPT")
        if not isinstance(official, dict):
            raise ValueError("Official template assignment is not a dictionary")
        for key in TARGETS.values():
            if not isinstance(official.get(key), str):
                raise ValueError("Missing official template: " + key)

        root = args.repo_root.resolve()
        source_path = root / "v4/scripts/eval/eval_safety_v4.py"
        source = source_path.read_text(encoding="utf-8")
        checks = [
            compare(name, find_literal(source, name), official[key])
            for name, key in TARGETS.items()
        ]

        # This checks an existing independently written fixture too, when present.
        test_path = root / "v4/tests/test_e0_audit_gate.py"
        if test_path.exists():
            test_source = test_path.read_text(encoding="utf-8")
            try:
                fixture = find_literal(
                    test_source, "OFFICIAL_STANDARD_FIXTURE", recursive=True
                )
            except ValueError:
                checks.append({
                    "name": "OFFICIAL_STANDARD_FIXTURE",
                    "status": "NOT_CHECKED",
                    "reason": "No unique literal fixture; inspect file-based tests separately",
                })
            else:
                checks.append(compare(
                    "OFFICIAL_STANDARD_FIXTURE", fixture, official["prompt"]
                ))

        report = {
            "reference_url": URL,
            "reference_revision": REVISION,
            "reference_source_sha256": sha256(raw),
            "retrieval": retrieval,
            "local_source_path": str(source_path),
            "local_source_sha256": sha256(source.encode("utf-8")),
            "scope": "Literal templates only; no model or complete pipeline execution",
            "checks": checks,
        }

        # Fixture export is explicit and refuses to replace an existing file.
        if args.write_fixture:
            dst = args.write_fixture
            dst.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "source_url": URL,
                "source_revision": REVISION,
                "source_sha256": sha256(raw),
                "templates": {key: official[key] for key in TARGETS.values()},
            }
            with dst.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            report["fixture_written"] = str(dst.resolve())

        output = json.dumps(report, ensure_ascii=False, indent=2)
        print(output)
        if args.json_report:
            args.json_report.parent.mkdir(parents=True, exist_ok=True)
            args.json_report.write_text(output + "\n", encoding="utf-8")
        return 0 if all(c.get("equal", True) for c in checks) else 1

    except (OSError, ValueError, SyntaxError, UnicodeError, urllib.error.URLError) as exc:
        print("REFERENCE_CHECK_NOT_COMPLETED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
