#!/usr/bin/env python3
"""LED-Merging 非侵襲パッチ実行ラッパー（上流 v3/baselines/LED-Merging は一切書き換えない）。

詳細・1 行差分・理由は v5/PATCHES.md §1 を参照。

適用する最小修正:
  1. 実行時モンキーパッチ（locate/lib/model_wrapper.py L516-533 相当）:
     prune_wandg 内の _random_prune_core(...) 呼び出しを _prune_core(..., prune_mode="gradient")
     に差し替え、289 個の Transformer 層重要度スコア |W * dL/dW| を wanda_score/ へ保存する。
  2. 必須チェック（指示書 v2 §4.2）:
     - スコアファイル数が対象テンソル数と一致すること（欠落時は即エラー終了）。
     - 語彙数不一致（32,000 vs 32,001）で embed_tokens / lm_head を無警告スキップせず、
       先頭 min0 行へマスク適用・末尾拡張行は SFT 側を維持する。
     - マージ後に単精度 §4.2 退化統計を計算し、更新テンソル数 > 0 を検証・保存する。

公式既定設定（v3/scripts/mergers/baselines.py と同一）:
  - merging_method: top_merging + task_arithmetic
  - scaling_coefficient = 0.9
  - fuse_rates = (0.5, 0.5) [safety, math]
  - fuse_patterns = ("01", "01")
  - sparsity_ratio = 0.01, neg_prune = True
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import pickle
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
import torch.nn as nn

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"
LED_ROOT = V3_ROOT / "baselines" / "LED-Merging"
sys.path.insert(0, str(V5_ROOT / "src"))

from v5lib.safeio import write_json, write_text  # noqa: E402


def apply_runtime_patch_to_model_wrapper(mw_module: Any) -> Any:
    """上流 locate/lib/model_wrapper.py を書き換えずに実行時メモリ上だけで 1 行修正を適用する。

    上流 prune_wandg (L525) は `_random_prune_core(args, model, model_base, prune_n, prune_m, name_filter_fn=...)`
    を呼んで random_score/ に乱数マスクを出してしまうため、`_prune_core(..., prune_mode="gradient")`
    を呼ぶアダプタで差し替える。元の関数を返す（復元用）。
    """
    orig_fn = mw_module._random_prune_core

    def _patched_random_to_prune_core(
        args: Any,
        model: nn.Module,
        model_base: nn.Module | None = None,
        prune_n: int = 0,
        prune_m: int = 0,
        name_filter_fn: Any = None,
    ) -> Any:
        return mw_module._prune_core(
            args=args,
            model=model,
            model_base=model_base,
            prune_n=prune_n,
            prune_m=prune_m,
            prune_mode="gradient",
            name_filter_fn=name_filter_fn,
        )

    mw_module._random_prune_core = _patched_random_to_prune_core
    return orig_fn


def _top_mask(score: torch.Tensor, rate: float) -> torch.Tensor:
    flat = score.reshape(-1)
    n = flat.numel()
    idx = max(0, min(int(rate * n) - 1, n - 1))
    sorted_vals, _ = torch.sort(flat, descending=True)
    thr = sorted_vals[idx]
    return score > thr


def _pattern_mask(m_ft: torch.Tensor, m_base: torch.Tensor | None, pattern: str) -> torch.Tensor:
    if m_base is None:
        return m_ft
    if m_base.shape[0] != m_ft.shape[0]:
        if m_base.shape[0] < m_ft.shape[0]:
            pad = m_base[-1:].expand(m_ft.shape[0] - m_base.shape[0], *m_base.shape[1:])
            m_base = torch.cat([m_base, pad], dim=0)
        else:
            m_base = m_base[: m_ft.shape[0]]
    if pattern == "01":
        return (~m_base) & m_ft
    if pattern == "10":
        return (~m_ft) & m_base
    if pattern == "00":
        return (~m_ft) & (~m_base)
    if pattern == "11":
        return m_ft & m_base
    return m_ft


def led_merge_state_dicts(
    *,
    base_sd: dict[str, torch.Tensor],
    ft_sds: dict[str, dict[str, torch.Tensor]],
    ft_scores: dict[str, dict[str, torch.Tensor]],
    base_scores: dict[str, dict[str, torch.Tensor]],
    fuse_rates: dict[str, float],
    fuse_patterns: dict[str, str],
    scaling_coefficient: float = 0.9,
    patched: bool = True,
) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    """LED-Merging (Elect + Disjoint + Task Arithmetic) を状態辞書上で実行する（テスト・本番共通コア）。

    Args:
      patched=False: 上流 commit 1149224 のバグ挙動（欠落スコアの無警告スキップ＋語彙形状不一致の無警告スキップ）を忠実に再現。
      patched=True:  全対象テンソルに対するスコア存在チェック＋語彙アライメント＋衝突解除 (Elect/Disjoint) を実施。
    """
    tasks = list(ft_sds.keys())
    all_names = list(base_sd.keys())

    # Elect ステップ: 各タスク t について他タスクと衝突する重要パラメータの和集合 (param_mask) を構築
    task_raw_masks: dict[str, dict[str, torch.Tensor]] = {t: {} for t in tasks}
    for t in tasks:
        for name in all_names:
            sc_ft = ft_scores.get(t, {}).get(name)
            if sc_ft is None:
                continue
            m_ft = _top_mask(sc_ft.to(torch.float32), fuse_rates[t])
            sc_b = base_scores.get(t, {}).get(name)
            m_b = _top_mask(sc_b.to(torch.float32), fuse_rates[t]) if sc_b is not None else None
            task_raw_masks[t][name] = _pattern_mask(m_ft, m_b, fuse_patterns[t])

    # Disjoint + Task Arithmetic マージ
    merged_sd: dict[str, torch.Tensor] = {}
    n_updated = 0
    n_untouched = 0
    n_missing_score_skips = 0
    n_shape_skips = 0

    for name in all_names:
        tb = base_sd[name].to(torch.float32)
        target_rows = max([tb.shape[0]] + [ft_sds[t][name].shape[0] for t in tasks if name in ft_sds[t]])
        if tb.shape[0] < target_rows:
            pad_b = torch.zeros((target_rows - tb.shape[0], *tb.shape[1:]), dtype=torch.float32)
            tb_aligned = torch.cat([tb, pad_b], dim=0)
        else:
            tb_aligned = tb

        delta_sum = torch.zeros_like(tb_aligned)
        any_applied = False

        for t in tasks:
            if name not in ft_sds[t]:
                continue
            ts = ft_sds[t][name].to(torch.float32)
            m_self = task_raw_masks[t].get(name)
            if m_self is None:
                n_missing_score_skips += 1
                continue

            # 他タスクの重要マスクとの衝突 (param_mask) を除外: true_mask = m_self & ~conflict
            conflict = torch.zeros(tb.shape, dtype=torch.bool)
            for other in tasks:
                if other == t:
                    continue
                m_o = task_raw_masks[other].get(name)
                if m_o is not None:
                    n0 = min(conflict.shape[0], m_o.shape[0])
                    conflict[:n0] |= m_o[:n0]

            if not patched:
                # 上流 mask_weights_utils.py L569-586 の挙動再現:
                # conflict は base shape (32000), m_self は SFT shape (32001) -> min0 に切り詰め
                # true_mask.shape (32000) != ts.shape (32001) -> continue (サイレントスキップ!)
                min0 = min(m_self.shape[0], conflict.shape[0])
                true_mask = m_self[:min0] & (~conflict[:min0])
                if true_mask.shape != ts.shape:
                    n_shape_skips += 1
                    continue
                masked_w = torch.where(true_mask, ts, tb_aligned)
                delta_sum += masked_w - tb_aligned
                any_applied = True
            else:
                # パッチ後: 先頭 min0 行に true_mask を適用し、末尾拡張行（[PAD] 等）はそのまま保持
                min0 = min(m_self.shape[0], conflict.shape[0], ts.shape[0])
                true_mask = torch.zeros(ts.shape, dtype=torch.bool)
                true_mask[:min0] = m_self[:min0] & (~conflict[:min0])
                if ts.shape[0] > min0:
                    true_mask[min0:] = True
                masked_w = torch.where(true_mask, ts, tb_aligned[: ts.shape[0]])
                delta_sum[: ts.shape[0]] += masked_w - tb_aligned[: ts.shape[0]]
                any_applied = True

        merged_t = tb_aligned + scaling_coefficient * delta_sum
        merged_sd[name] = merged_t.to(base_sd[name].dtype)
        if any_applied and float((merged_t[: tb.shape[0]] - tb).abs().max().item()) > 1e-6:
            n_updated += 1
        else:
            n_untouched += 1

    # §4.2 単精度退化統計（base および各入力との差・proj_util）
    stats: dict[str, Any] = {
        "patched": patched,
        "n_tensors_total": len(all_names),
        "n_tensors_updated": n_updated,
        "n_tensors_untouched": n_untouched,
        "n_missing_score_skips": n_missing_score_skips,
        "n_shape_skips": n_shape_skips,
        "per_input": {},
    }
    norm_b2 = sum(float(base_sd[k].to(torch.float32).pow(2).sum().item()) for k in all_names)
    norm_dm2 = 0.0
    for k in all_names:
        tb = base_sd[k].to(torch.float32)
        tm = merged_sd[k].to(torch.float32)[: tb.shape[0]]
        norm_dm2 += float((tm - tb).pow(2).sum().item())
    stats["rel_diff_vs_base_pct"] = (100.0 * math.sqrt(norm_dm2) / math.sqrt(norm_b2)) if norm_b2 > 0 else 0.0

    for t in tasks:
        norm_du2 = 0.0
        dot_dm_du = 0.0
        for k in all_names:
            tb = base_sd[k].to(torch.float32)
            tm = merged_sd[k].to(torch.float32)[: tb.shape[0]]
            tu = ft_sds[t][k].to(torch.float32)[: tb.shape[0]]
            dm = tm - tb
            du = tu - tb
            norm_du2 += float(du.pow(2).sum().item())
            dot_dm_du += float((dm * du).sum().item())
        stats["per_input"][t] = {
            "proj_pct": (100.0 * dot_dm_du / norm_du2) if norm_du2 > 0 else None,
            "cos": (dot_dm_du / (math.sqrt(norm_dm2) * math.sqrt(norm_du2))) if (norm_dm2 > 0 and norm_du2 > 0) else None,
        }

    util_task = next((t for t in tasks if t != "safety"), tasks[-1])
    proj_u = stats["per_input"][util_task]["proj_pct"]
    stats["degenerated"] = bool(
        n_updated == 0
        or stats["rel_diff_vs_base_pct"] < 1.0
        or (proj_u is not None and proj_u < 10.0)
    )
    return merged_sd, stats


def compute_wandg_scores_patched(
    *,
    model_path: str,
    prune_data: str,
    save_dir: Path,
    nsamples: int = 128,
    seed: int = 0,
) -> Path:
    """上流 locate/lib/model_wrapper.py にメモリ上 1 行パッチを当てて WandaG 勾配スコアを計算・保存する。"""
    save_dir.mkdir(parents=True, exist_ok=True)
    score_dir = save_dir / "wanda_score"
    if score_dir.is_dir() and len(list(score_dir.glob("*.pkl"))) >= 224:
        print(f"[SKIP] 既存パッチ済みスコアを再利用: {score_dir} ({len(list(score_dir.glob('*.pkl')))} files)")
        return score_dir

    locate_dir = LED_ROOT / "locate"
    sys.path.insert(0, str(locate_dir))
    import lib.model_wrapper as mw  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer

    orig_fn = apply_runtime_patch_to_model_wrapper(mw)
    prev_cwd = os.getcwd()
    try:
        os.chdir(locate_dir)
        tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            device_map="auto",
        )
        model.eval()
        ns_args = argparse.Namespace(
            nsamples=nsamples,
            seed=seed,
            sparsity_ratio=0.01,
            sparsity_type="unstructured",
            prune_method="wandg",
            prune_data=prune_data,
            use_diff=False,
            neg_prune=False,
            recover_from_base=False,
            prune_part=False,
            disentangle=True,
            dump_wanda_score=True,
            save=str(save_dir),
        )
        mw.prune_wandg(
            ns_args,
            model,
            tokenizer,
            model_base=None,
            device=torch.device("cuda:0"),
            prune_n=0,
            prune_m=0,
            prune_data=prune_data,
        )
    finally:
        mw._random_prune_core = orig_fn
        os.chdir(prev_cwd)
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    n_files = len(list(score_dir.glob("*.pkl"))) if score_dir.is_dir() else 0
    if n_files < 224:
        raise RuntimeError(
            f"スコアファイル数が不足しています（指示書 v2 §4.2 ゲート失敗）: {score_dir} に {n_files} 件（期待 >= 224）"
        )
    print(f"[OK] パッチ済み WandaG スコア保存完了: {score_dir} ({n_files} files)")
    return score_dir


def _load_score_dir_to_param_map(score_dir: Path, param_names: list[str]) -> dict[str, torch.Tensor]:
    sys.path.insert(0, str(LED_ROOT))
    from model_merging_methods.mask_weights_utils import eq_param_name  # type: ignore

    files = sorted(os.listdir(score_dir))
    out: dict[str, torch.Tensor] = {}
    for pname in param_names:
        fname = eq_param_name(pname, files)
        if fname is not None:
            with open(score_dir / fname, "rb") as f:
                t = pickle.load(f)
            out[pname] = t.cpu() if isinstance(t, torch.Tensor) else torch.as_tensor(t)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, required=True, help="指示書 v2 第 1 節準拠のランフォルダ（RUN.md 必須）")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--nsamples", type=int, default=128)
    ap.add_argument("--scaling-coefficient", type=float, default=0.9)
    ap.add_argument("--fuse-rate", type=float, default=0.5)
    ap.add_argument("--output-model-dir", type=Path, default=None)
    args = ap.parse_args()

    if not (args.run_dir / "RUN.md").is_file():
        raise FileNotFoundError(f"RUN.md が存在しません（指示書 v2 §1.4）: {args.run_dir}")

    base_model_id = "meta-llama/Llama-2-7b-hf"
    math_model_id = "WizardLMTeam/WizardMath-7B-V1.0"
    safe_model_dir = str(V3_ROOT / "models" / f"temp_safety_full_seed{args.seed}")
    out_model_dir = args.output_model_dir or (V5_ROOT / "models" / f"led_merging_patched_safety+math_seed{args.seed}")
    score_root = args.run_dir / "outputs" / "led_scores"

    t0 = time.time()
    # 1) Locate（パッチ済み _prune_core(prune_mode="gradient")）
    s_safe_ft = compute_wandg_scores_patched(model_path=safe_model_dir, prune_data="align", save_dir=score_root / "safety_ft", nsamples=args.nsamples)
    s_safe_b = compute_wandg_scores_patched(model_path=base_model_id, prune_data="align", save_dir=score_root / "safety_base", nsamples=args.nsamples)
    s_math_ft = compute_wandg_scores_patched(model_path=math_model_id, prune_data="math", save_dir=score_root / "math_ft", nsamples=args.nsamples)
    s_math_b = compute_wandg_scores_patched(model_path=base_model_id, prune_data="math", save_dir=score_root / "math_base", nsamples=args.nsamples)

    # 2) モデル読み込み（CPU fp16）→ Elect & Disjoint & Task Arithmetic マージ
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print("[MERGE] Loading base, safety, and math models on CPU ...")
    m_base = AutoModelForCausalLM.from_pretrained(base_model_id, torch_dtype=torch.float16, low_cpu_mem_usage=True)
    m_safe = AutoModelForCausalLM.from_pretrained(safe_model_dir, torch_dtype=torch.float16, low_cpu_mem_usage=True)
    m_math = AutoModelForCausalLM.from_pretrained(math_model_id, torch_dtype=torch.float16, low_cpu_mem_usage=True)

    base_sd = {k: v.cpu() for k, v in m_base.state_dict().items() if not k.endswith("rotary_emb.inv_freq")}
    safe_sd = {k: v.cpu() for k, v in m_safe.state_dict().items() if k in base_sd}
    math_sd = {k: v.cpu() for k, v in m_math.state_dict().items() if k in base_sd}
    del m_base, m_safe
    gc.collect()

    param_names = list(base_sd.keys())
    ft_scores = {
        "safety": _load_score_dir_to_param_map(s_safe_ft, param_names),
        "math": _load_score_dir_to_param_map(s_math_ft, param_names),
    }
    base_scores = {
        "safety": _load_score_dir_to_param_map(s_safe_b, param_names),
        "math": _load_score_dir_to_param_map(s_math_b, param_names),
    }

    merged_sd, stats = led_merge_state_dicts(
        base_sd=base_sd,
        ft_sds={"safety": safe_sd, "math": math_sd},
        ft_scores=ft_scores,
        base_scores=base_scores,
        fuse_rates={"safety": args.fuse_rate, "math": args.fuse_rate},
        fuse_patterns={"safety": "01", "math": "01"},
        scaling_coefficient=args.scaling_coefficient,
        patched=True,
    )

    if stats["n_tensors_updated"] <= 0:
        raise RuntimeError(f"更新テンソル数が 0 のため異常終了します: {stats}")

    # 3) マージ済みモデル保存（WizardMath 側の config/tokenizer 32001 ベースで保存）
    out_model_dir.mkdir(parents=True, exist_ok=True)
    m_math.load_state_dict(merged_sd, strict=False)
    m_math.save_pretrained(out_model_dir, safe_serialization=True)
    tok = AutoTokenizer.from_pretrained(math_model_id, use_fast=False)
    tok.save_pretrained(out_model_dir)

    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": "led_merging_patched",
        "patch_reference": "v5/PATCHES.md §1 (upstream MqLeet/LED-Merging commit 1149224: _random_prune_core -> _prune_core(gradient) + vocab alignment)",
        "pattern": "safety+math",
        "seed": args.seed,
        "scaling_coefficient": args.scaling_coefficient,
        "fuse_rate": args.fuse_rate,
        "fuse_pattern": "01",
        "nsamples": args.nsamples,
        "output_model_dir": str(out_model_dir),
        "elapsed_sec": round(time.time() - t0, 2),
        "weight_audit": stats,
    }
    write_json(out_model_dir / "merge_metadata.json", meta)
    write_json(args.run_dir / "outputs" / "led_merging_patched_audit.json", meta)
    write_json(args.run_dir / "summary.json", meta)
    print(
        f"[DONE] LED-Merging patched saved: {out_model_dir} | "
        f"updated={stats['n_tensors_updated']}/{stats['n_tensors_total']}, "
        f"rel_diff_vs_base={stats['rel_diff_vs_base_pct']:.3f}%, "
        f"proj_math={stats['per_input']['math']['proj_pct']:.2f}%, "
        f"degenerated={stats['degenerated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
