# Implementation Plan - v3/scripts の整理

`v3/scripts` 内にフラットに配置されている 38 個のスクリプト群を役割ごとに整理し、不要な一時ファイルや修復用スクリプトを隔離・分類することで、コードベースの保守性と見通しを向上させます。

---

## User Review Required

> [!IMPORTANT]
> - `v3/scripts/` 直下に配置されていた修正スクリプト（`fix_*_jsons.py`, `clean_*_results.py` 等）は、トラブルシューティング用のユーティリティとして `v3/scripts/fixes/` ディレクトリに退避します。
> - 評価スクリプト（`eval_*.py`）や各種ツールスクリプトのディレクトリ移動に伴い、`run_experiments.py` や `merge_eval_parallel.py` などの自動化スクリプト内および `v3/README.md` 内の呼び出しパスを安全に一括更新します。

---

## Proposed Changes

### 1. 不要メタファイルの削除
- macOS 固有のメタファイル (`.DS_Store`, `._.DS_Store`, `._run_base_eval_parallel.py`, `._run_mergekit_parallel.py`) の削除。

### 2. ディレクトリ構造の再編成 (`v3/scripts/` 内)

新しいディレクトリ構造イメージ:

```text
v3/scripts/
├── [Top-level Entrypoints & Runners]
│   ├── run_experiments.py          # 全工程一括実行ランナー
│   ├── merge.py                    # マージ CLI エントリーポイント
│   ├── merge_eval_parallel.py      # 並列マージ・評価ランナー
│   ├── run_base_eval_parallel.py   # ベースモデル評価ランナー
│   ├── run_mergekit_parallel.py    # mergekit並列ランナー
│   ├── fine_tuning.py              # Safety model SFT 学習
│   ├── data_prep.py                # FIM 推定データ配置
│   ├── setup_env.sh                # 自動ビルド
│   └── mergers/                    # マージコアパッケージ
│
├── eval/                           # 評価・ベンチマーク系スクリプト
│   ├── eval_safety.py
│   ├── eval_utility.py
│   ├── eval_alpaca.py
│   ├── eval_instruction_datasets.py
│   ├── eval_hirundo_unlearning.py
│   └── check_harmbench_results.py
│
├── merging/                        # マージ手法・補助スコア計算系
│   ├── compute_datafree_importance.py
│   ├── matena_fisher.py
│   ├── prepare_led_scores.py
│   └── elect_led_masks.py
│
├── analysis/                       # 解析・集計・視覚化系
│   ├── pareto_auc.py
│   ├── generate_tables.py
│   └── count_dataset_sizes.py
│
├── tools/                          # モデル・環境ユーティリティ
│   ├── create_dummy_models.py
│   └── create_full_model.py
│
├── tests/                          # テスト・動的検証系
│   ├── test_merge_all.py
│   ├── steering_hook.py
│   └── test_steering_hook.py
│
└── fixes/                          # データ修正・クリーンアップ系ユーティリティ (単発・復旧用)
    ├── fix_all_alpaca_eval_jsons.py
    ├── fix_humaneval_jsons.py
    ├── fix_ifeval_jsons.py
    ├── fix_mbpp_jsons.py
    ├── fix_mmlu_pro_jsons.py
    ├── clean_failed_results.py
    ├── clean_ifeval_results.py
    └── verify_mbpp_fix.py
```

---

### 3. 呼び出しパスの更新

以下のファイルに含まれる内部スクリプトの呼び出しパスを新しい配置に合わせて変更します：

- [MODIFY] `v3/scripts/run_experiments.py` (`scripts/eval_*.py` -> `scripts/eval/eval_*.py` 等)
- [MODIFY] `v3/scripts/merge_eval_parallel.py`
- [MODIFY] `v3/scripts/run_base_eval_parallel.py`
- [MODIFY] `v3/scripts/run_mergekit_parallel.py`
- [MODIFY] `v3/scripts/prepare_led_scores.py`
- [MODIFY] `v3/scripts/tests/test_merge_all.py`
- [MODIFY] `v3/scripts/eval/eval_hirundo_unlearning.py`
- [MODIFY] `v3/README.md` (ディレクトリ構成およびコマンド記述の更新)

---

## Verification Plan

### Automated Tests
- 各種構文エラー・パスエラーの確認:
  ```bash
  python3 -m py_compile v3/scripts/run_experiments.py
  python3 -m py_compile v3/scripts/merge_eval_parallel.py
  python3 -m py_compile v3/scripts/run_base_eval_parallel.py
  ```
- テスト実行:
  ```bash
  python3 v3/scripts/tests/test_steering_hook.py
  ```

### Manual Verification
- `python3 v3/scripts/run_experiments.py --help` が正常に起動することを確認。
- 各移動スクリプトのインポートエラー等が発生しないことを確認。
