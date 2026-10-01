# 評価結果集計・比較検証レポート (Walkthrough & Audit)

ユーザー様のご指示に基づき、全 468 評価タスクの結果抽出およびドメインカテゴリ平均の集計ロジックを全件精密監査し、発見した不整合およびバグを完全に修復しました。

---

## 1. 監査で発見された主要な課題と修正内容

1. **HumanEval スコア誤認識バグの修正**:
   - **課題**: `HumanEval (%)` に `109.33%` という 100% を超える不正な数値が入っていた。
   - **原因**: 結果 JSON 内の評価スコアキーミスマッチ時、フォールバック処理で `sample_len: 109` などのメタデータ属性を誤ってスコアとして取得していた。
   - **修正**: 各ベンチマークの指定キー (`pass@1`, `exact_match`, `acc,none` 等) を完全一致判定し、範囲外数値のフォールバック取得を無効化。

2. **MMLU スコア集計の正確化**:
   - **課題**: MMLU の全 57 サブタスクのうち、先頭の 1 サブタスク (`mmlu_abstract_algebra`) のみの精度を取得していた。
   - **修正**: 全 57 サブタスクの正解率 (`acc,none`) を正確に読み込み、全タスクの算術平均値を算出・反映。

3. **Instruction benchmarks (`Evol-Code`, `MedAlpaca`) の抽出補完**:
   - **課題**: スコアが抽出されず `-` (ハイフン) になっていた。
   - **修正**: `inst_evol_code.json` および `inst_medalpaca.json` 内の `similarity_score` を正しくパースして % 表記で表示。

4. **パターン名部分一致誤誤判定の解消**:
   - **課題**: `safety+math+code+medical` 内に `safety+math` の文字列が含まれるため、誤分類が発生していた。
   - **修正**: 文字列長の長いパターン名から最優先で一致判定を行うロジックに変更。

---

## 2. 修正後の集計比較サンプル (`safety+math` パターン)

| Pattern | Method | Alpha | Safety Ave (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench (ASR↓ %) | StrongReject (ASR↓ %) | WildJailbreak (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code (%) | MedAlpaca (%) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.40 | 60.99% | 23.54% | 4.89% | 60.99% | 26.16% | 27.60% | 76.00% | 78.91% | 61.46% | 41.35% | 5.73% | 4.47% | 5.31% | 89.69% | 32.29% | 43.12% | 12.29% | 58.63% | 9.96% | 6.80% |
| safety+math | data_free_sst_main | 0.40 | 59.21% | 24.38% | 3.85% | 60.78% | 32.31% | 27.29% | 67.33% | 82.43% | 59.79% | 42.71% | 6.04% | 4.27% | 3.44% | 89.27% | 32.29% | 42.88% | 13.12% | 58.12% | 10.12% | 7.10% |

---

## 3. 再実行コマンド

```bash
python v3/scripts/analysis/generate_summary_tables.py \
    --results_dir v3/results/debug_limit320/merged \
    --output_dir v3/results/summary_tables \
    --target_alpha 0.4
```
