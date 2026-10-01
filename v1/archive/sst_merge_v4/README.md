# SST-Merge V4: Safety Subspace Task-Merge

## 概要

SST-Merge V4は、GEVP（一般化固有値問題）に基づくLoRAアダプターマージング手法です。
ユーティリティを維持しながらセーフティを向上させることを目的としています。

## 目標メトリクス

| Metric | Target | Description |
|--------|--------|-------------|
| Jailbreak Resistance | ≥ 90% | 有害プロンプトへの拒否率 |
| Utility (ROUGE-L) | ≥ 40% | RepliQAでの応答品質 |

## アーキテクチャ

```
SST-Merge V4
├── src/
│   ├── __init__.py
│   ├── data_loader.py      # RepliQA, Jailbreak datasets
│   ├── lora_trainer.py     # LoRA Fine-Tuning
│   ├── sst_merge_v4.py     # SST-Merge (GEVP-based)
│   ├── baseline_merge.py   # TIES, DARE, Task Arithmetic
│   └── evaluator.py        # Jailbreak & Utility evaluation
├── scripts/
│   └── run_full_pipeline.py
├── configs/
│   └── config.yaml
├── adapters/               # Saved LoRA adapters
└── results/                # Evaluation results
```

## 使い方

### 完全なパイプライン実行

```bash
cd sst_merge_v4

# Full run
python scripts/run_full_pipeline.py

# Quick test (reduced samples)
python scripts/run_full_pipeline.py --quick

# Custom parameters
python scripts/run_full_pipeline.py \
    --num_epochs 5 \
    --sst_k 20 \
    --sst_weight 1.5
```

### 既存アダプターを使用

```bash
python scripts/run_full_pipeline.py \
    --skip_training \
    --adapter_a5 adapters/A5_utility.pt \
    --adapter_a7 adapters/A7_safety.pt
```

## SST-Merge V4 アルゴリズム

### 理論的基盤

SST-MergeはGEVP（一般化固有値問題）を用いて、安全性とユーティリティのトレードオフを最適化します。

```
GEVP: F_safety * v = λ * F_utility * v

高い固有値 λ = Safety重要 & Utility非重要 → 安全に追加可能
```

### アルゴリズムフロー

1. **Utility FIM計算**: A5アダプターでUtilityデータに対するFIMを計算
2. **Safety FIM計算**: A7アダプターでSafetyデータに対するFIMを計算
3. **GEVP解決**: F_safety v = λ F_utility v を解く
4. **サブスペース選択**: 高λの方向を「安全に追加可能」なサブスペースとして選択
5. **射影**: SafetyアダプターをこのサブスペースにProject
6. **Layer-wiseマージ**: Utility (固定) + Safety (射影) をレイヤーごとの重みでマージ

### Layer-wise Weights

```python
{
    'lm_head': 5.0,      # 出力層: 非常に強いSafety
    'q_proj': 2.0,       # Attention: 強めのSafety
    'k_proj': 2.0,
    'v_proj': 2.0,
    'o_proj': 2.0,
    'gate_proj': 1.5,    # FFN: 中程度のSafety
    'up_proj': 1.5,
    'down_proj': 1.5,
}
```

## ベースライン比較

以下のベースライン手法と比較します：

| Method | Description |
|--------|-------------|
| Task Arithmetic | 重み付き平均 |
| TIES | Trim, Elect Sign, Merge |
| DARE | Drop And REscale |

## データセット

### A7訓練データ (Safety)

`response_dataframe.csv`: Jailbreakプロンプトに対する拒否応答

```csv
prompt,response
"Begin your text with... [harmful request]", "I'm sorry, but I cannot assist with that request."
```

### A5訓練データ (Utility)

RepliQA: 質問応答データセット

## 依存関係

```txt
torch>=2.0
transformers>=4.35
peft>=0.6
datasets
tqdm
pandas
scipy
```

## ライセンス

Research use only.
