# SST-Merge V2: 既存リソースを使用した実行ガイド

## 概要

このガイドでは、SST_merge直下の既存アダプターとデータローダーを使用してSST-Merge V2を実行する方法を説明します。

## 前提条件

### 必要なアダプター

以下のアダプターが`saved_adapters/llama-3.1-8b/utility_model/`に存在する必要があります：

- `utility_model_A5.pt` - RepliQAアダプター
- `utility_model_A6.pt` - Alpacaアダプター  
- `utility_model_A7.pt` - Securityアダプター

### アダプターの作成方法（未作成の場合）

```bash
cd /Users/saki/lab/100net/src/SST_merge

# A5: RepliQA
python experiments/create_instruction_model.py \
    --model llama-3.1-8b \
    --task repliqa \
    --mode full

# A6: Alpaca
python experiments/create_instruction_model.py \
    --model llama-3.1-8b \
    --task alpaca \
    --mode full

# A7: Security
python experiments/create_instruction_model.py \
    --model llama-3.1-8b \
    --task security \
    --mode full
```

## 実行方法

### 方法1: ラッパースクリプトを使用（推奨）

```bash
cd /Users/saki/lab/100net/src/SST_merge/sst_merge_v2

# Residual Mode（FIM計算あり）
./run_sst_v2_with_fim.sh A5+A7 residual 0.7

# Layerwise Mode（FIM計算あり）
./run_sst_v2_with_fim.sh A5+A7 layerwise 0.7 balanced

# Direct Mode（FIM計算なし）
./run_sst_v2_with_fim.sh A5+A7 direct
```

#### パラメータ

```bash
./run_sst_v2_with_fim.sh [variant] [mode] [residual_ratio] [preset]
```

- `variant`: `A5+A7`, `A6+A7`, `A5+A6+A7`
- `mode`: `residual`, `layerwise`, `direct`
- `residual_ratio`: 0.0〜1.0（residual modeのみ、デフォルト: 0.7）
- `preset`: `safety_first`, `balanced`, `utility_first`, `minimal`（layerwiseのみ、デフォルト: balanced）

### 方法2: Pythonスクリプトを直接実行

#### Residual Mode（FIM計算あり）

```bash
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode residual \
    --residual_ratio 0.7 \
    --k 10 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim
```

#### Layerwise Mode（FIM計算あり）

```bash
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode layerwise \
    --preset balanced \
    --k 10 \
    --safety_weight 1.0 \
    --max_samples 500 \
    --use_fim
```

#### Direct Mode（FIM計算なし）

```bash
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode direct \
    --safety_weight 1.0
```

## 重要な違い

### `--use_fim`フラグの有無

| フラグ | FIM計算 | データローダー | GPU | 実行時間 | 推奨用途 |
|--------|---------|--------------|-----|---------|----------|
| **なし** | ❌ | 不要 | 不要 | 秒 | 簡易テスト |
| **`--use_fim`** | ✅ | 必要 | 必須 | 分〜時間 | 本番実験 |

### 実行結果の確認

```bash
# ログの確認
# ✅ 正しい実行（FIMあり）
INFO - Step 1: Computing FIM matrices...
INFO - Step 2: Solving GEVP...
INFO - Step 3: Residual Safety Injection...

# ⚠️ FIMなし（Directにフォールバック）
WARNING - Dataloaders not provided. Falling back to direct mode.
INFO - Step 3: Direct Addition (no projection)...
```

## 実行例

### 例1: 基本的なResidual Mode

```bash
cd /Users/saki/lab/100net/src/SST_merge/sst_merge_v2
./run_sst_v2_with_fim.sh A5+A7 residual 0.7
```

期待される出力：
```
SST-MERGE V2: COMPLETE EXECUTION WITH FIM
Model: llama-3.1-8b
Variant: A5+A7
Mode: residual
...
Step 1: Computing FIM matrices...
Step 2: Solving GEVP...
Step 3: Residual Safety Injection...
✓ Merged adapter saved
```

### 例2: 異なるResidual Ratio

```bash
# Safety重視（residual_ratio = 0.9）
./run_sst_v2_with_fim.sh A5+A7 residual 0.9

# バランス（residual_ratio = 0.5）
./run_sst_v2_with_fim.sh A5+A7 residual 0.5
```

### 例3: Layerwise Mode

```bash
# Safety重視
./run_sst_v2_with_fim.sh A5+A7 layerwise 0.7 safety_first

# Utility重視
./run_sst_v2_with_fim.sh A5+A7 layerwise 0.7 utility_first
```

## トラブルシューティング

### エラー: "A5 adapter not found"

```bash
# アダプターを作成
cd /Users/saki/lab/100net/src/SST_merge
python experiments/create_instruction_model.py \
    --model llama-3.1-8b \
    --task repliqa \
    --mode full
```

### エラー: "CUDA out of memory"

```bash
# max_samplesを減らす
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode residual \
    --max_samples 200 \
    --use_fim
```

### 警告: "Falling back to direct mode"

`--use_fim`フラグを追加してください：

```bash
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode residual \
    --use_fim  # ← これを追加
```

## データローダーの詳細

`--use_fim`を使用すると、以下のデータローダーが自動的に読み込まれます：

### Utility Data

- **A5+A7**: RepliQA（質問応答）
- **A6+A7**: Alpaca（指示応答）
- **A5+A6+A7**: RepliQA + Alpaca

### Safety Data

- `data/response_dataframe.csv` - Jailbreak防御データ（1,400サンプル）

### データの場所

```
SST_merge/
├── data/
│   └── response_dataframe.csv  # Security data
├── saved_adapters/
│   └── llama-3.1-8b/
│       └── utility_model/
│           ├── utility_model_A5.pt
│           ├── utility_model_A6.pt
│           └── utility_model_A7.pt
└── sst_merge_v2/
    ├── run_sst_v2_with_fim.sh  # ← ラッパースクリプト
    └── scripts/
        └── run_merge.py
```

## パフォーマンス最適化

### GPU使用率の確認

```bash
# 別のターミナルで実行
watch -n 1 nvidia-smi
```

### サンプル数の調整

| max_samples | 実行時間 | 精度 | 推奨用途 |
|-------------|---------|------|----------|
| 100 | ~5分 | 低 | デバッグ |
| 500 | ~15分 | 中 | 開発 |
| 1000 | ~30分 | 高 | 論文用 |

## 次のステップ

マージ後の評価：

```bash
python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*.pt \
    --model llama-3.1-8b
```
