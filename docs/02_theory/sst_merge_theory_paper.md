# SST-Merge: Safe and Secure Task-specific Model Merging

## 概要

**SST-Merge（Safe and Secure Task-specific Merge）**は、利便性（Utility）と安全性（Safety）のバランスを維持しながら、複数のLoRAアダプターまたはフルモデルをマージする革新的な手法です。本手法は一般化固有値問題（Generalized Eigenvalue Problem, GEVP）に基づくインテリジェントなマスキングを採用し、Utilityへの影響を最小限に抑えながらSafety機能を効果的に統合します。

---

## 1. 導入（Introduction）

### 1.1 背景

大規模言語モデル（LLM）のファインチューニングにおいて、異なるタスク（例えば、Utilityタスクと Safetyタスク）に特化した複数のモデルを統合することは重要な課題です。従来のマージ手法では、以下の問題が存在します：

1. **Utilityの劣化**: Safetyを追加するとUtility性能が大幅に低下
2. **干渉問題**: 異なるタスクのパラメータが互いに干渉
3. **最適化の困難**: Utility-Safety間のトレードオフのバランス調整が困難

### 1.2 SST-Mergeの貢献

SST-Mergeは以下の特徴により、これらの問題を解決します：

- **GEVP-based Masking**: Fisher Information Matrix（FIM）を用いてUtilityに影響するパラメータを自動検出
- **Layer-wise Weighting**: 層ごとに最適なSafety重みを適用
- **Data-Free Variant**: 学習データなしで高速にマージ可能
- **Flexible Merge Modes**: 加算型（Additive）と補間型（Interpolation）をサポート

---

## 2. 理論的基盤（Theoretical Foundation）

### 2.1 Fisher Information Matrix（FIM）

Fisher Information Matrix (FIM) は、パラメータ空間における損失関数の曲率を表し、各パラメータの重要度を定量化します。

#### 2.1.1 FIM の定義

対角FIMは、対数尤度の勾配の分散として近似計算されます：

```
F ≈ E[(∇log p(y|x,θ))²]
```

ここで：
- `θ`: モデルパラメータ
- `p(y|x,θ)`: モデルの条件付き確率分布
- `∇log p(y|x,θ)`: 対数尤度の勾配

#### 2.1.2 FIM の計算アルゴリズム

```
入力: モデル M, データセット D, サンプル数 N
出力: 対角FIM F_diag

1. gradients ← []
2. for each batch in D (最大N個):
3.     batch_grads ← []
4.     outputs ← M(batch)
5.     loss ← -log p(y|x,θ)
6.     loss.backward()
7.     for each param in M.parameters():
8.         batch_grads.append(param.grad.flatten())
9.     gradients.append(concat(batch_grads))
10. F_diag ← variance(gradients) + regularization
11. return F_diag
```

**実装コード** ([sst_merge.py:L135-216](file:///mnt/nas/home/hiromi/src/sst_v2/v1/core/sst_merge.py#L135-L216)):

```python
def compute_fim(self, dataloader, max_samples: int = 200) -> torch.Tensor:
    """対角FIMを勾配分散で近似計算"""
    gradients = []
    for batch in dataloader:
        # バッチ処理
        outputs = self.model(input_ids, attention_mask, labels=input_ids)
        outputs.loss.backward()
        
        # 勾配収集
        batch_grads = [param.grad.detach().cpu().flatten() 
                      for param in self.params if param.grad is not None]
        gradients.append(torch.cat(batch_grads))
    
    # 勾配の分散 → 対角FIM
    fim_diag = torch.stack(gradients).var(dim=0) + self.regularization
    return fim_diag
```

### 2.2 Generalized Eigenvalue Problem（GEVP）

#### 2.2.1 GEVP の定式化

SST-MergeはGEVPを解くことで、Safetyを追加すべきパラメータを特定します：

```
F_harm v = λ F_benign v
```

ここで：
- `F_harm`: Safety FIM（安全性タスクに関する重要度）
- `F_benign`: Utility FIM（利便性タスクに関する重要度）
- `λ`: 固有値（Rayleigh商）
- `v`: 固有ベクトル

#### 2.2.2 Rayleigh Quotient

固有値 `λ_i` は、以下のRayleigh商として解釈できます：

```
λ_i = (v^T F_harm v) / (v^T F_benign v)
```

対角FIMの場合、要素ごとの固有値は：

```
λ_i = F_harm[i] / (F_benign[i] + ε)
```

ここで `ε` は正則化項（数値安定性のため）。

#### 2.2.3 固有値の解釈

- **λ_i が大きい**: 
  - Safety（F_harm）に重要
  - Utility（F_benign）への影響が小さい
  - → **Safetyを安全に追加可能**

- **λ_i が小さい**: 
  - Utility（F_benign）に重要
  - → **変更すべきでない（Utility保持）**

**実装コード** ([sst_merge.py:L235-266](file:///mnt/nas/home/hiromi/src/sst_v2/v1/core/sst_merge.py#L235-L266)):

```python
def solve_gevp_diagonal(self, F_harm: torch.Tensor, F_benign: torch.Tensor):
    """対角FIM用のGEVPを解く"""
    # λ_i = F_harm[i] / F_benign[i]
    eigenvalues = F_harm / (F_benign + self.regularization)
    
    # 降順ソート（高いλが先頭）
    sorted_indices = torch.argsort(eigenvalues, descending=True)
    
    return eigenvalues, sorted_indices
```

### 2.3 Safety Mask の計算

#### 2.3.1 ハードマスク（Top-k Selection）

上位 `k%` のパラメータのみSafetyを適用：

```
mask[i] = {
    1.0  if rank(λ_i) ≤ k
    0.0  otherwise
}
```

#### 2.3.2 ソフトマスク（Log-scale Normalization）

連続的なマスク値を計算：

```
1. log_λ ← log(λ + ε)
2. p5 ← percentile(log_λ, 5%)
3. p95 ← percentile(log_λ, 95%)
4. mask ← clamp((log_λ - p5) / (p95 - p5), 0, 1)
```

**実装コード** ([sst_merge.py:L268-324](file:///mnt/nas/home/hiromi/src/sst_v2/v1/core/sst_merge.py#L268-L324)):

```python
def compute_safety_mask(self, eigenvalues: torch.Tensor, top_k_ratio: Optional[float] = None):
    """固有値λに基づくSafety適用マスクを計算"""
    if top_k_ratio is not None:
        # ハードマスク
        k = int(len(eigenvalues) * top_k_ratio)
        sorted_indices = torch.argsort(eigenvalues, descending=True)
        mask = torch.zeros_like(eigenvalues)
        mask[sorted_indices[:k]] = 1.0
        return mask
    
    # ソフトマスク（Log-scale正規化）
    log_eigenvalues = torch.log(eigenvalues + 1e-10)
    p5 = torch.quantile(log_eigenvalues, 0.05)
    p95 = torch.quantile(log_eigenvalues, 0.95)
    
    normalized = (log_eigenvalues - p5) / (p95 - p5)
    normalized = torch.clamp(normalized, 0.0, 1.0)
    
    return normalized
```

### 2.4 Layer-wise Weighting

異なる層には異なるSafety重みを適用します：

```python
LAYER_WEIGHTS = {
    'lm_head': 1.5,      # 出力層: Safety強め
    'q_proj': 1.2,       # Attention: Safety強め
    'k_proj': 1.2,
    'v_proj': 1.2,
    'o_proj': 1.2,
    'gate_proj': 0.8,    # FFN: Utility保持
    'up_proj': 0.8,
    'down_proj': 0.8,
}
```

---

## 3. SST-Merge 手法の詳細

### 3.1 加算型SST-Merge（Additive SST-Merge）

#### 3.1.1 定式化

加算型SST-Mergeは、Utilityを完全に保持しながらSafetyを追加します：

```
θ_merged[i] = θ_utility[i] + α × w_layer × mask[i] × θ_safety[i]
```

ここで：
- `θ_utility[i]`: Utilityアダプターのi番目のパラメータ
- `θ_safety[i]`: Safetyアダプターのi番目のパラメータ
- `α ∈ [0, 1]`: 基本Safety重み
- `w_layer ∈ [0.8, 1.5]`: Layer-wise重み
- `mask[i] ∈ [0, 1]`: GEVPマスク（高λ方向で大きい）

#### 3.1.2 アルゴリズム

```
入力: θ_utility, θ_safety, D_utility, D_safety, α, use_gevp
出力: θ_merged

if use_gevp:
    # Step 1: Utility FIM計算
    F_benign ← compute_fim(θ_utility, D_utility)
    
    # Step 2: Safety FIM計算
    F_harm ← compute_fim(θ_safety, D_safety)
    
    # Step 3: GEVP解く
    λ, indices ← solve_gevp_diagonal(F_harm, F_benign)
    
    # Step 4: Safety maskを計算
    mask ← compute_safety_mask(λ, top_k_ratio)
    
    # Step 5: マスクを使ってマージ
    for each parameter i:
        w_layer ← get_layer_weight(i)
        θ_merged[i] ← θ_utility[i] + α × w_layer × mask[i] × θ_safety[i]
else:
    # シンプルな加算型マージ
    for each parameter i:
        w_layer ← get_layer_weight(i)
        θ_merged[i] ← θ_utility[i] + α × w_layer × θ_safety[i]

return θ_merged
```

**実装コード** ([sst_merge.py:L521-626](file:///mnt/nas/home/hiromi/src/sst_v2/v1/core/sst_merge.py#L521-L626)):

```python
def _merge_with_mask(self, utility_adapter, safety_adapter, safety_mask):
    """GEVPマスクを使った加算型マージ"""
    merged = {}
    alpha = min(max(self.safety_weight, 0.0), 1.0)
    
    for key in utility_adapter.keys():
        # Layer-wise weight
        layer_weight = 1.0
        if self.use_layerwise_weights:
            for layer_type, weight in self.LAYER_WEIGHTS.items():
                if layer_type in key:
                    layer_weight = weight
                    break
        
        if key in safety_adapter:
            utility_val = utility_adapter[key]
            safety_val = safety_adapter[key]
            
            # 加算型: utility + α × layer_weight × mask × safety
            safety_weight = alpha * layer_weight * param_mask
            merged[key] = utility_val + safety_weight * safety_val
        else:
            merged[key] = utility_adapter[key]
    
    return merged
```

### 3.2 補間型SST-Merge（Interpolation SST-Merge）

#### 3.2.1 定式化

補間型SST-Mergeは、Task Arithmeticと互換性のある補間マージを実行します：

```
θ_merged[i] = (1 - α × w_layer × mask[i]) × θ_utility[i] 
            + α × w_layer × mask[i] × θ_safety[i]
```

これは以下のように簡略化できます：

```
θ_merged[i] = (1 - w_safety[i]) × θ_utility[i] + w_safety[i] × θ_safety[i]
```

ここで：
```
w_safety[i] = α × w_layer × mask[i]
```

#### 3.2.2 加算型との比較

| α値 | Task Arithmetic | 加算型SST-Merge | 補間型SST-Merge |
|-----|----------------|----------------|----------------|
| 0.0 | 100% Utility | 100% Utility | 100% Utility |
| 0.5 | 50% U + 50% S | U + 50% S | **50% U + 50% S** |
| 1.0 | 100% Safety | U + 100% S | **100% Safety** |

補間型はTask Arithmeticと同じ動作をします。

**実装コード** ([sst_merge_interpolation.py](file:///mnt/nas/home/hiromi/src/sst_v2/v1/core/sst_merge_interpolation.py)):

```python
def _interpolation_merge(self, utility_adapter, safety_adapter):
    """補間型マージ"""
    merged = {}
    alpha = self.safety_weight
    
    for key in utility_adapter.keys():
        if key in safety_adapter:
            utility_weight = 1.0 - alpha
            safety_weight = alpha
            merged[key] = utility_weight * utility_val + safety_weight * safety_val
        else:
            merged[key] = utility_val
    
    return merged
```

### 3.3 Data-Free SST-Merge

#### 3.3.1 動機

学習データが利用できない、またはデータプライバシーが重要な場合、Data-Free SST-Mergeを使用します。

#### 3.3.2 LoRAからのFIM近似

LoRAの低ランク構造 `ΔW = B × A` を利用してFIMを近似計算します：

```
FIM ≈ ||ΔW||² = ||B × A||²
```

より具体的には：

```
FIM_diag[i] ≈ (ΔW[i])² + ε
```

where `ΔW = flatten(B @ A)`

#### 3.3.3 アルゴリズム

```
入力: θ_utility (LoRA), θ_safety (LoRA), α, use_gevp
出力: θ_merged

if use_gevp:
    # Step 1: Utility FIMをLoRAから近似
    F_benign ← compute_fim_from_lora(θ_utility)
    
    # Step 2: Safety FIMをLoRAから近似
    F_harm ← compute_fim_from_lora(θ_safety)
    
    # Step 3-5: 通常のSST-Mergeと同じ
    λ, indices ← solve_gevp_diagonal(F_harm, F_benign)
    mask ← compute_safety_mask(λ, top_k_ratio)
    θ_merged ← merge_with_mask(θ_utility, θ_safety, mask)
else:
    # シンプルな加算型/補間型マージ
    θ_merged ← simple_merge(θ_utility, θ_safety, α)

return θ_merged
```

**実装コード** ([sst_merge_data_free.py:L29-69](file:///mnt/nas/home/hiromi/src/sst_v2/v1/core/sst_merge_data_free.py#L29-L69)):

```python
def compute_fim_from_lora(self, adapter_dict: Dict[str, torch.Tensor]):
    """LoRAアダプターからFIMを近似計算（データ不要）"""
    all_weights = []
    
    for key, val in adapter_dict.items():
        if 'lora_A' in key or 'lora_B' in key:
            # LoRAパラメータの絶対値の二乗を重要度として近似
            weight = val.abs().pow(2).flatten()
            all_weights.append(weight)
    
    if not all_weights:
        raise ValueError("No LoRA parameters found")
    
    # 全パラメータを連結
    fim_diag = torch.cat(all_weights)
    
    # 正則化
    fim_diag = fim_diag + self.regularization
    
    return fim_diag
```

#### 3.3.4 制限事項

- **精度**: データベースの手法より性能は劣る
- **k値・layerwiseの影響**: 実装上の課題により影響が小さい場合がある

---

## 4. ベースライン手法（Baseline Methods）

SST-Mergeと比較するため、以下のベースライン手法を実装しています。

### 4.1 Task Arithmetic

#### 4.1.1 定式化

Task Arithmeticは、タスクベクトル（ファインチューニング前後の差分）の重み付き平均を計算します：

```
θ_merged = Σ w_i × θ_i
```

通常、等重み（`w_1 = w_2 = 0.5`）が使用されます。

#### 4.1.2 参考文献

> Ilharco et al., "Editing Models with Task Arithmetic", ICLR 2023

**実装コード** ([baseline_merge.py:L285-307](file:///mnt/nas/home/hiromi/src/sst_v2/v1/scripts/merging/baseline_merge.py#L285-L307)):

```python
def task_arithmetic(self, adapters: List[Dict], weights: List[float]):
    """Task Arithmetic: 重み付き平均"""
    merged = {}
    
    for key in adapters[0].keys():
        weighted_sum = torch.zeros_like(adapters[0][key])
        for adapter, weight in zip(adapters, weights):
            if key in adapter:
                weighted_sum += weight * adapter[key]
        merged[key] = weighted_sum
    
    return merged
```

### 4.2 TIES-Merging

#### 4.2.1 定式化

TIES-Mergingは以下の3ステップで干渉を解決します：

**Step 1: Trim（トリミング）**

絶対値が小さいパラメータを0にします（上位 `density%` のみ保持）：

```
threshold ← topk(|θ|, k)
θ_trimmed[i] = {
    θ[i]  if |θ[i]| ≥ threshold
    0     otherwise
}
```

**Step 2: Elect Sign（符号選定）**

非ゼロパラメータの符号で多数決：

```
sign_sum ← Σ sign(θ_i) × I(θ_i ≠ 0)
elected_sign ← sign(sign_sum)
```

**Step 3: Disjoint Merge（分離マージ）**

選ばれた符号と同じ符号のパラメータのみを加重和：

```
contribution[i] = {
    θ[i]  if sign(θ[i]) = elected_sign
    0     otherwise
}
θ_merged ← Σ w_i × contribution_i
```

#### 4.2.2 参考文献

> Yadav et al., "TIES-Merging: Resolving Interference When Merging Models", NeurIPS 2023

**実装コード** ([baseline_merge.py:L309-368](file:///mnt/nas/home/hiromi/src/sst_v2/v1/scripts/merging/baseline_merge.py#L309-L368)):

```python
def ties_merge(self, adapters: List[Dict], weights: List[float], density: float = 0.5):
    """TIES-Merging: Trim, Elect Sign, Disjoint Merge"""
    merged = {}
    
    for key in adapters[0].keys():
        # Step 1: Trim
        trimmed_params = []
        for param in params:
            threshold = torch.topk(param.abs().flatten(), k).values[-1]
            mask = param.abs() >= threshold
            trimmed = param.clone()
            trimmed[~mask] = 0
            trimmed_params.append(trimmed)
        
        # Step 2: Elect Sign
        stacked = torch.stack(trimmed_params)
        sign_sum = torch.sign(stacked).sum(dim=0)
        elected_sign = torch.sign(sign_sum)
        
        # Step 3: Disjoint Merge
        merged_param = torch.zeros_like(params[0])
        for i, param in enumerate(trimmed_params):
            contribution = param * (torch.sign(param) == elected_sign).float()
            merged_param += weights[i] * contribution
        
        merged[key] = merged_param
    
    return merged
```

### 4.3 DARE (Drop And REscale)

#### 4.3.1 定式化

DAREは、ランダムにパラメータをドロップし、残りをリスケールします：

**Step 1: Drop（ドロップ）**

確率 `p_drop` でパラメータをランダムにドロップ：

```
mask[i] ~ Bernoulli(1 - p_drop)
θ_dropped[i] = θ[i] × mask[i]
```

**Step 2: Rescale（リスケール）**

期待値を保持するためにリスケール：

```
θ_rescaled[i] = θ_dropped[i] / (1 - p_drop)
```

**Step 3: Task Arithmetic**

リスケールされたパラメータをTask Arithmeticでマージ：

```
θ_merged = Σ w_i × θ_rescaled_i
```

#### 4.3.2 参考文献

> Yu et al., "Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch", ICML 2024

**実装コード** ([baseline_merge.py:L370-405](file:///mnt/nas/home/hiromi/src/sst_v2/v1/scripts/merging/baseline_merge.py#L370-L405)):

```python
def dare_merge(self, adapters: List[Dict], weights: List[float], drop_rate: float = 0.9):
    """DARE: Drop And REscale"""
    merged = {}
    rescale_factor = 1.0 / (1.0 - drop_rate)
    
    for key in adapters[0].keys():
        params = []
        for adapter in adapters:
            param = adapter[key].clone()
            # ランダムドロップ
            mask = torch.rand_like(param.float()) > drop_rate
            # リスケール
            dropped = param * mask.float() * rescale_factor
            params.append(dropped)
        
        # Task Arithmetic
        weighted_sum = torch.zeros_like(params[0])
        for param, weight in zip(params, weights):
            weighted_sum += weight * param
        merged[key] = weighted_sum
    
    return merged
```

---

## 5. パラメータ設定と実験

### 5.1 SST-Merge パラメータ

| パラメータ | 記号 | 説明 | デフォルト値 | 範囲 |
|-----------|------|------|------------|------|
| Safety Weight | `α` | 基本Safety重み | 0.5 | 0.0-1.0 |
| Top-k Ratio | `k` | Top-k固有値の選択比率（%） | - | 5, 10, 20 |
| GEVP Mask | `use_gevp` | GEVPマスク使用フラグ | True | True/False |
| Layerwise | `use_layerwise` | Layer-wise重み調整 | False | True/False |
| Merge Mode | `mode` | マージモード | additive | additive/interpolation |
| Regularization | `ε` | FIM正則化項 | 1e-6 | - |
| Max Samples | `N` | FIM計算の最大サンプル数 | 200 | - |

### 5.2 実験結果サマリー（α=0.1の場合）

| 手法 | Jailbreak Resistance | Alpaca ROUGE-L | バランス |
|------|---------------------|---------------|---------|
| **SST-Merge (k=5, GEVP, layerwise)** | **76.00%** | **70.59%** | ⭐️ 最良 |
| SST-Merge補間型 (k=5, GEVP) | 76.00% | 70.59% | 良 |
| Data-Free (k=5) | 79.20% | 66.82% | 中 |
| Task Arithmetic | 72.80% | 70.05% | 参考 |
| DARE | 0.00% | 0.02% | 不安定 |

### 5.3 主要な発見

#### 5.3.1 GEVP効果

- **GEVP有効**: Utility性能を維持しながらSafetyを向上
- **GEVP無効**: 高いSafety（最大100%）だが、Utilityが大幅低下

#### 5.3.2 α値の影響

- **低α（0.1-0.3）**: Utilityを保持、Safetyは中程度
- **高α（0.8-1.0）**: 高いSafety、Utilityは低下
- **推奨**: α=0.1でバランス最良

#### 5.3.3 Data-Freeの限界

- k値とlayerwiseの影響が小さい
- 学習データベースの手法より性能は劣る

---

## 6. 実装詳細（Implementation）

### 6.1 ファイル構成

```
sst_merge_v5/
├── core/                          # SST-Merge実装（コアライブラリ）
│   ├── sst_merge.py              # メインSST-Merge（加算型）
│   ├── sst_merge_interpolation.py # 補間型
│   └── sst_merge_data_free.py     # Data-Free版
│
├── scripts/merging/               # マージ実行スクリプト
│   ├── run_all_merges_adapter_based.py  # SST-Merge（adapter）
│   ├── run_all_merges_interpolation.py  # 補間型
│   ├── run_data_free_merge.py           # Data-Free
│   └── baseline_merge.py                # Baseline（TA/TIES/DARE）
│
└── docs/                          # ドキュメント
    └── evaluation_results_202602/ # 実験結果レポート
```

### 6.2 使用例

#### 6.2.1 加算型SST-Merge

```python
from core.sst_merge import SSTMerge

# SST-Mergeインスタンス作成
sst_merge = SSTMerge(
    safety_weight=0.5,           # α
    use_layerwise_weights=True,  # Layer-wise重み調整
    use_gevp=True,               # GEVPマスク使用
    top_k_ratio=0.05,            # Top-5%
    device='cuda'
)

# マージ実行
merged_model = sst_merge.merge(
    model=base_model,
    tokenizer=tokenizer,
    utility_adapter=utility_adapter,
    safety_adapter=safety_adapter,
    utility_dataloader=utility_dataloader,
    safety_dataloader=safety_dataloader,
    max_samples=200
)
```

#### 6.2.2 補間型SST-Merge

```python
from core.sst_merge_interpolation import SSTMergeInterpolation

sst_merge = SSTMergeInterpolation(
    safety_weight=0.5,
    use_gevp=True,
    top_k_ratio=0.05
)

merged_model = sst_merge.merge(...)
```

#### 6.2.3 Data-Free SST-Merge

```python
from core.sst_merge_data_free import SSTMergeDataFree

sst_merge = SSTMergeDataFree(
    safety_weight=0.5,
    use_gevp=True,
    top_k_ratio=0.05,
    merge_mode="additive"  # または "interpolation"
)

# データローダー不要
merged_adapter = sst_merge.merge(
    utility_adapter=utility_adapter,
    safety_adapter=safety_adapter
)
```

---

## 7. 結論（Conclusion）

SST-Mergeは、GEVP-basedマスキングとLayer-wise重み調整により、Utility-Safetyのトレードオフを効果的に管理する革新的なモデルマージ手法です。本手法の主な貢献は：

1. **理論的基盤**: FIMとGEVPに基づく厳密な理論的定式化
2. **柔軟性**: 加算型、補間型、Data-Free variantをサポート
3. **実用性**: 実験により、従来手法を上回る性能を実証
4. **拡張性**: フルモデルとLoRAアダプターの両方に対応

今後の研究課題として、以下が挙げられます：

- Data-Free版の精度向上
- より多様なタスクペアでの評価
- より大規模なモデル（70B+）への適用
- マルチタスクマージ（3つ以上のタスク）への拡張

---

## 参考文献（References）

1. Ilharco et al., "Editing Models with Task Arithmetic", ICLR 2023
2. Yadav et al., "TIES-Merging: Resolving Interference When Merging Models", NeurIPS 2023
3. Yu et al., "Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch", ICML 2024
4. Amari, "Natural Gradient Works Efficiently in Learning", Neural Computation 1998 (FIM理論)
5. Kirkpatrick et al., "Overcoming catastrophic forgetting in neural networks", PNAS 2017 (FIM応用)

---

## 付録（Appendix）

### A. 数学的記号一覧

| 記号 | 説明 |
|------|------|
| `θ` | モデルパラメータ |
| `F` | Fisher Information Matrix |
| `λ` | GEVP固有値 |
| `α` | Safety重み（基本） |
| `w_layer` | Layer-wise重み |
| `mask` | GEVPマスク |
| `ε` | 正則化項 |
| `N` | サンプル数 |

### B. 計算複雑度

| 操作 | 計算複雑度 | 備考 |
|------|-----------|------|
| FIM計算 | O(N × P) | N: サンプル数, P: パラメータ数 |
| GEVP解法（対角） | O(P) | 対角FIMの場合 |
| Safety Mask計算 | O(P log P) | ソート必要 |
| マージ | O(P) | 線形時間 |

### C. 実装上の注意点

1. **メモリ管理**: FIM計算時にGPUメモリを大量に消費するため、適切なバッチサイズとサンプル数を設定
2. **数値安定性**: 固有値計算時の正則化（ε = 1e-6）が重要
3. **パーセンタイル計算**: 大きなテンソル（>100,000要素）の場合はサンプリングで計算
4. **パラメータマッチング**: LoRAアダプターのキー名マッチングに注意

---

**文書作成日**: 2026年2月12日  
**バージョン**: v5.0  
**著者**: SST-Merge開発チーム
