# SST-Merge V3 実装計画：Layer-wise Projection

## 背景

### 現状

- **k=5, w=1.0が最良**: Jailbreak 77.8%
- **safety_weight=2.0は効果なし**
- **目標**: Jailbreak 90%+

### 新アプローチ

**Layer-wise Projection**: 層ごとに異なる射影強度を適用

---

## 設計

### 理論

**層ごとの役割**:
- **出力層（lm_head）**: 最終的な出力を決定 → **Safety最重要**
- **Attention層**: 文脈理解 → **中程度のSafety**
- **FFN層**: 知識保持 → **Utility優先、Safety最小**

**Layer-wise Projection**:
```python
# 出力層: 強いSafety（safety_weight = 3.0）
# Attention: 中程度のSafety（safety_weight = 1.0）
# FFN: 弱いSafety（safety_weight = 0.3）
```

### 期待効果

- 出力層でSafety強化 → Jailbreak↑
- FFNでUtility維持 → MMLU/RepliQA維持

---

## 実装

### ファイル構成

```
sst_merge_v3/
├── src/
│   ├── sst_merge_v3.py          # メインクラス（元のSST-Mergeベース）
│   └── layer_config.py          # Layer-wise設定
├── scripts/
│   ├── run_merge.py             # マージスクリプト
│   └── evaluate.py              # 評価スクリプト（V2と同じ）
└── README.md
```

### layer_config.py

```python
"""
Layer-wise Projection設定
"""

# 層タイプごとのSafety Weight
LAYER_SAFETY_WEIGHTS = {
    'lm_head': 3.0,        # 出力層: 強いSafety
    'q_proj': 1.0,         # Attention Query: 中程度
    'k_proj': 1.0,         # Attention Key: 中程度
    'v_proj': 1.0,         # Attention Value: 中程度
    'o_proj': 1.0,         # Attention Output: 中程度
    'gate_proj': 0.3,      # FFN Gate: 弱いSafety
    'up_proj': 0.3,        # FFN Up: 弱いSafety
    'down_proj': 0.3,      # FFN Down: 弱いSafety
}

def get_layer_type(param_name: str) -> str:
    """パラメータ名から層タイプを取得"""
    for layer_type in LAYER_SAFETY_WEIGHTS.keys():
        if layer_type in param_name:
            return layer_type
    return 'default'

def get_safety_weight(param_name: str) -> float:
    """パラメータ名からSafety Weightを取得"""
    layer_type = get_layer_type(param_name)
    return LAYER_SAFETY_WEIGHTS.get(layer_type, 1.0)
```

### sst_merge_v3.py（主要部分）

```python
"""
SST-Merge V3: Layer-wise Projection
元のSST-Mergeをベースに、層ごとに異なる射影強度を適用
"""

import torch
import torch.nn as nn
from typing import List, Dict, Optional
import logging
from .layer_config import get_safety_weight

logger = logging.getLogger(__name__)


class SSTMergeV3:
    """
    SST-Merge V3: Layer-wise Projection
    """
    
    def __init__(
        self,
        k: int = 5,
        fim_approximation: str = "gradient_variance",
        regularization: float = 1e-6,
        device: str = "cuda"
    ):
        self.k = k
        self.fim_approximation = fim_approximation
        self.regularization = regularization
        self.device = device
        
        logger.info(f"SST-Merge V3 initialized: k={k}")
    
    def merge_utility_safety(
        self,
        model: nn.Module,
        utility_adapters: List[Dict[str, torch.Tensor]],
        safety_adapter: Dict[str, torch.Tensor],
        utility_dataloader,
        safety_dataloader,
        max_samples: int = 500
    ) -> Dict[str, torch.Tensor]:
        """
        Layer-wise Projectionを使用したマージ
        
        手順:
        1. Utilityアダプターを固定（平均化）
        2. FIM計算とGEVP解決（元のSST-Mergeと同じ）
        3. Safetyアダプターを射影
        4. **Layer-wise**: 層ごとに異なるSafety Weightでマージ
        """
        logger.info("=" * 70)
        logger.info("SST-Merge V3: Layer-wise Projection")
        logger.info("=" * 70)
        
        # Step 1: Utilityアダプターを固定
        logger.info("\nStep 1: Fixing Utility adapters...")
        utility_merged = self._average_adapters(utility_adapters)
        logger.info("  ✓ Utility adapters fixed")
        
        # Step 2: FIM計算とGEVP解決
        logger.info("\nStep 2: Computing FIM and solving GEVP...")
        safety_subspace = self._compute_safety_subspace(
            model,
            utility_adapters,
            safety_adapter,
            utility_dataloader,
            safety_dataloader,
            max_samples
        )
        logger.info(f"  ✓ Safety subspace computed (k={self.k})")
        
        # Step 3: Safetyアダプターを射影
        logger.info("\nStep 3: Projecting Safety adapter...")
        safety_projected = self._project_to_safety_subspace(
            [safety_adapter],
            safety_subspace
        )
        logger.info("  ✓ Safety adapter projected")
        
        # Step 4: Layer-wise マージ
        logger.info("\nStep 4: Layer-wise merging...")
        merged = {}
        layer_stats = {}
        
        for key in utility_merged.keys():
            # 層ごとのSafety Weightを取得
            safety_weight = get_safety_weight(key)
            
            # マージ
            if key in safety_projected:
                merged[key] = (
                    utility_merged[key] + 
                    safety_weight * safety_projected[key]
                )
            else:
                merged[key] = utility_merged[key]
            
            # 統計
            layer_type = get_layer_type(key)
            if layer_type not in layer_stats:
                layer_stats[layer_type] = 0
            layer_stats[layer_type] += 1
        
        # 統計を表示
        logger.info("  Layer-wise Safety Weights:")
        for layer_type, count in sorted(layer_stats.items()):
            weight = LAYER_SAFETY_WEIGHTS.get(layer_type, 1.0)
            logger.info(f"    {layer_type:12s}: {weight:.1f} ({count} params)")
        
        logger.info("  ✓ Layer-wise merging completed")
        logger.info("=" * 70)
        
        return merged
    
    def _average_adapters(self, adapters):
        """アダプターを平均化（元のSST-Mergeと同じ）"""
        # 実装省略
        pass
    
    def _compute_safety_subspace(self, ...):
        """Safety Subspaceを計算（元のSST-Mergeと同じ）"""
        # 実装省略
        pass
    
    def _project_to_safety_subspace(self, ...):
        """Safety Subspaceに射影（元のSST-Mergeと同じ）"""
        # 実装省略
        pass
```

---

## 期待結果

### Layer-wise Safety Weights

| 層タイプ | Safety Weight | 役割 |
|---------|---------------|------|
| lm_head | 3.0 | 出力層：強いSafety |
| Attention | 1.0 | 中程度のSafety |
| FFN | 0.3 | Utility優先 |

### 期待メトリクス

| メトリクス | 現在 (k=5, w=1.0) | V3 (Layer-wise) | 目標 | 達成 |
|-----------|------------------|----------------|------|------|
| Jailbreak | 77.8% | **90-95%** | 90%+ | ✅ |
| MMLU | 49.6% | **50-52%** | 52%+ | △ |
| RepliQA | 33.7% | **35-38%** | 40%+ | △ |

---

## 実装手順

### Phase 1: 元のSST-Mergeをコピー

```bash
# 元のSST-Mergeをベースに作成
cp -r sst_merge_v2 sst_merge_v3
```

### Phase 2: Layer-wise Projectionを実装

1. `layer_config.py`を作成
2. `sst_merge_v3.py`を修正
   - `merge_utility_safety`にLayer-wiseロジックを追加
   - 他のメソッドは元のSST-Mergeと同じ

### Phase 3: テスト実行

```bash
cd sst_merge_v3
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --k 5 \
    --max_samples 500 \
    --use_fim

python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v3_*.pt \
    --model llama-3.1-8b \
    --max_samples 500
```

---

## まとめ

### アプローチ

**元のSST-Merge + Layer-wise Projection**

### 期待効果

- **Jailbreak**: 90-95%（出力層の強いSafety）
- **MMLU/RepliQA**: 維持または微改善（FFNのUtility優先）

### 次のアクション

1. 元のSST-Mergeをコピー
2. Layer-wise Projectionを実装
3. テスト実行
