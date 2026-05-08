# 実データ実験の実行手順

## 概要

このガイドでは、実際のデータセット（BeaverTails、MMLU、HumanEval）を使用してSST-Merge実験を実行する手順を説明します。

## 環境

- **GPU**: H100 x 4枚
- **モデル**: Mistral-7B、Llama-3.1-8B-Instruct、Qwen2.5-14B-Instruct
- **実験モード**: 最小構成（デバッグ用）とフルスケール（本番用）

---

## セットアップ

### 1. 依存関係のインストール

```bash
# 仮想環境の作成（推奨）
python -m venv sst
source sst/bin/activate  # Linux/Mac
# または
# sst\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt

# Flash Attention 2のインストール（オプション、高速化のため）
pip install flash-attn --no-build-isolation
```

### 2. データセットのダウンロード

```bash
# すべてのデータセットをダウンロード
python scripts/download_datasets.py --dataset all --verify

# または、個別にダウンロード
python scripts/download_datasets.py --dataset beavertails
python scripts/download_datasets.py --dataset mmlu
python scripts/download_datasets.py --dataset humaneval
```

**ダウンロード時間の目安**:
- BeaverTails: 約5-10分
- MMLU: 約3-5分
- HumanEval: 約1分

**ディスク容量**: 合計約5-10GB

---

## 実験の実行

### オプション1: 最小構成（デバッグ・動作確認）

計算時間: 約10-30分

```bash
# 単一モデルで実験
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all

# 特定の実験のみ
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment exp1
```

**最小構成の設定**:
- BeaverTails: 100サンプル（train）、50サンプル（eval）
- MMLU: 2サブジェクト、100サンプル
- HumanEval: 20サンプル
- バッチサイズ: 4

### オプション2: フルスケール（本番実験）

計算時間: 約4-8時間（モデルとGPU数による）

```bash
# すべてのモデルで全実験を実行
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all

# 単一モデルで全実験
python experiments/run_real_experiments.py \
    --mode full \
    --model llama-3.1-8b \
    --experiment all

# 特定のモデルと実験の組み合わせ
python experiments/run_real_experiments.py \
    --mode full \
    --model qwen-2.5-14b \
    --experiment exp3
```

**フルスケールの設定**:
- BeaverTails: 10,000サンプル（train）、2,000サンプル（eval）
- MMLU: 全57サブジェクト、全サンプル
- HumanEval: 全164サンプル
- バッチサイズ: 32

---

## モデル別の推奨設定

### Mistral-7B
- **VRAM**: 約16GB
- **推奨GPU**: 1枚のH100で十分
- **特徴**: 最も軽量、高速

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b
```

### Llama-3.1-8B-Instruct
- **VRAM**: 約18GB
- **推奨GPU**: 1枚のH100で十分
- **特徴**: Instructチューニング済み、高品質

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model llama-3.1-8b
```

### Qwen2.5-14B-Instruct
- **VRAM**: 約32GB
- **推奨GPU**: 1-2枚のH100
- **特徴**: 最大モデル、最高性能

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model qwen-2.5-14b
```

---

## 実験の種類

### 実験1: Safety Tax定量化
- **目的**: SST-MergeのSafety Tax削減効果を測定
- **期待結果**: AlignGuard-LoRAに対して60-70%の削減

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment exp1
```

### 実験2: マルチタスク干渉耐性
- **目的**: 複数のLoRAエキスパートをマージした際の性能維持率を測定
- **期待結果**: DAREに対して88-90%の性能維持（20エキスパート）

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment exp2
```

### 実験3: ベースライン比較
- **目的**: 5つの手法（TA、TIES、DARE、AGL、SST-Merge）を包括的に比較
- **期待結果**: SST-Mergeがパレート最適に最も近い

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment exp3
```

---

## 結果の確認

### 出力ディレクトリ

```
results/
├── exp1_safety_utility/
│   ├── results_*.json
│   └── visualizations/
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

### 可視化の確認

```bash
# 結果ディレクトリを確認
ls -lh results/exp*/

# レポートを表示
cat results/exp3_baseline/comprehensive_report.md
```

---

## トラブルシューティング

### メモリ不足エラー

```bash
# バッチサイズを減らす
# configs/experiment_config_real.yaml を編集
# batch_size: 32 → 16 または 8

# または、8bit量子化を使用
# models.*.load_in_8bit: true
```

### データセットのダウンロードエラー

```bash
# キャッシュをクリア
rm -rf data/cache/*

# 再ダウンロード
python scripts/download_datasets.py --all
```

### CUDA Out of Memory

```bash
# グラディエントチェックポイントを有効化
# configs/experiment_config_real.yaml
# compute.gradient_checkpointing: true

# または、より小さいモデルを使用
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b  # 最小モデル
```

---

## 推奨実行フロー

### ステップ1: 動作確認（最小構成）

```bash
# 1つのモデルで最小構成を実行
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment exp1

# 結果を確認
cat results/exp1_safety_utility/results_*.json
```

### ステップ2: 単一モデルでフルスケール

```bash
# Mistral-7Bでフルスケール実験
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all
```

### ステップ3: 全モデルでフルスケール

```bash
# すべてのモデルで全実験を実行
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all
```

---

## 計算時間の目安

### 最小構成
- **単一モデル、単一実験**: 5-10分
- **単一モデル、全実験**: 15-30分
- **全モデル、全実験**: 45分-1時間

### フルスケール
- **単一モデル、単一実験**: 1-2時間
- **単一モデル、全実験**: 3-6時間
- **全モデル、全実験**: 9-18時間

---

## 次のステップ

1. **最小構成で動作確認**
2. **単一モデルでフルスケール実験**
3. **全モデルで包括的実験**
4. **結果の分析とレポート作成**
5. **論文執筆**

---

## サポート

問題が発生した場合は、以下を確認してください：

1. ログファイル: `logs/*.log`
2. エラーメッセージ
3. GPU使用状況: `nvidia-smi`
4. ディスク容量: `df -h`
