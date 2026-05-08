# SST-Merge v5 各段階の詳細図解

**作成日:** 2026-02-12  
**v5実装ベース・F_utility表記使用**

本ドキュメントは、SST-Merge v5の各処理段階を詳細に図解したものです。実装コードの理論と数式に基づいています。

---

## 📊 全体フロー図

SST-Mergeの処理は6つの主要ステージで構成されます。

![SST-Merge全体フロー](sst_merge_overall_flow_1770896992310.png)

### Stage 1: 入力 (Input)

**入力データ:**
- **Utility Adapter** ($\theta_{\text{utility}}$): 有用性タスクに特化したLoRAアダプター
  - 例: RepliQA学習済みLoRA、質問応答能力
- **Safety Adapter** ($\theta_{\text{safety}}$): 安全性タスクに特化したLoRAアダプター
  - 例: 有害応答拒否LoRA、危険な質問への拒否能力

### Stage 2: FIM計算 (Fisher Information Matrix)

**並列処理で2つのFIMを計算:**

$$
F_{\text{utility}}[i] \approx \text{Var}(\nabla_{\theta_i} \mathcal{L}_{\text{utility}})
$$

$$
F_{\text{safety}}[i] \approx \text{Var}(\nabla_{\theta_i} \mathcal{L}_{\text{safety}})
$$

- **F_utility**: Utilityデータ ($D_{\text{utility}}$) における各パラメータの重要度
- **F_safety**: Safetyデータ ($D_{\text{safety}}$) における各パラメータの重要度

### Stage 3: GEVP求解 (Generalized Eigenvalue Problem)

**固有値計算:**

$$
\lambda_i = \frac{F_{\text{safety}}[i]}{F_{\text{utility}}[i]}
$$

**解釈:**
- $\lambda_i$が大きい → Safety重視可能（Safetyに重要、Utilityへの影響小）
- $\lambda_i$が小さい → Utility保持が重要（Utilityに重要、Safetyへの影響小）

### Stage 4: Safety Mask計算

**対数スケール正規化:**

$$
m_i = \text{normalize}(\log(\lambda_i))
$$

- **出力:** $[0, 1]$の連続値
- **意味:** 各パラメータへのSafety適用度

### Stage 5: マージ実行 (Merge)

**加算型マージ式:**

$$
\theta_{\text{merged}}[i] = \theta_{\text{utility}}[i] + \alpha \cdot w_{\text{layer}} \cdot m_i \cdot \theta_{\text{safety}}[i]
$$

**構成要素:**
- $\alpha$: 基本Safety重み（例: 0.5）
- $w_{\text{layer}}$: Layer-wise重み（例: lm_headは1.5）
- $m_i$: GEVPマスク（$[0, 1]$の連続値）

### Stage 6: 出力 (Output)

**マージ済みAdapter** ($\theta_{\text{merged}}$):
- ✅ 高い安全性
- ✅ 高い有用性

---

## 🧮 FIM計算の詳細プロセス

Fisher Information Matrix (FIM) は、各パラメータの重要度を測定します。

![FIM計算の詳細](fim_calculation_detail_1770897024858.png)

### Step 1: データバッチ処理

```python
for batch in dataloader:
    # Mini-batch: x₁, x₂, ..., xₙ
```

データセットから順次バッチを取得します。

### Step 2: 順伝播と損失計算

```python
outputs = model(inputs)
loss = -log p(y|x, θ)
```

**損失関数:**
- 負の対数尤度（Negative Log-Likelihood）
- モデルの予測精度を測定

### Step 3: 逆伝播

```python
loss.backward()
# ∇θᵢL を計算
```

各パラメータに対する勾配を計算します。

### Step 4: 勾配収集

```python
gradients.append(∇θ)
# [∇θ⁽¹⁾, ∇θ⁽²⁾, ..., ∇θ⁽ⁿ⁾]
```

各サンプルの勾配を保存し、スタックします。

### Step 5: 分散計算 → FIM

**理論:**

$$
F_{\text{utility}}[i] = \text{Var}(\nabla_{\theta_i} \mathcal{L}_{\text{utility}})
$$

**実装:**

$$
F_{\text{utility}}[i] = \frac{1}{n}\sum_{j=1}^{n}(\nabla_{\theta_i}^{(j)})^2 - \left(\frac{1}{n}\sum_{j=1}^{n}\nabla_{\theta_i}^{(j)}\right)^2
$$

**意味:** 勾配の分散 = パラメータの重要度

### Step 6: 正則化

```python
F[i] = F[i] + ε
# ε = 1e-6 (数値安定性)
```

ゼロ除算を防ぐための正則化項を追加します。

### Output

**F_utility**: `[total_params]`次元テンソル
- 各パラメータの重要度を表す
- 例: `[0.012, 0.345, 0.001, ...]`

### 📌 実装バリエーション

**右側パネルに示された2つの方式:**

#### 1. Data-Dependent版
- データセットを使用してFIMを計算
- 高精度だがデータが必要

#### 2. Data-Free版
$$
F[i] \approx \|\theta_i\|^2
$$
- LoRAパラメータのみ使用
- データ不要で高速

---

## 🔄 GEVP求解とSafety Mask計算

**（画像生成クォータのため、数式と説明で補足）**

### GEVP（一般化固有値問題）の求解

**入力:**
- F_utility (Utility FIM) - 青色
- F_safety (Safety FIM) - 赤色

**固有値計算:**

$$
\lambda_i = \frac{F_{\text{safety}}[i]}{F_{\text{utility}}[i] + \varepsilon}
$$

**固有値の解釈表:**

| $\lambda_i$の値 | パラメータ特性 | マージ戦略 |
|----------------|--------------|-----------|
| $\lambda_i \gg 1$ | Safety重要<br/>Utility影響小 | Safety強く適用 |
| $\lambda_i \approx 1$ | 両方同程度 | バランス調整 |
| $\lambda_i \ll 1$ | Utility重要<br/>Safety影響小 | Safety控えめ |

### Safety Mask計算

**2つの方式:**

#### ソフトマスク（デフォルト）

**Step 1: 対数変換**
$$
\log \lambda = \log(\lambda_i + 10^{-10})
$$

**Step 2: パーセンタイル計算**
$$
p_5 = \text{quantile}(\log \lambda, 0.05)
$$
$$
p_{95} = \text{quantile}(\log \lambda, 0.95)
$$

**Step 3: 正規化**
$$
m_i = \frac{\log \lambda - p_5}{p_{95} - p_5}
$$

**Step 4: クリップ**
$$
m_i = \text{clamp}(m_i, 0, 1)
$$

**出力:** 連続値マスク $[0, 1]$

**視覚化:** グラデーション 0（低） → 1（高）

#### ハードマスク（top_k指定時）

**Step 1: 降順ソート**

**Step 2: Top-k選択**
$$
k = \text{int}(\text{total\_params} \times \text{top\_k\_ratio})
$$

**Step 3: バイナリマスク**
$$
m_i = \begin{cases}
1 & \text{if } i \in \text{Top-}k \\
0 & \text{otherwise}
\end{cases}
$$

**出力:** 0 or 1 のマスク

**視覚化:** バイナリ（0または1）

---

## 🎚️ Layer-wise重み調整の仕組み

ニューラルネットワークの各層は異なる役割を持つため、層ごとに安全性の適用度を調整します。

### ニューラルネットワーク構造（下から上）

```
┌─────────────────────────────────────┐
│  lm_head (出力層)                   │  w_layer = 1.5
│  ▸ 最終応答生成                     │  ▸ Safety最重要
│  ▸ 赤色（最高Safety）               │
└─────────────────────────────────────┘
           ↑
┌─────────────────────────────────────┐
│  Attention層                        │  w_layer = 1.2
│  (q_proj, k_proj, v_proj, o_proj)   │  ▸ Safety重視
│  ▸ 文脈理解・応答品質               │
│  ▸ オレンジ色                       │
└─────────────────────────────────────┘
           ↑
┌─────────────────────────────────────┐
│  FFN層                              │  w_layer = 0.8
│  (gate_proj, up_proj, down_proj)    │  ▸ Utility優先
│  ▸ 知識保持・推論                   │
│  ▸ 青色                             │
└─────────────────────────────────────┘
           ↑
┌─────────────────────────────────────┐
│  Embedding層                        │  w_layer = 0.5
│  ▸ 入力表現                         │  ▸ Utility保持
│  ▸ 水色                             │
└─────────────────────────────────────┘
```

### Layer-wise重み一覧表

| 層タイプ | $w_{\text{layer}}$ | 役割 |
|---------|-------------------|------|
| lm_head | 1.5 | 出力（最重要） |
| q/k/v/o_proj | 1.2 | Attention |
| gate/up/down_proj | 0.8 | FFN（知識） |
| embedding | 0.5 | 入力表現 |

### 最終適用重みの計算

**公式:**

$$
w_{\text{final}}[i] = \alpha \times w_{\text{layer}} \times m_i
$$

**計算例:**

lm_headの第100パラメータの場合:
- $\alpha = 0.5$ (基本Safety重み)
- $w_{\text{layer}} = 1.5$ (lm_head重み)
- $m_i = 0.8$ (GEVPマスク値)
- → $w_{\text{final}} = 0.5 \times 1.5 \times 0.8 = 0.6$

**視覚的表現（ヒートマップ）:**

```
赤（最高Safety）   lm_head (1.5)        ████████
オレンジ          Attention (1.2)      ██████
黄                Default (1.0)        █████
青                FFN (0.8)            ████
水色（低Safety）   Embedding (0.5)      ██
```

---

## 🔀 マージ処理の詳細

SST-Mergeには2つのマージ方式があります。

### 加算型 (Additive)

**入力:**
- $\theta_{\text{utility}}[i]$ (青)
- $\theta_{\text{safety}}[i]$ (赤)
- $\alpha = 0.5$
- $w_{\text{layer}} = 1.2$
- $m_i = 0.7$

**マージ式:**

$$
\theta_{\text{merged}}[i] = \theta_{\text{utility}}[i] + \alpha \cdot w_{\text{layer}} \cdot m_i \cdot \theta_{\text{safety}}[i]
$$

**ステップごとの計算:**

**Step 1: Safety重み計算**
$$
w = \alpha \times w_{\text{layer}} \times m_i = 0.5 \times 1.2 \times 0.7 = 0.42
$$

**Step 2: Safety成分**
$$
\text{safety\_component} = 0.42 \times \theta_{\text{safety}}[i]
$$

**Step 3: 加算**
$$
\theta_{\text{merged}}[i] = \theta_{\text{utility}}[i] + \text{safety\_component}
$$

**視覚化:**
```
Utility:  ████████████████████ (完全保持)
Safety:   ████████ (0.42倍で追加)
Merged:   ████████████████████████████ (合計)
```

**特徴:**
- ✓ Utility完全保持
- ✓ Safetyを追加

### 補間型 (Interpolation)

**入力:**（加算型と同じ）

**マージ式:**

$$
\theta_{\text{merged}}[i] = (1 - \alpha \cdot w_{\text{layer}} \cdot m_i) \cdot \theta_{\text{utility}}[i] + \alpha \cdot w_{\text{layer}} \cdot m_i \cdot \theta_{\text{safety}}[i]
$$

**ステップごとの計算:**

**Step 1: 重み計算**
$$
w = \alpha \times w_{\text{layer}} \times m_i = 0.42
$$
$$
w_{\text{utility}} = 1 - 0.42 = 0.58
$$
$$
w_{\text{safety}} = 0.42
$$

**Step 2: 重み付け**
$$
\text{utility\_component} = 0.58 \times \theta_{\text{utility}}[i]
$$
$$
\text{safety\_component} = 0.42 \times \theta_{\text{safety}}[i]
$$

**Step 3: 補間**
$$
\theta_{\text{merged}}[i] = \text{utility\_component} + \text{safety\_component}
$$

**視覚化:**
```
Utility (58%):  ███████████ 
Safety (42%):   ████████ 
Merged (100%):  ███████████████████ (合計は常に100%)
```

**特徴:**
- ✓ 重み付き平均
- ✓ Task Arithmetic互換

### 比較表

| 項目 | Additive | Interpolation |
|------|----------|---------------|
| Utility | 完全保持 | 部分保持 |
| Safety | 追加 | 置換（補間） |
| 合計 | >100%可能 | 常に100% |

---

## 📚 まとめ

本ドキュメントでは、SST-Merge v5の各処理段階を詳細に図解しました:

1. **全体フロー**: 入力 → FIM → GEVP → マスク → マージ → 出力
2. **FIM計算**: 勾配の分散としてパラメータ重要度を算出
3. **GEVP求解**: F_safety / F_utilityで固有値を計算
4. **Safety Mask**: 対数正規化またはTop-k選択
5. **Layer-wise調整**: 層の役割に応じた重み設定
6. **マージ処理**: Additive（加算型）とInterpolation（補間型）

すべて **F_utility** 表記を使用し、v5の実装コードに基づいています。

---

**作成日:** 2026-02-12  
**v5実装ベース**
