# 実装計画: eval スクリプトのlimit/データセット件数対応修正

## 背景と目的

`eval_alpaca.py`, `eval_instruction_datasets.py`, `eval_safety.py`, `eval_utility.py`, `merge_eval_parallel.py` の各evalスクリプトが以下の要件を正しく満たしているかを確認・修正する。

- 1件ずつ応答を保存する（中断後に再開できる）
- 実行時にすでに生成済みの件数を確認し、`limit` 以下であれば不足分のみ生成する
- **ただし、データセットの件数が `limit` より少ない場合がある**

## 調査結果

### eval_alpaca.py ✅ 問題なし
- `normalize_samples()`: `limit > 0` のときのみ `[:limit]` でスライス → データセット件数 < limit でも正しく動作
- `has_required_outputs()`: 保存済み件数と `required_n` を比較
- ループ内で逐次 `save_model_outputs_checkpoint()` を呼ぶ

### eval_instruction_datasets.py ✅ 問題なし
- `get_dataset_samples()`: `end_idx = min(start_idx + actual_limit, len(ds))` でデータセット末尾を超えない
- 各評価ステップ（loss/response/similarity）ごとに `save_checkpoint()` を呼ぶ
- `missing` リストで不足分のみ処理

### eval_safety.py ⚠️ 修正が必要
**問題**: `is_complete(output_file, limit)` が `limit` パラメータを使っていない
- `expected_n` はファイルに保存された値（=実際の処理件数）を使用
- `limit=5` で完了したファイルを `limit=10` で再実行すると、`expected_n=5, len(results)=5` でスキップされてしまう

**修正方針**: `limit > 0` かつ `expected_n > limit` のとき `False` を返す

### eval_utility.py ⚠️ 修正が必要（lm_eval実行ロジックは維持）
**問題**: `is_completed_output()` が `limit` パラメータを判定に使っていない
- lm_eval は差分生成に非対応（全件再実行）だが、スキップ判定は正しくすべき

**修正方針**: `limit > 0` かつ `expected_n > limit` のとき `False` を返す。lm_eval の実行コードは変更しない。

### merge_eval_parallel.py ⚠️ 修正が必要
**問題**: `get_expected_n()` の以下の箇所が問題

```python
count = get_count_from_output(data)
if count > 0 and count < limit:
    return count  # 途中停止とデータセット小を区別できない
```

例: `limit=10`, 途中で3件生成して中断 → `count=3 < limit=10` → `expected_n=3` → `count(3) >= expected_n(3)` → スキップされてしまう

**修正方針**: `completed=True` のときのみ `count` をデータセット実件数として返し、`completed=False` の場合は `int(limit)` を返して不完全と判定させる

## 修正一覧

| ファイル | 関数 | 修正内容 |
|---------|------|---------|
| `eval_safety.py` | `is_complete()` | `limit > 0 and expected_n > limit` → `return False` を追加 |
| `eval_utility.py` | `is_completed_output()` | 同上 |
| `merge_eval_parallel.py` | `get_expected_n()` | `count < limit` のとき `completed=True` のみ `count` を返す |

## 検証計画

### 手動確認
- `limit=5` で完了済みファイルがある状態で `limit=10` を指定した場合、スキップされずに再実行されることを確認
- `limit=10` でデータセットが5件しかない場合、5件で完了後、再度 `limit=10` で実行してもスキップされることを確認
- 途中停止（`completed=False`）のファイルがある状態で再実行し、不足分のみ生成されることを確認
