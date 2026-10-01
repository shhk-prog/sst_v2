# SST-Merge V2: Safety-Preserving Subspace Task-Merge

**SafetyとUtility両方を維持する改善版SST-Merge実装**

## 📋 概要

SST-Merge V2は、元のSST-Mergeの問題点を解決し、**Jailbreak攻撃耐性90%以上**と**Utility維持**の両立を目指す改善版実装です。

### 従来のSST-Mergeの問題点

| 問題 | 原因 | 結果 |
|------|------|------|
| Safety性能の大幅な低下 | Safetyアダプターを直交サブスペースに完全射影 | Jailbreak耐性: 77%（ベースライン: 99%+） |
| 理論と実践の乖離 | 射影によりSafety情報が失われる | Safety Tax削減目標未達成 |

### SST-Merge V2の解決策

1. **Residual Safety Injection**: 射影後も元のSafety情報を保持
2. **Layer-wise Projection**: 層ごとに異なる射影強度を適用
3. **Direct Addition Mode**: 射影なしの直接追加モード（ベースライン相当）

---

## 🚀 クイックスタート

### 1. Direct Mode（最高のSafety性能）

```bash
cd sst_merge_v2

# A5+A7 マージ（射影なし、ベースライン相当）
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode direct \
    --safety_weight 1.0
```

### 2. Residual Mode（推奨：Safety/Utility両立）

```bash
# A5+A7 マージ（Residual ratio 0.7）
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode residual \
    --residual_ratio 0.7 \
    --safety_weight 1.0
```

### 3. 評価

```bash
python scripts/evaluate.py \
    --adapter results/llama-3.1-8b/sst_v2_A5_A7_*.pt \
    --model llama-3.1-8b
```

---

## 📊 モード比較

| モード | Jailbreak耐性 | MMLU | 新規性 | 推奨用途 |
|--------|--------------|------|--------|----------|
| `direct` | ~99% | ~53% | 低（TA相当） | ベースライン比較 |
| `residual` (r=0.7) | ~95% | ~53% | 中 | **推奨** |
| `residual` (r=0.5) | ~90% | ~54% | 中-高 | Safety/Utility調整 |
| `layerwise` | ~90% | ~54% | 高 | 研究用途 |

---

## 🔧 パラメータ説明

### 主要パラメータ

| パラメータ | 説明 | 推奨値 |
|-----------|------|--------|
| `mode` | マージモード | `residual` |
| `residual_ratio` | 元のSafety保持率 | `0.7` |
| `safety_weight` | Safety追加の重み | `1.0` |
| `k` | サブスペース次元数 | `10-20` |

### Residual Ratio の影響

```
residual_ratio = 0.0  →  完全射影（従来SST-Merge）→ Safety低下
residual_ratio = 0.5  →  半分保持、半分射影      →  バランス
residual_ratio = 0.7  →  70%保持、30%射影       →  Safety重視（推奨）
residual_ratio = 1.0  →  射影なし（直接追加）    →  ベースライン相当
```

### Layer-wise Projection Presets

```bash
# Safety重視
python scripts/run_merge.py --mode layerwise --preset safety_first

# バランス（デフォルト）
python scripts/run_merge.py --mode layerwise --preset balanced

# Utility重視
python scripts/run_merge.py --mode layerwise --preset utility_first
```

---

## 📁 ディレクトリ構造

```
sst_merge_v2/
├── src/
│   ├── __init__.py           # パッケージ初期化
│   ├── sst_merge_v2.py       # メインアルゴリズム
│   └── layer_config.py       # 層別設定
├── scripts/
│   ├── run_merge.py          # マージ実行スクリプト
│   ├── evaluate.py           # 評価スクリプト
│   └── run_experiments.sh    # 実験バッチスクリプト
├── configs/
│   └── default.yaml          # デフォルト設定
├── results/                  # 実験結果
└── README.md                 # このファイル
```

---

## 🧪 実験の実行

### 全実験を一括実行

```bash
chmod +x scripts/run_experiments.sh
./scripts/run_experiments.sh
```

### 実行される実験条件（合計19実験）

#### Phase 1: Direct Mode（3実験）- GPU不要

| # | Variant | Mode | Safety Weight | 備考 |
|---|---------|------|---------------|------|
| 1 | A5+A7 | direct | 1.0 | ベースライン |
| 2 | A6+A7 | direct | 1.0 | ベースライン |
| 3 | A5+A6+A7 | direct | 1.0 | ベースライン |

#### Phase 2: Residual Mode（9実験）- ⚠️ GPU必須

| # | Variant | residual_ratio | Safety Weight |
|---|---------|----------------|---------------|
| 4-6 | A5+A7 | 0.5, 0.7, 0.9 | 1.0 |
| 7-9 | A6+A7 | 0.5, 0.7, 0.9 | 1.0 |
| 10-12 | A5+A6+A7 | 0.5, 0.7, 0.9 | 1.0 |

#### Phase 3: Safety Weight Variation（3実験）- GPU不要

| # | Variant | Mode | Safety Weight |
|---|---------|------|---------------|
| 13 | A5+A7 | direct | 0.5 |
| 14 | A5+A7 | direct | 1.0 |
| 15 | A5+A7 | direct | 1.5 |

#### Phase 4: Layerwise Mode（4実験）- ⚠️ GPU必須

| # | Variant | Preset | 備考 |
|---|---------|--------|------|
| 16 | A5+A7 | safety_first | FIM計算あり |
| 17 | A5+A7 | balanced | FIM計算あり |
| 18 | A5+A7 | utility_first | FIM計算あり |
| 19 | A5+A7 | minimal | FIM計算あり |

#### 実行時間の目安

| Phase | 実験数 | GPU | 推定時間 |
|-------|--------|-----|----------|
| Phase 1 | 3 | 不要 | ~1分 |
| Phase 2 | 9 | **必須** | ~30分〜数時間 |
| Phase 3 | 3 | 不要 | ~1分 |
| Phase 4 | 4 | **必須** | ~20分〜1時間 |

#### GPU環境がない場合（Direct Modeのみ実行）

```bash
# Phase 1 + Phase 3 のみ実行
for variant in A5+A7 A6+A7 A5+A6+A7; do
    python scripts/run_merge.py --model llama-3.1-8b --variant $variant --mode direct --safety_weight 1.0
done

for weight in 0.5 1.0 1.5; do
    python scripts/run_merge.py --model llama-3.1-8b --variant A5+A7 --mode direct --safety_weight $weight
done
```

### カスタム実験

```python
from src.sst_merge_v2 import SSTMergeV2

# Residual mode（推奨）
merger = SSTMergeV2(
    k=10,
    mode="residual",
    residual_ratio=0.7,
    device="cuda"
)

merged = merger.merge_utility_safety(
    model=None,  # direct modeではモデル不要
    utility_adapters=[A5_adapter, A6_adapter],
    safety_adapter=A7_adapter,
    safety_weight=1.0
)

merger.save_merged_adapter(merged, "results/merged.pt")
```

---

## 📈 期待される結果

### Direct Mode（ベースライン相当）

| 評価指標 | 期待値 | 備考 |
|----------|--------|------|
| Jailbreak耐性 | ~99% | ベースラインと同等 |
| MMLU Accuracy | ~53% | Utility維持 |

### Residual Mode（r=0.7、推奨）

| 評価指標 | 期待値 | 備考 |
|----------|--------|------|
| Jailbreak耐性 | 90-95% | わずかに低下 |
| MMLU Accuracy | ~54% | Utility維持または改善 |

---

## 🔬 理論的背景

### SST-Mergeの核心理論

SST-Mergeは、モデルマージングを**制約付き最適化問題**として定式化します：

```
目標: 安全性のゲイン（Gain）を最大化しつつ、有用性のコスト（Cost）を最小化

λ = φᵀ F_harm φ / φᵀ F_benign φ  (安全効率 = Safety Gain / Utility Cost)
```

#### Fisher Information Matrix (FIM)

| FIM | データソース | 意味 |
|-----|------------|------|
| `F_harm` | 有害データ（拒否応答） | パラメータ変化がSafety向上にどれだけ効くか |
| `F_benign` | 良性データ（通常タスク） | パラメータ変化がUtility低下にどれだけ繋がるか |

#### 一般化固有値問題 (GEVP)

```
F_harm v = λ F_benign v

解の意味:
- 固有値 λ が大きい方向 → 「Safety効率が高い」（Utilityを害さずSafetyを改善可能）
- 固有値 λ が小さい方向 → 「Safety Tax が高い」（Safetyを上げるとUtilityも下がる）
```

上位k個の固有ベクトルで張られる空間が**安全サブスペース (Safety Subspace)** です。

---

## 🔄 Residual Mode（推奨）

### 理論

従来のSST-Mergeでは、Safetyアダプターを安全サブスペースに完全射影することで、重要なSafety情報が失われていました。

**Residual Safety Injection**は、射影されたSafetyと元のSafetyをブレンドすることで、この問題を解決します：

```
# 射影されたSafety
safety_projected = V_k @ (V_kᵀ @ safety_original)

# ブレンド（residual_ratio = r）
blended_safety = (1 - r) × safety_projected + r × safety_original

# 最終マージ
merged = utility + safety_weight × blended_safety
```

### residual_ratio の解釈

```
r = 0.0  →  完全射影（従来SST-Merge）
             Safety情報が大幅に失われる
             Jailbreak耐性: ~77%

r = 0.5  →  半分保持、半分射影
             Safety/Utilityのバランス
             Jailbreak耐性: ~90%

r = 0.7  →  70%保持、30%射影（推奨）
             Safetyを優先しつつ理論的新規性を保持
             Jailbreak耐性: ~95%

r = 1.0  →  射影なし（Direct Modeと同等）
             ベースライン相当、新規性なし
             Jailbreak耐性: ~99%
```

### 使用例（GPU必須）

```bash
# FIM/GEVP計算を使用するResidual Mode
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode residual \
    --residual_ratio 0.7 \
    --k 10 \
    --max_samples 1000 \
    --safety_weight 1.0
```

### Pythonコード例

```python
from src.sst_merge_v2 import SSTMergeV2

merger = SSTMergeV2(
    k=10,                    # 安全サブスペース次元
    mode="residual",         # Residual Safety Injection
    residual_ratio=0.7,      # 70%元のSafetyを保持
    fim_approximation="gradient_variance",
    device="cuda"            # GPU必須
)

merged = merger.merge_utility_safety(
    model=base_model,        # ベースモデル（FIM計算に必要）
    utility_adapters=[A5, A6],
    safety_adapter=A7,
    utility_dataloader=utility_dl,   # Utilityデータ
    safety_dataloader=safety_dl,     # Safetyデータ
    max_samples=1000,
    safety_weight=1.0
)
```

---

## 🔧 Layerwise Mode（研究用途）

### 理論

ニューラルネットワークの各層は、SafetyとUtilityに対して異なる感度を持っています：

- **Attention層** (`q_proj`, `k_proj`, `v_proj`): Safetyに強く影響
- **FFN層** (`gate_proj`, `up_proj`, `down_proj`): Utilityに強く影響

**Layer-wise Soft Projection**は、層ごとに異なる射影強度を適用します：

```
# 層ごとの射影強度 (0.0 = 射影なし, 1.0 = 完全射影)
strength = get_projection_strength(layer_name, preset)

# ソフト射影
soft_projected = (1 - strength) × safety_original + strength × safety_projected

# 最終マージ
merged[layer] = utility[layer] + safety_weight × soft_projected
```

### Layer Projection Presets

#### `safety_first` (Safety重視)

```python
LAYER_PROJECTION_CONFIG["safety_first"] = {
    'q_proj': 0.3,      # 弱い射影 → Safety情報保持
    'k_proj': 0.3,
    'v_proj': 0.5,
    'o_proj': 0.7,      # 強い射影 → Utility保護
    'gate_proj': 0.8,
    'up_proj': 0.8,
    'down_proj': 0.8,
}
```

#### `utility_first` (Utility重視)

```python
LAYER_PROJECTION_CONFIG["utility_first"] = {
    'q_proj': 0.6,      # 中程度の射影
    'k_proj': 0.6,
    'v_proj': 0.8,
    'o_proj': 0.9,      # 非常に強い射影 → Utility最大保護
    'gate_proj': 0.9,
    'up_proj': 0.9,
    'down_proj': 0.9,
}
```

#### `balanced` (バランス)

```python
LAYER_PROJECTION_CONFIG["balanced"] = {
    'q_proj': 0.4,
    'k_proj': 0.4,
    'v_proj': 0.6,
    'o_proj': 0.7,
    'gate_proj': 0.7,
    'up_proj': 0.7,
    'down_proj': 0.7,
}
```

### 使用例（GPU必須）

```bash
# Layer-wise Projection Mode
python scripts/run_merge.py \
    --model llama-3.1-8b \
    --variant A5+A7 \
    --mode layerwise \
    --preset safety_first \
    --k 10 \
    --safety_weight 1.0
```

---

## 📊 3つのモードの比較

| 特性 | Direct | Residual | Layerwise |
|-----|--------|----------|-----------|
| **FIM/GEVP計算** | ❌ 不要 | ✅ 必要 | ✅ 必要 |
| **GPU** | ❌ 不要 | ✅ 必須 | ✅ 必須 |
| **計算時間** | 秒 | 分〜時間 | 分〜時間 |
| **理論的新規性** | 低（TA相当） | 中〜高 | 高 |
| **Jailbreak耐性** | ~99% | 90-95% | 90-95% |
| **MMLU** | ~53% | ~54% | ~54% |
| **推奨用途** | ベースライン比較 | **実運用** | 研究・論文 |

### アルゴリズムフロー

```
Direct Mode:
  Utility + Safety → Merged (単純加算)

Residual Mode:
  1. F_utility, F_safety 計算 (FIM)
  2. GEVP解法 → 安全サブスペース V_k
  3. Safety射影 → safety_projected
  4. ブレンド: (1-r)×projected + r×original
  5. Merged = Utility + blended_safety

Layerwise Mode:
  1. F_utility, F_safety 計算 (FIM)
  2. GEVP解法 → 安全サブスペース V_k
  3. 各層ごとに射影強度を決定
  4. ソフト射影: (1-s)×original + s×projected
  5. Merged = Utility + soft_projected_safety
```

---

## 🎯 新規性の整理

| 手法 | アプローチ | 数学的ツール | Safety Tax対策 |
|-----|----------|------------|---------------|
| **Task Arithmetic** | 線形結合 | ベクトル加算 | ❌ なし |
| **TIES-Merging** | 方向性・大きさ | 符号判定 | ⚠️ 間接的 |
| **DARE** | 幾何学的 | SVD | ⚠️ 偶発的 |
| **AlignGuard-LoRA** | 防御的 | 単一FIM | ✅ 静的制約 |
| **SST-Merge V2** | 能動的最適化 | **二つのFIM + GEVP** | ✅ **直接最適化** |

### SST-Merge V2の新規性

1. **二つのFIM** (`F_harm`, `F_benign`) で安全性と有用性を同時に測定
2. **GEVP** で両者のトレードオフを数学的に最適化
3. **Residual Injection** でSafety情報の損失を防止
4. **Layer-wise Projection** で細粒度の制御を実現

---

## 📚 参考文献

- [Task Arithmetic (ICLR 2023)](https://arxiv.org/abs/2212.04089)
- [TIES-Merging (NeurIPS 2023)](https://arxiv.org/abs/2306.01708)
- [DARE](https://arxiv.org/abs/2311.03099)

---

## ⚠️ 注意事項

### GPU要件

| モード | GPU | 備考 |
|--------|-----|------|
| `direct` | ❌ 不要 | CPUのみでアダプターマージ可能 |
| `residual` | ✅ **必須** | FIM計算にモデル順伝播が必要 |
| `layerwise` | ✅ **必須** | FIM計算にモデル順伝播が必要 |

### モード選択ガイド

```
Q: GPU環境がありますか？
├─ No  → Direct Mode（ベースライン相当）
└─ Yes → Q: 理論的新規性が必要ですか？
          ├─ No  → Direct Mode
          └─ Yes → Residual Mode (r=0.7) 推奨
```

### 推奨ワークフロー

1. **まずDirect Mode**で実験し、ベースライン相当の性能を確認
2. **GPU環境で**Residual Mode (r=0.7)を実行
3. 必要に応じて`residual_ratio`を調整（0.5〜0.9）
4. 論文・研究用途ではLayerwise Modeも検討

### トラブルシューティング

| 問題 | 原因 | 解決策 |
|------|------|--------|
| `CUDA out of memory` | FIM計算でメモリ不足 | `--max_samples`を減らす |
| Jailbreak耐性が低い | residual_ratioが低すぎる | `--residual_ratio 0.8`以上に |
| MMLU低下 | safety_weightが高すぎる | `--safety_weight 0.8`に調整 |
| FIM計算が遅い | サンプル数が多い | `--max_samples 500`に |

---

## 🤝 既存コードとの関係

このモジュールは既存の`SST_merge2/src/`のコードを変更せず、新しいフォルダ内で完結しています。

```python
# 既存のモジュールを利用
from src.fim_calculator import FIMCalculator  # 親ディレクトリから
from src.gevp_solver import GEVPSolver        # 親ディレクトリから
```

---

## 📝 ライセンス

MIT License
