# Data-Free実装の問題点分析レポート

**調査日**: 2026-02-03  
**問題**: k値とlayerwiseパラメータの設定に関わらず、全て同一の結果が出力される

---

## 🔴 発見された問題

### 1. **k値が完全に無視されている**

#### コード: `run_data_free_merge.py` (行213-229)

```python
for k in k_values:  # ← ループは回るが
    for use_layerwise in use_layerwise_options:
        for top_k_ratio in top_k_ratio_options:
            for alpha in alpha_values:
                # SST-Merge実行
                sst_merge = SSTMergeDataFree(
                    safety_weight=alpha,
                    use_gevp=use_gevp,
                    top_k_ratio=top_k_ratio,
                    use_layerwise=use_layerwise
                )
                # ← k値がコンストラクタに渡されていない！
```

**問題点**:
- `k` 値がループで回っているが、`SSTMergeDataFree`のコンストラクタに**一切渡されていない**
- k値は出力ファイル名にのみ使用されている（行232: `output_name = f"{pair_name}_data_free_k{k}"`）
- **実際のマージ処理では全く使われていない**

### 2. **layerwiseパラメータが実装されていない**

#### コード: `sst_merge_data_free.py` - `__init__` (行163-186)

```python
def __init__(
    self,
    safety_weight: float = 0.5,
    use_gevp: bool = True,
    regularization: float = 1e-6,
    top_k_ratio: Optional[float] = None,
    use_layerwise: bool = False  # ← 受け取るが...
):
    self.safety_weight = safety_weight
    self.use_gevp = use_gevp
    self.regularization = regularization
    self.top_k_ratio = top_k_ratio
    self.use_layerwise = use_layerwise  # ← 保存されるが使われない！
```

**問題点**:
- `use_layerwise` パラメータは受け取って保存されるが、**マージ処理で一切参照されていない**
- コメントに「将来の拡張用」と書かれており、**未実装**であることが明記されている

### 3. **マージ実装でlayerwiseが無視されている**

#### コード: `sst_merge_data_free.py` - `_merge_with_gevp` (行215-257)

```python
def _merge_with_gevp(...):
    # ... (FIM計算、GEVP解法、マスク計算)
    
    for key in utility_adapter.keys():
        u_param = utility_adapter[key]
        s_param = safety_adapter[key]
        
        param_numel = u_param.numel()
        param_mask = mask[idx:idx+param_numel].reshape(u_param.shape)
        
        # Merge: Utility + α × mask × Safety
        merged_adapter[key] = u_param + self.safety_weight * param_mask * s_param
        # ← layerwiseによる重み調整が一切ない！
```

**問題点**:
- `self.safety_weight` が全パラメータに一律適用されている
- レイヤータイプ（attention, mlp, outputなど）による重み調整が**全く実装されていない**

---

## 📊 影響範囲

### 結果への影響

1. **k値**: 
   - 設定: `k_values = [5, 10, 20]`
   - 実態: **全て同一のマージ結果**
   - ファイル名だけが異なる

2. **layerwise**:
   - 設定: `use_layerwise_options = [True, False]`
   - 実態: **True/Falseで結果が変わらない**
   - ファイル名だけが異なる

### 実際の設定数

- **想定**: 2ペア × 3k値 × 2layerwise × 15α値 = **180設定**
- **実態**: 2ペア × 1実装 × 1実装 × 15α値 = **30設定** （同じ結果が6回コピーされている）

---

## 🔧 修正方法

### 修正1: k値の実装

**現在のtop_k_ratioを活用**:

```python
# run_data_free_merge.py
for k in k_values:
    # k値からtop_k_ratioを計算
    # 例: k=5 → top_k_ratio=0.05, k=10 → 0.10, k=20 → 0.20
    top_k_ratio = k / 100.0  # またはパラメータ総数に対する割合
    
    sst_merge = SSTMergeDataFree(
        safety_weight=alpha,
        use_gevp=use_gevp,
        top_k_ratio=top_k_ratio,  # ← k値を反映
        use_layerwise=use_layerwise
    )
```

### 修正2: layerwiseの実装

**sst_merge.pyと同様のレイヤー重み調整を追加**:

```python
# sst_merge_data_free.py に追加
LAYER_WEIGHTS = {
    'lm_head': 1.0,      # 出力層: 強いSafety
    'q_proj': 0.8,       # Attention: やや強いSafety
    'k_proj': 0.8,
    'v_proj': 0.8,
    'o_proj': 0.8,
    'gate_proj': 0.6,    # FFN: 中程度Safety
    'up_proj': 0.6,
    'down_proj': 0.6,
}

def _merge_with_gevp(...):
    for key in utility_adapter.keys():
        # レイヤータイプによる重み調整
        layer_weight = 1.0
        if self.use_layerwise:
            for layer_type, weight in LAYER_WEIGHTS.items():
                if layer_type in key:
                    layer_weight = weight
                    break
        
        # 調整後のマージ
        merged_adapter[key] = u_param + (self.safety_weight * layer_weight) * param_mask * s_param
```

---

## ✅ 結論

Data-Free実装には**未実装**または**誤実装**の機能が複数存在します：

1. ✗ **k値**: 完全に無視されている
2. ✗ **layerwise**: 受け取るが使用されていない
3. ✓ **α値**: 正しく実装されている
4. ✓ **GEVP**: 正しく実装されている

これにより、実験結果は**見かけ上180設定**あるように見えるが、**実際には30設定の結果が6回重複**しているだけです。
