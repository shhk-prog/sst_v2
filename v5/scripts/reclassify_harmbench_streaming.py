#!/usr/bin/env python3
"""SoK 実証 2 用: HarmBench 13B 再分類スクリプト（1 件ずつ逐次原子保存・途中再開対応）。

v3/scripts/tools/reclassify_safety_with_harmbench.py は全ファイル・全サンプルをまとめて推論後に
一括保存する仕様だったが、本スクリプトでは **1 件推論するごとに** 対象 JSON を原子保存（.tmp -> os.replace）する。

仕様保証:
  - 出力先が `v5/` 配下であることを事前検証（`v3/` は読み取り専用）。
  - 途中保存時は個別アイテムの `harmbench_cls_asr` / `harmbench_cls_output`（および `--update_primary_asr` 時の `asr`）
    を即座に保存し、ファイル内の全サンプルが完了した時点でのみトップレベル `harmbench_cls_asr` を確定する
    （途中で止まっても次回起動時に未処理の 1 件目から正確に再開できる）。
"""

from __future__ import annotations

import argparse
import gc
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any

import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"

sys.path.insert(0, str(V3_ROOT / "scripts" / "eval"))
from eval_safety import eval_harmbench_one, is_gibberish_or_invalid  # noqa: E402


def assert_inside_v5(path: str | Path) -> Path:
    resolved = Path(path).resolve()
    v5_resolved = V5_ROOT.resolve()
    if resolved != v5_resolved and v5_resolved not in resolved.parents:
        raise PermissionError(f"v5/ の外への書き込みは禁止されています: {resolved}")
    return resolved


def write_json_atomic(path: str | Path, obj: Any) -> None:
    p = assert_inside_v5(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(p) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, str(p))


def update_and_save_file(fpath: str, data: dict[str, Any], update_primary_asr: bool) -> bool:
    """ファイルの現時点の状態を原子保存する。全件完了していればトップレベル harmbench_cls_asr も確定し True を返す。"""
    results = data.get("results", [])
    all_done = bool(results) and all(
        isinstance(r, dict) and r.get("harmbench_cls_asr") is not None for r in results
    )
    if all_done:
        hb_asrs = [float(r["harmbench_cls_asr"]) for r in results]
        hb_mean_asr = float(sum(hb_asrs) / len(hb_asrs))
        data["harmbench_cls_asr"] = hb_mean_asr
        if update_primary_asr:
            data["asr"] = hb_mean_asr
    else:
        # 途中段階ではファイル全体のスキップ判定を誤発動させないため None のままにする
        if "harmbench_cls_asr" in data:
            data["harmbench_cls_asr"] = None

    write_json_atomic(fpath, data)
    return all_done


def clear_cuda() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results_dir", type=str, required=True)
    parser.add_argument("--file", type=str, default=None)
    parser.add_argument("--output_summary_dir", type=str, required=True)
    parser.add_argument("--batch_size", type=int, default=32, help="互換用引数（逐次 1 件保存で実行）")
    parser.add_argument("--update_primary_asr", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.file:
        files = [args.file]
    else:
        files = sorted(glob.glob(os.path.join(args.results_dir, "**", "*_safety.json"), recursive=True))

    if not files:
        print("[reclassify_harmbench_streaming] No safety files found.", flush=True)
        return 0

    for fpath in files:
        assert_inside_v5(fpath)
    assert_inside_v5(args.output_summary_dir)

    target_samples: list[dict[str, Any]] = []
    file_data_map: dict[str, dict[str, Any]] = {}
    already_evaluated_files = 0
    gibberish_skipped_count = 0

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed to load {fpath}: {e}", flush=True)
            continue

        if not isinstance(data, dict) or "results" not in data:
            continue

        results = data.get("results", [])
        file_data_map[fpath] = data

        if not args.force and data.get("harmbench_cls_asr") is not None:
            if all(isinstance(r, dict) and r.get("harmbench_cls_asr") is not None for r in results):
                already_evaluated_files += 1
                continue

        file_modified_by_gib = False
        for idx, item in enumerate(results):
            if not isinstance(item, dict):
                continue
            if not args.force and item.get("harmbench_cls_asr") is not None:
                continue

            resp = item.get("response", "")
            prompt = item.get("prompt", "")
            if is_gibberish_or_invalid(resp):
                item["harmbench_cls_asr"] = 0.0
                item["harmbench_cls_output"] = "No (Gibberish)"
                if args.update_primary_asr:
                    item["asr"] = 0.0
                gibberish_skipped_count += 1
                file_modified_by_gib = True
                continue

            target_samples.append({
                "filepath": fpath,
                "item_index": idx,
                "prompt": prompt,
                "response": resp,
            })

        if file_modified_by_gib:
            update_and_save_file(fpath, data, update_primary_asr=args.update_primary_asr)

    print(
        f"[reclassify_harmbench_streaming] スキップ済ファイル={already_evaluated_files}/{len(files)}, "
        f"gibberish即判定={gibberish_skipped_count}, 1件ずつ再分類対象={len(target_samples)}",
        flush=True,
    )

    if target_samples:
        cls_model_id = "cais/HarmBench-Llama-2-13b-cls"
        print(f"[reclassify_harmbench_streaming] Loading {cls_model_id}...", flush=True)
        cls_tokenizer = AutoTokenizer.from_pretrained(cls_model_id, use_fast=False)
        cls_model = AutoModelForCausalLM.from_pretrained(
            cls_model_id,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        cls_model.eval()

        for s in tqdm(target_samples, desc="HarmBench 1-by-1 Reclassifying"):
            fpath = s["filepath"]
            idx = s["item_index"]
            data = file_data_map[fpath]
            item = data["results"][idx]
            asr, label = eval_harmbench_one(cls_model, cls_tokenizer, s["prompt"], s["response"])
            item["harmbench_cls_asr"] = float(asr)
            item["harmbench_cls_output"] = label
            if args.update_primary_asr:
                item["asr"] = float(asr)
            # 1 件ごとに即座に原子保存
            update_and_save_file(fpath, data, update_primary_asr=args.update_primary_asr)

        del cls_model
        clear_cuda()

    # サマリー作成
    summary_records = []
    for fpath, data in file_data_map.items():
        results = data.get("results", [])
        hb_asrs = [
            float(r["harmbench_cls_asr"])
            for r in results
            if isinstance(r, dict) and r.get("harmbench_cls_asr") is not None
        ]
        if len(hb_asrs) == len(results) and results:
            if data.get("harmbench_cls_asr") is None:
                update_and_save_file(fpath, data, update_primary_asr=args.update_primary_asr)
            hb_mean_asr = float(data["harmbench_cls_asr"])
            summary_records.append({
                "filepath": fpath,
                "filename": os.path.basename(fpath),
                "model": data.get("model", "unknown"),
                "task": data.get("task", "unknown"),
                "n": len(results),
                "original_asr_pct": float(data.get("original_asr", data.get("asr", 0.0))) * 100.0,
                "current_asr_pct": float(data.get("asr", 0.0)) * 100.0,
                "harmbench_cls_asr_pct": hb_mean_asr * 100.0,
                "gibberish_ratio_pct": float(data.get("gibberish_ratio", 0.0)),
            })

    if summary_records and not args.file:
        out_dir = assert_inside_v5(args.output_summary_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json_atomic(out_dir / "safety_harmbench_reeval_summary.json", summary_records)

        lines = [
            "# HarmBench Classifier による全安全応答データ逐次再評価レポート",
            "",
            "| File / Model | Task | Total N | Original ASR (前) | Filtered ASR (後) | HarmBench Unified ASR | Gibberish Filter Ratio |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
        ]
        for rec in summary_records:
            lines.append(
                f"| `{rec['filename']}` | {rec['task']} | {rec['n']} | "
                f"{rec['original_asr_pct']:.2f}% | {rec['current_asr_pct']:.2f}% | "
                f"**{rec['harmbench_cls_asr_pct']:.2f}%** | {rec['gibberish_ratio_pct']:.2f}% |"
            )
        md_path = out_dir / "safety_harmbench_reeval_summary.md"
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[reclassify_harmbench_streaming] Summary saved: {md_path}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
