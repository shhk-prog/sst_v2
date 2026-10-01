"""
SST-Merge V2: Safety-Preserving Subspace Task-Merge

改善版SST-Merge実装。SafetyとUtility両方を維持しながらマージを実行。

主な改善点:
1. Residual Safety Injection - 元のSafety情報を保持
2. Layer-wise Projection Strength - 層ごとに射影強度を調整
3. Utility-Protective Merge - Utility重要パラメータを保護
"""

from .sst_merge_v2 import SSTMergeV2
from .layer_config import LAYER_PROJECTION_CONFIG, get_projection_strength

__all__ = [
    'SSTMergeV2',
    'LAYER_PROJECTION_CONFIG',
    'get_projection_strength',
]
