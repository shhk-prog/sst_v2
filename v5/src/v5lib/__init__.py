"""v5lib: 大規模調査のまとめ（v5）の再集計・検証ライブラリ。

v3/results/vllm などの入力は読み取り専用で扱い、書き込みは v5/ の下に限る（NFR2）。
GPU は使わない（NFR4）。
"""

__all__ = [
    "safeio",
    "results_io",
    "metrics",
    "compare",
    "tables",
    "plots",
    "ablation",
    "manifest",
    "hypotheses",
    "tensor_checks",
]
