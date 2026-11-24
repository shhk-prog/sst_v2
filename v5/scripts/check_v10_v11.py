#!/usr/bin/env python3
"""V10、V11 の再集計（FR2.2 の第 3 段階）。結果ファイル（JSON）の名前と中身だけを読む。CPU 専用。

- V10: ablation 結果のファイル名から、k0.05、k0.1、additive、layerwise_* の評価済みの条件を一覧する。
- V11: Step 5 の比較ロジックで、SST と task_arithmetic を、観測済みの点の Pareto 支配と
  近傍比較で比べる（VRR の下限は事前登録の値。感度分析の下限の結果も添える）。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/check_v10_v11.py
出力: v5/outputs/hypotheses/v10_v11.json / .md / .manifest.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common  # noqa: F401
from _common import DEFAULT_OUT, DEFAULT_RESULTS_ROOT, load_prereg

from v5lib import compare, metrics, results_io, verify
from v5lib.hypotheses import neighborhood_tolerance, vrr_floors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT, help="結果ルート（読み取り専用）")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT / "hypotheses", help="出力先（v5/ の下だけ）")
    args = parser.parse_args(argv)
    prereg = load_prereg()
    primary, sensitivity = vrr_floors(prereg)
    rule = prereg["comparison"]["harm_rule_primary"]
    try:
        scan = results_io.scan_results(args.results_root)
        errors: list[dict[str, str]] = []
        records = metrics.load_point_records(scan.files, errors)
        points = compare.points_from_records(records, rule)
        results = {
            "V10": verify.run_v10(scan.files, prereg),
            "V11": verify.run_v11(points, sensitivity, neighborhood_tolerance(prereg), primary),
        }
        results["V11"]["inputs"] = sorted(
            {p for r in records if r["kind"] == "main" and r["method"] in ("diagonal_sst_main", "task_arithmetic")
             for p in list(r["sources"]["safety"].values()) + [i["path"] for i in r["sources"]["tasks"].values()]}
        )
        judged = verify.judge_stage(["V10", "V11"], results, prereg)
        written = verify.write_stage_output("v10_v11", args.out_dir, judged, results,
                                            extra={"load_errors": errors, "unparsed_names": scan.unparsed})
    except (FileNotFoundError, PermissionError, ValueError) as exc:
        print(f"失敗: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"書き込み: {path}")
    for hid, j in judged.items():
        print(f"{hid}: {j['verdict']}（{j['reason']}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
