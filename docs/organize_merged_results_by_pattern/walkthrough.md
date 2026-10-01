# Walkthrough: results/merged の pattern 別階層再編成

`/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged` 配下のディレクトリ構造について、`seed` の直下にパターン名 (`safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`) の階層を追加・整理し、スクリプトの出力パスロジックを更新しました。

---

## 完了した変更

### 1. ディレクトリ構造の変更設計
- **旧構造**: `results/debug_limit320/merged/seed<seed>/<method>/<filename>`
- **新構造**: `results/debug_limit320/merged/seed<seed>/<pattern>/<method>/<filename>`

### 2. スクリプト出力パスの同期更新

- **[merge_eval_parallel.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge_eval_parallel.py)**:
  モデル名からパターン名 (`safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`) を動的に判定抽出し、`target_dir = os.path.join(result_dir, f"seed{seed}", pattern, method)` としてディレクトリを作成・保存するように修正しました。

- **[run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)**:
  `run_merge_eval_phase` における評価出力ディレクトリの生成箇所（MERGEKIT_METHODS, CUSTOM_SINGLE_RUN_METHODS, PROPOSED_METHODS）を `target_dir = os.path.join(RESULT_DIR, f"seed{seed}", pattern, method_name)` に更新しました。

- **[v3/README.md](file:///mnt/nas/home/hiromi/src/sst_v2/v3/README.md)**:
  `results/` ディレクトリ配下の最新階層構造をドキュメントに反映しました。

---

## 既存データの移動・クリーンアップコマンド

既存の `results/debug_limit320/merged/` 配下にある全ファイル・全結果ディレクトリを新階層（`seed<seed>/<pattern>/<method>/`）へ自動で一括移動するには、以下のコマンドをターミナルで実行してください：

```bash
python3 -c '
import os, shutil
base = "/mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged"
patterns = ["safety+math+code+medical", "safety+math", "safety+code", "safety+medical"]
seeds = [d for d in os.listdir(base) if d.startswith("seed") and os.path.isdir(os.path.join(base, d))]
moved_files = 0
moved_dirs = 0
for seed in seeds:
    seed_path = os.path.join(base, seed)
    method_dirs = [e for e in os.listdir(seed_path) if e not in patterns and os.path.isdir(os.path.join(seed_path, e))]
    for method in method_dirs:
        method_path = os.path.join(seed_path, method)
        for item in os.listdir(method_path):
            item_path = os.path.join(method_path, item)
            matched = next((p for p in patterns if f"_{p}_" in item), None)
            if matched:
                dest_dir = os.path.join(seed_path, matched, method)
                os.makedirs(dest_dir, exist_ok=True)
                shutil.move(item_path, os.path.join(dest_dir, item))
                if os.path.isdir(os.path.join(dest_dir, item)):
                    moved_dirs += 1
                else:
                    moved_files += 1
        if os.path.exists(method_path) and len(os.listdir(method_path)) == 0:
            os.rmdir(method_path)
print(f"Reorganization completed. Moved {moved_files} files and {moved_dirs} directories.")
'
```
