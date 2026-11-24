# 外部コード監査レポート（`v3/baselines/`：P1〜P5 の実装事実）

- 監査日: 2026-11-24
- 対象: `v3/baselines/` に配置されている外部公開コード 4 種（SafeMERGE、LED-Merging、MergeAlign、mergekit）および `v3/scripts/mergers/{baselines,mergekit}.py` の呼び出し設定
- 方針: 結論を先に決めず、ソースコードに書かれている事実のみを行番号付きで記録する（問題が見つからない項目は「問題なし／該当処理なし」と明記する）。

---

## 1. 監査結果サマリー（P1〜P5）

| 外部実装 | P1（崩れた出力の扱い） | P2（判定器の数・種類） | P3（係数・比較） | P4（系統・設定継承） | P5（数値精度・実効統計ログ） |
|:---|:---|:---|:---|:---|:---|
| **SafeMERGE** (`baselines/SafeMERGE/`) | 評価コード非同梱（記載なし） | 評価コード非同梱（記載なし） | 既定 `cos_threshold=0.35`, `weighting=[0.8, 0.2]`（`get_safemerge_model.py` L83-85） | PEFT アダプタのみ保存（L73）。ベース設定継承は呼び出し側依存 | **射影行列・コサイン計算は明示的 `float32`**（`utils.py` L57, L88-90）。**層ごとの判定・マージ数を `safemerge_layer_weights.json` に自動記録**（L145-176）。ただし射影行列と LoRA 層は名前ではなく位置インデックス順で照合（L278-299）、形状不一致時は `cos=1.0` を返してスキップ（L92-100） |
| **LED-Merging** (`baselines/LED-Merging/`) | 同梱 `HarmBench/` 評価器に崩壊出力フィルタなし | 同梱は `HarmBench` 単一評価系 | 固定係数 `--scaling_coefficient 0.9`, `--fuse_rates 0.5 0.5`（`v3` 呼び出し: `baselines.py` L62-64） | 保存時は常に `pretrained_model` の config/tokenizer を使用（`merge_llms.py` L90-92）。語彙数のみ `align_tokenizers_and_embeddings` で調整（L60-62）。`rope_theta` 等の継承なし | スコア算出は `bfloat16`（`locate/main.py` L85。fp16 より下限が広く即アンダーフローは起きにくい）。マスク生成は **`>= threshold` を複数関数で使用**（`mask_weights_utils.py` L114-115, L148-149, L238-239, L339-340, L657。一方 L537, L644 は `>`）。**マージ時の実効マスク比率・退化検証ログは出力なし**（`prune.py` L44-93 のスパース率確認関数はマージから未呼出） |
| **MergeAlign** (`baselines/MergeAlign/`) | **崩壊出力の除外なし**: `infer.py` L155-158 は `"unsafe"` 文字列の有無のみで `1 - unsafe/total` を算出（崩壊応答が `"unsafe"` にならなければ安全側に計上） | **単一判定器**（`Meta-Llama-Guard-2-8B`、`bfloat16`、`infer.py` L43-45） | `--temp` 1 パラメータ。データシャッフルに seed 固定なし（`lmcocktail_merge_align.py` L19, L30 `ds.shuffle()`） | 外部 `LM_Cocktail.mix_models_with_data` へ委譲（L141-149） | マージ本体は `LM_Cocktail` へ委譲しており、ラッパー側では **計算 dtype・実効重み・退化の検証ログなし**（公式ライブラリ側のタイポ引数 `example_ata=` を使用、L144） |
| **mergekit** (`baselines/mergekit/`) | 評価コード非同梱 | 評価コード非同梱 | 呼び出し側の YAML 指定に依存（`v3` は `density=0.5`, `weight=α` / `(1-α)/n`） | `--copy-tokenizer` でベース側をコピー、`--allow-crimes` で異系統・形状差も警告停止せず通過（`v3/scripts/mergers/mergekit.py` L56） | 呼び出し側が `dtype: "float16"` を指定（`mergekit.py` L36）。`generalized_task_arithmetic.py` L122 はテンソル dtype（未指定時 `float16`）で演算。`arcee_fusion.py` L56 は `>= threshold`、`sce.py` L69 は `torch.topk(...).indices`。**マージ時の実効マスク比率・退化ログの自動出力はなし** |

---

## 2. 監査から得られた客観的な知見（SoK での位置付け）

1. **P5（数値精度と実装忠実度）について — 「全外部コードに fp16 バグがある」わけではない**
   - **SafeMERGE** は射影・コサイン計算を明示的に `float32` で行い、さらに層ごとの判定結果とマージ層数を JSON に保存しており、実装忠実度の検証慣行として良好な事例である。
   - **LED-Merging** は `bfloat16` を使っており、`v3` の SST のような fp16 特有の $6\times 10^{-8}$ アンダーフロー自体は直ちには起きない。一方でマスク生成に `>= threshold` を使いつつマージ時の実効マスク比率を記録しない点、**MergeAlign**・**mergekit** がマージ内部の実効統計（重み分布・実効スパース率・退化有無）を出力しない点は確認された。
   - したがって SoK における P5 の主張は、「外部実装すべてに fp16 バグがある」と断定するのではなく、**「数値精度や実効マスク比率・退化チェックを論文・コードで検証・報告する慣行が欠けているため（SafeMERGE のように層ログを出す例は少数派）、ひとたび fp16 キャスト＋`>= threshold` のような不整合が入ると手法が黙って別手法に退化しても誰も気づかない」** と位置付けるのが事実に忠実かつ査読に強い。

2. **P1・P2（崩壊応答の扱いと単一判定器）は外部公式コードでも直接確認された**
   - **MergeAlign** の公式評価スクリプト（`baselines/MergeAlign/evaluation/llama_guard_eval/infer.py` L43-45, L155-158）は、単一判定器（`Meta-Llama-Guard-2-8B`）で `"unsafe"` の部分一致のみを数え、崩れた出力を除外・分離する処理を一切持たない。

3. **P4（設定継承・系統チェック）は外部マージツール共通の空白**
   - **LED-Merging**（`merge_llms.py` L90-92）と **mergekit**（`--allow-crimes`）のいずれも、ユーティリティ側の `rope_theta` 等の推論設定継承や、モデル系統の事前検証（相対差分チェック等）を自動では行わない。
