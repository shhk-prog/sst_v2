# SST-Merge 実行方法ガイド

## 概要

SST-Merge v5では、以下の3つのマージ方式を提供しています：

1. **通常版SST-Merge (加算型)**: 実データでFIMを計算、`Utility + α × mask × Safety`
2. **通常版SST-Merge (補間型)**: 実データでFIMを計算、`(1-α) × Utility + α × mask × Safety`
3. **Data-Free SST-Merge**: データ不要でLoRA重みからFIM近似、加算型と補間型の両方をサポート

---

## 1. 通常版SST-Merge (補間型)

### 📂 スクリプト
```bash
scripts/merging/run_all_merges_interpolation.py
```

### 🎯 マージ式
```python
merged = (1 - α) × Utility + α × mask × Safety
```
- Task Arithmetic互換の動作
- α値による明確なトレードオフ

### ⚙️ 設定項目

#### マージペア (48-53行目)
```python
merge_pairs = [
    ("../../models/finetuned/adapters/FT_model/A5_utility_...", 
     "../../models/finetuned/adapters/FT_model/A7_safety_...", 
     "A5_A7"),
    ("../../models/finetuned/adapters/FT_model/A6_utility_...", 
     "../../models/finetuned/adapters/FT_model/A7_safety_...", 
     "A6_A7"),
]
```

#### パラメータ (57-63行目)
```python
alpha_values = [0.05, 0.07, 0.09, 0.1, 0.12, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
sst_k_values = [5, 10, 20]           # FIM次元数
use_layerwise_options = [True, False] # Layer-wise重み調整
use_gevp_options = [True]             # GEVP使用（Trueを推奨）
sst_max_fim_samples = 500             # FIM計算サンプル数
```

#### データパス (66-72行目)
```python
safety_data_path = "../../data/response_dataframe.csv"

utility_datasets = {
    "A5_A7": {"name": "ServiceNow/repliqa", "split": "repliqa_0"},
    "A6_A7": {"name": "tatsu-lab/alpaca", "split": "train"},
}
```

### 🚀 実行方法
```bash
cd scripts/merging
python3 run_all_merges_interpolation.py
# GPU番号を入力 (例: 0)
```

### 📁 出力先
- **アダプター**: `models/merged/interpolation/adapters/merge_adapters_interpolation/`
- **フルモデル**: `models/merged/interpolation/full/merge_model_interpolation/`

### 📝 出力ファイル名の形式
```
A5_A7_sst_interp_k5_lw_a0.5_adapter/     # アダプター
A5_A7_sst_interp_k5_lw_a0.5/            # フルモデル
```

命名規則：
- `_interp`: 補間型
- `_k5`: FIM次元数k=5
- `_lw`: layerwise=True
- `_nogevp`: GEVP未使用（省略時はGEVP使用）
- `_a0.5`: α=0.5

### ✅ スキップ機能
- **フルモデル存在時**: タスク全体をスキップ
- **アダプターのみ存在時**: マージをスキップ、フルモデル変換のみ実行

実行途中で中断しても、再実行時に既存のモデルは自動的にスキップされます。

---

## 2. Data-Free SST-Merge

### 📂 スクリプト
```bash
scripts/merging/run_data_free_merge.py
```

### 🎯 マージ方式

#### 加算型（デフォルト）
```python
merged = Utility + α × mask × Safety
```

#### 補間型
```python
merged = (1 - α) × Utility + α × mask × Safety
```

### 🌟 特徴
- **データ不要**: 学習データなしでマージ可能
- **高速**: FIM計算にLoRA重みの二乗ノルム近似を使用
- **両モード対応**: 加算型と補間型の両方を実行

### ⚙️ 設定項目

#### マージペア (31-40行目)
```python
merge_pairs = [
    ("../../models/finetuned/adapters/FT_model/A5_utility_...",
     "../../models/finetuned/adapters/FT_model/A7_safety_...",
     "A5_A7"),
    ("../../models/finetuned/adapters/FT_model/A6_utility_...",
     "../../models/finetuned/adapters/FT_model/A7_safety_...",
     "A6_A7"),
]
```

#### パラメータ (43-48行目)
```python
k_values = [5, 10, 20]
use_layerwise_options = [True, False]
merge_mode_options = ["additive", "interpolation"]  # 加算型と補間型
alpha_values = [0.05, 0.07, 0.09, 0.1, 0.12, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
use_gevp = True
top_k_ratio_options = [None]  # None=ソフトマスク
```

### 🚀 実行方法
```bash
cd scripts/merging
python3 run_data_free_merge.py
```

GPU選択プロンプトは**ありません**（自動的にCUDAデバイスを使用）。

### 📁 出力先
- **アダプター**: `models/merged/data_free/adapters/merge_model_data_free/`
- **フルモデル**: `models/merged/data_free/full/merge_model_data_free/`

### 📝 出力ファイル名の形式

#### 加算型
```
A5_A7_data_free_k5_lw_a0.5_topk5/
```

#### 補間型
```
A5_A7_data_free_interp_k5_lw_a0.5_topk5/
```

命名規則：
- `_data_free`: Data-Freeマージ
- `_interp`: 補間型（省略時は加算型）
- `_k5`: k=5
- `_lw`: layerwise=True
- `_a0.5`: α=0.5
- `_topk5`: top_k_ratio=0.05 (k値から自動計算)

### ✅ スキップ機能
- **アダプターとフルモデル両方存在時**: 完全スキップ
- **アダプターのみ存在時**: フルモデル変換のみ実行
- **`adapter_config.json`不足時**: 自動補完

---

## 3. 評価とビジュアライゼーション

### 📊 評価実行
```bash
cd scripts/evaluation
python3 run_all_evals.py
```

評価対象：
- Jailbreak Resistance
- Utility (RepliQA / Alpaca)

### 📈 グラフ生成
```bash
cd scripts/visualization
python3 visualize_sst_merge_detailed.py
```

生成されるグラフ：
- SST-Merge (補間型・加算型)
- Data-Free SST-Merge (加算型・補間型)

出力先: `docs/evaluation_results_202602/`

---

## 4. 比較表

| 項目 | 通常版（補間型） | Data-Free | 
|---|---|---|
| **データ要件** | 必要 | 不要 |
| **FIM計算** | 実データ | LoRA重み近似 |
| **精度** | 高い | 近似的 |
| **速度** | 遅い | 速い |
| **マージ方式** | 補間型のみ | 加算型・補間型 |
| **用途** | 精度重視 | 高速プロトタイピング |

---

## 5. トラブルシューティング

### インポートエラー
```
ModuleNotFoundError: No module named 'sst_merge'
```
**解決策**: `core.sst_merge`からインポートするように修正済み

### アダプターが見つからない
```
FileNotFoundError: Adapter not found
```
**解決策**: アダプターパスを確認（スクリプトからの相対パス `../../models/finetuned/adapters/...`）

### データが見つからない
```
FileNotFoundError: response_dataframe.csv
```
**解決策**: Safety dataのパスを確認（`../../data/response_dataframe.csv`）

### GPU メモリ不足
**解決策**: 
- `sst_max_fim_samples`を減らす（デフォルト: 500）
- バッチサイズを調整

---

## 6. 推奨ワークフロー

### ステップ1: Data-Freeで高速プロトタイピング
```bash
cd scripts/merging
python3 run_data_free_merge.py
```
- 両モード（加算型・補間型）を同時に実行
- データ不要で高速

### ステップ2: 評価
```bash
cd scripts/evaluation
python3 run_all_evals.py
```

### ステップ3: ビジュアライゼーション
```bash
cd scripts/visualization
python3 visualize_sst_merge_detailed.py
```

### ステップ4: 通常版で精度向上
最適なα値とk値が判明したら、通常版で高精度マージ:
```bash
cd scripts/merging
python3 run_all_merges_interpolation.py
```

---

## 7. 出力ファイル構造

```
models/merged/
├── interpolation/              # 通常版（補間型）
│   ├── adapters/
│   │   └── merge_adapters_interpolation/
│   │       └── A5_A7_sst_interp_k5_lw_a0.5_adapter/
│   └── full/
│       └── merge_model_interpolation/
│           └── A5_A7_sst_interp_k5_lw_a0.5/
│
└── data_free/                  # Data-Free
    ├── adapters/
    │   └── merge_model_data_free/
    │       ├── A5_A7_data_free_k5_lw_a0.5_topk5/        # 加算型
    │       └── A5_A7_data_free_interp_k5_lw_a0.5_topk5/ # 補間型
    └── full/
        └── merge_model_data_free/
            ├── A5_A7_data_free_k5_lw_a0.5_topk5/
            └── A5_A7_data_free_interp_k5_lw_a0.5_topk5/
```

---

## 8. パラメータチューニングガイド

### α値 (Safety Weight)
- **0.0-0.2**: Utility優先（低JB耐性、高Utility）
- **0.3-0.7**: バランス
- **0.8-1.0**: Safety優先（高JB耐性、低Utility）

### k値 (FIM次元数)
- **k=5**: 最小マスク（5%のパラメータに適用）
- **k=10**: 中程度マスク
- **k=20**: 大規模マスク（20%のパラメータに適用）

### layerwise
- **True**: 層ごとに異なる重みを適用（推奨）
- **False**: 全層同一重み

### GEVP
- **True**: GEVPマスクを使用（推奨）
- **False**: シンプルな補間/加算のみ
