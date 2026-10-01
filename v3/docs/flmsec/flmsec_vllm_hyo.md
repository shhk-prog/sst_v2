# SST-Merge実験結果一覧 (flmsec_vllm_hyo.md) (vLLM Only)
本ファイルは自動生成された実験結果ドキュメントです。
各実験設定ごとに **「平均±標準偏差 (Mean ± Std) の集計表」** と **「シード別 (Seed 42, 43, 44) の詳細結果比較表」** をセットで上下に掲載しています。
この表は (vLLM Only) に絞った結果です。

## 0. 論文メインテキスト用 簡易まとめ表
`flmsec.md` のメインテキストに直接貼り付けられるよう、不要な列（Env, Alpha, Seed等）を省き、主要な設定（Alpha=0.6またはN/A）のみを抽出した表です。ベースモデルのスコアも参考として含めています。

### 予備実験 簡易版

#### 【簡易版】 予備実験 (Alpha=0.6 / N/A) (vLLM Only)

| Pattern | Method | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :---: | :---: | :---: |
| safety+code | Base | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+code | dare | 100.00 ± 0.00% | 36.35 ± 12.66% | 64.06 ± 11.87% |
| safety+code | data_free_sst_main | 92.60 ± 2.90% | 64.38 ± 1.13% | 27.40 ± 3.77% |
| safety+code | della | 100.00 ± 0.00% | 33.65 ± 8.21% | 67.19 ± 5.42% |
| safety+code | diagonal_sst_main | 98.12 ± 1.65% | 76.77 ± 3.31% | 19.58 ± 2.90% |
| safety+code | led_merging | 87.19 ± 0.00% | 95.94 ± 0.00% | 5.00 ± 0.00% |
| safety+code | matena_fisher | 95.62 ± 1.13% | 71.98 ± 1.57% | 28.33 ± 2.22% |
| safety+code | mergealign | 100.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+code | safemerge | 4.58 ± 5.81% | 6.25 ± 10.56% | 2.81 ± 2.19% |
| safety+code | task_arithmetic | 82.40 ± 2.73% | 56.67 ± 4.07% | 24.38 ± 3.29% |
| safety+code | ties | 99.38 ± 0.31% | 62.29 ± 6.59% | 34.58 ± 2.37% |
| safety+math | Base | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+math | dare | 17.19 ± 0.83% | 18.65 ± 0.95% | 9.69 ± 2.86% |
| safety+math | data_free_sst_main | 36.88 ± 3.25% | 36.04 ± 4.24% | 21.15 ± 0.36% |
| safety+math | della | 19.06 ± 3.17% | 20.62 ± 5.20% | 7.81 ± 2.05% |
| safety+math | diagonal_sst_main | 24.38 ± 1.74% | 58.44 ± 5.94% | 12.81 ± 2.44% |
| safety+math | led_merging | 87.19 ± 0.00% | 96.15 ± 0.18% | 5.00 ± 0.00% |
| safety+math | matena_fisher | 19.79 ± 1.18% | 67.19 ± 3.52% | 10.00 ± 1.65% |
| safety+math | mergealign | 100.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+math | safemerge | 14.27 ± 22.55% | 31.15 ± 53.95% | 3.33 ± 3.34% |
| safety+math | task_arithmetic | 9.69 ± 0.31% | 47.92 ± 18.35% | 6.35 ± 1.91% |
| safety+math | ties | 18.65 ± 4.77% | 36.67 ± 4.77% | 11.25 ± 1.08% |
| safety+math+code+medical | Base | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+math+code+medical | dare | 100.00 ± 0.00% | 70.42 ± 40.72% | 31.46 ± 41.41% |
| safety+math+code+medical | data_free_sst_main | 95.73 ± 6.35% | 84.79 ± 18.14% | 15.62 ± 15.77% |
| safety+math+code+medical | della | 100.00 ± 0.00% | 73.65 ± 24.63% | 28.65 ± 26.34% |
| safety+math+code+medical | diagonal_sst_main | 97.29 ± 2.01% | 95.31 ± 2.19% | 5.10 ± 0.48% |
| safety+math+code+medical | matena_fisher | 100.00 ± 0.00% | 80.10 ± 0.18% | 16.56 ± 1.36% |
| safety+math+code+medical | task_arithmetic | 66.25 ± 11.12% | 70.73 ± 14.23% | 4.90 ± 1.44% |
| safety+math+code+medical | ties | 100.00 ± 0.00% | 40.94 ± 49.27% | 60.21 ± 50.93% |
| safety+medical | Base | 0.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+medical | dare | 70.21 ± 51.60% | 63.75 ± 44.93% | 36.56 ± 44.96% |
| safety+medical | data_free_sst_main | 100.00 ± 0.00% | 69.69 ± 15.86% | 27.40 ± 10.79% |
| safety+medical | della | 99.90 ± 0.18% | 70.83 ± 30.45% | 31.77 ± 32.89% |
| safety+medical | diagonal_sst_main | 100.00 ± 0.00% | 38.85 ± 53.60% | 59.58 ± 52.21% |
| safety+medical | matena_fisher | 100.00 ± 0.00% | 62.19 ± 53.64% | 37.50 ± 53.89% |
| safety+medical | mergealign | 100.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+medical | safemerge | 3.02 ± 0.18% | 0.00 ± 0.00% | 2.60 ± 1.83% |
| safety+medical | task_arithmetic | 100.00 ± 0.00% | 97.60 ± 2.60% | 1.77 ± 2.01% |
| safety+medical | ties | 100.00 ± 0.00% | 88.96 ± 9.58% | 11.15 ± 9.45% |


### メイン実験 簡易版

#### 【簡易版】 メイン実験 (Alpha=0.6 / N/A) (vLLM Only)

| Pattern | Method | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Base (MedAlpaca) | Base (MedAlpaca) | 5.17 ± 0.00% | 4.53 ± 0.00% | 3.59 ± 0.00% | 52.81 ± 0.00% | 20.28 ± 0.00% |
| Base (SafetyFT) | Base (SafetyFT) | 0.00 ± 0.00% | 0.52 ± 0.48% | 4.22 ± 3.39% | 43.49 ± 11.80% | 11.38 ± 0.41% |
| Base (WizardCoder) | Base (WizardCoder) | 24.69 ± 0.00% | 4.53 ± 0.00% | 21.03 ± 0.00% | 54.53 ± 0.00% | 18.41 ± 0.00% |
| Base (WizardMath) | Base (WizardMath) | 31.01 ± 0.00% | 6.41 ± 0.00% | 3.12 ± 0.00% | 55.00 ± 0.00% | 14.02 ± 0.00% |
| safety+code | dare | 0.00 ± 0.00% | 0.05 ± 0.09% | 0.00 ± 0.00% | 29.58 ± 12.27% | 11.73 ± 0.70% |
| safety+code | data_free_sst_main | 0.03 ± 0.05% | 0.21 ± 0.24% | 0.00 ± 0.00% | 78.75 ± 2.48% | 14.07 ± 0.05% |
| safety+code | della | 0.00 ± 0.00% | 0.62 ± 0.41% | 0.00 ± 0.00% | 43.54 ± 14.08% | 12.43 ± 0.46% |
| safety+code | diagonal_sst_main | 0.97 ± 0.42% | 0.89 ± 0.24% | 0.00 ± 0.00% | 86.25 ± 0.31% | 12.26 ± 0.55% |
| safety+code | led_merging | 2.88 ± 0.14% | 1.41 ± 0.00% | 5.62 ± 0.00% | 83.75 ± 0.00% | 22.49 ± 0.04% |
| safety+code | matena_fisher | 3.37 ± 1.40% | 1.09 ± 0.00% | 0.00 ± 0.00% | 83.12 ± 0.31% | 12.77 ± 0.37% |
| safety+code | mergealign | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 15.73 ± 3.41% |
| safety+code | safemerge | 0.10 ± 0.18% | 1.51 ± 1.33% | 5.99 ± 5.39% | 73.75 ± 2.98% | 19.84 ± 8.02% |
| safety+code | task_arithmetic | 29.17 ± 3.07% | 2.97 ± 0.68% | 4.63 ± 0.09% | 88.85 ± 0.79% | 17.39 ± 0.39% |
| safety+code | ties | 0.11 ± 0.04% | 1.41 ± 0.47% | 0.00 ± 0.00% | 38.65 ± 26.32% | 17.85 ± 9.81% |
| safety+math | dare | 6.14 ± 5.14% | 5.42 ± 0.79% | 5.00 ± 1.02% | 84.27 ± 2.35% | 22.85 ± 8.57% |
| safety+math | data_free_sst_main | 14.73 ± 3.41% | 5.57 ± 0.24% | 7.19 ± 4.33% | 69.38 ± 13.52% | 24.69 ± 0.38% |
| safety+math | della | 6.66 ± 5.52% | 5.52 ± 0.63% | 5.31 ± 1.36% | 85.62 ± 0.54% | 31.03 ± 4.06% |
| safety+math | diagonal_sst_main | 17.09 ± 5.01% | 6.82 ± 0.86% | 6.72 ± 0.95% | 72.55 ± 15.91% | 22.48 ± 8.92% |
| safety+math | led_merging | 2.80 ± 0.00% | 1.41 ± 0.00% | 5.62 ± 0.00% | 83.75 ± 0.00% | 22.51 ± 0.02% |
| safety+math | matena_fisher | 4.29 ± 0.43% | 6.04 ± 0.86% | 6.61 ± 0.39% | 85.73 ± 0.65% | 26.72 ± 11.70% |
| safety+math | mergealign | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 15.73 ± 3.41% |
| safety+math | safemerge | 4.61 ± 7.99% | 1.30 ± 0.86% | 6.67 ± 4.86% | 82.50 ± 1.74% | 13.09 ± 1.77% |
| safety+math | task_arithmetic | 2.48 ± 2.89% | 6.88 ± 1.56% | 7.50 ± 0.68% | 75.21 ± 15.93% | 27.18 ± 6.92% |
| safety+math | ties | 9.03 ± 5.55% | 5.94 ± 0.83% | 6.15 ± 0.18% | 85.00 ± 2.44% | 27.65 ± 3.07% |
| safety+math+code+medical | dare | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 38.02 ± 41.77% | 11.53 ± 0.23% |
| safety+math+code+medical | data_free_sst_main | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.67 ± 24.56% | 11.85 ± 0.59% |
| safety+math+code+medical | della | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 15.42 ± 16.18% | 12.53 ± 0.78% |
| safety+math+code+medical | diagonal_sst_main | 0.00 ± 0.00% | 0.42 ± 0.18% | 0.00 ± 0.00% | 57.29 ± 17.67% | 10.16 ± 0.49% |
| safety+math+code+medical | matena_fisher | 0.00 ± 0.00% | 0.99 ± 0.24% | 0.00 ± 0.00% | 27.81 ± 3.29% | 13.12 ± 0.12% |
| safety+math+code+medical | task_arithmetic | 5.88 ± 0.55% | 2.55 ± 0.39% | 0.05 ± 0.09% | 65.42 ± 9.24% | 13.26 ± 1.65% |
| safety+math+code+medical | ties | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.17 ± 7.94% | 12.28 ± 0.40% |
| safety+medical | dare | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 22.08 ± 10.81% | 12.39 ± 0.44% |
| safety+medical | data_free_sst_main | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 61.67 ± 41.50% | 12.27 ± 0.07% |
| safety+medical | della | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 27.29 ± 23.45% | 12.10 ± 1.01% |
| safety+medical | diagonal_sst_main | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.69 ± 8.46% | 12.06 ± 0.13% |
| safety+medical | matena_fisher | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.99 ± 0.18% |
| safety+medical | mergealign | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 13.76 ± 3.41% |
| safety+medical | safemerge | 0.03 ± 0.05% | 1.09 ± 1.89% | 3.91 ± 6.77% | 53.44 ± 10.84% | 12.81 ± 1.63% |
| safety+medical | task_arithmetic | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.85 ± 0.18% | 12.72 ± 0.06% |
| safety+medical | ties | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.54 ± 0.36% | 11.90 ± 0.62% |


## 1. 予備実験 (TrustLLM / BeaverTails)
各マージ手法のベースラインとしての安全性（TrustLLM ASR / Gibberish）と有用性（BeaverTails Accuracy）の比較。

### 予備実験: Pattern = safety+medical

#### 【集計】 予備実験 (Mean ± Std) - safety+medical

| Pattern | Method | Alpha | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | dare | 0.00 | 100.00 ± 0.00% | 51.46 ± 42.80% | 51.56 ± 40.41% |
| safety+medical | dare | 0.20 | 99.79 ± 0.36% | 65.42 ± 22.45% | 34.38 ± 18.33% |
| safety+medical | dare | 0.40 | 99.17 ± 1.44% | 41.46 ± 39.78% | 60.00 ± 41.19% |
| safety+medical | dare | 0.60 | 70.21 ± 51.60% | 63.75 ± 44.93% | 36.56 ± 44.96% |
| safety+medical | dare | 0.80 | 99.90 ± 0.18% | 67.29 ± 5.18% | 32.40 ± 2.08% |
| safety+medical | dare | 1.00 | 1.77 ± 1.30% | 0.00 ± 0.00% | 1.25 ± 0.62% |
| safety+medical | data_free_sst_main | 0.00 | 100.00 ± 0.00% | 37.50 ± 0.00% | 60.31 ± 0.00% |
| safety+medical | data_free_sst_main | 0.20 | 100.00 ± 0.00% | 38.85 ± 6.41% | 57.60 ± 8.28% |
| safety+medical | data_free_sst_main | 0.40 | 100.00 ± 0.00% | 52.40 ± 16.41% | 46.46 ± 18.28% |
| safety+medical | data_free_sst_main | 0.60 | 100.00 ± 0.00% | 69.69 ± 15.86% | 27.40 ± 10.79% |
| safety+medical | data_free_sst_main | 0.80 | 100.00 ± 0.00% | 84.17 ± 18.55% | 12.81 ± 14.73% |
| safety+medical | data_free_sst_main | 1.00 | 100.00 ± 0.00% | 61.46 ± 31.42% | 35.00 ± 32.27% |
| safety+medical | della | 0.00 | 100.00 ± 0.00% | 59.27 ± 17.74% | 40.21 ± 11.79% |
| safety+medical | della | 0.20 | 100.00 ± 0.00% | 92.71 ± 7.53% | 8.23 ± 11.33% |
| safety+medical | della | 0.40 | 88.85 ± 19.31% | 52.81 ± 33.33% | 44.90 ± 33.83% |
| safety+medical | della | 0.60 | 99.90 ± 0.18% | 70.83 ± 30.45% | 31.77 ± 32.89% |
| safety+medical | della | 0.80 | 100.00 ± 0.00% | 52.71 ± 39.47% | 46.77 ± 39.22% |
| safety+medical | della | 1.00 | 1.04 ± 0.95% | 0.10 ± 0.18% | 1.04 ± 0.95% |
| safety+medical | diagonal_sst_main | 0.00 | 100.00 ± 0.00% | 37.50 ± 0.00% | 60.31 ± 0.00% |
| safety+medical | diagonal_sst_main | 0.20 | 100.00 ± 0.00% | 5.10 ± 7.76% | 91.98 ± 11.73% |
| safety+medical | diagonal_sst_main | 0.40 | 100.00 ± 0.00% | 64.58 ± 31.56% | 34.48 ± 32.81% |
| safety+medical | diagonal_sst_main | 0.60 | 100.00 ± 0.00% | 38.85 ± 53.60% | 59.58 ± 52.21% |
| safety+medical | diagonal_sst_main | 0.80 | 100.00 ± 0.00% | 74.17 ± 43.67% | 24.17 ± 40.51% |
| safety+medical | diagonal_sst_main | 1.00 | 99.69 ± 0.54% | 99.79 ± 0.18% | 0.52 ± 0.90% |
| safety+medical | matena_fisher | N/A | 100.00 ± 0.00% | 62.19 ± 53.64% | 37.50 ± 53.89% |
| safety+medical | mergealign | N/A | 100.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+medical | safemerge | N/A | 3.02 ± 0.18% | 0.00 ± 0.00% | 2.60 ± 1.83% |
| safety+medical | task_arithmetic | 0.00 | 25.94 ± 0.00% | 6.88 ± 0.00% | 19.06 ± 0.00% |
| safety+medical | task_arithmetic | 0.20 | 91.15 ± 0.18% | 72.50 ± 0.00% | 19.58 ± 0.65% |
| safety+medical | task_arithmetic | 0.40 | 97.19 ± 3.55% | 96.35 ± 1.10% | 4.17 ± 1.41% |
| safety+medical | task_arithmetic | 0.60 | 100.00 ± 0.00% | 97.60 ± 2.60% | 1.77 ± 2.01% |
| safety+medical | task_arithmetic | 0.80 | 96.25 ± 2.98% | 99.58 ± 0.48% | 0.62 ± 0.83% |
| safety+medical | task_arithmetic | 1.00 | 0.83 ± 0.79% | 0.10 ± 0.18% | 1.46 ± 0.79% |
| safety+medical | ties | 0.00 | 100.00 ± 0.00% | 86.88 ± 0.00% | 14.37 ± 0.00% |
| safety+medical | ties | 0.20 | 100.00 ± 0.00% | 38.65 ± 41.80% | 61.77 ± 40.24% |
| safety+medical | ties | 0.40 | 100.00 ± 0.00% | 66.15 ± 28.53% | 36.77 ± 31.58% |
| safety+medical | ties | 0.60 | 100.00 ± 0.00% | 88.96 ± 9.58% | 11.15 ± 9.45% |
| safety+medical | ties | 0.80 | 100.00 ± 0.00% | 36.98 ± 43.16% | 64.06 ± 42.90% |
| safety+medical | ties | 1.00 | 0.73 ± 1.00% | 0.00 ± 0.00% | 1.46 ± 0.95% |


#### 【シード別詳細】 予備実験 - Method: mergealign, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 42 | 100.00% | 100.00% | 0.00% |
| safety+medical | mergealign | N/A | 43 | 100.00% | 100.00% | 0.00% |
| safety+medical | mergealign | N/A | 44 | 100.00% | 100.00% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: diagonal_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.00 | 42 | 100.00% | 37.50% | 60.31% |
| safety+medical | diagonal_sst_main | 0.00 | 43 | 100.00% | 37.50% | 60.31% |
| safety+medical | diagonal_sst_main | 0.00 | 44 | 100.00% | 37.50% | 60.31% |
| safety+medical | diagonal_sst_main | 0.20 | 42 | 100.00% | 0.62% | 99.06% |
| safety+medical | diagonal_sst_main | 0.20 | 43 | 100.00% | 14.06% | 78.44% |
| safety+medical | diagonal_sst_main | 0.20 | 44 | 100.00% | 0.62% | 98.44% |
| safety+medical | diagonal_sst_main | 0.40 | 42 | 100.00% | 35.00% | 67.50% |
| safety+medical | diagonal_sst_main | 0.40 | 43 | 100.00% | 60.94% | 34.06% |
| safety+medical | diagonal_sst_main | 0.40 | 44 | 100.00% | 97.81% | 1.88% |
| safety+medical | diagonal_sst_main | 0.60 | 42 | 100.00% | 0.00% | 98.75% |
| safety+medical | diagonal_sst_main | 0.60 | 43 | 100.00% | 100.00% | 0.31% |
| safety+medical | diagonal_sst_main | 0.60 | 44 | 100.00% | 16.56% | 79.69% |
| safety+medical | diagonal_sst_main | 0.80 | 42 | 100.00% | 98.75% | 1.56% |
| safety+medical | diagonal_sst_main | 0.80 | 43 | 100.00% | 100.00% | 0.00% |
| safety+medical | diagonal_sst_main | 0.80 | 44 | 100.00% | 23.75% | 70.94% |
| safety+medical | diagonal_sst_main | 1.00 | 42 | 100.00% | 99.69% | 0.00% |
| safety+medical | diagonal_sst_main | 1.00 | 43 | 100.00% | 99.69% | 1.56% |
| safety+medical | diagonal_sst_main | 1.00 | 44 | 99.06% | 100.00% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: dare, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | dare | 0.00 | 42 | 100.00% | 79.38% | 25.62% |
| safety+medical | dare | 0.00 | 43 | 100.00% | 72.81% | 30.94% |
| safety+medical | dare | 0.00 | 44 | 100.00% | 2.19% | 98.12% |
| safety+medical | dare | 0.20 | 42 | 99.38% | 40.62% | 53.44% |
| safety+medical | dare | 0.20 | 43 | 100.00% | 84.38% | 16.88% |
| safety+medical | dare | 0.20 | 44 | 100.00% | 71.25% | 32.81% |
| safety+medical | dare | 0.40 | 42 | 97.50% | 86.88% | 12.81% |
| safety+medical | dare | 0.40 | 43 | 100.00% | 12.81% | 88.75% |
| safety+medical | dare | 0.40 | 44 | 100.00% | 24.69% | 78.44% |
| safety+medical | dare | 0.60 | 42 | 10.62% | 88.75% | 12.50% |
| safety+medical | dare | 0.60 | 43 | 100.00% | 90.62% | 8.75% |
| safety+medical | dare | 0.60 | 44 | 100.00% | 11.88% | 88.44% |
| safety+medical | dare | 0.80 | 42 | 99.69% | 67.81% | 30.00% |
| safety+medical | dare | 0.80 | 43 | 100.00% | 72.19% | 33.44% |
| safety+medical | dare | 0.80 | 44 | 100.00% | 61.88% | 33.75% |
| safety+medical | dare | 1.00 | 42 | 2.81% | 0.00% | 1.25% |
| safety+medical | dare | 1.00 | 43 | 2.19% | 0.00% | 1.88% |
| safety+medical | dare | 1.00 | 44 | 0.31% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: ties, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | ties | 0.00 | 42 | 100.00% | 86.88% | 14.37% |
| safety+medical | ties | 0.00 | 43 | 100.00% | 86.88% | 14.37% |
| safety+medical | ties | 0.00 | 44 | 100.00% | 86.88% | 14.37% |
| safety+medical | ties | 0.20 | 42 | 100.00% | 16.25% | 85.31% |
| safety+medical | ties | 0.20 | 43 | 100.00% | 12.81% | 84.69% |
| safety+medical | ties | 0.20 | 44 | 100.00% | 86.88% | 15.31% |
| safety+medical | ties | 0.40 | 42 | 100.00% | 55.62% | 43.12% |
| safety+medical | ties | 0.40 | 43 | 100.00% | 44.38% | 64.69% |
| safety+medical | ties | 0.40 | 44 | 100.00% | 98.44% | 2.50% |
| safety+medical | ties | 0.60 | 42 | 100.00% | 87.81% | 8.75% |
| safety+medical | ties | 0.60 | 43 | 100.00% | 80.00% | 21.56% |
| safety+medical | ties | 0.60 | 44 | 100.00% | 99.06% | 3.12% |
| safety+medical | ties | 0.80 | 42 | 100.00% | 16.56% | 85.31% |
| safety+medical | ties | 0.80 | 43 | 100.00% | 7.81% | 92.19% |
| safety+medical | ties | 0.80 | 44 | 100.00% | 86.56% | 14.69% |
| safety+medical | ties | 1.00 | 42 | 0.31% | 0.00% | 1.25% |
| safety+medical | ties | 1.00 | 43 | 1.88% | 0.00% | 2.50% |
| safety+medical | ties | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: task_arithmetic, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.00 | 42 | 25.94% | 6.88% | 19.06% |
| safety+medical | task_arithmetic | 0.00 | 43 | 25.94% | 6.88% | 19.06% |
| safety+medical | task_arithmetic | 0.00 | 44 | 25.94% | 6.88% | 19.06% |
| safety+medical | task_arithmetic | 0.20 | 42 | 90.94% | 72.50% | 19.38% |
| safety+medical | task_arithmetic | 0.20 | 43 | 91.25% | 72.50% | 20.31% |
| safety+medical | task_arithmetic | 0.20 | 44 | 91.25% | 72.50% | 19.06% |
| safety+medical | task_arithmetic | 0.40 | 42 | 93.12% | 96.25% | 4.06% |
| safety+medical | task_arithmetic | 0.40 | 43 | 99.69% | 97.50% | 2.81% |
| safety+medical | task_arithmetic | 0.40 | 44 | 98.75% | 95.31% | 5.62% |
| safety+medical | task_arithmetic | 0.60 | 42 | 100.00% | 99.69% | 0.31% |
| safety+medical | task_arithmetic | 0.60 | 43 | 100.00% | 98.44% | 0.94% |
| safety+medical | task_arithmetic | 0.60 | 44 | 100.00% | 94.69% | 4.06% |
| safety+medical | task_arithmetic | 0.80 | 42 | 98.12% | 99.06% | 1.56% |
| safety+medical | task_arithmetic | 0.80 | 43 | 97.81% | 100.00% | 0.00% |
| safety+medical | task_arithmetic | 0.80 | 44 | 92.81% | 99.69% | 0.31% |
| safety+medical | task_arithmetic | 1.00 | 42 | 0.94% | 0.31% | 1.56% |
| safety+medical | task_arithmetic | 1.00 | 43 | 1.56% | 0.00% | 2.19% |
| safety+medical | task_arithmetic | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: della, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | della | 0.00 | 42 | 100.00% | 75.94% | 32.19% |
| safety+medical | della | 0.00 | 43 | 100.00% | 40.62% | 53.75% |
| safety+medical | della | 0.00 | 44 | 100.00% | 61.25% | 34.69% |
| safety+medical | della | 0.20 | 42 | 100.00% | 84.06% | 21.25% |
| safety+medical | della | 0.20 | 43 | 100.00% | 96.25% | 2.81% |
| safety+medical | della | 0.20 | 44 | 100.00% | 97.81% | 0.62% |
| safety+medical | della | 0.40 | 42 | 100.00% | 15.62% | 82.81% |
| safety+medical | della | 0.40 | 43 | 66.56% | 80.00% | 17.81% |
| safety+medical | della | 0.40 | 44 | 100.00% | 62.81% | 34.06% |
| safety+medical | della | 0.60 | 42 | 100.00% | 76.88% | 23.12% |
| safety+medical | della | 0.60 | 43 | 100.00% | 97.81% | 4.06% |
| safety+medical | della | 0.60 | 44 | 99.69% | 37.81% | 68.12% |
| safety+medical | della | 0.80 | 42 | 100.00% | 97.19% | 2.50% |
| safety+medical | della | 0.80 | 43 | 100.00% | 21.88% | 77.19% |
| safety+medical | della | 0.80 | 44 | 100.00% | 39.06% | 60.62% |
| safety+medical | della | 1.00 | 42 | 1.25% | 0.00% | 1.25% |
| safety+medical | della | 1.00 | 43 | 1.88% | 0.31% | 1.88% |
| safety+medical | della | 1.00 | 44 | 0.00% | 0.00% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: safemerge, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 42 | 3.12% | 0.00% | 1.88% |
| safety+medical | safemerge | N/A | 43 | 3.12% | 0.00% | 1.25% |
| safety+medical | safemerge | N/A | 44 | 2.81% | 0.00% | 4.69% |


#### 【シード別詳細】 予備実験 - Method: data_free_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.00 | 42 | 100.00% | 37.50% | 60.31% |
| safety+medical | data_free_sst_main | 0.00 | 43 | 100.00% | 37.50% | 60.31% |
| safety+medical | data_free_sst_main | 0.00 | 44 | 100.00% | 37.50% | 60.31% |
| safety+medical | data_free_sst_main | 0.20 | 42 | 100.00% | 38.75% | 50.94% |
| safety+medical | data_free_sst_main | 0.20 | 43 | 100.00% | 45.31% | 55.00% |
| safety+medical | data_free_sst_main | 0.20 | 44 | 100.00% | 32.50% | 66.88% |
| safety+medical | data_free_sst_main | 0.40 | 42 | 100.00% | 36.25% | 64.69% |
| safety+medical | data_free_sst_main | 0.40 | 43 | 100.00% | 69.06% | 28.12% |
| safety+medical | data_free_sst_main | 0.40 | 44 | 100.00% | 51.88% | 46.56% |
| safety+medical | data_free_sst_main | 0.60 | 42 | 100.00% | 73.75% | 26.88% |
| safety+medical | data_free_sst_main | 0.60 | 43 | 100.00% | 83.12% | 16.88% |
| safety+medical | data_free_sst_main | 0.60 | 44 | 100.00% | 52.19% | 38.44% |
| safety+medical | data_free_sst_main | 0.80 | 42 | 100.00% | 93.44% | 6.25% |
| safety+medical | data_free_sst_main | 0.80 | 43 | 100.00% | 96.25% | 2.50% |
| safety+medical | data_free_sst_main | 0.80 | 44 | 100.00% | 62.81% | 29.69% |
| safety+medical | data_free_sst_main | 1.00 | 42 | 100.00% | 76.88% | 18.44% |
| safety+medical | data_free_sst_main | 1.00 | 43 | 100.00% | 25.31% | 72.19% |
| safety+medical | data_free_sst_main | 1.00 | 44 | 100.00% | 82.19% | 14.37% |


#### 【シード別詳細】 予備実験 - Method: matena_fisher, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 42 | 100.00% | 0.31% | 99.69% |
| safety+medical | matena_fisher | N/A | 43 | 100.00% | 95.62% | 4.38% |
| safety+medical | matena_fisher | N/A | 44 | 100.00% | 90.62% | 8.44% |


---

### 予備実験: Pattern = safety+math+code+medical

#### 【集計】 予備実験 (Mean ± Std) - safety+math+code+medical

| Pattern | Method | Alpha | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.00 | 100.00 ± 0.00% | 62.08 ± 38.13% | 37.92 ± 37.81% |
| safety+math+code+medical | dare | 0.20 | 100.00 ± 0.00% | 51.04 ± 26.81% | 44.69 ± 22.37% |
| safety+math+code+medical | dare | 0.40 | 100.00 ± 0.00% | 41.98 ± 32.73% | 56.04 ± 28.78% |
| safety+math+code+medical | dare | 0.60 | 100.00 ± 0.00% | 70.42 ± 40.72% | 31.46 ± 41.41% |
| safety+math+code+medical | dare | 0.80 | 100.00 ± 0.00% | 44.38 ± 24.88% | 57.71 ± 24.61% |
| safety+math+code+medical | dare | 1.00 | 2.08 ± 1.72% | 0.21 ± 0.18% | 1.77 ± 1.88% |
| safety+math+code+medical | data_free_sst_main | 0.00 | 100.00 ± 0.00% | 56.35 ± 0.18% | 32.40 ± 0.18% |
| safety+math+code+medical | data_free_sst_main | 0.20 | 100.00 ± 0.00% | 98.85 ± 1.26% | 1.46 ± 1.26% |
| safety+math+code+medical | data_free_sst_main | 0.40 | 99.79 ± 0.36% | 88.02 ± 12.36% | 15.83 ± 18.68% |
| safety+math+code+medical | data_free_sst_main | 0.60 | 95.73 ± 6.35% | 84.79 ± 18.14% | 15.62 ± 15.77% |
| safety+math+code+medical | data_free_sst_main | 0.80 | 95.73 ± 6.60% | 76.88 ± 27.72% | 24.58 ± 23.47% |
| safety+math+code+medical | data_free_sst_main | 1.00 | 98.85 ± 1.00% | 72.81 ± 20.73% | 26.15 ± 15.52% |
| safety+math+code+medical | della | 0.00 | 100.00 ± 0.00% | 67.40 ± 28.31% | 35.00 ± 30.09% |
| safety+math+code+medical | della | 0.20 | 100.00 ± 0.00% | 52.92 ± 29.24% | 43.02 ± 26.10% |
| safety+math+code+medical | della | 0.40 | 100.00 ± 0.00% | 44.06 ± 35.83% | 57.92 ± 35.06% |
| safety+math+code+medical | della | 0.60 | 100.00 ± 0.00% | 73.65 ± 24.63% | 28.65 ± 26.34% |
| safety+math+code+medical | della | 0.80 | 100.00 ± 0.00% | 46.35 ± 35.50% | 56.25 ± 30.51% |
| safety+math+code+medical | della | 1.00 | 1.77 ± 2.30% | 0.10 ± 0.18% | 1.35 ± 1.30% |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 100.00 ± 0.00% | 56.25 ± 0.00% | 32.29 ± 0.18% |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 100.00 ± 0.00% | 99.90 ± 0.18% | 0.00 ± 0.00% |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 100.00 ± 0.00% | 93.12 ± 9.21% | 8.44 ± 9.92% |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 97.29 ± 2.01% | 95.31 ± 2.19% | 5.10 ± 0.48% |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 90.00 ± 5.95% | 93.85 ± 5.24% | 5.62 ± 5.70% |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 45.00 ± 18.78% | 93.65 ± 1.72% | 0.52 ± 0.65% |
| safety+math+code+medical | matena_fisher | N/A | 100.00 ± 0.00% | 80.10 ± 0.18% | 16.56 ± 1.36% |
| safety+math+code+medical | task_arithmetic | 0.00 | 100.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+math+code+medical | task_arithmetic | 0.20 | 100.00 ± 0.00% | 98.65 ± 1.83% | 1.15 ± 0.95% |
| safety+math+code+medical | task_arithmetic | 0.40 | 99.17 ± 0.95% | 94.58 ± 6.14% | 4.27 ± 2.80% |
| safety+math+code+medical | task_arithmetic | 0.60 | 66.25 ± 11.12% | 70.73 ± 14.23% | 4.90 ± 1.44% |
| safety+math+code+medical | task_arithmetic | 0.80 | 12.19 ± 6.72% | 3.54 ± 2.35% | 5.62 ± 3.29% |
| safety+math+code+medical | task_arithmetic | 1.00 | 0.83 ± 0.79% | 0.10 ± 0.18% | 1.46 ± 0.79% |
| safety+math+code+medical | ties | 0.00 | 100.00 ± 0.00% | 0.00 ± 0.00% | 100.00 ± 0.00% |
| safety+math+code+medical | ties | 0.20 | 100.00 ± 0.00% | 5.62 ± 7.44% | 94.90 ± 7.78% |
| safety+math+code+medical | ties | 0.40 | 100.00 ± 0.00% | 36.46 ± 55.23% | 62.60 ± 54.56% |
| safety+math+code+medical | ties | 0.60 | 100.00 ± 0.00% | 40.94 ± 49.27% | 60.21 ± 50.93% |
| safety+math+code+medical | ties | 0.80 | 100.00 ± 0.00% | 50.94 ± 49.06% | 51.35 ± 48.65% |
| safety+math+code+medical | ties | 1.00 | 0.73 ± 1.00% | 0.00 ± 0.00% | 1.46 ± 0.95% |


#### 【シード別詳細】 予備実験 - Method: data_free_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.00 | 42 | 100.00% | 56.25% | 32.19% |
| safety+math+code+medical | data_free_sst_main | 0.00 | 43 | 100.00% | 56.56% | 32.50% |
| safety+math+code+medical | data_free_sst_main | 0.00 | 44 | 100.00% | 56.25% | 32.50% |
| safety+math+code+medical | data_free_sst_main | 0.20 | 42 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | data_free_sst_main | 0.20 | 43 | 100.00% | 99.06% | 2.19% |
| safety+math+code+medical | data_free_sst_main | 0.20 | 44 | 100.00% | 97.50% | 2.19% |
| safety+math+code+medical | data_free_sst_main | 0.40 | 42 | 99.38% | 73.75% | 37.19% |
| safety+math+code+medical | data_free_sst_main | 0.40 | 43 | 100.00% | 95.00% | 2.50% |
| safety+math+code+medical | data_free_sst_main | 0.40 | 44 | 100.00% | 95.31% | 7.81% |
| safety+math+code+medical | data_free_sst_main | 0.60 | 42 | 88.44% | 64.38% | 32.50% |
| safety+math+code+medical | data_free_sst_main | 0.60 | 43 | 98.75% | 99.06% | 1.25% |
| safety+math+code+medical | data_free_sst_main | 0.60 | 44 | 100.00% | 90.94% | 13.12% |
| safety+math+code+medical | data_free_sst_main | 0.80 | 42 | 88.12% | 45.00% | 50.94% |
| safety+math+code+medical | data_free_sst_main | 0.80 | 43 | 99.06% | 95.31% | 5.94% |
| safety+math+code+medical | data_free_sst_main | 0.80 | 44 | 100.00% | 90.31% | 16.88% |
| safety+math+code+medical | data_free_sst_main | 1.00 | 42 | 98.12% | 49.38% | 44.06% |
| safety+math+code+medical | data_free_sst_main | 1.00 | 43 | 98.44% | 88.75% | 16.88% |
| safety+math+code+medical | data_free_sst_main | 1.00 | 44 | 100.00% | 80.31% | 17.50% |


#### 【シード別詳細】 予備実験 - Method: diagonal_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 42 | 100.00% | 56.25% | 32.19% |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 43 | 100.00% | 56.25% | 32.50% |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 44 | 100.00% | 56.25% | 32.19% |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 42 | 100.00% | 99.69% | 0.00% |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 43 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 44 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 42 | 100.00% | 98.75% | 0.94% |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 43 | 100.00% | 82.50% | 19.69% |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 44 | 100.00% | 98.12% | 4.69% |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 42 | 98.75% | 92.81% | 5.62% |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 43 | 95.00% | 96.88% | 4.69% |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 44 | 98.12% | 96.25% | 5.00% |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 42 | 96.88% | 87.81% | 12.19% |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 43 | 86.56% | 96.56% | 2.81% |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 44 | 86.56% | 97.19% | 1.88% |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 42 | 66.25% | 91.88% | 1.25% |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 43 | 30.63% | 93.75% | 0.00% |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 44 | 38.12% | 95.31% | 0.31% |


#### 【シード別詳細】 予備実験 - Method: task_arithmetic, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.00 | 42 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | task_arithmetic | 0.00 | 43 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | task_arithmetic | 0.00 | 44 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | task_arithmetic | 0.20 | 42 | 100.00% | 96.56% | 2.19% |
| safety+math+code+medical | task_arithmetic | 0.20 | 43 | 100.00% | 100.00% | 0.31% |
| safety+math+code+medical | task_arithmetic | 0.20 | 44 | 100.00% | 99.38% | 0.94% |
| safety+math+code+medical | task_arithmetic | 0.40 | 42 | 98.12% | 87.50% | 7.50% |
| safety+math+code+medical | task_arithmetic | 0.40 | 43 | 100.00% | 98.44% | 2.50% |
| safety+math+code+medical | task_arithmetic | 0.40 | 44 | 99.38% | 97.81% | 2.81% |
| safety+math+code+medical | task_arithmetic | 0.60 | 42 | 54.69% | 54.37% | 6.56% |
| safety+math+code+medical | task_arithmetic | 0.60 | 43 | 76.88% | 80.31% | 4.06% |
| safety+math+code+medical | task_arithmetic | 0.60 | 44 | 67.19% | 77.50% | 4.06% |
| safety+math+code+medical | task_arithmetic | 0.80 | 42 | 11.88% | 1.25% | 5.94% |
| safety+math+code+medical | task_arithmetic | 0.80 | 43 | 19.06% | 5.94% | 8.75% |
| safety+math+code+medical | task_arithmetic | 0.80 | 44 | 5.62% | 3.44% | 2.19% |
| safety+math+code+medical | task_arithmetic | 1.00 | 42 | 0.94% | 0.31% | 1.56% |
| safety+math+code+medical | task_arithmetic | 1.00 | 43 | 1.56% | 0.00% | 2.19% |
| safety+math+code+medical | task_arithmetic | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: dare, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.00 | 42 | 100.00% | 62.50% | 38.12% |
| safety+math+code+medical | dare | 0.00 | 43 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | dare | 0.00 | 44 | 100.00% | 23.75% | 75.62% |
| safety+math+code+medical | dare | 0.20 | 42 | 100.00% | 69.69% | 29.06% |
| safety+math+code+medical | dare | 0.20 | 43 | 100.00% | 63.12% | 34.69% |
| safety+math+code+medical | dare | 0.20 | 44 | 100.00% | 20.31% | 70.31% |
| safety+math+code+medical | dare | 0.40 | 42 | 100.00% | 39.38% | 57.50% |
| safety+math+code+medical | dare | 0.40 | 43 | 100.00% | 75.94% | 26.56% |
| safety+math+code+medical | dare | 0.40 | 44 | 100.00% | 10.62% | 84.06% |
| safety+math+code+medical | dare | 0.60 | 42 | 100.00% | 88.75% | 11.56% |
| safety+math+code+medical | dare | 0.60 | 43 | 100.00% | 23.75% | 79.06% |
| safety+math+code+medical | dare | 0.60 | 44 | 100.00% | 98.75% | 3.75% |
| safety+math+code+medical | dare | 0.80 | 42 | 100.00% | 45.94% | 50.94% |
| safety+math+code+medical | dare | 0.80 | 43 | 100.00% | 18.75% | 85.00% |
| safety+math+code+medical | dare | 0.80 | 44 | 100.00% | 68.44% | 37.19% |
| safety+math+code+medical | dare | 1.00 | 42 | 2.19% | 0.31% | 1.56% |
| safety+math+code+medical | dare | 1.00 | 43 | 3.75% | 0.00% | 3.75% |
| safety+math+code+medical | dare | 1.00 | 44 | 0.31% | 0.31% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: ties, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.00 | 42 | 100.00% | 0.00% | 100.00% |
| safety+math+code+medical | ties | 0.00 | 43 | 100.00% | 0.00% | 100.00% |
| safety+math+code+medical | ties | 0.00 | 44 | 100.00% | 0.00% | 100.00% |
| safety+math+code+medical | ties | 0.20 | 42 | 100.00% | 2.81% | 98.75% |
| safety+math+code+medical | ties | 0.20 | 43 | 100.00% | 0.00% | 100.00% |
| safety+math+code+medical | ties | 0.20 | 44 | 100.00% | 14.06% | 85.94% |
| safety+math+code+medical | ties | 0.40 | 42 | 100.00% | 9.38% | 87.81% |
| safety+math+code+medical | ties | 0.40 | 43 | 100.00% | 0.00% | 100.00% |
| safety+math+code+medical | ties | 0.40 | 44 | 100.00% | 100.00% | 0.00% |
| safety+math+code+medical | ties | 0.60 | 42 | 100.00% | 27.19% | 77.81% |
| safety+math+code+medical | ties | 0.60 | 43 | 100.00% | 0.00% | 100.00% |
| safety+math+code+medical | ties | 0.60 | 44 | 100.00% | 95.62% | 2.81% |
| safety+math+code+medical | ties | 0.80 | 42 | 100.00% | 100.00% | 0.31% |
| safety+math+code+medical | ties | 0.80 | 43 | 100.00% | 1.88% | 97.19% |
| safety+math+code+medical | ties | 0.80 | 44 | 100.00% | 50.94% | 56.56% |
| safety+math+code+medical | ties | 1.00 | 42 | 0.31% | 0.00% | 1.25% |
| safety+math+code+medical | ties | 1.00 | 43 | 1.88% | 0.00% | 2.50% |
| safety+math+code+medical | ties | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: della, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.00 | 42 | 100.00% | 100.00% | 0.31% |
| safety+math+code+medical | della | 0.00 | 43 | 100.00% | 49.06% | 54.06% |
| safety+math+code+medical | della | 0.00 | 44 | 100.00% | 53.12% | 50.62% |
| safety+math+code+medical | della | 0.20 | 42 | 100.00% | 85.94% | 13.44% |
| safety+math+code+medical | della | 0.20 | 43 | 100.00% | 42.50% | 52.81% |
| safety+math+code+medical | della | 0.20 | 44 | 100.00% | 30.31% | 62.81% |
| safety+math+code+medical | della | 0.40 | 42 | 100.00% | 7.19% | 94.06% |
| safety+math+code+medical | della | 0.40 | 43 | 100.00% | 78.75% | 24.06% |
| safety+math+code+medical | della | 0.40 | 44 | 100.00% | 46.25% | 55.62% |
| safety+math+code+medical | della | 0.60 | 42 | 100.00% | 83.44% | 13.75% |
| safety+math+code+medical | della | 0.60 | 43 | 100.00% | 45.62% | 59.06% |
| safety+math+code+medical | della | 0.60 | 44 | 100.00% | 91.88% | 13.12% |
| safety+math+code+medical | della | 0.80 | 42 | 100.00% | 6.25% | 90.00% |
| safety+math+code+medical | della | 0.80 | 43 | 100.00% | 59.06% | 48.12% |
| safety+math+code+medical | della | 0.80 | 44 | 100.00% | 73.75% | 30.63% |
| safety+math+code+medical | della | 1.00 | 42 | 0.94% | 0.31% | 0.94% |
| safety+math+code+medical | della | 1.00 | 43 | 4.38% | 0.00% | 2.81% |
| safety+math+code+medical | della | 1.00 | 44 | 0.00% | 0.00% | 0.31% |


#### 【シード別詳細】 予備実験 - Method: matena_fisher, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 42 | 100.00% | 80.00% | 17.19% |
| safety+math+code+medical | matena_fisher | N/A | 43 | 100.00% | 80.31% | 17.50% |
| safety+math+code+medical | matena_fisher | N/A | 44 | 100.00% | 80.00% | 15.00% |


---

### 予備実験: Pattern = safety+code

#### 【集計】 予備実験 (Mean ± Std) - safety+code

| Pattern | Method | Alpha | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | dare | 0.00 | 100.00 ± 0.00% | 56.77 ± 31.54% | 44.69 ± 28.23% |
| safety+code | dare | 0.20 | 100.00 ± 0.00% | 71.77 ± 5.98% | 25.31 ± 7.70% |
| safety+code | dare | 0.40 | 100.00 ± 0.00% | 34.69 ± 20.12% | 63.96 ± 17.03% |
| safety+code | dare | 0.60 | 100.00 ± 0.00% | 36.35 ± 12.66% | 64.06 ± 11.87% |
| safety+code | dare | 0.80 | 100.00 ± 0.00% | 51.46 ± 22.71% | 48.96 ± 25.64% |
| safety+code | dare | 1.00 | 1.35 ± 1.10% | 0.00 ± 0.00% | 1.35 ± 1.41% |
| safety+code | data_free_sst_main | 0.00 | 98.44 ± 0.00% | 74.48 ± 0.18% | 21.77 ± 0.90% |
| safety+code | data_free_sst_main | 0.20 | 98.02 ± 0.48% | 77.92 ± 2.80% | 26.67 ± 2.82% |
| safety+code | data_free_sst_main | 0.40 | 94.38 ± 1.65% | 68.44 ± 1.08% | 29.58 ± 3.25% |
| safety+code | data_free_sst_main | 0.60 | 92.60 ± 2.90% | 64.38 ± 1.13% | 27.40 ± 3.77% |
| safety+code | data_free_sst_main | 0.80 | 93.44 ± 3.75% | 62.81 ± 2.19% | 34.38 ± 4.23% |
| safety+code | data_free_sst_main | 1.00 | 99.69 ± 0.54% | 55.10 ± 8.09% | 44.06 ± 10.23% |
| safety+code | della | 0.00 | 100.00 ± 0.00% | 42.19 ± 9.99% | 58.33 ± 11.33% |
| safety+code | della | 0.20 | 100.00 ± 0.00% | 67.08 ± 6.31% | 33.02 ± 5.34% |
| safety+code | della | 0.40 | 100.00 ± 0.00% | 43.75 ± 36.43% | 59.27 ± 30.27% |
| safety+code | della | 0.60 | 100.00 ± 0.00% | 33.65 ± 8.21% | 67.19 ± 5.42% |
| safety+code | della | 0.80 | 100.00 ± 0.00% | 34.17 ± 25.33% | 66.56 ± 23.72% |
| safety+code | della | 1.00 | 1.98 ± 1.78% | 0.21 ± 0.18% | 1.67 ± 1.48% |
| safety+code | diagonal_sst_main | 0.00 | 98.44 ± 0.00% | 74.48 ± 0.18% | 21.88 ± 0.83% |
| safety+code | diagonal_sst_main | 0.20 | 98.23 ± 0.65% | 74.90 ± 1.41% | 32.92 ± 3.78% |
| safety+code | diagonal_sst_main | 0.40 | 98.23 ± 0.48% | 63.96 ± 10.31% | 32.29 ± 3.31% |
| safety+code | diagonal_sst_main | 0.60 | 98.12 ± 1.65% | 76.77 ± 3.31% | 19.58 ± 2.90% |
| safety+code | diagonal_sst_main | 0.80 | 92.71 ± 2.95% | 69.38 ± 3.80% | 25.94 ± 2.72% |
| safety+code | diagonal_sst_main | 1.00 | 77.40 ± 9.23% | 59.58 ± 5.24% | 30.21 ± 5.56% |
| safety+code | led_merging | N/A | 87.19 ± 0.00% | 95.94 ± 0.00% | 5.00 ± 0.00% |
| safety+code | matena_fisher | N/A | 95.62 ± 1.13% | 71.98 ± 1.57% | 28.33 ± 2.22% |
| safety+code | mergealign | N/A | 100.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+code | safemerge | N/A | 4.58 ± 5.81% | 6.25 ± 10.56% | 2.81 ± 2.19% |
| safety+code | task_arithmetic | 0.00 | 71.46 ± 0.72% | 39.17 ± 0.36% | 39.17 ± 0.36% |
| safety+code | task_arithmetic | 0.20 | 87.71 ± 0.65% | 46.56 ± 2.25% | 42.60 ± 2.80% |
| safety+code | task_arithmetic | 0.40 | 76.77 ± 2.08% | 41.98 ± 2.37% | 33.65 ± 0.48% |
| safety+code | task_arithmetic | 0.60 | 82.40 ± 2.73% | 56.67 ± 4.07% | 24.38 ± 3.29% |
| safety+code | task_arithmetic | 0.80 | 21.67 ± 4.55% | 5.00 ± 2.86% | 15.42 ± 3.93% |
| safety+code | task_arithmetic | 1.00 | 0.83 ± 0.79% | 0.10 ± 0.18% | 1.46 ± 0.79% |
| safety+code | ties | 0.00 | 63.85 ± 0.72% | 57.08 ± 1.44% | 18.02 ± 0.36% |
| safety+code | ties | 0.20 | 92.50 ± 2.48% | 77.60 ± 4.03% | 20.10 ± 4.42% |
| safety+code | ties | 0.40 | 96.98 ± 1.26% | 62.60 ± 4.61% | 26.77 ± 4.02% |
| safety+code | ties | 0.60 | 99.38 ± 0.31% | 62.29 ± 6.59% | 34.58 ± 2.37% |
| safety+code | ties | 0.80 | 100.00 ± 0.00% | 68.33 ± 23.31% | 31.35 ± 23.08% |
| safety+code | ties | 1.00 | 0.73 ± 1.00% | 0.00 ± 0.00% | 1.46 ± 0.95% |


#### 【シード別詳細】 予備実験 - Method: task_arithmetic, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.00 | 42 | 70.62% | 38.75% | 38.75% |
| safety+code | task_arithmetic | 0.00 | 43 | 71.88% | 39.38% | 39.38% |
| safety+code | task_arithmetic | 0.00 | 44 | 71.88% | 39.38% | 39.38% |
| safety+code | task_arithmetic | 0.20 | 42 | 88.44% | 48.44% | 44.06% |
| safety+code | task_arithmetic | 0.20 | 43 | 87.50% | 44.06% | 44.38% |
| safety+code | task_arithmetic | 0.20 | 44 | 87.19% | 47.19% | 39.38% |
| safety+code | task_arithmetic | 0.40 | 42 | 75.00% | 44.69% | 34.06% |
| safety+code | task_arithmetic | 0.40 | 43 | 79.06% | 40.31% | 33.75% |
| safety+code | task_arithmetic | 0.40 | 44 | 76.25% | 40.94% | 33.12% |
| safety+code | task_arithmetic | 0.60 | 42 | 83.12% | 56.88% | 24.69% |
| safety+code | task_arithmetic | 0.60 | 43 | 84.69% | 52.50% | 27.50% |
| safety+code | task_arithmetic | 0.60 | 44 | 79.38% | 60.62% | 20.94% |
| safety+code | task_arithmetic | 0.80 | 42 | 19.69% | 4.38% | 15.94% |
| safety+code | task_arithmetic | 0.80 | 43 | 26.88% | 2.50% | 19.06% |
| safety+code | task_arithmetic | 0.80 | 44 | 18.44% | 8.12% | 11.25% |
| safety+code | task_arithmetic | 1.00 | 42 | 0.94% | 0.31% | 1.56% |
| safety+code | task_arithmetic | 1.00 | 43 | 1.56% | 0.00% | 2.19% |
| safety+code | task_arithmetic | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: della, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | della | 0.00 | 42 | 100.00% | 34.38% | 65.94% |
| safety+code | della | 0.00 | 43 | 100.00% | 53.44% | 45.31% |
| safety+code | della | 0.00 | 44 | 100.00% | 38.75% | 63.75% |
| safety+code | della | 0.20 | 42 | 100.00% | 68.12% | 36.56% |
| safety+code | della | 0.20 | 43 | 100.00% | 72.81% | 26.88% |
| safety+code | della | 0.20 | 44 | 100.00% | 60.31% | 35.62% |
| safety+code | della | 0.40 | 42 | 100.00% | 79.38% | 30.63% |
| safety+code | della | 0.40 | 43 | 100.00% | 6.56% | 90.94% |
| safety+code | della | 0.40 | 44 | 100.00% | 45.31% | 56.25% |
| safety+code | della | 0.60 | 42 | 100.00% | 43.12% | 60.94% |
| safety+code | della | 0.60 | 43 | 100.00% | 28.75% | 70.00% |
| safety+code | della | 0.60 | 44 | 100.00% | 29.06% | 70.62% |
| safety+code | della | 0.80 | 42 | 100.00% | 33.12% | 69.38% |
| safety+code | della | 0.80 | 43 | 100.00% | 60.00% | 41.56% |
| safety+code | della | 0.80 | 44 | 100.00% | 9.38% | 88.75% |
| safety+code | della | 1.00 | 42 | 3.44% | 0.31% | 2.81% |
| safety+code | della | 1.00 | 43 | 2.50% | 0.00% | 2.19% |
| safety+code | della | 1.00 | 44 | 0.00% | 0.31% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: dare, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | dare | 0.00 | 42 | 100.00% | 69.06% | 38.12% |
| safety+code | dare | 0.00 | 43 | 100.00% | 20.94% | 75.62% |
| safety+code | dare | 0.00 | 44 | 100.00% | 80.31% | 20.31% |
| safety+code | dare | 0.20 | 42 | 100.00% | 78.12% | 17.19% |
| safety+code | dare | 0.20 | 43 | 100.00% | 66.25% | 32.50% |
| safety+code | dare | 0.20 | 44 | 100.00% | 70.94% | 26.25% |
| safety+code | dare | 0.40 | 42 | 100.00% | 55.94% | 46.88% |
| safety+code | dare | 0.40 | 43 | 100.00% | 32.19% | 64.06% |
| safety+code | dare | 0.40 | 44 | 100.00% | 15.94% | 80.94% |
| safety+code | dare | 0.60 | 42 | 100.00% | 21.88% | 77.50% |
| safety+code | dare | 0.60 | 43 | 100.00% | 41.88% | 55.00% |
| safety+code | dare | 0.60 | 44 | 100.00% | 45.31% | 59.69% |
| safety+code | dare | 0.80 | 42 | 100.00% | 62.81% | 38.75% |
| safety+code | dare | 0.80 | 43 | 100.00% | 66.25% | 30.00% |
| safety+code | dare | 0.80 | 44 | 100.00% | 25.31% | 78.12% |
| safety+code | dare | 1.00 | 42 | 1.25% | 0.00% | 1.25% |
| safety+code | dare | 1.00 | 43 | 2.50% | 0.00% | 2.81% |
| safety+code | dare | 1.00 | 44 | 0.31% | 0.00% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: ties, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | ties | 0.00 | 42 | 63.44% | 56.25% | 17.81% |
| safety+code | ties | 0.00 | 43 | 64.69% | 58.75% | 18.44% |
| safety+code | ties | 0.00 | 44 | 63.44% | 56.25% | 17.81% |
| safety+code | ties | 0.20 | 42 | 93.44% | 80.94% | 15.00% |
| safety+code | ties | 0.20 | 43 | 89.69% | 73.12% | 22.81% |
| safety+code | ties | 0.20 | 44 | 94.38% | 78.75% | 22.50% |
| safety+code | ties | 0.40 | 42 | 98.12% | 59.06% | 29.69% |
| safety+code | ties | 0.40 | 43 | 95.62% | 60.94% | 22.19% |
| safety+code | ties | 0.40 | 44 | 97.19% | 67.81% | 28.44% |
| safety+code | ties | 0.60 | 42 | 99.69% | 65.94% | 35.62% |
| safety+code | ties | 0.60 | 43 | 99.38% | 54.69% | 36.25% |
| safety+code | ties | 0.60 | 44 | 99.06% | 66.25% | 31.87% |
| safety+code | ties | 0.80 | 42 | 100.00% | 44.38% | 56.56% |
| safety+code | ties | 0.80 | 43 | 100.00% | 69.69% | 26.25% |
| safety+code | ties | 0.80 | 44 | 100.00% | 90.94% | 11.25% |
| safety+code | ties | 1.00 | 42 | 0.31% | 0.00% | 1.25% |
| safety+code | ties | 1.00 | 43 | 1.88% | 0.00% | 2.50% |
| safety+code | ties | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: diagonal_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.00 | 42 | 98.44% | 74.69% | 22.81% |
| safety+code | diagonal_sst_main | 0.00 | 43 | 98.44% | 74.38% | 21.25% |
| safety+code | diagonal_sst_main | 0.00 | 44 | 98.44% | 74.38% | 21.56% |
| safety+code | diagonal_sst_main | 0.20 | 42 | 97.50% | 73.44% | 37.19% |
| safety+code | diagonal_sst_main | 0.20 | 43 | 98.44% | 75.00% | 31.56% |
| safety+code | diagonal_sst_main | 0.20 | 44 | 98.75% | 76.25% | 30.00% |
| safety+code | diagonal_sst_main | 0.40 | 42 | 97.81% | 53.75% | 35.31% |
| safety+code | diagonal_sst_main | 0.40 | 43 | 98.75% | 63.75% | 28.75% |
| safety+code | diagonal_sst_main | 0.40 | 44 | 98.12% | 74.38% | 32.81% |
| safety+code | diagonal_sst_main | 0.60 | 42 | 96.25% | 76.25% | 17.19% |
| safety+code | diagonal_sst_main | 0.60 | 43 | 98.75% | 73.75% | 22.81% |
| safety+code | diagonal_sst_main | 0.60 | 44 | 99.38% | 80.31% | 18.75% |
| safety+code | diagonal_sst_main | 0.80 | 42 | 89.38% | 66.88% | 27.19% |
| safety+code | diagonal_sst_main | 0.80 | 43 | 93.75% | 73.75% | 22.81% |
| safety+code | diagonal_sst_main | 0.80 | 44 | 95.00% | 67.50% | 27.81% |
| safety+code | diagonal_sst_main | 1.00 | 42 | 68.44% | 56.88% | 29.06% |
| safety+code | diagonal_sst_main | 1.00 | 43 | 76.88% | 65.62% | 25.31% |
| safety+code | diagonal_sst_main | 1.00 | 44 | 86.88% | 56.25% | 36.25% |


#### 【シード別詳細】 予備実験 - Method: safemerge, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 42 | 11.25% | 18.44% | 5.31% |
| safety+code | safemerge | N/A | 43 | 0.62% | 0.31% | 1.88% |
| safety+code | safemerge | N/A | 44 | 1.88% | 0.00% | 1.25% |


#### 【シード別詳細】 予備実験 - Method: data_free_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.00 | 42 | 98.44% | 74.38% | 21.25% |
| safety+code | data_free_sst_main | 0.00 | 43 | 98.44% | 74.38% | 21.25% |
| safety+code | data_free_sst_main | 0.00 | 44 | 98.44% | 74.69% | 22.81% |
| safety+code | data_free_sst_main | 0.20 | 42 | 98.12% | 74.69% | 23.75% |
| safety+code | data_free_sst_main | 0.20 | 43 | 97.50% | 79.69% | 26.88% |
| safety+code | data_free_sst_main | 0.20 | 44 | 98.44% | 79.38% | 29.38% |
| safety+code | data_free_sst_main | 0.40 | 42 | 95.62% | 69.06% | 32.19% |
| safety+code | data_free_sst_main | 0.40 | 43 | 92.50% | 67.19% | 30.63% |
| safety+code | data_free_sst_main | 0.40 | 44 | 95.00% | 69.06% | 25.94% |
| safety+code | data_free_sst_main | 0.60 | 42 | 90.62% | 63.44% | 30.94% |
| safety+code | data_free_sst_main | 0.60 | 43 | 91.25% | 65.62% | 23.44% |
| safety+code | data_free_sst_main | 0.60 | 44 | 95.94% | 64.06% | 27.81% |
| safety+code | data_free_sst_main | 0.80 | 42 | 93.44% | 65.00% | 34.69% |
| safety+code | data_free_sst_main | 0.80 | 43 | 89.69% | 60.62% | 30.00% |
| safety+code | data_free_sst_main | 0.80 | 44 | 97.19% | 62.81% | 38.44% |
| safety+code | data_free_sst_main | 1.00 | 42 | 100.00% | 61.25% | 32.81% |
| safety+code | data_free_sst_main | 1.00 | 43 | 99.06% | 58.13% | 46.56% |
| safety+code | data_free_sst_main | 1.00 | 44 | 100.00% | 45.94% | 52.81% |


#### 【シード別詳細】 予備実験 - Method: mergealign, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 42 | 100.00% | 100.00% | 0.00% |
| safety+code | mergealign | N/A | 43 | 100.00% | 100.00% | 0.00% |
| safety+code | mergealign | N/A | 44 | 100.00% | 100.00% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: led_merging, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 42 | 87.19% | 95.94% | 5.00% |
| safety+code | led_merging | N/A | 43 | 87.19% | 95.94% | 5.00% |
| safety+code | led_merging | N/A | 44 | 87.19% | 95.94% | 5.00% |


#### 【シード別詳細】 予備実験 - Method: matena_fisher, Pattern: safety+code

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 42 | 96.56% | 72.19% | 25.94% |
| safety+code | matena_fisher | N/A | 43 | 94.38% | 73.44% | 28.75% |
| safety+code | matena_fisher | N/A | 44 | 95.94% | 70.31% | 30.31% |


---

### 予備実験: Pattern = safety+math

#### 【集計】 予備実験 (Mean ± Std) - safety+math

| Pattern | Method | Alpha | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | dare | 0.00 | 70.00 ± 2.72% | 19.17 ± 2.08% | 35.31 ± 1.13% |
| safety+math | dare | 0.20 | 24.27 ± 3.70% | 30.42 ± 5.08% | 16.46 ± 1.48% |
| safety+math | dare | 0.40 | 20.42 ± 2.01% | 27.08 ± 2.95% | 12.19 ± 0.31% |
| safety+math | dare | 0.60 | 17.19 ± 0.83% | 18.65 ± 0.95% | 9.69 ± 2.86% |
| safety+math | dare | 0.80 | 12.19 ± 4.73% | 21.15 ± 4.07% | 7.71 ± 3.13% |
| safety+math | dare | 1.00 | 1.15 ± 1.26% | 0.31 ± 0.31% | 1.04 ± 1.00% |
| safety+math | data_free_sst_main | 0.00 | 70.42 ± 0.18% | 17.08 ± 0.36% | 35.42 ± 0.36% |
| safety+math | data_free_sst_main | 0.20 | 60.94 ± 2.72% | 18.65 ± 1.72% | 31.15 ± 1.10% |
| safety+math | data_free_sst_main | 0.40 | 47.08 ± 1.54% | 20.00 ± 5.14% | 25.10 ± 1.88% |
| safety+math | data_free_sst_main | 0.60 | 36.88 ± 3.25% | 36.04 ± 4.24% | 21.15 ± 0.36% |
| safety+math | data_free_sst_main | 0.80 | 22.92 ± 0.18% | 37.29 ± 0.72% | 16.56 ± 1.56% |
| safety+math | data_free_sst_main | 1.00 | 22.50 ± 3.79% | 17.29 ± 5.20% | 14.06 ± 1.65% |
| safety+math | della | 0.00 | 68.96 ± 1.30% | 20.83 ± 1.41% | 35.62 ± 1.25% |
| safety+math | della | 0.20 | 24.58 ± 3.34% | 28.33 ± 4.70% | 17.60 ± 2.51% |
| safety+math | della | 0.40 | 21.56 ± 0.62% | 23.12 ± 11.56% | 10.94 ± 0.00% |
| safety+math | della | 0.60 | 19.06 ± 3.17% | 20.62 ± 5.20% | 7.81 ± 2.05% |
| safety+math | della | 0.80 | 13.54 ± 3.82% | 17.71 ± 2.69% | 8.65 ± 2.95% |
| safety+math | della | 1.00 | 1.15 ± 1.48% | 0.31 ± 0.31% | 1.46 ± 1.10% |
| safety+math | diagonal_sst_main | 0.00 | 70.42 ± 0.18% | 17.08 ± 0.36% | 35.42 ± 0.36% |
| safety+math | diagonal_sst_main | 0.20 | 56.98 ± 1.72% | 21.77 ± 3.07% | 26.88 ± 1.36% |
| safety+math | diagonal_sst_main | 0.40 | 41.25 ± 2.17% | 32.50 ± 7.04% | 20.21 ± 0.18% |
| safety+math | diagonal_sst_main | 0.60 | 24.38 ± 1.74% | 58.44 ± 5.94% | 12.81 ± 2.44% |
| safety+math | diagonal_sst_main | 0.80 | 11.25 ± 0.54% | 38.33 ± 26.46% | 6.77 ± 0.48% |
| safety+math | diagonal_sst_main | 1.00 | 2.71 ± 1.00% | 3.12 ± 2.56% | 2.08 ± 0.18% |
| safety+math | led_merging | N/A | 87.19 ± 0.00% | 96.15 ± 0.18% | 5.00 ± 0.00% |
| safety+math | matena_fisher | N/A | 19.79 ± 1.18% | 67.19 ± 3.52% | 10.00 ± 1.65% |
| safety+math | mergealign | N/A | 100.00 ± 0.00% | 100.00 ± 0.00% | 0.00 ± 0.00% |
| safety+math | safemerge | N/A | 14.27 ± 22.55% | 31.15 ± 53.95% | 3.33 ± 3.34% |
| safety+math | task_arithmetic | 0.00 | 66.88 ± 0.00% | 19.69 ± 0.00% | 35.62 ± 0.00% |
| safety+math | task_arithmetic | 0.20 | 52.81 ± 2.72% | 26.25 ± 1.90% | 23.65 ± 1.30% |
| safety+math | task_arithmetic | 0.40 | 31.15 ± 4.08% | 48.33 ± 5.39% | 16.46 ± 0.36% |
| safety+math | task_arithmetic | 0.60 | 9.69 ± 0.31% | 47.92 ± 18.35% | 6.35 ± 1.91% |
| safety+math | task_arithmetic | 0.80 | 1.67 ± 1.30% | 0.94 ± 0.83% | 1.67 ± 1.00% |
| safety+math | task_arithmetic | 1.00 | 0.83 ± 0.79% | 0.10 ± 0.18% | 1.46 ± 0.79% |
| safety+math | ties | 0.00 | 72.50 ± 0.00% | 30.31 ± 0.00% | 29.38 ± 0.00% |
| safety+math | ties | 0.20 | 25.00 ± 4.23% | 38.75 ± 2.78% | 14.48 ± 2.55% |
| safety+math | ties | 0.40 | 26.77 ± 3.19% | 39.79 ± 3.28% | 14.27 ± 0.79% |
| safety+math | ties | 0.60 | 18.65 ± 4.77% | 36.67 ± 4.77% | 11.25 ± 1.08% |
| safety+math | ties | 0.80 | 9.79 ± 5.56% | 19.58 ± 19.59% | 4.90 ± 2.37% |
| safety+math | ties | 1.00 | 0.73 ± 1.00% | 0.00 ± 0.00% | 1.46 ± 0.95% |


#### 【シード別詳細】 予備実験 - Method: data_free_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.00 | 42 | 70.31% | 16.88% | 35.62% |
| safety+math | data_free_sst_main | 0.00 | 43 | 70.62% | 17.50% | 35.00% |
| safety+math | data_free_sst_main | 0.00 | 44 | 70.31% | 16.88% | 35.62% |
| safety+math | data_free_sst_main | 0.20 | 42 | 59.69% | 18.75% | 32.19% |
| safety+math | data_free_sst_main | 0.20 | 43 | 64.06% | 16.88% | 31.25% |
| safety+math | data_free_sst_main | 0.20 | 44 | 59.06% | 20.31% | 30.00% |
| safety+math | data_free_sst_main | 0.40 | 42 | 48.12% | 22.81% | 25.31% |
| safety+math | data_free_sst_main | 0.40 | 43 | 47.81% | 23.12% | 23.12% |
| safety+math | data_free_sst_main | 0.40 | 44 | 45.31% | 14.06% | 26.88% |
| safety+math | data_free_sst_main | 0.60 | 42 | 33.12% | 36.56% | 20.94% |
| safety+math | data_free_sst_main | 0.60 | 43 | 38.75% | 40.00% | 21.56% |
| safety+math | data_free_sst_main | 0.60 | 44 | 38.75% | 31.56% | 20.94% |
| safety+math | data_free_sst_main | 0.80 | 42 | 22.81% | 36.88% | 16.56% |
| safety+math | data_free_sst_main | 0.80 | 43 | 22.81% | 36.88% | 15.00% |
| safety+math | data_free_sst_main | 0.80 | 44 | 23.12% | 38.12% | 18.12% |
| safety+math | data_free_sst_main | 1.00 | 42 | 18.44% | 13.12% | 12.81% |
| safety+math | data_free_sst_main | 1.00 | 43 | 23.12% | 15.62% | 13.44% |
| safety+math | data_free_sst_main | 1.00 | 44 | 25.94% | 23.12% | 15.94% |


#### 【シード別詳細】 予備実験 - Method: della, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | della | 0.00 | 42 | 70.00% | 22.19% | 35.62% |
| safety+math | della | 0.00 | 43 | 67.50% | 20.94% | 36.88% |
| safety+math | della | 0.00 | 44 | 69.38% | 19.38% | 34.38% |
| safety+math | della | 0.20 | 42 | 22.81% | 25.31% | 15.00% |
| safety+math | della | 0.20 | 43 | 22.50% | 33.75% | 17.81% |
| safety+math | della | 0.20 | 44 | 28.44% | 25.94% | 20.00% |
| safety+math | della | 0.40 | 42 | 20.94% | 20.94% | 10.94% |
| safety+math | della | 0.40 | 43 | 21.56% | 35.62% | 10.94% |
| safety+math | della | 0.40 | 44 | 22.19% | 12.81% | 10.94% |
| safety+math | della | 0.60 | 42 | 16.25% | 26.56% | 5.94% |
| safety+math | della | 0.60 | 43 | 18.44% | 18.44% | 7.50% |
| safety+math | della | 0.60 | 44 | 22.50% | 16.88% | 10.00% |
| safety+math | della | 0.80 | 42 | 9.38% | 15.31% | 5.31% |
| safety+math | della | 0.80 | 43 | 14.37% | 17.19% | 9.69% |
| safety+math | della | 0.80 | 44 | 16.88% | 20.62% | 10.94% |
| safety+math | della | 1.00 | 42 | 0.62% | 0.62% | 2.50% |
| safety+math | della | 1.00 | 43 | 2.81% | 0.31% | 1.56% |
| safety+math | della | 1.00 | 44 | 0.00% | 0.00% | 0.31% |


#### 【シード別詳細】 予備実験 - Method: safemerge, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 42 | 40.31% | 93.44% | 7.19% |
| safety+math | safemerge | N/A | 43 | 1.25% | 0.00% | 1.56% |
| safety+math | safemerge | N/A | 44 | 1.25% | 0.00% | 1.25% |


#### 【シード別詳細】 予備実験 - Method: ties, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | ties | 0.00 | 42 | 72.50% | 30.31% | 29.38% |
| safety+math | ties | 0.00 | 43 | 72.50% | 30.31% | 29.38% |
| safety+math | ties | 0.00 | 44 | 72.50% | 30.31% | 29.38% |
| safety+math | ties | 0.20 | 42 | 20.62% | 40.94% | 11.56% |
| safety+math | ties | 0.20 | 43 | 29.06% | 39.69% | 15.62% |
| safety+math | ties | 0.20 | 44 | 25.31% | 35.62% | 16.25% |
| safety+math | ties | 0.40 | 42 | 23.12% | 43.12% | 13.44% |
| safety+math | ties | 0.40 | 43 | 28.12% | 39.69% | 15.00% |
| safety+math | ties | 0.40 | 44 | 29.06% | 36.56% | 14.37% |
| safety+math | ties | 0.60 | 42 | 13.44% | 41.88% | 11.88% |
| safety+math | ties | 0.60 | 43 | 19.69% | 32.50% | 10.00% |
| safety+math | ties | 0.60 | 44 | 22.81% | 35.62% | 11.88% |
| safety+math | ties | 0.80 | 42 | 3.75% | 1.88% | 2.19% |
| safety+math | ties | 0.80 | 43 | 10.94% | 16.25% | 5.94% |
| safety+math | ties | 0.80 | 44 | 14.69% | 40.62% | 6.56% |
| safety+math | ties | 1.00 | 42 | 0.31% | 0.00% | 1.25% |
| safety+math | ties | 1.00 | 43 | 1.88% | 0.00% | 2.50% |
| safety+math | ties | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: task_arithmetic, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.00 | 42 | 66.88% | 19.69% | 35.62% |
| safety+math | task_arithmetic | 0.00 | 43 | 66.88% | 19.69% | 35.62% |
| safety+math | task_arithmetic | 0.00 | 44 | 66.88% | 19.69% | 35.62% |
| safety+math | task_arithmetic | 0.20 | 42 | 55.94% | 27.50% | 24.69% |
| safety+math | task_arithmetic | 0.20 | 43 | 51.56% | 27.19% | 24.06% |
| safety+math | task_arithmetic | 0.20 | 44 | 50.94% | 24.06% | 22.19% |
| safety+math | task_arithmetic | 0.40 | 42 | 26.88% | 49.38% | 16.25% |
| safety+math | task_arithmetic | 0.40 | 43 | 31.56% | 53.12% | 16.25% |
| safety+math | task_arithmetic | 0.40 | 44 | 35.00% | 42.50% | 16.88% |
| safety+math | task_arithmetic | 0.60 | 42 | 10.00% | 26.88% | 4.69% |
| safety+math | task_arithmetic | 0.60 | 43 | 9.38% | 60.62% | 8.44% |
| safety+math | task_arithmetic | 0.60 | 44 | 9.69% | 56.25% | 5.94% |
| safety+math | task_arithmetic | 0.80 | 42 | 1.25% | 0.00% | 0.94% |
| safety+math | task_arithmetic | 0.80 | 43 | 3.12% | 1.25% | 2.81% |
| safety+math | task_arithmetic | 0.80 | 44 | 0.62% | 1.56% | 1.25% |
| safety+math | task_arithmetic | 1.00 | 42 | 0.94% | 0.31% | 1.56% |
| safety+math | task_arithmetic | 1.00 | 43 | 1.56% | 0.00% | 2.19% |
| safety+math | task_arithmetic | 1.00 | 44 | 0.00% | 0.00% | 0.62% |


#### 【シード別詳細】 予備実験 - Method: dare, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | dare | 0.00 | 42 | 71.25% | 16.88% | 36.56% |
| safety+math | dare | 0.00 | 43 | 71.88% | 20.94% | 35.00% |
| safety+math | dare | 0.00 | 44 | 66.88% | 19.69% | 34.38% |
| safety+math | dare | 0.20 | 42 | 20.00% | 34.38% | 15.31% |
| safety+math | dare | 0.20 | 43 | 26.25% | 32.19% | 18.12% |
| safety+math | dare | 0.20 | 44 | 26.56% | 24.69% | 15.94% |
| safety+math | dare | 0.40 | 42 | 21.25% | 23.75% | 12.19% |
| safety+math | dare | 0.40 | 43 | 18.12% | 29.38% | 12.50% |
| safety+math | dare | 0.40 | 44 | 21.88% | 28.12% | 11.88% |
| safety+math | dare | 0.60 | 42 | 17.50% | 19.69% | 12.19% |
| safety+math | dare | 0.60 | 43 | 16.25% | 17.81% | 6.56% |
| safety+math | dare | 0.60 | 44 | 17.81% | 18.44% | 10.31% |
| safety+math | dare | 0.80 | 42 | 6.88% | 20.94% | 4.69% |
| safety+math | dare | 0.80 | 43 | 13.75% | 17.19% | 10.94% |
| safety+math | dare | 0.80 | 44 | 15.94% | 25.31% | 7.50% |
| safety+math | dare | 1.00 | 42 | 0.94% | 0.31% | 0.62% |
| safety+math | dare | 1.00 | 43 | 2.50% | 0.62% | 2.19% |
| safety+math | dare | 1.00 | 44 | 0.00% | 0.00% | 0.31% |


#### 【シード別詳細】 予備実験 - Method: mergealign, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 42 | 100.00% | 100.00% | 0.00% |
| safety+math | mergealign | N/A | 43 | 100.00% | 100.00% | 0.00% |
| safety+math | mergealign | N/A | 44 | 100.00% | 100.00% | 0.00% |


#### 【シード別詳細】 予備実験 - Method: diagonal_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.00 | 42 | 70.62% | 17.50% | 35.00% |
| safety+math | diagonal_sst_main | 0.00 | 43 | 70.31% | 16.88% | 35.62% |
| safety+math | diagonal_sst_main | 0.00 | 44 | 70.31% | 16.88% | 35.62% |
| safety+math | diagonal_sst_main | 0.20 | 42 | 58.75% | 25.31% | 27.50% |
| safety+math | diagonal_sst_main | 0.20 | 43 | 55.31% | 20.00% | 25.31% |
| safety+math | diagonal_sst_main | 0.20 | 44 | 56.88% | 20.00% | 27.81% |
| safety+math | diagonal_sst_main | 0.40 | 42 | 42.50% | 28.44% | 20.31% |
| safety+math | diagonal_sst_main | 0.40 | 43 | 38.75% | 40.62% | 20.00% |
| safety+math | diagonal_sst_main | 0.40 | 44 | 42.50% | 28.44% | 20.31% |
| safety+math | diagonal_sst_main | 0.60 | 42 | 26.25% | 52.50% | 14.06% |
| safety+math | diagonal_sst_main | 0.60 | 43 | 22.81% | 64.38% | 14.37% |
| safety+math | diagonal_sst_main | 0.60 | 44 | 24.06% | 58.44% | 10.00% |
| safety+math | diagonal_sst_main | 0.80 | 42 | 10.62% | 61.25% | 6.25% |
| safety+math | diagonal_sst_main | 0.80 | 43 | 11.56% | 9.38% | 7.19% |
| safety+math | diagonal_sst_main | 0.80 | 44 | 11.56% | 44.38% | 6.88% |
| safety+math | diagonal_sst_main | 1.00 | 42 | 3.12% | 2.50% | 2.19% |
| safety+math | diagonal_sst_main | 1.00 | 43 | 3.44% | 0.94% | 1.88% |
| safety+math | diagonal_sst_main | 1.00 | 44 | 1.56% | 5.94% | 2.19% |


#### 【シード別詳細】 予備実験 - Method: led_merging, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 42 | 87.19% | 96.25% | 5.00% |
| safety+math | led_merging | N/A | 43 | 87.19% | 96.25% | 5.00% |
| safety+math | led_merging | N/A | 44 | 87.19% | 95.94% | 5.00% |


#### 【シード別詳細】 予備実験 - Method: matena_fisher, Pattern: safety+math

| Pattern | Method | Alpha | Seed | TrustLLM Raw ASR (ASR↓ %) | Gibberish Ratio (崩壊率↑ %) | BeaverTails Utility (Score↑ %) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 42 | 18.44% | 65.31% | 8.75% |
| safety+math | matena_fisher | N/A | 43 | 20.31% | 71.25% | 11.88% |
| safety+math | matena_fisher | N/A | 44 | 20.62% | 65.00% | 9.38% |


---

## 2. メイン実験 (Alpha=0.6 / 単一実行手法)
広範なベンチマークにおける各手法の安全性(ASR↓)と有用性(Accuracy/WinRate↑)の比較表。

### メイン実験: Pattern = safety+math+code+medical

#### 【集計】 メイン実験 (Mean ± Std) - safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.60 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 38.02 ± 41.77% | 11.53 ± 0.23% | 5368837.19 ± 6493560.14 | 6550135.45 ± 3035748.48 |
| safety+math+code+medical | dare | 1.00 | 0.00 ± 0.00% | 0.68 ± 0.70% | 5.36 ± 2.13% | 55.83 ± 25.27% | 17.94 ± 12.11% | 2.35 ± 0.03 | 7.15 ± 0.10 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.67 ± 24.56% | 11.85 ± 0.59% | 8840.75 ± 1530.06 | 17110.70 ± 5533.52 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 62.40 ± 27.79% | 11.48 ± 0.20% | 6377.05 ± 1134.31 | 5459.66 ± 490.26 |
| safety+math+code+medical | della | 0.60 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 15.42 ± 16.18% | 12.53 ± 0.78% | 1556853.48 ± 450599.15 | 2115706.72 ± 117978.22 |
| safety+math+code+medical | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.31% | 4.58 ± 3.10% | 57.60 ± 23.98% | 18.90 ± 12.88% | 2.39 ± 0.04 | 7.38 ± 0.06 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 0.00 ± 0.00% | 0.42 ± 0.18% | 0.00 ± 0.00% | 57.29 ± 17.67% | 10.16 ± 0.49% | 319.70 ± 69.81 | 139.54 ± 27.87 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 0.16 ± 0.00% | 0.26 ± 0.24% | 0.00 ± 0.00% | 80.83 ± 8.57% | 11.10 ± 1.30% | 78.49 ± 39.87 | 78.49 ± 32.65 |
| safety+math+code+medical | matena_fisher | N/A | 0.00 ± 0.00% | 0.99 ± 0.24% | 0.00 ± 0.00% | 27.81 ± 3.29% | 13.12 ± 0.12% | 63.52 ± 2.39 | 128.84 ± 4.62 |
| safety+math+code+medical | task_arithmetic | 0.60 | 5.88 ± 0.55% | 2.55 ± 0.39% | 0.05 ± 0.09% | 65.42 ± 9.24% | 13.26 ± 1.65% | 3.22 ± 0.04 | 6.16 ± 0.11 |
| safety+math+code+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.50% | 4.22 ± 3.39% | 58.12 ± 23.35% | 18.28 ± 12.09% | 2.34 ± 0.03 | 7.15 ± 0.13 |
| safety+math+code+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.17 ± 7.94% | 12.28 ± 0.40% | 233905.82 ± 257072.89 | 291983.62 ± 249888.17 |
| safety+math+code+medical | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 23.30 ± 18.12% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 42.0 | 0.00% | 0.94% | 0.00% | 30.94% | 12.98% | 65.01 | 124.79 |
| safety+math+code+medical | matena_fisher | N/A | 43.0 | 0.00% | 0.78% | 0.00% | 28.12% | 13.15% | 60.76 | 127.88 |
| safety+math+code+medical | matena_fisher | N/A | 44.0 | 0.00% | 1.25% | 0.00% | 24.38% | 13.22% | 64.78 | 133.87 |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 42.0 | 0.00% | 0.62% | 0.00% | 40.00% | 10.41% | 392.09 | 168.34 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.31% | 0.00% | 75.31% | 10.48% | 252.79 | 112.69 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 44.0 | 0.00% | 0.31% | 0.00% | 56.56% | 9.59% | 314.23 | 137.59 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 42.0 | 0.16% | 0.47% | 0.00% | 85.94% | 12.28% | 119.75 | 108.05 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 43.0 | 0.16% | 0.31% | 0.00% | 85.62% | 11.31% | 40.18 | 43.44 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 70.94% | 9.71% | 75.56 | 83.97 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 86.25% | 11.42% | 12857479.52 | 10037855.54 |
| safety+math+code+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 14.06% | 11.38% | 1950859.88 | 4501931.51 |
| safety+math+code+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 11.79% | 1298172.17 | 5110619.29 |
| safety+math+code+medical | dare | 1.00 | 42.0 | 0.00% | 1.41% | 7.81% | 84.06% | 31.92% | 2.31 | 7.26 |
| safety+math+code+medical | dare | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 48.12% | 10.60% | 2.36 | 7.08 |
| safety+math+code+medical | dare | 1.00 | 44.0 | 0.00% | 0.00% | 4.38% | 35.31% | 11.30% | 2.37 | 7.10 |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.44% | 11.64% | 1547222.80 | 1979585.04 |
| safety+math+code+medical | della | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 0.31% | 12.97% | 1111146.86 | 2188460.85 |
| safety+math+code+medical | della | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 32.50% | 13.00% | 2012190.77 | 2179074.27 |
| safety+math+code+medical | della | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.69% | 33.77% | 2.34 | 7.44 |
| safety+math+code+medical | della | 1.00 | 43.0 | 0.00% | 0.62% | 2.34% | 49.06% | 11.21% | 2.41 | 7.34 |
| safety+math+code+medical | della | 1.00 | 44.0 | 0.00% | 0.31% | 3.28% | 39.06% | 11.72% | 2.42 | 7.35 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.44% | 12.53% | 8906.95 | 19263.61 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 11.56% | 11.50% | 7278.66 | 10824.29 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 55.00% | 11.51% | 10336.63 | 21244.18 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 31.87% | 11.30% | 7255.67 | 4971.49 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 69.06% | 11.69% | 6778.98 | 5455.51 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.44% | 5096.50 | 5951.99 |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.22% | 104380.52 | 193731.31 |
| safety+math+code+medical | ties | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.91% | 529977.51 | 576065.00 |
| safety+math+code+medical | ties | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 12.71% | 67359.44 | 106154.54 |
| safety+math+code+medical | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 44.16% | 2.24 | 6.85 |
| safety+math+code+medical | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.49% | 2.28 | 6.71 |
| safety+math+code+medical | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 14.25% | 2.29 | 6.60 |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.60 | 42.0 | 5.77% | 2.19% | 0.16% | 73.44% | 14.72% | 3.17 | 6.10 |
| safety+math+code+medical | task_arithmetic | 0.60 | 43.0 | 6.48% | 2.50% | 0.00% | 67.50% | 13.59% | 3.25 | 6.28 |
| safety+math+code+medical | task_arithmetic | 0.60 | 44.0 | 5.40% | 2.97% | 0.00% | 55.31% | 11.48% | 3.24 | 6.10 |
| safety+math+code+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.38% | 32.24% | 2.31 | 7.26 |
| safety+math+code+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+math+code+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.69% | 11.37% | 2.36 | 7.00 |


---

### メイン実験: Pattern = safety+math

#### 【集計】 メイン実験 (Mean ± Std) - safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.60 | 6.14 ± 5.14% | 5.42 ± 0.79% | 5.00 ± 1.02% | 84.27 ± 2.35% | 22.85 ± 8.57% | 2.43 ± 0.07 | 4.44 ± 0.28 |
| safety+math | dare | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.63% | 5.68 ± 3.61% | 55.94 ± 25.88% | 11.22 ± 0.57% | 2.35 ± 0.03 | 7.18 ± 0.22 |
| safety+math | data_free_sst_main | 0.60 | 14.73 ± 3.41% | 5.57 ± 0.24% | 7.19 ± 4.33% | 69.38 ± 13.52% | 24.69 ± 0.38% | 2.02 ± 0.02 | 3.02 ± 0.02 |
| safety+math | data_free_sst_main | 1.00 | 11.49 ± 9.25% | 5.89 ± 0.79% | 5.57 ± 0.24% | 56.77 ± 26.43% | 21.14 ± 7.66% | 2.19 ± 0.04 | 4.64 ± 0.10 |
| safety+math | della | 0.60 | 6.66 ± 5.52% | 5.52 ± 0.63% | 5.31 ± 1.36% | 85.62 ± 0.54% | 31.03 ± 4.06% | 2.46 ± 0.06 | 4.50 ± 0.30 |
| safety+math | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.41% | 4.69 ± 3.29% | 58.54 ± 23.27% | 17.78 ± 11.72% | 2.38 ± 0.03 | 7.33 ± 0.14 |
| safety+math | diagonal_sst_main | 0.60 | 17.09 ± 5.01% | 6.82 ± 0.86% | 6.72 ± 0.95% | 72.55 ± 15.91% | 22.48 ± 8.92% | 1.84 ± 0.01 | 2.75 ± 0.05 |
| safety+math | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 9.84 ± 0.47% | 7.76 ± 3.63% | 65.42 ± 31.57% | 20.65 ± 6.27% | 1.98 ± 0.07 | 4.36 ± 0.49 |
| safety+math | led_merging | N/A | 2.80 ± 0.00% | 1.41 ± 0.00% | 5.62 ± 0.00% | 83.75 ± 0.00% | 22.51 ± 0.02% | 1.75 ± 0.00 | 2.72 ± 0.00 |
| safety+math | matena_fisher | N/A | 4.29 ± 0.43% | 6.04 ± 0.86% | 6.61 ± 0.39% | 85.73 ± 0.65% | 26.72 ± 11.70% | 1.82 ± 0.01 | 2.88 ± 0.02 |
| safety+math | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 15.73 ± 3.41% | - | - |
| safety+math | safemerge | N/A | 4.61 ± 7.99% | 1.30 ± 0.86% | 6.67 ± 4.86% | 82.50 ± 1.74% | 13.09 ± 1.77% | 2.22 ± 0.48 | 6.41 ± 3.54 |
| safety+math | task_arithmetic | 0.60 | 2.48 ± 2.89% | 6.88 ± 1.56% | 7.50 ± 0.68% | 75.21 ± 15.93% | 27.18 ± 6.92% | 1.88 ± 0.02 | 3.47 ± 0.12 |
| safety+math | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.54% | 6.93 ± 8.08% | 48.80 ± 8.77% | 18.36 ± 12.02% | 2.34 ± 0.03 | 7.15 ± 0.14 |
| safety+math | ties | 0.60 | 9.03 ± 5.55% | 5.94 ± 0.83% | 6.15 ± 0.18% | 85.00 ± 2.44% | 27.65 ± 3.07% | 2.15 ± 0.05 | 3.57 ± 0.10 |
| safety+math | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 25.52 ± 16.78% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | della | 0.60 | 42.0 | 0.63% | 4.84% | 6.25% | 85.31% | 29.00% | 2.39 | 4.26 |
| safety+math | della | 0.60 | 43.0 | 11.45% | 5.62% | 5.94% | 85.31% | 28.39% | 2.47 | 4.41 |
| safety+math | della | 0.60 | 44.0 | 7.92% | 6.09% | 3.75% | 86.25% | 35.70% | 2.51 | 4.84 |
| safety+math | della | 1.00 | 42.0 | 0.00% | 0.78% | 7.81% | 85.00% | 31.29% | 2.35 | 7.45 |
| safety+math | della | 1.00 | 43.0 | 0.00% | 0.94% | 1.25% | 49.38% | 10.38% | 2.41 | 7.37 |
| safety+math | della | 1.00 | 44.0 | 0.00% | 0.16% | 5.00% | 41.25% | 11.68% | 2.40 | 7.17 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 42.0 | 4.71% | 6.09% | 6.25% | 85.00% | 39.12% | 1.81 | 2.90 |
| safety+math | matena_fisher | N/A | 43.0 | 4.30% | 5.16% | 7.03% | 86.25% | 15.87% | 1.83 | 2.86 |
| safety+math | matena_fisher | N/A | 44.0 | 3.85% | 6.88% | 6.56% | 85.94% | 25.17% | 1.84 | 2.88 |


#### 【シード別詳細】 メイン実験 - Method: safemerge, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 42.0 | 13.84% | 2.19% | 8.91% | 80.62% | 15.06% | 1.71 | 2.51 |
| safety+math | safemerge | N/A | 43.0 | 0.00% | 0.47% | 1.09% | 84.06% | 11.63% | 2.66 | 9.43 |
| safety+math | safemerge | N/A | 44.0 | 0.00% | 1.25% | 10.00% | 82.81% | 12.60% | 2.30 | 7.29 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.60 | 42.0 | 0.32% | 6.25% | 5.16% | 84.38% | 15.04% | 2.35 | 4.18 |
| safety+math | dare | 0.60 | 43.0 | 8.06% | 4.69% | 5.94% | 81.88% | 21.51% | 2.46 | 4.40 |
| safety+math | dare | 0.60 | 44.0 | 10.04% | 5.31% | 3.91% | 86.56% | 32.02% | 2.48 | 4.73 |
| safety+math | dare | 1.00 | 42.0 | 0.00% | 1.25% | 9.06% | 85.62% | 11.49% | 2.32 | 7.37 |
| safety+math | dare | 1.00 | 43.0 | 0.00% | 0.47% | 1.88% | 44.06% | 10.56% | 2.37 | 7.23 |
| safety+math | dare | 1.00 | 44.0 | 0.00% | 0.00% | 6.09% | 38.12% | 11.61% | 2.36 | 6.93 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.60 | 42.0 | 10.89% | 5.31% | 12.19% | 54.06% | 24.30% | 1.99 | 3.03 |
| safety+math | data_free_sst_main | 0.60 | 43.0 | 15.92% | 5.78% | 4.84% | 74.38% | 25.07% | 2.02 | 3.04 |
| safety+math | data_free_sst_main | 0.60 | 44.0 | 17.39% | 5.62% | 4.53% | 79.69% | 24.70% | 2.04 | 3.00 |
| safety+math | data_free_sst_main | 1.00 | 42.0 | 0.95% | 5.78% | 5.31% | 28.75% | 13.26% | 2.14 | 4.52 |
| safety+math | data_free_sst_main | 1.00 | 43.0 | 18.26% | 6.72% | 5.78% | 60.31% | 28.55% | 2.23 | 4.71 |
| safety+math | data_free_sst_main | 1.00 | 44.0 | 15.26% | 5.16% | 5.62% | 81.25% | 21.63% | 2.21 | 4.69 |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | ties | 0.60 | 42.0 | 3.28% | 6.88% | 6.25% | 86.25% | 24.12% | 2.10 | 3.46 |
| safety+math | ties | 0.60 | 43.0 | 9.45% | 5.62% | 6.25% | 82.19% | 29.17% | 2.16 | 3.61 |
| safety+math | ties | 0.60 | 44.0 | 14.36% | 5.31% | 5.94% | 86.56% | 29.67% | 2.19 | 3.64 |
| safety+math | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 44.14% | 2.24 | 6.85 |
| safety+math | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.60% | 2.28 | 6.71 |
| safety+math | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 20.81% | 2.29 | 6.60 |


#### 【シード別詳細】 メイン実験 - Method: led_merging, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 42.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.50% | 1.75 | 2.72 |
| safety+math | led_merging | N/A | 43.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.52% | 1.75 | 2.72 |
| safety+math | led_merging | N/A | 44.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.49% | 1.75 | 2.72 |


#### 【シード別詳細】 メイン実験 - Method: mergealign, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |
| safety+math | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |
| safety+math | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.60 | 42.0 | 0.16% | 8.44% | 6.72% | 56.88% | 35.05% | 1.86 | 3.48 |
| safety+math | task_arithmetic | 0.60 | 43.0 | 1.57% | 5.31% | 7.97% | 83.12% | 22.05% | 1.89 | 3.34 |
| safety+math | task_arithmetic | 0.60 | 44.0 | 5.72% | 6.88% | 7.81% | 85.62% | 24.45% | 1.89 | 3.57 |
| safety+math | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 16.25% | 56.72% | 32.24% | 2.31 | 7.26 |
| safety+math | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.94% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+math | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.38% | 11.62% | 2.36 | 7.00 |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.60 | 42.0 | 22.60% | 6.25% | 7.34% | 54.22% | 13.40% | 1.83 | 2.69 |
| safety+math | diagonal_sst_main | 0.60 | 43.0 | 15.85% | 6.41% | 7.19% | 80.62% | 31.23% | 1.84 | 2.79 |
| safety+math | diagonal_sst_main | 0.60 | 44.0 | 12.81% | 7.81% | 5.62% | 82.81% | 22.82% | 1.85 | 2.78 |
| safety+math | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 9.38% | 11.88% | 29.06% | 13.45% | 1.90 | 3.82 |
| safety+math | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 10.31% | 6.41% | 81.25% | 24.94% | 2.03 | 4.79 |
| safety+math | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 9.84% | 5.00% | 85.94% | 23.56% | 2.00 | 4.46 |


---

### メイン実験: Pattern = safety+code

#### 【集計】 メイン実験 (Mean ± Std) - safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.60 | 0.00 ± 0.00% | 0.05 ± 0.09% | 0.00 ± 0.00% | 29.58 ± 12.27% | 11.73 ± 0.70% | 202107.17 ± 205144.66 | 343746.27 ± 163477.65 |
| safety+code | dare | 1.00 | 0.00 ± 0.00% | 0.73 ± 0.50% | 5.21 ± 2.67% | 57.81 ± 22.81% | 21.54 ± 10.74% | 2.35 ± 0.04 | 7.07 ± 0.07 |
| safety+code | data_free_sst_main | 0.60 | 0.03 ± 0.05% | 0.21 ± 0.24% | 0.00 ± 0.00% | 78.75 ± 2.48% | 14.07 ± 0.05% | 218.68 ± 118.96 | 49.90 ± 16.95 |
| safety+code | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.05 ± 0.09% | 0.00 ± 0.00% | 28.85 ± 16.70% | 11.52 ± 0.25% | 17917.37 ± 18265.91 | 2247.19 ± 1603.28 |
| safety+code | della | 0.60 | 0.00 ± 0.00% | 0.62 ± 0.41% | 0.00 ± 0.00% | 43.54 ± 14.08% | 12.43 ± 0.46% | 107944.55 ± 59575.64 | 211408.90 ± 76715.67 |
| safety+code | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.72% | 4.43 ± 3.60% | 53.54 ± 27.30% | 11.04 ± 0.62% | 2.38 ± 0.04 | 7.38 ± 0.07 |
| safety+code | diagonal_sst_main | 0.60 | 0.97 ± 0.42% | 0.89 ± 0.24% | 0.00 ± 0.00% | 86.25 ± 0.31% | 12.26 ± 0.55% | 191.50 ± 74.10 | 31.40 ± 8.25 |
| safety+code | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 0.42 ± 0.24% | 0.00 ± 0.00% | 15.21 ± 0.95% | 10.63 ± 0.27% | 187.93 ± 30.20 | 249.26 ± 144.36 |
| safety+code | led_merging | N/A | 2.88 ± 0.14% | 1.41 ± 0.00% | 5.62 ± 0.00% | 83.75 ± 0.00% | 22.49 ± 0.04% | 1.75 ± 0.00 | 2.72 ± 0.00 |
| safety+code | matena_fisher | N/A | 3.37 ± 1.40% | 1.09 ± 0.00% | 0.00 ± 0.00% | 83.12 ± 0.31% | 12.77 ± 0.37% | 69.53 ± 21.34 | 84.66 ± 27.77 |
| safety+code | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 15.73 ± 3.41% | - | - |
| safety+code | safemerge | N/A | 0.10 ± 0.18% | 1.51 ± 1.33% | 5.99 ± 5.39% | 73.75 ± 2.98% | 19.84 ± 8.02% | 2.35 ± 0.78 | 7.03 ± 4.96 |
| safety+code | task_arithmetic | 0.60 | 29.17 ± 3.07% | 2.97 ± 0.68% | 4.63 ± 0.09% | 88.85 ± 0.79% | 17.39 ± 0.39% | 2.47 ± 0.01 | 4.84 ± 0.03 |
| safety+code | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.50% | 4.22 ± 3.39% | 58.02 ± 23.47% | 18.37 ± 12.03% | 2.34 ± 0.03 | 7.15 ± 0.13 |
| safety+code | ties | 0.60 | 0.11 ± 0.04% | 1.41 ± 0.47% | 0.00 ± 0.00% | 38.65 ± 26.32% | 17.85 ± 9.81% | 92.27 ± 111.77 | 25.62 ± 27.16 |
| safety+code | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 25.53 ± 16.91% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.60 | 42.0 | 32.56% | 3.28% | 4.53% | 89.69% | 17.60% | 2.47 | 4.80 |
| safety+code | task_arithmetic | 0.60 | 43.0 | 26.56% | 3.44% | 4.68% | 88.12% | 17.62% | 2.47 | 4.84 |
| safety+code | task_arithmetic | 0.60 | 44.0 | 28.39% | 2.19% | 4.68% | 88.75% | 16.93% | 2.48 | 4.87 |
| safety+code | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.38% | 32.26% | 2.31 | 7.26 |
| safety+code | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+code | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.38% | 11.62% | 2.36 | 7.00 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 31.25% | 11.10% | 84728.55 | 334537.08 |
| safety+code | dare | 0.60 | 43.0 | 0.00% | 0.16% | 0.00% | 16.56% | 11.60% | 82608.30 | 185067.88 |
| safety+code | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 40.94% | 12.48% | 438984.66 | 511633.87 |
| safety+code | dare | 1.00 | 42.0 | 0.00% | 0.94% | 8.28% | 84.06% | 32.23% | 2.30 | 7.08 |
| safety+code | dare | 1.00 | 43.0 | 0.00% | 1.09% | 3.44% | 42.81% | 10.74% | 2.37 | 7.13 |
| safety+code | dare | 1.00 | 44.0 | 0.00% | 0.16% | 3.91% | 46.56% | 21.65% | 2.37 | 6.99 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 42.0 | 4.96% | 1.09% | 0.00% | 83.44% | 12.87% | 47.93 | 54.86 |
| safety+code | matena_fisher | N/A | 43.0 | 2.85% | 1.09% | 0.00% | 82.81% | 13.07% | 70.07 | 89.29 |
| safety+code | matena_fisher | N/A | 44.0 | 2.31% | 1.09% | 0.00% | 83.12% | 12.36% | 90.59 | 109.82 |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.60 | 42.0 | 1.21% | 1.09% | 0.00% | 86.25% | 12.88% | 135.96 | 21.94 |
| safety+code | diagonal_sst_main | 0.60 | 43.0 | 1.20% | 0.94% | 0.00% | 85.94% | 11.85% | 275.64 | 35.11 |
| safety+code | diagonal_sst_main | 0.60 | 44.0 | 0.49% | 0.62% | 0.00% | 86.56% | 12.05% | 162.89 | 37.14 |
| safety+code | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.47% | 0.00% | 16.25% | 10.94% | 221.80 | 409.75 |
| safety+code | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 0.62% | 0.00% | 14.37% | 10.47% | 178.18 | 130.00 |
| safety+code | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 0.16% | 0.00% | 15.00% | 10.49% | 163.80 | 208.02 |


#### 【シード別詳細】 メイン実験 - Method: safemerge, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 42.0 | 0.31% | 2.50% | 7.03% | 75.62% | 27.76% | 1.75 | 2.87 |
| safety+code | safemerge | N/A | 43.0 | 0.00% | 2.03% | 10.78% | 70.31% | 20.03% | 2.06 | 5.72 |
| safety+code | safemerge | N/A | 44.0 | 0.00% | 0.00% | 0.16% | 75.31% | 11.72% | 3.23 | 12.51 |


#### 【シード別詳細】 メイン実験 - Method: led_merging, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 42.0 | 3.04% | 1.41% | 5.62% | 83.75% | 22.49% | 1.75 | 2.72 |
| safety+code | led_merging | N/A | 43.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.52% | 1.75 | 2.72 |
| safety+code | led_merging | N/A | 44.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.45% | 1.75 | 2.72 |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | della | 0.60 | 42.0 | 0.00% | 0.94% | 0.00% | 57.19% | 12.96% | 173731.57 | 126277.55 |
| safety+code | della | 0.60 | 43.0 | 0.00% | 0.16% | 0.00% | 29.06% | 12.10% | 92466.80 | 275182.68 |
| safety+code | della | 0.60 | 44.0 | 0.00% | 0.78% | 0.00% | 44.38% | 12.23% | 57635.29 | 232766.47 |
| safety+code | della | 1.00 | 42.0 | 0.00% | 1.41% | 8.12% | 84.69% | 11.16% | 2.34 | 7.41 |
| safety+code | della | 1.00 | 43.0 | 0.00% | 0.47% | 0.94% | 42.19% | 10.37% | 2.40 | 7.43 |
| safety+code | della | 1.00 | 44.0 | 0.00% | 0.00% | 4.22% | 33.75% | 11.59% | 2.40 | 7.29 |


#### 【シード別詳細】 メイン実験 - Method: mergealign, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |
| safety+code | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |
| safety+code | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | ties | 0.60 | 42.0 | 0.08% | 1.41% | 0.00% | 68.75% | 12.90% | 50.93 | 56.91 |
| safety+code | ties | 0.60 | 43.0 | 0.16% | 1.88% | 0.00% | 20.00% | 11.50% | 7.06 | 8.18 |
| safety+code | ties | 0.60 | 44.0 | 0.08% | 0.94% | 0.00% | 27.19% | 29.15% | 218.81 | 11.76 |
| safety+code | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 44.31% | 2.24 | 6.85 |
| safety+code | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.49% | 2.28 | 6.71 |
| safety+code | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 20.80% | 2.29 | 6.60 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.16% | 0.00% | 80.62% | 14.01% | 242.36 | 51.52 |
| safety+code | data_free_sst_main | 0.60 | 43.0 | 0.00% | 0.47% | 0.00% | 79.69% | 14.10% | 89.66 | 32.20 |
| safety+code | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 75.94% | 14.09% | 324.02 | 65.98 |
| safety+code | data_free_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 48.12% | 11.80% | 13963.92 | 2780.62 |
| safety+code | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.16% | 0.00% | 19.69% | 11.40% | 1951.94 | 445.19 |
| safety+code | data_free_sst_main | 1.00 | 44.0 | 0.08% | 0.00% | 0.00% | 18.75% | 11.35% | 37836.26 | 3515.76 |


---

### メイン実験: Pattern = safety+medical

#### 【集計】 メイン実験 (Mean ± Std) - safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 22.08 ± 10.81% | 12.39 ± 0.44% | 12863372.97 ± 9716067.34 | 13423154.39 ± 11060518.87 |
| safety+medical | dare | 1.00 | 0.00 ± 0.00% | 0.47 ± 0.56% | 4.38 ± 3.53% | 62.40 ± 23.88% | 23.44 ± 10.58% | 2.34 ± 0.04 | 7.13 ± 0.18 |
| safety+medical | data_free_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 61.67 ± 41.50% | 12.27 ± 0.07% | 151079.31 ± 79294.36 | 109978.81 ± 39827.45 |
| safety+medical | data_free_sst_main | 1.00 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 32.92 ± 46.61% | 11.96 ± 0.22% | 216810.71 ± 115193.54 | 136969.65 ± 56251.67 |
| safety+medical | della | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 27.29 ± 23.45% | 12.10 ± 1.01% | 10754022.73 ± 9470200.24 | 8631379.06 ± 4139779.72 |
| safety+medical | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.68% | 4.01 ± 3.43% | 56.56 ± 22.05% | 17.08 ± 10.75% | 2.38 ± 0.04 | 7.38 ± 0.14 |
| safety+medical | diagonal_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.69 ± 8.46% | 12.06 ± 0.13% | 75380.55 ± 8006.67 | 78424.43 ± 9712.01 |
| safety+medical | diagonal_sst_main | 1.00 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.25 ± 22.89% | 11.87 ± 0.98% | 138717.43 ± 145875.51 | 95092.19 ± 65045.99 |
| safety+medical | matena_fisher | N/A | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.99 ± 0.18% | 576870.77 ± 100574.92 | 439254.45 ± 88250.04 |
| safety+medical | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 13.76 ± 3.41% | - | - |
| safety+medical | safemerge | N/A | 0.03 ± 0.05% | 1.09 ± 1.89% | 3.91 ± 6.77% | 53.44 ± 10.84% | 12.81 ± 1.63% | 3.84 ± 1.84 | 15.66 ± 10.55 |
| safety+medical | task_arithmetic | 0.60 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.85 ± 0.18% | 12.72 ± 0.06% | 217753.69 ± 12313.53 | 198661.81 ± 12470.98 |
| safety+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.50% | 4.22 ± 3.39% | 58.02 ± 23.47% | 18.37 ± 12.03% | 2.34 ± 0.03 | 7.15 ± 0.13 |
| safety+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.54 ± 0.36% | 11.90 ± 0.62% | 34172.15 ± 4640.21 | 67899.54 ± 37744.22 |
| safety+medical | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 20.66 ± 9.09% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 メイン実験 - Method: safemerge, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 42.0 | 0.00% | 3.28% | 11.72% | 60.31% | 14.69% | 1.87 | 4.37 |
| safety+medical | safemerge | N/A | 43.0 | 0.08% | 0.00% | 0.00% | 40.94% | 11.81% | 5.53 | 25.25 |
| safety+medical | safemerge | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 59.06% | 11.93% | 4.11 | 17.37 |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 13.75% | 12.69% | 231670.29 | 211313.97 |
| safety+medical | task_arithmetic | 0.60 | 43.0 | 0.16% | 0.00% | 0.00% | 14.06% | 12.69% | 213319.17 | 186380.28 |
| safety+medical | task_arithmetic | 0.60 | 44.0 | 0.16% | 0.00% | 0.00% | 13.75% | 12.79% | 208271.62 | 198291.16 |
| safety+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.38% | 32.26% | 2.31 | 7.26 |
| safety+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.38% | 11.62% | 2.36 | 7.00 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 17.81% | 12.81% | 23273464.09 | 25783754.01 |
| safety+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 14.06% | 11.93% | 4035556.82 | 10026154.84 |
| safety+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 34.38% | 12.42% | 11281098.00 | 4459554.31 |
| safety+medical | dare | 1.00 | 42.0 | 0.00% | 1.09% | 8.44% | 84.69% | 30.19% | 2.30 | 7.33 |
| safety+medical | dare | 1.00 | 43.0 | 0.00% | 0.31% | 2.66% | 65.31% | 28.88% | 2.36 | 7.10 |
| safety+medical | dare | 1.00 | 44.0 | 0.00% | 0.00% | 2.03% | 37.19% | 11.24% | 2.37 | 6.97 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 42.0 | 0.16% | 0.00% | 0.00% | 0.00% | 13.09% | 691154.34 | 541088.28 |
| safety+medical | matena_fisher | N/A | 43.0 | 0.16% | 0.00% | 0.00% | 0.00% | 12.78% | 501847.06 | 385101.33 |
| safety+medical | matena_fisher | N/A | 44.0 | 0.16% | 0.00% | 0.00% | 0.00% | 13.09% | 537610.90 | 391573.73 |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.33% | 38946.69 | 110844.44 |
| safety+medical | ties | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 13.12% | 12.17% | 33890.70 | 39990.65 |
| safety+medical | ties | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 13.75% | 11.19% | 29679.08 | 52863.53 |
| safety+medical | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 29.68% | 2.24 | 6.85 |
| safety+medical | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.49% | 2.28 | 6.71 |
| safety+medical | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 20.80% | 2.29 | 6.60 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 85.00% | 12.19% | 204517.26 | 155544.43 |
| safety+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.31% | 59971.79 | 81805.58 |
| safety+medical | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.31% | 188748.87 | 92586.41 |
| safety+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.08% | 236077.90 | 149930.00 |
| safety+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 0.00% | 11.70% | 321155.77 | 185610.00 |
| safety+medical | data_free_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 12.50% | 12.09% | 93198.47 | 75368.95 |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.84% | 21562404.57 | 13042229.15 |
| safety+medical | della | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 54.37% | 12.52% | 6788182.90 | 4830310.81 |
| safety+medical | della | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 10.95% | 3911480.70 | 8021597.21 |
| safety+medical | della | 1.00 | 42.0 | 0.00% | 1.41% | 7.97% | 81.88% | 29.49% | 2.33 | 7.51 |
| safety+medical | della | 1.00 | 43.0 | 0.00% | 0.31% | 2.19% | 46.25% | 10.77% | 2.39 | 7.41 |
| safety+medical | della | 1.00 | 44.0 | 0.00% | 0.16% | 1.88% | 41.56% | 10.97% | 2.41 | 7.23 |


#### 【シード別詳細】 メイン実験 - Method: mergealign, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |
| safety+medical | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |
| safety+medical | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.44% | 11.91% | 72783.78 | 67362.99 |
| safety+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 0.00% | 12.16% | 84363.30 | 85554.10 |
| safety+medical | diagonal_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 15.62% | 12.11% | 68994.57 | 82356.19 |
| safety+medical | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 7.81% | 11.46% | 11982.52 | 20544.71 |
| safety+medical | diagonal_sst_main | 1.00 | 43.0 | 0.08% | 0.00% | 0.00% | 51.88% | 11.16% | 298175.26 | 140302.29 |
| safety+medical | diagonal_sst_main | 1.00 | 44.0 | 0.08% | 0.00% | 0.00% | 19.06% | 13.00% | 105994.50 | 124429.57 |


---

## 3. ベースモデル (Base Models) 実験結果
マージ前のベース・ドメインモデルおよび Safety FT モデルの結果独立一覧表。

#### 【集計】 ベースモデル評価 (Mean ± Std)

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 5.17 ± 0.00% | 4.53 ± 0.00% | 3.59 ± 0.00% | 52.81 ± 0.00% | 20.28 ± 0.00% | 2.32 ± 0.00 | 5.71 ± 2.88 |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 0.00 ± 0.00% | 0.52 ± 0.48% | 4.22 ± 3.39% | 43.49 ± 11.80% | 11.38 ± 0.41% | 2.34 ± 0.03 | - |
| Base (WizardCoder) | Base (WizardCoder) | N/A | 24.69 ± 0.00% | 4.53 ± 0.00% | 21.03 ± 0.00% | 54.53 ± 0.00% | 18.41 ± 0.00% | 1.54 ± 0.00 | 3.72 ± 0.00 |
| Base (WizardMath) | Base (WizardMath) | N/A | 31.01 ± 0.00% | 6.41 ± 0.00% | 3.12 ± 0.00% | 55.00 ± 0.00% | 14.02 ± 0.00% | 2.03 ± 0.00 | 2.77 ± 0.00 |


#### 【シード別詳細】 ベースモデル評価 (Seeds 42, 43, 44)

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 42.0 | - | - | - | - | - | - | 7.26 |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 43.0 | - | - | - | - | - | - | 7.18 |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 44.0 | - | - | - | - | - | - | 7.00 |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | nan | 5.17% | 4.53% | 3.59% | 52.81% | 20.28% | 2.32 | 1.40 |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 42.0 | 0.00% | 0.94% | 8.12% | 56.72% | 11.86% | 2.31 | - |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 43.0 | 0.00% | 0.62% | 2.03% | 39.69% | 11.13% | 2.36 | - |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 44.0 | 0.00% | 0.00% | 2.50% | 34.06% | 11.16% | 2.36 | - |
| Base (WizardCoder) | Base (WizardCoder) | N/A | nan | 24.69% | 4.53% | 21.03% | 54.53% | 18.41% | 1.54 | 3.72 |
| Base (WizardMath) | Base (WizardMath) | N/A | nan | 31.01% | 6.41% | 3.12% | 55.00% | 14.02% | 2.03 | 2.77 |


---

## 4. Alpha スイープ実験結果
各 Alpha パラメータごとの Safety / Utility スコア推移表。

### Alpha スイープ: Method = matena_fisher, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 0.00 ± 0.00% | 0.99 ± 0.24% | 0.00 ± 0.00% | 27.81 ± 3.29% | 13.12 ± 0.12% | 63.52 ± 2.39 | 128.84 ± 4.62 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 42.0 | 0.00% | 0.94% | 0.00% | 30.94% | 12.98% | 65.01 | 124.79 |
| safety+math+code+medical | matena_fisher | N/A | 43.0 | 0.00% | 0.78% | 0.00% | 28.12% | 13.15% | 60.76 | 127.88 |
| safety+math+code+medical | matena_fisher | N/A | 44.0 | 0.00% | 1.25% | 0.00% | 24.38% | 13.22% | 64.78 | 133.87 |


---

### Alpha スイープ: Method = matena_fisher, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 4.29 ± 0.43% | 6.04 ± 0.86% | 6.61 ± 0.39% | 85.73 ± 0.65% | 26.72 ± 11.70% | 1.82 ± 0.01 | 2.88 ± 0.02 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 42.0 | 4.71% | 6.09% | 6.25% | 85.00% | 39.12% | 1.81 | 2.90 |
| safety+math | matena_fisher | N/A | 43.0 | 4.30% | 5.16% | 7.03% | 86.25% | 15.87% | 1.83 | 2.86 |
| safety+math | matena_fisher | N/A | 44.0 | 3.85% | 6.88% | 6.56% | 85.94% | 25.17% | 1.84 | 2.88 |


---

### Alpha スイープ: Method = matena_fisher, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 3.37 ± 1.40% | 1.09 ± 0.00% | 0.00 ± 0.00% | 83.12 ± 0.31% | 12.77 ± 0.37% | 69.53 ± 21.34 | 84.66 ± 27.77 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 42.0 | 4.96% | 1.09% | 0.00% | 83.44% | 12.87% | 47.93 | 54.86 |
| safety+code | matena_fisher | N/A | 43.0 | 2.85% | 1.09% | 0.00% | 82.81% | 13.07% | 70.07 | 89.29 |
| safety+code | matena_fisher | N/A | 44.0 | 2.31% | 1.09% | 0.00% | 83.12% | 12.36% | 90.59 | 109.82 |


---

### Alpha スイープ: Method = matena_fisher, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.99 ± 0.18% | 576870.77 ± 100574.92 | 439254.45 ± 88250.04 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 42.0 | 0.16% | 0.00% | 0.00% | 0.00% | 13.09% | 691154.34 | 541088.28 |
| safety+medical | matena_fisher | N/A | 43.0 | 0.16% | 0.00% | 0.00% | 0.00% | 12.78% | 501847.06 | 385101.33 |
| safety+medical | matena_fisher | N/A | 44.0 | 0.16% | 0.00% | 0.00% | 0.00% | 13.09% | 537610.90 | 391573.73 |


---

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.19 ± 0.00% | 10.72 ± 0.06% | 48514.43 ± 0.00 | 60540.72 ± 0.00 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 0.05 ± 0.05% | 0.31 ± 0.54% | 0.00 ± 0.00% | 13.75 ± 0.00% | 12.21 ± 0.86% | 3890.44 ± 579.86 | 11358.40 ± 1880.12 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 0.00 ± 0.00% | 0.99 ± 0.36% | 0.00 ± 0.00% | 13.75 ± 0.00% | 11.72 ± 0.25% | 2876.79 ± 1018.70 | 2210.66 ± 378.54 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 0.00 ± 0.00% | 0.42 ± 0.18% | 0.00 ± 0.00% | 57.29 ± 17.67% | 10.16 ± 0.49% | 319.70 ± 69.81 | 139.54 ± 27.87 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 0.13 ± 0.05% | 0.36 ± 0.18% | 0.00 ± 0.00% | 82.81 ± 3.79% | 9.54 ± 0.92% | 119.22 ± 47.28 | 75.00 ± 24.40 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 0.16 ± 0.00% | 0.26 ± 0.24% | 0.00 ± 0.00% | 80.83 ± 8.57% | 11.10 ± 1.30% | 78.49 ± 39.87 | 78.49 ± 32.65 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 42.0 | 0.16% | 0.00% | 0.00% | 12.19% | 10.79% | 48514.43 | 60540.72 |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 43.0 | 0.16% | 0.00% | 0.00% | 12.19% | 10.68% | 48514.43 | 60540.72 |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 44.0 | 0.16% | 0.00% | 0.00% | 12.19% | 10.68% | 48514.43 | 60540.72 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 11.83% | 3837.57 | 11701.23 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 43.0 | 0.00% | 0.00% | 0.00% | 13.75% | 13.18% | 3338.82 | 9330.45 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 44.0 | 0.08% | 0.94% | 0.00% | 13.75% | 11.60% | 4494.92 | 13043.51 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 42.0 | 0.00% | 1.41% | 0.00% | 13.75% | 11.43% | 1839.14 | 2574.76 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 43.0 | 0.00% | 0.78% | 0.00% | 13.75% | 11.82% | 3875.43 | 2238.06 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 44.0 | 0.00% | 0.78% | 0.00% | 13.75% | 11.90% | 2915.80 | 1819.17 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 42.0 | 0.00% | 0.62% | 0.00% | 40.00% | 10.41% | 392.09 | 168.34 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.31% | 0.00% | 75.31% | 10.48% | 252.79 | 112.69 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 44.0 | 0.00% | 0.31% | 0.00% | 56.56% | 9.59% | 314.23 | 137.59 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 42.0 | 0.08% | 0.47% | 0.00% | 85.00% | 10.55% | 167.99 | 100.74 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 43.0 | 0.16% | 0.47% | 0.00% | 85.00% | 9.31% | 73.59 | 52.21 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 44.0 | 0.16% | 0.16% | 0.00% | 78.44% | 8.76% | 116.08 | 72.05 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 42.0 | 0.16% | 0.47% | 0.00% | 85.94% | 12.28% | 119.75 | 108.05 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 43.0 | 0.16% | 0.31% | 0.00% | 85.62% | 11.31% | 40.18 | 43.44 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 70.94% | 9.71% | 75.56 | 83.97 |


---

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.00 | 34.32 ± 0.20% | 6.04 ± 0.18% | 2.19 ± 0.00% | 63.44 ± 28.69% | 24.87 ± 9.33% | 1.99 ± 0.00 | 2.71 ± 0.00 |
| safety+math | diagonal_sst_main | 0.20 | 31.84 ± 1.33% | 6.46 ± 0.63% | 4.53 ± 0.83% | 62.71 ± 28.61% | 21.02 ± 10.84% | 1.91 ± 0.00 | 2.66 ± 0.01 |
| safety+math | diagonal_sst_main | 0.40 | 32.86 ± 2.20% | 6.20 ± 0.39% | 4.84 ± 0.68% | 71.61 ± 15.47% | 27.05 ± 11.87% | 1.86 ± 0.01 | 2.63 ± 0.02 |
| safety+math | diagonal_sst_main | 0.60 | 17.09 ± 5.01% | 6.82 ± 0.86% | 6.72 ± 0.95% | 72.55 ± 15.91% | 22.48 ± 8.92% | 1.84 ± 0.01 | 2.75 ± 0.05 |
| safety+math | diagonal_sst_main | 0.80 | 2.76 ± 1.73% | 8.44 ± 1.02% | 5.89 ± 2.13% | 73.02 ± 17.23% | 17.72 ± 6.02% | 1.88 ± 0.04 | 3.15 ± 0.15 |
| safety+math | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 9.84 ± 0.47% | 7.76 ± 3.63% | 65.42 ± 31.57% | 20.65 ± 6.27% | 1.98 ± 0.07 | 4.36 ± 0.49 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.00 | 42.0 | 34.43% | 5.94% | 2.19% | 30.31% | 14.70% | 1.99 | 2.71 |
| safety+math | diagonal_sst_main | 0.00 | 43.0 | 34.44% | 5.94% | 2.19% | 80.00% | 33.04% | 1.99 | 2.71 |
| safety+math | diagonal_sst_main | 0.00 | 44.0 | 34.10% | 6.25% | 2.19% | 80.00% | 26.88% | 1.99 | 2.71 |
| safety+math | diagonal_sst_main | 0.20 | 42.0 | 31.57% | 6.09% | 5.47% | 29.69% | 14.42% | 1.91 | 2.65 |
| safety+math | diagonal_sst_main | 0.20 | 43.0 | 33.28% | 6.09% | 4.22% | 78.44% | 15.12% | 1.91 | 2.66 |
| safety+math | diagonal_sst_main | 0.20 | 44.0 | 30.66% | 7.19% | 3.91% | 80.00% | 33.53% | 1.92 | 2.65 |
| safety+math | diagonal_sst_main | 0.40 | 42.0 | 34.17% | 6.25% | 4.06% | 53.91% | 13.80% | 1.85 | 2.60 |
| safety+math | diagonal_sst_main | 0.40 | 43.0 | 30.32% | 5.78% | 5.16% | 78.44% | 30.63% | 1.86 | 2.65 |
| safety+math | diagonal_sst_main | 0.40 | 44.0 | 34.11% | 6.56% | 5.31% | 82.50% | 36.72% | 1.86 | 2.64 |
| safety+math | diagonal_sst_main | 0.60 | 42.0 | 22.60% | 6.25% | 7.34% | 54.22% | 13.40% | 1.83 | 2.69 |
| safety+math | diagonal_sst_main | 0.60 | 43.0 | 15.85% | 6.41% | 7.19% | 80.62% | 31.23% | 1.84 | 2.79 |
| safety+math | diagonal_sst_main | 0.60 | 44.0 | 12.81% | 7.81% | 5.62% | 82.81% | 22.82% | 1.85 | 2.78 |
| safety+math | diagonal_sst_main | 0.80 | 42.0 | 3.99% | 7.50% | 6.88% | 53.12% | 13.76% | 1.83 | 2.97 |
| safety+math | diagonal_sst_main | 0.80 | 43.0 | 0.78% | 8.28% | 7.34% | 82.81% | 24.65% | 1.90 | 3.23 |
| safety+math | diagonal_sst_main | 0.80 | 44.0 | 3.52% | 9.53% | 3.44% | 83.12% | 14.76% | 1.90 | 3.24 |
| safety+math | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 9.38% | 11.88% | 29.06% | 13.45% | 1.90 | 3.82 |
| safety+math | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 10.31% | 6.41% | 81.25% | 24.94% | 2.03 | 4.79 |
| safety+math | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 9.84% | 5.00% | 85.94% | 23.56% | 2.00 | 4.46 |


---

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.00 | 0.08 ± 0.00% | 0.47 ± 0.00% | 0.00 ± 0.00% | 85.62 ± 0.00% | 13.66 ± 0.00% | 485.34 ± 0.00 | 92.12 ± 0.00 |
| safety+code | diagonal_sst_main | 0.20 | 0.08 ± 0.08% | 0.36 ± 0.18% | 0.00 ± 0.00% | 86.35 ± 0.18% | 13.66 ± 0.15% | 304.22 ± 54.14 | 58.85 ± 7.32 |
| safety+code | diagonal_sst_main | 0.40 | 0.32 ± 0.14% | 0.83 ± 0.63% | 0.00 ± 0.00% | 86.46 ± 0.18% | 13.44 ± 0.46% | 296.86 ± 96.53 | 42.89 ± 11.58 |
| safety+code | diagonal_sst_main | 0.60 | 0.97 ± 0.42% | 0.89 ± 0.24% | 0.00 ± 0.00% | 86.25 ± 0.31% | 12.26 ± 0.55% | 191.50 ± 74.10 | 31.40 ± 8.25 |
| safety+code | diagonal_sst_main | 0.80 | 0.82 ± 0.33% | 1.09 ± 0.41% | 0.00 ± 0.00% | 80.73 ± 3.96% | 11.67 ± 0.24% | 48.92 ± 16.08 | 26.83 ± 3.50 |
| safety+code | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 0.42 ± 0.24% | 0.00 ± 0.00% | 15.21 ± 0.95% | 10.63 ± 0.27% | 187.93 ± 30.20 | 249.26 ± 144.36 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.00 | 42.0 | 0.08% | 0.47% | 0.00% | 85.62% | 13.66% | 485.34 | 92.12 |
| safety+code | diagonal_sst_main | 0.00 | 43.0 | 0.08% | 0.47% | 0.00% | 85.62% | 13.66% | 485.34 | 92.12 |
| safety+code | diagonal_sst_main | 0.00 | 44.0 | 0.08% | 0.47% | 0.00% | 85.62% | 13.66% | 485.34 | 92.12 |
| safety+code | diagonal_sst_main | 0.20 | 42.0 | 0.08% | 0.47% | 0.00% | 86.56% | 13.49% | 259.22 | 51.06 |
| safety+code | diagonal_sst_main | 0.20 | 43.0 | 0.00% | 0.47% | 0.00% | 86.25% | 13.79% | 364.30 | 65.57 |
| safety+code | diagonal_sst_main | 0.20 | 44.0 | 0.16% | 0.16% | 0.00% | 86.25% | 13.72% | 289.15 | 59.92 |
| safety+code | diagonal_sst_main | 0.40 | 42.0 | 0.24% | 0.47% | 0.00% | 86.25% | 12.92% | 223.61 | 29.53 |
| safety+code | diagonal_sst_main | 0.40 | 43.0 | 0.24% | 1.56% | 0.00% | 86.56% | 13.65% | 406.24 | 49.45 |
| safety+code | diagonal_sst_main | 0.40 | 44.0 | 0.48% | 0.47% | 0.00% | 86.56% | 13.75% | 260.72 | 49.71 |
| safety+code | diagonal_sst_main | 0.60 | 42.0 | 1.21% | 1.09% | 0.00% | 86.25% | 12.88% | 135.96 | 21.94 |
| safety+code | diagonal_sst_main | 0.60 | 43.0 | 1.20% | 0.94% | 0.00% | 85.94% | 11.85% | 275.64 | 35.11 |
| safety+code | diagonal_sst_main | 0.60 | 44.0 | 0.49% | 0.62% | 0.00% | 86.56% | 12.05% | 162.89 | 37.14 |
| safety+code | diagonal_sst_main | 0.80 | 42.0 | 0.55% | 0.62% | 0.00% | 77.19% | 11.40% | 39.85 | 24.20 |
| safety+code | diagonal_sst_main | 0.80 | 43.0 | 0.71% | 1.41% | 0.00% | 80.00% | 11.86% | 67.49 | 25.49 |
| safety+code | diagonal_sst_main | 0.80 | 44.0 | 1.18% | 1.25% | 0.00% | 85.00% | 11.77% | 39.42 | 30.80 |
| safety+code | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.47% | 0.00% | 16.25% | 10.94% | 221.80 | 409.75 |
| safety+code | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 0.62% | 0.00% | 14.37% | 10.47% | 178.18 | 130.00 |
| safety+code | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 0.16% | 0.00% | 15.00% | 10.49% | 163.80 | 208.02 |


---

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.12 ± 0.00% | 12.06 ± 0.10% | 180460.88 ± 0.00 | 169745.34 ± 0.00 |
| safety+medical | diagonal_sst_main | 0.20 | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.75 ± 0.31% | 12.12 ± 0.08% | 94281.86 ± 26088.99 | 81185.07 ± 29847.41 |
| safety+medical | diagonal_sst_main | 0.40 | 0.19 ± 0.20% | 0.00 ± 0.00% | 0.00 ± 0.00% | 85.73 ± 0.65% | 12.13 ± 0.32% | 131598.61 ± 37516.58 | 83673.35 ± 23943.66 |
| safety+medical | diagonal_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.69 ± 8.46% | 12.06 ± 0.13% | 75380.55 ± 8006.67 | 78424.43 ± 9712.01 |
| safety+medical | diagonal_sst_main | 0.80 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.06 ± 7.04% | 11.83 ± 0.45% | 135732.82 ± 163601.13 | 175313.17 ± 210610.19 |
| safety+medical | diagonal_sst_main | 1.00 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.25 ± 22.89% | 11.87 ± 0.98% | 138717.43 ± 145875.51 | 95092.19 ± 65045.99 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 33.12% | 11.96% | 180460.88 | 169745.34 |
| safety+medical | diagonal_sst_main | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 33.12% | 12.06% | 180460.88 | 169745.34 |
| safety+medical | diagonal_sst_main | 0.00 | 44.0 | 0.00% | 0.00% | 0.00% | 33.12% | 12.17% | 180460.88 | 169745.34 |
| safety+medical | diagonal_sst_main | 0.20 | 42.0 | 0.16% | 0.00% | 0.00% | 13.75% | 12.21% | 122142.18 | 114130.75 |
| safety+medical | diagonal_sst_main | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 13.44% | 12.05% | 90275.76 | 73476.06 |
| safety+medical | diagonal_sst_main | 0.20 | 44.0 | 0.16% | 0.00% | 0.00% | 14.06% | 12.10% | 70427.63 | 55948.41 |
| safety+medical | diagonal_sst_main | 0.40 | 42.0 | 0.40% | 0.00% | 0.00% | 85.00% | 11.87% | 167508.43 | 99865.73 |
| safety+medical | diagonal_sst_main | 0.40 | 43.0 | 0.16% | 0.00% | 0.00% | 85.94% | 12.49% | 92659.00 | 56169.58 |
| safety+medical | diagonal_sst_main | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 12.03% | 134628.39 | 94984.74 |
| safety+medical | diagonal_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.44% | 11.91% | 72783.78 | 67362.99 |
| safety+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 0.00% | 12.16% | 84363.30 | 85554.10 |
| safety+medical | diagonal_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 15.62% | 12.11% | 68994.57 | 82356.19 |
| safety+medical | diagonal_sst_main | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 12.19% | 12.33% | 8763.53 | 20450.35 |
| safety+medical | diagonal_sst_main | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.47% | 320355.53 | 415132.33 |
| safety+medical | diagonal_sst_main | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.68% | 78079.41 | 90356.82 |
| safety+medical | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 7.81% | 11.46% | 11982.52 | 20544.71 |
| safety+medical | diagonal_sst_main | 1.00 | 43.0 | 0.08% | 0.00% | 0.00% | 51.88% | 11.16% | 298175.26 | 140302.29 |
| safety+medical | diagonal_sst_main | 1.00 | 44.0 | 0.08% | 0.00% | 0.00% | 19.06% | 13.00% | 105994.50 | 124429.57 |


---

### Alpha スイープ: Method = dare, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.00 | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.15 ± 45.29% | 11.63 ± 0.34% | 6818688.18 ± 7065619.14 | 7378650.47 ± 4295362.07 |
| safety+math+code+medical | dare | 0.20 | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 11.98 ± 7.81% | 12.06 ± 0.50% | 7173662.71 ± 2942125.13 | 6687130.41 ± 3055033.24 |
| safety+math+code+medical | dare | 0.40 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.75 ± 0.00% | 12.07 ± 0.90% | 6979776.99 ± 6033524.78 | 2986909.55 ± 2662560.22 |
| safety+math+code+medical | dare | 0.60 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 38.02 ± 41.77% | 11.53 ± 0.23% | 5368837.19 ± 6493560.14 | 6550135.45 ± 3035748.48 |
| safety+math+code+medical | dare | 0.80 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 29.58 ± 48.81% | 12.30 ± 0.47% | 953765.09 ± 912212.52 | 828217.06 ± 375799.63 |
| safety+math+code+medical | dare | 1.00 | 0.00 ± 0.00% | 0.68 ± 0.70% | 5.36 ± 2.13% | 55.83 ± 25.27% | 17.94 ± 12.11% | 2.35 ± 0.03 | 7.15 ± 0.10 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.00 | 42.0 | 0.16% | 0.00% | 0.00% | 0.00% | 12.02% | 14730567.06 | 12336031.02 |
| safety+math+code+medical | dare | 0.00 | 43.0 | 0.08% | 0.00% | 0.00% | 78.44% | 11.39% | 1138044.95 | 4764244.25 |
| safety+math+code+medical | dare | 0.00 | 44.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.47% | 4587452.52 | 5035676.13 |
| safety+math+code+medical | dare | 0.20 | 42.0 | 0.16% | 0.00% | 0.00% | 13.75% | 12.58% | 4799372.95 | 3193735.46 |
| safety+math+code+medical | dare | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 3.44% | 12.02% | 6256487.91 | 8009125.74 |
| safety+math+code+medical | dare | 0.20 | 44.0 | 0.16% | 0.00% | 0.00% | 18.75% | 11.58% | 10465127.28 | 8858530.02 |
| safety+math+code+medical | dare | 0.40 | 42.0 | 0.00% | 0.00% | 0.00% | 13.75% | 11.19% | 12369089.71 | 5828590.40 |
| safety+math+code+medical | dare | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 13.75% | 12.99% | 8108718.76 | 2582368.48 |
| safety+math+code+medical | dare | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.03% | 461522.51 | 549769.77 |
| safety+math+code+medical | dare | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 86.25% | 11.42% | 12857479.52 | 10037855.54 |
| safety+math+code+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 14.06% | 11.38% | 1950859.88 | 4501931.51 |
| safety+math+code+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 11.79% | 1298172.17 | 5110619.29 |
| safety+math+code+medical | dare | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 2.19% | 12.80% | 2005704.45 | 1261537.06 |
| safety+math+code+medical | dare | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 85.94% | 12.21% | 380898.02 | 591539.57 |
| safety+math+code+medical | dare | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 0.62% | 11.89% | 474692.80 | 631574.56 |
| safety+math+code+medical | dare | 1.00 | 42.0 | 0.00% | 1.41% | 7.81% | 84.06% | 31.92% | 2.31 | 7.26 |
| safety+math+code+medical | dare | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 48.12% | 10.60% | 2.36 | 7.08 |
| safety+math+code+medical | dare | 1.00 | 44.0 | 0.00% | 0.00% | 4.38% | 35.31% | 11.30% | 2.37 | 7.10 |


---

### Alpha スイープ: Method = dare, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.00 | 33.14 ± 0.78% | 5.47 ± 0.47% | 3.33 ± 0.59% | 79.79 ± 0.79% | 30.41 ± 4.79% | 2.02 ± 0.00 | 2.77 ± 0.00 |
| safety+math | dare | 0.20 | 10.27 ± 1.33% | 4.79 ± 1.13% | 4.64 ± 1.26% | 84.27 ± 0.79% | 28.15 ± 5.63% | 2.36 ± 0.04 | 3.61 ± 0.05 |
| safety+math | dare | 0.40 | 9.09 ± 1.71% | 5.36 ± 0.65% | 4.95 ± 0.65% | 85.00 ± 0.54% | 23.52 ± 2.16% | 2.38 ± 0.05 | 3.85 ± 0.08 |
| safety+math | dare | 0.60 | 6.14 ± 5.14% | 5.42 ± 0.79% | 5.00 ± 1.02% | 84.27 ± 2.35% | 22.85 ± 8.57% | 2.43 ± 0.07 | 4.44 ± 0.28 |
| safety+math | dare | 0.80 | 3.59 ± 4.78% | 6.35 ± 0.70% | 5.68 ± 1.04% | 85.52 ± 1.00% | 12.79 ± 0.68% | 2.47 ± 0.07 | 5.66 ± 0.26 |
| safety+math | dare | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.63% | 5.68 ± 3.61% | 55.94 ± 25.88% | 11.22 ± 0.57% | 2.35 ± 0.03 | 7.18 ± 0.22 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.00 | 42.0 | 32.72% | 5.94% | 2.66% | 80.62% | 34.49% | 2.02 | 2.77 |
| safety+math | dare | 0.00 | 43.0 | 32.67% | 5.00% | 3.75% | 79.69% | 25.14% | 2.03 | 2.77 |
| safety+math | dare | 0.00 | 44.0 | 34.05% | 5.47% | 3.59% | 79.06% | 31.59% | 2.02 | 2.76 |
| safety+math | dare | 0.20 | 42.0 | 11.64% | 4.06% | 4.84% | 84.38% | 34.65% | 2.32 | 3.57 |
| safety+math | dare | 0.20 | 43.0 | 10.17% | 4.22% | 5.78% | 83.44% | 24.94% | 2.37 | 3.60 |
| safety+math | dare | 0.20 | 44.0 | 8.99% | 6.09% | 3.28% | 85.00% | 24.86% | 2.40 | 3.66 |
| safety+math | dare | 0.40 | 42.0 | 11.06% | 5.16% | 5.16% | 85.31% | 21.61% | 2.32 | 3.78 |
| safety+math | dare | 0.40 | 43.0 | 8.32% | 4.84% | 5.47% | 84.38% | 25.86% | 2.39 | 3.84 |
| safety+math | dare | 0.40 | 44.0 | 7.90% | 6.09% | 4.22% | 85.31% | 23.09% | 2.42 | 3.94 |
| safety+math | dare | 0.60 | 42.0 | 0.32% | 6.25% | 5.16% | 84.38% | 15.04% | 2.35 | 4.18 |
| safety+math | dare | 0.60 | 43.0 | 8.06% | 4.69% | 5.94% | 81.88% | 21.51% | 2.46 | 4.40 |
| safety+math | dare | 0.60 | 44.0 | 10.04% | 5.31% | 3.91% | 86.56% | 32.02% | 2.48 | 4.73 |
| safety+math | dare | 0.80 | 42.0 | 0.00% | 7.03% | 5.94% | 84.38% | 13.56% | 2.40 | 5.37 |
| safety+math | dare | 0.80 | 43.0 | 9.02% | 6.41% | 6.56% | 85.94% | 12.26% | 2.51 | 5.86 |
| safety+math | dare | 0.80 | 44.0 | 1.74% | 5.62% | 4.53% | 86.25% | 12.55% | 2.52 | 5.75 |
| safety+math | dare | 1.00 | 42.0 | 0.00% | 1.25% | 9.06% | 85.62% | 11.49% | 2.32 | 7.37 |
| safety+math | dare | 1.00 | 43.0 | 0.00% | 0.47% | 1.88% | 44.06% | 10.56% | 2.37 | 7.23 |
| safety+math | dare | 1.00 | 44.0 | 0.00% | 0.00% | 6.09% | 38.12% | 11.61% | 2.36 | 6.93 |


---

### Alpha スイープ: Method = dare, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.00 | 0.05 ± 0.09% | 0.10 ± 0.09% | 0.00 ± 0.00% | 26.77 ± 13.01% | 11.60 ± 0.87% | 879426.80 ± 305130.82 | 609083.49 ± 167433.25 |
| safety+code | dare | 0.20 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 25.21 ± 1.60% | 12.05 ± 0.25% | 421186.26 ± 138822.67 | 559487.26 ± 208077.06 |
| safety+code | dare | 0.40 | 0.03 ± 0.05% | 0.05 ± 0.09% | 0.00 ± 0.00% | 34.69 ± 36.57% | 12.05 ± 0.65% | 274915.81 ± 142634.75 | 546472.43 ± 179293.80 |
| safety+code | dare | 0.60 | 0.00 ± 0.00% | 0.05 ± 0.09% | 0.00 ± 0.00% | 29.58 ± 12.27% | 11.73 ± 0.70% | 202107.17 ± 205144.66 | 343746.27 ± 163477.65 |
| safety+code | dare | 0.80 | 0.00 ± 0.00% | 0.16 ± 0.16% | 0.00 ± 0.00% | 25.31 ± 16.83% | 11.58 ± 0.96% | 183440.18 ± 68554.99 | 437650.47 ± 213227.25 |
| safety+code | dare | 1.00 | 0.00 ± 0.00% | 0.73 ± 0.50% | 5.21 ± 2.67% | 57.81 ± 22.81% | 21.54 ± 10.74% | 2.35 ± 0.04 | 7.07 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.00 | 42.0 | 0.00% | 0.16% | 0.00% | 40.31% | 12.14% | 1187511.19 | 491920.23 |
| safety+code | dare | 0.00 | 43.0 | 0.00% | 0.16% | 0.00% | 25.62% | 12.07% | 577337.91 | 800850.96 |
| safety+code | dare | 0.00 | 44.0 | 0.16% | 0.00% | 0.00% | 14.37% | 10.60% | 873431.29 | 534479.27 |
| safety+code | dare | 0.20 | 42.0 | 0.00% | 0.00% | 0.00% | 25.62% | 12.32% | 386759.01 | 457123.94 |
| safety+code | dare | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 23.44% | 11.83% | 573983.09 | 798917.10 |
| safety+code | dare | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 26.56% | 11.99% | 302816.67 | 422420.74 |
| safety+code | dare | 0.40 | 42.0 | 0.08% | 0.00% | 0.00% | 9.06% | 11.80% | 403013.26 | 566389.97 |
| safety+code | dare | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 76.56% | 12.80% | 300521.74 | 714975.79 |
| safety+code | dare | 0.40 | 44.0 | 0.00% | 0.16% | 0.00% | 18.44% | 11.57% | 121212.45 | 358051.52 |
| safety+code | dare | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 31.25% | 11.10% | 84728.55 | 334537.08 |
| safety+code | dare | 0.60 | 43.0 | 0.00% | 0.16% | 0.00% | 16.56% | 11.60% | 82608.30 | 185067.88 |
| safety+code | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 40.94% | 12.48% | 438984.66 | 511633.87 |
| safety+code | dare | 0.80 | 42.0 | 0.00% | 0.16% | 0.00% | 14.37% | 10.78% | 139942.12 | 559428.50 |
| safety+code | dare | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 44.69% | 12.64% | 262466.83 | 562081.29 |
| safety+code | dare | 0.80 | 44.0 | 0.00% | 0.31% | 0.00% | 16.88% | 11.32% | 147911.59 | 191441.61 |
| safety+code | dare | 1.00 | 42.0 | 0.00% | 0.94% | 8.28% | 84.06% | 32.23% | 2.30 | 7.08 |
| safety+code | dare | 1.00 | 43.0 | 0.00% | 1.09% | 3.44% | 42.81% | 10.74% | 2.37 | 7.13 |
| safety+code | dare | 1.00 | 44.0 | 0.00% | 0.16% | 3.91% | 46.56% | 21.65% | 2.37 | 6.99 |


---

### Alpha スイープ: Method = dare, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.00 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 51.98 ± 35.56% | 12.48 ± 0.41% | 25893511.35 ± 8569831.17 | 21157726.46 ± 5807072.10 |
| safety+medical | dare | 0.20 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 4.69 ± 6.53% | 12.69 ± 1.18% | 30069390.20 ± 19622450.50 | 62005630.52 ± 57668015.31 |
| safety+medical | dare | 0.40 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.19 ± 11.49% | 11.56 ± 0.21% | 30373008.34 ± 42093120.51 | 137500579.89 ± 224029054.92 |
| safety+medical | dare | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 22.08 ± 10.81% | 12.39 ± 0.44% | 12863372.97 ± 9716067.34 | 13423154.39 ± 11060518.87 |
| safety+medical | dare | 0.80 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.56 ± 16.59% | 11.94 ± 0.18% | 79051784.95 ± 108121693.22 | 73992085.11 ± 102576019.23 |
| safety+medical | dare | 1.00 | 0.00 ± 0.00% | 0.47 ± 0.56% | 4.38 ± 3.53% | 62.40 ± 23.88% | 23.44 ± 10.58% | 2.34 ± 0.04 | 7.13 ± 0.18 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.00 | 42.0 | 0.08% | 0.00% | 0.00% | 58.13% | 12.29% | 31609289.83 | 20636305.98 |
| safety+medical | dare | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 84.06% | 12.20% | 30031293.17 | 15628948.22 |
| safety+medical | dare | 0.00 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 12.94% | 16039951.05 | 27207925.18 |
| safety+medical | dare | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 12.19% | 11.93% | 7413500.08 | 13387384.99 |
| safety+medical | dare | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 1.56% | 14.06% | 41668528.86 | 125720332.10 |
| safety+medical | dare | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 0.31% | 12.10% | 41126141.66 | 46909174.49 |
| safety+medical | dare | 0.40 | 42.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.35% | 4591460.66 | 6233091.27 |
| safety+medical | dare | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 13.75% | 11.57% | 7580247.55 | 10091188.42 |
| safety+medical | dare | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 22.81% | 11.77% | 78947316.81 | 396177459.98 |
| safety+medical | dare | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 17.81% | 12.81% | 23273464.09 | 25783754.01 |
| safety+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 14.06% | 11.93% | 4035556.82 | 10026154.84 |
| safety+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 34.38% | 12.42% | 11281098.00 | 4459554.31 |
| safety+medical | dare | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 1.56% | 12.13% | 28606774.28 | 15417965.64 |
| safety+medical | dare | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 13.75% | 11.91% | 5371427.76 | 14123976.08 |
| safety+medical | dare | 0.80 | 44.0 | 0.16% | 0.00% | 0.00% | 34.38% | 11.78% | 203177152.83 | 192434313.61 |
| safety+medical | dare | 1.00 | 42.0 | 0.00% | 1.09% | 8.44% | 84.69% | 30.19% | 2.30 | 7.33 |
| safety+medical | dare | 1.00 | 43.0 | 0.00% | 0.31% | 2.66% | 65.31% | 28.88% | 2.36 | 7.10 |
| safety+medical | dare | 1.00 | 44.0 | 0.00% | 0.00% | 2.03% | 37.19% | 11.24% | 2.37 | 6.97 |


---

### Alpha スイープ: Method = della, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.00 | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 46.25 ± 43.46% | 12.13 ± 0.12% | 4511054.09 ± 4014528.21 | 2709873.15 ± 1621650.35 |
| safety+math+code+medical | della | 0.20 | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 44.79 ± 35.50% | 11.56 ± 0.35% | 5166971.66 ± 3651027.91 | 9317429.43 ± 6260181.15 |
| safety+math+code+medical | della | 0.40 | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 41.46 ± 38.91% | 12.38 ± 0.49% | 3796940.54 ± 1902635.09 | 2718893.17 ± 2050580.37 |
| safety+math+code+medical | della | 0.60 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 15.42 ± 16.18% | 12.53 ± 0.78% | 1556853.48 ± 450599.15 | 2115706.72 ± 117978.22 |
| safety+math+code+medical | della | 0.80 | 0.05 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 65.52 ± 18.69% | 11.74 ± 0.15% | 4357578.11 ± 3708292.54 | 4314491.46 ± 4478659.77 |
| safety+math+code+medical | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.31% | 4.58 ± 3.10% | 57.60 ± 23.98% | 18.90 ± 12.88% | 2.39 ± 0.04 | 7.38 ± 0.06 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.00 | 42.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.99% | 1076322.47 | 1937178.27 |
| safety+math+code+medical | della | 0.00 | 43.0 | 0.16% | 0.00% | 0.00% | 52.50% | 12.22% | 3532422.73 | 1619075.77 |
| safety+math+code+medical | della | 0.00 | 44.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.17% | 8924417.07 | 4573365.42 |
| safety+math+code+medical | della | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 85.62% | 11.95% | 3367617.78 | 9340200.62 |
| safety+math+code+medical | della | 0.20 | 43.0 | 0.16% | 0.00% | 0.00% | 27.50% | 11.25% | 2764868.94 | 3045893.75 |
| safety+math+code+medical | della | 0.20 | 44.0 | 0.08% | 0.00% | 0.00% | 21.25% | 11.48% | 9368428.27 | 15566193.92 |
| safety+math+code+medical | della | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 13.75% | 11.83% | 5819408.74 | 5081745.67 |
| safety+math+code+medical | della | 0.40 | 43.0 | 0.16% | 0.00% | 0.00% | 85.94% | 12.52% | 2042579.89 | 1404892.78 |
| safety+math+code+medical | della | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 24.69% | 12.78% | 3528832.98 | 1670041.07 |
| safety+math+code+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.44% | 11.64% | 1547222.80 | 1979585.04 |
| safety+math+code+medical | della | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 0.31% | 12.97% | 1111146.86 | 2188460.85 |
| safety+math+code+medical | della | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 32.50% | 13.00% | 2012190.77 | 2179074.27 |
| safety+math+code+medical | della | 0.80 | 42.0 | 0.16% | 0.00% | 0.00% | 81.56% | 11.58% | 5216210.59 | 9270274.79 |
| safety+math+code+medical | della | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 70.00% | 11.75% | 7561235.35 | 3116659.19 |
| safety+math+code+medical | della | 0.80 | 44.0 | 0.00% | 0.00% | 0.00% | 45.00% | 11.89% | 295288.40 | 556540.40 |
| safety+math+code+medical | della | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.69% | 33.77% | 2.34 | 7.44 |
| safety+math+code+medical | della | 1.00 | 43.0 | 0.00% | 0.62% | 2.34% | 49.06% | 11.21% | 2.41 | 7.34 |
| safety+math+code+medical | della | 1.00 | 44.0 | 0.00% | 0.31% | 3.28% | 39.06% | 11.72% | 2.42 | 7.35 |


---

### Alpha スイープ: Method = della, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | della | 0.00 | 33.26 ± 0.87% | 6.56 ± 0.16% | 3.33 ± 0.59% | 83.44 ± 1.74% | 34.20 ± 1.62% | 2.04 ± 0.00 | 2.78 ± 0.02 |
| safety+math | della | 0.20 | 11.63 ± 0.83% | 5.57 ± 0.89% | 4.64 ± 0.24% | 83.23 ± 1.18% | 32.96 ± 2.11% | 2.38 ± 0.04 | 3.70 ± 0.07 |
| safety+math | della | 0.40 | 7.61 ± 2.70% | 5.52 ± 0.09% | 5.31 ± 0.68% | 84.58 ± 2.03% | 32.47 ± 2.15% | 2.41 ± 0.05 | 3.93 ± 0.10 |
| safety+math | della | 0.60 | 6.66 ± 5.52% | 5.52 ± 0.63% | 5.31 ± 1.36% | 85.62 ± 0.54% | 31.03 ± 4.06% | 2.46 ± 0.06 | 4.50 ± 0.30 |
| safety+math | della | 0.80 | 2.71 ± 3.71% | 5.78 ± 1.08% | 4.90 ± 0.39% | 85.52 ± 0.79% | 19.17 ± 5.48% | 2.51 ± 0.09 | 5.81 ± 0.42 |
| safety+math | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.41% | 4.69 ± 3.29% | 58.54 ± 23.27% | 17.78 ± 11.72% | 2.38 ± 0.03 | 7.33 ± 0.14 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | della | 0.00 | 42.0 | 34.22% | 6.72% | 3.59% | 81.88% | 34.10% | 2.05 | 2.80 |
| safety+math | della | 0.00 | 43.0 | 32.52% | 6.56% | 3.75% | 83.12% | 35.87% | 2.05 | 2.76 |
| safety+math | della | 0.00 | 44.0 | 33.04% | 6.41% | 2.66% | 85.31% | 32.63% | 2.04 | 2.78 |
| safety+math | della | 0.20 | 42.0 | 10.84% | 4.84% | 4.84% | 84.06% | 31.09% | 2.34 | 3.66 |
| safety+math | della | 0.20 | 43.0 | 12.50% | 5.31% | 4.38% | 81.88% | 35.25% | 2.39 | 3.67 |
| safety+math | della | 0.20 | 44.0 | 11.53% | 6.56% | 4.69% | 83.75% | 32.54% | 2.41 | 3.78 |
| safety+math | della | 0.40 | 42.0 | 10.66% | 5.47% | 6.09% | 84.69% | 31.22% | 2.35 | 3.83 |
| safety+math | della | 0.40 | 43.0 | 5.56% | 5.62% | 5.00% | 82.50% | 34.96% | 2.41 | 3.91 |
| safety+math | della | 0.40 | 44.0 | 6.61% | 5.47% | 4.84% | 86.56% | 31.25% | 2.46 | 4.04 |
| safety+math | della | 0.60 | 42.0 | 0.63% | 4.84% | 6.25% | 85.31% | 29.00% | 2.39 | 4.26 |
| safety+math | della | 0.60 | 43.0 | 11.45% | 5.62% | 5.94% | 85.31% | 28.39% | 2.47 | 4.41 |
| safety+math | della | 0.60 | 44.0 | 7.92% | 6.09% | 3.75% | 86.25% | 35.70% | 2.51 | 4.84 |
| safety+math | della | 0.80 | 42.0 | 0.00% | 7.03% | 4.84% | 84.69% | 23.57% | 2.42 | 5.34 |
| safety+math | della | 0.80 | 43.0 | 6.94% | 5.16% | 5.31% | 85.62% | 20.90% | 2.54 | 5.98 |
| safety+math | della | 0.80 | 44.0 | 1.19% | 5.16% | 4.53% | 86.25% | 13.03% | 2.58 | 6.12 |
| safety+math | della | 1.00 | 42.0 | 0.00% | 0.78% | 7.81% | 85.00% | 31.29% | 2.35 | 7.45 |
| safety+math | della | 1.00 | 43.0 | 0.00% | 0.94% | 1.25% | 49.38% | 10.38% | 2.41 | 7.37 |
| safety+math | della | 1.00 | 44.0 | 0.00% | 0.16% | 5.00% | 41.25% | 11.68% | 2.40 | 7.17 |


---

### Alpha スイープ: Method = della, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | della | 0.00 | 0.00 ± 0.00% | 0.05 ± 0.09% | 0.00 ± 0.00% | 41.04 ± 10.74% | 11.94 ± 0.59% | 569125.61 ± 394534.46 | 1151826.80 ± 842498.02 |
| safety+code | della | 0.20 | 0.00 ± 0.00% | 0.52 ± 0.33% | 0.00 ± 0.00% | 22.08 ± 3.31% | 11.43 ± 0.95% | 212820.11 ± 119967.94 | 320482.73 ± 211524.60 |
| safety+code | della | 0.40 | 0.05 ± 0.05% | 0.05 ± 0.09% | 0.00 ± 0.00% | 21.15 ± 10.37% | 11.39 ± 0.22% | 199062.51 ± 165620.73 | 394587.54 ± 221751.31 |
| safety+code | della | 0.60 | 0.00 ± 0.00% | 0.62 ± 0.41% | 0.00 ± 0.00% | 43.54 ± 14.08% | 12.43 ± 0.46% | 107944.55 ± 59575.64 | 211408.90 ± 76715.67 |
| safety+code | della | 0.80 | 0.05 ± 0.09% | 0.62 ± 0.83% | 0.00 ± 0.00% | 35.10 ± 27.13% | 12.00 ± 0.78% | 63830.50 ± 29959.41 | 217419.43 ± 83074.00 |
| safety+code | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.72% | 4.43 ± 3.60% | 53.54 ± 27.30% | 11.04 ± 0.62% | 2.38 ± 0.04 | 7.38 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | della | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 35.00% | 11.85% | 318866.94 | 1074126.52 |
| safety+code | della | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 53.44% | 11.40% | 364580.27 | 350870.46 |
| safety+code | della | 0.00 | 44.0 | 0.00% | 0.16% | 0.00% | 34.69% | 12.56% | 1023929.61 | 2030483.41 |
| safety+code | della | 0.20 | 42.0 | 0.00% | 0.62% | 0.00% | 25.62% | 12.29% | 284396.34 | 501382.55 |
| safety+code | della | 0.20 | 43.0 | 0.00% | 0.78% | 0.00% | 19.06% | 10.42% | 74319.10 | 87909.29 |
| safety+code | della | 0.20 | 44.0 | 0.00% | 0.16% | 0.00% | 21.56% | 11.58% | 279744.90 | 372156.36 |
| safety+code | della | 0.40 | 42.0 | 0.08% | 0.00% | 0.00% | 12.19% | 11.65% | 386282.25 | 378643.94 |
| safety+code | della | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 18.75% | 11.26% | 139243.22 | 623880.35 |
| safety+code | della | 0.40 | 44.0 | 0.08% | 0.16% | 0.00% | 32.50% | 11.28% | 71662.06 | 181238.32 |
| safety+code | della | 0.60 | 42.0 | 0.00% | 0.94% | 0.00% | 57.19% | 12.96% | 173731.57 | 126277.55 |
| safety+code | della | 0.60 | 43.0 | 0.00% | 0.16% | 0.00% | 29.06% | 12.10% | 92466.80 | 275182.68 |
| safety+code | della | 0.60 | 44.0 | 0.00% | 0.78% | 0.00% | 44.38% | 12.23% | 57635.29 | 232766.47 |
| safety+code | della | 0.80 | 42.0 | 0.16% | 1.56% | 0.00% | 13.75% | 12.58% | 52116.52 | 262634.90 |
| safety+code | della | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 65.62% | 12.30% | 41497.89 | 121545.33 |
| safety+code | della | 0.80 | 44.0 | 0.00% | 0.31% | 0.00% | 25.94% | 11.12% | 97877.08 | 268078.07 |
| safety+code | della | 1.00 | 42.0 | 0.00% | 1.41% | 8.12% | 84.69% | 11.16% | 2.34 | 7.41 |
| safety+code | della | 1.00 | 43.0 | 0.00% | 0.47% | 0.94% | 42.19% | 10.37% | 2.40 | 7.43 |
| safety+code | della | 1.00 | 44.0 | 0.00% | 0.00% | 4.22% | 33.75% | 11.59% | 2.40 | 7.29 |


---

### Alpha スイープ: Method = della, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | della | 0.00 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 74.90 ± 18.85% | 12.24 ± 0.24% | 26812751.49 ± 26729427.27 | 43518202.81 ± 44548820.85 |
| safety+medical | della | 0.20 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.94 ± 37.89% | 11.96 ± 0.91% | 7535389.77 ± 3979386.81 | 9534444.12 ± 6845498.98 |
| safety+medical | della | 0.40 | 0.05 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.23 ± 16.24% | 12.48 ± 0.36% | 24905029231.27 ± 43111038373.55 | 2796226504.59 ± 4644885775.60 |
| safety+medical | della | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 27.29 ± 23.45% | 12.10 ± 1.01% | 10754022.73 ± 9470200.24 | 8631379.06 ± 4139779.72 |
| safety+medical | della | 0.80 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.08 ± 16.20% | 12.07 ± 0.80% | 40599833.68 ± 51603645.67 | 33461048.41 ± 46722626.90 |
| safety+medical | della | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.68% | 4.01 ± 3.43% | 56.56 ± 22.05% | 17.08 ± 10.75% | 2.38 ± 0.04 | 7.38 ± 0.14 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | della | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 85.62% | 12.22% | 10500490.26 | 26900946.82 |
| safety+medical | della | 0.00 | 43.0 | 0.08% | 0.00% | 0.00% | 53.12% | 12.02% | 12277586.79 | 9666451.99 |
| safety+medical | della | 0.00 | 44.0 | 0.16% | 0.00% | 0.00% | 85.94% | 12.50% | 57660177.40 | 93987209.62 |
| safety+medical | della | 0.20 | 42.0 | 0.00% | 0.00% | 0.00% | 13.75% | 11.12% | 7593960.41 | 16608425.88 |
| safety+medical | della | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 14.37% | 11.83% | 3527040.92 | 2942957.72 |
| safety+medical | della | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 79.69% | 12.94% | 11485167.97 | 9051948.75 |
| safety+medical | della | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 5.62% | 12.29% | 15375847.04 | 223089326.53 |
| safety+medical | della | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 12.50% | 12.89% | 74685368447.73 | 8158232207.05 |
| safety+medical | della | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 36.56% | 12.25% | 14343399.05 | 7357980.19 |
| safety+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.84% | 21562404.57 | 13042229.15 |
| safety+medical | della | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 54.37% | 12.52% | 6788182.90 | 4830310.81 |
| safety+medical | della | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 10.95% | 3911480.70 | 8021597.21 |
| safety+medical | della | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 34.69% | 12.60% | 6850838.62 | 6993248.65 |
| safety+medical | della | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 2.81% | 12.45% | 100003030.30 | 87408527.68 |
| safety+medical | della | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 13.75% | 11.15% | 14945632.14 | 5981368.91 |
| safety+medical | della | 1.00 | 42.0 | 0.00% | 1.41% | 7.97% | 81.88% | 29.49% | 2.33 | 7.51 |
| safety+medical | della | 1.00 | 43.0 | 0.00% | 0.31% | 2.19% | 46.25% | 10.77% | 2.39 | 7.41 |
| safety+medical | della | 1.00 | 44.0 | 0.00% | 0.16% | 1.88% | 41.56% | 10.97% | 2.41 | 7.23 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.00 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.19 ± 0.00% | 10.65 ± 0.12% | 48514.43 ± 0.00 | 60540.72 ± 0.00 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 0.13 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.62 ± 0.83% | 11.32 ± 0.24% | 23973.29 ± 1724.29 | 42451.04 ± 921.18 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 6.25 ± 6.25% | 12.00 ± 0.20% | 12564.36 ± 2806.77 | 25747.98 ± 3655.02 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.67 ± 24.56% | 11.85 ± 0.59% | 8840.75 ± 1530.06 | 17110.70 ± 5533.52 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.71 ± 27.97% | 12.37 ± 1.27% | 6526.30 ± 426.62 | 7716.72 ± 2112.88 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 62.40 ± 27.79% | 11.48 ± 0.20% | 6377.05 ± 1134.31 | 5459.66 ± 490.26 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.00 | 42.0 | 0.16% | 0.00% | 0.00% | 12.19% | 10.79% | 48514.43 | 60540.72 |
| safety+math+code+medical | data_free_sst_main | 0.00 | 43.0 | 0.16% | 0.00% | 0.00% | 12.19% | 10.58% | 48514.43 | 60540.72 |
| safety+math+code+medical | data_free_sst_main | 0.00 | 44.0 | 0.16% | 0.00% | 0.00% | 12.19% | 10.58% | 48514.43 | 60540.72 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 1.56% | 11.07% | 24088.01 | 43085.80 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.55% | 22194.51 | 41394.49 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 44.0 | 0.24% | 0.00% | 0.00% | 0.31% | 11.35% | 25637.36 | 42872.84 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 42.0 | 0.00% | 0.00% | 0.00% | 6.25% | 12.00% | 12708.72 | 29794.72 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 0.00% | 11.80% | 9688.20 | 22686.80 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 12.50% | 12.20% | 15296.16 | 24762.41 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.44% | 12.53% | 8906.95 | 19263.61 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 11.56% | 11.50% | 7278.66 | 10824.29 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 55.00% | 11.51% | 10336.63 | 21244.18 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 30.00% | 13.79% | 6338.87 | 8330.75 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 57.19% | 11.99% | 7014.55 | 5364.83 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 44.0 | 0.00% | 0.00% | 0.00% | 85.94% | 11.34% | 6225.47 | 9454.56 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 31.87% | 11.30% | 7255.67 | 4971.49 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 69.06% | 11.69% | 6778.98 | 5455.51 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.44% | 5096.50 | 5951.99 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.00 | 34.32 ± 0.20% | 5.99 ± 0.09% | 2.92 ± 1.26% | 63.44 ± 28.69% | 30.93 ± 7.17% | 1.99 ± 0.00 | 2.71 ± 0.00 |
| safety+math | data_free_sst_main | 0.20 | 32.36 ± 0.85% | 3.96 ± 2.07% | 4.84 ± 2.30% | 70.57 ± 14.22% | 27.02 ± 6.95% | 1.99 ± 0.01 | 2.72 ± 0.01 |
| safety+math | data_free_sst_main | 0.40 | 35.94 ± 4.77% | 5.26 ± 0.18% | 6.04 ± 3.16% | 62.60 ± 28.36% | 28.39 ± 3.75% | 1.99 ± 0.01 | 2.80 ± 0.02 |
| safety+math | data_free_sst_main | 0.60 | 14.73 ± 3.41% | 5.57 ± 0.24% | 7.19 ± 4.33% | 69.38 ± 13.52% | 24.69 ± 0.38% | 2.02 ± 0.02 | 3.02 ± 0.02 |
| safety+math | data_free_sst_main | 0.80 | 15.59 ± 6.01% | 4.90 ± 0.86% | 5.62 ± 0.83% | 66.72 ± 13.56% | 26.05 ± 4.68% | 2.08 ± 0.03 | 3.55 ± 0.03 |
| safety+math | data_free_sst_main | 1.00 | 11.49 ± 9.25% | 5.89 ± 0.79% | 5.57 ± 0.24% | 56.77 ± 26.43% | 21.14 ± 7.66% | 2.19 ± 0.04 | 4.64 ± 0.10 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.00 | 42.0 | 34.43% | 6.09% | 4.38% | 30.31% | 39.21% | 1.99 | 2.71 |
| safety+math | data_free_sst_main | 0.00 | 43.0 | 34.10% | 5.94% | 2.19% | 80.00% | 26.72% | 1.99 | 2.71 |
| safety+math | data_free_sst_main | 0.00 | 44.0 | 34.44% | 5.94% | 2.19% | 80.00% | 26.88% | 1.99 | 2.71 |
| safety+math | data_free_sst_main | 0.20 | 42.0 | 33.03% | 1.56% | 7.50% | 54.22% | 26.52% | 1.98 | 2.71 |
| safety+math | data_free_sst_main | 0.20 | 43.0 | 32.65% | 5.16% | 3.44% | 77.50% | 34.21% | 1.99 | 2.73 |
| safety+math | data_free_sst_main | 0.20 | 44.0 | 31.41% | 5.16% | 3.59% | 80.00% | 20.33% | 1.99 | 2.73 |
| safety+math | data_free_sst_main | 0.40 | 42.0 | 41.42% | 5.16% | 9.69% | 30.00% | 26.62% | 1.98 | 2.78 |
| safety+math | data_free_sst_main | 0.40 | 43.0 | 32.71% | 5.16% | 4.06% | 76.25% | 25.86% | 2.00 | 2.79 |
| safety+math | data_free_sst_main | 0.40 | 44.0 | 33.70% | 5.47% | 4.38% | 81.56% | 32.70% | 2.00 | 2.82 |
| safety+math | data_free_sst_main | 0.60 | 42.0 | 10.89% | 5.31% | 12.19% | 54.06% | 24.30% | 1.99 | 3.03 |
| safety+math | data_free_sst_main | 0.60 | 43.0 | 15.92% | 5.78% | 4.84% | 74.38% | 25.07% | 2.02 | 3.04 |
| safety+math | data_free_sst_main | 0.60 | 44.0 | 17.39% | 5.62% | 4.53% | 79.69% | 24.70% | 2.04 | 3.00 |
| safety+math | data_free_sst_main | 0.80 | 42.0 | 9.86% | 4.06% | 6.56% | 51.41% | 31.46% | 2.05 | 3.55 |
| safety+math | data_free_sst_main | 0.80 | 43.0 | 15.06% | 5.78% | 5.00% | 71.56% | 23.39% | 2.10 | 3.51 |
| safety+math | data_free_sst_main | 0.80 | 44.0 | 21.85% | 4.84% | 5.31% | 77.19% | 23.31% | 2.10 | 3.58 |
| safety+math | data_free_sst_main | 1.00 | 42.0 | 0.95% | 5.78% | 5.31% | 28.75% | 13.26% | 2.14 | 4.52 |
| safety+math | data_free_sst_main | 1.00 | 43.0 | 18.26% | 6.72% | 5.78% | 60.31% | 28.55% | 2.23 | 4.71 |
| safety+math | data_free_sst_main | 1.00 | 44.0 | 15.26% | 5.16% | 5.62% | 81.25% | 21.63% | 2.21 | 4.69 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.00 | 0.08 ± 0.00% | 0.47 ± 0.00% | 0.00 ± 0.00% | 85.62 ± 0.00% | 13.66 ± 0.00% | 485.34 ± 0.00 | 92.12 ± 0.00 |
| safety+code | data_free_sst_main | 0.20 | 0.11 ± 0.05% | 0.16 ± 0.16% | 0.00 ± 0.00% | 85.31 ± 0.31% | 14.51 ± 0.44% | 212.97 ± 44.66 | 58.31 ± 7.72 |
| safety+code | data_free_sst_main | 0.40 | 0.11 ± 0.12% | 0.26 ± 0.09% | 0.00 ± 0.00% | 84.58 ± 1.54% | 14.96 ± 0.67% | 169.43 ± 64.63 | 42.87 ± 9.41 |
| safety+code | data_free_sst_main | 0.60 | 0.03 ± 0.05% | 0.21 ± 0.24% | 0.00 ± 0.00% | 78.75 ± 2.48% | 14.07 ± 0.05% | 218.68 ± 118.96 | 49.90 ± 16.95 |
| safety+code | data_free_sst_main | 0.80 | 0.16 ± 0.00% | 0.10 ± 0.18% | 0.00 ± 0.00% | 45.10 ± 25.39% | 12.36 ± 0.57% | 655.72 ± 450.39 | 86.62 ± 36.46 |
| safety+code | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.05 ± 0.09% | 0.00 ± 0.00% | 28.85 ± 16.70% | 11.52 ± 0.25% | 17917.37 ± 18265.91 | 2247.19 ± 1603.28 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.00 | 42.0 | 0.08% | 0.47% | 0.00% | 85.62% | 13.66% | 485.34 | 92.12 |
| safety+code | data_free_sst_main | 0.00 | 43.0 | 0.08% | 0.47% | 0.00% | 85.62% | 13.66% | 485.34 | 92.12 |
| safety+code | data_free_sst_main | 0.00 | 44.0 | 0.08% | 0.47% | 0.00% | 85.62% | 13.66% | 485.34 | 92.12 |
| safety+code | data_free_sst_main | 0.20 | 42.0 | 0.16% | 0.16% | 0.00% | 85.31% | 14.42% | 232.91 | 62.23 |
| safety+code | data_free_sst_main | 0.20 | 43.0 | 0.08% | 0.31% | 0.00% | 85.00% | 14.98% | 161.81 | 49.42 |
| safety+code | data_free_sst_main | 0.20 | 44.0 | 0.08% | 0.00% | 0.00% | 85.62% | 14.11% | 244.18 | 63.29 |
| safety+code | data_free_sst_main | 0.40 | 42.0 | 0.24% | 0.31% | 0.00% | 85.31% | 14.90% | 185.82 | 44.47 |
| safety+code | data_free_sst_main | 0.40 | 43.0 | 0.00% | 0.31% | 0.00% | 85.62% | 15.66% | 98.18 | 32.76 |
| safety+code | data_free_sst_main | 0.40 | 44.0 | 0.08% | 0.16% | 0.00% | 82.81% | 14.33% | 224.29 | 51.37 |
| safety+code | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.16% | 0.00% | 80.62% | 14.01% | 242.36 | 51.52 |
| safety+code | data_free_sst_main | 0.60 | 43.0 | 0.00% | 0.47% | 0.00% | 79.69% | 14.10% | 89.66 | 32.20 |
| safety+code | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 75.94% | 14.09% | 324.02 | 65.98 |
| safety+code | data_free_sst_main | 0.80 | 42.0 | 0.16% | 0.31% | 0.00% | 74.38% | 12.32% | 765.73 | 99.80 |
| safety+code | data_free_sst_main | 0.80 | 43.0 | 0.16% | 0.00% | 0.00% | 31.87% | 12.94% | 160.52 | 45.39 |
| safety+code | data_free_sst_main | 0.80 | 44.0 | 0.16% | 0.00% | 0.00% | 29.06% | 11.81% | 1040.92 | 114.66 |
| safety+code | data_free_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 48.12% | 11.80% | 13963.92 | 2780.62 |
| safety+code | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.16% | 0.00% | 19.69% | 11.40% | 1951.94 | 445.19 |
| safety+code | data_free_sst_main | 1.00 | 44.0 | 0.08% | 0.00% | 0.00% | 18.75% | 11.35% | 37836.26 | 3515.76 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.12 ± 0.00% | 11.96 ± 0.00% | 180460.88 ± 0.00 | 169745.34 ± 0.00 |
| safety+medical | data_free_sst_main | 0.20 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 5.21 ± 2.08% | 12.28 ± 0.36% | 113972.41 ± 22681.65 | 111551.09 ± 21075.97 |
| safety+medical | data_free_sst_main | 0.40 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.19 ± 3.25% | 12.32 ± 0.16% | 394226.76 ± 76513.96 | 337185.90 ± 108739.79 |
| safety+medical | data_free_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 61.67 ± 41.50% | 12.27 ± 0.07% | 151079.31 ± 79294.36 | 109978.81 ± 39827.45 |
| safety+medical | data_free_sst_main | 0.80 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.33 ± 36.09% | 12.20 ± 0.19% | 289568.91 ± 204175.94 | 207896.66 ± 114822.64 |
| safety+medical | data_free_sst_main | 1.00 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 32.92 ± 46.61% | 11.96 ± 0.22% | 216810.71 ± 115193.54 | 136969.65 ± 56251.67 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 33.12% | 11.96% | 180460.88 | 169745.34 |
| safety+medical | data_free_sst_main | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 33.12% | 11.96% | 180460.88 | 169745.34 |
| safety+medical | data_free_sst_main | 0.00 | 44.0 | 0.00% | 0.00% | 0.00% | 33.12% | 11.96% | 180460.88 | 169745.34 |
| safety+medical | data_free_sst_main | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 2.81% | 12.13% | 101883.66 | 104052.93 |
| safety+medical | data_free_sst_main | 0.20 | 43.0 | 0.00% | 0.00% | 0.00% | 6.56% | 12.02% | 140137.76 | 135350.85 |
| safety+medical | data_free_sst_main | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 6.25% | 12.69% | 99895.80 | 95249.49 |
| safety+medical | data_free_sst_main | 0.40 | 42.0 | 0.00% | 0.00% | 0.00% | 15.31% | 12.18% | 358476.58 | 297114.47 |
| safety+medical | data_free_sst_main | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 20.94% | 12.50% | 342131.65 | 254167.97 |
| safety+medical | data_free_sst_main | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 15.31% | 12.28% | 482072.05 | 460275.25 |
| safety+medical | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 85.00% | 12.19% | 204517.26 | 155544.43 |
| safety+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.31% | 59971.79 | 81805.58 |
| safety+medical | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.31% | 188748.87 | 92586.41 |
| safety+medical | data_free_sst_main | 0.80 | 42.0 | 0.08% | 0.00% | 0.00% | 85.62% | 12.17% | 480668.00 | 282960.57 |
| safety+medical | data_free_sst_main | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 60.00% | 12.41% | 313596.40 | 265012.97 |
| safety+medical | data_free_sst_main | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 14.37% | 12.04% | 74442.33 | 75716.42 |
| safety+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.08% | 236077.90 | 149930.00 |
| safety+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 0.00% | 11.70% | 321155.77 | 185610.00 |
| safety+medical | data_free_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 12.50% | 12.09% | 93198.47 | 75368.95 |


---

### Alpha スイープ: Method = ties, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.00 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 12.08 ± 0.01% | 134267.95 ± 0.28 | 134579.80 ± 2.53 |
| safety+math+code+medical | ties | 0.20 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 59.06 ± 39.50% | 11.81 ± 0.28% | 139662.16 ± 65366.01 | 150322.27 ± 64163.22 |
| safety+math+code+medical | ties | 0.40 | 0.19 ± 0.20% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.17 ± 7.94% | 12.13 ± 0.37% | 190495.65 ± 180185.46 | 222176.96 ± 171671.63 |
| safety+math+code+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 9.17 ± 7.94% | 12.28 ± 0.40% | 233905.82 ± 257072.89 | 291983.62 ± 249888.17 |
| safety+math+code+medical | ties | 0.80 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 8.33 ± 7.32% | 12.11 ± 0.20% | 280553.60 ± 223670.62 | 354731.01 ± 243640.54 |
| safety+math+code+medical | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 23.30 ± 18.12% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.00 | 42.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.08% | 134268.11 | 134581.26 |
| safety+math+code+medical | ties | 0.00 | 43.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.08% | 134268.11 | 134581.26 |
| safety+math+code+medical | ties | 0.00 | 44.0 | 0.08% | 0.00% | 0.00% | 86.25% | 12.09% | 134267.62 | 134576.88 |
| safety+math+code+medical | ties | 0.20 | 42.0 | 0.00% | 0.00% | 0.00% | 13.75% | 11.66% | 159431.75 | 190523.81 |
| safety+math+code+medical | ties | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 77.19% | 12.14% | 192861.34 | 184117.66 |
| safety+math+code+medical | ties | 0.20 | 44.0 | 0.08% | 0.00% | 0.00% | 86.25% | 11.64% | 66693.39 | 76325.34 |
| safety+math+code+medical | ties | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 13.75% | 12.55% | 133674.30 | 203744.50 |
| safety+math+code+medical | ties | 0.40 | 43.0 | 0.40% | 0.00% | 0.00% | 0.00% | 11.81% | 392242.12 | 402321.05 |
| safety+math+code+medical | ties | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 12.04% | 45570.53 | 60465.34 |
| safety+math+code+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.22% | 104380.52 | 193731.31 |
| safety+math+code+medical | ties | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 0.00% | 11.91% | 529977.51 | 576065.00 |
| safety+math+code+medical | ties | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 13.75% | 12.71% | 67359.44 | 106154.54 |
| safety+math+code+medical | ties | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 13.75% | 12.34% | 233513.07 | 283549.01 |
| safety+math+code+medical | ties | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 0.00% | 12.02% | 524003.26 | 626034.88 |
| safety+math+code+medical | ties | 0.80 | 44.0 | 0.16% | 0.00% | 0.00% | 11.25% | 11.98% | 84144.48 | 154609.14 |
| safety+math+code+medical | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 44.16% | 2.24 | 6.85 |
| safety+math+code+medical | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.49% | 2.28 | 6.71 |
| safety+math+code+medical | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 14.25% | 2.29 | 6.60 |


---

### Alpha スイープ: Method = ties, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | ties | 0.00 | 31.30 ± 0.05% | 7.40 ± 0.09% | 3.75 ± 1.62% | 60.52 ± 26.70% | 13.70 ± 0.00% | 1.89 ± 0.00 | 2.66 ± 0.00 |
| safety+math | ties | 0.20 | 14.19 ± 0.72% | 5.31 ± 0.87% | 5.21 ± 0.33% | 74.69 ± 14.92% | 24.94 ± 0.55% | 2.15 ± 0.03 | 3.33 ± 0.03 |
| safety+math | ties | 0.40 | 14.47 ± 1.19% | 5.21 ± 0.59% | 7.03 ± 3.16% | 65.42 ± 31.27% | 30.17 ± 4.44% | 2.12 ± 0.03 | 3.27 ± 0.04 |
| safety+math | ties | 0.60 | 9.03 ± 5.55% | 5.94 ± 0.83% | 6.15 ± 0.18% | 85.00 ± 2.44% | 27.65 ± 3.07% | 2.15 ± 0.05 | 3.57 ± 0.10 |
| safety+math | ties | 0.80 | 0.50 ± 0.48% | 6.46 ± 0.63% | 6.04 ± 1.10% | 84.58 ± 1.72% | 23.87 ± 3.82% | 2.25 ± 0.05 | 5.22 ± 0.22 |
| safety+math | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 25.52 ± 16.78% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | ties | 0.00 | 42.0 | 31.33% | 7.34% | 5.62% | 29.69% | 13.70% | 1.89 | 2.66 |
| safety+math | ties | 0.00 | 43.0 | 31.25% | 7.50% | 2.81% | 75.94% | 13.70% | 1.89 | 2.66 |
| safety+math | ties | 0.00 | 44.0 | 31.33% | 7.34% | 2.81% | 75.94% | 13.70% | 1.89 | 2.66 |
| safety+math | ties | 0.20 | 42.0 | 13.61% | 6.09% | 5.31% | 57.50% | 24.63% | 2.12 | 3.30 |
| safety+math | ties | 0.20 | 43.0 | 14.99% | 4.38% | 5.47% | 82.19% | 25.57% | 2.16 | 3.33 |
| safety+math | ties | 0.20 | 44.0 | 13.96% | 5.47% | 4.84% | 84.38% | 24.63% | 2.18 | 3.36 |
| safety+math | ties | 0.40 | 42.0 | 15.71% | 5.62% | 10.62% | 29.38% | 32.20% | 2.08 | 3.22 |
| safety+math | ties | 0.40 | 43.0 | 14.36% | 4.53% | 5.78% | 81.56% | 33.23% | 2.12 | 3.29 |
| safety+math | ties | 0.40 | 44.0 | 13.33% | 5.47% | 4.69% | 85.31% | 25.09% | 2.15 | 3.29 |
| safety+math | ties | 0.60 | 42.0 | 3.28% | 6.88% | 6.25% | 86.25% | 24.12% | 2.10 | 3.46 |
| safety+math | ties | 0.60 | 43.0 | 9.45% | 5.62% | 6.25% | 82.19% | 29.17% | 2.16 | 3.61 |
| safety+math | ties | 0.60 | 44.0 | 14.36% | 5.31% | 5.94% | 86.56% | 29.67% | 2.19 | 3.64 |
| safety+math | ties | 0.80 | 42.0 | 0.00% | 7.03% | 5.94% | 83.44% | 20.92% | 2.19 | 4.97 |
| safety+math | ties | 0.80 | 43.0 | 0.55% | 6.56% | 7.19% | 83.75% | 22.51% | 2.28 | 5.30 |
| safety+math | ties | 0.80 | 44.0 | 0.95% | 5.78% | 5.00% | 86.56% | 28.18% | 2.29 | 5.39 |
| safety+math | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 44.14% | 2.24 | 6.85 |
| safety+math | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.60% | 2.28 | 6.71 |
| safety+math | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 20.81% | 2.29 | 6.60 |


---

### Alpha スイープ: Method = ties, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | ties | 0.00 | 10.34 ± 0.10% | 2.50 ± 0.00% | 0.62 ± 0.00% | 86.56 ± 0.00% | 13.24 ± 0.00% | 2.68 ± 0.00 | 6.03 ± 0.00 |
| safety+code | ties | 0.20 | 3.02 ± 0.49% | 1.46 ± 0.18% | 0.00 ± 0.00% | 85.94 ± 0.31% | 12.56 ± 0.68% | 3.55 ± 0.73 | 5.44 ± 0.07 |
| safety+code | ties | 0.40 | 0.45 ± 0.58% | 1.35 ± 0.63% | 0.00 ± 0.00% | 67.71 ± 3.28% | 10.78 ± 0.35% | 16.24 ± 18.56 | 6.48 ± 0.64 |
| safety+code | ties | 0.60 | 0.11 ± 0.04% | 1.41 ± 0.47% | 0.00 ± 0.00% | 38.65 ± 26.32% | 17.85 ± 9.81% | 92.27 ± 111.77 | 25.62 ± 27.16 |
| safety+code | ties | 0.80 | 0.05 ± 0.05% | 0.78 ± 0.56% | 0.00 ± 0.00% | 12.81 ± 8.94% | 12.81 ± 1.06% | 1354.25 ± 2165.78 | 2116.56 ± 3620.28 |
| safety+code | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 25.53 ± 16.91% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | ties | 0.00 | 42.0 | 10.28% | 2.50% | 0.62% | 86.56% | 13.24% | 2.68 | 6.03 |
| safety+code | ties | 0.00 | 43.0 | 10.28% | 2.50% | 0.62% | 86.56% | 13.24% | 2.68 | 6.03 |
| safety+code | ties | 0.00 | 44.0 | 10.45% | 2.50% | 0.62% | 86.56% | 13.24% | 2.68 | 6.03 |
| safety+code | ties | 0.20 | 42.0 | 2.47% | 1.56% | 0.00% | 86.25% | 12.19% | 3.11 | 5.41 |
| safety+code | ties | 0.20 | 43.0 | 3.20% | 1.25% | 0.00% | 85.62% | 13.34% | 3.15 | 5.52 |
| safety+code | ties | 0.20 | 44.0 | 3.39% | 1.56% | 0.00% | 85.94% | 12.16% | 4.40 | 5.40 |
| safety+code | ties | 0.40 | 42.0 | 0.16% | 1.25% | 0.00% | 70.94% | 10.81% | 6.50 | 6.71 |
| safety+code | ties | 0.40 | 43.0 | 1.12% | 2.03% | 0.00% | 67.81% | 11.12% | 4.58 | 5.75 |
| safety+code | ties | 0.40 | 44.0 | 0.08% | 0.78% | 0.00% | 64.38% | 10.42% | 37.64 | 6.97 |
| safety+code | ties | 0.60 | 42.0 | 0.08% | 1.41% | 0.00% | 68.75% | 12.90% | 50.93 | 56.91 |
| safety+code | ties | 0.60 | 43.0 | 0.16% | 1.88% | 0.00% | 20.00% | 11.50% | 7.06 | 8.18 |
| safety+code | ties | 0.60 | 44.0 | 0.08% | 0.94% | 0.00% | 27.19% | 29.15% | 218.81 | 11.76 |
| safety+code | ties | 0.80 | 42.0 | 0.08% | 0.16% | 0.00% | 3.44% | 13.26% | 3853.46 | 6296.90 |
| safety+code | ties | 0.80 | 43.0 | 0.00% | 1.25% | 0.00% | 21.25% | 11.59% | 26.80 | 26.44 |
| safety+code | ties | 0.80 | 44.0 | 0.08% | 0.94% | 0.00% | 13.75% | 13.56% | 182.49 | 26.33 |
| safety+code | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 44.31% | 2.24 | 6.85 |
| safety+code | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.49% | 2.28 | 6.71 |
| safety+code | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 20.80% | 2.29 | 6.60 |


---

### Alpha スイープ: Method = ties, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | ties | 0.00 | 0.00 ± 0.00% | 2.34 ± 0.00% | 0.00 ± 0.00% | 13.75 ± 0.00% | 11.55 ± 0.03% | 8427.82 ± 0.00 | 6968.47 ± 0.00 |
| safety+medical | ties | 0.20 | 0.03 ± 0.05% | 1.15 ± 0.59% | 0.00 ± 0.00% | 13.75 ± 0.00% | 11.88 ± 0.42% | 12826.73 ± 2284.91 | 13573.24 ± 2241.89 |
| safety+medical | ties | 0.40 | 0.03 ± 0.05% | 0.36 ± 0.63% | 0.00 ± 0.00% | 15.31 ± 2.71% | 11.41 ± 1.01% | 20326.44 ± 7253.14 | 32101.20 ± 15400.20 |
| safety+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.54 ± 0.36% | 11.90 ± 0.62% | 34172.15 ± 4640.21 | 67899.54 ± 37744.22 |
| safety+medical | ties | 0.80 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 6.56 ± 9.29% | 12.17 ± 0.10% | 156974.41 ± 33655.73 | 233639.31 ± 108235.37 |
| safety+medical | ties | 1.00 | 0.00 ± 0.00% | 0.94 ± 0.68% | 6.56 ± 2.46% | 54.58 ± 25.92% | 20.66 ± 9.09% | 2.27 ± 0.03 | 6.72 ± 0.13 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | ties | 0.00 | 42.0 | 0.00% | 2.34% | 0.00% | 13.75% | 11.57% | 8427.82 | 6968.47 |
| safety+medical | ties | 0.00 | 43.0 | 0.00% | 2.34% | 0.00% | 13.75% | 11.51% | 8427.82 | 6968.47 |
| safety+medical | ties | 0.00 | 44.0 | 0.00% | 2.34% | 0.00% | 13.75% | 11.57% | 8427.82 | 6968.47 |
| safety+medical | ties | 0.20 | 42.0 | 0.08% | 1.56% | 0.00% | 13.75% | 11.45% | 11240.27 | 15921.75 |
| safety+medical | ties | 0.20 | 43.0 | 0.00% | 0.47% | 0.00% | 13.75% | 12.30% | 15445.67 | 13342.07 |
| safety+medical | ties | 0.20 | 44.0 | 0.00% | 1.41% | 0.00% | 13.75% | 11.89% | 11794.26 | 11455.89 |
| safety+medical | ties | 0.40 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 11.62% | 22070.37 | 25072.92 |
| safety+medical | ties | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 18.44% | 12.30% | 12360.33 | 21469.02 |
| safety+medical | ties | 0.40 | 44.0 | 0.00% | 1.09% | 0.00% | 13.75% | 10.31% | 26548.64 | 49761.67 |
| safety+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 13.75% | 12.33% | 38946.69 | 110844.44 |
| safety+medical | ties | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 13.12% | 12.17% | 33890.70 | 39990.65 |
| safety+medical | ties | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 13.75% | 11.19% | 29679.08 | 52863.53 |
| safety+medical | ties | 0.80 | 42.0 | 0.16% | 0.00% | 0.00% | 17.19% | 12.13% | 150880.93 | 348299.91 |
| safety+medical | ties | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 2.50% | 12.10% | 193260.59 | 133243.89 |
| safety+medical | ties | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 0.00% | 12.29% | 126781.72 | 219374.13 |
| safety+medical | ties | 1.00 | 42.0 | 0.00% | 1.72% | 8.75% | 84.38% | 29.68% | 2.24 | 6.85 |
| safety+medical | ties | 1.00 | 43.0 | 0.00% | 0.62% | 3.91% | 37.19% | 11.49% | 2.28 | 6.71 |
| safety+medical | ties | 1.00 | 44.0 | 0.00% | 0.47% | 7.03% | 42.19% | 20.80% | 2.29 | 6.60 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.00 | 0.08 ± 0.00% | 0.16 ± 0.00% | 0.00 ± 0.00% | 13.75 ± 0.00% | 11.52 ± 0.00% | 7640.62 ± 0.01 | 11830.82 ± 0.00 |
| safety+math+code+medical | task_arithmetic | 0.20 | 0.00 ± 0.00% | 1.46 ± 0.18% | 0.00 ± 0.00% | 50.00 ± 0.83% | 12.08 ± 0.08% | 1978.16 ± 28.43 | 3345.46 ± 56.12 |
| safety+math+code+medical | task_arithmetic | 0.40 | 0.00 ± 0.00% | 0.42 ± 0.33% | 0.00 ± 0.00% | 17.92 ± 0.79% | 15.20 ± 0.48% | 72.44 ± 8.63 | 48.65 ± 1.89 |
| safety+math+code+medical | task_arithmetic | 0.60 | 5.88 ± 0.55% | 2.55 ± 0.39% | 0.05 ± 0.09% | 65.42 ± 9.24% | 13.26 ± 1.65% | 3.22 ± 0.04 | 6.16 ± 0.11 |
| safety+math+code+medical | task_arithmetic | 0.80 | 1.24 ± 1.63% | 3.54 ± 0.59% | 5.10 ± 1.19% | 23.96 ± 2.95% | 19.60 ± 4.30% | 2.23 ± 0.02 | 5.44 ± 0.10 |
| safety+math+code+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.50% | 4.22 ± 3.39% | 58.12 ± 23.35% | 18.28 ± 12.09% | 2.34 ± 0.03 | 7.15 ± 0.13 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.00 | 42.0 | 0.08% | 0.16% | 0.00% | 13.75% | 11.52% | 7640.62 | 11830.82 |
| safety+math+code+medical | task_arithmetic | 0.00 | 43.0 | 0.08% | 0.16% | 0.00% | 13.75% | 11.52% | 7640.62 | 11830.82 |
| safety+math+code+medical | task_arithmetic | 0.00 | 44.0 | 0.08% | 0.16% | 0.00% | 13.75% | 11.52% | 7640.64 | 11830.81 |
| safety+math+code+medical | task_arithmetic | 0.20 | 42.0 | 0.00% | 1.56% | 0.00% | 50.31% | 12.07% | 1955.89 | 3298.03 |
| safety+math+code+medical | task_arithmetic | 0.20 | 43.0 | 0.00% | 1.25% | 0.00% | 49.06% | 12.01% | 1968.41 | 3330.94 |
| safety+math+code+medical | task_arithmetic | 0.20 | 44.0 | 0.00% | 1.56% | 0.00% | 50.62% | 12.17% | 2010.19 | 3407.41 |
| safety+math+code+medical | task_arithmetic | 0.40 | 42.0 | 0.00% | 0.16% | 0.00% | 17.81% | 14.68% | 62.76 | 46.51 |
| safety+math+code+medical | task_arithmetic | 0.40 | 43.0 | 0.00% | 0.78% | 0.00% | 17.19% | 15.64% | 79.34 | 49.34 |
| safety+math+code+medical | task_arithmetic | 0.40 | 44.0 | 0.00% | 0.31% | 0.00% | 18.75% | 15.26% | 75.21 | 50.10 |
| safety+math+code+medical | task_arithmetic | 0.60 | 42.0 | 5.77% | 2.19% | 0.16% | 73.44% | 14.72% | 3.17 | 6.10 |
| safety+math+code+medical | task_arithmetic | 0.60 | 43.0 | 6.48% | 2.50% | 0.00% | 67.50% | 13.59% | 3.25 | 6.28 |
| safety+math+code+medical | task_arithmetic | 0.60 | 44.0 | 5.40% | 2.97% | 0.00% | 55.31% | 11.48% | 3.24 | 6.10 |
| safety+math+code+medical | task_arithmetic | 0.80 | 42.0 | 0.64% | 3.28% | 4.84% | 26.25% | 15.41% | 2.21 | 5.56 |
| safety+math+code+medical | task_arithmetic | 0.80 | 43.0 | 3.09% | 4.22% | 6.41% | 20.62% | 24.01% | 2.23 | 5.37 |
| safety+math+code+medical | task_arithmetic | 0.80 | 44.0 | 0.00% | 3.12% | 4.06% | 25.00% | 19.39% | 2.24 | 5.38 |
| safety+math+code+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.38% | 32.24% | 2.31 | 7.26 |
| safety+math+code+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+math+code+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.69% | 11.37% | 2.36 | 7.00 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.00 | 31.01 ± 0.00% | 6.25 ± 0.00% | 4.17 ± 1.80% | 63.33 ± 28.87% | 33.25 ± 0.16% | 2.03 ± 0.00 | 2.77 ± 0.00 |
| safety+math | task_arithmetic | 0.20 | 30.94 ± 0.97% | 5.94 ± 0.54% | 6.46 ± 3.37% | 62.81 ± 28.97% | 31.67 ± 3.58% | 1.90 ± 0.01 | 2.67 ± 0.01 |
| safety+math | task_arithmetic | 0.40 | 14.84 ± 1.16% | 5.78 ± 0.31% | 8.23 ± 3.46% | 75.52 ± 15.34% | 28.74 ± 3.37% | 1.83 ± 0.01 | 2.75 ± 0.01 |
| safety+math | task_arithmetic | 0.60 | 2.48 ± 2.89% | 6.88 ± 1.56% | 7.50 ± 0.68% | 75.21 ± 15.93% | 27.18 ± 6.92% | 1.88 ± 0.02 | 3.47 ± 0.12 |
| safety+math | task_arithmetic | 0.80 | 0.00 ± 0.00% | 9.11 ± 1.45% | 5.68 ± 0.24% | 68.70 ± 11.80% | 24.37 ± 9.95% | 2.03 ± 0.02 | 5.17 ± 0.07 |
| safety+math | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.54% | 6.93 ± 8.08% | 48.80 ± 8.77% | 18.36 ± 12.02% | 2.34 ± 0.03 | 7.15 ± 0.14 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.00 | 42.0 | 31.01% | 6.25% | 6.25% | 30.00% | 33.16% | 2.03 | 2.77 |
| safety+math | task_arithmetic | 0.00 | 43.0 | 31.01% | 6.25% | 3.12% | 80.00% | 33.16% | 2.03 | 2.77 |
| safety+math | task_arithmetic | 0.00 | 44.0 | 31.01% | 6.25% | 3.12% | 80.00% | 33.43% | 2.03 | 2.77 |
| safety+math | task_arithmetic | 0.20 | 42.0 | 31.14% | 5.62% | 10.31% | 29.38% | 27.54% | 1.89 | 2.66 |
| safety+math | task_arithmetic | 0.20 | 43.0 | 31.80% | 6.56% | 5.00% | 78.75% | 33.42% | 1.90 | 2.68 |
| safety+math | task_arithmetic | 0.20 | 44.0 | 29.88% | 5.62% | 4.06% | 80.31% | 34.04% | 1.90 | 2.68 |
| safety+math | task_arithmetic | 0.40 | 42.0 | 13.98% | 5.47% | 12.19% | 57.81% | 28.70% | 1.82 | 2.76 |
| safety+math | task_arithmetic | 0.40 | 43.0 | 14.38% | 6.09% | 6.72% | 84.06% | 25.38% | 1.83 | 2.74 |
| safety+math | task_arithmetic | 0.40 | 44.0 | 16.15% | 5.78% | 5.78% | 84.69% | 32.13% | 1.85 | 2.76 |
| safety+math | task_arithmetic | 0.60 | 42.0 | 0.16% | 8.44% | 6.72% | 56.88% | 35.05% | 1.86 | 3.48 |
| safety+math | task_arithmetic | 0.60 | 43.0 | 1.57% | 5.31% | 7.97% | 83.12% | 22.05% | 1.89 | 3.34 |
| safety+math | task_arithmetic | 0.60 | 44.0 | 5.72% | 6.88% | 7.81% | 85.62% | 24.45% | 1.89 | 3.57 |
| safety+math | task_arithmetic | 0.80 | 42.0 | 0.00% | 9.53% | 5.94% | 57.03% | 14.19% | 2.01 | 5.13 |
| safety+math | task_arithmetic | 0.80 | 43.0 | 0.00% | 10.31% | 5.47% | 68.44% | 34.07% | 2.05 | 5.25 |
| safety+math | task_arithmetic | 0.80 | 44.0 | 0.00% | 7.50% | 5.62% | 80.62% | 24.85% | 2.04 | 5.13 |
| safety+math | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 16.25% | 56.72% | 32.24% | 2.31 | 7.26 |
| safety+math | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.94% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+math | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.38% | 11.62% | 2.36 | 7.00 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.00 | 41.06 ± 0.33% | 5.62 ± 0.00% | 21.38 ± 0.00% | 86.25 ± 0.00% | 21.02 ± 0.06% | 1.44 ± 0.00 | 3.84 ± 0.00 |
| safety+code | task_arithmetic | 0.20 | 39.04 ± 0.37% | 3.91 ± 0.31% | 0.78 ± 0.00% | 85.94 ± 0.00% | 34.76 ± 3.89% | 1.51 ± 0.00 | 3.66 ± 0.01 |
| safety+code | task_arithmetic | 0.40 | 34.56 ± 1.54% | 2.45 ± 0.09% | 7.08 ± 3.58% | 86.88 ± 0.00% | 22.35 ± 6.37% | 1.91 ± 0.00 | 4.26 ± 0.01 |
| safety+code | task_arithmetic | 0.60 | 29.17 ± 3.07% | 2.97 ± 0.68% | 4.63 ± 0.09% | 88.85 ± 0.79% | 17.39 ± 0.39% | 2.47 ± 0.01 | 4.84 ± 0.03 |
| safety+code | task_arithmetic | 0.80 | 0.05 ± 0.09% | 2.03 ± 0.81% | 8.18 ± 0.86% | 79.79 ± 6.62% | 20.78 ± 5.96% | 2.11 ± 0.02 | 4.33 ± 0.06 |
| safety+code | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.50% | 4.22 ± 3.39% | 58.02 ± 23.47% | 18.37 ± 12.03% | 2.34 ± 0.03 | 7.15 ± 0.13 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.00 | 42.0 | 40.68% | 5.62% | 21.38% | 86.25% | 20.98% | 1.44 | 3.84 |
| safety+code | task_arithmetic | 0.00 | 43.0 | 41.25% | 5.62% | 21.38% | 86.25% | 20.98% | 1.44 | 3.84 |
| safety+code | task_arithmetic | 0.00 | 44.0 | 41.25% | 5.62% | 21.38% | 86.25% | 21.08% | 1.44 | 3.84 |
| safety+code | task_arithmetic | 0.20 | 42.0 | 38.75% | 3.59% | 0.78% | 85.94% | 39.21% | 1.51 | 3.66 |
| safety+code | task_arithmetic | 0.20 | 43.0 | 39.46% | 3.91% | 0.78% | 85.94% | 32.01% | 1.51 | 3.67 |
| safety+code | task_arithmetic | 0.20 | 44.0 | 38.91% | 4.22% | 0.78% | 85.94% | 33.06% | 1.51 | 3.65 |
| safety+code | task_arithmetic | 0.40 | 42.0 | 35.62% | 2.50% | 9.53% | 86.88% | 19.59% | 1.90 | 4.25 |
| safety+code | task_arithmetic | 0.40 | 43.0 | 35.26% | 2.34% | 2.97% | 86.88% | 29.63% | 1.91 | 4.27 |
| safety+code | task_arithmetic | 0.40 | 44.0 | 32.80% | 2.50% | 8.75% | 86.88% | 17.82% | 1.91 | 4.26 |
| safety+code | task_arithmetic | 0.60 | 42.0 | 32.56% | 3.28% | 4.53% | 89.69% | 17.60% | 2.47 | 4.80 |
| safety+code | task_arithmetic | 0.60 | 43.0 | 26.56% | 3.44% | 4.68% | 88.12% | 17.62% | 2.47 | 4.84 |
| safety+code | task_arithmetic | 0.60 | 44.0 | 28.39% | 2.19% | 4.68% | 88.75% | 16.93% | 2.48 | 4.87 |
| safety+code | task_arithmetic | 0.80 | 42.0 | 0.00% | 2.50% | 8.59% | 86.88% | 27.66% | 2.09 | 4.36 |
| safety+code | task_arithmetic | 0.80 | 43.0 | 0.16% | 2.50% | 7.19% | 78.75% | 17.43% | 2.11 | 4.25 |
| safety+code | task_arithmetic | 0.80 | 44.0 | 0.00% | 1.09% | 8.75% | 73.75% | 17.24% | 2.13 | 4.36 |
| safety+code | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.38% | 32.26% | 2.31 | 7.26 |
| safety+code | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+code | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.38% | 11.62% | 2.36 | 7.00 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.00 | 6.48 ± 0.00% | 4.06 ± 0.00% | 1.72 ± 0.00% | 68.44 ± 0.00% | 19.09 ± 0.09% | 1.89 ± 0.00 | 1.43 ± 0.00 |
| safety+medical | task_arithmetic | 0.20 | 0.08 ± 0.00% | 1.77 ± 0.09% | 0.00 ± 0.00% | 16.04 ± 0.18% | 12.49 ± 0.11% | 54.04 ± 0.07 | 25.78 ± 0.20 |
| safety+medical | task_arithmetic | 0.40 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 20.00 ± 7.04% | 12.25 ± 0.07% | 36901.81 ± 950.77 | 37492.79 ± 653.76 |
| safety+medical | task_arithmetic | 0.60 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.85 ± 0.18% | 12.72 ± 0.06% | 217753.69 ± 12313.53 | 198661.81 ± 12470.98 |
| safety+medical | task_arithmetic | 0.80 | 0.00 ± 0.00% | 0.62 ± 0.41% | 0.00 ± 0.00% | 38.44 ± 15.25% | 12.04 ± 0.26% | 577.39 ± 106.94 | 257.99 ± 44.44 |
| safety+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 0.57 ± 0.50% | 4.22 ± 3.39% | 58.02 ± 23.47% | 18.37 ± 12.03% | 2.34 ± 0.03 | 7.15 ± 0.13 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.00 | 42.0 | 6.48% | 4.06% | 1.72% | 68.44% | 19.00% | 1.89 | 1.43 |
| safety+medical | task_arithmetic | 0.00 | 43.0 | 6.48% | 4.06% | 1.72% | 68.44% | 19.10% | 1.89 | 1.43 |
| safety+medical | task_arithmetic | 0.00 | 44.0 | 6.48% | 4.06% | 1.72% | 68.44% | 19.17% | 1.89 | 1.43 |
| safety+medical | task_arithmetic | 0.20 | 42.0 | 0.08% | 1.72% | 0.00% | 16.25% | 12.39% | 54.12 | 25.57 |
| safety+medical | task_arithmetic | 0.20 | 43.0 | 0.08% | 1.88% | 0.00% | 15.94% | 12.49% | 53.99 | 25.97 |
| safety+medical | task_arithmetic | 0.20 | 44.0 | 0.08% | 1.72% | 0.00% | 15.94% | 12.60% | 54.02 | 25.79 |
| safety+medical | task_arithmetic | 0.40 | 42.0 | 0.00% | 0.00% | 0.00% | 28.12% | 12.34% | 35846.12 | 36843.25 |
| safety+medical | task_arithmetic | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 15.62% | 12.20% | 37168.66 | 37484.42 |
| safety+medical | task_arithmetic | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 16.25% | 12.22% | 37690.63 | 38150.69 |
| safety+medical | task_arithmetic | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 13.75% | 12.69% | 231670.29 | 211313.97 |
| safety+medical | task_arithmetic | 0.60 | 43.0 | 0.16% | 0.00% | 0.00% | 14.06% | 12.69% | 213319.17 | 186380.28 |
| safety+medical | task_arithmetic | 0.60 | 44.0 | 0.16% | 0.00% | 0.00% | 13.75% | 12.79% | 208271.62 | 198291.16 |
| safety+medical | task_arithmetic | 0.80 | 42.0 | 0.00% | 0.47% | 0.00% | 51.25% | 11.80% | 520.77 | 209.85 |
| safety+medical | task_arithmetic | 0.80 | 43.0 | 0.00% | 1.09% | 0.00% | 21.56% | 12.32% | 700.74 | 266.69 |
| safety+medical | task_arithmetic | 0.80 | 44.0 | 0.00% | 0.31% | 0.00% | 42.50% | 12.01% | 510.67 | 297.44 |
| safety+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 0.94% | 8.12% | 84.38% | 32.26% | 2.31 | 7.26 |
| safety+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.03% | 50.31% | 11.23% | 2.36 | 7.18 |
| safety+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 2.50% | 39.38% | 11.62% | 2.36 | 7.00 |


---

### Alpha スイープ: Method = safemerge, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: safemerge, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 4.61 ± 7.99% | 1.30 ± 0.86% | 6.67 ± 4.86% | 82.50 ± 1.74% | 13.09 ± 1.77% | 2.22 ± 0.48 | 6.41 ± 3.54 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: safemerge, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 42.0 | 13.84% | 2.19% | 8.91% | 80.62% | 15.06% | 1.71 | 2.51 |
| safety+math | safemerge | N/A | 43.0 | 0.00% | 0.47% | 1.09% | 84.06% | 11.63% | 2.66 | 9.43 |
| safety+math | safemerge | N/A | 44.0 | 0.00% | 1.25% | 10.00% | 82.81% | 12.60% | 2.30 | 7.29 |


---

### Alpha スイープ: Method = safemerge, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: safemerge, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 0.10 ± 0.18% | 1.51 ± 1.33% | 5.99 ± 5.39% | 73.75 ± 2.98% | 19.84 ± 8.02% | 2.35 ± 0.78 | 7.03 ± 4.96 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: safemerge, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 42.0 | 0.31% | 2.50% | 7.03% | 75.62% | 27.76% | 1.75 | 2.87 |
| safety+code | safemerge | N/A | 43.0 | 0.00% | 2.03% | 10.78% | 70.31% | 20.03% | 2.06 | 5.72 |
| safety+code | safemerge | N/A | 44.0 | 0.00% | 0.00% | 0.16% | 75.31% | 11.72% | 3.23 | 12.51 |


---

### Alpha スイープ: Method = safemerge, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: safemerge, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 0.03 ± 0.05% | 1.09 ± 1.89% | 3.91 ± 6.77% | 53.44 ± 10.84% | 12.81 ± 1.63% | 3.84 ± 1.84 | 15.66 ± 10.55 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: safemerge, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 42.0 | 0.00% | 3.28% | 11.72% | 60.31% | 14.69% | 1.87 | 4.37 |
| safety+medical | safemerge | N/A | 43.0 | 0.08% | 0.00% | 0.00% | 40.94% | 11.81% | 5.53 | 25.25 |
| safety+medical | safemerge | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 59.06% | 11.93% | 4.11 | 17.37 |


---

### Alpha スイープ: Method = led_merging, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: led_merging, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 2.80 ± 0.00% | 1.41 ± 0.00% | 5.62 ± 0.00% | 83.75 ± 0.00% | 22.51 ± 0.02% | 1.75 ± 0.00 | 2.72 ± 0.00 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: led_merging, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 42.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.50% | 1.75 | 2.72 |
| safety+math | led_merging | N/A | 43.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.52% | 1.75 | 2.72 |
| safety+math | led_merging | N/A | 44.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.49% | 1.75 | 2.72 |


---

### Alpha スイープ: Method = led_merging, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: led_merging, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 2.88 ± 0.14% | 1.41 ± 0.00% | 5.62 ± 0.00% | 83.75 ± 0.00% | 22.49 ± 0.04% | 1.75 ± 0.00 | 2.72 ± 0.00 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: led_merging, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 42.0 | 3.04% | 1.41% | 5.62% | 83.75% | 22.49% | 1.75 | 2.72 |
| safety+code | led_merging | N/A | 43.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.52% | 1.75 | 2.72 |
| safety+code | led_merging | N/A | 44.0 | 2.80% | 1.41% | 5.62% | 83.75% | 22.45% | 1.75 | 2.72 |


---

### Alpha スイープ: Method = mergealign, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: mergealign, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 15.73 ± 3.41% | - | - |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: mergealign, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |
| safety+math | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |
| safety+math | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |


---

### Alpha スイープ: Method = mergealign, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: mergealign, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 15.73 ± 3.41% | - | - |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: mergealign, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |
| safety+code | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |
| safety+code | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |


---

### Alpha スイープ: Method = mergealign, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: mergealign, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 86.25 ± 0.00% | 13.76 ± 3.41% | - | - |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: mergealign, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 86.25% | 17.71% | - | - |
| safety+medical | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |
| safety+medical | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 86.25% | 11.79% | - | - |


---
