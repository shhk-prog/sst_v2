# Matena Fisher-Weighted Averaging の統合実装計画（最終確定版）

## 背景と目的

`baselines/model_merging` には Matena & Wortsman (NeurIPS 2022) の公式実装がすでに clone 済み。
本タスクでは **公式の数式** を踏襲しつつ **PyTorch/CausalLM** で再実装し、比較手法 `matena_fisher` として既存パイプラインに統合する。

---

## 公式実装の調査結果と問題点

公式実装は **TensorFlow + TFBert/TFRoberta + GLUE** 向けで設計されており、Llama-2/CausalLM には非対応：

| 非対応要素 | 理由 |
|---|---|
| `TFAutoModelForSequenceClassification` | GLUE分類専用 |
| `tf.GradientTape` | TensorFlowのみ |
| `hdf5_util.py` | TensorFlow変数のみ保存可能 |
| `data.py` | GLUEデータセット専用 |

---

## 確定した実装方針

**Matena 再実装（PyTorch/CausalLM 向け）**：公式の数式を完全に踏襲し、計算基盤を既存パイプラインに合わせる。

### 確定パラメータ

| 項目 | 設定 | 理由 |
|---|---|---|
| **対象パラメータ** | `TARGET_MODULE_KEYWORDS` のみ（q/k/v/o/gate/up/down proj） | 既存 `fisher_weighted`/SST と比較条件を統一。全パラメータは計算コスト過大 |
| **L2 ノルム正規化** | `normalize_fishers=True`（デフォルト） | 論文の設定に従う |
| **Fisher floor** | `1e-6`（config 指定可能） | 数値安定性 |
| **FIM キャッシュ** | `cache/fim/*.pt` を再利用 | 既存キャッシュが整備済み |

> [!NOTE]
> `TARGET_MODULE_KEYWORDS` は attention（q/k/v/o）と MLP（gate/up/down）の両方を含む。
> 正確な表現：**既存 SST/Fisher 実装と同じ target modules（q/k/v/o/gate/up/down projection）のみに限定**。

> [!IMPORTANT]
> **target modules 以外のパラメータは `base_model` の重みをそのまま使用する**。これは比較手法として保守的な設計である。この事実を `merge_metadata.json` に必ず記録する（後述）。

---

## FIM キャッシュの互換性（重要）

既存の `estimate_fim()` は `is_target_weight(name)` で対象を絞っており、保存済みキャッシュは **`TARGET_MODULE_KEYWORDS` のパラメータに対する FIM のみ** を含む。

| 実装パターン | 既存キャッシュ再利用 | 備考 |
|---|---|---|
| `matena_fisher`（target modules のみ） | ✅ **再利用可能** | 本実装がここ |
| `matena_fisher_all_params`（全パラメータ） | ❌ **再利用不可** | ablation 時は FIM 再計算が必要 |

**再利用できるキャッシュ（seed=42, n=500 の例）：**
```
cache/fim/benign_math_Llama2_WizardMath_n500_seed42.pt
cache/fim/harmful_safety_Llama2_SafetyFT_n500_seed42.pt
```

> [!WARNING]
> 将来 `matena_fisher_all_params` を実装する際は、既存キャッシュを流用しないこと。
> `fisher_target_params` が `all_params` の場合は `reused_existing_fim_cache: false` とすること。

---

## Matena Fisher の数式

$$\theta^* = \frac{\sum_i F_i \odot \theta_i}{\sum_i F_i + \epsilon}$$

コード内コメント用の正確な表記：
```
theta = sum_i(F_i * theta_i) / (sum_i F_i + epsilon)
```

L2 ノルム正規化あり（`normalize_fishers=True` 時）：$F_i \leftarrow F_i / \|F_i\|_2$

---

## 変更ファイル一覧（実装済み）

### [NEW] `scripts/matena_fisher.py`

`run_matena_fisher()` 関数を実装。

- 戻り値：`merged_state_dict, matena_info = run_matena_fisher(...)` に統一
- target modules のみ FIM 重み付き平均
- それ以外は base_model の重みをそのまま使用（保守的設計、metadata に記録）

### [MODIFY] `scripts/merge.py`

1. `CUSTOM_BASELINES = ["fisher_weighted", "matena_fisher"]`
2. `get_complexity_info()` に `"matena_fisher": "O(N * C_backward + P)"` を追記
3. `fim_required` 判定を全 2 箇所で更新（`"matena_fisher"` を追加）
4. `execute_merge()` に `matena_fisher` 専用分岐を追加
5. `save_success_metadata()` に `method_metadata=None` 引数を追加、`"method_metadata"` キーで保存
6. `matena_fisher_info.json` を別ファイルとして出力

### [MODIFY] `scripts/run_experiments.py`

```python
CUSTOM_SINGLE_RUN_METHODS = {"fisher_weighted", "matena_fisher", "safemerge", "led_merging", "mergealign"}
```

### `scripts/steering_hook.py`

変更不要。`matena_fisher` は `official_mergekit_methods` に含まれないため、`implementation` チェックを通過する。

---

## method_metadata の内容

`merge_metadata.json` の `method_metadata.matena_fisher` に以下を保存：

```json
{
  "implementation": "causallm_reimplementation",
  "reference_repo": "mmatena/model_merging",
  "paper": "Merging Models with Fisher-Weighted Averaging (NeurIPS 2022)",
  "formula": "theta = sum_i(F_i * theta_i) / (sum_i F_i + epsilon)",
  "normalize_fishers": true,
  "normalization": "global_l2",
  "fisher_floor": 1e-6,
  "fisher_target_params": "target_modules_only",
  "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
  "non_target_params_treatment": "use_base_model_weights",
  "reused_existing_fim_cache": true,
  "uses_cached_fim": true
}
```

---

## Ablation 計画（後から追加）

| Variant | method 名 | 変更点 | FIM キャッシュ |
|---|---|---|---|
| デフォルト | `matena_fisher` | target_modules_only + normalize=True | ✅ 再利用可 |
| 正規化 ablation | `matena_fisher_nonorm` | normalize=False | ✅ 再利用可 |
| 対象パラメータ ablation | `matena_fisher_all_params` | 全パラメータ対象 | ❌ 再計算必要 |

---

## 検証コマンド

```bash
python scripts/merge.py \
  --method matena_fisher \
  --pattern safety+math \
  --output_dir results/matena_fisher_test \
  --seed 42
```
