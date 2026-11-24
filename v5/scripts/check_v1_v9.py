#!/usr/bin/env python3
"""V1〜V9 の CPU 検証（FR2.2 の第 2 段階）。読み取り専用、GPU は使わない。

- V1 FIM の 0 の割合、V2 マスク比率と inf、V3 マスクの Jaccard と順位相関、V4 fp16 の丸め、
  V5 注入量、V6 系統、V7 rope_theta、V8 FIM データ、V9 語彙。
- テンソルは 1 つずつ読む（torch.load の mmap と weights_only、safetensors は safe_open）。
- FIM キャッシュは大きい（1 ファイルが数十 GB になりうる）ので、--seed、--pattern、--layers、
  --max-tensors で範囲を絞れる。実行した範囲は出力に必ず記録され、範囲を絞った仮説は「判定不能」になる。
- 実行の前に、実行するコマンドを依頼者に示して許可を得る（FR2.4）。このスクリプトは、
  --approved-by-user が無いと実行しない（--dry-run で計画だけ表示できる）。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/check_v1_v9.py --dry-run --seed 42 --pattern safety+math --max-tensors 8
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common  # noqa: F401
from _common import DEFAULT_OUT, load_prereg
from check_inputs import add_model_args, build_context

from v5lib import verify
from v5lib.hypotheses import HYPOTHESIS_IDS
from v5lib.results_io import PATTERNS, SEEDS

STAGE_IDS = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9"]


def parse_layers(text: str | None) -> set[int] | None:
    """``0,1,31`` や ``0-3`` の形の層の指定を読む。"""
    if not text:
        return None
    layers: set[int] = set()
    for part in text.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            layers.update(range(int(lo), int(hi) + 1))
        elif part:
            layers.add(int(part))
    return layers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_model_args(parser)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT / "hypotheses", help="出力先（v5/ の下だけ）")
    parser.add_argument("--seed", type=int, action="append", choices=SEEDS, help="対象の seed（複数指定可。既定は全部）")
    parser.add_argument("--pattern", action="append", choices=PATTERNS, help="対象のパターン（複数指定可。既定は全部）")
    parser.add_argument("--layers", default=None, help="対象の層（例: 0,15,31 または 0-3）。既定は全層")
    parser.add_argument("--max-tensors", type=int, default=None, help="1 回のループで見るテンソル数の上限")
    parser.add_argument("--max-models", type=int, default=None, help="V7、V9 で見る merge 済みモデル数の上限")
    parser.add_argument("--hypotheses", default=",".join(STAGE_IDS), help="実行する仮説（例: V1,V2）")
    parser.add_argument("--spearman-samples", type=int, default=1_000_000, help="V3 の順位相関の部分抽出の座標数")
    parser.add_argument("--dry-run", action="store_true", help="何も読まず、実行する計画だけを表示する")
    parser.add_argument("--approved-by-user", action="store_true", help="依頼者が、このコマンドの実行を許可した（FR2.4）")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prereg = load_prereg()
    wanted = [h.strip() for h in args.hypotheses.split(",") if h.strip()]
    unknown = [h for h in wanted if h not in STAGE_IDS]
    if unknown:
        print(f"この段階で扱わない仮説です: {unknown}（V10、V11 は check_v10_v11.py。V12 以降は実装しない）", file=sys.stderr)
        return 2
    scope = verify.Scope(
        seeds=sorted(args.seed or SEEDS), patterns=list(args.pattern or PATTERNS),
        layers=parse_layers(args.layers), max_tensors=args.max_tensors, max_models=args.max_models,
    )
    ctx = build_context(args, scope, prereg)
    ctx.spearman_samples = args.spearman_samples
    print("実行範囲:", scope.to_dict())
    print("入力の有無:")
    availability = verify.compute_availability(ctx, args.results_root)
    for need, ok in sorted(availability.items()):
        print(f"  {'あり' if ok else 'なし'}  {need}")
    if args.dry_run:
        print("--dry-run: ここまで。何も読まず、何も書いていません。")
        return 0
    if not args.approved_by_user:
        print("依頼者の許可（--approved-by-user）がないため実行しません。--dry-run で計画を確認し、許可を得てください。", file=sys.stderr)
        return 3

    results: dict[str, dict] = {}
    if "V1" in wanted:
        print("[進行] V1 を実行中...", flush=True)
        results["V1"] = verify.run_v1(ctx)
        print(f"[完了] V1: {results['V1'].get('metrics')}", flush=True)
    if "V2" in wanted or "V3" in wanted:
        print("[進行] V2/V3 を実行中...", flush=True)
        pair = verify.run_v2_v3(ctx)
        for hid in ("V2", "V3"):
            if hid in wanted:
                results[hid] = pair[hid]
                print(f"[完了] {hid}: {results[hid].get('metrics')}", flush=True)
    runners = {"V4": verify.run_v4, "V5": verify.run_v5, "V6": verify.run_v6,
               "V7": verify.run_v7, "V8": verify.run_v8, "V9": verify.run_v9}
    for hid, runner in runners.items():
        if hid in wanted:
            print(f"[進行] {hid} を実行中...", flush=True)
            results[hid] = runner(ctx)
            print(f"[完了] {hid}: {results[hid].get('metrics')}", flush=True)
    judged = verify.judge_stage([h for h in STAGE_IDS if h in wanted], results, prereg)
    try:
        written = verify.write_stage_output("v1_v9", args.out_dir, judged, results,
                                            extra={"requested": wanted, "availability": availability})
    except PermissionError as exc:
        print(f"失敗: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"書き込み: {path}")
    for hid, j in judged.items():
        print(f"{hid}: {j['verdict']}（{j['reason']}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
