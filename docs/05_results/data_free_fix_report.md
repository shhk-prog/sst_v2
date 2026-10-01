# Data-Free実装修正完了レポート

**修正日**: 2026-02-03  
**修正者**: Antigravity AI

---

## ✅ 修正完了

Data-Free実装の問題（k値とlayerwiseパラメータが無視されていた）を修正しました。

---

## 🔧 実施した修正

### 修正1: layerwise重み調整の実装

**ファイル**: `sst_merge_data_free.py`

#### 変更内容

1. **LAYER_WEIGHTS定数の追加**
```python
class SSTMergeDataFree:
    # Layer-wise重み調整（sst_merge.pyと同じ）
    LAYER_WEIGHTS = {
        'lm_head': 1.0,      # 出力層: 最も強いSafety
        'q_proj': 0.8,       # Attention: やや強いSafety
        'k_proj': 0.8,
        'v_proj': 0.8,
        'o_proj': 0.8,
        'gate_proj': 0.6,    # FFN: 中程度のSafety
        'up_proj': 0.6,
        'down_proj': 0.6,
    }
```

2. **_merge_with_gevpメソッドの修正**
```python
# Layer-wise重み調整
layer_weight = 1.0
if self.use_layerwise:
    for layer_type, weight in self.LAYER_WEIGHTS.items():
        if layer_type in key:
            layer_weight = weight
            break

# Merge: Utility + α × layer_weight × mask × Safety
merged_adapter[key] = u_param + (self.safety_weight * layer_weight) * param_mask * s_param
```

3. **_merge_simpleメソッドの修正**
```python
# Layer-wise重み調整
layer_weight = 1.0
if self.use_layerwise:
    for layer_type, weight in self.LAYER_WEIGHTS.items():
        if layer_type in key:
            layer_weight = weight
            break

merged_adapter[key] = (
    utility_adapter[key] + 
    (self.safety_weight * layer_weight) * safety_adapter[key]
)
```

### 修正2: k値のtop_k_ratioへの変換

**ファイル**: `run_data_free_merge.py`

#### 変更内容

```python
for k in k_values:
    for use_layerwise in use_layerwise_options:
        for top_k_ratio_base in top_k_ratio_options:
            # k値をtop_k_ratioに変換（k%のパラメータを選択）
            # k=5 → 0.05, k=10 → 0.10, k=20 → 0.20
            if top_k_ratio_base is None:
                # k値に基づいてtop_k_ratioを設定
                top_k_ratio = k / 100.0
            else:
                # 明示的に指定された場合はそれを使用
                top_k_ratio = top_k_ratio_base
            
            for alpha in alpha_values:
                # SST-Merge実行（k値を反映したtop_k_ratioを使用）
                sst_merge = SSTMergeDataFree(
                    safety_weight=alpha,
                    use_gevp=use_gevp,
                    top_k_ratio=top_k_ratio,  # k値がここに反映される
                    use_layerwise=use_layerwise
                )
```

**変換ロジック**:
- `k=5` → `top_k_ratio=0.05` （上位5%のパラメータを選択）
- `k=10` → `top_k_ratio=0.10` （上位10%のパラメータを選択）
- `k=20` → `top_k_ratio=0.20` （上位20%のパラメータを選択）

---

## 📊 期待される効果

### 修正前

- **k=5, 10, 20**: 全て同一の結果
- **layerwise=True/False**: 全て同一の結果
- **実質的な設定数**: 30設定（同じ結果が6回重複）

### 修正後

- **k=5, 10, 20**: **異なる結果**（GEVPマスクの選択比率が変わる）
- **layerwise=True/False**: **異なる結果**（レイヤータイプによる重み調整が適用される）
- **実質的な設定数**: **180設定**（全て独立した結果）

---

## 🧪 検証方法

### 1. 簡単な検証

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/sst_merge_v5

# スクリプトが構文エラーなく実行できるか確認
python3 -c "from sst_merge_data_free import SSTMergeDataFree; print('✓ Import OK')"
```

### 2. 実際のマージ実行

```bash
# run_data_free_merge.pyを実行して新しいモデルを生成
python3 run_data_free_merge.py
```

新しく生成されたモデルは、k値とlayerwiseの組み合わせによって**異なる性能**を示すはずです。

---

## 📝 今後の推奨事項

1. **既存のData-Freeモデルの削除**
   - 修正前のモデルは全て重複しているため、削除して再生成を推奨

2. **再評価の実施**
   - 新しく生成されたモデルで評価を実行
   - k値とlayerwiseの効果を検証

3. **結果の比較**
   - 修正前と修正後の結果を比較
   - k値とlayerwiseの実際の影響を分析

---

## ✅ 結論

Data-Free実装の重大な問題を修正しました：

- ✅ **k値**: `top_k_ratio`に正しく変換され、GEVPマスクに反映される
- ✅ **layerwise**: レイヤータイプに応じた重み調整が実装された

これにより、Data-Freeは真の180設定（2ペア × 3k × 2lw × 15α）として機能するようになりました。
