# テーブル自動生成スクリプト仕様と出力サンプル (Walkthrough)

ユーザー様のご要望に応じ、**4 つの全ドメインパターン (`safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`) を常に漏れなく出力し、データが存在しない項目については `-` (ハイフン) を補填して表を自動生成** するようにスクリプト `v3/scripts/analysis/generate_summary_tables.py` を更新しました。

---

## 1. 強化ポイント

1. **4ドメインパターンの完全保証**:
   - `safety+math`
   - `safety+code`
   - `safety+medical`
   - `safety+math+code+medical`
   上記 4 パターンすべてにおいて、手法比較表および手法別独立表が必ず出力されます。
2. **欠損値の `-` 補填**:
   特定のパラメータやパターンで未評価の手法が存在する場合でも、行自体をスキップせず全項目スコア `-` の状態で行を維持・出力します。
3. **α非保有手法 (`SafeMerge`, `LED Merging`, `Matena Fisher`, `MergeAlign`) の同列比較**:
   Alpha 列を `-` とし、比較表および 3 Seeds Average 表に一括掲載。

---

## 2. 出力サンプル (3 Seeds Average / パターン: `safety+math+code+medical`)

#### ドメインパターン: `safety+math+code+medical` (比較表: Alpha=0.4 / 単一実行手法含む)

| Pattern | Method | Alpha | Safety Ave (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | HarmBench (ASR↓ %) | JailbreakBench (ASR↓ %) | StrongReject (ASR↓ %) | WildJailbreak (ASR↓ %) | GSM8K (%) | Minerva Math500 (%) | HumanEval (%) | MBPP (%) | PubMedQA (%) | MedQA (%) | MMLU (%) | IFEval (%) | AlpacaEval2 WinRate (%) | Evol-Code (%) | MedAlpaca (%) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 24.50% | 37.80% | 44.10% | 85.40% | 45.60% | 24.50% | 9.20% | 28.40% | 25.10% | 37.80% | 3.20% | 44.10% | 27.20% | 85.40% | 33.50% | 45.60% | 13.80% | 58.90% | 30.20% | 48.90% |
| safety+math+code+medical | data_free_sst_main | 0.40 | 25.20% | 37.20% | 43.60% | 84.90% | 45.20% | 25.20% | 9.60% | 29.20% | 25.90% | 37.20% | 3.00% | 43.60% | 26.50% | 84.90% | 33.00% | 45.20% | 13.40% | 58.40% | 29.60% | 48.30% |
| safety+math+code+medical | ties | 0.40 | 21.80% | 36.50% | 43.00% | 85.10% | 45.50% | 21.80% | 7.90% | 24.80% | 22.30% | 36.50% | 2.70% | 43.00% | 25.80% | 85.10% | 33.40% | 45.50% | 16.10% | 58.80% | 30.80% | 48.80% |
| safety+math+code+medical | dare | 0.40 | 22.10% | 36.80% | 43.30% | 85.00% | 45.40% | 22.10% | 8.10% | 25.20% | 22.60% | 36.80% | 2.90% | 43.30% | 26.00% | 85.00% | 33.30% | 45.40% | 15.50% | 58.50% | 30.70% | 48.70% |
| safety+math+code+medical | della | 0.40 | 21.80% | 36.50% | 43.00% | 85.10% | 45.50% | 21.80% | 7.90% | 24.80% | 22.30% | 36.50% | 2.70% | 43.00% | 25.80% | 85.10% | 33.40% | 45.50% | 16.10% | 58.80% | 30.80% | 48.80% |
| safety+math+code+medical | task_arithmetic | 0.40 | 21.80% | 36.50% | 43.00% | 85.10% | 45.50% | 21.80% | 7.90% | 24.80% | 22.30% | 36.50% | 2.70% | 43.00% | 25.80% | 85.10% | 33.40% | 45.50% | 16.10% | 58.80% | 30.80% | 48.80% |
| safety+math+code+medical | safemerge | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| safety+math+code+medical | led_merging | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |
| safety+math+code+medical | matena_fisher | - | 23.90% | 37.10% | 43.80% | 85.20% | 45.40% | 23.90% | 8.90% | 27.60% | 24.40% | 37.10% | 3.10% | 43.80% | 26.80% | 85.20% | 33.30% | 45.40% | 13.50% | 58.50% | 29.90% | 48.50% |
| safety+math+code+medical | mergealign | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - | - |

---

## 3. 再実行コマンド

```bash
python v3/scripts/analysis/generate_summary_tables.py \
    --results_dir v3/results/debug_limit320/merged \
    --output_dir v3/results/summary_tables \
    --target_alpha 0.4
```
