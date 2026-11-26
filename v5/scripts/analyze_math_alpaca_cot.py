#!/usr/bin/env python3
"""SoK 数学有用性（WizardMath 公式 Alpaca-CoT GSM8K、55% スケール）× 安全性の最終集計・曲線プロット・ブートストラップ解析（CPU 専用）。

機能:
  1. v5/results/math_alpaca_cot/ 配下の全 11 手法（fp32 SST + v3 10 手法）× 全 α × 完了済み seed（最大 3 seed）と
     単体参照モデル（WizardMath-7B-V1.0 / SafetyFT_seed42 / Llama-2-7b-hf）の GSM8K Alpaca-CoT 正答率を集計。
  2. 同一条件の安全性結果（v5/results/fp32_sst_math/ および v3/results/vllm/debug_limit320/）と結合し、
     拡張妥当性判定（P1 修正）＋3 種の有害分類器個別（HarmBench / WildGuard / StrongREJECT）を並べる。
  3. 修正前（v3 の旧プロンプト GSM8K: ~6%）vs 修正後（Alpaca-CoT GSM8K: ~55%）の比較表を作成。
  4. 妥当性制約付き Pareto フロンティア（拡張 VRR ≥ 80%、低 Cond.ASR HB、高 Alpaca-CoT GSM8K）を抽出。
  5. プロンプト単位ブートストラップ（1,000 回、固定 seed=20261124）で 95% CI を算出:
     - 同一名目 α での比較（fp32 SST vs fp16 SST vs TA vs Data-Free SST）
     - **同等の安全性水準を揃えた比較**（例: fp32 SST α=0.8 vs fp16 SST α=0.6 vs TA α=0.4、
       および fp32 SST α=1.0 vs fp16 SST α=0.8 vs TA α=0.6）
  6. 論文用図 3 枚を出力:
     - `math_alpaca_p5_curve_3classifiers.png`: 3 分類器別 安全性–有用性曲線（fp32 SST / fp16 SST / Data-Free SST / TA）
     - `math_alpaca_all11_pareto.png`: 全 11 手法の安全性–有用性散布図＋Pareto フロンティア
     - `math_prompt_before_after_alpha06.png`: 旧プロンプト（6%）vs 新 Alpaca-CoT（55%）の比較棒グラフ

制約: CPU 専用・v3/ は読み取り専用。出力は v5/outputs/sok_math_alpaca/ のみ。
"""

from __future__ import annotations

import argparse
import json
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
    WILDGUARD_BENCHES,
    STRONGREJECT_BENCHES,
    extract_math_task_scores,
    extract_safety_arrays,
)
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
                    benches_out[b] = extract_safety_arrays(b, rows)

        def _avg(bs: tuple[str, ...], field: str) -> float | None:
            vals = [benches_out[b][field] for b in bs if b in benches_out and benches_out[b][field] is not None]
            return (sum(vals) / len(vals)) if len(vals) == len(bs) else None

        safety_records[key] = {
            "benches": benches_out,
            "vrr_ext": _avg(BENCHES, "vrr_ext"),
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

    # 1. GSM8K Alpaca-CoT (320 docs)
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

    # 2. Safety Cond.ASR (HB / WG / SR)
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


def compute_pareto_front(points: list[dict[str, Any]], vrr_min: float = 80.0) -> set[tuple[str, float | None]]:
    """拡張 VRR >= vrr_min の点から、低 Cond.ASR HB かつ 高 Alpaca-CoT GSM8K の非支配点集合を求める。"""
    eligible = [
        p
        for p in points
        if p["vrr_ext"]["mean"] is not None
        and p["vrr_ext"]["mean"] >= vrr_min
        and p["cond_hb"]["mean"] is not None
        and p["gsm8k_alpaca"]["mean"] is not None
    ]
    front: set[tuple[str, float | None]] = set()
    for p in eligible:
        pa, pg = p["cond_hb"]["mean"], p["gsm8k_alpaca"]["mean"]
        dominated = False
        for q in eligible:
            if q is p:
                continue
            qa, qg = q["cond_hb"]["mean"], q["gsm8k_alpaca"]["mean"]
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
    out_png: Path,
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

    fig, axes = plt.subplots(1, 3, figsize=(16.0, 5.5), sharex=True)
    for ax, (y_key, title) in zip(axes, panels):
        if wm_acc is not None:
            ax.axvline(wm_acc, color="#555555", linestyle="--", linewidth=1.0, alpha=0.6)
        if sf_acc is not None:
            ax.axvline(sf_acc, color="#999999", linestyle=":", linewidth=1.0, alpha=0.6)

        for m in ("fp32_sst_v5", "fp16_sst_v3", "data_free_sst_v3", "task_arithmetic_v3"):
            pts = sorted(
                (r for r in summary_rows if r["method"] == m and r["gsm8k_alpaca"]["mean"] is not None and r[y_key]["mean"] is not None),
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
                linewidth=1.8, markersize=6, capsize=3, alpha=0.92,
            )
            for p, x, y in zip(pts, xs, ys):
                ax.annotate(f"{p['alpha']:.1f}", (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7.5, color=st["color"])
        ax.set_title(title, fontsize=10.5)
        ax.set_xlabel("GSM8K Accuracy — WizardMath Alpaca-CoT (%)")
        ax.set_ylabel("Conditional ASR (%, lower is safer)")
        ax.set_xlim(0, 62)
        ax.set_ylim(-3, 102)
        ax.grid(True, alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.suptitle("safety+math (Alpaca-CoT GSM8K): Safety–Utility Curves Across 3 Harm Classifiers", y=0.985, fontsize=12.0)
    if handles:
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.93), ncol=4, frameon=False, fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.87))
    fig.savefig(prepare_write_path(out_png), dpi=150, metadata={"Software": None})
    plt.close(fig)


def plot_all11_pareto(
    summary_rows: list[dict[str, Any]],
    pareto_set: set[tuple[str, float | None]],
    base_models: dict[str, dict[str, Any]],
    out_png: Path,
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
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    wm_acc = base_models.get("WizardMath-7B-V1.0", {}).get("acc_pct")
    if wm_acc is not None:
        ax.axvline(wm_acc, color="#444444", linestyle="--", linewidth=1.0, alpha=0.6, label=f"WizardMath-7B standalone ({wm_acc:.1f}%)")

    for m in ALL_METHODS:
        pts = [
            r for r in summary_rows
            if r["method"] == m
            and r["gsm8k_alpaca"]["mean"] is not None
            and r["cond_hb"]["mean"] is not None
            and (r["vrr_ext"]["mean"] or 0.0) >= 80.0
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
            ax.scatter(xs, ys, marker="*", s=140, color=c, label=METHOD_LABELS[m], zorder=5)

    # Pareto フロンティアを強調線で結ぶ
    front_pts = sorted(
        (r for r in summary_rows if (r["method"], r["alpha"]) in pareto_set),
        key=lambda r: r["gsm8k_alpaca"]["mean"],
    )
    if front_pts:
        fxs = [p["gsm8k_alpaca"]["mean"] for p in front_pts]
        fys = [p["cond_hb"]["mean"] for p in front_pts]
        ax.plot(fxs, fys, color="black", linestyle="-", linewidth=2.4, alpha=0.55, label="Pareto Frontier (VRR ≥ 80%)", zorder=4)
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
                # 中間域の密集を避けるため交互に上下オフセット
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
    ax.set_title("safety+math: All 11 Methods Validity-Constrained Pareto Frontier (VRR ≥ 80%)")
    ax.set_xlim(0, 64)
    ax.set_ylim(-3.5, 42)
    ax.grid(True, alpha=0.3)
    ax.legend(bbox_to_anchor=(1.02, 1.0), loc="upper left", fontsize=8.5, frameon=True)
    fig.tight_layout()
    fig.savefig(prepare_write_path(out_png), dpi=150, metadata={"Software": None})
    plt.close(fig)


def plot_before_after_prompt(summary_rows: list[dict[str, Any]], out_png: Path) -> None:
    """α=0.6 主結果における旧プロンプト GSM8K (v3) vs 新 Alpaca-CoT GSM8K (v5) 比較棒グラフ。"""
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--alpaca-root", type=Path, default=V5_ROOT / "results" / "math_alpaca_cot")
    ap.add_argument("--v3-results-root", type=Path, default=V3_ROOT / "results" / "vllm" / "debug_limit320")
    ap.add_argument("--v5-fp32-root", type=Path, default=V5_ROOT / "results" / "fp32_sst_math")
    ap.add_argument("--out-dir", type=Path, default=V5_ROOT / "outputs" / "sok_math_alpaca")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--boot-seed", type=int, default=20261124)
    args = ap.parse_args()

    base_models, alpaca_map = load_alpaca_results(args.alpaca_root)
    safety_map, old_gsm8k = load_safety_and_old_gsm8k(args.v3_results_root, args.v5_fp32_root)

    # (method, alpha) ごとに seed 集計
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
                "cond_hb": mean_std([safety_map.get((m, a, s), {}).get("cond_hb") for s in seeds]),
                "cond_wg": mean_std([safety_map.get((m, a, s), {}).get("cond_wg") for s in seeds]),
                "cond_sr": mean_std([safety_map.get((m, a, s), {}).get("cond_sr") for s in seeds]),
                "vsr_hb": mean_std([safety_map.get((m, a, s), {}).get("vsr_hb") for s in seeds]),
            }
            summary_rows.append(row)

    pareto_set = compute_pareto_front(summary_rows, vrr_min=80.0)

    # 1) 同一 α ブートストラップ
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

    # 2) 同等安全性水準（P3 曲線比較）ブートストラップ
    matched_safety_specs = [
        ("HB~15-17%: fp32_sst(α=0.8) - fp16_sst(α=0.6)", ("fp32_sst_v5", 0.8), ("fp16_sst_v3", 0.6)),
        ("HB~15-17%: fp32_sst(α=0.8) - TA(α=0.4)", ("fp32_sst_v5", 0.8), ("task_arithmetic_v3", 0.4)),
        ("HB~15-17%: fp16_sst(α=0.6) - TA(α=0.4)", ("fp16_sst_v3", 0.6), ("task_arithmetic_v3", 0.4)),
        ("HB~2-8%: fp32_sst(α=1.0) - fp16_sst(α=0.8)", ("fp32_sst_v5", 1.0), ("fp16_sst_v3", 0.8)),
        ("HB~2-8%: fp32_sst(α=1.0) - TA(α=0.6)", ("fp32_sst_v5", 1.0), ("task_arithmetic_v3", 0.6)),
        ("HB~2-3%: fp16_sst(α=0.8) - TA(α=0.6)", ("fp16_sst_v3", 0.8), ("task_arithmetic_v3", 0.6)),
        ("HB=0%: fp16_sst(α=1.0) - TA(α=0.8)", ("fp16_sst_v3", 1.0), ("task_arithmetic_v3", 0.8)),
    ]
    matched_safety_boot = []
    for idx, (label, ma, mb) in enumerate(matched_safety_specs):
        b_res = bootstrap_pair(alpaca_map, safety_map, ma, mb, args.n_boot, args.boot_seed + 900 + idx)
        if b_res["n_seeds"] > 0:
            matched_safety_boot.append({"comparison": label, **b_res})

    # 図の出力
    out_dir = args.out_dir
    plot_p5_curves_3classifiers(summary_rows, base_models, out_dir / "math_alpaca_p5_curve_3classifiers.png")
    plot_all11_pareto(summary_rows, pareto_set, base_models, out_dir / "math_alpaca_all11_pareto.png")
    plot_before_after_prompt(summary_rows, out_dir / "math_prompt_before_after_alpha06.png")

    # Markdown レポート
    n_total_completed = len(alpaca_map)
    md = [
        "# SoK `safety+math` 最終集計: WizardMath 公式 Alpaca-CoT GSM8K × 安全性（3 分類器・拡張妥当性）",
        "",
        f"- 完了モデル数: `{n_total_completed} / 138`（全 3 seed 揃っていれば 138/138）",
        "- 単体参照モデル（GSM8K Alpaca-CoT）: "
        + ", ".join(f"**{k}**=`{v['acc_pct']:.2f}%` ({v['n_correct']}/{v['n_total']})" for k, v in sorted(base_models.items())),
        "",
        "## 1. α=0.6 主結果（および単発 4 手法）: 旧プロンプト vs 新 Alpaca-CoT 比較",
        "",
        "| Method | α | 旧 GSM8K (v3, %) | **新 GSM8K (Alpaca-CoT, %)** | 拡張 VRR (%) | Cond.ASR HB (%) | Cond.ASR WG (%) | Cond.ASR SR (%) | Pareto |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in summary_rows:
        if r["alpha"] is not None and abs(r["alpha"] - 0.6) > 1e-9:
            continue
        is_p = "★" if (r["method"], r["alpha"]) in pareto_set else ""
        a_str = f"{r['alpha']:.1f}" if r["alpha"] is not None else "N/A"
        md.append(
            f"| {r['label']} | {a_str} | {_fms(r['gsm8k_old'])} | **{_fms(r['gsm8k_alpaca'])}** "
            f"| {_fms(r['vrr_ext'])} | {_fms(r['cond_hb'])} | {_fms(r['cond_wg'])} | {_fms(r['cond_sr'])} | {is_p} |"
        )

    md += [
        "",
        "## 2. 全 11 手法 × 全 α 一覧（拡張妥当性・3 分類器別）",
        "",
        "| Method | α | **GSM8K Alpaca-CoT (%)** | 拡張 VRR (%) | Cond.ASR HB (%) | Cond.ASR WG (%) | Cond.ASR SR (%) | VSR HB (%) | Pareto |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in summary_rows:
        is_p = "★" if (r["method"], r["alpha"]) in pareto_set else ""
        a_str = f"{r['alpha']:.1f}" if r["alpha"] is not None else "N/A"
        md.append(
            f"| {r['label']} | {a_str} | {_fms(r['gsm8k_alpaca'])} | {_fms(r['vrr_ext'])} "
            f"| {_fms(r['cond_hb'])} | {_fms(r['cond_wg'])} | {_fms(r['cond_sr'])} | {_fms(r['vsr_hb'])} | {is_p} |"
        )

    md += [
        "",
        "## 3. 同等安全性水準での曲線比較（プロンプト単位ブートストラップ 95% CI、1,000 回）",
        "",
        "| 比較（A − B） | seeds | Δ GSM8K Alpaca-CoT (pp) | Δ Cond.ASR HB (pp) | Δ Cond.ASR WG (pp) | Δ Cond.ASR SR (pp) |",
        "|:---|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in matched_safety_boot:
        md.append(
            f"| {r['comparison']} | {r['n_seeds']} | **{_fci(r['gsm8k'])}** "
            f"| {_fci(r['cond_hb'])} | {_fci(r['cond_wg'])} | {_fci(r['cond_sr'])} |"
        )

    md += [
        "",
        "## 4. 同一名目 α でのブートストラップ比較（95% CI、1,000 回）",
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
        "## 5. 出力図",
        "",
        "- `math_alpaca_p5_curve_3classifiers.png`（3 分類器別 安全性–有用性曲線）",
        "- `math_alpaca_all11_pareto.png`（全 11 手法 妥当性制約付き Pareto フロンティア）",
        "- `math_prompt_before_after_alpha06.png`（旧プロンプト vs 新 Alpaca-CoT 比較棒グラフ）",
    ]

    write_text(out_dir / "math_alpaca_analysis.md", "\n".join(md) + "\n")
    write_json(
        out_dir / "math_alpaca_analysis.json",
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "n_completed_models": n_total_completed,
            "base_models": {k: {kk: vv for kk, vv in v.items() if kk != "arr"} for k, v in base_models.items()},
            "pareto_frontier": [{"method": m, "alpha": a} for (m, a) in sorted(pareto_set, key=lambda x: (x[0], -1.0 if x[1] is None else x[1]))],
            "summary_rows": summary_rows,
            "matched_safety_bootstrap": matched_safety_boot,
            "same_alpha_bootstrap": same_alpha_boot,
        },
    )
    print(f"保存完了: {out_dir / 'math_alpaca_analysis.md'} (完了モデル {n_total_completed}/138)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
