# Data-Free SST-Merge 実行ガイド

**作成日**: 2026-02-03  
**対象**: 修正済みData-Free実装

---

## 📋 前提条件

### 必要なファイル

1. ✅ `sst_merge_data_free.py` (修正済み)
2. ✅ `run_data_free_merge.py` (修正済み)
3. ✅ LoRAアダプター:
   - A5 Utility (RepliQA)
   - A6 Utility (Alpaca)
   - A7 Safety

### 必要な環境

- Python 3.8+
- PyTorch
- transformers
- peft
- safetensors

---

## 🚀 実行手順

### ステップ1: 設定確認

`run_data_free_merge.py`の設定を確認：

```python
# マージするアダプターのペア
merge_pairs = [
    ("./FT_model/A5_utility_...", "./FT_model/A7_safety_...", "A5_A7"),
    ("./FT_model/A6_utility_...", "./FT_model/A7_safety_...", "A6_A7"),
]

# SST-Merge設定
k_values = [5, 10, 20]              # 修正済み: top_k_ratioに変換される
use_layerwise_options = [True, False]  # 修正済み: 実装完了
alpha_values = [0.05, 0.07, ..., 1.0]  # 15段階
use_gevp = True
```

**重要**: アダプターのパスが正しいことを確認してください。

### ステップ2: スクリプト実行

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/sst_merge_v5

# Data-Freeマージ実行（フルモデル生成も含む）
python3 run_data_free_merge.py
```

### ステップ3: 実行時間の目安

**総設定数**: 2ペア × 3k × 2layerwise × 15α = **180設定**

- 1設定あたり: 約5-10分（環境による）
- **総実行時間**: 約15-30時間

### ステップ4: 出力確認

#### 生成されるディレクトリ

1. **`./merge_model_data_free/`**: LoRAアダプター形式
   ```
   ./merge_model_data_free/
   ├── A5_A7_data_free_k5_a0.05/
   ├── A5_A7_data_free_k5_lw_a0.05/
   ├── A5_A7_data_free_k10_a0.05/
   ├── A5_A7_data_free_k10_lw_a0.05/
   ...
   ```

2. **`./merge_model_data_free_full/`**: フルモデル形式
   ```
   ./merge_model_data_free_full/
   ├── A5_A7_data_free_k5_a0.05/
   ├── A5_A7_data_free_k5_lw_a0.05/
   ...
   ```

#### ファイル命名規則

```
{pair}_data_free_k{k}[_lw]_a{alpha}

例:
- A6_A7_data_free_k5_a0.5       # k=5, layerwise=False, α=0.5
- A6_A7_data_free_k10_lw_a1.0   # k=10, layerwise=True, α=1.0
```

---

## 🔧 トラブルシューティング

### エラー1: メモリ不足

**症状**: CUDA out of memory

**解決策**:
1. GPU台数を増やす（device_map='auto'は複数GPU対応）
2. バッチサイズを減らす（該当しないが念のため）
3. 一部の設定をコメントアウトして分割実行

### エラー2: アダプターが見つからない

**症状**: FileNotFoundError

**解決策**:
```bash
# アダプターのパスを確認
ls -la ./FT_model/

# run_data_free_merge.pyの27-33行目を修正
```

### エラー3: 途中で中断した場合

**解決策**:
既に生成されたモデルはスキップされないため、以下を検討：

1. **手動スキップ**: 生成済み設定をコメントアウト
2. **スクリプト修正**: 存在チェックを追加
```python
if (adapter_output / "adapter_model.bin").exists():
    logger.info(f"Skipping existing: {output_name}")
    continue
```

---

## 📊 進捗確認

### ログの見方

実行中のログ例：
```
==================================================
Processing pair: A6_A7
  Utility: ./FT_model/A6_utility_...
  Safety: ./FT_model/A7_safety_...
==================================================

------------------------------------------------------------
k=5, layerwise=False, top_k=0.05, α=0.05
------------------------------------------------------------

============================================================
Starting Data-Free SST-Merge
  Safety weight (α): 0.05
  Use GEVP: True
  Top-k ratio: 0.05
============================================================

Step 1: Computing Utility FIM (data-free)...
Step 2: Computing Safety FIM (data-free)...
Step 3: Solving GEVP...
Step 4: Computing Safety mask...
Step 5: Merging adapters...
Merge completed: 578 parameters
✓ Adapter saved: A6_A7_data_free_k5_a0.05
Converting adapter to full model...
✓ Full model saved: A6_A7_data_free_k5_a0.05
```

### 進捗カウント

```
Total configurations: 180
Completed: 45 / 180  (25%)
```

---

## 🧪 次のステップ: 評価実行

マージ完了後、各モデルを評価：

```bash
# 評価スクリプトを実行（既存のevalスクリプトを修正）
python3 run_all_evals_data_free.py
```

**注意**: Data-Free評価用のスクリプトが必要な場合は、`run_all_evals.py`を参考に作成してください。

---

## 📝 実行前チェックリスト

- [ ] アダプターのパスを確認
- [ ] 十分なディスク空き容量（約500GB推奨）
- [ ] GPU利用可能（CUDA対応）
- [ ] 実行時間の確保（15-30時間）
- [ ] ログ保存の準備（`python3 run_data_free_merge.py 2>&1 | tee data_free_merge.log`推奨）

---

## 💡 実行例（小規模テスト）

初めての実行では、設定を減らしてテスト実行を推奨：

```python
# run_data_free_merge.py を編集
k_values = [5]              # 1つのみ
use_layerwise_options = [False]  # 1つのみ
alpha_values = [0.5, 1.0]   # 2つのみ

# 総設定: 2ペア × 1k × 1lw × 2α = 4設定
# 実行時間: 約20-40分
```

テスト実行で問題がなければ、フル設定で実行してください。
