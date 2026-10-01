# MBPP 評価修復計画 (Fix MBPP Evaluation Plan)

## 概要
MBPP の評価において、生成結果 JSON 内の生のモデル応答 (`resps`) から Python コードを抽出し、付属のテストケース (`test_list`) に対してプロセス分離＆タイムアウト保護付きで再評価を行って、MBPP スコア (`pass_at_1,none` および `pass@1`) を修復・JSONファイルへ上書き更新する。

## 修復スクリプトの仕様 (`v3/scripts/fix_mbpp_jsons_fast.py`)

1. **コード抽出アルゴリズム (Python Code Extraction)**:
   - パターン 1: ```python ... ``` または ``` ... ``` マークダウンコードブロックの検出
   - パターン 2: `def ...` から始まる関数定義ブロックの抽出
   - パターン 3: `[BEGIN] ... [DONE]` 形式の抽出

2. **安全な並列再評価**:
   - `ProcessPoolExecutor` によるプロセス分離。
   - タイムアウト (0.5秒/サンプル) 設定による無限ループ防止。
   - テストコード (`test_list` の全 assert) が成功したかを判定。

3. **結果の更新**:
   - `results.mbpp["pass_at_1,none"]` および `pass@1` を正しく書き換え。
   - `samples` 配下の個々のサンプルの `pass_at_1` も更新。
