# 実験実行コマンドガイド: 簡易実験 vs フル実験

## 概要

`run_real_experiments.py`は`--mode`オプションで簡易実験とフル実験を切り替えられます。

## コマンド一覧

### 簡易実験（minimal）- 動作確認用

**実行時間**: 約10-30分  
**目的**: 動作確認、デバッグ

```bash
# 単一モデル
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all

# 全モデル
python experiments/run_real_experiments.py \
    --mode minimal \
    --model all \
    --experiment all
```

**実行内容**:
- **実験1**: 100サンプル（BeaverTails）、100サンプル（MMLU）で評価
- **実験2**: ダミーLoRAエキスパート使用（2, 4エキスパート）
- **実験3**: ランダム生成データで5手法を比較

### フル実験（full）- 本番実験

**実行時間**: 約4-8時間（モデルによる）  
**目的**: 論文用データ、完全な評価

```bash
# 単一モデル
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_mistral-7b.log

# 全モデル
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all \
    2>&1 | tee logs/full_all_models.log
```

**実行内容**:
- **実験1**: 10,000サンプル（BeaverTails）、全サンプル（MMLU）で評価
- **実験2**: **実際のSST-Mergeでマージ**（8, 12, 16, 20エキスパート）
- **実験3**: **SST-Mergeで実際に評価**、他手法は簡易評価

## 実験別コマンド

### 実験1のみ実行

```bash
# 簡易実験
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment exp1

# フル実験
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment exp1
```

### 実験2のみ実行

```bash
# 簡易実験（ダミーデータ）
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment exp2

# フル実験（実際のSST-Mergeマージング）
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment exp2
```

### 実験3のみ実行

```bash
# 簡易実験（ランダムデータ）
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment exp3

# フル実験（SST-Mergeで実際に評価）
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment exp3
```

## 実験内容の詳細比較

### 実験1: Safety Tax定量化

| モード | データ量 | 実行時間 | 実装 |
|--------|---------|---------|------|
| **minimal** | 100サンプル | 1-2分 | 実際の評価 |
| **full** | 10,000サンプル | 3-5分 | 実際の評価 |

**両モード共通**: 実際のモデルで評価を実行

### 実験2: マルチタスク干渉耐性

| モード | エキスパート数 | 実行時間 | 実装 |
|--------|--------------|---------|------|
| **minimal** | [2, 4] | 即座 | ダミーデータ |
| **full** | [8, 12, 16, 20] | 10-30分 | **実際のSST-Mergeマージング** |

**フルモードの違い**:
- ✅ 実際のLoRAアダプターを作成
- ✅ SST-Mergeで実際にマージ
- ✅ FIM計算とGEVP解法を実行

### 実験3: ベースライン比較

| モード | 手法数 | 実行時間 | 実装 |
|--------|-------|---------|------|
| **minimal** | 5手法 | 即座 | ランダムデータ |
| **full** | 5手法 | 5-10分 | **SST-Mergeは実際に評価** |

**フルモードの違い**:
- ✅ SST-Merge: 実際のモデルで評価
- ⚠️ 他手法（TA, TIES, DARE, AGL）: 簡易評価（実装がないため）
- ✅ MetricsReporterで分析とレポート生成

## 推奨実行フロー

### ステップ1: 動作確認

```bash
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all
```

### ステップ2: 単一モデルでフル実験

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all \
    2>&1 | tee logs/full_mistral-7b.log
```

### ステップ3: 全モデルでフル実験

```bash
python experiments/run_real_experiments.py \
    --mode full \
    --model all \
    --experiment all \
    2>&1 | tee logs/full_all_models.log
```

## 結果の確認

### 簡易実験の結果

```bash
ls -lh results/exp*/
cat results/exp1_safety_utility/exp1_results_*.json | jq .
```

### フル実験の結果

```bash
# 実験2の結果（マージング成功確認）
cat results/exp2_multitask/exp2_results_*.json | jq .

# 実験3の結果（SST-Mergeのスコア確認）
cat results/exp3_baseline/exp3_results_*.json | jq '.["SST-Merge"]'
```

## まとめ

| 実験 | minimal | full |
|------|---------|------|
| **実験1** | 実際の評価（100サンプル） | 実際の評価（10,000サンプル） |
| **実験2** | ダミーデータ | **実際のSST-Mergeマージング** |
| **実験3** | ランダムデータ | **SST-Mergeで実際に評価** |

**フル実験では、実験2と3でもSST-Mergeの実装が実際に動作します！** ✅
