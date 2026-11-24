#!/usr/bin/env python3
"""V1〜V11 に必要な入力の有無とサイズを、読み取りだけで一覧にする（FR2.2 の第 1 段階）。

見るもの: v3/cache/fim/*.pt、v3/data/fim/*.json、モデル（safetensors のファイル名とサイズ、config.json の有無）、
v3/models/merged、v3/results/vllm。ファイルの中身は開かない（stat とフォルダの一覧だけ）。
CPU 専用、v3/ には書かない。出力は v5/outputs/ の下。

実行場所: ワークスペース直下。
    venv_sst/bin/python v5/scripts/check_inputs.py [--hf-home <HF のキャッシュ>]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _common  # noqa: F401
from _common import DEFAULT_OUT, DEFAULT_RESULTS_ROOT, DEFAULT_V3, load_prereg

from v5lib import safeio, verify
from v5lib.hypotheses import VERDICT_UNDETERMINED


def add_model_args(parser: argparse.ArgumentParser) -> None:
    """モデルのパスに関する引数（check_inputs と check_v1_v9 で共通）。"""
    parser.add_argument("--v3-dir", type=Path, default=DEFAULT_V3, help="v3 のフォルダ（読み取り専用）")
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--fim-n", type=int, default=500, help="FIM のサンプル数 n（ファイル名の n{N}）")
    parser.add_argument("--hf-home", type=Path, default=None, help="HF のキャッシュ（base とドメインモデルの探索に使う。読み取りだけ）")
    parser.add_argument("--base-model-dir", type=Path, default=None, help="Llama-2-7b-hf のフォルダ")
    parser.add_argument("--wizardmath-dir", type=Path, default=None)
    parser.add_argument("--wizardcoder-dir", type=Path, default=None)
    parser.add_argument("--medalpaca-dir", type=Path, default=None)
    parser.add_argument("--safety-dir-template", default=None,
                        help="safety フルモデルのフォルダ（{seed} を置換）。既定は <v3>/models/temp_safety_full_seed{seed}")


def build_context(args: argparse.Namespace, scope: verify.Scope, prereg: dict) -> verify.Context:
    """引数から ``verify.Context`` を作る。指定が無いモデルは、HF のキャッシュから探す。"""
    v3 = args.v3_dir
    explicit = {"base": args.base_model_dir, "math": args.wizardmath_dir, "code": args.wizardcoder_dir,
                "medical": args.medalpaca_dir}
    resolved: dict[str, Path | None] = {}
    for key, repo_id in verify.HF_REPO_IDS.items():
        resolved[key] = explicit[key] or verify.resolve_hf_snapshot(repo_id, args.hf_home)
    params = {hid: entry.get("params", {}) for hid, entry in prereg["hypotheses"].items()}
    return verify.Context(
        fim_dir=v3 / "cache" / "fim",
        data_fim_dir=v3 / "data" / "fim",
        merged_dir=v3 / "models" / "merged",
        scope=scope,
        fim_n=args.fim_n,
        base_dir=resolved["base"],
        util_dirs={d: resolved[d] for d in verify.DOMAINS},
        safety_dir_template=args.safety_dir_template or str(v3 / "models" / "temp_safety_full_seed{seed}"),
        params=params,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_model_args(parser)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT / "inputs", help="出力先（v5/ の下だけ）")
    args = parser.parse_args(argv)
    prereg = load_prereg()
    ctx = build_context(args, verify.Scope(), prereg)
    report = verify.collect_inputs(ctx, args.results_root, prereg)
    try:
        path = safeio.write_json(args.out_dir / "inputs_report.json", report)
    except PermissionError as exc:
        print(f"失敗: {exc}", file=sys.stderr)
        return 1
    print(f"書き込み: {path}")
    for need, ok in sorted(report["availability"].items()):
        print(f"  {'あり' if ok else 'なし'}  {need}")
    if report["likely_undetermined"]:
        print(f"{VERDICT_UNDETERMINED}になる見込みの仮説（入力が足りない）:")
        for hid, missing in sorted(report["likely_undetermined"].items(), key=lambda kv: int(kv[0][1:])):
            print(f"  {hid}: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
