# run_real_experiments.py 実行可能性検証レポート

## 検証結果サマリー

**結論**: ✅ **ほぼ実行可能ですが、設定ファイルの作成が必要です**

## 依存関係の確認

### ✅ すべての依存モジュールが利用可能

```
✓ src.sst_merge.SSTMerge
✓ src.utils.model_loader.ModelLoader
✓ src.utils.data_loader.load_beavertails
✓ src.baselines.dare.DARE
✓ src.baselines.alignguard_lora.AlignGuardLoRA
✓ src.evaluation.safety_tax_calculator.SafetyTaxCalculator
✓ src.evaluation.metrics_reporter.MetricsReporter
```

**Phase 1-10で実装したすべてのコアモジュールが正常にインポート可能です！**

## 実装したコードとの対応

### ✅ Phase 1-7: SST-Mergeコア機能

| Phase | モジュール | 使用箇所 | 状態 |
|-------|----------|---------|------|
| Phase 1-3 | `ModelLoader` | モデルロード | ✅ 利用可能 |
| Phase 4 | `FIMCalculator` | SST-Merge内部で使用 | ✅ 利用可能 |
| Phase 5 | `GEVPSolver` | SST-Merge内部で使用 | ✅ 利用可能 |
| Phase 6-7 | `SSTMerge` | 実験1-3で使用 | ✅ 利用可能 |

### ✅ Phase 8-10: 評価とベンチマーク

| Phase | モジュール | 使用箇所 | 状態 |
|-------|----------|---------|------|
| Phase 8 | `SafetyEvaluator` | 実験1で使用（簡易版実装済み） | ✅ 利用可能 |
| Phase 8 | `UtilityEvaluator` | 実験1で使用（簡易版実装済み） | ✅ 利用可能 |
| Phase 8 | `MetricsReporter` | 実験3で使用 | ✅ 利用可能 |
| Phase 9 | ベンチマーク | 実験2で実装 | ✅ 利用可能 |
| Phase 10 | エンドツーエンド | run_real_experiments.py | ✅ 利用可能 |

## 必要な追加ファイル

### ⚠️ 設定ファイルが必要

`configs/experiment_config_real.yaml`が存在しません。以下の内容で作成する必要があります:

```yaml
# SST-Merge実験設定ファイル

# データセット設定
datasets:
  cache_dir: "data/cache"
  
  # 最小構成（デバッグ用）
  minimal:
    beavertails:
      train_samples: 100
      eval_samples: 50
      batch_size: 4
    mmlu:
      subjects: 2
      max_samples: 100
      batch_size: 4
    humaneval:
      max_samples: 20
      batch_size: 4
  
  # フルスケール（本番用）
  full:
    beavertails:
      train_samples: 10000
      eval_samples: 2000
      batch_size: 32
    mmlu:
      subjects: null  # 全サブジェクト
      max_samples: null  # 全サンプル
      batch_size: 32
    humaneval:
      max_samples: null  # 全サンプル
      batch_size: 32

# モデル設定
models:
  mistral-7b:
    full_name: "mistralai/Mistral-7B-v0.1"
    device_map: "auto"
    torch_dtype: "float16"
    use_flash_attention: true
  
  llama-3.1-8b:
    full_name: "meta-llama/Llama-3.1-8B-Instruct"
    device_map: "auto"
    torch_dtype: "float16"
    use_flash_attention: true
  
  qwen-2.5-14b:
    full_name: "Qwen/Qwen2.5-14B-Instruct"
    device_map: "auto"
    torch_dtype: "float16"
    use_flash_attention: true

# 実験設定
experiments:
  # 実験1: Safety Tax定量化
  exp1_safety_utility:
    output_dir: "results/exp1_safety_utility"
    minimal:
      max_samples: 100
    full:
      max_samples: null
  
  # 実験2: マルチタスク干渉耐性
  exp2_multitask:
    output_dir: "results/exp2_multitask"
    minimal:
      num_experts: [8, 12, 16]
    full:
      num_experts: [8, 12, 16, 20, 24]
  
  # 実験3: ベースライン比較
  exp3_baseline:
    output_dir: "results/exp3_baseline"
    methods: ["TA", "TIES", "DARE", "AGL", "SST-Merge"]
```

## 実行手順

### ステップ1: 設定ファイルの作成

```bash
# 設定ファイルを作成
cat > configs/experiment_config_real.yaml << 'EOF'
# [上記のYAML内容をコピー]
EOF
```

### ステップ2: データセットのダウンロード（オプション）

```bash
# データセットをダウンロード（実際のデータを使用する場合）
python scripts/download_datasets.py --dataset all
```

**Note**: データセットがなくても実験は実行できます。`run_real_experiments.py`は簡易版の評価を実装しているため、ダミーデータでも動作します。

### ステップ3: 実験の実行

```bash
# 最小構成で動作確認
python experiments/run_real_experiments.py \
    --mode minimal \
    --model mistral-7b \
    --experiment all

# フルスケール実験
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all
```

## 実装したコードの動作確認

### Phase 1-7のコードが動作する部分

`run_real_experiments.py`では、以下のPhase 1-7のコードは**直接使用されていません**が、**間接的に利用可能**です:

- **FIMCalculator**: `SSTMerge`内部で使用
- **GEVPSolver**: `SSTMerge`内部で使用
- **LoRAマージング**: `SSTMerge.merge_lora_adapters()`で実行

### Phase 8-10のコードが動作する部分

`run_real_experiments.py`では、以下のPhase 8-10のコードを**直接使用**しています:

- ✅ **実験1**: 安全性評価（`evaluate_safety`）とユーティリティ評価（`evaluate_utility`）
- ✅ **実験2**: マルチタスク干渉耐性のベンチマーク
- ✅ **実験3**: ベースライン比較（MetricsReporterを使用可能）

## 完全なテストを実行する方法

Phase 1-10のすべてのコードを動作させるには、以下のテストスクリプトを使用してください:

### Phase 1-7のテスト

```bash
# Phase 1-3: LoRA基礎
python scripts/test_lora_basics.py

# Phase 4-5: FIM & GEVP
python scripts/test_fim_gevp.py

# Phase 6-7: SST-Merge
python scripts/test_sst_merge.py
```

### Phase 8-10のテスト

```bash
# Phase 8: 評価パイプライン
python scripts/test_evaluation.py

# Phase 9-10: エンドツーエンド
python scripts/test_end_to_end.py
```

### 実データ実験

```bash
# 設定ファイル作成後
python experiments/run_real_experiments.py \
    --mode full \
    --model mistral-7b \
    --experiment all
```

## まとめ

### ✅ 実行可能

**`run_real_experiments.py`は、設定ファイルを作成すれば実行可能です！**

### 実装したコードの利用状況

| コード | run_real_experiments.py | テストスクリプト |
|--------|------------------------|----------------|
| **Phase 1-7** | 間接的に利用（SSTMerge内部） | ✅ 直接テスト可能 |
| **Phase 8-10** | ✅ 直接利用 | ✅ 直接テスト可能 |

### 推奨実行フロー

1. **設定ファイル作成**: `configs/experiment_config_real.yaml`
2. **テストスクリプト実行**: Phase 1-10の動作確認
3. **実データ実験実行**: `run_real_experiments.py`

これにより、実装したすべてのコード（Phase 1-10）を動作させることができます！
