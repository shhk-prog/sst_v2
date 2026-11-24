#!/usr/bin/env python3
"""SoK 実証 2: safety+math の fp32 SST-Merge 再マージスクリプト（v3 からの厳密な 1 要因修正）。

v3/scripts/mergers/sst.py との完全一致を保ちつつ、P5（数値精度によるマスク全 1 退化）の 2 点のみを修正する:
  1. v3/cache/fim/ の既存 fp32 FIM キャッシュを fp32 のまま読み込み、λ = F_h / (F_b + 1e-6) を fp32 で計算する
     （fim.py L161 の fp16 キャストを行わない）。
  2. ハードマスクを `>= threshold` ではなく `torch.topk(..., k_elements).indices` による厳密なインデックス選択にする。

v3 と完全同一に保つ事項（切り分けのため変更しない）:
  - 対象 7 モジュール（q/k/v/o/gate/up/down_proj の weight）、k = 0.20（テンソル単位）、interpolation、layer_wise = False
  - norm 層を含む対象外パラメータ: `param_util_mean + alpha * delta_safe`（Safety は LoRA のため実質 `param_util_mean`）
  - 語彙不一致の embed_tokens / lm_head（32001 vs 32000）: ベースモデルの重み `base_data.clone()`
  - 保存時の config / tokenizer: ベースモデル（meta-llama/Llama-2-7b-hf）のもの

安全装置:
  - v3/ へは一切書き込まない（読み取り専用）。出力は v5/ 配下のみ。
  - 各マージごとに全 224 対象テンソルの実効マスク比率・fp32 ゼロ率・inf 数・nan 数を `merge_metadata.json` に記録し、
    全テンソルで `|mask_ratio - k| <= 0.05` かつ `inf == 0, nan == 0` を assert で検証してから保存する。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"

BASE_MODEL_ID = "meta-llama/Llama-2-7b-hf"
UTIL_MODEL_ID = "WizardLMTeam/WizardMath-7B-V1.0"
TARGET_MODULE_KEYWORDS = ("q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj")


def is_target_weight(name: str) -> bool:
    """v3/scripts/mergers/utils.py の is_target_weight と完全同一。"""
    return "weight" in name and any(k in name for k in TARGET_MODULE_KEYWORDS)


def assert_inside_v5(path: Path) -> Path:
    resolved = path.resolve()
    v5_resolved = V5_ROOT.resolve()
    if resolved != v5_resolved and v5_resolved not in resolved.parents:
        raise PermissionError(f"v5/ の外への書き込みは禁止されています: {resolved}")
    return resolved


def load_fim_fp32(path: Path) -> dict[str, torch.Tensor]:
    if not path.is_file():
        raise FileNotFoundError(f"FIM キャッシュが見つかりません: {path}")
    obj = torch.load(str(path), map_location="cpu", mmap=True, weights_only=True)
    if not isinstance(obj, dict):
        raise ValueError(f"FIM キャッシュが辞書ではありません: {path}")
    return obj


def compute_and_verify_masks(
    fim_h: dict[str, torch.Tensor],
    fim_b: dict[str, torch.Tensor],
    k_ratio: float,
    eps: float,
    mask_tol: float,
    device: str,
    keep_masks: bool = True,
) -> tuple[dict[str, torch.Tensor], dict[str, Any]]:
    """全対象テンソルの fp32 λ とインデックス top-k マスクを計算し、退化が無いことを厳密検証する。"""
    target_names = sorted(n for n in fim_h.keys() if is_target_weight(n))
    if not target_names:
        raise RuntimeError("FIM キャッシュに対象テンソルが見つかりません")

    masks: dict[str, torch.Tensor] = {}
    per_tensor: list[dict[str, Any]] = []
    ratios: list[float] = []
    max_abs_err = 0.0
    total_inf = 0
    total_nan = 0

    with torch.no_grad():
        for name in target_names:
            if name not in fim_b:
                raise KeyError(f"benign FIM にテンソルがありません: {name}")
            fh = fim_h[name].detach().to(device=device, dtype=torch.float32)
            fb = fim_b[name].detach().to(device=device, dtype=torch.float32)
            lam = fh / (fb + eps)

            n_inf = int(torch.isinf(lam).sum().item())
            n_nan = int(torch.isnan(lam).sum().item())
            fh_zero_fp32 = float((fh == 0).float().mean().item())
            fb_zero_fp32 = float((fb == 0).float().mean().item())

            flat = lam.reshape(-1)
            numel = flat.numel()
            k_elements = max(1, int(numel * k_ratio))
            # インデックスによる厳密な上位 k 個選択（>= threshold による同値全 1 退化を防止）
            top_idx = torch.topk(flat, k_elements, largest=True, sorted=False).indices
            mask_flat = torch.zeros(numel, dtype=torch.bool, device=flat.device)
            mask_flat[top_idx] = True
            actual_ratio = float(mask_flat.float().mean().item())
            abs_err = abs(actual_ratio - k_ratio)

            if n_inf > 0 or n_nan > 0:
                raise AssertionError(f"λ に非有限値が発生しました: {name} (inf={n_inf}, nan={n_nan})")
            if abs_err > mask_tol:
                raise AssertionError(
                    f"実効マスク比率が許容範囲 {k_ratio} ± {mask_tol} を外れました: {name} -> {actual_ratio:.6f}"
                )

            total_inf += n_inf
            total_nan += n_nan
            ratios.append(actual_ratio)
            max_abs_err = max(max_abs_err, abs_err)
            per_tensor.append({
                "tensor": name,
                "numel": numel,
                "k_elements": k_elements,
                "actual_mask_ratio": actual_ratio,
                "fh_zero_frac_fp32": fh_zero_fp32,
                "fb_zero_frac_fp32": fb_zero_fp32,
                "inf_count": n_inf,
                "nan_count": n_nan,
            })
            if keep_masks:
                masks[name] = mask_flat.view_as(lam).cpu()
            del fh, fb, lam, top_idx, mask_flat

    summary = {
        "k_target": k_ratio,
        "mask_tolerance": mask_tol,
        "eps": eps,
        "mask_selection": "exact_topk_indices_fp32",
        "n_target_tensors": len(per_tensor),
        "mean_mask_ratio": sum(ratios) / len(ratios),
        "min_mask_ratio": min(ratios),
        "max_mask_ratio": max(ratios),
        "max_abs_error_from_k": max_abs_err,
        "total_inf_count": total_inf,
        "total_nan_count": total_nan,
        "all_within_tolerance": True,
        "per_tensor": per_tensor,
    }
    return masks, summary


def run_merge_for_seed(
    seed: int,
    alphas: list[float],
    k_ratio: float,
    eps: float,
    mask_tol: float,
    out_models_root: Path,
    device: str,
    verify_only: bool,
    force: bool,
) -> dict[str, Any]:
    fim_dir = V3_ROOT / "cache" / "fim"
    fim_h_path = fim_dir / f"harmful_safety_Llama2_SafetyFT_n500_seed{seed}.pt"
    fim_b_path = fim_dir / f"benign_math_Llama2_WizardMath_n500_seed{seed}.pt"
    safety_lora_path = V3_ROOT / "models" / f"safety_lora_seed{seed}"

    print(f"[seed{seed}] fp32 FIM を読み込み中: {fim_h_path.name}, {fim_b_path.name}", flush=True)
    fim_h = load_fim_fp32(fim_h_path)
    fim_b = load_fim_fp32(fim_b_path)

    masks, mask_summary = compute_and_verify_masks(
        fim_h=fim_h,
        fim_b=fim_b,
        k_ratio=k_ratio,
        eps=eps,
        mask_tol=mask_tol,
        device=device,
        keep_masks=not verify_only,
    )
    del fim_h, fim_b
    if device.startswith("cuda"):
        torch.cuda.empty_cache()

    print(
        f"[seed{seed}] マスク検証合格: n={mask_summary['n_target_tensors']}, "
        f"mean={mask_summary['mean_mask_ratio']:.6f}, "
        f"range=[{mask_summary['min_mask_ratio']:.6f}, {mask_summary['max_mask_ratio']:.6f}], "
        f"inf={mask_summary['total_inf_count']}, nan={mask_summary['total_nan_count']}",
        flush=True,
    )

    if verify_only:
        return {
            "seed": seed,
            "fim_h_path": str(fim_h_path),
            "fim_b_path": str(fim_b_path),
            "mask_summary": {k: v for k, v in mask_summary.items() if k != "per_tensor"},
            "n_target_tensors": mask_summary["n_target_tensors"],
        }

    # すでに全 α が保存済みならスキップ（--force 時を除く）
    pending_alphas = []
    for alpha in alphas:
        mdir = out_models_root / f"fp32_sst_safety+math_alpha{alpha:.1f}_n500_k{k_ratio:g}_seed{seed}"
        if not force and (mdir / "merge_metadata.json").is_file() and (
            (mdir / "model.safetensors").is_file() or (mdir / "model.safetensors.index.json").is_file()
        ):
            print(f"[seed{seed} α={alpha:.1f}] 既存マージ済みモデルをスキップ: {mdir.name}", flush=True)
        else:
            pending_alphas.append(alpha)

    if not pending_alphas:
        return {
            "seed": seed,
            "skipped": True,
            "mask_summary": {k: v for k, v in mask_summary.items() if k != "per_tensor"},
        }

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"[seed{seed}] モデル読み込み中 (base, safety_lora, WizardMath) on {device}...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, use_fast=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID, torch_dtype=torch.float16)
    base_state = {k: v.detach().cpu() for k, v in base_model.state_dict().items()}
    base_param_names = [n for n, _ in base_model.named_parameters()]

    safety_base = AutoModelForCausalLM.from_pretrained(BASE_MODEL_ID, torch_dtype=torch.float16)
    safe_model = PeftModel.from_pretrained(safety_base, str(safety_lora_path)).merge_and_unload()
    safe_state = {k: v.detach().cpu() for k, v in safe_model.state_dict().items()}
    del safety_base, safe_model

    util_model = AutoModelForCausalLM.from_pretrained(UTIL_MODEL_ID, torch_dtype=torch.float16)
    util_state = {k: v.detach().cpu() for k, v in util_model.state_dict().items()}
    del util_model

    saved_dirs: list[str] = []
    with torch.no_grad():
        for alpha in pending_alphas:
            model_name = f"fp32_sst_safety+math_alpha{alpha:.1f}_n500_k{k_ratio:g}_seed{seed}"
            out_dir = assert_inside_v5(out_models_root / model_name)
            out_dir.mkdir(parents=True, exist_ok=True)
            merged_state: dict[str, torch.Tensor] = {}
            norm_preserved_count = 0
            shape_mismatch_names: list[str] = []
            target_merged_count = 0

            for name in base_param_names:
                base_data = base_state[name].to(device=device, dtype=torch.float16)
                if name not in safe_state:
                    merged_state[name] = base_data.cpu()
                    continue

                param_safe = safe_state[name].to(device=device, dtype=torch.float16)
                delta_safe = (
                    param_safe - base_data if param_safe.shape == base_data.shape else torch.zeros_like(base_data)
                )
                param_safe_for_merge = base_data + delta_safe

                if name not in util_state or util_state[name].shape != base_data.shape:
                    # v3/scripts/mergers/sst.py L53-55 と完全同一（vocab 32001 の embed/lm_head は base_data）
                    merged_state[name] = base_data.cpu()
                    shape_mismatch_names.append(name)
                    continue

                param_util = util_state[name].to(device=device, dtype=torch.float16)
                delta_util = param_util - base_data
                param_util_mean = base_data + delta_util

                if not is_target_weight(name):
                    # v3/scripts/mergers/sst.py L103-105 と完全同一（norm 層等は param_util_mean + alpha * delta_safe）
                    merged_state[name] = (param_util_mean + alpha * delta_safe).cpu()
                    if "norm" in name.lower():
                        norm_preserved_count += 1
                    continue

                # 対象 7 モジュール: fp32 厳密 top-k マスクによる interpolation（v3 sst.py L191-192 と同式）
                mask_f16 = masks[name].to(device=device, dtype=torch.float16)
                w = torch.clamp(alpha * mask_f16, 0.0, 1.0)
                merged_state[name] = ((1.0 - w) * param_util_mean + w * param_safe_for_merge).cpu()
                target_merged_count += 1

            assert target_merged_count == mask_summary["n_target_tensors"], (
                f"対象テンソル数不一致: {target_merged_count} != {mask_summary['n_target_tensors']}"
            )
            base_model.load_state_dict(merged_state, strict=False)
            base_model.save_pretrained(str(out_dir))
            tokenizer.save_pretrained(str(out_dir))

            meta = {
                "status": "success",
                "experiment": "sok_exp2_fp32_sst_math",
                "method": "diagonal_sst_fp32_indextopk",
                "pattern": "safety+math",
                "seed": seed,
                "alpha": alpha,
                "k_ratio": k_ratio,
                "eps": eps,
                "variant": "interpolation",
                "layer_wise": False,
                "base_model": BASE_MODEL_ID,
                "util_model": UTIL_MODEL_ID,
                "safety_lora_path": str(safety_lora_path),
                "fim_h_path": str(fim_h_path),
                "fim_b_path": str(fim_b_path),
                "norm_handling": "identical_to_v3_sst_py_L103_105",
                "norm_tensors_count": norm_preserved_count,
                "shape_mismatch_tensors_kept_base": shape_mismatch_names,
                "mask_verification": mask_summary,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            with open(out_dir / "merge_metadata.json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            saved_dirs.append(str(out_dir))
            print(
                f"[seed{seed} α={alpha:.1f}] 保存完了: {out_dir.name} "
                f"(target={target_merged_count}, norm={norm_preserved_count}, "
                f"mean_mask={mask_summary['mean_mask_ratio']:.6f})",
                flush=True,
            )

    del base_model, base_state, safe_state, util_state, masks
    if device.startswith("cuda"):
        torch.cuda.empty_cache()

    return {
        "seed": seed,
        "saved_dirs": saved_dirs,
        "mask_summary": {k: v for k, v in mask_summary.items() if k != "per_tensor"},
    }


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--alphas", type=float, nargs="+", default=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ap.add_argument("--k", type=float, default=0.20)
    ap.add_argument("--eps", type=float, default=1e-6)
    ap.add_argument("--mask-tol", type=float, default=0.05)
    ap.add_argument("--out-models-root", type=Path, default=V5_ROOT / "models" / "fp32_sst_math")
    ap.add_argument("--summary-out", type=Path, default=V5_ROOT / "outputs" / "sok_exp2" / "mask_verification_summary.json")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--verify-mask-only", action="store_true", help="重みを保存せず、全対象テンソルの fp32 マスク比率のみ検証する")
    ap.add_argument("--force", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    device = ("cuda" if torch.cuda.is_available() else "cpu") if args.device == "auto" else args.device
    if args.verify_mask_only:
        device = "cpu"
    assert_inside_v5(args.out_models_root)
    assert_inside_v5(args.summary_out)

    results = []
    for seed in args.seeds:
        res = run_merge_for_seed(
            seed=seed,
            alphas=args.alphas,
            k_ratio=args.k,
            eps=args.eps,
            mask_tol=args.mask_tol,
            out_models_root=args.out_models_root,
            device=device,
            verify_only=args.verify_mask_only,
            force=args.force,
        )
        results.append(res)

    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "mode": "verify_mask_only" if args.verify_mask_only else "full_merge",
        "k_ratio": args.k,
        "mask_tol": args.mask_tol,
        "eps": args.eps,
        "alphas": args.alphas,
        "seeds": args.seeds,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    with open(args.summary_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"サマリー保存: {args.summary_out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
