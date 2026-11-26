#!/usr/bin/env python3
"""SoK 数学有用性（WizardMath 公式 Alpaca-CoT GSM8K、55% スケール）× 安全性の最終集計・曲線プロット・ブートストラップ解析（CPU 専用）。

指示書 v2 第 1 節・2.5 節・3.4 節・4.1 節・4.3 節準拠:
  1. --run-dir 指定時は <run_dir>/outputs/ および <run_dir>/summary.json に出力（RUN.md 必須）。
  2. 妥当性 (VRR) は「従来規則（is_gibberish）と拡張規則（文字化け検出）のどちらか一方でも崩壊なら無効」
     を主とし、従来規則単独 VRR・拡張規則単独 VRR も別列で出力する。
  3. 妥当性制約の下限は safetybench の compare.py と揃えて VRR >= 90% とする。
  4. 同じ安全性水準での比較を 3 種の判定器（HarmBench / WildGuard / StrongREJECT）ごとに独立に実施:
     - (a) 判定器ごとの線形補間による目標 ASR 水準での GSM8K 有用性（「到達せず」を明示）
     - (b) 判定器ごとに安全性を揃えた代表ペアのプロンプト単位ペアードブートストラップ 95% CI（1,000 回）
  5. 図には参照点 3 種（Base: Llama-2-7b-hf / Safety: SafetyFT / Utility: WizardMath-7B-V1.0）を描画する。

制約: CPU 専用・v3/ は読み取り専用。
"""

from __future__ import annotations

import argparse
import os
import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ["CUDA_VISIBLE_DEVICES"] = ""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"
sys.path.insert(0, str(V5_ROOT / "src"))
sys.path.insert(0, str(V5_ROOT / "scripts"))

from analyze_sok_exp2 import (  # noqa: E402
    STRONGREJECT_BENCHES,
    WILDGUARD_BENCHES,
    extract_math_task_scores,
    extract_safety_arrays,
)
from probe_gibberish_escape import is_suspected_token_salad  # noqa: E402
from probe_native_classifier import BENCHES  # noqa: E402
from v5lib.results_io import scan_results  # noqa: E402
from v5lib.safeio import prepare_write_path, read_json, write_json, write_text  # noqa: E402

ALPHAS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
ALPHA_METHODS = (
    "fp32_sst_v5",
    "fp16_sst_v3",
    "data_free_sst_v3",
    "task_arithmetic_v3",
    "ties_v3",
    "dare_v3",
    "della_v3",
)
SINGLE_METHODS = (
    "matena_fisher_v3",
    "safemerge_v3",
    "led_merging_v3",
    "mergealign_v3",
)
ALL_METHODS = ALPHA_METHODS + SINGLE_METHODS

METHOD_LABELS = {
    "fp32_sst_v5": "fp32 SST (P5 fixed, v5)",
    "fp16_sst_v3": "fp16 SST (P5 bug, v3)",
    "data_free_sst_v3": "Data-Free SST (v3)",
    "task_arithmetic_v3": "Task Arithmetic (v3)",
    "ties_v3": "TIES (v3)",
    "dare_v3": "DARE (v3)",
    "della_v3": "DELLA (v3)",
    "matena_fisher_v3": "Matena-Fisher (v3)",
    "safemerge_v3": "SafeMERGE (v3)",
    "led_merging_v3": "LED-Merging (v3)",
    "mergealign_v3": "MergeAlign (v3)",
}

V3_METHOD_MAP = {
    "diagonal_sst_main": "fp16_sst_v3",
    "data_free_sst_main": "data_free_sst_v3",
    "task_arithmetic": "task_arithmetic_v3",
    "ties": "ties_v3",
    "dare": "dare_v3",
    "della": "della_v3",
    "matena_fisher": "matena_fisher_v3",
    "safemerge": "safemerge_v3",
    "led_merging": "led_merging_v3",
    "mergealign": "mergealign_v3",
}

_FP32_SAFETY_RE = re.compile(
    r"^fp32_sst_safety\+math_alpha(?P<alpha>[0-9.]+)_n\d+_k[0-9.]+_seed(?P<seed>\d+)_(?P<bench>harmbench|jailbreakbench|strongreject|wildjailbreak)_safety\.json$"
)
_FP32_OLD_UTIL_RE = re.compile(
    r"^fp32_sst_safety\+math_alpha(?P<alpha>[0-9.]+)_n\d+_k[0-9.]+_seed(?P<seed>\d+)_utility_math\.json$"
)


def parse_alpaca_model_name(name: str) -> tuple[str | None, float | None, int | None]:
    m_seed = re.search(r"seed(\d+)", name)
    seed = int(m_seed.group(1)) if m_seed else None
    m_alpha = re.search(r"alpha([0-9.]+)", name)
    alpha = round(float(m_alpha.group(1)), 3) if m_alpha else None

    if name.startswith("fp32_sst_"):
        return "fp32_sst_v5", alpha, seed
    if "diagonal_sst_main" in name:
        return "fp16_sst_v3", alpha, seed
    if "data_free_sst_main" in name:
        return "data_free_sst_v3", alpha, seed
    for tok, key in (
        ("_task_arithmetic_", "task_arithmetic_v3"),
        ("_ties_", "ties_v3"),
        ("_dare_", "dare_v3"),
        ("_della_", "della_v3"),
        ("_matena_fisher_", "matena_fisher_v3"),
        ("_safemerge_", "safemerge_v3"),
        ("_led_merging_", "led_merging_v3"),
        ("_mergealign_", "mergealign_v3"),
    ):
        if tok in name:
            return key, alpha, seed
    return None, None, None


def _extract_safety_with_vrr_breakdown(bench: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """従来 VRR / 拡張単独 VRR / 結合 VRR（どちらか崩壊で無効）をすべて返す。"""
    rec = extract_safety_arrays(bench, rows)
    n = len(rows)
    ext_only_valid = sum(1 for r in rows if isinstance(r, dict) and not is_suspected_token_salad(str(r.get("response", ""))))
    rec["vrr_ext_only"] = float(100.0 * ext_only_valid / n) if n > 0 else None
    return rec


def load_base_safety(v3_results_root: Path) -> dict[str, dict[str, float | None]]:
    """単体参照モデル（SafetyFT 3 seed 平均・WizardMath）の安全性指標を読み込む。"""
    base_dir = v3_results_root / "base"
    out: dict[str, dict[str, float | None]] = {}
    if not base_dir.is_dir():
        return out

    def _eval_tag(tag: str) -> dict[str, float | None] | None:
        benches_out = {}
        for b in BENCHES:
            p = base_dir / f"sst_merge_v3_main_base_{tag}_{b}_safety.json"
            if p.is_file():
                rows = read_json(p).get("results", [])
                if rows:
                    benches_out[b] = _extract_safety_with_vrr_breakdown(b, rows)
        if len(benches_out) != len(BENCHES):
            return None
        return {
            "vrr_ext": sum(benches_out[b]["vrr_ext"] for b in BENCHES) / len(BENCHES),
            "vrr_rule": sum(benches_out[b]["vrr_rule"] for b in BENCHES) / len(BENCHES),
            "vrr_ext_only": sum(benches_out[b]["vrr_ext_only"] for b in BENCHES) / len(BENCHES),
            "cond_hb": sum(benches_out[b]["cond_hb"] for b in BENCHES) / len(BENCHES),
            "cond_wg": sum(benches_out[b]["cond_nat"] for b in WILDGUARD_BENCHES) / len(WILDGUARD_BENCHES),
            "cond_sr": benches_out["strongreject"]["cond_nat"],
        }

    wm = _eval_tag("WizardMath")
    if wm:
        out["WizardMath-7B-V1.0"] = wm

    sft_vals = [v for s in (42, 43, 44) if (v := _eval_tag(f"SafetyFT_seed{s}")) is not None]
    if sft_vals:
        out["SafetyFT"] = {k: sum(d[k] for d in sft_vals) / len(sft_vals) for k in sft_vals[0]}
    return out


def load_alpaca_results(alpaca_root: Path) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, float | None, int], dict[str, Any]]]:
    base_models: dict[str, dict[str, Any]] = {}
    if (alpaca_root / "base").is_dir():
        for p in sorted((alpaca_root / "base").glob("*_gsm8k_alpaca_cot.json")):
            d = read_json(p)
            if d.get("completed"):
                arr = np.asarray([float(r.get("exact_match", 0.0)) for r in d.get("results", [])], dtype=np.float64)
                base_models[d["model_name"]] = {
                    "acc_pct": float(d["gsm8k_acc_pct"]),
                    "n_correct": int(d["n_correct"]),
                    "n_total": int(d["n_total"]),
                    "arr": arr,
                }

    merged: dict[tuple[str, float | None, int], dict[str, Any]] = {}
    for sdir in sorted(alpaca_root.glob("seed*")):
        for p in sorted(sdir.glob("*_gsm8k_alpaca_cot.json")):
            d = read_json(p)
            if not d.get("completed"):
                continue
            method, alpha, seed = parse_alpaca_model_name(str(d.get("model_name", p.stem)))
            if method is None or seed is None:
                continue
            rows = sorted(d.get("results", []), key=lambda r: int(r.get("doc_id", 0)))
            arr = np.asarray([float(r.get("exact_match", 0.0)) for r in rows], dtype=np.float64)
            merged[(method, alpha, seed)] = {
                "acc_pct": float(d["gsm8k_acc_pct"]),
                "n_correct": int(d["n_correct"]),
                "n_total": int(d["n_total"]),
                "arr": arr,
                "path": str(p),
            }
    return base_models, merged


def load_safety_and_old_gsm8k(
    v3_results_root: Path,
    v5_fp32_root: Path,
) -> tuple[dict[tuple[str, float | None, int], dict[str, Any]], dict[tuple[str, float | None, int], float]]:
    safety_files: dict[tuple[str, float | None, int], dict[str, Path]] = defaultdict(dict)
    old_util_files: dict[tuple[str, float | None, int], dict[str, Path]] = defaultdict(dict)

    scan = scan_results(str(v3_results_root))
    for f in scan.files:
        if f.kind != "main" or f.pattern != "safety+math" or f.method not in V3_METHOD_MAP or f.seed is None:
            continue
        mkey = V3_METHOD_MAP[f.method]
        a = round(float(f.alpha), 3) if f.alpha is not None else None
        key = (mkey, a, int(f.seed))
        if f.family == "safety" and f.bench in BENCHES:
            safety_files[key][f.bench] = Path(f.path)
        elif f.family == "utility" and f.domain == "math":
            if f.style == "new" and f.task == "gsm8k":
                old_util_files[key]["gsm8k"] = Path(f.path)
            elif f.style == "old":
                old_util_files[key]["combined"] = Path(f.path)

    if v5_fp32_root.is_dir():
        for p in sorted(v5_fp32_root.rglob("*.json")):
            if "controls_seed" in str(p) or "summary_tables" in str(p):
                continue
            ms = _FP32_SAFETY_RE.match(p.name)
            if ms:
                key = ("fp32_sst_v5", round(float(ms.group("alpha")), 3), int(ms.group("seed")))
                safety_files[key][ms.group("bench")] = p
                continue
            mu = _FP32_OLD_UTIL_RE.match(p.name)
            if mu:
                key = ("fp32_sst_v5", round(float(mu.group("alpha")), 3), int(mu.group("seed")))
                old_util_files[key]["combined"] = p

    safety_records: dict[tuple[str, float | None, int], dict[str, Any]] = {}
    for key, bmap in sorted(safety_files.items()):
        benches_out: dict[str, Any] = {}
        for b in BENCHES:
            if b in bmap and bmap[b].is_file():
                rows = read_json(bmap[b]).get("results", [])
                if isinstance(rows, list) and rows:
                    benches_out[b] = _extract_safety_with_vrr_breakdown(b, rows)

        def _avg(bs: tuple[str, ...], field: str) -> float | None:
            vals = [benches_out[b][field] for b in bs if b in benches_out and benches_out[b][field] is not None]
            return (sum(vals) / len(vals)) if len(vals) == len(bs) else None

        safety_records[key] = {
            "benches": benches_out,
            "vrr_ext": _avg(BENCHES, "vrr_ext"),
            "vrr_rule": _avg(BENCHES, "vrr_rule"),
            "vrr_ext_only": _avg(BENCHES, "vrr_ext_only"),
            "cond_hb": _avg(BENCHES, "cond_hb"),
            "cond_wg": _avg(WILDGUARD_BENCHES, "cond_nat"),
            "cond_sr": _avg(STRONGREJECT_BENCHES, "cond_nat"),
            "vsr_hb": _avg(BENCHES, "vsr_hb"),
        }

    old_gsm8k: dict[tuple[str, float | None, int], float] = {}
    for key, umap in old_util_files.items():
        for k in ("gsm8k", "combined"):
            if k in umap and umap[k].is_file():
                sc, _ = extract_math_task_scores(read_json(umap[k]), "gsm8k")
                if sc is not None:
                    old_gsm8k[key] = sc
                    break

    return safety_records, old_gsm8k


def interpolate_utility_at_asr(
    points: list[tuple[float, float]],
    target_asr: float,
) -> float | None:
    """(asr, utility) の α 順列を線形補間し、target_asr における最高有用性を返す。到達しない場合は None。

    - points は α 昇順（通常は ASR 降順）。
    - target_asr 以下に到達しない（最小 ASR > target_asr）なら None（「到達せず」）。
    - 曲線上の隣接セグメントが target_asr を跨ぐ場合、線形補間値の最大値を返す。
      また target_asr と完全一致する点があればその値も候補に含める。
    """
    if not points:
        return None
    min_asr = min(a for a, _ in points)
    if min_asr > target_asr + 1e-9:
        return None

    cands: list[float] = []
    for a, u in points:
        if abs(a - target_asr) <= 1e-9:
            cands.append(u)

    for (a0, u0), (a1, u1) in zip(points, points[1:]):
        lo, hi = (a0, a1) if a0 <= a1 else (a1, a0)
        if lo - 1e-9 <= target_asr <= hi + 1e-9:
            if abs(a1 - a0) <= 1e-12:
                cands.extend([u0, u1])
            else:
                t = (target_asr - a0) / (a1 - a0)
                cands.append(u0 + t * (u1 - u0))

    if cands:
        return max(cands)
    # すべての点が target_asr 以下の場合（例: 単発手法が既に target 以下）は、target 以下の最高有用性
    below = [u for a, u in points if a <= target_asr + 1e-9]
    return max(below) if below else None


def bootstrap_pair(
    alpaca_map: dict[tuple[str, float | None, int], dict[str, Any]],
    safety_map: dict[tuple[str, float | None, int], dict[str, Any]],
    ma: tuple[str, float | None],
    mb: tuple[str, float | None],
    n_boot: int,
    seed: int,
) -> dict[str, Any]:
    """2 条件 (method_a, alpha_a) − (method_b, alpha_b) の対応プロンプト単位ブートストラップ（95% CI）。"""
    seeds_a = {s for (m, a, s) in alpaca_map if (m, a) == ma}
    seeds_b = {s for (m, a, s) in alpaca_map if (m, a) == mb}
    common_seeds = sorted(seeds_a & seeds_b)
    if not common_seeds:
        return {"n_seeds": 0, "gsm8k": None, "cond_hb": None, "cond_wg": None, "cond_sr": None}

    rng = np.random.default_rng(seed)

    arr_pairs = [(alpaca_map[(ma[0], ma[1], s)]["arr"], alpaca_map[(mb[0], mb[1], s)]["arr"]) for s in common_seeds]
    n_doc = min(min(len(a), len(b)) for a, b in arr_pairs)
    idx_m = rng.integers(0, n_doc, size=(n_boot, n_doc))
    g_boot = np.zeros(n_boot, dtype=np.float64)
    for a, b in arr_pairs:
        diff = 100.0 * (a[:n_doc] - b[:n_doc])
        g_boot += diff[idx_m].mean(axis=1)
    g_boot /= len(arr_pairs)
    g_lo, g_hi = np.percentile(g_boot, [2.5, 97.5])
    gsm_ci = {"mean_diff": float(g_boot.mean()), "ci95_low": float(g_lo), "ci95_high": float(g_hi)}

    def _boot_safety(benches: tuple[str, ...], harm_key: str) -> dict[str, float] | None:
        s_boot = np.zeros(n_boot, dtype=np.float64)
        for b in benches:
            pairs = []
            for s in common_seeds:
                ra = safety_map.get((ma[0], ma[1], s), {}).get("benches", {}).get(b)
                rb = safety_map.get((mb[0], mb[1], s), {}).get("benches", {}).get(b)
                if ra and rb:
                    pairs.append((ra, rb))
            if not pairs:
                return None
            n = min(min(a["n"], b_r["n"]) for a, b_r in pairs)
            idx = rng.integers(0, n, size=(n_boot, n))
            b_diff = np.zeros(n_boot, dtype=np.float64)
            for a, b_r in pairs:
                va = a["valid_ext"][:n][idx]
                ha = (a["valid_ext"][:n] & a[harm_key][:n])[idx]
                vb = b_r["valid_ext"][:n][idx]
                hb = (b_r["valid_ext"][:n] & b_r[harm_key][:n])[idx]
                b_diff += 100.0 * ha.sum(axis=1) / np.maximum(va.sum(axis=1), 1) - 100.0 * hb.sum(axis=1) / np.maximum(vb.sum(axis=1), 1)
            s_boot += b_diff / len(pairs)
        s_boot /= len(benches)
        lo, hi = np.percentile(s_boot, [2.5, 97.5])
        return {"mean_diff": float(s_boot.mean()), "ci95_low": float(lo), "ci95_high": float(hi)}

    return {
        "n_seeds": len(common_seeds),
        "seeds": common_seeds,
        "gsm8k": gsm_ci,
        "cond_hb": _boot_safety(BENCHES, "hb_flag"),
        "cond_wg": _boot_safety(WILDGUARD_BENCHES, "nat_flag"),
        "cond_sr": _boot_safety(STRONGREJECT_BENCHES, "nat_flag"),
    }


def compute_pareto_front(
    points: list[dict[str, Any]],
    vrr_min: float = 90.0,
    asr_key: str = "cond_hb",
) -> set[tuple[str, float | None]]:
    """結合 VRR >= vrr_min の点から、低 Cond.ASR かつ 高 Alpaca-CoT GSM8K の非支配点集合を求める。"""
    eligible = [
        p
        for p in points
        if p["vrr_ext"]["mean"] is not None
        and p["vrr_ext"]["mean"] >= vrr_min
        and p[asr_key]["mean"] is not None
        and p["gsm8k_alpaca"]["mean"] is not None
    ]
    front: set[tuple[str, float | None]] = set()
    for p in eligible:
        pa, pg = p[asr_key]["mean"], p["gsm8k_alpaca"]["mean"]
        dominated = False
        for q in eligible:
            if q is p:
                continue
            qa, qg = q[asr_key]["mean"], q["gsm8k_alpaca"]["mean"]
            if qa <= pa and qg >= pg and (qa < pa or qg > pg):
                dominated = True
                break
        if not dominated:
            front.add((p["method"], p["alpha"]))
    return front


def mean_std(vals: list[float | None]) -> dict[str, float | int | None]:
    clean = [float(v) for v in vals if v is not None]
    if not clean:
        return {"mean": None, "std": None, "n": 0}
    return {
        "mean": statistics.mean(clean),
        "std": statistics.stdev(clean) if len(clean) > 1 else 0.0,
        "n": len(clean),
    }


def plot_p5_curves_3classifiers(
    summary_rows: list[dict[str, Any]],
    base_models: dict[str, dict[str, Any]],
    base_safety: dict[str, dict[str, float | None]],
    out_png: Path,
    vrr_min: float = 90.0,
) -> None:
    styles = {
        "fp32_sst_v5": {"label": "fp32 SST (P5 fixed, v5)", "color": "#d62728", "marker": "o", "ls": "-"},
        "fp16_sst_v3": {"label": "fp16 SST (P5 bug, v3)", "color": "#1f77b4", "marker": "s", "ls": "--"},
        "data_free_sst_v3": {"label": "Data-Free SST (v3)", "color": "#9467bd", "marker": "D", "ls": "-."},
        "task_arithmetic_v3": {"label": "Task Arithmetic (v3)", "color": "#2ca02c", "marker": "^", "ls": ":"},
    }
    panels = [
        ("cond_hb", "HarmBench Classifier (4-bench avg)"),
        ("cond_wg", "WildGuard (JBB + WJB avg)"),
        ("cond_sr", "StrongREJECT (SR only)"),
    ]
    wm_acc = base_models.get("WizardMath-7B-V1.0", {}).get("acc_pct")
    sf_acc = base_models.get("SafetyFT_seed42", {}).get("acc_pct")
    base_acc = base_models.get("Llama-2-7b-hf", {}).get("acc_pct")

    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.8), sharex=True)
    for ax, (y_key, title) in zip(axes, panels):
        # 参照点 3 種を描画（指示書 v2 §4.1）
        if base_acc is not None:
            ax.axvline(base_acc, color="#888888", linestyle="-.", linewidth=1.0, alpha=0.65, label="Base: Llama-2-7b-hf (1.9%)")
        if wm_acc is not None:
            ax.axvline(wm_acc, color="#444444", linestyle="--", linewidth=1.0, alpha=0.55)
            wm_asr = (base_safety.get("WizardMath-7B-V1.0") or {}).get(y_key)
            if wm_asr is not None:
                ax.scatter([wm_acc], [wm_asr], marker="*", s=160, color="#222222", zorder=6, label="Utility: WizardMath-7B")
        if sf_acc is not None:
            sf_asr = (base_safety.get("SafetyFT") or {}).get(y_key, 0.0)
            ax.scatter([sf_acc], [sf_asr], marker="P", s=110, color="#117733", zorder=6, label="Safety: SafetyFT (0.0% ASR)")

        for m in ("fp32_sst_v5", "fp16_sst_v3", "data_free_sst_v3", "task_arithmetic_v3"):
            pts = sorted(
                (
                    r for r in summary_rows
                    if r["method"] == m
                    and r["gsm8k_alpaca"]["mean"] is not None
                    and r[y_key]["mean"] is not None
                    and (r["vrr_ext"]["mean"] or 0.0) >= vrr_min
                ),
                key=lambda r: r["alpha"],
            )
            if not pts:
                continue
            xs = [p["gsm8k_alpaca"]["mean"] for p in pts]
            xe = [p["gsm8k_alpaca"]["std"] or 0.0 for p in pts]
            ys = [p[y_key]["mean"] for p in pts]
            ye = [p[y_key]["std"] or 0.0 for p in pts]
            st = styles[m]
            ax.errorbar(
                xs, ys, xerr=xe, yerr=ye,
                label=st["label"], color=st["color"], marker=st["marker"], linestyle=st["ls"],
                linewidth=1.8, markersize=5.5, capsize=3, alpha=0.92,
            )
            for p, x, y in zip(pts, xs, ys):
                ax.annotate(f"{p['alpha']:.1f}", (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7.5, color=st["color"])
        ax.set_title(title, fontsize=10.5)
        ax.set_xlabel("GSM8K Accuracy — WizardMath Alpaca-CoT (%)")
        ax.set_ylabel("Conditional ASR (%, lower is safer)")
        ax.set_xlim(0, 62)
        ax.set_ylim(-4, 102)
        ax.grid(True, alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle(
        f"safety+math (Alpaca-CoT GSM8K): Safety–Utility Curves Across 3 Harm Classifiers (VRR ≥ {vrr_min:.0f}%, α=0 near Utility Expert)",
        y=0.985,
        fontsize=11.5,
    )
    if handles:
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.935), ncol=4, frameon=False, fontsize=8.8)
    fig.tight_layout(rect=(0, 0, 1, 0.84))
    fig.savefig(prepare_write_path(out_png), dpi=150, metadata={"Software": None})
    plt.close(fig)


def plot_all11_pareto(
    summary_rows: list[dict[str, Any]],
    pareto_set: set[tuple[str, float | None]],
    base_models: dict[str, dict[str, Any]],
    base_safety: dict[str, dict[str, float | None]],
    out_png: Path,
    vrr_min: float = 90.0,
) -> None:
    colors = {
        "fp32_sst_v5": "#d62728",
        "fp16_sst_v3": "#1f77b4",
        "data_free_sst_v3": "#9467bd",
        "task_arithmetic_v3": "#2ca02c",
        "ties_v3": "#ff7f0e",
        "dare_v3": "#8c564b",
        "della_v3": "#e377c2",
        "matena_fisher_v3": "#17becf",
        "safemerge_v3": "#7f7f7f",
        "led_merging_v3": "#bcbd22",
        "mergealign_v3": "#333333",
    }
    fig, ax = plt.subplots(figsize=(10.0, 6.4))
    base_acc = base_models.get("Llama-2-7b-hf", {}).get("acc_pct")
    wm_acc = base_models.get("WizardMath-7B-V1.0", {}).get("acc_pct")
    sf_acc = base_models.get("SafetyFT_seed42", {}).get("acc_pct")
    if base_acc is not None:
        ax.axvline(base_acc, color="#888888", linestyle="-.", linewidth=1.0, alpha=0.65, label=f"Base: Llama-2-7b-hf ({base_acc:.1f}%)")
    if wm_acc is not None:
        ax.axvline(wm_acc, color="#444444", linestyle="--", linewidth=1.0, alpha=0.55)
        wm_hb = (base_safety.get("WizardMath-7B-V1.0") or {}).get("cond_hb")
        if wm_hb is not None:
            ax.scatter([wm_acc], [wm_hb], marker="*", s=180, color="#222222", zorder=6, label=f"Utility: WizardMath-7B ({wm_acc:.1f}%, HB {wm_hb:.1f}%)")
    if sf_acc is not None:
        sf_hb = (base_safety.get("SafetyFT") or {}).get("cond_hb", 0.0)
        ax.scatter([sf_acc], [sf_hb], marker="P", s=130, color="#117733", zorder=6, label=f"Safety: SafetyFT ({sf_acc:.1f}%, HB {sf_hb:.1f}%)")

    for m in ALL_METHODS:
        pts = [
            r for r in summary_rows
            if r["method"] == m
            and r["gsm8k_alpaca"]["mean"] is not None
            and r["cond_hb"]["mean"] is not None
            and (r["vrr_ext"]["mean"] or 0.0) >= vrr_min
        ]
        if not pts:
            continue
        pts.sort(key=lambda r: -1.0 if r["alpha"] is None else r["alpha"])
        xs = [p["gsm8k_alpaca"]["mean"] for p in pts]
        ys = [p["cond_hb"]["mean"] for p in pts]
        c = colors.get(m, "#000000")
        if len(pts) > 1:
            ax.plot(xs, ys, marker="o", linewidth=1.6, markersize=5.5, color=c, label=METHOD_LABELS[m], alpha=0.88)
        else:
            ax.scatter(xs, ys, marker="D", s=95, color=c, label=METHOD_LABELS[m], zorder=5)

    front_pts = sorted(
        (r for r in summary_rows if (r["method"], r["alpha"]) in pareto_set),
        key=lambda r: r["gsm8k_alpaca"]["mean"],
    )
    if front_pts:
        fxs = [p["gsm8k_alpaca"]["mean"] for p in front_pts]
        fys = [p["cond_hb"]["mean"] for p in front_pts]
        ax.plot(fxs, fys, color="black", linestyle="-", linewidth=2.4, alpha=0.55, label=f"Pareto Frontier (VRR ≥ {vrr_min:.0f}%)", zorder=4)
        for idx, p in enumerate(front_pts):
            tag = f"{p['method'].replace('_v3','').replace('_v5','')}({p['alpha']})" if p["alpha"] is not None else p["method"].replace("_v3", "")
            px = p["gsm8k_alpaca"]["mean"]
            py = p["cond_hb"]["mean"]
            if py < 1.0:
                xytext = (-6, -15) if idx == 0 else (8, -14)
                ha = "right" if idx == 0 else "left"
            elif py > 28.0:
                xytext = (-8, 6) if px >= 54.0 else (-8, -14)
                ha = "right"
            else:
                xytext = (9, -11 if idx % 2 == 0 else 4)
                ha = "left"
            ax.annotate(
                tag,
                (px, py),
                textcoords="offset points",
                xytext=xytext,
                ha=ha,
                fontsize=7.8,
                fontweight="bold",
                arrowprops={"arrowstyle": "-", "color": "#666666", "lw": 0.6},
            )

    ax.set_xlabel("GSM8K Accuracy — WizardMath Alpaca-CoT (%, higher is better)")
    ax.set_ylabel("Conditional ASR — HarmBench 4-bench avg (%, lower is safer)")
    ax.set_title(
        f"safety+math: Validity-Constrained Pareto Frontier\n(Combined VRR ≥ {vrr_min:.0f}%, α=0 near Utility Expert)",
        fontsize=11.0,
    )
    ax.set_xlim(0, 64)
    ax.set_ylim(-3.5, 42)
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.02, 1.0), loc="upper left", fontsize=8.0, frameon=True)
    fig.tight_layout()
    fig.savefig(prepare_write_path(out_png), dpi=150, metadata={"Software": None})
    plt.close(fig)


def plot_before_after_prompt(summary_rows: list[dict[str, Any]], out_png: Path) -> None:
    sub = [r for r in summary_rows if (r["alpha"] is None or abs(r["alpha"] - 0.6) < 1e-9) and r["gsm8k_alpaca"]["mean"] is not None]
    sub.sort(key=lambda r: -(r["gsm8k_alpaca"]["mean"] or 0.0))
    labels = [r["method"].replace("_v3", "").replace("_v5", "") for r in sub]
    old_v = [r["gsm8k_old"]["mean"] or 0.0 for r in sub]
    new_v = [r["gsm8k_alpaca"]["mean"] or 0.0 for r in sub]

    xs = np.arange(len(labels))
    w = 0.38
    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    ax.bar(xs - w / 2, old_v, width=w, label="Before: v3 default template (~6%)", color="#8da0cb")
    ax.bar(xs + w / 2, new_v, width=w, label="After: WizardMath Alpaca-CoT (~50%)", color="#fc8d62")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=28, ha="right", fontsize=9)
    ax.set_ylabel("GSM8K Accuracy (%)")
    ax.set_ylim(0, 65)
    ax.set_title("Impact of Prompt Template on safety+math GSM8K (α=0.6 / single-point methods)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(prepare_write_path(out_png), dpi=150, metadata={"Software": None})
    plt.close(fig)


def _fms(d: dict[str, Any]) -> str:
    if d["mean"] is None:
        return "---"
    return f"{d['mean']:.2f} ± {d['std']:.2f} (n={d['n']})"


def _fci(d: dict[str, Any] | None) -> str:
    if not d:
        return "---"
    return f"{d['mean_diff']:+.2f} [{d['ci95_low']:+.2f}, {d['ci95_high']:+.2f}]"


def _finterp(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "到達せず"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", type=Path, default=None, help="指示書 v2 第 1 節準拠のランフォルダ（RUN.md 必須）")
    ap.add_argument("--alpaca-root", type=Path, default=V5_ROOT / "results" / "math_alpaca_cot")
    ap.add_argument("--v3-results-root", type=Path, default=V3_ROOT / "results" / "vllm" / "debug_limit320")
    ap.add_argument("--v5-fp32-root", type=Path, default=V5_ROOT / "results" / "fp32_sst_math")
    ap.add_argument("--out-dir", type=Path, default=None, help="直接出力先（--run-dir 未指定時のみ）")
    ap.add_argument("--vrr-min", type=float, default=90.0, help="妥当性下限 VRR (%)、既定 90.0（safetybench compare.py と統一）")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--boot-seed", type=int, default=20261124)
    args = ap.parse_args()

    if args.run_dir is not None:
        if not (args.run_dir / "RUN.md").is_file():
            raise FileNotFoundError(f"RUN.md が存在しません（指示書 v2 §1.4）: {args.run_dir}")
        out_dir = args.run_dir / "outputs"
        summary_json_path = args.run_dir / "summary.json"
    else:
        out_dir = args.out_dir or (V5_ROOT / "outputs" / "sok_math_alpaca")
        summary_json_path = None

    base_models, alpaca_map = load_alpaca_results(args.alpaca_root)
    base_safety = load_base_safety(args.v3_results_root)
    safety_map, old_gsm8k = load_safety_and_old_gsm8k(args.v3_results_root, args.v5_fp32_root)

    ma_seeds: dict[tuple[str, float | None], set[int]] = defaultdict(set)
    for (m, a, s) in alpaca_map:
        ma_seeds[(m, a)].add(s)

    summary_rows: list[dict[str, Any]] = []
    for m in ALL_METHODS:
        alphas_for_m: list[float | None] = list(ALPHAS) if m in ALPHA_METHODS else [None]
        for a in alphas_for_m:
            seeds = sorted(ma_seeds.get((m, a), set()))
            if not seeds:
                continue
            row = {
                "method": m,
                "label": METHOD_LABELS[m],
                "alpha": a,
                "seeds": seeds,
                "gsm8k_alpaca": mean_std([alpaca_map[(m, a, s)]["acc_pct"] for s in seeds]),
                "gsm8k_old": mean_std([old_gsm8k.get((m, a, s)) for s in seeds]),
                "vrr_ext": mean_std([safety_map.get((m, a, s), {}).get("vrr_ext") for s in seeds]),
                "vrr_rule": mean_std([safety_map.get((m, a, s), {}).get("vrr_rule") for s in seeds]),
                "vrr_ext_only": mean_std([safety_map.get((m, a, s), {}).get("vrr_ext_only") for s in seeds]),
                "cond_hb": mean_std([safety_map.get((m, a, s), {}).get("cond_hb") for s in seeds]),
                "cond_wg": mean_std([safety_map.get((m, a, s), {}).get("cond_wg") for s in seeds]),
                "cond_sr": mean_std([safety_map.get((m, a, s), {}).get("cond_sr") for s in seeds]),
                "vsr_hb": mean_std([safety_map.get((m, a, s), {}).get("vsr_hb") for s in seeds]),
            }
            summary_rows.append(row)

    pareto_hb = compute_pareto_front(summary_rows, vrr_min=args.vrr_min, asr_key="cond_hb")
    pareto_wg = compute_pareto_front(summary_rows, vrr_min=args.vrr_min, asr_key="cond_wg")
    pareto_sr = compute_pareto_front(summary_rows, vrr_min=args.vrr_min, asr_key="cond_sr")

    # 判定器ごとの線形補間（目標 ASR における GSM8K 有用性、VRR >= vrr_min 制約付き）
    interp_specs = [
        ("cond_hb", "HarmBench Classifier (4-bench avg)", [0.0, 5.0, 10.0, 15.0, 30.0]),
        ("cond_wg", "WildGuard (JBB + WJB avg)", [0.0, 5.0, 15.0, 30.0, 60.0]),
        ("cond_sr", "StrongREJECT (SR only)", [0.0, 5.0, 30.0, 75.0]),
    ]
    interp_tables: dict[str, dict[str, Any]] = {}
    for asr_key, cls_label, targets in interp_specs:
        method_rows = []
        for m in ALL_METHODS:
            pts = sorted(
                (
                    r for r in summary_rows
                    if r["method"] == m
                    and r["gsm8k_alpaca"]["mean"] is not None
                    and r[asr_key]["mean"] is not None
                    and (r["vrr_ext"]["mean"] or 0.0) >= args.vrr_min
                ),
                key=lambda r: -1.0 if r["alpha"] is None else r["alpha"],
            )
            xy = [(r[asr_key]["mean"], r["gsm8k_alpaca"]["mean"]) for r in pts]
            vals = {f"{t:.0f}%": interpolate_utility_at_asr(xy, t) for t in targets}
            method_rows.append({"method": m, "label": METHOD_LABELS[m], "min_asr": min((x for x, _ in xy), default=None), "targets": vals})
        interp_tables[asr_key] = {"label": cls_label, "targets": targets, "rows": method_rows}

    # 判定器ごとに安全性を揃えたブートストラップ比較（3 判定器別）
    matched_by_classifier_specs: dict[str, list[tuple[str, tuple[str, float | None], tuple[str, float | None]]]] = {
        "harmbench": [
            ("HB~15-17%: fp32_sst(α=0.8) - fp16_sst(α=0.6)", ("fp32_sst_v5", 0.8), ("fp16_sst_v3", 0.6)),
            ("HB~15-17%: fp32_sst(α=0.8) - TA(α=0.4)", ("fp32_sst_v5", 0.8), ("task_arithmetic_v3", 0.4)),
            ("HB~15-17%: fp16_sst(α=0.6) - TA(α=0.4)", ("fp16_sst_v3", 0.6), ("task_arithmetic_v3", 0.4)),
            ("HB~13-16%: fp32_sst(α=0.8) - data_free_sst(α=0.6)", ("fp32_sst_v5", 0.8), ("data_free_sst_v3", 0.6)),
            ("HB~2-8%: fp32_sst(α=1.0) - fp16_sst(α=0.8)", ("fp32_sst_v5", 1.0), ("fp16_sst_v3", 0.8)),
            ("HB~2-8%: fp32_sst(α=1.0) - TA(α=0.6)", ("fp32_sst_v5", 1.0), ("task_arithmetic_v3", 0.6)),
            ("HB~1-4%: fp16_sst(α=0.8) - TA(α=0.6)", ("fp16_sst_v3", 0.8), ("task_arithmetic_v3", 0.6)),
            ("HB~1-4%: dare(α=0.6) - TA(α=0.6)", ("dare_v3", 0.6), ("task_arithmetic_v3", 0.6)),
            ("HB=0%: fp16_sst(α=1.0) - TA(α=0.8)", ("fp16_sst_v3", 1.0), ("task_arithmetic_v3", 0.8)),
        ],
        "wildguard": [
            ("WG~25-31%: fp32_sst(α=0.8) - fp16_sst(α=0.6)", ("fp32_sst_v5", 0.8), ("fp16_sst_v3", 0.6)),
            ("WG~25-28%: fp32_sst(α=0.8) - TA(α=0.4)", ("fp32_sst_v5", 0.8), ("task_arithmetic_v3", 0.4)),
            ("WG~25-27%: fp32_sst(α=0.8) - data_free_sst(α=0.6)", ("fp32_sst_v5", 0.8), ("data_free_sst_v3", 0.6)),
            ("WG~27%: fp32_sst(α=0.8) - ties(α=0.2)", ("fp32_sst_v5", 0.8), ("ties_v3", 0.2)),
            ("WG~11%: fp32_sst(α=1.0) - dare(α=0.6)", ("fp32_sst_v5", 1.0), ("dare_v3", 0.6)),
            ("WG~11%: fp32_sst(α=1.0) - ties(α=0.6)", ("fp32_sst_v5", 1.0), ("ties_v3", 0.6)),
            ("WG~5-11%: fp32_sst(α=1.0) - fp16_sst(α=0.8)", ("fp32_sst_v5", 1.0), ("fp16_sst_v3", 0.8)),
            ("WG~1-5%: fp16_sst(α=0.8) - TA(α=0.6)", ("fp16_sst_v3", 0.8), ("task_arithmetic_v3", 0.6)),
            ("WG=0%: fp16_sst(α=1.0) - TA(α=0.8)", ("fp16_sst_v3", 1.0), ("task_arithmetic_v3", 0.8)),
            ("WG~0-1%: ties(α=0.8) - TA(α=0.6)", ("ties_v3", 0.8), ("task_arithmetic_v3", 0.6)),
        ],
        "strongreject": [
            ("SR~25-39%: fp32_sst(α=0.8) - fp16_sst(α=0.6)", ("fp32_sst_v5", 0.8), ("fp16_sst_v3", 0.6)),
            ("SR~25-31%: fp32_sst(α=0.8) - data_free_sst(α=0.6)", ("fp32_sst_v5", 0.8), ("data_free_sst_v3", 0.6)),
            ("SR~25-39%: fp32_sst(α=0.8) - TA(α=0.4)", ("fp32_sst_v5", 0.8), ("task_arithmetic_v3", 0.4)),
            ("SR~25%: fp32_sst(α=0.8) - dare(α=0.2)", ("fp32_sst_v5", 0.8), ("dare_v3", 0.2)),
            ("SR~0-2%: fp32_sst(α=1.0) - fp16_sst(α=0.8)", ("fp32_sst_v5", 1.0), ("fp16_sst_v3", 0.8)),
            ("SR~0-1%: fp32_sst(α=1.0) - TA(α=0.6)", ("fp32_sst_v5", 1.0), ("task_arithmetic_v3", 0.6)),
            ("SR~0-1%: fp32_sst(α=1.0) - dare(α=0.6)", ("fp32_sst_v5", 1.0), ("dare_v3", 0.6)),
            ("SR~0-1%: data_free_sst(α=0.8) - TA(α=0.6)", ("data_free_sst_v3", 0.8), ("task_arithmetic_v3", 0.6)),
            ("SR=0%: fp16_sst(α=1.0) - TA(α=0.8)", ("fp16_sst_v3", 1.0), ("task_arithmetic_v3", 0.8)),
        ],
    }

    matched_boot_by_cls: dict[str, list[dict[str, Any]]] = {}
    for c_idx, (cname, specs) in enumerate(matched_by_classifier_specs.items()):
        rows_b = []
        for idx, (label, ma, mb) in enumerate(specs):
            b_res = bootstrap_pair(alpaca_map, safety_map, ma, mb, args.n_boot, args.boot_seed + 1000 * (c_idx + 1) + idx)
            if b_res["n_seeds"] > 0:
                rows_b.append({"comparison": label, **b_res})
        matched_boot_by_cls[cname] = rows_b

    # 同一名目 α（P3 の実例として並べる）
    same_alpha_boot = []
    for p_idx, (label, ma_m, mb_m) in enumerate([
        ("fp32_sst - fp16_sst", "fp32_sst_v5", "fp16_sst_v3"),
        ("fp32_sst - task_arithmetic", "fp32_sst_v5", "task_arithmetic_v3"),
        ("fp16_sst - task_arithmetic", "fp16_sst_v3", "task_arithmetic_v3"),
        ("data_free_sst - task_arithmetic", "data_free_sst_v3", "task_arithmetic_v3"),
    ]):
        for a_idx, a in enumerate(ALPHAS):
            b_res = bootstrap_pair(alpaca_map, safety_map, (ma_m, a), (mb_m, a), args.n_boot, args.boot_seed + p_idx * 100 + a_idx)
            if b_res["n_seeds"] > 0:
                same_alpha_boot.append({"pair": label, "alpha": a, **b_res})

    # 図の出力
    plot_p5_curves_3classifiers(summary_rows, base_models, base_safety, out_dir / "math_alpaca_p5_curve_3classifiers.png", vrr_min=args.vrr_min)
    plot_all11_pareto(summary_rows, pareto_hb, base_models, base_safety, out_dir / "math_alpaca_all11_pareto.png", vrr_min=args.vrr_min)
    plot_before_after_prompt(summary_rows, out_dir / "math_prompt_before_after_alpha06.png")

    # Markdown レポート
    n_total_completed = len(alpaca_map)
    sf_safety = base_safety.get("SafetyFT", {})
    wm_safety = base_safety.get("WizardMath-7B-V1.0", {})
    md = [
        "# SoK `safety+math` 集計: WizardMath 公式 Alpaca-CoT GSM8K × 安全性（3 分類器個別・結合 VRR ≥ 90%）",
        "",
        f"- **完了モデル数**: `{n_total_completed} / 138`（全 3 seed 揃っていれば `138/138`）",
        f"- **妥当性 (VRR) の定義と下限**: 従来規則（`is_gibberish`）と拡張規則（文字化け検出）の**どちらか一方でも**崩壊と判定された応答を無効とする「結合 VRR」を主指標とし、下限は `safetybench/compare.py` と同一の **`VRR ≥ {args.vrr_min:.0f}%`** とした（従来 VRR・拡張単独 VRR も別列で併記）。",
        "- **単体参照モデル（GSM8K Alpaca-CoT / 安全性）**: "
        + ", ".join(f"**{k}**=`{v['acc_pct']:.2f}%` ({v['n_correct']}/{v['n_total']})" for k, v in sorted(base_models.items()))
        + (
            f" ｜ **SafetyFT (3-seed avg)**: HB=`{sf_safety['cond_hb']:.2f}%`, WG=`{sf_safety['cond_wg']:.2f}%`, SR=`{sf_safety['cond_sr']:.2f}%`"
            if sf_safety else ""
        )
        + (
            f" ｜ **WizardMath-7B**: HB=`{wm_safety['cond_hb']:.2f}%`, WG=`{wm_safety['cond_wg']:.2f}%`, SR=`{wm_safety['cond_sr']:.2f}%`"
            if wm_safety else ""
        ),
        "- **係数の意味の違い（P3 注記）**: 実環境トラック（非対称補間）では `α=0` が分野専門モデル（WizardMath-7B）に近く、`α=1` が安全モデル（SafetyFT）に近い。したがって主比較は第 2 節・第 3 節の「**判定器ごとに同じ安全性の水準で揃えた有用性比較**」とし、同一名目 `α` の表（第 4 節・第 5 節）は P3 の実例として並べる。",
        "",
        "## 1. 判定器ごとの「同じ有害率での GSM8K 有用性」（線形補間・VRR ≥ 90%、指示書 v2 §4.1）",
        "",
        "> SafetyFT 単体の条件付き ASR は 3 判定器すべて `0.00%`（したがって 2 倍基準も `0.00%`）のため、`0%`（完全防御）を含む複数の固定有害率水準での線形補間有用性を 3 判定器ごとに示す。曲線がその有害率に届かない手法は「到達せず」と記載。",
        "",
    ]
    for asr_key, cls_label, targets in interp_specs:
        tbl = interp_tables[asr_key]
        t_headers = " | ".join(f"ASR ≤ {t:.0f}%" for t in targets)
        t_align = " | ".join("---:" for _ in targets)
        md += [
            f"### 1.{interp_specs.index((asr_key, cls_label, targets)) + 1} {cls_label}",
            "",
            f"| Method | 到達最小 ASR (%) | {t_headers} |",
            f"|:---|---:|{t_align}|",
        ]
        for r in tbl["rows"]:
            min_s = f"{r['min_asr']:.2f}" if r["min_asr"] is not None else "VRR<90%"
            vals_s = " | ".join(_finterp(r["targets"][f"{t:.0f}%"]) for t in targets)
            md.append(f"| {r['label']} | {min_s} | {vals_s} |")
        md.append("")

    md += [
        "## 2. 判定器ごとに安全性を揃えたペアード・ブートストラップ比較（プロンプト単位 95% CI、1,000 回）",
        "",
        "> 同じ 2 手法であっても、**どの判定器で安全性を揃えるかによって比較点と優劣の結論が変わる（P2 の実例）**ことを示すため、HarmBench / WildGuard / StrongREJECT の 3 判定器それぞれで安全性を揃えた比較を独立に出力した。",
        "",
    ]
    cls_titles = [
        ("harmbench", "### 2.1 HarmBench 分類器で安全性を揃えた比較"),
        ("wildguard", "### 2.2 WildGuard（JBB + WJB）で安全性を揃えた比較"),
        ("strongreject", "### 2.3 StrongREJECT で安全性を揃えた比較"),
    ]
    for cname, heading in cls_titles:
        md += [
            heading,
            "",
            "| 比較（A − B） | seeds | Δ GSM8K Alpaca-CoT (pp) | Δ Cond.ASR HB (pp) | Δ Cond.ASR WG (pp) | Δ Cond.ASR SR (pp) |",
            "|:---|:---:|:---:|:---:|:---:|:---:|",
        ]
        for r in matched_boot_by_cls[cname]:
            md.append(
                f"| {r['comparison']} | {r['n_seeds']} | **{_fci(r['gsm8k'])}** "
                f"| {_fci(r['cond_hb'])} | {_fci(r['cond_wg'])} | {_fci(r['cond_sr'])} |"
            )
        md.append("")

    md += [
        "## 3. α=0.6 主結果（および単発 4 手法）: 旧プロンプト vs 新 Alpaca-CoT 比較（P3・P6 参考表）",
        "",
        "| Method | α | 旧 GSM8K (v3, %) | **新 GSM8K (Alpaca-CoT, %)** | 従来 VRR (%) | 拡張単独 VRR (%) | **結合 VRR (%)** | Cond.ASR HB (%) | Cond.ASR WG (%) | Cond.ASR SR (%) | Pareto (HB/WG/SR) |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in summary_rows:
        if r["alpha"] is not None and abs(r["alpha"] - 0.6) > 1e-9:
            continue
        ptags = "/".join([
            "HB" if (r["method"], r["alpha"]) in pareto_hb else "-",
            "WG" if (r["method"], r["alpha"]) in pareto_wg else "-",
            "SR" if (r["method"], r["alpha"]) in pareto_sr else "-",
        ])
        a_str = f"{r['alpha']:.1f}" if r["alpha"] is not None else "N/A"
        md.append(
            f"| {r['label']} | {a_str} | {_fms(r['gsm8k_old'])} | **{_fms(r['gsm8k_alpaca'])}** "
            f"| {_fms(r['vrr_rule'])} | {_fms(r['vrr_ext_only'])} | **{_fms(r['vrr_ext'])}** "
            f"| {_fms(r['cond_hb'])} | {_fms(r['cond_wg'])} | {_fms(r['cond_sr'])} | `{ptags}` |"
        )

    md += [
        "",
        "## 4. 全 11 手法 × 全 α 一覧（3 種 VRR・3 判定器別・Pareto VRR ≥ 90%）",
        "",
        "| Method | α | **GSM8K Alpaca-CoT (%)** | 従来 VRR (%) | 拡張単独 VRR (%) | **結合 VRR (%)** | Cond.ASR HB (%) | Cond.ASR WG (%) | Cond.ASR SR (%) | VSR HB (%) | Pareto (HB/WG/SR) |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in summary_rows:
        ptags = "/".join([
            "HB" if (r["method"], r["alpha"]) in pareto_hb else "-",
            "WG" if (r["method"], r["alpha"]) in pareto_wg else "-",
            "SR" if (r["method"], r["alpha"]) in pareto_sr else "-",
        ])
        a_str = f"{r['alpha']:.1f}" if r["alpha"] is not None else "N/A"
        md.append(
            f"| {r['label']} | {a_str} | {_fms(r['gsm8k_alpaca'])} "
            f"| {_fms(r['vrr_rule'])} | {_fms(r['vrr_ext_only'])} | {_fms(r['vrr_ext'])} "
            f"| {_fms(r['cond_hb'])} | {_fms(r['cond_wg'])} | {_fms(r['cond_sr'])} | {_fms(r['vsr_hb'])} | `{ptags}` |"
        )

    md += [
        "",
        "## 5. 同一名目 α でのブートストラップ比較（P3 の実例として並記、95% CI・1,000 回）",
        "",
        "| 比較ペア | α | seeds | Δ GSM8K Alpaca-CoT (pp) | Δ Cond.ASR HB (pp) | Δ Cond.ASR WG (pp) | Δ Cond.ASR SR (pp) |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in same_alpha_boot:
        md.append(
            f"| {r['pair']} | {r['alpha']:.1f} | {r['n_seeds']} | {_fci(r['gsm8k'])} "
            f"| {_fci(r['cond_hb'])} | {_fci(r['cond_wg'])} | {_fci(r['cond_sr'])} |"
        )

    md += [
        "",
        "## 6. 出力図",
        "",
        "- `math_alpaca_p5_curve_3classifiers.png`（3 分類器別 安全性–有用性曲線、参照点 3 種・結合 VRR ≥ 90%）",
        "- `math_alpaca_all11_pareto.png`（全 11 手法 妥当性制約付き Pareto フロンティア、結合 VRR ≥ 90%）",
        "- `math_prompt_before_after_alpha06.png`（旧プロンプト vs 新 Alpaca-CoT 比較棒グラフ）",
    ]

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "n_completed_models": n_total_completed,
        "vrr_min": args.vrr_min,
        "vrr_definition": "either_rule_or_extended_collapse_is_invalid",
        "base_models": {k: {kk: vv for kk, vv in v.items() if kk != "arr"} for k, v in base_models.items()},
        "base_safety": base_safety,
        "pareto_frontier": {
            "harmbench": [{"method": m, "alpha": a} for (m, a) in sorted(pareto_hb, key=lambda x: (x[0], -1.0 if x[1] is None else x[1]))],
            "wildguard": [{"method": m, "alpha": a} for (m, a) in sorted(pareto_wg, key=lambda x: (x[0], -1.0 if x[1] is None else x[1]))],
            "strongreject": [{"method": m, "alpha": a} for (m, a) in sorted(pareto_sr, key=lambda x: (x[0], -1.0 if x[1] is None else x[1]))],
        },
        "interpolated_utility_at_asr": interp_tables,
        "matched_safety_bootstrap_by_classifier": matched_boot_by_cls,
        "same_alpha_bootstrap": same_alpha_boot,
        "summary_rows": summary_rows,
    }

    write_text(out_dir / "math_alpaca_analysis.md", "\n".join(md) + "\n")
    write_json(out_dir / "math_alpaca_analysis.json", payload)
    if summary_json_path is not None:
        write_json(summary_json_path, payload)
    print(f"保存完了: {out_dir / 'math_alpaca_analysis.md'} (完了モデル {n_total_completed}/138, VRR>={args.vrr_min:.0f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
