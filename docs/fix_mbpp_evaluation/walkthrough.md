# MBPP 評価自動修復・再評価スクリプト (Walkthrough)

`lm-evaluation-harness` のプロンプト形式によるパース不一致でスコアが 0.00% になっていた MBPP の評価結果について、生成済み結果 JSON の生応答テキスト (`resps`) からコードブロックを抽出・安全に再評価してスコアを修復するスクリプト `v3/scripts/fix_mbpp_jsons_fast.py` を実装しました。

---

## 1. 実装スクリプト

- [fix_mbpp_jsons_fast.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fix_mbpp_jsons_fast.py)

---

## 2. 修復ロジックのポイント

1. **モデル生応答 (`resps`) からのコード抽出**:
   - ````python ... ```` または ```` ... ```` マークダウンコードブロックの自動抽出。
   - `def ...` 関数定義ブロックのスマート切り出し。
   - 不要な解説テキストや `The answer is:` 等の削除。
2. **高速並列テスト実行 (`ProcessPoolExecutor`)**:
   - 抽出コードと MBPP テストコード (`test_list`) を結合。
   - タイムアウト保護 (0.5秒/サンプル) 付きで安全に `exec()` 実行。
3. **JSON のスコア上書き保存**:
   - `results.mbpp["pass_at_1,none"]` および `pass@1` を正しく書き換え更新。
   - `samples` 配下の個々のテストサンプルの `pass_at_1` (1.0 / 0.0) を更新。

---

## 3. 実行コマンド

評価環境のターミナルにて以下のコマンドを実行します：

```bash
# 1. MBPP 結果 JSON ファイルのスコア修復・一括更新
python v3/scripts/fix_mbpp_jsons_fast.py --results_dir v3/results/debug_limit320/merged

# 2. 修復後のスコアでサマリーテーブルを再生成
python v3/scripts/analysis/generate_summary_tables.py \
    --results_dir v3/results/debug_limit320/merged \
    --output_dir v3/results/summary_tables \
    --target_alpha 0.4
```
