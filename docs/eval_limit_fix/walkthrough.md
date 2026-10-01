# 修正内容レポート: eval スクリプトのlimit/データセット件数対応修正

## 実施日
2026-07-09

## 概要

`eval_safety.py`, `eval_utility.py`, `merge_eval_parallel.py` の3ファイルにおいて、
スキップ判定ロジックが `limit` パラメータを正しく使用していない問題を修正した。

`eval_alpaca.py` と `eval_instruction_datasets.py` は問題なし（修正不要）。

---

## 変更ファイル

### 1. `v3/scripts/eval_safety.py`

**修正関数**: `is_complete(output_file, limit)` (L71付近)

**問題**: `limit` パラメータが受け取られているが、スキップ判定に全く使われていなかった。
`limit=5` で完了したファイルを `limit=10` で再実行しようとしてもスキップされてしまう。

**修正内容**:
```python
# 追加したチェック
if limit > 0 and expected_n > limit:
    return False
```

`expected_n > limit` の場合（前回より大きいlimitで再実行）は不完全と判定し、再実行を促す。
`expected_n < limit`（データセットがlimitより小さい）ケースは既存の `completed=True` チェックで正しく処理される。

---

### 2. `v3/scripts/eval_utility.py`

**修正関数**: `is_completed_output(output_file, limit)` (L97付近)

**問題**: `limit` パラメータが受け取られているが、スキップ判定に全く使われていなかった。
`eval_safety.py` と同様の問題。

**修正内容**:
```python
# 追加したチェック
if limit > 0 and expected_n is not None and expected_n > limit:
    return False
```

> [!NOTE]
> `lm_eval` の実行ロジック（`run_lm_eval_python_api`, `run_lm_eval_cli_fallback`）は変更なし。
> スキップ判定のみを修正した。

---

### 3. `v3/scripts/merge_eval_parallel.py`

**修正関数**: `get_expected_n(data, limit)` (L370付近)

**問題**: `count < limit` のとき無条件に `count` を期待値として返していた。
これでは途中停止（`completed=False`）の中断ファイルとデータセット件数 < limit を区別できず、
途中停止ファイルが「完了済み」として誤判定されスキップされてしまう。

**修正前**:
```python
count = get_count_from_output(data)
if count > 0 and count < limit:
    return count  # ← 途中停止とデータセット小を区別できない
return int(limit)
```

**修正後**:
```python
count = get_count_from_output(data)
if count > 0 and count < limit:
    # completed=True の場合のみ「データセットが limit 未満」とみなす
    # completed=False は途中停止の可能性があるため limit を期待値にする
    if data.get("completed") is True:
        return count
return int(limit)
```

**動作確認**:

| 状況 | 修正前 | 修正後 |
|------|--------|--------|
| limit=10, 途中3件で中断 (`completed=False`) | `expected_n=3` → スキップ（❌誤判定） | `expected_n=10` → 再実行（✅正しい） |
| limit=10, データセット5件で完了 (`completed=True`) | `expected_n=5` → スキップ（✅正しい） | `expected_n=5` → スキップ（✅正しい） |
| limit=10, 10件で完了 (`completed=True`) | `expected_n=10` → スキップ（✅正しい） | `expected_n=10` → スキップ（✅正しい） |

---

## 各スクリプトの評価（修正後）

| スクリプト | 1件ずつ保存 | 差分生成 | limit > dataset対応 |
|-----------|------------|---------|---------------------|
| `eval_alpaca.py` | ✅ | ✅ | ✅ (変更なし) |
| `eval_instruction_datasets.py` | ✅ | ✅ | ✅ (変更なし) |
| `eval_safety.py` | ✅ | ✅ | ✅ (修正済み) |
| `eval_utility.py` | ❌ lm_eval依存 | ❌ lm_eval依存 | ✅ (修正済み、lm_eval維持) |
| `merge_eval_parallel.py` | — | — | ✅ (修正済み) |
