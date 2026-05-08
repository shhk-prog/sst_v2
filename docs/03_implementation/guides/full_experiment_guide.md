# SST-Mergeフル実験実行ガイド

## 概要

このガイドでは、SST-Mergeの完全な実験を実行する方法を説明します。実際のLLMモデル（Mistral-7B、Llama-3.1-8B、Qwen2.5-14B）と実データセット（BeaverTails、MMLU、HumanEval）を使用した大規模評価を行います。

## 前提条件

- **GPU**: H100 x 1-4枚（モデルサイズによる）
- **ディスク容量**: 約50-100GB（モデル + データセット）
- **Python**: 3.9以上
- **CUDA**: 11.8以上

## ステップ1: 環境セットアップ

### 1.1 仮想環境の作成

```bash
# プロジェクトディレクトリに移動
cd /mnt/iag-02/home/hiromi/src/SST_merge

# 仮想環境を作成（既に作成済みの場合はスキップ）
python -m venv sst
source sst/bin/activate
```

### 1.2 依存関係のインストール

```bash
# 基本的な依存関係
pip install -r requirements.txt

# Flash Attention 2（オプション、高速化のため）
pip install flash-attn --no-build-isolation

# インストール確認
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
```

## ステップ2: データセットのダウンロード

### 2.1 自動ダウンロード

```bash
# すべてのデータセットをダウンロード
python scripts/download_datasets.py --dataset all --verify

# または、個別にダウンロード
python scripts/download_datasets.py --dataset beavertails
python scripts/download_datasets.py --dataset mmlu
python scripts/download_datasets.py --dataset humaneval
```

**ダウンロード時間**: 約10-20分  
**ディスク容量**: 約5-10GB

### 2.2 データセットの確認

```bash
# データセットが正しくダウンロードされたか確認
ls -lh data/

# 期待される出力:
# data/
# ├── beavertails/
# ├── mmlu/
# └── humaneval/
```

## ステップ3: 実験の実行

### オプション1: クイックテスト（最小構成）

**目的**: 動作確認とデバッグ  
**計算時間**: 約10-30分

```bash
# 単一モデルで最小構成テスト
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all
```

**最小構成の設定**:
- BeaverTails: 100サンプル（train）、50サンプル（eval）
- MMLU: 2サブジェクト、100サンプル
- HumanEval: 20サンプル
- バッチサイズ: 4

### オプション2: フルスケール実験（推奨）

**目的**: 本番実験、論文用データ  
**計算時間**: 約4-8時間（モデルとGPU数による）

#### 2.1 単一モデルで全実験

```bash
# Mistral-7B（最も軽量、推奨開始点）
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all

# Llama-3.1-8B-Instruct（高品質）
python experiments/run_real_experiments.py \
    --mode full \
    --model llama-3.1-8b \
    --experiment all

# Qwen2.5-14B-Instruct（最大モデル）
python experiments/run_real_experiments.py \
    --mode full \
    --model qwen-2.5-14b \
    --experiment all
```

#### 2.2 すべてのモデルで全実験

```bash
# 包括的な実験（9-18時間）
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all
```

### オプション3: 特定の実験のみ実行

```bash
# 実験1: Safety Tax定量化
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment exp1

# 実験2: マルチタスク干渉耐性
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment exp2

# 実験3: ベースライン比較
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment exp3
```

## ステップ4: 実験の詳細

### 実験1: Safety Tax定量化

**目的**: SST-MergeのSafety Tax削減効果を測定

**期待結果**:
- AlignGuard-LoRAに対して60-70%のSafety Tax削減
- ユーティリティ維持率: 95%以上

**実行コマンド**:
```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment exp1
```

### 実験2: マルチタスク干渉耐性

**目的**: 複数のLoRAエキスパートをマージした際の性能維持率を測定

**期待結果**:
- DAREに対して88-90%の性能維持（20エキスパート）
- 干渉耐性の向上

**実行コマンド**:
```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment exp2
```

### 実験3: ベースライン比較

**目的**: 5つの手法を包括的に比較
- Task Arithmetic (TA)
- TIES-Merging
- DARE
- AlignGuard-LoRA (AGL)
- SST-Merge（提案手法）

**期待結果**:
- SST-Mergeがパレート最適に最も近い
- 複合スコアで最高性能

**実行コマンド**:
```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment exp3
```

## ステップ5: 結果の確認

### 5.1 出力ディレクトリの構造

```
results/
├── exp1_safety_utility/
│   ├── results_mistral-7b.json
│   ├── results_llama-3.1-8b.json
│   ├── results_qwen-2.5-14b.json
│   └── visualizations/
│       ├── safety_tax_comparison.png
│       └── utility_preservation.png
├── exp2_multitask/
│   ├── results.json
│   ├── performance_comparison.png
│   └── performance_bar_chart.png
└── exp3_baseline/
    ├── metrics.json
    ├── safety_utility_tradeoff.png
    ├── safety_tax_comparison.png
    └── comprehensive_report.md
```

### 5.2 結果の確認コマンド

```bash
# 結果ディレクトリを確認
ls -lh results/exp*/

# JSONファイルを表示
cat results/exp1_safety_utility/results_mistral-7b.json | jq .

# レポートを表示
cat results/exp3_baseline/comprehensive_report.md

# 可視化を確認
open results/exp3_baseline/safety_utility_tradeoff.png  # Mac
# または
xdg-open results/exp3_baseline/safety_utility_tradeoff.png  # Linux
```

### 5.3 主要メトリクスの確認

```bash
# Safety Tax
jq '.safety_tax' results/exp1_safety_utility/results_*.json

# 複合スコア
jq '.composite_score' results/exp3_baseline/metrics.json

# パレート距離
jq '.pareto_distance' results/exp3_baseline/metrics.json
```

## ステップ6: トラブルシューティング

### 6.1 メモリ不足エラー

```bash
# バッチサイズを減らす
# configs/experiment_config_real.yaml を編集
# batch_size: 32 → 16 または 8

# または、8bit量子化を使用
# models.*.load_in_8bit: true
```

### 6.2 CUDA Out of Memory

```bash
# グラディエントチェックポイントを有効化
# configs/experiment_config_real.yaml
# compute.gradient_checkpointing: true

# または、より小さいモデルを使用
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b  # 最小モデル
```

### 6.3 データセットのダウンロードエラー

```bash
# キャッシュをクリア
rm -rf data/cache/*

# 再ダウンロード
python scripts/download_datasets.py --dataset all
```

## ステップ7: 推奨実行フロー

### 7.1 初回実行（動作確認）

```bash
# ステップ1: 最小構成で動作確認
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment exp1

# 結果を確認
cat results/exp1_safety_utility/results_*.json
```

### 7.2 単一モデルでフルスケール

```bash
# ステップ2: Mistral-7Bでフルスケール実験
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all

# 結果を確認
ls -lh results/
```

### 7.3 全モデルでフルスケール

```bash
# ステップ3: すべてのモデルで全実験を実行
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all

# 包括的なレポートを確認
cat results/exp3_baseline/comprehensive_report.md
```

## 計算時間とリソースの目安

### 最小構成
| 構成 | 計算時間 | GPU使用率 |
|------|---------|----------|
| 単一モデル、単一実験 | 5-10分 | ~50% |
| 単一モデル、全実験 | 15-30分 | ~60% |
| 全モデル、全実験 | 45分-1時間 | ~70% |

### フルスケール
| 構成 | 計算時間 | GPU使用率 |
|------|---------|----------|
| 単一モデル、単一実験 | 1-2時間 | ~80% |
| 単一モデル、全実験 | 3-6時間 | ~85% |
| 全モデル、全実験 | 9-18時間 | ~90% |

## モデル別の推奨設定

### Mistral-7B
- **VRAM**: 約16GB
- **推奨GPU**: 1枚のH100で十分
- **特徴**: 最も軽量、高速
- **推奨用途**: 初回テスト、デバッグ

### Llama-3.1-8B-Instruct
- **VRAM**: 約18GB
- **推奨GPU**: 1枚のH100で十分
- **特徴**: Instructチューニング済み、高品質
- **推奨用途**: 本番実験

### Qwen2.5-14B-Instruct
- **VRAM**: 約32GB
- **推奨GPU**: 1-2枚のH100
- **特徴**: 最大モデル、最高性能
- **推奨用途**: 最終評価、論文用データ

## 次のステップ

1. ✅ 環境セットアップ
2. ✅ データセットダウンロード
3. ✅ 最小構成で動作確認
4. ✅ 単一モデルでフルスケール実験
5. ✅ 全モデルで包括的実験
6. ✅ 結果の分析とレポート作成
7. 📝 論文執筆

## サポート

問題が発生した場合は、以下を確認してください：

1. **ログファイル**: `logs/*.log`
2. **エラーメッセージ**: コンソール出力
3. **GPU使用状況**: `nvidia-smi`
4. **ディスク容量**: `df -h`
5. **メモリ使用量**: `free -h`

## クイックリファレンス

```bash
# 最小構成テスト
python experiments/run_real_experiments.py --mode minimal --model mistral-7b --experiment all

# フルスケール（単一モデル）
python experiments/run_real_experiments.py --mode full --model mistral-7b --experiment all

# フルスケール（全モデル）
python experiments/run_real_experiments.py --mode full --model all --experiment all

# 結果確認
ls -lh results/
cat results/exp3_baseline/comprehensive_report.md
```
