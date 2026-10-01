# 実装計画: 出力ディレクトリ構造の階層化

## 目標
実験データ（評価結果や保存モデル）が増えた際に、どのベースモデルに基づく実験結果であるかを判別しやすくするため、出力ディレクトリ構造を `results/<モデル名>/<実験名>` および `models/<モデル名>/<実験名>` のように階層化する。

## 変更内容
1. **`run_phase2.sh` のパス生成処理を修正**
   - `$MODEL` 変数（例: `meta-llama/Meta-Llama-3-8B`）から `basename` と `sed` を用いて、`Meta-` という接頭辞を除去した簡易的なモデル名（例: `Llama-3-8B`）を抽出する。
   - `RUN_DIR` および `MODEL_BASE_DIR` に上記の簡易モデル名変数を挿入し、出力を整理する。

```bash
MODEL_DIR_NAME=$(basename "$MODEL" | sed 's/Meta-//')
RUN_DIR="../../results/$MODEL_DIR_NAME/$RUN_NAME"
MODEL_BASE_DIR="../../models/$MODEL_DIR_NAME/$RUN_NAME"
```

## 確認事項
- `RUN_DIR` と `MODEL_BASE_DIR` の設定が正しく階層化されていることを確認する。
