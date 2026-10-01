# 実装計画書: merged ディレクトリの pattern 別階層再編成

`results/debug_limit320/merged` ディレクトリ内の結果ファイルについて、`seed` ディレクトリの直下にドメインパターン (`safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`) の階層を追加し、今後の実験実行でも同階層構造で出力されるように修正・再編成します。

---

## ユーザー確認・承認事項

> [!IMPORTANT]
> 既存の `results/debug_limit320/merged/seed<seed>/<method>/` 配下にあるすべての JSON ファイルおよび AlpacaEval 出力ディレクトリ（`*_alpaca_eval_out`）を、ファイル名に含まれるパターン名に応じて `results/debug_limit320/merged/seed<seed>/<pattern>/<method>/` へ移動します。
> また、今後実行される `merge_eval_parallel.py` 等の自動化スクリプトの出力先パス生成ロジックも新しい階層構造に同期更新します。

---

## 現状と変更後の構造比較

### 変更前 (Current)
```text
results/debug_limit320/merged/
├── seed42/
│   ├── dare/
│   │   ├── sst_merge_v3_main_dare_safety+math_alpha0.2_seed42_...json
│   │   └── sst_merge_v3_main_dare_safety+code_alpha0.2_seed42_...json
│   ├── diagonal_sst_main/
│   └── ...
├── seed43/
└── seed44/
```

### 変更後 (Proposed)
```text
results/debug_limit320/merged/
├── seed42/
│   ├── safety+math/
│   │   ├── dare/
│   │   └── ...
│   ├── safety+code/
│   │   ├── dare/
│   │   └── ...
│   ├── safety+medical/
│   │   ├── dare/
│   │   └── ...
│   └── safety+math+code+medical/
│       ├── dare/
│       └── ...
├── seed43/
└── seed44/
```

---

## 変更対象ファイルおよび作業手順

### 1. 既存結果データの整理スクリプト作成 & 実行
- スクリプト: `docs/organize_merged_results_by_pattern/organize_pattern_dirs.py` (scratch / 実行用)
- 処理内容:
  1. `results/debug_limit320/merged/seed<seed>/<method>/` 配下のファイルおよび `*_alpaca_eval_out` ディレクトリを走査。
  2. ファイル名・ディレクトリ名から `safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical` を判定。
  3. `seed<seed>/<pattern>/<method>/` へ安全に移動。

### 2. パイプラインスクリプトの出力パス修正

#### [MODIFY] [merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)
`target_dir` 生成ロジックを変更し、モデル名から `pattern` を抽出して `seed` の直下に `pattern` ディレクトリを付与します。

```python
# pattern (safety+math, safety+code, safety+medical, safety+math+code+medical) の抽出
pattern = "unknown_pattern"
for p in ["safety+math+code+medical", "safety+math", "safety+code", "safety+medical"]:
    if f"_{p}_" in model_name:
        pattern = p
        break

# 出力先ディレクトリの作成 (seed -> pattern -> method)
target_dir = os.path.join(result_dir, f"seed{seed}", pattern, method)
```

---

## 検証計画

### 自動 / ディレクトリ検証
- ディレクトリ移動実行後、`seed42`, `seed43`, `seed44` の直下に `safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical` の4フォルダが生成され、各手法フォルダがその配下に正しく分類・移動されているか確認します。
- 空になった旧 `<method>` 直下フォルダが適切に整理されたことを検証します。
