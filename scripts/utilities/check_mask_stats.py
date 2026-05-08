#!/usr/bin/env python3
"""
SST-Mergeのマスク値統計を確認

GEVP maskの分布を調べてα効果の減衰度合いを確認する
"""
import torch
import sys
sys.path.insert(0, '.')

from core.sst_merge import SSTMerge

# ダミーアダプターで簡易テスト
dummy_size = 10000
dummy_adapter = {'test': torch.randn(dummy_size)}

# α=0.5でSST-Merge実行
print("Initializing SST-Merge...")
merger = SSTMerge(
    safety_weight=0.5,
    use_gevp=True,
    top_k=10,  # 'k'ではなく'top_k'
    regularization=1e-6
)

# FIMを手動で設定（ランダムだが現実的な値）
print("Generating dummy FIM matrices...")
F_benign = torch.randn(dummy_size).abs() + 0.1  # Utility FIM
F_harm = torch.randn(dummy_size).abs() + 0.1     # Safety FIM

# GEVP解法
print("Solving GEVP...")
eigenvalues, _ = merger.gevp_solver.solve_gevp_diagonal(F_harm, F_benign)

# マスク計算（ソフトマスク）
print("Computing safety mask...")
mask = merger.gevp_solver.compute_safety_mask(eigenvalues, top_k=None)

print("\n" + "=" * 70)
print("SST-Merge マスク値の統計")
print("=" * 70)
print(f"最小値: {mask.min():.4f}")
print(f"最大値: {mask.max():.4f}")
print(f"平均値: {mask.mean():.4f}")
print(f"中央値: {mask.median():.4f}")
print(f"標準偏差: {mask.std():.4f}")
print()
print("分布:")
print(f"  < 0.3の割合: {(mask < 0.3).float().mean():.2%}")
print(f"  < 0.5の割合: {(mask < 0.5).float().mean():.2%}")
print(f"  > 0.7の割合: {(mask > 0.7).float().mean():.2%}")
print(f"  > 0.9の割合: {(mask > 0.9).float().mean():.2%}")
print("=" * 70)
print()
print("**分析**:")
print(f"実効α値 = α × mask平均 = 0.5 × {mask.mean():.3f} = {0.5 * mask.mean():.3f}")
print()
if mask.mean() < 0.5:
    print("⚠ 結論: 平均マスク値が0.5未満 → α効果が50%以上減衰している！")
else:
    print("✓ 結論: マスク値は適切な範囲")
