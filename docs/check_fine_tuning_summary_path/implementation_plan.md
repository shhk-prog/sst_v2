# fine_tuning 集計スクリプト実行パス確認計画

## 概要
`v2/scripts/fine_tuning/summarize_results.py` が指定のパスで正しく実行可能かを確認します。

## 調査結果および背景
- スクリプト内部では相対パス `../../results/{run_name}` が参照されているため、`v2/scripts/fine_tuning` ディレクトリを作業ディレクトリ (Cwd) として実行する必要があります。
- 実行時にデフォルトとなる `--run_name lr2e-4_ep3` のディレクトリは `v2/results/` 直下に存在しませんが、`v2/results/Llama-3-8B/lr2e-4_ep10` や `v2/results/Llama-3-8B/lr5e-4_ep10` などのデータが存在することを確認しました。
- したがって、`--run_name Llama-3-8B/lr2e-4_ep10` を指定して実行テストを行います。

## 提案される変更 / 実行手順
1. 作業ディレクトリを `v2/scripts/fine_tuning` に設定する。
2. 以下のコマンドを実行する。
   ```bash
   python3 summarize_results.py --run_name Llama-3-8B/lr2e-4_ep10
   ```
3. スクリプトがエラーなく動作し、`v2/results/Llama-3-8B/lr2e-4_ep10/summary_report.md` が正しく生成されることを確認する。

## 検証計画
### 手動検証
- 生成された `summary_report.md` の存在とファイルサイズを確認する。
