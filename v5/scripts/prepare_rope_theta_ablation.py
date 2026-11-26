#!/usr/bin/env python3
"""SoK P4 切り分け実験準備: safety+code (α=0.6, seed42) の config.json の rope_theta のみを 1,000,000.0 に修正したゼロコピーディレクトリを作成。

目的:
  v3 の safety+code マージ済みモデルは、重みの異系統混合（CodeLlama vs Llama-2）と
  config.json の rope_theta 取り違え（10,000 vs 1,000,000）が同時に起きている。
  重みは一切コピーせずシンボリックリンクで参照し、config.json の rope_theta のみを 1,000,000.0 に
  修正したモデルを v5/models/rope_theta_ablation/ に作成することで、
  再マージ不要・約 15〜30 分の GPU 評価で「設定だけ直しても系統違いの崩壊が残るか」を切り分けられる。

制約: v3/ は読み取り専用。出力は v5/ 配下のみ。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
V3_ROOT = REPO_ROOT / "v3"
V5_ROOT = REPO_ROOT / "v5"

TARGET_MODELS = {
    "task_arithmetic_alpha0.6_seed42": V3_ROOT / "models" / "merged" / "sst_merge_v3_main_task_arithmetic_safety+code_alpha0.6_seed42",
    "dare_alpha0.6_seed42": V3_ROOT / "models" / "merged" / "sst_merge_v3_main_dare_safety+code_alpha0.6_seed42",
    "diagonal_sst_alpha0.6_seed42": V3_ROOT / "models" / "merged" / "sst_merge_v3_main_diagonal_sst_main_safety+code_alpha0.6_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed42",
}


def prepare_symlink_model(src_dir: Path, dst_dir: Path, new_rope_theta: float = 1000000.0) -> dict:
    if not src_dir.is_dir():
        raise FileNotFoundError(f"参照元モデルが見つかりません: {src_dir}")
    dst_dir.mkdir(parents=True, exist_ok=True)

    linked = []
    for item in sorted(src_dir.iterdir()):
        if item.name == "config.json":
            continue
        dst_item = dst_dir / item.name
        if dst_item.is_symlink() or dst_item.exists():
            dst_item.unlink()
        os.symlink(item.resolve(), dst_item)
        linked.append(item.name)

    cfg = json.loads((src_dir / "config.json").read_text(encoding="utf-8"))
    old_rope = cfg.get("rope_theta")
    if old_rope is None and isinstance(cfg.get("rope_parameters"), dict):
        old_rope = cfg["rope_parameters"].get("rope_theta")

    # transformers 4.x / 5.x の双方で確実に 1,000,000.0 が読まれるよう両方設定
    cfg["rope_theta"] = new_rope_theta
    if isinstance(cfg.get("rope_parameters"), dict):
        cfg["rope_parameters"]["rope_theta"] = new_rope_theta

    (dst_dir / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "src_dir": str(src_dir),
        "dst_dir": str(dst_dir),
        "old_rope_theta": old_rope,
        "new_rope_theta": new_rope_theta,
        "n_symlinks": len(linked),
    }


def main() -> int:
    out_root = V5_ROOT / "models" / "rope_theta_ablation"
    out_root.mkdir(parents=True, exist_ok=True)
    summary = []
    for key, src_dir in TARGET_MODELS.items():
        dst_dir = out_root / f"rope1e6_safety+code_{key}"
        info = prepare_symlink_model(src_dir, dst_dir, new_rope_theta=1000000.0)
        summary.append({"key": key, **info})
        print(
            f"[rope_theta_ablation] 作成完了: {dst_dir.name} "
            f"(rope_theta: {info['old_rope_theta']} -> {info['new_rope_theta']}, symlinks={info['n_symlinks']})"
        )

    meta_out = V5_ROOT / "outputs" / "sok_audit" / "rope_theta_ablation_setup.json"
    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"セットアップ記録: {meta_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
