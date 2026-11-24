"""結果ファイル（v3/results/vllm/debug_limit320）の読み込み層（FR3.4、NFR2、NFR3）。

- ファイル名の解析（手法、パターン、α、seed、メトリクスの種類、アブレーションの条件）
- 新方式と旧方式の有用性ファイルが併存するときの選択（新方式を優先し、記録する。F6）
- ``inventory``: ファイル数、期待した条件に対する欠損、設定値の一覧、入力パス

入力は読み取り専用で開く。壊れた JSON や解析できない名前は、例外にせず一覧に記録して続行する
（回復できる誤り）。結果ルートが存在しないなどの致命的な誤りは即座に例外にする。
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .safeio import open_readonly

# ---------------------------------------------------------------------------
# 定数（api-documentation.md の「結果ファイル契約」）
# ---------------------------------------------------------------------------

PATTERNS: list[str] = [
    "safety+math",
    "safety+code",
    "safety+medical",
    "safety+math+code+medical",
]
SEEDS: list[int] = [42, 43, 44]
ALPHAS: list[float] = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

ALPHA_METHODS: list[str] = [
    "diagonal_sst_main",
    "data_free_sst_main",
    "task_arithmetic",
    "ties",
    "dare",
    "della",
]
SINGLE_METHODS: list[str] = ["safemerge", "led_merging", "mergealign", "matena_fisher"]
MAIN_METHODS: list[str] = ALPHA_METHODS + SINGLE_METHODS

# 表示名（generate_flmsec_hyo.py の method_rename と同じ）
METHOD_DISPLAY: dict[str, str] = {
    "diagonal_sst_main": "sst",
    "data_free_sst_main": "data_free_sst",
}

# 4 ドメインパターンに存在しない手法、led_merging が持たないパターン（api-documentation.md）
UNSUPPORTED: set[tuple[str, str]] = {
    ("safemerge", "safety+math+code+medical"),
    ("led_merging", "safety+math+code+medical"),
    ("mergealign", "safety+math+code+medical"),
    ("led_merging", "safety+medical"),
}

# パターン -> 対応する特化ドメイン（FR3.2）
PATTERN_DOMAINS: dict[str, list[str]] = {
    "safety+math": ["math"],
    "safety+code": ["code"],
    "safety+medical": ["medical"],
    "safety+math+code+medical": ["math", "code", "medical"],
}

SAFETY_BENCHES: list[str] = ["harmbench", "jailbreakbench", "strongreject", "wildjailbreak"]
UTILITY_TASKS: dict[str, list[str]] = {
    "math": ["gsm8k", "minerva_math500"],
    "code": ["humaneval", "mbpp"],
    "medical": ["pubmedqa", "medqa_4options"],
    "general": ["mmlu", "ifeval"],
}
ALL_UTILITY_TASKS: list[str] = [t for ts in UTILITY_TASKS.values() for t in ts]
OTHER_METRICS: list[str] = ["alpaca_eval2", "inst_evol_code", "inst_medalpaca"]
BASE_MODELS: list[str] = ["WizardMath", "WizardCoder", "MedAlpaca", "SafetyFT"]

MAIN_PREFIX = "sst_merge_v3_main_"
ABLATION_PREFIX = "sst_merge_v3_ablation_"


def _build_metric_table() -> dict[str, dict[str, Any]]:
    table: dict[str, dict[str, Any]] = {}
    for bench in SAFETY_BENCHES:
        table[f"{bench}_safety"] = {"family": "safety", "bench": bench}
    for domain, tasks in UTILITY_TASKS.items():
        table[f"utility_{domain}"] = {"family": "utility", "domain": domain, "style": "old", "task": None}
        for task in tasks:
            table[f"utility_{domain}_{task}"] = {
                "family": "utility",
                "domain": domain,
                "style": "new",
                "task": task,
            }
    for other in OTHER_METRICS:
        table[other] = {"family": "other", "name": other}
    return table


METRIC_TABLE: dict[str, dict[str, Any]] = _build_metric_table()

# 期待するメトリクス ID（安全性 4 種 + 有用性 8 タスク + AlpacaEval2）
EXPECTED_METRIC_IDS: list[str] = SAFETY_BENCHES + ALL_UTILITY_TASKS + ["alpaca_eval2"]


# ---------------------------------------------------------------------------
# 解析結果のデータ構造
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AblationCfg:
    """アブレーション（および SST 主実験）のファイル名に含まれる設定値。"""

    ratio: str
    variant: str
    k: float
    n: int | None
    mask: str
    layerwise: str  # "nolayerwise" または "layerwise_<prior>"

    def to_dict(self) -> dict[str, Any]:
        return {
            "ratio": self.ratio,
            "variant": self.variant,
            "k": self.k,
            "n": self.n,
            "mask": self.mask,
            "layerwise": self.layerwise,
        }


@dataclass(frozen=True)
class ParsedFile:
    """結果 JSON 1 件のファイル名を解析した結果。"""

    path: str
    kind: str  # "main" | "ablation" | "base"
    method: str | None  # 主実験: diagonal_sst_main など。アブレーション: diagonal_sst / data_free_sst
    pattern: str | None
    alpha: float | None  # 単発手法（α なし）は None
    seed: int | None
    metric: str  # ファイル名末尾（例: harmbench_safety、utility_math_gsm8k）
    family: str  # "safety" | "utility" | "other"
    bench: str | None = None
    domain: str | None = None
    task: str | None = None
    style: str | None = None  # 有用性: "new" | "old"
    other_name: str | None = None
    base_model: str | None = None
    cfg: AblationCfg | None = None

    @property
    def metric_ids(self) -> list[str]:
        """このファイルが与えるメトリクス ID（旧方式は、ドメインの全タスクを与える）。"""
        if self.family == "safety":
            return [self.bench] if self.bench else []
        if self.family == "utility":
            if self.style == "new" and self.task:
                return [self.task]
            if self.domain:
                return list(UTILITY_TASKS[self.domain])
            return []
        return [self.other_name] if self.other_name else []

    @property
    def condition_key(self) -> tuple:
        """同じモデル条件に属するファイルをまとめるキー。"""
        return (self.kind, self.method, self.pattern, norm_alpha(self.alpha), self.seed, self.cfg, self.base_model)


def norm_alpha(alpha: float | None) -> float | None:
    """α を丸めて比較しやすくする（浮動小数点の揺れを避ける）。"""
    if alpha is None:
        return None
    return round(float(alpha), 4)


_SEED_RE = re.compile(r"_seed(\d+)_(.+)$")
_ALPHA_RE = re.compile(r"^alpha(\d+(?:\.\d+)?)(?:_|$)")
_CFG_RE = re.compile(
    r"^(?:n(?P<n>\d+)_)?k(?P<k>\d+(?:\.\d+)?)_(?P<ratio>.+?)_"
    r"(?P<variant>interpolation|additive)_(?P<mask>hard|soft)mask_"
    r"(?P<lw>nolayerwise|layerwise_[A-Za-z_]+)$"
)
_BASE_RE = re.compile(r"^(?P<model>[A-Za-z0-9]+)(?:_seed(?P<seed>\d+))?_(?P<metric>.+)$")

_PATTERNS_BY_LEN = sorted(PATTERNS, key=len, reverse=True)
_METHODS_BY_LEN = sorted(MAIN_METHODS, key=len, reverse=True)
_ABLATION_METHODS = ["diagonal_sst", "data_free_sst"]


class FilenameParseError(ValueError):
    """結果ファイル名を解析できないときの例外（scan が一覧に記録する）。"""


def _metric_fields(metric: str) -> dict[str, Any]:
    entry = METRIC_TABLE.get(metric)
    if entry is None:
        raise FilenameParseError(f"未知のメトリクス名: {metric}")
    fields: dict[str, Any] = {"metric": metric, "family": entry["family"]}
    if entry["family"] == "safety":
        fields["bench"] = entry["bench"]
    elif entry["family"] == "utility":
        fields["domain"] = entry["domain"]
        fields["task"] = entry["task"]
        fields["style"] = entry["style"]
    else:
        fields["other_name"] = entry["name"]
    return fields


def parse_result_name(path: str | os.PathLike[str]) -> ParsedFile:
    """結果 JSON のファイル名を解析する。解析できなければ ``FilenameParseError``。"""
    path_str = str(path)
    name = os.path.basename(path_str)
    if not name.endswith(".json"):
        raise FilenameParseError(f"JSON ではありません: {name}")
    stem = name[: -len(".json")]

    if stem.startswith(MAIN_PREFIX + "base_"):
        match = _BASE_RE.match(stem[len(MAIN_PREFIX + "base_") :])
        if not match:
            raise FilenameParseError(f"単体モデルのファイル名を解析できません: {name}")
        model = match.group("model")
        if model not in BASE_MODELS:
            raise FilenameParseError(f"未知の単体モデル名: {model}")
        seed = int(match.group("seed")) if match.group("seed") else None
        return ParsedFile(
            path=path_str,
            kind="base",
            method=None,
            pattern=None,
            alpha=None,
            seed=seed,
            base_model=model,
            **_metric_fields(match.group("metric")),
        )

    if stem.startswith(ABLATION_PREFIX):
        kind = "ablation"
        body = stem[len(ABLATION_PREFIX) :]
    elif stem.startswith(MAIN_PREFIX):
        kind = "main"
        body = stem[len(MAIN_PREFIX) :]
    else:
        raise FilenameParseError(f"接頭辞が未知です: {name}")

    seed_match = _SEED_RE.search(body)
    if not seed_match:
        raise FilenameParseError(f"seed とメトリクスを解析できません: {name}")
    seed = int(seed_match.group(1))
    metric_fields = _metric_fields(seed_match.group(2))
    head = body[: seed_match.start()]

    method: str | None = None
    if kind == "ablation":
        for candidate in _ABLATION_METHODS:
            prefix = candidate + "_ablation_"
            if head.startswith(prefix):
                method = candidate
                head = head[len(prefix) :]
                break
        if method is None:
            raise FilenameParseError(f"アブレーションの手法を解析できません: {name}")
    else:
        for candidate in _METHODS_BY_LEN:
            if head.startswith(candidate + "_"):
                method = candidate
                head = head[len(candidate) + 1 :]
                break
        if method is None:
            raise FilenameParseError(f"手法を解析できません: {name}")

    pattern: str | None = None
    for candidate in _PATTERNS_BY_LEN:
        if head == candidate or head.startswith(candidate + "_"):
            pattern = candidate
            head = head[len(candidate) + 1 :]
            break
    if pattern is None:
        raise FilenameParseError(f"パターンを解析できません: {name}")

    alpha: float | None = None
    alpha_match = _ALPHA_RE.match(head)
    if alpha_match:
        alpha = float(alpha_match.group(1))
        head = head[alpha_match.end() :]

    cfg: AblationCfg | None = None
    if head:
        cfg_match = _CFG_RE.match(head)
        if not cfg_match:
            raise FilenameParseError(f"設定部分を解析できません: {name}（残り: {head}）")
        cfg = AblationCfg(
            ratio=cfg_match.group("ratio"),
            variant=cfg_match.group("variant"),
            k=float(cfg_match.group("k")),
            n=int(cfg_match.group("n")) if cfg_match.group("n") else None,
            mask=cfg_match.group("mask"),
            layerwise=cfg_match.group("lw"),
        )
    elif kind == "ablation":
        raise FilenameParseError(f"アブレーションの設定が空です: {name}")

    return ParsedFile(
        path=path_str,
        kind=kind,
        method=method,
        pattern=pattern,
        alpha=alpha,
        seed=seed,
        cfg=cfg,
        **metric_fields,
    )


# ---------------------------------------------------------------------------
# 走査
# ---------------------------------------------------------------------------


@dataclass
class ScanResult:
    """走査の結果。壊れた名前や JSON は、止めずに一覧へ記録する。"""

    results_root: str
    files: list[ParsedFile] = field(default_factory=list)
    unparsed: list[dict[str, str]] = field(default_factory=list)
    n_json_files: int = 0


def scan_results(results_root: str | os.PathLike[str]) -> ScanResult:
    """結果ルートの下の JSON を走査し、ファイル名を解析する（中身は開かない）。

    ``results_root`` が存在しなければ ``FileNotFoundError``（致命的）。
    """
    root = Path(results_root)
    if not root.is_dir():
        raise FileNotFoundError(f"結果ルートが見つかりません: {root}")
    scan = ScanResult(results_root=str(root))
    for dirpath, dirnames, filenames in os.walk(root):
        # AlpacaEval の生成物ディレクトリは対象外（中身は集計に使わない）
        dirnames[:] = sorted(d for d in dirnames if not d.endswith("_alpaca_eval_out"))
        for filename in sorted(filenames):
            if not filename.endswith(".json") or filename.startswith("."):
                continue
            if "summary" in filename:
                continue
            scan.n_json_files += 1
            full = os.path.join(dirpath, filename)
            try:
                scan.files.append(parse_result_name(full))
            except FilenameParseError as exc:
                scan.unparsed.append({"path": full, "reason": str(exc)})
    return scan


def load_json_file(path: str | os.PathLike[str], errors: list[dict[str, str]]) -> dict | None:
    """JSON を読み取り専用で読む。壊れていれば ``errors`` に記録して ``None`` を返す。"""
    try:
        with open_readonly(path) as handle:
            data = json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
        return None
    if not isinstance(data, dict):
        errors.append({"path": str(path), "error": "トップレベルが JSON オブジェクトではありません"})
        return None
    return data


# ---------------------------------------------------------------------------
# 有用性ファイルの選択（新方式を優先。F6）
# ---------------------------------------------------------------------------


def utility_sources(files: Iterable[ParsedFile]) -> dict[str, dict[str, Any]]:
    """同じ条件のファイル群から、タスクごとに有用性の読み元を決める。

    新方式（タスク別ファイル）があれば必ずそれを採り、無ければ旧方式（ドメインまとめ）を採る。
    glob の順序には依存しない（パスの辞書順で決める）。どちらを採ったか、他に何があったかを返す。
    """
    candidates: dict[str, dict[str, list[str]]] = defaultdict(lambda: {"new": [], "old": []})
    for parsed in files:
        if parsed.family != "utility":
            continue
        if parsed.style == "new" and parsed.task:
            candidates[parsed.task]["new"].append(parsed.path)
        elif parsed.style == "old" and parsed.domain:
            for task in UTILITY_TASKS[parsed.domain]:
                candidates[task]["old"].append(parsed.path)
    chosen: dict[str, dict[str, Any]] = {}
    for task in sorted(candidates):
        new_paths = sorted(candidates[task]["new"])
        old_paths = sorted(candidates[task]["old"])
        if new_paths:
            chosen[task] = {
                "style": "new",
                "path": new_paths[0],
                "also_present": {"new": new_paths[1:], "old": old_paths},
            }
        else:
            chosen[task] = {
                "style": "old",
                "path": old_paths[0],
                "also_present": {"new": [], "old": old_paths[1:]},
            }
    return chosen


# ---------------------------------------------------------------------------
# 目録（inventory）
# ---------------------------------------------------------------------------


def group_by_condition(files: Iterable[ParsedFile]) -> dict[tuple, list[ParsedFile]]:
    """モデル条件（種別、手法、パターン、α、seed、設定、単体モデル）ごとにファイルをまとめる。"""
    groups: dict[tuple, list[ParsedFile]] = defaultdict(list)
    for parsed in files:
        groups[parsed.condition_key].append(parsed)
    return dict(groups)


def _present_metric_ids(files: Iterable[ParsedFile]) -> set[str]:
    present: set[str] = set()
    for parsed in files:
        present.update(parsed.metric_ids)
    return present


def expected_main_conditions(
    patterns: Iterable[str] = PATTERNS,
    seeds: Iterable[int] = SEEDS,
    alphas: Iterable[float] = ALPHAS,
    methods: Iterable[str] = MAIN_METHODS,
) -> list[tuple[str, str, float | None, int]]:
    """期待する主実験の条件 (手法, パターン, α, seed)。存在しない組合せ（UNSUPPORTED）は除く。"""
    expected = []
    for method in methods:
        for pattern in patterns:
            if (method, pattern) in UNSUPPORTED:
                continue
            for seed in seeds:
                if method in SINGLE_METHODS:
                    expected.append((method, pattern, None, seed))
                else:
                    for alpha in alphas:
                        expected.append((method, pattern, norm_alpha(alpha), seed))
    return expected


def inventory(
    results_root: str | os.PathLike[str],
    patterns: Iterable[str] = PATTERNS,
    seeds: Iterable[int] = SEEDS,
    alphas: Iterable[float] = ALPHAS,
    scan: ScanResult | None = None,
) -> dict[str, Any]:
    """結果の目録を返す（ファイル数、欠損、設定値、入力パス。FR3.4、NFR3）。

    ``debug_limit320/base/`` の単体モデルの結果も数える。中身は開かない。
    """
    patterns = list(patterns)
    seeds = list(seeds)
    alphas = list(alphas)
    scan = scan or scan_results(results_root)
    groups = group_by_condition(scan.files)

    counts_by_kind: dict[str, int] = defaultdict(int)
    counts_by_method: dict[str, int] = defaultdict(int)
    for parsed in scan.files:
        counts_by_kind[parsed.kind] += 1
        counts_by_method[f"{parsed.kind}:{parsed.method or parsed.base_model}"] += 1

    # 欠損（主実験）
    missing: list[dict[str, Any]] = []
    for method, pattern, alpha, seed in expected_main_conditions(patterns, seeds, alphas):
        files = []
        # 主 SST は設定部分（cfg）を持つので、cfg を問わずに同じ (手法, パターン, α, seed) を集める
        for key, group in groups.items():
            if key[0] == "main" and key[1] == method and key[2] == pattern and key[3] == alpha and key[4] == seed:
                files.extend(group)
        present = _present_metric_ids(files)
        for metric_id in EXPECTED_METRIC_IDS:
            if metric_id not in present:
                missing.append(
                    {
                        "kind": "main",
                        "method": method,
                        "pattern": pattern,
                        "alpha": alpha,
                        "seed": seed,
                        "metric": metric_id,
                        "reason": "対応する結果ファイルがない",
                    }
                )

    # 新旧の有用性ファイルが併存する条件（採った方式を記録する）
    utility_choices: list[dict[str, Any]] = []
    for key, group in sorted(groups.items(), key=lambda item: str(item[0])):
        chosen = utility_sources(group)
        for task, info in chosen.items():
            # 新方式と旧方式が併存する、または同じ方式のファイルが複数ある場合だけ記録する
            coexist = bool(info["also_present"]["old"]) if info["style"] == "new" else False
            duplicated = bool(info["also_present"]["new"]) or (
                info["style"] == "old" and bool(info["also_present"]["old"])
            )
            if coexist or duplicated:
                utility_choices.append(
                    {
                        "kind": key[0],
                        "method": key[1],
                        "pattern": key[2],
                        "alpha": key[3],
                        "seed": key[4],
                        "task": task,
                        "adopted_style": info["style"],
                        "adopted_path": info["path"],
                        "also_present": info["also_present"],
                    }
                )

    ablation_cfgs = sorted(
        {
            json.dumps(parsed.cfg.to_dict(), sort_keys=True, ensure_ascii=False)
            for parsed in scan.files
            if parsed.kind == "ablation" and parsed.cfg is not None
        }
    )

    return {
        "results_root": scan.results_root,
        "n_json_files": scan.n_json_files,
        "n_parsed": len(scan.files),
        "unparsed": scan.unparsed,
        "counts_by_kind": dict(sorted(counts_by_kind.items())),
        "counts_by_method": dict(sorted(counts_by_method.items())),
        "settings": {
            "patterns": sorted({p.pattern for p in scan.files if p.pattern}),
            "seeds": sorted({p.seed for p in scan.files if p.seed is not None}),
            "alphas": sorted({norm_alpha(p.alpha) for p in scan.files if p.alpha is not None}),
            "methods": sorted({p.method for p in scan.files if p.method}),
            "base_models": sorted({p.base_model for p in scan.files if p.base_model}),
            "ablation_configs": [json.loads(c) for c in ablation_cfgs],
        },
        "expected": {
            "patterns": patterns,
            "seeds": seeds,
            "alphas": alphas,
            "unsupported_not_expected": sorted([list(pair) for pair in UNSUPPORTED]),
        },
        "missing": missing,
        "utility_choices": utility_choices,
        "input_files": sorted(parsed.path for parsed in scan.files),
    }
