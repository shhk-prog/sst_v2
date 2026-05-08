# SST-Merge 実験実行クイックスタートガイド

**最終更新**: 2025年12月21日

---

## 🚀 即座に実行可能な実験

### 1. 並列実行スクリプトのテスト（推奨）

**目的**: H100 4枚を使用して3モデルを並列実行

```bash
# 実験1のみを並列実行（実データ、16,042サンプル）
python scripts/run_parallel_experiments.py \
    --mode full \
    --experiment exp1

# 推定時間: 4分（並列）vs 12分（逐次）
# 短縮率: 67%
```

**期待される結果**:
- 3モデルが同時に実行される
- 各モデルが異なるGPUに割り当てられる
- ログが`logs/parallel/`に保存される
- 結果サマリーが`results/parallel/`に保存される

---

### 2. 単一モデルでのフルスケール実験

**目的**: 特定のモデルで完全な評価を実行

```bash
# Qwen2.5-14B（最高性能）でフルスケール実験
python experiments/run_real_experiments.py \
    --mode full \
    --model qwen-2.5-14b \
    --experiment exp1

# 推定時間: 4分
```

---

## 📊 現在の実験状況

### ✅ 実装済み・実行可能

| 実験 | 状態 | データ | 実行時間 |
|------|------|--------|---------|
| **実験1: Safety Tax定量化** | ✅ 完了 | 実データ（16,042サンプル） | 4分/モデル |
| 実験2: マルチタスク干渉耐性 | ⚠️ ダミー | ダミーデータ | <1秒 |
| 実験3: ベースライン比較 | ⚠️ ダミー | ダミーデータ | <1秒 |

### 📈 実験1の結果（フルスケール）

| モデル | Refusal Rate | Utility | サンプル数 |
|--------|-------------|---------|----------|
| Qwen2.5-14B | 25.15% 🥇 | 69.87% | 16,042 |
| Llama-3.1-8B | 9.75% | 70.30% 🥇 | 16,042 |
| Mistral-7B | 1.35% | 69.56% | 16,042 |

---

## 🔧 次のステップ: LoRA実装

### オプション1: 事前学習済みLoRAアダプタを使用（推奨）

**推定時間**: 1日

```python
# 1. LoRAアダプタのダウンロード
from huggingface_hub import hf_hub_download

# 安全性特化LoRA
safety_lora = hf_hub_download(
    repo_id="alignment-handbook/zephyr-7b-sft-lora",
    filename="adapter_model.bin"
)

# 数学特化LoRA
math_lora = hf_hub_download(
    repo_id="meta-math/MetaMath-Mistral-7B-LoRA",
    filename="adapter_model.bin"
)
```

**次のステップ**:
1. LoRAアダプタをダウンロード
2. `src/sst_merge.py`を使用してマージ
3. 実験2-3を実行

---

### オプション2: 簡易ファインチューニング

**推定時間**: 2日

```bash
# 小規模データでLoRAをファインチューニング
python scripts/train_lora.py \
    --model mistral-7b \
    --dataset beavertails \
    --samples 1000 \
    --output lora_adapters/safety_lora

# 推定時間: 1-2時間/アダプタ
```

---

## 📁 ファイル構成

### 実験結果
```
results/
├── minimal/          # 最小構成（320サンプル）
│   └── exp1_safety_utility/
│       ├── mistral-7b_minimal.json
│       ├── llama-3.1-8b_minimal.json
│       └── qwen-2.5-14b_minimal.json
│
├── full/             # フルスケール（16,042サンプル）
│   └── exp1_safety_utility/
│       ├── mistral-7b_full.json
│       ├── llama-3.1-8b_full.json
│       └── qwen-2.5-14b_full.json
│
└── parallel/         # 並列実行の結果
    └── summary_*.json
```

### スクリプト
```
scripts/
├── download_datasets.py          # データセットダウンロード
├── run_parallel_experiments.py   # 並列実行（NEW）
└── (train_lora.py)               # LoRAファインチューニング（TODO）
```

---

## 🎯 推奨実行フロー

### ステップ1: 並列実行のテスト（5分）

```bash
# 3モデルを並列実行
python scripts/run_parallel_experiments.py \
    --mode full \
    --experiment exp1
```

**確認事項**:
- [ ] 3つのプロセスが起動
- [ ] 各プロセスが異なるGPUを使用
- [ ] ログファイルが生成される
- [ ] 結果が正しく保存される

---

### ステップ2: LoRAアダプタの準備（1日）

**オプションA: ダウンロード（推奨）**
```bash
# Hugging Face Hubから既存のLoRAをダウンロード
python scripts/download_lora_adapters.py \
    --models mistral-7b,llama-3.1-8b,qwen-2.5-14b \
    --types safety,math,code
```

**オプションB: ファインチューニング**
```bash
# 小規模データでファインチューニング
python scripts/train_lora.py \
    --model mistral-7b \
    --dataset beavertails \
    --samples 1000
```

---

### ステップ3: 完全な実験実行（2時間）

```bash
# 実験1-3をすべて並列実行
python scripts/run_parallel_experiments.py \
    --mode full \
    --experiment all

# 推定時間: 2時間（並列）vs 6時間（逐次）
```

---

### ステップ4: 結果の分析とレポート作成（1時間）

```bash
# 結果を分析
python scripts/analyze_results.py \
    --input results/parallel/ \
    --output reports/

# 可視化を生成
python scripts/generate_visualizations.py \
    --input results/parallel/ \
    --output visualizations/
```

---

## 💡 トラブルシューティング

### GPU使用状況の確認

```bash
# GPU使用状況をモニタリング
watch -n 1 nvidia-smi
```

### ログの確認

```bash
# 並列実行のログを確認
tail -f logs/parallel/mistral-7b_*.log
tail -f logs/parallel/llama-3.1-8b_*.log
tail -f logs/parallel/qwen-2.5-14b_*.log
```

### プロセスの管理

```bash
# 実行中のプロセスを確認
ps aux | grep run_real_experiments

# プロセスを停止（必要な場合）
pkill -f run_real_experiments
```

---

## 📊 期待される成果

### 現在（実験1のみ）
- ✅ 実データでの評価（16,042サンプル）
- ✅ 3モデルでの比較
- ✅ 並列実行による高速化

### LoRA実装後（実験1-3）
- ✅ 完全なSST-Merge評価
- ✅ マルチタスク干渉耐性の測定
- ✅ 5手法の包括的比較
- ✅ 論文に必要なすべてのデータ

---

## 📝 チェックリスト

### 即座に実行可能
- [ ] 並列実行スクリプトのテスト
- [ ] 実験1の結果確認
- [ ] GPU使用状況の確認

### LoRA実装後
- [ ] LoRAアダプタのダウンロード/準備
- [ ] 実験2-3の実装
- [ ] 完全な実験実行
- [ ] 結果の分析とレポート作成

---

**サポート**: 問題が発生した場合は、ログファイルとGPU使用状況を確認してください。
