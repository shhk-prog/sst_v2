#!/usr/bin/env python3
"""SoK 実証 2: 評価完了後の集計・プロット・プロンプト単位ブートストラップ解析スクリプト（CPU 専用）。

位置づけ:
  「P5（fp16 桁落ち＋>= 閾値による全 1 マスク退化）を修正すると、safety+math の
   安全性–有用性曲線がどう動くか」を検証する。Math 正答率が約 10% と小さいため、
   SST の TA に対する統計的優位を主張するのではなく、プロンプト単位ブートストラップで
   不確実性を明示したうえで曲線の変化を報告する。

実装内容:
  1. fp16 SST (v3) / fp32 SST (v5) / Task Arithmetic (v3) を共通条件で揃えて集計:
     - 実証 1 の拡張妥当性判定（is_gibberish OR is_suspected_token_salad）を全 3 手法に適用
     - 3 種の有害分類器を個別に集計:
       (a) HarmBench（4 ベンチ平均）
       (b) WildGuard（JailbreakBench + WildJailbreak 平均）
       (c) StrongREJECT（StrongREJECT 単独）
       および参考として Native 4 ベンチ平均・VRR（修正前/後）
     - fp32 側 JSON に `classifier_output` が欠落せず記録されているかを自動検証
  2. seed 42 の GPU 差対照モデル 2 本（v3 TA α=0.6 / v3 fp16 SST α=0.6 の同 GPU 再評価）と
     元の v3 結果を突き合わせ、GPU 差によるドリフト量を定量報告
  3. 曲線プロット（α 固定ではなく全 α 曲線で比較）:
     - 主図: 横軸 = Math 有用性 (%), 縦軸 = Conditional ASR (%), 3 seed の mean ± std（3 分類器別パネル）
     - 補助図: 横軸 = 実効安全注入量（α × 実効マスク比率、または post-merge V5 注入比）, 縦軸 = Cond. ASR / Math
  4. プロンプト単位ブートストラップ（1,000 回、固定 seed=20261124）で Math・Conditional ASR および
     fp32 SST − fp16 SST / fp32 SST − TA 差分の 95% 信頼区間を算出

制約: CPU 専用・v3/ は読み取り専用。出力は v5/outputs/sok_exp2/ のみ。
"""

from __future__ import annotations

import argparse
import json
import math
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

from probe_gibberish_escape import is_suspected_token_salad  # noqa: E402
from probe_native_classifier import BENCHES, harmful_harmbench_only, harmful_native  # noqa: E402
from v5lib.results_io import scan_results  # noqa: E402
from v5lib.safeio import prepare_write_path, read_json, write_json, write_text  # noqa: E402

ALPHAS = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
SEEDS = (42, 43, 44)
WILDGUARD_BENCHES = ("jailbreakbench", "wildjailbreak")
STRONGREJECT_BENCHES = ("strongreject",)

_FP32_SAFETY_RE = re.compile(
    r"^fp32_sst_safety\+math_alpha(?P<alpha>[0-9.]+)_n\d+_k[0-9.]+_seed(?P<seed>\d+)_(?P<bench>harmbench|jailbreakbench|strongreject|wildjailbreak)_safety\.json$"
)
_FP32_UTIL_RE = re.compile(
    r"^fp32_sst_safety\+math_alpha(?P<alpha>[0-9.]+)_n\d+_k[0-9.]+_seed(?P<seed>\d+)_utility_math(?:_(?P<task>gsm8k|minerva_math500))?\.json$"
)


def is_valid_extended(row: dict[str, Any]) -> bool:
    if bool(row.get("is_gibberish", False)):
        return False
    return not is_suspected_token_salad(str(row.get("response", "")))


def is_valid_rule_only(row: dict[str, Any]) -> bool:
    return not bool(row.get("is_gibberish", False))


def extract_safety_arrays(bench: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """安全性 JSON の rows から、拡張妥当性・3 分類器フラグ・classifier_output 存在確認を抽出する。"""
    n = len(rows)
    valid_ext = np.zeros(n, dtype=bool)
    valid_rule = np.zeros(n, dtype=bool)
    hb_flag = np.zeros(n, dtype=bool)
    nat_flag = np.zeros(n, dtype=bool)
    has_cls_out = 0
    has_hb_out = 0

    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            continue
        vr = is_valid_rule_only(r)
        ve = is_valid_extended(r)
        valid_rule[i] = vr
        valid_ext[i] = ve
        hb_flag[i] = harmful_harmbench_only(r)
        nat_flag[i] = harmful_native(bench, r)
        if r.get("classifier_output") is not None and str(r.get("classifier_output")).strip() != "":
            has_cls_out += 1
        if r.get("harmbench_cls_output") is not None and str(r.get("harmbench_cls_output")).strip() != "":
            has_hb_out += 1

    def _cond(valid_mask: np.ndarray, harm_mask: np.ndarray) -> float | None:
        nv = int(valid_mask.sum())
        if nv == 0:
            return None
        return float(100.0 * int((valid_mask & harm_mask).sum()) / nv)

    vrr_ext = float(100.0 * valid_ext.mean()) if n > 0 else None
    vrr_rule = float(100.0 * valid_rule.mean()) if n > 0 else None
    cond_hb = _cond(valid_ext, hb_flag)
    cond_nat = _cond(valid_ext, nat_flag)
    vsr_hb = float(100.0 * int((valid_ext & ~hb_flag).sum()) / n) if n > 0 else None

    return {
        "n": n,
        "valid_ext": valid_ext,
        "valid_rule": valid_rule,
        "hb_flag": hb_flag,
        "nat_flag": nat_flag,
        "vrr_ext": vrr_ext,
        "vrr_rule": vrr_rule,
        "cond_hb": cond_hb,
        "cond_nat": cond_nat,
        "vsr_hb": vsr_hb,
        "classifier_output_present": has_cls_out,
        "harmbench_cls_output_present": has_hb_out,
    }


def extract_math_task_scores(data: dict[str, Any], task: str) -> tuple[float | None, np.ndarray | None]:
    """lm-eval の utility JSON から、指定タスクの集約スコア(%)とプロンプト単位 0/1 配列を抽出する。"""
    results = data.get("results") or {}
    task_res = results.get(task)
    agg_score = None
    if isinstance(task_res, dict):
        if task == "gsm8k":
            for k in ("exact_match,flexible-extract", "exact_match,strict-match", "exact_match", "acc,none"):
                if task_res.get(k) is not None:
                    val = float(task_res[k])
                    agg_score = val * 100.0 if val <= 1.0 else val
                    break
        elif task == "minerva_math500":
            for k in ("math_verify,none", "exact_match,none", "acc,none"):
                if task_res.get(k) is not None:
                    val = float(task_res[k])
                    agg_score = val * 100.0 if val <= 1.0 else val
                    break

    samples_dict = data.get("samples") or {}
    raw_samples = samples_dict.get(task)
    per_doc: np.ndarray | None = None
    if isinstance(raw_samples, list) and raw_samples:
        if task == "gsm8k":
            # gsm8k は strict-match と flexible-extract の 2 フィルタが同 doc_id で入ることがある
            filtered = [s for s in raw_samples if isinstance(s, dict) and s.get("filter") == "flexible-extract"]
            if not filtered:
                filtered = [s for s in raw_samples if isinstance(s, dict)]
            filtered.sort(key=lambda s: int(s.get("doc_id", 0)))
            vals = [float(s.get("exact_match", 0.0)) for s in filtered]
            per_doc = np.asarray(vals, dtype=np.float64)
        elif task == "minerva_math500":
            filtered = [s for s in raw_samples if isinstance(s, dict)]
            filtered.sort(key=lambda s: int(s.get("doc_id", 0)))
            vals = [float(s.get("math_verify", s.get("exact_match", 0.0))) for s in filtered]
            per_doc = np.asarray(vals, dtype=np.float64)
        if agg_score is None and per_doc is not None and len(per_doc) > 0:
            agg_score = float(100.0 * per_doc.mean())

    return agg_score, per_doc


def load_math_scores_from_paths(paths: dict[str, Path]) -> dict[str, Any]:
    """new-style (gsm8k/minerva 個別) と combined (_utility_math.json) の両方に対応する。"""
    out: dict[str, Any] = {"gsm8k": None, "minerva_math500": None, "gsm8k_arr": None, "minerva_arr": None}
    for task in ("gsm8k", "minerva_math500"):
        candidate_paths = []
        if task in paths:
            candidate_paths.append(paths[task])
        if "combined" in paths:
            candidate_paths.append(paths["combined"])
        for p in candidate_paths:
            if p.is_file():
                d = read_json(p)
                sc, arr = extract_math_task_scores(d, task)
                if sc is not None:
                    out[task] = sc
                    out["gsm8k_arr" if task == "gsm8k" else "minerva_arr"] = arr
                    break
    if out["gsm8k"] is not None and out["minerva_math500"] is not None:
        out["math_avg"] = 0.5 * (out["gsm8k"] + out["minerva_math500"])
    else:
        out["math_avg"] = None
    return out


def collect_v3_math_results(v3_results_root: Path) -> dict[tuple[str, float, int], dict[str, Any]]:
    """v3/results/vllm/debug_limit320 から safety+math の fp16 SST (diagonal_sst_main) と TA を収集する。"""
    scan = scan_results(str(v3_results_root))
    safety_files: dict[tuple[str, float, int], dict[str, Path]] = defaultdict(dict)
    util_files: dict[tuple[str, float, int], dict[str, Path]] = defaultdict(dict)

    method_map = {
        "diagonal_sst_main": "fp16_sst_v3",
        "task_arithmetic": "task_arithmetic_v3",
    }
    for f in scan.files:
        if f.kind != "main" or f.pattern != "safety+math" or f.method not in method_map:
            continue
        if f.alpha is None or f.seed is None:
            continue
        mkey = method_map[f.method]
        a = round(float(f.alpha), 3)
        key = (mkey, a, int(f.seed))
        if f.family == "safety" and f.bench in BENCHES:
            safety_files[key][f.bench] = Path(f.path)
        elif f.family == "utility" and f.domain == "math":
            if f.style == "new" and f.task in ("gsm8k", "minerva_math500"):
                util_files[key][f.task] = Path(f.path)
            elif f.style == "old":
                util_files[key]["combined"] = Path(f.path)

    return _build_condition_records(safety_files, util_files)


def collect_v5_fp32_results(v5_results_root: Path) -> dict[tuple[str, float, int], dict[str, Any]]:
    """v5/results/fp32_sst_math/seed{42,43,44} から fp32 SST の結果を収集する。"""
    safety_files: dict[tuple[str, float, int], dict[str, Path]] = defaultdict(dict)
    util_files: dict[tuple[str, float, int], dict[str, Path]] = defaultdict(dict)

    if not v5_results_root.is_dir():
        return {}

    for p in sorted(v5_results_root.rglob("*.json")):
        if "controls_seed" in str(p) or "summary_tables" in str(p):
            continue
        m_s = _FP32_SAFETY_RE.match(p.name)
        if m_s:
            a = round(float(m_s.group("alpha")), 3)
            seed = int(m_s.group("seed"))
            bench = m_s.group("bench")
            safety_files[("fp32_sst_v5", a, seed)][bench] = p
            continue
        m_u = _FP32_UTIL_RE.match(p.name)
        if m_u:
            a = round(float(m_u.group("alpha")), 3)
            seed = int(m_u.group("seed"))
            task = m_u.group("task") or "combined"
            util_files[("fp32_sst_v5", a, seed)][task] = p

    return _build_condition_records(safety_files, util_files)


def _build_condition_records(
    safety_files: dict[tuple[str, float, int], dict[str, Path]],
    util_files: dict[tuple[str, float, int], dict[str, Path]],
) -> dict[tuple[str, float, int], dict[str, Any]]:
    records: dict[tuple[str, float, int], dict[str, Any]] = {}
    all_keys = sorted(set(safety_files.keys()) | set(util_files.keys()))
    for key in all_keys:
        s_paths = safety_files.get(key, {})
        u_paths = util_files.get(key, {})
        bench_stats: dict[str, Any] = {}
        for b in BENCHES:
            if b in s_paths and s_paths[b].is_file():
                d = read_json(s_paths[b])
                rows = d.get("results", [])
                if isinstance(rows, list) and rows:
                    bench_stats[b] = extract_safety_arrays(b, rows)

        math_stats = load_math_scores_from_paths(u_paths)

        def _avg_metric(benches: tuple[str, ...], field: str) -> float | None:
            vals = [bench_stats[b][field] for b in benches if b in bench_stats and bench_stats[b][field] is not None]
            return (sum(vals) / len(vals)) if len(vals) == len(benches) else None

        records[key] = {
            "method": key[0],
            "alpha": key[1],
            "seed": key[2],
            "benches": bench_stats,
            "math": math_stats,
            "vrr_ext": _avg_metric(BENCHES, "vrr_ext"),
            "vrr_rule": _avg_metric(BENCHES, "vrr_rule"),
            "cond_hb": _avg_metric(BENCHES, "cond_hb"),
            "cond_wg": _avg_metric(WILDGUARD_BENCHES, "cond_nat"),
            "cond_sr": _avg_metric(STRONGREJECT_BENCHES, "cond_nat"),
            "cond_nat_all4": _avg_metric(BENCHES, "cond_nat"),
            "vsr_hb": _avg_metric(BENCHES, "vsr_hb"),
            "math_avg": math_stats["math_avg"],
            "gsm8k": math_stats["gsm8k"],
            "minerva_math500": math_stats["minerva_math500"],
        }
    return records


def collect_controls_comparison(
    controls_dir: Path,
    v3_records: dict[tuple[str, float, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    """seed 42 の GPU 差対照モデル 2 本と元の v3 結果を比較する。"""
    specs = [
        ("ctrl_v3_task_arithmetic_safety+math_alpha0.6_seed42", "task_arithmetic_v3", "Task Arithmetic (α=0.6, seed42)"),
        ("ctrl_v3_diagonal_sst_safety+math_alpha0.6_seed42", "fp16_sst_v3", "fp16 SST (α=0.6, seed42)"),
    ]
    out: list[dict[str, Any]] = []
    if not controls_dir.is_dir():
        return out

    for prefix, v3_method, label in specs:
        s_paths = {b: controls_dir / f"{prefix}_{b}_safety.json" for b in BENCHES}
        u_paths = {"combined": controls_dir / f"{prefix}_utility_math.json"}
        if not any(p.is_file() for p in s_paths.values()):
            continue
        ctrl_rec = _build_condition_records({(prefix, 0.6, 42): s_paths}, {(prefix, 0.6, 42): u_paths})[(prefix, 0.6, 42)]
        orig_rec = v3_records.get((v3_method, 0.6, 42))
        row: dict[str, Any] = {"label": label, "prefix": prefix, "ctrl": {}, "orig": {}, "delta": {}}
        for metric in ("vrr_ext", "cond_hb", "cond_wg", "cond_sr", "gsm8k", "minerva_math500", "math_avg"):
            cv = ctrl_rec.get(metric)
            ov = orig_rec.get(metric) if orig_rec else None
            row["ctrl"][metric] = cv
            row["orig"][metric] = ov
            row["delta"][metric] = (cv - ov) if (cv is not None and ov is not None) else None
        out.append(row)
    return out


def verify_fp32_classifier_outputs(records: dict[tuple[str, float, int], dict[str, Any]]) -> dict[str, Any]:
    """fp32 側安全性 JSON に classifier_output と harmbench_cls_output が入っているか検証する。"""
    total_files = 0
    missing_cls_files = 0
    missing_hb_files = 0
    per_bench: dict[str, dict[str, int]] = {b: {"files": 0, "rows": 0, "cls_present": 0, "hb_present": 0} for b in BENCHES}

    for (method, _alpha, _seed), rec in sorted(records.items()):
        if method != "fp32_sst_v5":
            continue
        for b, st in rec["benches"].items():
            total_files += 1
            per_bench[b]["files"] += 1
            per_bench[b]["rows"] += st["n"]
            per_bench[b]["cls_present"] += st["classifier_output_present"]
            per_bench[b]["hb_present"] += st["harmbench_cls_output_present"]
            if st["classifier_output_present"] < st["n"]:
                missing_cls_files += 1
            if st["harmbench_cls_output_present"] < st["n"]:
                missing_hb_files += 1

    return {
        "total_fp32_safety_files": total_files,
        "files_with_missing_classifier_output": missing_cls_files,
        "files_with_missing_harmbench_cls_output": missing_hb_files,
        "all_classifier_outputs_present": total_files > 0 and missing_cls_files == 0 and missing_hb_files == 0,
        "per_bench": per_bench,
    }


def _bootstrap_mean_cond_asr(
    recs: list[dict[str, Any]],
    benches: tuple[str, ...],
    harm_key: str,
    rng: np.random.Generator,
    n_boot: int,
) -> np.ndarray | None:
    """複数 seed にわたり、各ベンチマーク内でプロンプトを復元抽出して seed 平均のブートストラップ分布を返す。"""
    valid_recs = [r for r in recs if all(b in r["benches"] for b in benches)]
    if not valid_recs:
        return None
    # 各ベンチマーク共通のプロンプト数 N に対し、同じリサンプリング添字を使って seed 間・手法間の対応を保つ
    n_per_bench = {b: min(r["benches"][b]["n"] for r in valid_recs) for b in benches}
    boot = np.zeros(n_boot, dtype=np.float64)
    for b in benches:
        n = n_per_bench[b]
        idx = rng.integers(0, n, size=(n_boot, n))
        bench_boot = np.zeros(n_boot, dtype=np.float64)
        for r in valid_recs:
            ve = r["benches"][b]["valid_ext"][:n]
            hm = r["benches"][b][harm_key][:n]
            ve_s = ve[idx]
            hm_s = (ve & hm)[idx]
            denom = np.maximum(ve_s.sum(axis=1), 1)
            bench_boot += 100.0 * hm_s.sum(axis=1) / denom
        boot += bench_boot / len(valid_recs)
    boot /= len(benches)
    return boot


def _bootstrap_paired_diff(
    recs_a: list[dict[str, Any]],
    recs_b: list[dict[str, Any]],
    metric_kind: str,
    n_boot: int,
    seed: int,
) -> dict[str, float | None]:
    """対応のあるプロンプト単位ブートストラップで (A - B) の点推定・95% CI を算出する。"""
    by_seed_a = {r["seed"]: r for r in recs_a}
    by_seed_b = {r["seed"]: r for r in recs_b}
    common_seeds = sorted(set(by_seed_a) & set(by_seed_b))
    if not common_seeds:
        return {"mean_diff": None, "ci95_low": None, "ci95_high": None}

    rng = np.random.default_rng(seed)

    if metric_kind == "math_avg":
        boot_diff = np.zeros(n_boot, dtype=np.float64)
        used_tasks = 0
        for arr_key in ("gsm8k_arr", "minerva_arr"):
            pairs = [
                (by_seed_a[s]["math"].get(arr_key), by_seed_b[s]["math"].get(arr_key))
                for s in common_seeds
                if by_seed_a[s]["math"].get(arr_key) is not None and by_seed_b[s]["math"].get(arr_key) is not None
            ]
            if not pairs:
                continue
            n = min(min(len(a), len(b)) for a, b in pairs)
            if n == 0:
                continue
            idx = rng.integers(0, n, size=(n_boot, n))
            task_diff = np.zeros(n_boot, dtype=np.float64)
            for a, b in pairs:
                diff_vec = 100.0 * (a[:n] - b[:n])
                task_diff += diff_vec[idx].mean(axis=1)
            boot_diff += task_diff / len(pairs)
            used_tasks += 1
        if used_tasks == 0:
            return {"mean_diff": None, "ci95_low": None, "ci95_high": None}
        boot_diff /= used_tasks
        lo, hi = np.percentile(boot_diff, [2.5, 97.5])
        return {"mean_diff": float(boot_diff.mean()), "ci95_low": float(lo), "ci95_high": float(hi)}

    benches_map = {
        "cond_hb": (BENCHES, "hb_flag"),
        "cond_wg": (WILDGUARD_BENCHES, "nat_flag"),
        "cond_sr": (STRONGREJECT_BENCHES, "nat_flag"),
    }
    benches, harm_key = benches_map[metric_kind]
    boot_diff = np.zeros(n_boot, dtype=np.float64)
    for b in benches:
        pairs = [
            (by_seed_a[s]["benches"].get(b), by_seed_b[s]["benches"].get(b))
            for s in common_seeds
            if b in by_seed_a[s]["benches"] and b in by_seed_b[s]["benches"]
        ]
        if not pairs:
            return {"mean_diff": None, "ci95_low": None, "ci95_high": None}
        n = min(min(a["n"], b_rec["n"]) for a, b_rec in pairs)
        idx = rng.integers(0, n, size=(n_boot, n))
        b_diff = np.zeros(n_boot, dtype=np.float64)
        for a, b_rec in pairs:
            va = a["valid_ext"][:n][idx]
            ha = (a["valid_ext"][:n] & a[harm_key][:n])[idx]
            vb = b_rec["valid_ext"][:n][idx]
            hb = (b_rec["valid_ext"][:n] & b_rec[harm_key][:n])[idx]
            asr_a = 100.0 * ha.sum(axis=1) / np.maximum(va.sum(axis=1), 1)
            asr_b = 100.0 * hb.sum(axis=1) / np.maximum(vb.sum(axis=1), 1)
            b_diff += asr_a - asr_b
        boot_diff += b_diff / len(pairs)
    boot_diff /= len(benches)
    lo, hi = np.percentile(boot_diff, [2.5, 97.5])
    return {"mean_diff": float(boot_diff.mean()), "ci95_low": float(lo), "ci95_high": float(hi)}


def mean_std(vals: list[float | None]) -> tuple[float | None, float | None]:
    clean = [v for v in vals if v is not None]
    if not clean:
        return None, None
    return statistics.mean(clean), (statistics.stdev(clean) if len(clean) > 1 else 0.0)


def aggregate_curves(records: dict[tuple[str, float, int], dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """手法ごと・α ごとに 3 seed の mean ± std を集計する。"""
    grouped: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for (method, alpha, _seed), rec in sorted(records.items()):
        grouped[(method, alpha)].append(rec)

    curves: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (method, alpha), recs in sorted(grouped.items()):
        entry: dict[str, Any] = {"method": method, "alpha": alpha, "n_seeds": len(recs)}
        for m in ("vrr_rule", "vrr_ext", "cond_hb", "cond_wg", "cond_sr", "cond_nat_all4", "vsr_hb", "gsm8k", "minerva_math500", "math_avg"):
            mu, sd = mean_std([r.get(m) for r in recs])
            entry[m] = {"mean": mu, "std": sd}
        curves[method].append(entry)
    return dict(curves)


def load_effective_injection_scale(exp2_out_dir: Path) -> dict[str, float]:
    """補助図の横軸用: 各手法の α=1.0 基準の対 TA 実効注入スケールを取得する。"""
    # Task Arithmetic は定義上 1.0、v3 fp16 SST は V5 実測の中央値 1.000（平均 0.7043）
    scales = {
        "task_arithmetic_v3": 1.000,
        "fp16_sst_v3": 0.7043,  # v3 全 224 テンソル実効マスク平均（中央値 1.000）
        "fp32_sst_v5": 0.2000,  # 厳密 k=0.20（post_merge_verification の実測があれば上書き）
    }
    ratios = []
    for seed in SEEDS:
        p = exp2_out_dir / f"post_merge_verification_seed{seed}.json"
        if p.is_file():
            d = read_json(p)
            r = d.get("check3_alpha06_injection_ratio_vs_v3_ta", {}).get("median_inner_ratio")
            if r is not None:
                ratios.append(float(r))
    if ratios:
        scales["fp32_sst_v5"] = statistics.mean(ratios)
    return scales


def plot_safety_utility_curves(curves: dict[str, list[dict[str, Any]]], out_png: Path) -> None:
    """主図: 横軸 = Math (%), 縦軸 = Conditional ASR (%), 3 分類器別パネル（3 seed mean ± std）。"""
    styles = {
        "fp32_sst_v5": {"label": "fp32 SST (P5 fixed, v5)", "color": "#d62728", "marker": "o", "linestyle": "-"},
        "fp16_sst_v3": {"label": "fp16 SST (P5 bug, v3)", "color": "#1f77b4", "marker": "s", "linestyle": "--"},
        "task_arithmetic_v3": {"label": "Task Arithmetic (v3)", "color": "#2ca02c", "marker": "^", "linestyle": ":"},
    }
    panels = [
        ("cond_hb", "HarmBench Classifier (4-bench avg)"),
        ("cond_wg", "WildGuard (JBB + WJB avg)"),
        ("cond_sr", "StrongREJECT (SR only)"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8), sharex=True)
    for ax, (y_key, title) in zip(axes, panels):
        for method in ("fp32_sst_v5", "fp16_sst_v3", "task_arithmetic_v3"):
            pts = curves.get(method, [])
            valid_pts = [p for p in pts if p["math_avg"]["mean"] is not None and p[y_key]["mean"] is not None]
            if not valid_pts:
                continue
            xs = [p["math_avg"]["mean"] for p in valid_pts]
            xerr = [p["math_avg"]["std"] or 0.0 for p in valid_pts]
            ys = [p[y_key]["mean"] for p in valid_pts]
            yerr = [p[y_key]["std"] or 0.0 for p in valid_pts]
            st = styles[method]
            ax.errorbar(
                xs,
                ys,
                xerr=xerr,
                yerr=yerr,
                label=st["label"],
                color=st["color"],
                marker=st["marker"],
                linestyle=st["linestyle"],
                linewidth=1.8,
                markersize=6,
                capsize=3,
                alpha=0.9,
            )
            for p, x, y in zip(valid_pts, xs, ys):
                ax.annotate(f"{p['alpha']:.1f}", (x, y), textcoords="offset points", xytext=(4, 4), fontsize=7.5, color=st["color"])

        ax.set_title(title, fontsize=10.5)
        ax.set_xlabel("Math Utility (GSM8K + Minerva500 avg, %)")
        ax.set_ylabel("Conditional ASR (%, lower is safer)")
        ax.grid(True, alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, fontsize=9.5)
    fig.suptitle("SoK Exp 2 (safety+math): Safety–Utility Curve Shift after Fixing P5 (3-seed mean ± std)", y=0.99, fontsize=11.5)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    path = prepare_write_path(out_png)
    fig.savefig(path, dpi=150, metadata={"Software": None})
    plt.close(fig)


def plot_injection_aux(curves: dict[str, list[dict[str, Any]]], scales: dict[str, float], out_png: Path) -> None:
    """補助図: 横軸 = 実効安全注入量（α × 対 TA 注入スケール）, 縦軸 = Cond. ASR(HB) および Math (%)。"""
    styles = {
        "fp32_sst_v5": {"label": f"fp32 SST (scale={scales['fp32_sst_v5']:.2f})", "color": "#d62728", "marker": "o", "linestyle": "-"},
        "fp16_sst_v3": {"label": f"fp16 SST (scale={scales['fp16_sst_v3']:.2f})", "color": "#1f77b4", "marker": "s", "linestyle": "--"},
        "task_arithmetic_v3": {"label": "Task Arithmetic (scale=1.00)", "color": "#2ca02c", "marker": "^", "linestyle": ":"},
    }
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharex=True)
    for ax, y_key, ylabel, title in [
        (axes[0], "cond_hb", "Conditional ASR - HarmBench (%)", "Effective Safety Injection vs Cond. ASR (HB)"),
        (axes[1], "math_avg", "Math Utility (%)", "Effective Safety Injection vs Math Utility"),
    ]:
        for method in ("fp32_sst_v5", "fp16_sst_v3", "task_arithmetic_v3"):
            pts = [p for p in curves.get(method, []) if p[y_key]["mean"] is not None]
            if not pts:
                continue
            xs = [p["alpha"] * scales[method] for p in pts]
            ys = [p[y_key]["mean"] for p in pts]
            yerr = [p[y_key]["std"] or 0.0 for p in pts]
            st = styles[method]
            ax.errorbar(
                xs,
                ys,
                yerr=yerr,
                label=st["label"],
                color=st["color"],
                marker=st["marker"],
                linestyle=st["linestyle"],
                linewidth=1.8,
                markersize=6,
                capsize=3,
            )
            for p, x, y in zip(pts, xs, ys):
                ax.annotate(f"α={p['alpha']:.1f}", (x, y), textcoords="offset points", xytext=(3, 4), fontsize=7.5, color=st["color"])
        ax.set_xlabel("Effective Safety Injection Scale (α × injection_ratio_vs_TA)")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=10.5)
        ax.grid(True, alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, fontsize=9.5)
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    path = prepare_write_path(out_png)
    fig.savefig(path, dpi=150, metadata={"Software": None})
    plt.close(fig)


def fmt_ms(d: dict[str, float | None]) -> str:
    if d["mean"] is None:
        return "---"
    return f"{d['mean']:.2f} ± {d['std']:.2f}"


def fmt_ci(d: dict[str, float | None]) -> str:
    if d["mean_diff"] is None:
        return "---"
    return f"{d['mean_diff']:+.2f} [{d['ci95_low']:+.2f}, {d['ci95_high']:+.2f}]"


def load_gpu_infos(exp2_out_dir: Path) -> list[dict[str, Any]]:
    """v5/outputs/sok_exp2/gpu_info_seed*.json があれば読み込む。"""
    infos: list[dict[str, Any]] = []
    for seed in SEEDS:
        p = exp2_out_dir / f"gpu_info_seed{seed}.json"
        if p.is_file():
            try:
                infos.append(read_json(p))
            except Exception:
                continue
    return infos


def build_report(
    curves: dict[str, list[dict[str, Any]]],
    bootstrap_rows: list[dict[str, Any]],
    cls_check: dict[str, Any],
    controls_cmp: list[dict[str, Any]],
    scales: dict[str, float],
    gpu_infos: list[dict[str, Any]] | None = None,
) -> str:
    lines = [
        "# SoK 実証 2: P5 修正（fp32 SST-Merge）による安全性–有用性曲線の変化",
        "",
        "- **位置づけ**: 本解析は「P5（fp16 桁落ち＋`>= threshold` による全 1 マスク退化）を修正したときに `safety+math` の安全性–有用性曲線がどう動くか」を確認するものであり、Math 正答率が約 10% 規模であることを踏まえ、プロンプト単位ブートストラップ（1,000 回）で不確実性（95% CI）を併記する。",
        "- **共通妥当性ルール**: 全 3 手法に実証 1 の拡張妥当性判定（`is_gibberish` OR 非 ASCII 混入 OR 35 文字以上の無空白連続）を統一適用。",
        "- **3 種の有害分類器を個別集計**: HarmBench（4 ベンチ平均）、WildGuard（JBB + WJB 平均）、StrongREJECT（SR 単独）。",
        "",
        "## 1. `classifier_output` 存在検証（fp32 側 JSON）",
        "",
        f"- 対象安全性ファイル数: `{cls_check['total_fp32_safety_files']}`",
        f"- `classifier_output` 欠落ファイル数: `{cls_check['files_with_missing_classifier_output']}`",
        f"- `harmbench_cls_output` 欠落ファイル数: `{cls_check['files_with_missing_harmbench_cls_output']}`",
        f"- 検証結果: **{'PASS（全件記録済み）' if cls_check['all_classifier_outputs_present'] else '未評価または欠落あり'}**",
        "",
        "## 2. 全 α 曲線比較表（3 seed 平均 ± 標準偏差、拡張妥当性適用後）",
        "",
        "| Method | α | VRR (Ext, %) | Cond.ASR HB (%) | Cond.ASR WG (%) | Cond.ASR SR (%) | GSM8K (%) | Minerva500 (%) | Math Avg (%) |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for method in ("fp32_sst_v5", "fp16_sst_v3", "task_arithmetic_v3"):
        for p in curves.get(method, []):
            lines.append(
                f"| {method} | {p['alpha']:.1f} | {fmt_ms(p['vrr_ext'])} "
                f"| {fmt_ms(p['cond_hb'])} | {fmt_ms(p['cond_wg'])} | {fmt_ms(p['cond_sr'])} "
                f"| {fmt_ms(p['gsm8k'])} | {fmt_ms(p['minerva_math500'])} | {fmt_ms(p['math_avg'])} |"
            )

    lines += [
        "",
        "## 3. プロンプト単位ブートストラップ（95% CI、1,000 回、seed=20261124）",
        "",
        "| 比較ペア | α | Δ Cond.ASR HB (pp) | Δ Cond.ASR WG (pp) | Δ Cond.ASR SR (pp) | Δ Math Avg (pp) |",
        "|:---|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in bootstrap_rows:
        lines.append(
            f"| {r['pair']} | {r['alpha']:.1f} | {fmt_ci(r['cond_hb'])} | {fmt_ci(r['cond_wg'])} "
            f"| {fmt_ci(r['cond_sr'])} | {fmt_ci(r['math_avg'])} |"
        )

    lines += [
        "",
        "## 4. GPU 差対照モデルの検証（seed 42, α=0.6: 今回 GPU 再評価 − 元 v3 結果）",
        "",
    ]
    if controls_cmp:
        lines += [
            "| 対照モデル | Δ VRR (pp) | Δ Cond.ASR HB (pp) | Δ Cond.ASR WG (pp) | Δ Cond.ASR SR (pp) | Δ Math Avg (pp) |",
            "|:---|:---:|:---:|:---:|:---:|:---:|",
        ]
        for c in controls_cmp:
            def _fd(k: str) -> str:
                v = c["delta"].get(k)
                return f"{v:+.2f}" if v is not None else "---"
            lines.append(
                f"| {c['label']} | {_fd('vrr_ext')} | {_fd('cond_hb')} | {_fd('cond_wg')} | {_fd('cond_sr')} | {_fd('math_avg')} |"
            )
    else:
        lines.append("- （対照モデルの再評価結果がまだ出力されていません）")

    lines += [
        "",
        "## 5. 実行 GPU 環境の記録",
        "",
    ]
    if gpu_infos:
        lines += [
            "| Seed | Host | CUDA_VISIBLE_DEVICES | GPU 名 | UUID | Driver | PyTorch / CUDA / vLLM |",
            "|:---:|:---|:---:|:---|:---|:---|:---|",
        ]
        for g in gpu_infos:
            ng = (g.get("nvidia_smi_gpus") or [{}])[0]
            tg = (g.get("torch_gpus") or [{}])[0]
            gname = ng.get("name") or tg.get("name") or "---"
            uuid = ng.get("uuid") or "---"
            drv = ng.get("driver_version") or "---"
            vers = f"{g.get('torch_version')} / {g.get('torch_cuda_version')} / {g.get('vllm_version')}"
            lines.append(
                f"| {g.get('seed')} | {g.get('hostname')} | `{g.get('cuda_visible_devices')}` | {gname} | `{uuid}` | {drv} | `{vers}` |"
            )
    else:
        lines.append("- （`gpu_info_seed*.json` 未出力）")

    lines += [
        "",
        "## 6. 図の出力",
        "",
        f"- 主図（曲線比較、3 分類器別）: `exp2_safety_utility_curve.png`",
        f"- 補助図（実効安全注入量スケール vs 安全性・有用性）: `exp2_injection_ratio_curve.png`（スケール: `fp32_sst={scales['fp32_sst_v5']:.3f}`, `fp16_sst={scales['fp16_sst_v3']:.3f}`, `TA=1.000`）",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--v3-results-root", type=Path, default=V3_ROOT / "results" / "vllm" / "debug_limit320")
    ap.add_argument("--v5-results-root", type=Path, default=V5_ROOT / "results" / "fp32_sst_math")
    ap.add_argument("--out-dir", type=Path, default=V5_ROOT / "outputs" / "sok_exp2")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--boot-seed", type=int, default=20261124)
    args = ap.parse_args()

    v3_records = collect_v3_math_results(args.v3_results_root)
    v5_records = collect_v5_fp32_results(args.v5_results_root)
    all_records = {**v3_records, **v5_records}

    curves = aggregate_curves(all_records)
    cls_check = verify_fp32_classifier_outputs(v5_records)
    controls_cmp = collect_controls_comparison(args.v5_results_root / "controls_seed42", v3_records)
    scales = load_effective_injection_scale(args.out_dir)

    # プロンプト単位ブートストラップ（対応比較）
    by_ma: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for (method, alpha, _seed), rec in all_records.items():
        by_ma[(method, alpha)].append(rec)

    bootstrap_rows: list[dict[str, Any]] = []
    pair_specs = [
        ("fp32_sst_v5 - fp16_sst_v3", "fp32_sst_v5", "fp16_sst_v3"),
        ("fp32_sst_v5 - task_arithmetic_v3", "fp32_sst_v5", "task_arithmetic_v3"),
        ("fp16_sst_v3 - task_arithmetic_v3", "fp16_sst_v3", "task_arithmetic_v3"),
    ]
    for pair_label, ma, mb in pair_specs:
        for idx_a, alpha in enumerate(ALPHAS):
            recs_a = by_ma.get((ma, alpha), [])
            recs_b = by_ma.get((mb, alpha), [])
            if not recs_a or not recs_b:
                continue
            row: dict[str, Any] = {"pair": pair_label, "alpha": alpha}
            for k_i, mk in enumerate(("cond_hb", "cond_wg", "cond_sr", "math_avg")):
                row[mk] = _bootstrap_paired_diff(
                    recs_a,
                    recs_b,
                    metric_kind=mk,
                    n_boot=args.n_boot,
                    seed=args.boot_seed + idx_a * 17 + k_i,
                )
            bootstrap_rows.append(row)

    out_dir = args.out_dir
    gpu_infos = load_gpu_infos(out_dir)
    plot_safety_utility_curves(curves, out_dir / "exp2_safety_utility_curve.png")
    plot_injection_aux(curves, scales, out_dir / "exp2_injection_ratio_curve.png")

    report_md = build_report(curves, bootstrap_rows, cls_check, controls_cmp, scales, gpu_infos=gpu_infos)
    write_text(out_dir / "exp2_analysis_summary.md", report_md)
    write_json(
        out_dir / "exp2_analysis_summary.json",
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "n_boot": args.n_boot,
            "boot_seed": args.boot_seed,
            "gpu_infos": gpu_infos,
            "classifier_output_check": cls_check,
            "effective_injection_scales": scales,
            "curves": curves,
            "bootstrap_diffs": bootstrap_rows,
            "controls_comparison": controls_cmp,
        },
    )
    print(f"実証 2 解析出力完了: {out_dir}")
    print(f"  - fp32 側レコード数: {len(v5_records)}, v3 側レコード数: {len(v3_records)}")
    print(f"  - classifier_output 検証: {cls_check['all_classifier_outputs_present']} ({cls_check['total_fp32_safety_files']} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
