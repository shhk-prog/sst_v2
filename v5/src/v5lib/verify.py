"""仮説 V1〜V11 の検証の実行部分（FR2.2）。

段階:
1. ``collect_inputs``（check_inputs.py）: 入力の有無と大きさを、読み取りだけで一覧にする（中身は開かない）
2. ``run_v1`` 〜 ``run_v9``（check_v1_v9.py）: CPU での検証。テンソルは 1 つずつ読む
3. ``run_v10``、``run_v11``（check_v10_v11.py）: 結果ファイル名と比較ロジックでの再集計

どの検証も、実行した範囲（seed、パターン、層、テンソル数）を結果に記録する。範囲を絞った実行は、
その仮説を「判定不能」にする（``hypotheses.judge`` の ``complete=False``）。
GPU は使わない（``tensor_checks`` が ``device="cpu"`` に固定）。
"""

from __future__ import annotations

import glob
import json
import os
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from . import tensor_checks as tc
from .results_io import PATTERN_DOMAINS, PATTERNS, SEEDS

DOMAINS = ("math", "code", "medical")
UTIL_MODEL_NAMES = {"math": "WizardMath", "code": "WizardCoder", "medical": "MedAlpaca"}
HF_REPO_IDS = {
    "base": "meta-llama/Llama-2-7b-hf",
    "math": "WizardLMTeam/WizardMath-7B-V1.0",
    "code": "vanillaOVO/WizardCoder-Python-7B-V1.0",
    "medical": "medalpaca/medalpaca-7b",
}
MERGEKIT_METHODS = ("ties", "dare", "task_arithmetic", "della")
PLACEHOLDER_RES = [
    re.compile(r"^(Solve math problem|Write code for task|Diagnose medical case) \d+$"),
    re.compile(r"^[A-Za-z ]{3,40} \d+$"),
    re.compile(r"placeholder|lorem ipsum|dummy", re.IGNORECASE),
]
_LAYER_RE = re.compile(r"layers\.(\d+)\.")


# ---------------------------------------------------------------------------
# 判定と出力（段階ごとの結果ファイル）
# ---------------------------------------------------------------------------


def judge_stage(hypothesis_ids: Iterable[str], results: dict[str, dict[str, Any]], prereg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """段階の各仮説を、事前登録の基準で分類する。結果が無い（未実行の）仮説は「判定不能」にする。"""
    from .hypotheses import judge

    judged: dict[str, dict[str, Any]] = {}
    for hid in hypothesis_ids:
        res = results.get(hid)
        if res is None:
            judged[hid] = judge(hid, prereg, None, True, ["未実行"])
            continue
        judged[hid] = judge(hid, prereg, res.get("metrics"), res.get("complete", True),
                            res.get("missing_inputs", []), res.get("scope"))
    return judged


def render_verdicts_markdown(stage: str, judged: dict[str, dict[str, Any]]) -> str:
    """判定の一覧を Markdown にする（根拠の数値つき）。"""
    lines = [f"### 仮説の判定: {stage}", "", "| 仮説 | 判定 | 指標 | 値 | 理由 |", "|:---|:---|:---|---:|:---|"]
    for hid, j in judged.items():
        value = j["value"]
        value_text = "---" if value is None else (f"{value:.4g}" if isinstance(value, (int, float)) else str(value))
        lines.append("| " + " | ".join(str(x).replace("|", "\\|") for x in (
            f"{hid} {j['title']}", j["verdict"], j["metric"], value_text, j["reason"])) + " |")
    return "\n".join(lines) + "\n"


def write_stage_output(stage: str, out_dir: str | os.PathLike[str], judged: dict[str, dict[str, Any]],
                       results: dict[str, dict[str, Any]], extra: dict[str, Any] | None = None) -> list[str]:
    """段階の結果（判定、根拠、実行範囲、詳細）を ``out_dir`` に JSON と Markdown で書き、manifest を残す。"""
    from . import manifest
    from .safeio import write_json, write_text

    out = Path(out_dir)
    json_path = out / f"{stage}.json"
    md_path = out / f"{stage}.md"
    inputs = sorted({p for r in results.values() for p in r.get("inputs", [])})
    script_name = {"v1_v9": "check_v1_v9.py", "v10_v11": "check_v10_v11.py"}.get(stage, stage)
    payload = {
        "stage": stage,
        "verdicts": judged,
        "details": {hid: {"complete": r.get("complete"), "missing_inputs": r.get("missing_inputs"),
                          "scope": r.get("scope"), "notes": r.get("notes"), "details": r.get("details")}
                    for hid, r in results.items()},
        "inputs": inputs,
    }
    if extra:
        payload["extra"] = extra
    write_json(json_path, payload)
    write_text(md_path, render_verdicts_markdown(stage, judged))
    manifest.write_manifest(
        json_path, script=f"v5/scripts/{script_name}",
        inputs=inputs,
        counts={"n_hypotheses": len(judged),
                "n_support": sum(1 for j in judged.values() if j["verdict"] == "支持"),
                "n_refute": sum(1 for j in judged.values() if j["verdict"] == "不支持"),
                "n_undetermined": sum(1 for j in judged.values() if j["verdict"] == "判定不能")},
        missing=[{"hypothesis": hid, "missing_inputs": r.get("missing_inputs")} for hid, r in results.items() if r.get("missing_inputs")],
        settings={"scope": {hid: r.get("scope") for hid, r in results.items()}},
    )
    return [str(json_path), str(md_path)]


# ---------------------------------------------------------------------------
# 範囲と共通の補助
# ---------------------------------------------------------------------------


@dataclass
class Scope:
    """実行範囲。絞った範囲は、結果に必ず記録される。"""

    seeds: list[int] = field(default_factory=lambda: list(SEEDS))
    patterns: list[str] = field(default_factory=lambda: list(PATTERNS))
    layers: set[int] | None = None
    max_tensors: int | None = None
    max_models: int | None = None

    @property
    def full_seeds(self) -> bool:
        return sorted(self.seeds) == sorted(SEEDS)

    @property
    def full_patterns(self) -> bool:
        return sorted(self.patterns) == sorted(PATTERNS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seeds": sorted(self.seeds),
            "patterns": list(self.patterns),
            "layers": None if self.layers is None else sorted(self.layers),
            "max_tensors": self.max_tensors,
            "max_models": self.max_models,
            "full_seeds": self.full_seeds,
            "full_patterns": self.full_patterns,
        }


@dataclass
class Context:
    """検証に必要なパスと設定。"""

    fim_dir: Path
    data_fim_dir: Path
    merged_dir: Path
    scope: Scope
    fim_n: int = 500
    base_dir: Path | None = None
    util_dirs: dict[str, Path | None] = field(default_factory=lambda: {d: None for d in DOMAINS})
    safety_dir_template: str = ""
    params: dict[str, dict[str, Any]] = field(default_factory=dict)  # 仮説 ID -> 事前登録の params
    sst_alpha: float = 0.6
    spearman_samples: int = 1_000_000
    random_seed: int = 0

    def safety_dir(self, seed: int) -> Path | None:
        if not self.safety_dir_template:
            return None
        path = Path(self.safety_dir_template.format(seed=seed))
        return path if path.is_dir() else None


def layer_index(name: str) -> int | None:
    match = _LAYER_RE.search(name)
    return int(match.group(1)) if match else None


def select_names(names: Iterable[str], scope: Scope) -> tuple[list[str], int, bool]:
    """対象テンソル名を、層の指定と最大数で絞る。

    戻り値: (選んだ名前, 絞る前の対象テンソル数, 範囲を絞ったか)。
    """
    targets = sorted((n for n in names if tc.is_target_weight(n)), key=lambda n: (layer_index(n) is None, layer_index(n) or 0, n))
    total = len(targets)
    selected = targets
    restricted = False
    if scope.layers is not None:
        selected = [n for n in selected if layer_index(n) in scope.layers]
        restricted = True
    if scope.max_tensors is not None and len(selected) > scope.max_tensors:
        selected = selected[: scope.max_tensors]
        restricted = True
    return selected, total, restricted


def median(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return float(statistics.median(values)) if values else None


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return float(sum(values) / len(values)) if values else None


def resolve_hf_snapshot(repo_id: str, hf_home: str | os.PathLike[str] | None = None) -> Path | None:
    """HF のキャッシュ（読み取りだけ）から、モデルのスナップショットのフォルダを探す。無ければ ``None``。"""
    home = Path(hf_home) if hf_home else Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface")
    snaps = home / "hub" / ("models--" + repo_id.replace("/", "--")) / "snapshots"
    if not snaps.is_dir():
        return None
    candidates = sorted(d for d in snaps.iterdir() if d.is_dir() and (d / "config.json").exists())
    return candidates[-1] if candidates else None


def _result(metrics: dict[str, Any] | None, complete: bool, missing: list[str], ctx: Context,
            details: list[Any] | None = None, inputs: list[str] | None = None, notes: list[str] | None = None,
            ) -> dict[str, Any]:
    return {
        "metrics": metrics or {},
        "complete": complete,
        "missing_inputs": sorted(set(missing)),
        # 乱数（V3 の random マスクと順位相関の部分抽出）の seed は固定し、記録する（NFR1）
        "scope": {**ctx.scope.to_dict(), "random_seed": ctx.random_seed, "spearman_samples": ctx.spearman_samples},
        "details": details or [],
        "inputs": sorted(set(inputs or [])),
        "notes": notes or [],
    }


# ---------------------------------------------------------------------------
# 入力の一覧（check_inputs）
# ---------------------------------------------------------------------------


def _stat_entry(category: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    size = None
    if exists and path.is_file():
        size = path.stat().st_size
    return {"category": category, "path": str(path), "exists": exists, "size_bytes": size}


def _dir_summary(category: str, path: Path) -> dict[str, Any]:
    entry = {"category": category, "path": str(path), "exists": path.is_dir(), "files": []}
    if path.is_dir():
        for child in sorted(path.iterdir()):
            if child.is_file() and (child.suffix in (".safetensors", ".bin", ".json") or child.name.endswith(".index.json")):
                entry["files"].append({"name": child.name, "size_bytes": child.stat().st_size})
    return entry


def fim_cache_paths(ctx: Context, seed: int) -> dict[str, Any]:
    """FIM キャッシュのパス: harmful と、ドメインごとの benign（glob で 1 件に決まるものだけ）。"""
    harmful = ctx.fim_dir / f"harmful_safety_Llama2_SafetyFT_n{ctx.fim_n}_seed{seed}.pt"
    benign: dict[str, Path | None] = {}
    for domain in DOMAINS:
        matches = sorted(glob.glob(str(ctx.fim_dir / f"benign_{domain}_Llama2_*_n{ctx.fim_n}_seed{seed}.pt")))
        benign[domain] = Path(matches[0]) if len(matches) == 1 else None
    return {"harmful": harmful, "benign": benign}


def merged_dir_for(ctx: Context, method: str, pattern: str, seed: int, alpha: float | None = None) -> Path:
    """merge 済みモデルのフォルダ（v3 の命名: ``build_out_name_for_*``）。"""
    a = "" if alpha is None else f"_alpha{alpha:.1f}"
    if method == "diagonal_sst_main":
        name = f"sst_merge_v3_main_{method}_{pattern}{a}_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed{seed}"
    else:
        name = f"sst_merge_v3_main_{method}_{pattern}{a}_seed{seed}"
    return ctx.merged_dir / name


def compute_availability(ctx: Context, results_root: Path | None = None) -> dict[str, bool]:
    """仮説の ``needs`` に対応する入力が、そろっているか（存在確認だけ。中身は開かない）。"""
    seeds, patterns = ctx.scope.seeds, ctx.scope.patterns
    avail: dict[str, bool] = {}
    avail["fim_cache_harmful"] = all(fim_cache_paths(ctx, s)["harmful"].is_file() for s in seeds)
    need_domains = {d for p in patterns for d in PATTERN_DOMAINS[p]}
    avail["fim_cache_benign"] = all(
        fim_cache_paths(ctx, s)["benign"][d] is not None and fim_cache_paths(ctx, s)["benign"][d].is_file()
        for s in seeds for d in need_domains
    )

    def has_weights(path: Path | None) -> bool:
        return bool(path) and path.is_dir() and (
            (path / "model.safetensors").is_file()
            or (path / "model.safetensors.index.json").is_file()
            or (path / "pytorch_model.bin").is_file()
            or (path / "pytorch_model.bin.index.json").is_file()
        )

    avail["model_weights_base"] = has_weights(ctx.base_dir)
    avail["model_weights_util"] = all(has_weights(ctx.util_dirs.get(d)) for d in DOMAINS)
    avail["model_weights_safety"] = all(has_weights(ctx.safety_dir(s)) for s in seeds)
    avail["merged_models_sst"] = all(
        has_weights(merged_dir_for(ctx, "diagonal_sst_main", p, s, ctx.sst_alpha)) for p in patterns for s in seeds
    )
    avail["merged_models_ta"] = all(
        has_weights(merged_dir_for(ctx, "task_arithmetic", p, s, ctx.sst_alpha)) for p in patterns for s in seeds
    )
    avail["merged_model_configs"] = ctx.merged_dir.is_dir() and any(
        (d / "config.json").is_file() for d in list(ctx.merged_dir.iterdir())[:50] if d.is_dir()
    )
    avail["merged_model_safetensors_headers"] = ctx.merged_dir.is_dir() and any(
        (d / "model.safetensors.index.json").is_file() or (d / "model.safetensors").is_file()
        for d in list(ctx.merged_dir.iterdir())[:50] if d.is_dir()
    )
    avail["fim_data_json"] = all(
        (ctx.data_fim_dir / n).is_file()
        for n in ("fim_benign_math.json", "fim_benign_code.json", "fim_benign_medical.json", "fim_harmful.json")
    )
    root = Path(results_root) if results_root else None
    avail["results_ablation"] = bool(root) and root.is_dir() and any(root.glob("merged/seed*/*/ablation/*/*.json"))
    avail["results_main"] = bool(root) and root.is_dir() and any(root.glob("merged/seed*/*/*/*.json"))
    return avail


def collect_inputs(ctx: Context, results_root: Path | None, prereg: dict[str, Any]) -> dict[str, Any]:
    """V1〜V11 に必要な入力の有無とサイズを、読み取りだけで一覧にする（FR2.2 の第 1 段階）。

    ファイルの中身は開かない（``stat`` と、フォルダの一覧だけ）。判定不能になる見込みの仮説も添える。
    """
    entries: list[dict[str, Any]] = []
    for seed in SEEDS:
        paths = fim_cache_paths(ctx, seed)
        entries.append(_stat_entry("fim_cache_harmful", paths["harmful"]))
        for domain, p in paths["benign"].items():
            entries.append(_stat_entry("fim_cache_benign", p) if p else
                           {"category": "fim_cache_benign", "path": str(ctx.fim_dir / f"benign_{domain}_Llama2_*_n{ctx.fim_n}_seed{seed}.pt"),
                            "exists": False, "size_bytes": None})
    for name in ("fim_benign_math.json", "fim_benign_code.json", "fim_benign_medical.json", "fim_harmful.json"):
        entries.append(_stat_entry("fim_data_json", ctx.data_fim_dir / name))
    if ctx.base_dir:
        entries.append(_dir_summary("model_weights_base", ctx.base_dir))
    else:
        entries.append({"category": "model_weights_base", "path": None, "exists": False, "note": "--base-model-dir または --hf-home で指定する"})
    for domain in DOMAINS:
        p = ctx.util_dirs.get(domain)
        entries.append(_dir_summary(f"model_weights_util:{domain}", p) if p else
                       {"category": f"model_weights_util:{domain}", "path": None, "exists": False})
    for seed in SEEDS:
        p = ctx.safety_dir(seed)
        entries.append(_dir_summary(f"model_weights_safety:seed{seed}", p) if p else
                       {"category": f"model_weights_safety:seed{seed}", "path": ctx.safety_dir_template.format(seed=seed) if ctx.safety_dir_template else None, "exists": False})
    n_merged = len([d for d in ctx.merged_dir.iterdir() if d.is_dir()]) if ctx.merged_dir.is_dir() else 0
    entries.append({"category": "merged_models", "path": str(ctx.merged_dir), "exists": ctx.merged_dir.is_dir(), "n_dirs": n_merged})
    if results_root:
        entries.append({"category": "results", "path": str(results_root), "exists": Path(results_root).is_dir()})
    availability = compute_availability(ctx, results_root)
    likely_undetermined = {}
    for hid, entry in prereg["hypotheses"].items():
        missing = [n for n in entry.get("needs", []) if not availability.get(n, False)]
        if missing:
            likely_undetermined[hid] = missing
    return {"entries": entries, "availability": availability, "likely_undetermined": likely_undetermined,
            "scope": ctx.scope.to_dict()}


# ---------------------------------------------------------------------------
# V1
# ---------------------------------------------------------------------------


def run_v1(ctx: Context) -> dict[str, Any]:
    """V1: harmful FIM の fp16 キャスト後の 0 の割合。"""
    details: list[dict[str, Any]] = []
    inputs: list[str] = []
    missing: list[str] = []
    complete = ctx.scope.full_seeds
    notes: list[str] = []
    for seed in ctx.scope.seeds:
        path = fim_cache_paths(ctx, seed)["harmful"]
        if not path.is_file():
            missing.append("fim_cache_harmful")
            continue
        try:
            fim = tc.load_fim_lazy(path)
        except tc.TensorLoadError as exc:
            missing.append("fim_cache_harmful")
            notes.append(str(exc))
            continue
        inputs.append(str(path))
        names, _total, restricted = select_names(fim.keys(), ctx.scope)
        complete = complete and not restricted
        for name in names:
            tensor = fim[name]
            details.append({"seed": seed, "tensor": name, "numel": int(tensor.numel()),
                            "zero_fraction_fp16": tc.zero_fraction(tensor, True),
                            "zero_fraction_fp32": tc.zero_fraction(tensor, False)})
            del tensor
        del fim
    if not details:
        return _result(None, False, missing or ["fim_cache_harmful"], ctx, inputs=inputs, notes=notes)
    z16 = [d["zero_fraction_fp16"] for d in details]
    metrics = {
        "frac_tensors_fh_zero_over_80pct": sum(1 for z in z16 if z > 0.8) / len(z16),
        "max_zero_fraction_fh_fp16": max(z16),
        "mean_zero_fraction_fh_fp16": mean(z16),
        "mean_zero_fraction_fh_fp32": mean([d["zero_fraction_fp32"] for d in details]),
        "n_tensors": len(details),
    }
    return _result(metrics, complete and not missing, missing, ctx, details, inputs, notes)


# ---------------------------------------------------------------------------
# V2 と V3（同じ λ・マスクの計算を共有する）
# ---------------------------------------------------------------------------


def run_v2_v3(ctx: Context) -> dict[str, dict[str, Any]]:
    """V2（マスク比率と inf）と V3（Jaccard、順位相関）。戻り値は {"V2": 結果, "V3": 結果}。

    V3 は δ_s = θ_s − θ₀ が必要なので、基底モデルと safety モデルが無ければ V3 だけ入力不足になる。
    """
    k = float(ctx.params.get("V2", {}).get("k", 0.2))
    mask_tol = float(ctx.params.get("V2", {}).get("mask_tolerance", 0.05))
    inf_limit = float(ctx.params.get("V2", {}).get("inf_fraction_limit", 0.2))
    torch = tc._torch()
    entries: list[dict[str, Any]] = []
    inputs: list[str] = []
    missing2: list[str] = []
    missing3: list[str] = []
    notes: list[str] = []
    complete = ctx.scope.full_seeds and ctx.scope.full_patterns
    base_src = None
    if ctx.base_dir:
        try:
            base_src = tc.TensorSource(ctx.base_dir)
        except tc.TensorLoadError as exc:
            notes.append(str(exc))
    if base_src is None:
        missing3.append("model_weights_base")
    for seed in ctx.scope.seeds:
        paths = fim_cache_paths(ctx, seed)
        safety_src = None
        sdir = ctx.safety_dir(seed)
        if sdir is not None:
            try:
                safety_src = tc.TensorSource(sdir)
            except tc.TensorLoadError as exc:
                notes.append(str(exc))
        if safety_src is None:
            missing3.append("model_weights_safety")
        if not paths["harmful"].is_file():
            missing2.append("fim_cache_harmful")
            continue
        try:
            fim_h = tc.load_fim_lazy(paths["harmful"])
        except tc.TensorLoadError as exc:
            missing2.append("fim_cache_harmful")
            notes.append(str(exc))
            continue
        inputs.append(str(paths["harmful"]))
        # seed ごとに必要なドメインの benign FIM を 1 回だけ開く（パターン間の重複読込・重複計算を省く）
        seed_domains = sorted({d for p in ctx.scope.patterns for d in PATTERN_DOMAINS[p]})
        benign_by_domain: dict[str, Any] = {}
        for d in seed_domains:
            bp = paths["benign"][d]
            if bp is None or not bp.is_file():
                missing2.append("fim_cache_benign")
                continue
            try:
                benign_by_domain[d] = tc.load_fim_lazy(bp)
                inputs.append(str(bp))
            except tc.TensorLoadError as exc:
                missing2.append("fim_cache_benign")
                notes.append(str(exc))
        usable_patterns = [p for p in ctx.scope.patterns if all(d in benign_by_domain for d in PATTERN_DOMAINS[p])]
        if not usable_patterns:
            del fim_h, benign_by_domain
            continue
        names, _total, restricted = select_names(fim_h.keys(), ctx.scope)
        complete = complete and not restricted
        by_pattern_entries: dict[str, list[dict[str, Any]]] = {p: [] for p in usable_patterns}
        for index, name in enumerate(names):
            fh_tensor = fim_h[name]
            fb_tensors = {d: benign_by_domain[d][name] for d in benign_by_domain if name in benign_by_domain[d]}
            mag = mag_mask = rand = j_mag_rand = None
            if base_src is not None and safety_src is not None and base_src.has(name) and safety_src.has(name):
                theta_0 = base_src.get(name).half()
                theta_s = safety_src.get(name).half()
                if theta_0.shape == fh_tensor.shape == theta_s.shape:
                    mag = (theta_s - theta_0).abs()
                    mag_mask = tc.topk_mask(mag, k)
                    rand = tc.random_mask(fh_tensor.shape, k, ctx.random_seed + index)
                    j_mag_rand = tc.jaccard(mag_mask, rand)
                del theta_0, theta_s
            for pattern in usable_patterns:
                p_domains = PATTERN_DOMAINS[pattern]
                if any(d not in fb_tensors for d in p_domains):
                    notes.append(f"benign FIM にテンソルが無い（飛ばす）: {name} ({pattern}, seed{seed})")
                    continue
                lam = tc.lambda_fhfb(fh_tensor, [fb_tensors[d] for d in p_domains])
                mask = tc.topk_mask(lam, k)
                entry: dict[str, Any] = {
                    "seed": seed, "pattern": pattern, "tensor": name, "numel": int(lam.numel()),
                    "mask_ratio": tc.mask_ratio(mask), "inf_count": tc.inf_count(lam),
                }
                if mag is not None and mag_mask is not None and rand is not None:
                    entry["jaccard_fhfb_vs_magnitude"] = tc.jaccard(mask, mag_mask)
                    entry["jaccard_fhfb_vs_random"] = tc.jaccard(mask, rand)
                    entry["jaccard_magnitude_vs_random"] = j_mag_rand
                    entry["spearman_lambda_vs_abs_delta_s"] = tc.spearman(
                        lam.float(), mag.float(), ctx.spearman_samples, ctx.random_seed + index)
                by_pattern_entries[pattern].append(entry)
                del lam, mask
            del fh_tensor, fb_tensors, mag, mag_mask, rand
        for pattern in usable_patterns:
            entries.extend(by_pattern_entries[pattern])
        del benign_by_domain, fim_h
    inputs = sorted(set(inputs))
    scope_info = {**ctx.scope.to_dict(), "random_seed": ctx.random_seed, "spearman_samples": ctx.spearman_samples}
    # V2
    if entries:
        abnormal = [
            e for e in entries
            if abs(e["mask_ratio"] - k) > mask_tol or (e["inf_count"] / e["numel"]) > inf_limit
        ]
        m2 = {
            "frac_tensors_mask_or_inf_abnormal": len(abnormal) / len(entries),
            "mean_mask_ratio": mean([e["mask_ratio"] for e in entries]),
            "max_mask_ratio": max(e["mask_ratio"] for e in entries),
            "total_inf_count": sum(e["inf_count"] for e in entries),
            "n_tensors": len(entries),
        }
        r2 = _result(m2, complete and not missing2, missing2, ctx, entries, inputs, notes)
    else:
        r2 = _result(None, False, missing2 or ["fim_cache_harmful"], ctx, inputs=inputs, notes=notes)
    # V3
    with_j = [e for e in entries if "jaccard_fhfb_vs_magnitude" in e]
    if with_j and not missing3:
        m3 = {
            "median_jaccard_fhfb_vs_magnitude": median([e["jaccard_fhfb_vs_magnitude"] for e in with_j]),
            "median_jaccard_fhfb_vs_random": median([e["jaccard_fhfb_vs_random"] for e in with_j]),
            "median_jaccard_magnitude_vs_random": median([e["jaccard_magnitude_vs_random"] for e in with_j]),
            "median_spearman_lambda_vs_abs_delta_s": median(
                [e["spearman_lambda_vs_abs_delta_s"] for e in with_j if e["spearman_lambda_vs_abs_delta_s"] is not None]),
            "n_tensors": len(with_j),
        }
        r3 = _result(m3, complete and not missing2, missing2, ctx, with_j, inputs, notes)
    else:
        r3 = _result(None, False, (missing3 + missing2) or ["model_weights_base"], ctx, inputs=inputs, notes=notes)
    r2["scope"] = r3["scope"] = scope_info
    return {"V2": r2, "V3": r3}


# ---------------------------------------------------------------------------
# V4
# ---------------------------------------------------------------------------


def run_v4(ctx: Context) -> dict[str, Any]:
    """V4: |α·δ_s| < ulp_fp16(θ_u)/2 の座標の割合（α は事前登録の値）。"""
    alpha = float(ctx.params.get("V4", {}).get("alpha", 0.6))
    missing: list[str] = []
    notes: list[str] = []
    details: list[dict[str, Any]] = []
    inputs: list[str] = []
    complete = ctx.scope.full_seeds
    try:
        base_src = tc.TensorSource(ctx.base_dir) if ctx.base_dir else None
    except tc.TensorLoadError as exc:
        base_src = None
        notes.append(str(exc))
    if base_src is None:
        missing.append("model_weights_base")
    util_srcs: dict[str, tc.TensorSource] = {}
    for domain in DOMAINS:
        p = ctx.util_dirs.get(domain)
        try:
            if p is None:
                raise tc.TensorLoadError(f"{domain} のモデルが指定されていない")
            util_srcs[domain] = tc.TensorSource(p)
        except tc.TensorLoadError as exc:
            missing.append("model_weights_util")
            notes.append(str(exc))
    if missing:
        return _result(None, False, missing, ctx, notes=notes)
    inputs.append(str(ctx.base_dir))
    inputs.extend(str(ctx.util_dirs[d]) for d in DOMAINS)
    safety_srcs: dict[int, tc.TensorSource] = {}
    for seed in ctx.scope.seeds:
        sdir = ctx.safety_dir(seed)
        try:
            if sdir is None:
                raise tc.TensorLoadError(f"seed{seed} の safety モデルが見つからない")
            safety_srcs[seed] = tc.TensorSource(sdir)
            inputs.append(str(sdir))
        except tc.TensorLoadError as exc:
            missing.append("model_weights_safety")
            notes.append(str(exc))
    if not safety_srcs:
        return _result(None, False, missing or ["model_weights_safety"], ctx, notes=notes)
    first_safety = next(iter(safety_srcs.values()))
    names, _total, restricted = select_names(first_safety.names(), ctx.scope)
    complete = complete and not restricted
    # ドメインごとにシャードを 1 周だけ読む（.bin シャードの重複読込を避ける）
    for domain, util in util_srcs.items():
        for name in names:
            if not (base_src.has(name) and util.has(name)):
                continue
            theta_u = util.get(name).half()
            theta_0 = base_src.get(name).half()
            for seed, safety in safety_srcs.items():
                if not safety.has(name):
                    continue
                delta_s = safety.get(name).half() - theta_0
                if theta_u.shape != delta_s.shape:
                    continue
                details.append({"seed": seed, "domain": domain, "tensor": name,
                                "frac_below_half_ulp": tc.frac_below_half_ulp(theta_u, delta_s, alpha)})
                del delta_s
            del theta_0, theta_u
    if not details:
        return _result(None, False, missing or ["model_weights_safety"], ctx, notes=notes)
    fracs = [d["frac_below_half_ulp"] for d in details]
    metrics = {"mean_frac_alpha_delta_below_half_ulp": mean(fracs),
               "max_frac_alpha_delta_below_half_ulp": max(fracs), "n_tensors": len(fracs)}
    return _result(metrics, complete and not missing, missing, ctx, details, inputs, notes)


# ---------------------------------------------------------------------------
# V5
# ---------------------------------------------------------------------------


def run_v5(ctx: Context) -> dict[str, Any]:
    """V5: SST と task_arithmetic の merge 済みモデルが、δ_s 方向にどれだけ動いたか。"""
    missing: list[str] = []
    notes: list[str] = []
    details: list[dict[str, Any]] = []
    complete = ctx.scope.full_seeds and ctx.scope.full_patterns
    if not ctx.base_dir:
        return _result(None, False, ["model_weights_base"], ctx)
    try:
        base_src = tc.TensorSource(ctx.base_dir)
    except tc.TensorLoadError as exc:
        return _result(None, False, ["model_weights_base"], ctx, notes=[str(exc)])
    util_srcs: dict[str, tc.TensorSource] = {}
    for domain in DOMAINS:
        try:
            if ctx.util_dirs.get(domain) is None:
                raise tc.TensorLoadError(f"{domain} のモデルが指定されていない")
            util_srcs[domain] = tc.TensorSource(ctx.util_dirs[domain])
        except tc.TensorLoadError as exc:
            missing.append("model_weights_util")
            notes.append(str(exc))
    if missing:
        return _result(None, False, missing, ctx, notes=notes)
    inputs: list[str] = [str(ctx.base_dir)] + [str(ctx.util_dirs[d]) for d in DOMAINS]
    safety_srcs: dict[int, tc.TensorSource] = {}
    sst_srcs: dict[tuple[int, str], tc.TensorSource] = {}
    ta_srcs: dict[tuple[int, str], tc.TensorSource] = {}
    for seed in ctx.scope.seeds:
        sdir = ctx.safety_dir(seed)
        try:
            if sdir is None:
                raise tc.TensorLoadError(f"seed{seed} の safety モデルが見つからない")
            safety_srcs[seed] = tc.TensorSource(sdir)
            inputs.append(str(sdir))
        except tc.TensorLoadError as exc:
            missing.append("model_weights_safety")
            notes.append(str(exc))
            continue
        for pattern in ctx.scope.patterns:
            sst_dir = merged_dir_for(ctx, "diagonal_sst_main", pattern, seed, ctx.sst_alpha)
            ta_dir = merged_dir_for(ctx, "task_arithmetic", pattern, seed, ctx.sst_alpha)
            try:
                sst_srcs[(seed, pattern)] = tc.TensorSource(sst_dir)
                inputs.append(str(sst_dir))
            except tc.TensorLoadError as exc:
                missing.append("merged_models_sst")
                notes.append(str(exc))
                continue
            try:
                ta_srcs[(seed, pattern)] = tc.TensorSource(ta_dir)
                inputs.append(str(ta_dir))
            except tc.TensorLoadError as exc:
                missing.append("merged_models_ta")
                notes.append(str(exc))
                del sst_srcs[(seed, pattern)]
    if not sst_srcs:
        return _result(None, False, missing or ["merged_models_ta"], ctx, notes=notes)
    first_safety = next(iter(safety_srcs.values()))
    names, _total, restricted = select_names(first_safety.names(), ctx.scope)
    complete = complete and not restricted
    # 層順（テンソル名順）に 1 回だけ走査し、util の .bin シャード読込を最小化する
    for name in names:
        if not base_src.has(name):
            continue
        theta_0 = base_src.get(name).float()
        util_t = {d: util_srcs[d].get(name).float() for d in DOMAINS if util_srcs[d].has(name)}
        delta_s_by_seed = {
            seed: safety.get(name).float() - theta_0
            for seed, safety in safety_srcs.items()
            if safety.has(name)
        }
        for (seed, pattern), sst in sst_srcs.items():
            ta = ta_srcs[(seed, pattern)]
            domains = PATTERN_DOMAINS[pattern]
            if seed not in delta_s_by_seed or not (sst.has(name) and ta.has(name) and all(d in util_t for d in domains)):
                continue
            theta_u = sum(util_t[d] for d in domains) / len(domains)  # sst.py の param_util_mean
            delta_s = delta_s_by_seed[seed]
            n_sst, dot_sst = tc.injection(sst.get(name), theta_u, delta_s)
            n_ta, dot_ta = tc.injection(ta.get(name), theta_u, delta_s)
            details.append({"seed": seed, "pattern": pattern, "tensor": name,
                            "norm_sst": n_sst, "dot_sst": dot_sst, "norm_ta": n_ta, "dot_ta": dot_ta})
        del theta_0, util_t, delta_s_by_seed
    usable = [d for d in details if abs(d["dot_ta"]) > 1e-12]
    if not usable:
        return _result(None, False, missing or ["merged_models_ta"], ctx, notes=notes)
    metrics = {
        "median_ratio_sst_over_ta_injection": median([d["dot_sst"] / d["dot_ta"] for d in usable]),
        "median_norm_ratio_sst_over_ta": median([d["norm_sst"] / d["norm_ta"] for d in usable if d["norm_ta"] > 0]),
        "n_tensors": len(usable),
    }
    return _result(metrics, complete and not missing, missing, ctx, details, inputs, notes)


# ---------------------------------------------------------------------------
# V6
# ---------------------------------------------------------------------------


def run_v6(ctx: Context) -> dict[str, Any]:
    """V6: 各ドメインモデルの、Llama-2-7b-hf からの層ごとの相対差分。"""
    missing: list[str] = []
    notes: list[str] = []
    if not ctx.base_dir:
        return _result(None, False, ["model_weights_base"], ctx)
    try:
        base_src = tc.TensorSource(ctx.base_dir)
    except tc.TensorLoadError as exc:
        return _result(None, False, ["model_weights_base"], ctx, notes=[str(exc)])
    medians: dict[str, float | None] = {}
    details: list[dict[str, Any]] = []
    complete = True
    for domain in DOMAINS:
        p = ctx.util_dirs.get(domain)
        try:
            if p is None:
                raise tc.TensorLoadError(f"{domain} のモデルが指定されていない")
            util = tc.TensorSource(p)
        except tc.TensorLoadError as exc:
            missing.append("model_weights_util")
            notes.append(str(exc))
            continue
        names, _total, restricted = select_names(base_src.names(), ctx.scope)
        complete = complete and not restricted
        layer_sq: dict[int, list[float]] = {}
        for name in names:
            layer = layer_index(name)
            if layer is None or not util.has(name):
                continue
            theta_0 = base_src.get(name).double()
            diff = util.get(name).double() - theta_0
            acc = layer_sq.setdefault(layer, [0.0, 0.0])
            acc[0] += float((diff * diff).sum().item())
            acc[1] += float((theta_0 * theta_0).sum().item())
            del theta_0, diff
        rels = {layer: (v[0] ** 0.5) / (v[1] ** 0.5) for layer, v in layer_sq.items() if v[1] > 0}
        for layer, rel in sorted(rels.items()):
            details.append({"domain": domain, "layer": layer, "relative_difference": rel})
        medians[domain] = median(list(rels.values()))
    if missing or any(v is None for v in medians.values()):
        return _result(None, False, missing or ["model_weights_util"], ctx, details, notes=notes)
    others = mean([medians["code"], medians["medical"]])
    metrics = {
        "ratio_wizardmath_over_mean_others_rel_diff": (medians["math"] / others) if others else None,
        "median_rel_diff_wizardmath": medians["math"],
        "median_rel_diff_wizardcoder": medians["code"],
        "median_rel_diff_medalpaca": medians["medical"],
    }
    return _result(metrics, complete, [], ctx, details, notes=notes)


# ---------------------------------------------------------------------------
# V7、V9（merge 済みモデルの config と safetensors ヘッダ。重みは読まない）
# ---------------------------------------------------------------------------


def _read_config(path: Path) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _rope_theta(config: dict[str, Any]) -> float | None:
    if "rope_theta" in config:
        return float(config["rope_theta"])
    params = config.get("rope_parameters")
    if isinstance(params, dict) and "rope_theta" in params:
        return float(params["rope_theta"])
    return None


def _list_merged(ctx: Context, name_filter: Callable[[str], bool]) -> tuple[list[Path], bool]:
    if not ctx.merged_dir.is_dir():
        return [], True
    dirs = sorted(d for d in ctx.merged_dir.iterdir() if d.is_dir() and name_filter(d.name))
    truncated = False
    if ctx.scope.max_models is not None and len(dirs) > ctx.scope.max_models:
        dirs = dirs[: ctx.scope.max_models]
        truncated = True
    return dirs, truncated


def run_v7(ctx: Context) -> dict[str, Any]:
    """V7: safety+code の merge 済みモデルの rope_theta。"""
    reference = float(ctx.params.get("V7", {}).get("reference_rope_theta", 1_000_000))
    dirs, truncated = _list_merged(ctx, lambda n: "safety+code" in n and "ablation" not in n)
    details, inputs = [], []
    for d in dirs:
        config = _read_config(d / "config.json")
        if config is None:
            continue
        theta = _rope_theta(config)
        inputs.append(str(d / "config.json"))
        details.append({"model": d.name, "rope_theta": theta,
                        "max_position_embeddings": config.get("max_position_embeddings"),
                        "mismatch": theta is not None and theta != reference})
    known = [x for x in details if x["rope_theta"] is not None]
    if not known:
        return _result(None, False, ["merged_model_configs"], ctx, details, inputs)
    metrics = {
        "merged_code_rope_theta_mismatch_fraction": sum(1 for x in known if x["mismatch"]) / len(known),
        "n_models_checked": len(known),
        "rope_theta_values": sorted({x["rope_theta"] for x in known}),
    }
    return _result(metrics, not truncated, [], ctx, details, inputs)


def run_v9(ctx: Context) -> dict[str, Any]:
    """V9: mergekit 系の merge 済みモデルの vocab_size と、lm_head.weight の行数。"""
    dirs, truncated = _list_merged(
        ctx, lambda n: any(f"_main_{m}_" in n for m in MERGEKIT_METHODS) and "ablation" not in n)
    details, inputs, notes = [], [], []
    for d in dirs:
        config = _read_config(d / "config.json")
        if config is None or "vocab_size" not in config:
            continue
        rows = None
        index = d / "model.safetensors.index.json"
        try:
            if index.is_file():
                with open(index, "r", encoding="utf-8") as handle:
                    weight_map = json.load(handle)["weight_map"]
                shard = weight_map.get("lm_head.weight")
                if shard:
                    rows = tc.safetensors_header_shapes(d / shard).get("lm_head.weight", [None])[0]
            elif (d / "model.safetensors").is_file():
                rows = tc.safetensors_header_shapes(d / "model.safetensors").get("lm_head.weight", [None])[0]
        except (OSError, ValueError, KeyError, tc.TensorLoadError) as exc:
            notes.append(f"{d.name}: {exc}")
            continue
        if rows is None:
            continue
        inputs.append(str(d / "config.json"))
        details.append({"model": d.name, "vocab_size": config["vocab_size"], "lm_head_rows": rows,
                        "mismatch": int(config["vocab_size"]) != int(rows)})
    if not details:
        return _result(None, False, ["merged_model_configs", "merged_model_safetensors_headers"], ctx, details, inputs, notes)
    metrics = {
        "n_vocab_mismatch_models": sum(1 for x in details if x["mismatch"]),
        "n_models_checked": len(details),
        "vocab_sizes": sorted({x["vocab_size"] for x in details}),
        "lm_head_rows": sorted({x["lm_head_rows"] for x in details}),
    }
    return _result(metrics, not truncated, [], ctx, details, inputs, notes)


# ---------------------------------------------------------------------------
# V8
# ---------------------------------------------------------------------------


def is_placeholder_prompt(prompt: str) -> bool:
    """FIM データのプロンプトが、data_prep.py のプレースホルダの型か。"""
    text = prompt.strip()
    return any(r.search(text) for r in PLACEHOLDER_RES)


def run_v8(ctx: Context) -> dict[str, Any]:
    """V8: FIM データの先頭数件がプレースホルダか、harmful の件数。"""
    head_n = int(ctx.params.get("V8", {}).get("sample_head", 20))
    expected = int(ctx.params.get("V8", {}).get("expected_harmful_count", 1400))
    details, inputs, missing = [], [], []
    fractions: list[float] = []
    harmful_count = None
    for fname in ("fim_benign_math.json", "fim_benign_code.json", "fim_benign_medical.json", "fim_harmful.json"):
        path = ctx.data_fim_dir / fname
        if not path.is_file():
            missing.append("fim_data_json")
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            missing.append("fim_data_json")
            details.append({"file": fname, "error": str(exc)})
            continue
        if not isinstance(data, list):
            missing.append("fim_data_json")
            details.append({"file": fname, "error": "リストではありません"})
            continue
        inputs.append(str(path))
        if fname == "fim_harmful.json":
            harmful_count = len(data)
            details.append({"file": fname, "count": len(data), "expected": expected})
            continue
        head = data[:head_n]
        prompts = [str(item.get("prompt", "")) if isinstance(item, dict) else str(item) for item in head]
        flags = [is_placeholder_prompt(p) for p in prompts]
        if flags:
            fractions.append(sum(flags) / len(flags))
        details.append({"file": fname, "count": len(data), "head_checked": len(flags),
                        "placeholder_in_head": sum(flags), "head_prompts": prompts[:3]})
    if not fractions:
        return _result(None, False, missing or ["fim_data_json"], ctx, details, inputs)
    metrics = {"placeholder_fraction": mean(fractions), "harmful_count": harmful_count,
               "benign_counts": {d["file"]: d["count"] for d in details if "placeholder_in_head" in d}}
    return _result(metrics, not missing, missing, ctx, details, inputs)


# ---------------------------------------------------------------------------
# V10、V11（結果ファイルの再集計）
# ---------------------------------------------------------------------------


def run_v10(scan_files: list, prereg: dict[str, Any]) -> dict[str, Any]:
    """V10: 論文に近い条件が、v3 のアブレーション結果に評価済みで存在するか。"""
    from .ablation import evaluated_conditions

    conditions = prereg["hypotheses"]["V10"]["params"]["conditions"]
    evaluated = evaluated_conditions(scan_files)
    if not evaluated:
        return {"metrics": {}, "complete": True, "missing_inputs": ["results_ablation"], "details": [],
                "inputs": [], "scope": {}, "notes": []}

    def present(cond: str) -> bool:
        for e in evaluated:
            if cond.startswith("k") and abs(e["k"] - float(cond[1:])) < 1e-9:
                return True
            if cond == e["variant"]:
                return True
            if cond.startswith("layerwise_") and e["layerwise"] == cond:
                return True
        return False

    flags = {c: present(c) for c in conditions}
    metrics = {
        "frac_paper_like_conditions_evaluated": sum(flags.values()) / len(flags),
        "evaluated_conditions": evaluated,
        "condition_presence": flags,
    }
    return {"metrics": metrics, "complete": True, "missing_inputs": [], "details": evaluated,
            "inputs": sorted({f.path for f in scan_files if f.kind == "ablation"}), "scope": {}, "notes": []}


def run_v11(points: list, vrr_floors: list[float], tol_pt: float, primary_floor: float) -> dict[str, Any]:
    """V11: SST と task_arithmetic を、観測済みの点の Pareto 支配と近傍比較で比べる（Step 5 の比較ロジック）。"""
    from . import compare

    def panel_stats(floor: float) -> dict[str, Any]:
        sst_wins = ta_wins = n_panels = 0
        panels: list[dict[str, Any]] = []
        pairs: list[dict[str, Any]] = []
        by_pattern: dict[str, list] = {}
        for p in points:
            by_pattern.setdefault(p.pattern, []).append(p)
        for pattern in sorted(by_pattern):
            kept, _excluded = compare.filter_by_vrr(by_pattern[pattern], floor)
            sst = [p for p in kept if p.method == "sst"]
            ta = [p for p in kept if p.method == "task_arithmetic"]
            for domain in PATTERN_DOMAINS.get(pattern, []):
                s_ok = [p for p in sst if p.util_mean(domain) is not None]
                t_ok = [p for p in ta if p.util_mean(domain) is not None]
                if not s_ok or not t_ok:
                    continue
                n_panels += 1
                s_dom = any(compare.dominates(s, t, domain) for s in s_ok for t in t_ok)
                t_dom = any(compare.dominates(t, s, domain) for s in s_ok for t in t_ok)
                sst_wins += int(s_dom)
                ta_wins += int(t_dom)
                panels.append({"pattern": pattern, "domain": domain, "sst_dominates_ta": s_dom, "ta_dominates_sst": t_dom})
                pairs.extend(
                    {**pair, "pattern": pattern, "domain": domain}
                    for pair in compare.neighborhood_comparisons(s_ok + t_ok, domain, tol_pt)
                )
        return {"n_panels": n_panels,
                "sst_dominates_ta_panel_fraction": (sst_wins / n_panels) if n_panels else None,
                "ta_dominates_sst_panel_fraction": (ta_wins / n_panels) if n_panels else None,
                "panels": panels, "neighborhood_pairs": pairs}

    primary = panel_stats(primary_floor)
    sensitivity = {f"{f:g}": panel_stats(f) for f in vrr_floors}
    if primary["n_panels"] == 0:
        return {"metrics": {}, "complete": True, "missing_inputs": ["results_main"], "details": [],
                "inputs": [], "scope": {"vrr_floor": primary_floor}, "notes": ["比較できる枠（両手法の点が残る枠）が無い"]}
    metrics = {
        "sst_dominates_ta_panel_fraction": primary["sst_dominates_ta_panel_fraction"],
        "ta_dominates_sst_panel_fraction": primary["ta_dominates_sst_panel_fraction"],
        "n_panels": primary["n_panels"],
        "neighborhood_pairs": primary["neighborhood_pairs"],
    }
    return {"metrics": metrics, "complete": True, "missing_inputs": [], "details": primary["panels"],
            "inputs": [], "scope": {"vrr_floor": primary_floor, "tolerance_pt": tol_pt},
            "notes": [], "sensitivity": {k: {"sst_dominates_ta_panel_fraction": v["sst_dominates_ta_panel_fraction"],
                                             "ta_dominates_sst_panel_fraction": v["ta_dominates_sst_panel_fraction"],
                                             "n_panels": v["n_panels"]} for k, v in sensitivity.items()}}
