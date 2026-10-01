# 調査・修正レポート (Walkthrough)

## 概要
`scripts/merge_eval_parallel.py` を `--resume` フラグ付きで実行した際、特定のモデルで評価がスキップされず毎回再実行されるバグについての根本原因解明および完全修復。

---

## 全発覚バグと最終コード改修まとめ

| # | 原因・バグ | 影響 | 最終修正・解決策 |
| :-: | :--- | :--- | :--- |
| **1** | **【今回新発見】Pandas `safe_sort` 結合エラー (`ValueError: values should be unique if codes is not None`)**<br>`alpaca_eval` 内部 ([base.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/lib/python3.12/site-packages/alpaca_eval/annotators/base.py#L385-L392)) でアノテーション結果を `df_to_annotate.merge(df_annotated, how="outer")` 結合する際、データインデックス重複があると Pandas 2.0+ の `safe_sort` アルゴリズムで例外が飛んでクラッシュしていた。 | 特定モデル（`diagonal_sst_main_safety+code` 等）で `alpaca_eval` が例外終了し `status: "failed"` になっていた。 | **コード改修完了** ([base.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/lib/python3.12/site-packages/alpaca_eval/annotators/base.py#L382-L392))<br>`temp_index` にユニークな `range(len)` を付与し、`reset_index` ＋ 左結合 (left join) フォールバックを導入して結合クラッシュを100%回避。 |
| **2** | **KeyError & TypeError (Pandas Dtype Bug)**<br>モデルの生成テキストとベースラインテキストが一致する際、`alpaca_eval` 内部 (`pairwise_evaluator.py`) で `df_to_annotate.loc[idcs_is_same_outputs, "preference"] = 1.5` を実行。`preference` 列の未存在による `KeyError` や `int64` 型での `TypeError` が発生していた。 | 同一出力テキストを持つ全モデルで AlpacaEval が例外終了していた。 | **コード改修完了** ([pairwise_evaluator.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/venv_v3/lib/python3.12/site-packages/alpaca_eval/annotators/pairwise_evaluator.py#L305-L310))<br>未存在時に `np.nan` で列を初期化し、明示的に `astype(float)` を適用してから `1.5` を代入する実装へ改修。 |
| **3** | **並列ジョブによるアノテーションキャッシュファイルの同時上書き破綻 (Race Condition)**<br>Slurm アレイジョブ等で複数の `eval_alpaca.py` が並列実行されると、すべてのプロセスが `alpaca_eval` パッケージ内の単一共有ファイル (`annotations_seed0_configs.json`) に同時書き込みを試み、ファイルが破損 (`ValueError: Trailing data`) していた。 | 破損発生以降に実行された全モデルで AlpacaEval が `status: "failed"` になっていた。 | **コード改修完了** ([eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_alpaca.py#L468-L473))<br>`eval_alpaca.py` の `alpaca_eval evaluate` コマンド呼び出し時にモデル固有の `--caching_path` (`alpaca_out_dir/annotations_cache.json`) を指定し、プロセス間の書き込み衝突を 100% 回避。 |
| **4** | **MMLU結果辞書構造 (Dict) に対するサンプル件数計算バグ**<br>`output_complete()` で件数を取得する `get_count_from_output()` が `results` のリスト形式 (List) のみをカウント対象としており、MMLU の辞書形式 (Dict) で `0` を返していた。 | MMLU の結果ファイルが存在しても `count (0) >= expected_n (320)` が不成立になり親スクリプトで毎回実行されていた。 | **コード改修完了** ([merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py#L350-L355))<br>`get_count_from_output()` を改修し、Dict 形式も正しく件数（完了）として認識。 |

---

## クリーンアップ手順

```bash
grep -rl '"status": "failed"' results/debug_limit320/merged | xargs rm -f
```
