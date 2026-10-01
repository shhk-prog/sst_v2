# SST-Merge実験結果一覧 (flmsec_hyo.md)
本ファイルは自動生成された実験結果ドキュメントです。
各実験設定ごとに **「平均±標準偏差 (Mean ± Std) の集計表」** と **「シード別 (Seed 42, 43, 44) の詳細結果比較表」** をセットで上下に掲載しています。
ディレクトリ `results/normal` および `results/vllm` の両方からデータを収集・併記しています。

## 0. 論文メインテキスト用 簡易まとめ表
`flmsec.md` のメインテキストに直接貼り付けられるよう、不要な列（Env, Alpha, Seed等）を省き、主要な設定（Alpha=0.6またはN/A）のみを抽出した表です。ベースモデルのスコアも参考として含めています。

### メイン実験 簡易版

#### 【簡易版】 メイン実験 (Alpha=0.6 / N/A)

| Pattern | Method | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| Base (MedAlpaca) | Base (MedAlpaca) | 64.41 ± 0.00% | 2.81 ± 0.00% | 9.60 ± 0.00% | 62.03 ± 0.00% | 25.95 ± 0.00% |
| Base (SafetyFT) | Base (SafetyFT) | 0.00 ± 0.00% | 4.58 ± 1.15% | 7.88 ± 1.72% | 60.21 ± 1.26% | 16.17 ± 0.46% |
| Base (WizardCoder) | Base (WizardCoder) | 72.81 ± 0.00% | 4.53 ± 0.00% | 34.07 ± 0.00% | 54.06 ± 0.00% | 19.68 ± 0.00% |
| Base (WizardMath) | Base (WizardMath) | 64.93 ± 0.00% | 22.34 ± 0.00% | 9.07 ± 0.00% | 60.62 ± 0.00% | 18.36 ± 0.00% |
| safety+code | dare | 0.00 ± 0.00% | 0.26 ± 0.24% | 0.00 ± 0.00% | 31.56 ± 11.41% | 11.80 ± 0.92% |
| safety+code | data_free_sst_main | 0.03 ± 0.05% | 0.16 ± 0.27% | 0.00 ± 0.00% | 55.36 ± 3.82% | 14.94 ± 0.26% |
| safety+code | della | 0.00 ± 0.00% | 0.26 ± 0.33% | 0.00 ± 0.00% | 31.41 ± 13.67% | 12.31 ± 0.88% |
| safety+code | diagonal_sst_main | 1.10 ± 0.47% | 0.83 ± 0.09% | 0.00 ± 0.00% | 54.84 ± 1.02% | 12.60 ± 0.09% |
| safety+code | led_merging | 2.64 ± 0.00% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.65 ± 0.08% |
| safety+code | matena_fisher | 3.38 ± 1.18% | 0.83 ± 0.09% | 0.00 ± 0.00% | 56.20 ± 0.74% | 13.27 ± 0.61% |
| safety+code | mergealign | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.64 ± 0.00% |
| safety+code | safemerge | 0.10 ± 0.18% | 2.19 ± 1.65% | 8.20 ± 3.95% | 55.21 ± 6.44% | 23.78 ± 9.09% |
| safety+code | task_arithmetic | 29.22 ± 3.11% | 2.08 ± 0.95% | 2.37 ± 0.67% | 56.72 ± 0.95% | 19.13 ± 0.27% |
| safety+code | ties | 0.11 ± 0.13% | 1.25 ± 0.56% | 0.00 ± 0.00% | 30.89 ± 13.04% | 17.84 ± 9.74% |
| safety+math | dare | 6.22 ± 5.24% | 20.00 ± 0.47% | 7.91 ± 0.50% | 60.16 ± 0.56% | 28.04 ± 8.60% |
| safety+math | data_free_sst_main | 14.70 ± 3.30% | 21.46 ± 0.45% | 8.34 ± 0.71% | 61.04 ± 0.33% | 34.60 ± 8.29% |
| safety+math | della | 6.67 ± 5.52% | 21.77 ± 1.15% | 7.40 ± 0.93% | 59.74 ± 0.39% | 35.88 ± 3.59% |
| safety+math | diagonal_sst_main | 17.39 ± 5.23% | 19.95 ± 0.70% | 8.97 ± 0.51% | 60.89 ± 0.63% | 27.54 ± 8.99% |
| safety+math | led_merging | 2.67 ± 0.05% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.67 ± 0.07% |
| safety+math | matena_fisher | 4.26 ± 0.51% | 16.98 ± 1.15% | 9.32 ± 1.05% | 61.35 ± 0.39% | 31.80 ± 11.53% |
| safety+math | mergealign | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.85 ± 0.35% |
| safety+math | safemerge | 4.63 ± 8.03% | 3.80 ± 1.19% | 7.32 ± 2.18% | 60.94 ± 0.68% | 18.10 ± 2.89% |
| safety+math | task_arithmetic | 2.43 ± 2.80% | 15.68 ± 0.63% | 8.87 ± 2.24% | 61.61 ± 0.18% | 32.21 ± 6.62% |
| safety+math | ties | 8.95 ± 5.41% | 20.83 ± 0.90% | 9.73 ± 0.43% | 60.42 ± 0.24% | 32.81 ± 3.39% |
| safety+math+code+medical | dare | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.64 ± 20.19% | 11.51 ± 0.16% |
| safety+math+code+medical | data_free_sst_main | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 40.00 ± 18.66% | 11.61 ± 0.31% |
| safety+math+code+medical | della | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 21.98 ± 4.83% | 12.11 ± 0.51% |
| safety+math+code+medical | diagonal_sst_main | 0.00 ± 0.00% | 0.73 ± 0.72% | 0.00 ± 0.00% | 44.17 ± 7.44% | 10.22 ± 0.47% |
| safety+math+code+medical | matena_fisher | 0.00 ± 0.00% | 2.08 ± 1.17% | 0.00 ± 0.00% | 45.94 ± 16.65% | 13.09 ± 0.17% |
| safety+math+code+medical | task_arithmetic | 5.97 ± 0.50% | 2.92 ± 0.36% | 0.00 ± 0.00% | 48.91 ± 6.99% | 14.56 ± 1.63% |
| safety+math+code+medical | ties | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.51 ± 2.26% | 12.12 ± 0.48% |
| safety+medical | dare | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 19.79 ± 2.12% | 11.00 ± 1.11% |
| safety+medical | data_free_sst_main | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.49 ± 1.80% | 12.72 ± 0.20% |
| safety+medical | della | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.59 ± 10.90% | 12.34 ± 0.59% |
| safety+medical | diagonal_sst_main | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 41.15 ± 23.13% | 11.95 ± 0.28% |
| safety+medical | matena_fisher | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.08 ± 2.26% | 12.98 ± 0.17% |
| safety+medical | mergealign | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 11.98 ± 3.31% |
| safety+medical | safemerge | 0.03 ± 0.05% | 1.35 ± 2.35% | 3.23 ± 5.60% | 45.10 ± 14.55% | 14.87 ± 3.75% |
| safety+medical | task_arithmetic | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.86 ± 17.35% | 12.72 ± 0.06% |
| safety+medical | ties | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.93 ± 3.86% | 12.06 ± 1.23% |


## 1. 予備実験 (TrustLLM / BeaverTails)
各マージ手法のベースラインとしての安全性（TrustLLM ASR / Gibberish）と有用性（BeaverTails Accuracy）の比較。

*No preliminary data found.*

## 2. メイン実験 (Alpha=0.6 / 単一実行手法)
広範なベンチマークにおける各手法の安全性(ASR↓)と有用性(Accuracy/WinRate↑)の比較表。

### メイン実験: Pattern = safety+math

#### 【集計】 メイン実験 (Mean ± Std) - safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.60 | 6.22 ± 5.24% | 20.00 ± 0.47% | 7.91 ± 0.50% | 60.16 ± 0.56% | 28.04 ± 8.60% | 2.14 ± 0.05 | 3.15 ± 0.09 |
| safety+math | dare | 1.00 | 0.00 ± 0.00% | 3.96 ± 0.70% | 7.17 ± 2.69% | 60.47 ± 0.68% | 16.21 ± 0.71% | 1.96 ± 0.04 | 2.99 ± 0.08 |
| safety+math | data_free_sst_main | 0.60 | 14.70 ± 3.30% | 21.46 ± 0.45% | 8.34 ± 0.71% | 61.04 ± 0.33% | 34.60 ± 8.29% | 1.87 ± 0.02 | 2.65 ± 0.03 |
| safety+math | data_free_sst_main | 1.00 | 11.55 ± 9.34% | 19.06 ± 0.27% | 9.35 ± 1.45% | 61.41 ± 0.56% | 34.69 ± 9.06% | 1.93 ± 0.04 | 2.83 ± 0.08 |
| safety+math | della | 0.60 | 6.67 ± 5.52% | 21.77 ± 1.15% | 7.40 ± 0.93% | 59.74 ± 0.39% | 35.88 ± 3.59% | 2.16 ± 0.05 | 3.18 ± 0.08 |
| safety+math | della | 1.00 | 0.00 ± 0.00% | 4.38 ± 0.56% | 7.38 ± 2.42% | 59.64 ± 0.94% | 22.57 ± 10.96% | 1.99 ± 0.04 | 3.06 ± 0.07 |
| safety+math | diagonal_sst_main | 0.60 | 17.39 ± 5.23% | 19.95 ± 0.70% | 8.97 ± 0.51% | 60.89 ± 0.63% | 27.54 ± 8.99% | 1.70 ± 0.01 | 2.42 ± 0.02 |
| safety+math | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 13.28 ± 3.75% | 9.60 ± 2.12% | 61.61 ± 0.48% | 26.63 ± 6.45% | 1.72 ± 0.04 | 2.51 ± 0.09 |
| safety+math | led_merging | N/A | 2.67 ± 0.05% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.67 ± 0.07% | 1.61 ± 0.00 | 2.16 ± 0.00 |
| safety+math | matena_fisher | N/A | 4.26 ± 0.51% | 16.98 ± 1.15% | 9.32 ± 1.05% | 61.35 ± 0.39% | 31.80 ± 11.53% | 1.67 ± 0.01 | 2.39 ± 0.02 |
| safety+math | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.85 ± 0.35% | - | - |
| safety+math | safemerge | N/A | 4.63 ± 8.03% | 3.80 ± 1.19% | 7.32 ± 2.18% | 60.94 ± 0.68% | 18.10 ± 2.89% | 1.90 ± 0.30 | 2.93 ± 0.81 |
| safety+math | task_arithmetic | 0.60 | 2.43 ± 2.80% | 15.68 ± 0.63% | 8.87 ± 2.24% | 61.61 ± 0.18% | 32.21 ± 6.62% | 1.67 ± 0.01 | 2.44 ± 0.03 |
| safety+math | task_arithmetic | 1.00 | 0.00 ± 0.00% | 4.58 ± 0.86% | 7.38 ± 1.78% | 60.16 ± 1.18% | 23.16 ± 11.31% | 1.96 ± 0.04 | 2.98 ± 0.07 |
| safety+math | ties | 0.60 | 8.95 ± 5.41% | 20.83 ± 0.90% | 9.73 ± 0.43% | 60.42 ± 0.24% | 32.81 ± 3.39% | 1.94 ± 0.03 | 2.86 ± 0.06 |
| safety+math | ties | 1.00 | 0.00 ± 0.00% | 4.27 ± 0.33% | 7.99 ± 2.61% | 60.36 ± 1.04% | 25.53 ± 8.52% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.60 | 42.0 | 23.08% | 20.62% | 8.75% | 61.25% | 18.48% | 1.70 | 2.40 |
| safety+math | diagonal_sst_main | 0.60 | 43.0 | 16.28% | 19.22% | 8.61% | 60.16% | 36.46% | 1.70 | 2.44 |
| safety+math | diagonal_sst_main | 0.60 | 44.0 | 12.81% | 20.00% | 9.55% | 61.25% | 27.68% | 1.71 | 2.43 |
| safety+math | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 17.50% | 11.74% | 62.03% | 19.30% | 1.68 | 2.42 |
| safety+math | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 10.31% | 7.50% | 61.09% | 31.49% | 1.75 | 2.59 |
| safety+math | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 12.03% | 9.55% | 61.72% | 29.09% | 1.73 | 2.53 |


#### 【シード別詳細】 メイン実験 - Method: mergealign, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+math | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 57.50% | 14.25% | - | - |
| safety+math | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |


#### 【シード別詳細】 メイン実験 - Method: led_merging, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 42.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.63% | 1.61 | 2.16 |
| safety+math | led_merging | N/A | 43.0 | 2.72% | 1.41% | 5.62% | 56.25% | 28.75% | 1.61 | 2.16 |
| safety+math | led_merging | N/A | 44.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.63% | 1.61 | 2.16 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.60 | 42.0 | 10.97% | 21.72% | 9.08% | 60.94% | 44.16% | 1.85 | 2.62 |
| safety+math | data_free_sst_main | 0.60 | 43.0 | 15.92% | 21.72% | 7.67% | 61.41% | 30.28% | 1.88 | 2.67 |
| safety+math | data_free_sst_main | 0.60 | 44.0 | 17.22% | 20.94% | 8.29% | 60.78% | 29.36% | 1.88 | 2.67 |
| safety+math | data_free_sst_main | 1.00 | 42.0 | 0.87% | 18.91% | 10.34% | 61.25% | 43.95% | 1.89 | 2.74 |
| safety+math | data_free_sst_main | 1.00 | 43.0 | 18.18% | 19.38% | 7.69% | 62.03% | 34.30% | 1.95 | 2.86 |
| safety+math | data_free_sst_main | 1.00 | 44.0 | 15.59% | 18.91% | 10.02% | 60.94% | 25.83% | 1.96 | 2.89 |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.60 | 42.0 | 0.16% | 15.78% | 7.21% | 61.41% | 39.79% | 1.66 | 2.41 |
| safety+math | task_arithmetic | 0.60 | 43.0 | 1.57% | 15.00% | 7.99% | 61.72% | 27.55% | 1.68 | 2.46 |
| safety+math | task_arithmetic | 0.60 | 44.0 | 5.56% | 16.25% | 11.43% | 61.72% | 29.30% | 1.68 | 2.46 |
| safety+math | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.41% | 36.21% | 1.91 | 2.90 |
| safety+math | task_arithmetic | 1.00 | 43.0 | 0.00% | 5.47% | 5.34% | 60.00% | 16.63% | 1.97 | 3.01 |
| safety+math | task_arithmetic | 1.00 | 44.0 | 0.00% | 3.75% | 8.15% | 59.06% | 16.63% | 1.98 | 3.03 |


#### 【シード別詳細】 メイン実験 - Method: safemerge, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 42.0 | 13.90% | 4.84% | 7.18% | 61.41% | 21.24% | 1.59 | 2.12 |
| safety+math | safemerge | N/A | 43.0 | 0.00% | 2.50% | 5.21% | 60.16% | 15.55% | 2.19 | 3.74 |
| safety+math | safemerge | N/A | 44.0 | 0.00% | 4.06% | 9.56% | 61.25% | 17.50% | 1.92 | 2.94 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.60 | 42.0 | 0.32% | 20.47% | 7.71% | 59.53% | 19.57% | 2.08 | 3.06 |
| safety+math | dare | 0.60 | 43.0 | 7.99% | 19.53% | 8.48% | 60.62% | 27.78% | 2.16 | 3.16 |
| safety+math | dare | 0.60 | 44.0 | 10.35% | 20.00% | 7.55% | 60.31% | 36.77% | 2.18 | 3.23 |
| safety+math | dare | 1.00 | 42.0 | 0.00% | 3.28% | 9.57% | 61.25% | 15.49% | 1.92 | 2.91 |
| safety+math | dare | 1.00 | 43.0 | 0.00% | 4.69% | 4.27% | 60.16% | 16.23% | 1.97 | 3.04 |
| safety+math | dare | 1.00 | 44.0 | 0.00% | 3.91% | 7.68% | 60.00% | 16.90% | 1.99 | 3.03 |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | della | 0.60 | 42.0 | 0.70% | 22.19% | 6.78% | 60.16% | 34.07% | 2.11 | 3.09 |
| safety+math | della | 0.60 | 43.0 | 11.61% | 22.66% | 8.47% | 59.38% | 33.56% | 2.17 | 3.20 |
| safety+math | della | 0.60 | 44.0 | 7.68% | 20.47% | 6.93% | 59.69% | 40.02% | 2.20 | 3.25 |
| safety+math | della | 1.00 | 42.0 | 0.00% | 4.53% | 9.72% | 60.62% | 35.22% | 1.94 | 2.97 |
| safety+math | della | 1.00 | 43.0 | 0.00% | 4.84% | 4.89% | 59.53% | 15.86% | 2.00 | 3.09 |
| safety+math | della | 1.00 | 44.0 | 0.00% | 3.75% | 7.53% | 58.75% | 16.64% | 2.01 | 3.11 |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | ties | 0.60 | 42.0 | 3.20% | 20.31% | 10.06% | 60.47% | 28.90% | 1.90 | 2.80 |
| safety+math | ties | 0.60 | 43.0 | 9.69% | 21.88% | 9.25% | 60.62% | 34.87% | 1.95 | 2.87 |
| safety+math | ties | 0.60 | 44.0 | 13.95% | 20.31% | 9.88% | 60.16% | 34.68% | 1.97 | 2.91 |
| safety+math | ties | 1.00 | 42.0 | 0.00% | 3.91% | 10.35% | 61.56% | 33.97% | 1.86 | 2.78 |
| safety+math | ties | 1.00 | 43.0 | 0.00% | 4.53% | 5.18% | 59.84% | 16.94% | 1.92 | 2.86 |
| safety+math | ties | 1.00 | 44.0 | 0.00% | 4.38% | 8.45% | 59.69% | 25.67% | 1.93 | 2.88 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 42.0 | 4.79% | 16.09% | 8.11% | 61.41% | 44.12% | 1.66 | 2.37 |
| safety+math | matena_fisher | N/A | 43.0 | 4.22% | 18.28% | 9.84% | 60.94% | 21.26% | 1.68 | 2.41 |
| safety+math | matena_fisher | N/A | 44.0 | 3.77% | 16.56% | 10.01% | 61.72% | 30.01% | 1.68 | 2.40 |


---

### メイン実験: Pattern = safety+code

#### 【集計】 メイン実験 (Mean ± Std) - safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.60 | 0.00 ± 0.00% | 0.26 ± 0.24% | 0.00 ± 0.00% | 31.56 ± 11.41% | 11.80 ± 0.92% | 398649.10 ± 507513.35 | 425860.14 ± 214984.80 |
| safety+code | dare | 1.00 | 0.00 ± 0.00% | 2.86 ± 1.66% | 6.94 ± 3.12% | 52.60 ± 14.46% | 26.35 ± 10.13% | 1.96 ± 0.04 | 2.97 ± 0.06 |
| safety+code | data_free_sst_main | 0.60 | 0.03 ± 0.05% | 0.16 ± 0.27% | 0.00 ± 0.00% | 55.36 ± 3.82% | 14.94 ± 0.26% | 112.57 ± 56.38 | 23.38 ± 6.19 |
| safety+code | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.16 ± 0.16% | 0.00 ± 0.00% | 42.86 ± 16.15% | 12.18 ± 0.07% | 17815.49 ± 16468.76 | 2046.19 ± 1654.26 |
| safety+code | della | 0.60 | 0.00 ± 0.00% | 0.26 ± 0.33% | 0.00 ± 0.00% | 31.41 ± 13.67% | 12.31 ± 0.88% | 120223.11 ± 54132.59 | 253194.63 ± 34087.44 |
| safety+code | della | 1.00 | 0.00 ± 0.00% | 2.81 ± 2.03% | 5.80 ± 4.43% | 51.93 ± 14.31% | 15.93 ± 0.64% | 1.98 ± 0.04 | 3.05 ± 0.08 |
| safety+code | diagonal_sst_main | 0.60 | 1.10 ± 0.47% | 0.83 ± 0.09% | 0.00 ± 0.00% | 54.84 ± 1.02% | 12.60 ± 0.09% | 185.23 ± 93.56 | 23.14 ± 4.56 |
| safety+code | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.31% | 0.00 ± 0.00% | 32.19 ± 8.93% | 10.55 ± 0.30% | 258.23 ± 35.18 | 166.09 ± 78.86 |
| safety+code | led_merging | N/A | 2.64 ± 0.00% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.65 ± 0.08% | 1.61 ± 0.00 | 2.16 ± 0.00 |
| safety+code | matena_fisher | N/A | 3.38 ± 1.18% | 0.83 ± 0.09% | 0.00 ± 0.00% | 56.20 ± 0.74% | 13.27 ± 0.61% | 80.11 ± 15.69 | 63.11 ± 20.25 |
| safety+code | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.64 ± 0.00% | - | - |
| safety+code | safemerge | N/A | 0.10 ± 0.18% | 2.19 ± 1.65% | 8.20 ± 3.95% | 55.21 ± 6.44% | 23.78 ± 9.09% | 1.98 ± 0.54 | 3.19 ± 1.54 |
| safety+code | task_arithmetic | 0.60 | 29.22 ± 3.11% | 2.08 ± 0.95% | 2.37 ± 0.67% | 56.72 ± 0.95% | 19.13 ± 0.27% | 2.32 ± 0.02 | 3.95 ± 0.02 |
| safety+code | task_arithmetic | 1.00 | 0.00 ± 0.00% | 3.02 ± 1.98% | 6.38 ± 3.63% | 53.49 ± 11.88% | 23.16 ± 11.31% | 1.96 ± 0.04 | 2.98 ± 0.07 |
| safety+code | ties | 0.60 | 0.11 ± 0.13% | 1.25 ± 0.56% | 0.00 ± 0.00% | 30.89 ± 13.04% | 17.84 ± 9.74% | 137.44 ± 182.79 | 22.88 ± 22.58 |
| safety+code | ties | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.04% | 7.62 ± 3.22% | 51.35 ± 16.08% | 30.48 ± 16.26% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.60 | 42.0 | 0.00% | 0.31% | 0.00% | 28.91% | 10.77% | 88574.49 | 332254.62 |
| safety+code | dare | 0.60 | 43.0 | 0.00% | 0.47% | 0.00% | 21.72% | 12.11% | 123035.62 | 273547.43 |
| safety+code | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 44.06% | 12.52% | 984337.19 | 671778.37 |
| safety+code | dare | 1.00 | 42.0 | 0.00% | 4.38% | 9.42% | 61.88% | 36.30% | 1.91 | 2.90 |
| safety+code | dare | 1.00 | 43.0 | 0.00% | 1.09% | 3.44% | 35.94% | 16.06% | 1.97 | 3.01 |
| safety+code | dare | 1.00 | 44.0 | 0.00% | 3.12% | 7.98% | 60.00% | 26.70% | 1.99 | 3.01 |


#### 【シード別詳細】 メイン実験 - Method: led_merging, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 42.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.63% | 1.61 | 2.16 |
| safety+code | led_merging | N/A | 43.0 | 2.64% | 1.41% | 5.62% | 56.25% | 28.74% | 1.61 | 2.16 |
| safety+code | led_merging | N/A | 44.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.58% | 1.61 | 2.16 |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.60 | 42.0 | 32.61% | 1.88% | 1.84% | 56.09% | 19.11% | 2.33 | 3.96 |
| safety+code | task_arithmetic | 0.60 | 43.0 | 26.49% | 3.12% | 3.12% | 57.81% | 19.41% | 2.30 | 3.93 |
| safety+code | task_arithmetic | 0.60 | 44.0 | 28.54% | 1.25% | 2.14% | 56.25% | 18.88% | 2.33 | 3.96 |
| safety+code | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.56% | 36.23% | 1.91 | 2.90 |
| safety+code | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.19% | 39.84% | 16.63% | 1.97 | 3.01 |
| safety+code | task_arithmetic | 1.00 | 44.0 | 0.00% | 3.75% | 8.31% | 59.06% | 16.63% | 1.98 | 3.03 |


#### 【シード別詳細】 メイン実験 - Method: mergealign, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+code | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+code | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |


#### 【シード別詳細】 メイン実験 - Method: safemerge, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 42.0 | 0.31% | 3.91% | 10.16% | 61.25% | 32.54% | 1.60 | 2.13 |
| safety+code | safemerge | N/A | 43.0 | 0.00% | 2.03% | 10.78% | 48.44% | 24.41% | 1.75 | 2.47 |
| safety+code | safemerge | N/A | 44.0 | 0.00% | 0.62% | 3.66% | 55.94% | 14.39% | 2.60 | 4.95 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 42.0 | 4.72% | 0.78% | 0.00% | 55.94% | 13.68% | 68.60 | 77.14 |
| safety+code | matena_fisher | N/A | 43.0 | 2.93% | 0.94% | 0.00% | 55.62% | 13.57% | 73.74 | 39.89 |
| safety+code | matena_fisher | N/A | 44.0 | 2.49% | 0.78% | 0.00% | 57.03% | 12.57% | 97.99 | 72.30 |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | della | 0.60 | 42.0 | 0.00% | 0.62% | 0.00% | 20.94% | 13.26% | 174271.91 | 216049.68 |
| safety+code | della | 0.60 | 43.0 | 0.00% | 0.16% | 0.00% | 26.41% | 12.15% | 120390.29 | 260491.37 |
| safety+code | della | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 46.88% | 11.52% | 66007.11 | 283042.85 |
| safety+code | della | 1.00 | 42.0 | 0.00% | 4.06% | 9.88% | 61.41% | 15.43% | 1.93 | 2.96 |
| safety+code | della | 1.00 | 43.0 | 0.00% | 0.47% | 1.09% | 35.47% | 15.71% | 2.00 | 3.09 |
| safety+code | della | 1.00 | 44.0 | 0.00% | 3.91% | 6.43% | 58.91% | 16.64% | 2.01 | 3.10 |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.60 | 42.0 | 1.29% | 0.78% | 0.00% | 54.69% | 12.70% | 113.07 | 18.31 |
| safety+code | diagonal_sst_main | 0.60 | 43.0 | 1.44% | 0.94% | 0.00% | 53.91% | 12.57% | 290.94 | 27.36 |
| safety+code | diagonal_sst_main | 0.60 | 44.0 | 0.57% | 0.78% | 0.00% | 55.94% | 12.52% | 151.69 | 23.75 |
| safety+code | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.94% | 0.00% | 39.38% | 10.84% | 295.43 | 241.91 |
| safety+code | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 0.62% | 0.00% | 22.19% | 10.24% | 253.76 | 84.50 |
| safety+code | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 0.31% | 0.00% | 35.00% | 10.57% | 225.51 | 171.87 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 56.56% | 14.71% | 128.94 | 25.36 |
| safety+code | data_free_sst_main | 0.60 | 43.0 | 0.00% | 0.47% | 0.00% | 51.09% | 14.90% | 49.82 | 16.44 |
| safety+code | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 58.44% | 15.21% | 158.96 | 28.34 |
| safety+code | data_free_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 52.50% | 12.26% | 15402.26 | 2349.27 |
| safety+code | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.31% | 0.00% | 24.22% | 12.17% | 2686.49 | 261.35 |
| safety+code | data_free_sst_main | 1.00 | 44.0 | 0.08% | 0.16% | 0.00% | 51.88% | 12.11% | 35357.72 | 3527.96 |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | ties | 0.60 | 42.0 | 0.08% | 1.09% | 0.00% | 45.94% | 12.73% | 50.73 | 48.95 |
| safety+code | ties | 0.60 | 43.0 | 0.00% | 1.88% | 0.00% | 23.12% | 11.72% | 14.13 | 10.28 |
| safety+code | ties | 0.60 | 44.0 | 0.25% | 0.78% | 0.00% | 23.59% | 29.07% | 347.45 | 9.42 |
| safety+code | ties | 1.00 | 42.0 | 0.00% | 3.91% | 10.35% | 61.56% | 48.60% | 1.86 | 2.78 |
| safety+code | ties | 1.00 | 43.0 | 0.00% | 0.62% | 4.06% | 32.81% | 17.17% | 1.92 | 2.86 |
| safety+code | ties | 1.00 | 44.0 | 0.00% | 4.38% | 8.45% | 59.69% | 25.66% | 1.93 | 2.88 |


---

### メイン実験: Pattern = safety+medical

#### 【集計】 メイン実験 (Mean ± Std) - safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 19.79 ± 2.12% | 11.00 ± 1.11% | 20797785.11 ± 14399754.63 | 14708432.51 ± 16144047.41 |
| safety+medical | dare | 1.00 | 0.00 ± 0.00% | 2.50 ± 1.76% | 5.27 ± 4.94% | 47.19 ± 14.14% | 22.22 ± 10.35% | 1.96 ± 0.04 | 2.98 ± 0.07 |
| safety+medical | data_free_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.49 ± 1.80% | 12.72 ± 0.20% | 154475.14 ± 80159.01 | 118397.35 ± 35122.34 |
| safety+medical | data_free_sst_main | 1.00 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.20 ± 22.92% | 12.53 ± 0.09% | 303013.60 ± 160352.85 | 130002.00 ± 53693.74 |
| safety+medical | della | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.59 ± 10.90% | 12.34 ± 0.59% | 10981445.00 ± 6253371.40 | 12572823.50 ± 5352914.49 |
| safety+medical | della | 1.00 | 0.00 ± 0.00% | 1.25 ± 1.63% | 4.69 ± 4.61% | 44.48 ± 14.31% | 24.63 ± 8.87% | 1.98 ± 0.04 | 3.05 ± 0.07 |
| safety+medical | diagonal_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 41.15 ± 23.13% | 11.95 ± 0.28% | 79783.06 ± 18826.86 | 89052.84 ± 40211.85 |
| safety+medical | diagonal_sst_main | 1.00 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.55 ± 15.93% | 11.74 ± 0.55% | 139537.68 ± 165148.85 | 102521.68 ± 83446.86 |
| safety+medical | matena_fisher | N/A | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.08 ± 2.26% | 12.98 ± 0.17% | 384272.26 ± 81902.74 | 304225.05 ± 19087.67 |
| safety+medical | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 11.98 ± 3.31% | - | - |
| safety+medical | safemerge | N/A | 0.03 ± 0.05% | 1.35 ± 2.35% | 3.23 ± 5.60% | 45.10 ± 14.55% | 14.87 ± 3.75% | 3.00 ± 1.27 | 6.06 ± 3.55 |
| safety+medical | task_arithmetic | 0.60 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.86 ± 17.35% | 12.72 ± 0.06% | 200116.75 ± 7068.23 | 209487.62 ± 9249.30 |
| safety+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.07% | 6.38 ± 3.63% | 53.49 ± 11.88% | 23.13 ± 11.35% | 1.96 ± 0.04 | 2.98 ± 0.07 |
| safety+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.93 ± 3.86% | 12.06 ± 1.23% | 39894.11 ± 10705.72 | 63613.99 ± 30155.00 |
| safety+medical | ties | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.04% | 7.62 ± 3.22% | 51.35 ± 16.08% | 25.64 ± 8.45% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 メイン実験 - Method: safemerge, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 42.0 | 0.00% | 4.06% | 9.70% | 61.09% | 19.15% | 1.64 | 2.23 |
| safety+medical | safemerge | N/A | 43.0 | 0.08% | 0.00% | 0.00% | 32.66% | 12.18% | 4.16 | 9.24 |
| safety+medical | safemerge | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 41.56% | 13.29% | 3.20 | 6.72 |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 17.50% | 12.78% | 38043.47 | 97897.33 |
| safety+medical | ties | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 20.47% | 12.76% | 51404.50 | 41198.48 |
| safety+medical | ties | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 12.81% | 10.64% | 30234.36 | 51746.15 |
| safety+medical | ties | 1.00 | 42.0 | 0.00% | 3.91% | 10.35% | 61.56% | 34.08% | 1.86 | 2.78 |
| safety+medical | ties | 1.00 | 43.0 | 0.00% | 0.62% | 4.06% | 32.81% | 17.17% | 1.92 | 2.86 |
| safety+medical | ties | 1.00 | 44.0 | 0.00% | 4.38% | 8.45% | 59.69% | 25.66% | 1.93 | 2.88 |


#### 【シード別詳細】 メイン実験 - Method: mergealign, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+medical | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 57.50% | 14.13% | - | - |
| safety+medical | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 8.16% | - | - |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 37.66% | 12.43% | 16881833.35 | 18702955.33 |
| safety+medical | della | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 41.88% | 12.88% | 11635930.70 | 10193181.80 |
| safety+medical | della | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 21.25% | 11.71% | 4426570.97 | 8822333.38 |
| safety+medical | della | 1.00 | 42.0 | 0.00% | 3.12% | 10.02% | 60.94% | 33.76% | 1.93 | 2.97 |
| safety+medical | della | 1.00 | 43.0 | 0.00% | 0.47% | 2.19% | 37.50% | 24.09% | 1.99 | 3.07 |
| safety+medical | della | 1.00 | 44.0 | 0.00% | 0.16% | 1.88% | 35.00% | 16.05% | 2.02 | 3.11 |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 51.25% | 11.92% | 95009.90 | 79407.33 |
| safety+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 14.69% | 12.24% | 85606.83 | 133210.26 |
| safety+medical | diagonal_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 57.50% | 11.68% | 58732.45 | 54540.92 |
| safety+medical | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 20.31% | 12.25% | 22655.80 | 7801.03 |
| safety+medical | diagonal_sst_main | 1.00 | 43.0 | 0.08% | 0.00% | 0.00% | 40.62% | 11.16% | 328470.43 | 165191.36 |
| safety+medical | diagonal_sst_main | 1.00 | 44.0 | 0.08% | 0.00% | 0.00% | 51.72% | 11.81% | 67486.81 | 134572.64 |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 49.84% | 12.69% | 207511.45 | 220160.55 |
| safety+medical | task_arithmetic | 0.60 | 43.0 | 0.16% | 0.00% | 0.00% | 17.97% | 12.69% | 199410.83 | 203810.74 |
| safety+medical | task_arithmetic | 0.60 | 44.0 | 0.16% | 0.00% | 0.00% | 45.78% | 12.79% | 193427.97 | 204491.56 |
| safety+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.56% | 36.23% | 1.91 | 2.90 |
| safety+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.62% | 2.19% | 39.84% | 16.53% | 1.97 | 3.01 |
| safety+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 3.75% | 8.31% | 59.06% | 16.63% | 1.98 | 3.03 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 54.53% | 12.78% | 204138.99 | 156315.42 |
| safety+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 54.53% | 12.50% | 62000.09 | 86978.63 |
| safety+medical | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 51.41% | 12.89% | 197286.35 | 111898.00 |
| safety+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 56.88% | 12.43% | 415600.47 | 147036.09 |
| safety+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 12.81% | 12.59% | 374023.67 | 173112.44 |
| safety+medical | data_free_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 23.91% | 12.56% | 119416.65 | 69857.47 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 21.09% | 9.83% | 31717047.76 | 33279831.89 |
| safety+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 20.94% | 11.14% | 4478586.08 | 4023586.47 |
| safety+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 17.34% | 12.03% | 26197721.48 | 6821879.17 |
| safety+medical | dare | 1.00 | 42.0 | 0.00% | 3.59% | 10.96% | 61.41% | 34.17% | 1.91 | 2.90 |
| safety+medical | dare | 1.00 | 43.0 | 0.00% | 0.47% | 2.66% | 47.03% | 16.17% | 1.98 | 2.99 |
| safety+medical | dare | 1.00 | 44.0 | 0.00% | 3.44% | 2.19% | 33.12% | 16.30% | 1.99 | 3.05 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 42.0 | 0.16% | 0.00% | 0.00% | 14.69% | 13.06% | 478783.02 | 325558.33 |
| safety+medical | matena_fisher | N/A | 43.0 | 0.16% | 0.00% | 0.00% | 10.78% | 12.78% | 339991.11 | 288761.78 |
| safety+medical | matena_fisher | N/A | 44.0 | 0.16% | 0.00% | 0.00% | 10.78% | 13.09% | 334042.64 | 298355.05 |


---

### メイン実験: Pattern = safety+math+code+medical

#### 【集計】 メイン実験 (Mean ± Std) - safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.60 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.64 ± 20.19% | 11.51 ± 0.16% | 4659204.25 ± 5454560.12 | 4988976.69 ± 3382670.49 |
| safety+math+code+medical | dare | 1.00 | 0.00 ± 0.00% | 2.86 ± 2.48% | 6.84 ± 3.08% | 50.83 ± 16.17% | 22.66 ± 11.23% | 1.96 ± 0.04 | 2.98 ± 0.06 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 40.00 ± 18.66% | 11.61 ± 0.31% | 17938.54 ± 3918.72 | 37505.01 ± 22671.13 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.85 ± 4.44% | 11.59 ± 0.56% | 13257.09 ± 4123.52 | 16581.99 ± 3829.08 |
| safety+math+code+medical | della | 0.60 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 21.98 ± 4.83% | 12.11 ± 0.51% | 1879414.85 ± 888079.34 | 2040741.79 ± 582209.44 |
| safety+math+code+medical | della | 1.00 | 0.00 ± 0.00% | 2.71 ± 2.10% | 5.71 ± 2.88% | 51.35 ± 15.41% | 23.68 ± 12.39% | 1.99 ± 0.04 | 3.06 ± 0.09 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 0.00 ± 0.00% | 0.73 ± 0.72% | 0.00 ± 0.00% | 44.17 ± 7.44% | 10.22 ± 0.47% | 453.77 ± 82.57 | 109.69 ± 29.01 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 0.16 ± 0.00% | 0.57 ± 0.74% | 0.00 ± 0.00% | 54.74 ± 4.11% | 17.30 ± 4.28% | 109.78 ± 56.64 | 47.15 ± 20.38 |
| safety+math+code+medical | matena_fisher | N/A | 0.00 ± 0.00% | 2.08 ± 1.17% | 0.00 ± 0.00% | 45.94 ± 16.65% | 13.09 ± 0.17% | 63.37 ± 3.09 | 102.90 ± 1.68 |
| safety+math+code+medical | task_arithmetic | 0.60 | 5.97 ± 0.50% | 2.92 ± 0.36% | 0.00 ± 0.00% | 48.91 ± 6.99% | 14.56 ± 1.63% | 2.91 ± 0.06 | 4.50 ± 0.04 |
| safety+math+code+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 3.33 ± 2.92% | 7.22 ± 1.70% | 51.93 ± 15.36% | 22.97 ± 11.46% | 1.96 ± 0.04 | 2.98 ± 0.07 |
| safety+math+code+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.51 ± 2.26% | 12.12 ± 0.48% | 216889.35 ± 204103.70 | 271395.89 ± 218392.59 |
| safety+math+code+medical | ties | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.36% | 6.22 ± 4.17% | 52.29 ± 14.59% | 30.47 ± 16.30% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 メイン実験 - Method: diagonal_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 42.0 | 0.00% | 1.56% | 0.00% | 37.50% | 10.44% | 535.18 | 141.16 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.31% | 0.00% | 52.19% | 10.55% | 370.08 | 84.01 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 44.0 | 0.00% | 0.31% | 0.00% | 42.81% | 9.68% | 456.06 | 103.91 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 42.0 | 0.16% | 1.41% | 0.00% | 56.88% | 12.36% | 168.96 | 68.21 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 43.0 | 0.16% | 0.31% | 0.00% | 57.34% | 19.59% | 56.08 | 27.53 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 50.00% | 19.95% | 104.29 | 45.71 |


#### 【シード別詳細】 メイン実験 - Method: dare, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 57.03% | 11.37% | 10950640.94 | 8892188.86 |
| safety+math+code+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 29.06% | 11.68% | 1769599.74 | 2910245.81 |
| safety+math+code+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 17.81% | 11.49% | 1257372.06 | 3164495.39 |
| safety+math+code+medical | dare | 1.00 | 42.0 | 0.00% | 4.22% | 10.33% | 60.94% | 35.63% | 1.91 | 2.91 |
| safety+math+code+medical | dare | 1.00 | 43.0 | 0.00% | 4.38% | 5.66% | 59.38% | 16.24% | 1.97 | 3.00 |
| safety+math+code+medical | dare | 1.00 | 44.0 | 0.00% | 0.00% | 4.53% | 32.19% | 16.12% | 1.99 | 3.02 |


#### 【シード別詳細】 メイン実験 - Method: data_free_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 57.66% | 11.96% | 14544.18 | 28970.80 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 20.47% | 11.38% | 22227.08 | 20339.54 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 41.88% | 11.49% | 17044.37 | 63204.70 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 55.16% | 10.98% | 17981.87 | 20695.07 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 48.91% | 11.76% | 11405.37 | 13120.54 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 12.05% | 10384.04 | 15930.35 |


#### 【シード別詳細】 メイン実験 - Method: matena_fisher, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 42.0 | 0.00% | 2.03% | 0.00% | 55.31% | 12.92% | 65.47 | 102.13 |
| safety+math+code+medical | matena_fisher | N/A | 43.0 | 0.00% | 3.28% | 0.00% | 55.78% | 13.08% | 59.82 | 101.75 |
| safety+math+code+medical | matena_fisher | N/A | 44.0 | 0.00% | 0.94% | 0.00% | 26.72% | 13.26% | 64.83 | 104.83 |


#### 【シード別詳細】 メイン実験 - Method: della, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 20.62% | 11.68% | 1422834.97 | 1400940.99 |
| safety+math+code+medical | della | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 17.97% | 11.98% | 1312509.21 | 2181871.31 |
| safety+math+code+medical | della | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 27.34% | 12.67% | 2902900.38 | 2539413.07 |
| safety+math+code+medical | della | 1.00 | 42.0 | 0.00% | 3.59% | 8.95% | 61.25% | 37.98% | 1.94 | 2.96 |
| safety+math+code+medical | della | 1.00 | 43.0 | 0.00% | 4.22% | 4.73% | 59.22% | 16.51% | 2.00 | 3.10 |
| safety+math+code+medical | della | 1.00 | 44.0 | 0.00% | 0.31% | 3.44% | 33.59% | 16.55% | 2.02 | 3.12 |


#### 【シード別詳細】 メイン実験 - Method: task_arithmetic, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.60 | 42.0 | 6.18% | 3.12% | 0.00% | 56.25% | 16.33% | 2.85 | 4.49 |
| safety+math+code+medical | task_arithmetic | 0.60 | 43.0 | 6.32% | 2.50% | 0.00% | 48.12% | 14.22% | 2.94 | 4.47 |
| safety+math+code+medical | task_arithmetic | 0.60 | 44.0 | 5.40% | 3.12% | 0.00% | 42.34% | 13.12% | 2.96 | 4.54 |
| safety+math+code+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.56% | 36.21% | 1.91 | 2.90 |
| safety+math+code+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 5.47% | 5.34% | 60.00% | 16.52% | 1.97 | 3.01 |
| safety+math+code+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 7.68% | 34.22% | 16.19% | 1.98 | 3.03 |


#### 【シード別詳細】 メイン実験 - Method: ties, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 17.81% | 11.57% | 130316.85 | 178652.70 |
| safety+math+code+medical | ties | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 13.91% | 12.47% | 450010.32 | 520854.54 |
| safety+math+code+medical | ties | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 17.81% | 12.30% | 70340.88 | 114680.44 |
| safety+math+code+medical | ties | 1.00 | 42.0 | 0.00% | 3.75% | 10.81% | 61.56% | 48.56% | 1.86 | 2.78 |
| safety+math+code+medical | ties | 1.00 | 43.0 | 0.00% | 4.84% | 5.18% | 59.84% | 16.94% | 1.92 | 2.86 |
| safety+math+code+medical | ties | 1.00 | 44.0 | 0.00% | 0.31% | 2.66% | 35.47% | 25.90% | 1.93 | 2.88 |


---

## 3. ベースモデル (Base Models) 実験結果
マージ前のベース・ドメインモデルおよび Safety FT モデルの結果独立一覧表。

#### 【集計】 ベースモデル評価 (Mean ± Std)

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 64.41 ± 0.00% | 2.81 ± 0.00% | 9.60 ± 0.00% | 62.03 ± 0.00% | 25.95 ± 0.00% | 2.15 ± 0.00 | 2.52 ± 0.91 |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 0.00 ± 0.00% | 4.58 ± 1.15% | 7.88 ± 1.72% | 60.21 ± 1.26% | 16.17 ± 0.46% | 1.96 ± 0.04 | - |
| Base (WizardCoder) | Base (WizardCoder) | N/A | 72.81 ± 0.00% | 4.53 ± 0.00% | 34.07 ± 0.00% | 54.06 ± 0.00% | 19.68 ± 0.00% | 1.41 ± 0.00 | 2.94 ± 0.00 |
| Base (WizardMath) | Base (WizardMath) | N/A | 64.93 ± 0.00% | 22.34 ± 0.00% | 9.07 ± 0.00% | 60.62 ± 0.00% | 18.36 ± 0.00% | 1.90 ± 0.00 | 2.57 ± 0.00 |


#### 【シード別詳細】 ベースモデル評価 (Seeds 42, 43, 44)

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 42.0 | - | - | - | - | - | - | 2.90 |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 43.0 | - | - | - | - | - | - | 3.01 |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | 44.0 | - | - | - | - | - | - | 3.03 |
| Base (MedAlpaca) | Base (MedAlpaca) | N/A | nan | 64.41% | 2.81% | 9.60% | 62.03% | 25.95% | 2.15 | 1.15 |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 42.0 | 0.00% | 5.00% | 9.25% | 61.56% | 15.73% | 1.91 | - |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 43.0 | 0.00% | 5.47% | 5.95% | 60.00% | 16.64% | 1.97 | - |
| Base (SafetyFT) | Base (SafetyFT) | N/A | 44.0 | 0.00% | 3.28% | 8.46% | 59.06% | 16.16% | 1.98 | - |
| Base (WizardCoder) | Base (WizardCoder) | N/A | nan | 72.81% | 4.53% | 34.07% | 54.06% | 19.68% | 1.41 | 2.94 |
| Base (WizardMath) | Base (WizardMath) | N/A | nan | 64.93% | 22.34% | 9.07% | 60.62% | 18.36% | 1.90 | 2.57 |


---

## 4. Alpha スイープ実験結果
各 Alpha パラメータごとの Safety / Utility スコア推移表。

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.00 | 34.44 ± 0.50% | 20.10 ± 0.09% | 3.54 ± 3.70% | 61.41 ± 0.00% | 28.82 ± 9.38% | 1.87 ± 0.00 | 2.52 ± 0.00 |
| safety+math | diagonal_sst_main | 0.20 | 32.10 ± 0.41% | 21.41 ± 0.41% | 5.07 ± 2.51% | 61.30 ± 0.09% | 25.35 ± 10.87% | 1.80 ± 0.00 | 2.47 ± 0.00 |
| safety+math | diagonal_sst_main | 0.40 | 32.38 ± 1.37% | 21.77 ± 1.27% | 7.57 ± 0.55% | 60.99 ± 0.24% | 31.79 ± 11.84% | 1.74 ± 0.00 | 2.44 ± 0.01 |
| safety+math | diagonal_sst_main | 0.60 | 17.39 ± 5.23% | 19.95 ± 0.70% | 8.97 ± 0.51% | 60.89 ± 0.63% | 27.54 ± 8.99% | 1.70 ± 0.01 | 2.42 ± 0.02 |
| safety+math | diagonal_sst_main | 0.80 | 2.96 ± 1.82% | 16.25 ± 1.49% | 10.74 ± 1.09% | 61.77 ± 0.65% | 23.23 ± 6.39% | 1.69 ± 0.02 | 2.44 ± 0.04 |
| safety+math | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 13.28 ± 3.75% | 9.60 ± 2.12% | 61.61 ± 0.48% | 26.63 ± 6.45% | 1.72 ± 0.04 | 2.51 ± 0.09 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | diagonal_sst_main | 0.00 | 42.0 | 33.87% | 20.16% | 1.41% | 61.41% | 18.61% | 1.87 | 2.52 |
| safety+math | diagonal_sst_main | 0.00 | 43.0 | 34.69% | 20.16% | 7.81% | 61.41% | 37.05% | 1.87 | 2.52 |
| safety+math | diagonal_sst_main | 0.00 | 44.0 | 34.77% | 20.00% | 1.41% | 61.41% | 30.79% | 1.87 | 2.52 |
| safety+math | diagonal_sst_main | 0.20 | 42.0 | 31.95% | 21.88% | 2.19% | 61.25% | 18.70% | 1.80 | 2.47 |
| safety+math | diagonal_sst_main | 0.20 | 43.0 | 32.56% | 21.25% | 6.28% | 61.41% | 19.45% | 1.79 | 2.47 |
| safety+math | diagonal_sst_main | 0.20 | 44.0 | 31.78% | 21.09% | 6.75% | 61.25% | 37.89% | 1.80 | 2.47 |
| safety+math | diagonal_sst_main | 0.40 | 42.0 | 33.17% | 22.66% | 8.14% | 61.25% | 18.56% | 1.74 | 2.43 |
| safety+math | diagonal_sst_main | 0.40 | 43.0 | 30.80% | 20.31% | 7.04% | 60.78% | 35.41% | 1.74 | 2.44 |
| safety+math | diagonal_sst_main | 0.40 | 44.0 | 33.18% | 22.34% | 7.52% | 60.94% | 41.39% | 1.74 | 2.44 |
| safety+math | diagonal_sst_main | 0.60 | 42.0 | 23.08% | 20.62% | 8.75% | 61.25% | 18.48% | 1.70 | 2.40 |
| safety+math | diagonal_sst_main | 0.60 | 43.0 | 16.28% | 19.22% | 8.61% | 60.16% | 36.46% | 1.70 | 2.44 |
| safety+math | diagonal_sst_main | 0.60 | 44.0 | 12.81% | 20.00% | 9.55% | 61.25% | 27.68% | 1.71 | 2.43 |
| safety+math | diagonal_sst_main | 0.80 | 42.0 | 3.99% | 17.66% | 10.64% | 62.50% | 19.01% | 1.68 | 2.40 |
| safety+math | diagonal_sst_main | 0.80 | 43.0 | 0.86% | 14.69% | 9.71% | 61.25% | 30.57% | 1.70 | 2.48 |
| safety+math | diagonal_sst_main | 0.80 | 44.0 | 4.02% | 16.41% | 11.89% | 61.56% | 20.10% | 1.70 | 2.45 |
| safety+math | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 17.50% | 11.74% | 62.03% | 19.30% | 1.68 | 2.42 |
| safety+math | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 10.31% | 7.50% | 61.09% | 31.49% | 1.75 | 2.59 |
| safety+math | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 12.03% | 9.55% | 61.72% | 29.09% | 1.73 | 2.53 |


---

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.00 | 0.08 ± 0.00% | 0.26 ± 0.18% | 0.00 ± 0.00% | 54.43 ± 0.36% | 14.03 ± 0.00% | 203.70 ± 0.00 | 28.06 ± 0.00 |
| safety+code | diagonal_sst_main | 0.20 | 0.08 ± 0.08% | 0.10 ± 0.18% | 0.00 ± 0.00% | 55.00 ± 1.13% | 14.63 ± 0.17% | 117.61 ± 25.66 | 21.06 ± 2.04 |
| safety+code | diagonal_sst_main | 0.40 | 0.32 ± 0.14% | 0.89 ± 0.59% | 0.00 ± 0.00% | 54.53 ± 0.47% | 14.69 ± 0.13% | 171.98 ± 71.56 | 19.91 ± 2.79 |
| safety+code | diagonal_sst_main | 0.60 | 1.10 ± 0.47% | 0.83 ± 0.09% | 0.00 ± 0.00% | 54.84 ± 1.02% | 12.60 ± 0.09% | 185.23 ± 93.56 | 23.14 ± 4.56 |
| safety+code | diagonal_sst_main | 0.80 | 0.81 ± 0.09% | 0.89 ± 0.45% | 0.00 ± 0.00% | 54.64 ± 1.81% | 12.11 ± 0.35% | 54.38 ± 16.66 | 20.76 ± 1.35 |
| safety+code | diagonal_sst_main | 1.00 | 0.00 ± 0.00% | 0.62 ± 0.31% | 0.00 ± 0.00% | 32.19 ± 8.93% | 10.55 ± 0.30% | 258.23 ± 35.18 | 166.09 ± 78.86 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | diagonal_sst_main | 0.00 | 42.0 | 0.08% | 0.16% | 0.00% | 54.22% | 14.03% | 203.70 | 28.06 |
| safety+code | diagonal_sst_main | 0.00 | 43.0 | 0.08% | 0.47% | 0.00% | 54.84% | 14.03% | 203.70 | 28.06 |
| safety+code | diagonal_sst_main | 0.00 | 44.0 | 0.08% | 0.16% | 0.00% | 54.22% | 14.03% | 203.70 | 28.06 |
| safety+code | diagonal_sst_main | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 56.25% | 14.74% | 100.08 | 18.98 |
| safety+code | diagonal_sst_main | 0.20 | 43.0 | 0.00% | 0.00% | 0.00% | 54.06% | 14.43% | 147.06 | 23.06 |
| safety+code | diagonal_sst_main | 0.20 | 44.0 | 0.16% | 0.31% | 0.00% | 54.69% | 14.71% | 105.69 | 21.13 |
| safety+code | diagonal_sst_main | 0.40 | 42.0 | 0.24% | 0.47% | 0.00% | 54.53% | 14.57% | 122.82 | 17.14 |
| safety+code | diagonal_sst_main | 0.40 | 43.0 | 0.24% | 1.56% | 0.00% | 54.06% | 14.67% | 254.08 | 22.73 |
| safety+code | diagonal_sst_main | 0.40 | 44.0 | 0.48% | 0.62% | 0.00% | 55.00% | 14.83% | 139.04 | 19.87 |
| safety+code | diagonal_sst_main | 0.60 | 42.0 | 1.29% | 0.78% | 0.00% | 54.69% | 12.70% | 113.07 | 18.31 |
| safety+code | diagonal_sst_main | 0.60 | 43.0 | 1.44% | 0.94% | 0.00% | 53.91% | 12.57% | 290.94 | 27.36 |
| safety+code | diagonal_sst_main | 0.60 | 44.0 | 0.57% | 0.78% | 0.00% | 55.94% | 12.52% | 151.69 | 23.75 |
| safety+code | diagonal_sst_main | 0.80 | 42.0 | 0.87% | 0.62% | 0.00% | 52.97% | 11.70% | 39.87 | 19.78 |
| safety+code | diagonal_sst_main | 0.80 | 43.0 | 0.71% | 1.41% | 0.00% | 54.38% | 12.33% | 72.57 | 20.20 |
| safety+code | diagonal_sst_main | 0.80 | 44.0 | 0.87% | 0.62% | 0.00% | 56.56% | 12.29% | 50.70 | 22.30 |
| safety+code | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.94% | 0.00% | 39.38% | 10.84% | 295.43 | 241.91 |
| safety+code | diagonal_sst_main | 1.00 | 43.0 | 0.00% | 0.62% | 0.00% | 22.19% | 10.24% | 253.76 | 84.50 |
| safety+code | diagonal_sst_main | 1.00 | 44.0 | 0.00% | 0.31% | 0.00% | 35.00% | 10.57% | 225.51 | 171.87 |


---

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.97 ± 7.85% | 11.82 ± 0.06% | 200412.22 ± 0.00 | 195954.54 ± 5.55 |
| safety+medical | diagonal_sst_main | 0.20 | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 20.52 ± 0.55% | 12.25 ± 0.18% | 91035.76 ± 17521.94 | 74814.15 ± 18677.97 |
| safety+medical | diagonal_sst_main | 0.40 | 0.19 ± 0.20% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.70 ± 5.10% | 12.17 ± 0.22% | 137303.69 ± 20106.41 | 95595.75 ± 12745.83 |
| safety+medical | diagonal_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 41.15 ± 23.13% | 11.95 ± 0.28% | 79783.06 ± 18826.86 | 89052.84 ± 40211.85 |
| safety+medical | diagonal_sst_main | 0.80 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.91 ± 5.82% | 11.62 ± 0.55% | 139531.35 ± 112079.91 | 227857.25 ± 297572.09 |
| safety+medical | diagonal_sst_main | 1.00 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.55 ± 15.93% | 11.74 ± 0.55% | 139537.68 ± 165148.85 | 102521.68 ± 83446.86 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | diagonal_sst_main | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 42.50% | 11.85% | 200412.22 | 195948.13 |
| safety+medical | diagonal_sst_main | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 28.91% | 11.85% | 200412.22 | 195957.74 |
| safety+medical | diagonal_sst_main | 0.00 | 44.0 | 0.00% | 0.00% | 0.00% | 42.50% | 11.75% | 200412.22 | 195957.74 |
| safety+medical | diagonal_sst_main | 0.20 | 42.0 | 0.16% | 0.00% | 0.00% | 20.00% | 12.45% | 110445.00 | 88606.01 |
| safety+medical | diagonal_sst_main | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 20.47% | 12.14% | 86278.81 | 82278.05 |
| safety+medical | diagonal_sst_main | 0.20 | 44.0 | 0.16% | 0.00% | 0.00% | 21.09% | 12.14% | 76383.47 | 53558.39 |
| safety+medical | diagonal_sst_main | 0.40 | 42.0 | 0.40% | 0.00% | 0.00% | 56.41% | 12.23% | 160455.20 | 108563.37 |
| safety+medical | diagonal_sst_main | 0.40 | 43.0 | 0.16% | 0.00% | 0.00% | 56.88% | 12.35% | 127235.73 | 83083.94 |
| safety+medical | diagonal_sst_main | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 47.81% | 11.93% | 124220.16 | 95139.94 |
| safety+medical | diagonal_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 51.25% | 11.92% | 95009.90 | 79407.33 |
| safety+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 14.69% | 12.24% | 85606.83 | 133210.26 |
| safety+medical | diagonal_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 57.50% | 11.68% | 58732.45 | 54540.92 |
| safety+medical | diagonal_sst_main | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 16.88% | 12.23% | 100778.33 | 8865.83 |
| safety+medical | diagonal_sst_main | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 14.37% | 11.46% | 265845.03 | 566658.91 |
| safety+medical | diagonal_sst_main | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 25.47% | 11.17% | 51970.68 | 108047.03 |
| safety+medical | diagonal_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 20.31% | 12.25% | 22655.80 | 7801.03 |
| safety+medical | diagonal_sst_main | 1.00 | 43.0 | 0.08% | 0.00% | 0.00% | 40.62% | 11.16% | 328470.43 | 165191.36 |
| safety+medical | diagonal_sst_main | 1.00 | 44.0 | 0.08% | 0.00% | 0.00% | 51.72% | 11.81% | 67486.81 | 134572.64 |


---

### Alpha スイープ: Method = diagonal_sst_main, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: diagonal_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.61 ± 21.47% | 10.46 ± 0.16% | 29408.88 ± 0.00 | 73003.90 ± 0.00 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 0.05 ± 0.05% | 0.68 ± 0.48% | 0.00 ± 0.00% | 23.80 ± 4.42% | 12.30 ± 0.87% | 5113.50 ± 826.44 | 15825.46 ± 2469.63 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 0.00 ± 0.00% | 1.09 ± 0.83% | 0.00 ± 0.00% | 20.26 ± 1.88% | 11.75 ± 0.22% | 2684.19 ± 461.76 | 1266.19 ± 121.35 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 0.00 ± 0.00% | 0.73 ± 0.72% | 0.00 ± 0.00% | 44.17 ± 7.44% | 10.22 ± 0.47% | 453.77 ± 82.57 | 109.69 ± 29.01 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 0.13 ± 0.05% | 0.47 ± 0.31% | 0.00 ± 0.00% | 55.00 ± 1.65% | 9.53 ± 0.96% | 166.19 ± 72.34 | 51.23 ± 17.42 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 0.16 ± 0.00% | 0.57 ± 0.74% | 0.00 ± 0.00% | 54.74 ± 4.11% | 17.30 ± 4.28% | 109.78 ± 56.64 | 47.15 ± 20.38 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: diagonal_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 42.0 | 0.16% | 0.00% | 0.00% | 56.41% | 10.32% | 29408.88 | 73003.90 |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 43.0 | 0.16% | 0.00% | 0.00% | 19.22% | 10.42% | 29408.88 | 73003.90 |
| safety+math+code+medical | diagonal_sst_main | 0.00 | 44.0 | 0.16% | 0.00% | 0.00% | 19.22% | 10.63% | 29408.88 | 73003.90 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 42.0 | 0.08% | 1.09% | 0.00% | 28.91% | 11.96% | 5774.64 | 18344.40 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 43.0 | 0.00% | 0.16% | 0.00% | 21.25% | 13.29% | 4186.96 | 13408.29 |
| safety+math+code+medical | diagonal_sst_main | 0.20 | 44.0 | 0.08% | 0.78% | 0.00% | 21.25% | 11.65% | 5378.88 | 15723.68 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 42.0 | 0.00% | 2.03% | 0.00% | 22.03% | 11.55% | 2194.78 | 1406.28 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 43.0 | 0.00% | 0.47% | 0.00% | 20.47% | 11.71% | 3112.14 | 1193.53 |
| safety+math+code+medical | diagonal_sst_main | 0.40 | 44.0 | 0.00% | 0.78% | 0.00% | 18.28% | 11.98% | 2745.66 | 1198.75 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 42.0 | 0.00% | 1.56% | 0.00% | 37.50% | 10.44% | 535.18 | 141.16 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 43.0 | 0.00% | 0.31% | 0.00% | 52.19% | 10.55% | 370.08 | 84.01 |
| safety+math+code+medical | diagonal_sst_main | 0.60 | 44.0 | 0.00% | 0.31% | 0.00% | 42.81% | 9.68% | 456.06 | 103.91 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 42.0 | 0.08% | 0.78% | 0.00% | 54.38% | 10.57% | 240.86 | 69.58 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 43.0 | 0.16% | 0.47% | 0.00% | 56.88% | 9.33% | 96.43 | 34.93 |
| safety+math+code+medical | diagonal_sst_main | 0.80 | 44.0 | 0.16% | 0.16% | 0.00% | 53.75% | 8.69% | 161.28 | 49.18 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 42.0 | 0.16% | 1.41% | 0.00% | 56.88% | 12.36% | 168.96 | 68.21 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 43.0 | 0.16% | 0.31% | 0.00% | 57.34% | 19.59% | 56.08 | 27.53 |
| safety+math+code+medical | diagonal_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 50.00% | 19.95% | 104.29 | 45.71 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.00 | 34.17 ± 0.52% | 20.10 ± 0.09% | 3.54 ± 3.70% | 61.41 ± 0.00% | 35.24 ± 7.76% | 1.87 ± 0.00 | 2.52 ± 0.00 |
| safety+math | data_free_sst_main | 0.20 | 32.95 ± 1.10% | 21.09 ± 0.16% | 6.21 ± 2.94% | 61.09 ± 0.31% | 35.84 ± 10.21% | 1.86 ± 0.01 | 2.55 ± 0.01 |
| safety+math | data_free_sst_main | 0.40 | 32.85 ± 1.35% | 22.34 ± 0.83% | 7.62 ± 1.04% | 60.78 ± 0.41% | 37.56 ± 7.07% | 1.86 ± 0.01 | 2.60 ± 0.02 |
| safety+math | data_free_sst_main | 0.60 | 14.70 ± 3.30% | 21.46 ± 0.45% | 8.34 ± 0.71% | 61.04 ± 0.33% | 34.60 ± 8.29% | 1.87 ± 0.02 | 2.65 ± 0.03 |
| safety+math | data_free_sst_main | 0.80 | 16.02 ± 6.78% | 18.70 ± 0.63% | 9.59 ± 1.36% | 60.99 ± 0.59% | 33.77 ± 9.14% | 1.89 ± 0.03 | 2.73 ± 0.05 |
| safety+math | data_free_sst_main | 1.00 | 11.55 ± 9.34% | 19.06 ± 0.27% | 9.35 ± 1.45% | 61.41 ± 0.56% | 34.69 ± 9.06% | 1.93 ± 0.04 | 2.83 ± 0.08 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | data_free_sst_main | 0.00 | 42.0 | 33.87% | 20.16% | 1.41% | 61.41% | 44.21% | 1.87 | 2.52 |
| safety+math | data_free_sst_main | 0.00 | 43.0 | 33.87% | 20.16% | 7.81% | 61.41% | 30.74% | 1.87 | 2.52 |
| safety+math | data_free_sst_main | 0.00 | 44.0 | 34.77% | 20.00% | 1.41% | 61.41% | 30.79% | 1.87 | 2.52 |
| safety+math | data_free_sst_main | 0.20 | 42.0 | 34.08% | 21.25% | 2.81% | 61.09% | 44.45% | 1.85 | 2.55 |
| safety+math | data_free_sst_main | 0.20 | 43.0 | 32.89% | 21.09% | 7.98% | 61.41% | 38.51% | 1.87 | 2.56 |
| safety+math | data_free_sst_main | 0.20 | 44.0 | 31.88% | 20.94% | 7.83% | 60.78% | 24.57% | 1.86 | 2.56 |
| safety+math | data_free_sst_main | 0.40 | 42.0 | 31.68% | 22.03% | 8.76% | 60.31% | 44.83% | 1.85 | 2.58 |
| safety+math | data_free_sst_main | 0.40 | 43.0 | 32.54% | 23.28% | 7.36% | 61.09% | 30.72% | 1.87 | 2.61 |
| safety+math | data_free_sst_main | 0.40 | 44.0 | 34.34% | 21.72% | 6.74% | 60.94% | 37.13% | 1.87 | 2.60 |
| safety+math | data_free_sst_main | 0.60 | 42.0 | 10.97% | 21.72% | 9.08% | 60.94% | 44.16% | 1.85 | 2.62 |
| safety+math | data_free_sst_main | 0.60 | 43.0 | 15.92% | 21.72% | 7.67% | 61.41% | 30.28% | 1.88 | 2.67 |
| safety+math | data_free_sst_main | 0.60 | 44.0 | 17.22% | 20.94% | 8.29% | 60.78% | 29.36% | 1.88 | 2.67 |
| safety+math | data_free_sst_main | 0.80 | 42.0 | 9.45% | 17.97% | 9.24% | 61.25% | 44.33% | 1.86 | 2.67 |
| safety+math | data_free_sst_main | 0.80 | 43.0 | 15.63% | 19.06% | 8.44% | 61.41% | 28.68% | 1.90 | 2.75 |
| safety+math | data_free_sst_main | 0.80 | 44.0 | 22.99% | 19.06% | 11.10% | 60.31% | 28.30% | 1.91 | 2.76 |
| safety+math | data_free_sst_main | 1.00 | 42.0 | 0.87% | 18.91% | 10.34% | 61.25% | 43.95% | 1.89 | 2.74 |
| safety+math | data_free_sst_main | 1.00 | 43.0 | 18.18% | 19.38% | 7.69% | 62.03% | 34.30% | 1.95 | 2.86 |
| safety+math | data_free_sst_main | 1.00 | 44.0 | 15.59% | 18.91% | 10.02% | 60.94% | 25.83% | 1.96 | 2.89 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.00 | 0.08 ± 0.00% | 0.26 ± 0.18% | 0.00 ± 0.00% | 54.43 ± 0.36% | 14.10 ± 0.06% | 203.70 ± 0.00 | 28.06 ± 0.00 |
| safety+code | data_free_sst_main | 0.20 | 0.11 ± 0.05% | 0.21 ± 0.18% | 0.00 ± 0.00% | 54.17 ± 0.39% | 15.61 ± 0.17% | 78.83 ± 14.75 | 16.19 ± 1.34 |
| safety+code | data_free_sst_main | 0.40 | 0.08 ± 0.08% | 0.10 ± 0.18% | 0.00 ± 0.00% | 54.69 ± 0.47% | 15.46 ± 0.54% | 74.73 ± 27.01 | 16.98 ± 3.32 |
| safety+code | data_free_sst_main | 0.60 | 0.03 ± 0.05% | 0.16 ± 0.27% | 0.00 ± 0.00% | 55.36 ± 3.82% | 14.94 ± 0.26% | 112.57 ± 56.38 | 23.38 ± 6.19 |
| safety+code | data_free_sst_main | 0.80 | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 45.62 ± 13.50% | 13.22 ± 0.71% | 389.89 ± 255.30 | 54.67 ± 23.22 |
| safety+code | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.16 ± 0.16% | 0.00 ± 0.00% | 42.86 ± 16.15% | 12.18 ± 0.07% | 17815.49 ± 16468.76 | 2046.19 ± 1654.26 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | data_free_sst_main | 0.00 | 42.0 | 0.08% | 0.16% | 0.00% | 54.22% | 14.13% | 203.70 | 28.06 |
| safety+code | data_free_sst_main | 0.00 | 43.0 | 0.08% | 0.47% | 0.00% | 54.84% | 14.03% | 203.70 | 28.06 |
| safety+code | data_free_sst_main | 0.00 | 44.0 | 0.08% | 0.16% | 0.00% | 54.22% | 14.13% | 203.70 | 28.06 |
| safety+code | data_free_sst_main | 0.20 | 42.0 | 0.16% | 0.31% | 0.00% | 54.22% | 15.64% | 85.84 | 17.07 |
| safety+code | data_free_sst_main | 0.20 | 43.0 | 0.08% | 0.31% | 0.00% | 54.53% | 15.76% | 61.89 | 14.65 |
| safety+code | data_free_sst_main | 0.20 | 44.0 | 0.08% | 0.00% | 0.00% | 53.75% | 15.42% | 88.77 | 16.85 |
| safety+code | data_free_sst_main | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 55.16% | 15.07% | 86.59 | 19.01 |
| safety+code | data_free_sst_main | 0.40 | 43.0 | 0.00% | 0.31% | 0.00% | 54.22% | 16.07% | 43.83 | 13.14 |
| safety+code | data_free_sst_main | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 54.69% | 15.23% | 93.78 | 18.77 |
| safety+code | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 56.56% | 14.71% | 128.94 | 25.36 |
| safety+code | data_free_sst_main | 0.60 | 43.0 | 0.00% | 0.47% | 0.00% | 51.09% | 14.90% | 49.82 | 16.44 |
| safety+code | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 58.44% | 15.21% | 158.96 | 28.34 |
| safety+code | data_free_sst_main | 0.80 | 42.0 | 0.08% | 0.00% | 0.00% | 55.00% | 13.73% | 459.29 | 60.90 |
| safety+code | data_free_sst_main | 0.80 | 43.0 | 0.16% | 0.00% | 0.00% | 30.16% | 13.52% | 107.07 | 28.96 |
| safety+code | data_free_sst_main | 0.80 | 44.0 | 0.16% | 0.00% | 0.00% | 51.72% | 12.40% | 603.31 | 74.14 |
| safety+code | data_free_sst_main | 1.00 | 42.0 | 0.00% | 0.00% | 0.00% | 52.50% | 12.26% | 15402.26 | 2349.27 |
| safety+code | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.31% | 0.00% | 24.22% | 12.17% | 2686.49 | 261.35 |
| safety+code | data_free_sst_main | 1.00 | 44.0 | 0.08% | 0.16% | 0.00% | 51.88% | 12.11% | 35357.72 | 3527.96 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.00 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.97 ± 7.85% | 11.89 ± 0.15% | 200412.44 ± 0.39 | 195954.54 ± 5.55 |
| safety+medical | data_free_sst_main | 0.20 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 19.22 ± 3.54% | 11.92 ± 0.33% | 173037.71 ± 49082.15 | 163048.68 ± 25149.98 |
| safety+medical | data_free_sst_main | 0.40 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.49 ± 7.49% | 12.68 ± 0.39% | 432792.94 ± 79129.29 | 340350.46 ± 50490.28 |
| safety+medical | data_free_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.49 ± 1.80% | 12.72 ± 0.20% | 154475.14 ± 80159.01 | 118397.35 ± 35122.34 |
| safety+medical | data_free_sst_main | 0.80 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 51.20 ± 9.03% | 12.33 ± 0.28% | 204228.26 ± 108917.97 | 197501.22 ± 101088.17 |
| safety+medical | data_free_sst_main | 1.00 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.20 ± 22.92% | 12.53 ± 0.09% | 303013.60 ± 160352.85 | 130002.00 ± 53693.74 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | data_free_sst_main | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 42.50% | 12.06% | 200412.89 | 195948.13 |
| safety+medical | data_free_sst_main | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 28.91% | 11.76% | 200412.22 | 195957.74 |
| safety+medical | data_free_sst_main | 0.00 | 44.0 | 0.00% | 0.00% | 0.00% | 42.50% | 11.85% | 200412.22 | 195957.74 |
| safety+medical | data_free_sst_main | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 22.50% | 11.78% | 153445.39 | 149303.69 |
| safety+medical | data_free_sst_main | 0.20 | 43.0 | 0.00% | 0.00% | 0.00% | 15.47% | 11.68% | 228889.95 | 192075.81 |
| safety+medical | data_free_sst_main | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 19.69% | 12.29% | 136777.78 | 147766.54 |
| safety+medical | data_free_sst_main | 0.40 | 42.0 | 0.00% | 0.00% | 0.00% | 37.97% | 12.32% | 388503.16 | 313498.25 |
| safety+medical | data_free_sst_main | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 24.84% | 13.09% | 385726.14 | 308960.42 |
| safety+medical | data_free_sst_main | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 37.66% | 12.61% | 524149.50 | 398592.72 |
| safety+medical | data_free_sst_main | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 54.53% | 12.78% | 204138.99 | 156315.42 |
| safety+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 54.53% | 12.50% | 62000.09 | 86978.63 |
| safety+medical | data_free_sst_main | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 51.41% | 12.89% | 197286.35 | 111898.00 |
| safety+medical | data_free_sst_main | 0.80 | 42.0 | 0.08% | 0.00% | 0.00% | 56.72% | 12.58% | 285977.66 | 280031.02 |
| safety+medical | data_free_sst_main | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 40.78% | 12.36% | 246123.73 | 227723.66 |
| safety+medical | data_free_sst_main | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 56.09% | 12.03% | 80583.39 | 84748.97 |
| safety+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 56.88% | 12.43% | 415600.47 | 147036.09 |
| safety+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 12.81% | 12.59% | 374023.67 | 173112.44 |
| safety+medical | data_free_sst_main | 1.00 | 44.0 | 0.16% | 0.00% | 0.00% | 23.91% | 12.56% | 119416.65 | 69857.47 |


---

### Alpha スイープ: Method = data_free_sst_main, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: data_free_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.00 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 31.61 ± 21.47% | 10.46 ± 0.06% | 29408.90 ± 0.02 | 73004.68 ± 1.35 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 0.13 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 26.30 ± 26.07% | 10.93 ± 0.24% | 28883.36 ± 3514.80 | 78052.79 ± 10754.03 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 30.52 ± 23.21% | 11.63 ± 0.24% | 24950.09 ± 2368.54 | 57646.17 ± 16169.77 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 40.00 ± 18.66% | 11.61 ± 0.31% | 17938.54 ± 3918.72 | 37505.01 ± 22671.13 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 52.60 ± 8.34% | 12.23 ± 1.32% | 13402.49 ± 2042.70 | 20723.75 ± 7418.20 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 53.85 ± 4.44% | 11.59 ± 0.56% | 13257.09 ± 4123.52 | 16581.99 ± 3829.08 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: data_free_sst_main, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | data_free_sst_main | 0.00 | 42.0 | 0.16% | 0.00% | 0.00% | 56.41% | 10.52% | 29408.88 | 73003.90 |
| safety+math+code+medical | data_free_sst_main | 0.00 | 43.0 | 0.16% | 0.00% | 0.00% | 19.22% | 10.42% | 29408.88 | 73003.90 |
| safety+math+code+medical | data_free_sst_main | 0.00 | 44.0 | 0.16% | 0.00% | 0.00% | 19.22% | 10.42% | 29408.92 | 73006.24 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 56.41% | 10.65% | 32937.59 | 83622.44 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 11.41% | 11.07% | 26694.20 | 65656.33 |
| safety+math+code+medical | data_free_sst_main | 0.20 | 44.0 | 0.24% | 0.00% | 0.00% | 11.09% | 11.07% | 27018.30 | 84879.59 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 42.0 | 0.00% | 0.00% | 0.00% | 57.19% | 11.48% | 22713.93 | 57739.94 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 14.84% | 11.49% | 27431.87 | 41429.72 |
| safety+math+code+medical | data_free_sst_main | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 19.53% | 11.90% | 24704.48 | 73768.85 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 57.66% | 11.96% | 14544.18 | 28970.80 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 20.47% | 11.38% | 22227.08 | 20339.54 |
| safety+math+code+medical | data_free_sst_main | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 41.88% | 11.49% | 17044.37 | 63204.70 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.75% | 12542.75 | 18508.55 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 42.97% | 11.67% | 15734.53 | 14665.50 |
| safety+math+code+medical | data_free_sst_main | 0.80 | 44.0 | 0.00% | 0.00% | 0.00% | 57.34% | 11.28% | 11930.19 | 28997.20 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 42.0 | 0.08% | 0.00% | 0.00% | 55.16% | 10.98% | 17981.87 | 20695.07 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 43.0 | 0.00% | 0.00% | 0.00% | 48.91% | 11.76% | 11405.37 | 13120.54 |
| safety+math+code+medical | data_free_sst_main | 1.00 | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 12.05% | 10384.04 | 15930.35 |


---

### Alpha スイープ: Method = mergealign, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: mergealign, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.85 ± 0.35% | - | - |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: mergealign, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+math | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 57.50% | 14.25% | - | - |
| safety+math | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |


---

### Alpha スイープ: Method = mergealign, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: mergealign, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 13.64 ± 0.00% | - | - |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: mergealign, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+code | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+code | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |


---

### Alpha スイープ: Method = mergealign, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: mergealign, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 57.50 ± 0.00% | 11.98 ± 3.31% | - | - |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: mergealign, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | mergealign | N/A | 42.0 | 0.00% | 0.00% | 0.00% | 57.50% | 13.64% | - | - |
| safety+medical | mergealign | N/A | 43.0 | 0.00% | 0.00% | 0.00% | 57.50% | 14.13% | - | - |
| safety+medical | mergealign | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 57.50% | 8.16% | - | - |


---

### Alpha スイープ: Method = led_merging, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: led_merging, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 2.67 ± 0.05% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.67 ± 0.07% | 1.61 ± 0.00 | 2.16 ± 0.00 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: led_merging, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | led_merging | N/A | 42.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.63% | 1.61 | 2.16 |
| safety+math | led_merging | N/A | 43.0 | 2.72% | 1.41% | 5.62% | 56.25% | 28.75% | 1.61 | 2.16 |
| safety+math | led_merging | N/A | 44.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.63% | 1.61 | 2.16 |


---

### Alpha スイープ: Method = led_merging, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: led_merging, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 2.64 ± 0.00% | 3.07 ± 1.44% | 5.74 ± 0.10% | 59.90 ± 3.16% | 28.65 ± 0.08% | 1.61 ± 0.00 | 2.16 ± 0.00 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: led_merging, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | led_merging | N/A | 42.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.63% | 1.61 | 2.16 |
| safety+code | led_merging | N/A | 43.0 | 2.64% | 1.41% | 5.62% | 56.25% | 28.74% | 1.61 | 2.16 |
| safety+code | led_merging | N/A | 44.0 | 2.64% | 3.91% | 5.79% | 61.72% | 28.58% | 1.61 | 2.16 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.00 | 30.90 ± 0.10% | 20.36 ± 0.09% | 8.46 ± 0.00% | 60.62 ± 0.00% | 37.52 ± 0.24% | 1.90 ± 0.00 | 2.57 ± 0.00 |
| safety+math | task_arithmetic | 0.20 | 31.29 ± 0.77% | 22.14 ± 0.72% | 4.24 ± 2.87% | 61.30 ± 0.24% | 36.42 ± 3.56% | 1.77 ± 0.01 | 2.47 ± 0.01 |
| safety+math | task_arithmetic | 0.40 | 14.87 ± 0.94% | 18.44 ± 0.56% | 7.53 ± 0.68% | 60.52 ± 0.36% | 33.78 ± 3.21% | 1.70 ± 0.01 | 2.42 ± 0.02 |
| safety+math | task_arithmetic | 0.60 | 2.43 ± 2.80% | 15.68 ± 0.63% | 8.87 ± 2.24% | 61.61 ± 0.18% | 32.21 ± 6.62% | 1.67 ± 0.01 | 2.44 ± 0.03 |
| safety+math | task_arithmetic | 0.80 | 0.00 ± 0.00% | 6.46 ± 1.02% | 8.75 ± 1.66% | 61.25 ± 0.27% | 29.42 ± 10.44% | 1.72 ± 0.02 | 2.57 ± 0.06 |
| safety+math | task_arithmetic | 1.00 | 0.00 ± 0.00% | 4.58 ± 0.86% | 7.38 ± 1.78% | 60.16 ± 1.18% | 23.16 ± 11.31% | 1.96 ± 0.04 | 2.98 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | task_arithmetic | 0.00 | 42.0 | 30.96% | 20.47% | 8.46% | 60.62% | 37.50% | 1.90 | 2.57 |
| safety+math | task_arithmetic | 0.00 | 43.0 | 30.96% | 20.31% | 8.46% | 60.62% | 37.30% | 1.90 | 2.57 |
| safety+math | task_arithmetic | 0.00 | 44.0 | 30.78% | 20.31% | 8.46% | 60.62% | 37.77% | 1.90 | 2.57 |
| safety+math | task_arithmetic | 0.20 | 42.0 | 31.85% | 21.72% | 0.94% | 61.56% | 32.32% | 1.77 | 2.46 |
| safety+math | task_arithmetic | 0.20 | 43.0 | 31.62% | 22.97% | 5.66% | 61.25% | 38.19% | 1.78 | 2.47 |
| safety+math | task_arithmetic | 0.20 | 44.0 | 30.41% | 21.72% | 6.13% | 61.09% | 38.75% | 1.78 | 2.47 |
| safety+math | task_arithmetic | 0.40 | 42.0 | 14.06% | 18.59% | 8.31% | 60.31% | 33.78% | 1.69 | 2.41 |
| safety+math | task_arithmetic | 0.40 | 43.0 | 14.63% | 17.81% | 7.05% | 60.94% | 30.57% | 1.70 | 2.43 |
| safety+math | task_arithmetic | 0.40 | 44.0 | 15.91% | 18.91% | 7.22% | 60.31% | 36.98% | 1.70 | 2.43 |
| safety+math | task_arithmetic | 0.60 | 42.0 | 0.16% | 15.78% | 7.21% | 61.41% | 39.79% | 1.66 | 2.41 |
| safety+math | task_arithmetic | 0.60 | 43.0 | 1.57% | 15.00% | 7.99% | 61.72% | 27.55% | 1.68 | 2.46 |
| safety+math | task_arithmetic | 0.60 | 44.0 | 5.56% | 16.25% | 11.43% | 61.72% | 29.30% | 1.68 | 2.46 |
| safety+math | task_arithmetic | 0.80 | 42.0 | 0.00% | 7.50% | 9.39% | 60.94% | 19.20% | 1.70 | 2.51 |
| safety+math | task_arithmetic | 0.80 | 43.0 | 0.00% | 5.47% | 10.00% | 61.41% | 40.07% | 1.73 | 2.61 |
| safety+math | task_arithmetic | 0.80 | 44.0 | 0.00% | 6.41% | 6.87% | 61.41% | 28.99% | 1.74 | 2.60 |
| safety+math | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.41% | 36.21% | 1.91 | 2.90 |
| safety+math | task_arithmetic | 1.00 | 43.0 | 0.00% | 5.47% | 5.34% | 60.00% | 16.63% | 1.97 | 3.01 |
| safety+math | task_arithmetic | 1.00 | 44.0 | 0.00% | 3.75% | 8.15% | 59.06% | 16.63% | 1.98 | 3.03 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.00 | 40.91 ± 0.17% | 4.58 ± 0.90% | 12.41 ± 7.77% | 57.60 ± 0.45% | 23.54 ± 0.06% | 1.36 ± 0.00 | 2.92 ± 0.00 |
| safety+code | task_arithmetic | 0.20 | 39.22 ± 0.73% | 4.06 ± 0.31% | 4.17 ± 3.61% | 55.89 ± 1.89% | 40.30 ± 3.72% | 1.42 ± 0.00 | 2.90 ± 0.00 |
| safety+code | task_arithmetic | 0.40 | 34.86 ± 1.77% | 2.45 ± 0.24% | 3.43 ± 0.68% | 55.68 ± 1.30% | 24.27 ± 5.24% | 1.76 ± 0.00 | 3.41 ± 0.01 |
| safety+code | task_arithmetic | 0.60 | 29.22 ± 3.11% | 2.08 ± 0.95% | 2.37 ± 0.67% | 56.72 ± 0.95% | 19.13 ± 0.27% | 2.32 ± 0.02 | 3.95 ± 0.02 |
| safety+code | task_arithmetic | 0.80 | 0.05 ± 0.09% | 2.03 ± 0.62% | 4.84 ± 2.84% | 56.72 ± 1.39% | 22.48 ± 5.77% | 1.91 ± 0.00 | 2.83 ± 0.01 |
| safety+code | task_arithmetic | 1.00 | 0.00 ± 0.00% | 3.02 ± 1.98% | 6.38 ± 3.63% | 53.49 ± 11.88% | 23.16 ± 11.31% | 1.96 ± 0.04 | 2.98 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | task_arithmetic | 0.00 | 42.0 | 40.86% | 4.06% | 7.93% | 57.34% | 23.58% | 1.36 | 2.92 |
| safety+code | task_arithmetic | 0.00 | 43.0 | 40.77% | 5.62% | 21.38% | 58.12% | 23.58% | 1.36 | 2.92 |
| safety+code | task_arithmetic | 0.00 | 44.0 | 41.10% | 4.06% | 7.93% | 57.34% | 23.48% | 1.36 | 2.92 |
| safety+code | task_arithmetic | 0.20 | 42.0 | 38.57% | 4.38% | 6.40% | 56.56% | 42.37% | 1.42 | 2.90 |
| safety+code | task_arithmetic | 0.20 | 43.0 | 40.01% | 3.75% | 0.00% | 53.75% | 42.51% | 1.42 | 2.90 |
| safety+code | task_arithmetic | 0.20 | 44.0 | 39.09% | 4.06% | 6.10% | 57.34% | 36.01% | 1.42 | 2.90 |
| safety+code | task_arithmetic | 0.40 | 42.0 | 36.28% | 2.66% | 3.96% | 56.72% | 22.19% | 1.76 | 3.42 |
| safety+code | task_arithmetic | 0.40 | 43.0 | 35.42% | 2.19% | 2.66% | 54.22% | 30.23% | 1.76 | 3.41 |
| safety+code | task_arithmetic | 0.40 | 44.0 | 32.87% | 2.50% | 3.66% | 56.09% | 20.39% | 1.76 | 3.41 |
| safety+code | task_arithmetic | 0.60 | 42.0 | 32.61% | 1.88% | 1.84% | 56.09% | 19.11% | 2.33 | 3.96 |
| safety+code | task_arithmetic | 0.60 | 43.0 | 26.49% | 3.12% | 3.12% | 57.81% | 19.41% | 2.30 | 3.93 |
| safety+code | task_arithmetic | 0.60 | 44.0 | 28.54% | 1.25% | 2.14% | 56.25% | 18.88% | 2.33 | 3.96 |
| safety+code | task_arithmetic | 0.80 | 42.0 | 0.00% | 2.03% | 3.35% | 57.81% | 29.14% | 1.90 | 2.81 |
| safety+code | task_arithmetic | 0.80 | 43.0 | 0.16% | 2.66% | 8.12% | 55.16% | 19.34% | 1.91 | 2.83 |
| safety+code | task_arithmetic | 0.80 | 44.0 | 0.00% | 1.41% | 3.05% | 57.19% | 18.95% | 1.91 | 2.83 |
| safety+code | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.56% | 36.23% | 1.91 | 2.90 |
| safety+code | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.78% | 2.19% | 39.84% | 16.63% | 1.97 | 3.01 |
| safety+code | task_arithmetic | 1.00 | 44.0 | 0.00% | 3.75% | 8.31% | 59.06% | 16.63% | 1.98 | 3.03 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.00 | 6.55 ± 0.14% | 3.12 ± 0.81% | 2.10 ± 0.33% | 57.97 ± 7.31% | 25.41 ± 0.26% | 1.75 ± 0.00 | 1.15 ± 0.00 |
| safety+medical | task_arithmetic | 0.20 | 0.08 ± 0.00% | 2.19 ± 0.27% | 0.00 ± 0.00% | 21.30 ± 0.39% | 12.62 ± 0.07% | 59.38 ± 0.07 | 13.75 ± 0.12 |
| safety+medical | task_arithmetic | 0.40 | 0.00 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 14.53 ± 5.01% | 12.97 ± 0.02% | 22271.90 ± 681.75 | 39156.67 ± 722.70 |
| safety+medical | task_arithmetic | 0.60 | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 37.86 ± 17.35% | 12.72 ± 0.06% | 200116.75 ± 7068.23 | 209487.62 ± 9249.30 |
| safety+medical | task_arithmetic | 0.80 | 0.00 ± 0.00% | 0.94 ± 0.41% | 0.00 ± 0.00% | 29.95 ± 5.85% | 12.02 ± 0.24% | 1105.76 ± 231.85 | 397.75 ± 60.59 |
| safety+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.07% | 6.38 ± 3.63% | 53.49 ± 11.88% | 23.13 ± 11.35% | 1.96 ± 0.04 | 2.98 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | task_arithmetic | 0.00 | 42.0 | 6.46% | 2.66% | 2.29% | 62.19% | 25.21% | 1.75 | 1.15 |
| safety+medical | task_arithmetic | 0.00 | 43.0 | 6.71% | 4.06% | 1.72% | 49.53% | 25.33% | 1.75 | 1.15 |
| safety+medical | task_arithmetic | 0.00 | 44.0 | 6.47% | 2.66% | 2.29% | 62.19% | 25.70% | 1.75 | 1.15 |
| safety+medical | task_arithmetic | 0.20 | 42.0 | 0.08% | 2.34% | 0.00% | 21.25% | 12.59% | 59.44 | 13.62 |
| safety+medical | task_arithmetic | 0.20 | 43.0 | 0.08% | 1.88% | 0.00% | 21.72% | 12.58% | 59.31 | 13.85 |
| safety+medical | task_arithmetic | 0.20 | 44.0 | 0.08% | 2.34% | 0.00% | 20.94% | 12.70% | 59.40 | 13.78 |
| safety+medical | task_arithmetic | 0.40 | 42.0 | 0.00% | 0.00% | 0.00% | 11.56% | 12.98% | 21486.95 | 38369.71 |
| safety+medical | task_arithmetic | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 20.31% | 12.95% | 22612.65 | 39309.69 |
| safety+medical | task_arithmetic | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 11.72% | 12.98% | 22716.11 | 39790.61 |
| safety+medical | task_arithmetic | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 49.84% | 12.69% | 207511.45 | 220160.55 |
| safety+medical | task_arithmetic | 0.60 | 43.0 | 0.16% | 0.00% | 0.00% | 17.97% | 12.69% | 199410.83 | 203810.74 |
| safety+medical | task_arithmetic | 0.60 | 44.0 | 0.16% | 0.00% | 0.00% | 45.78% | 12.79% | 193427.97 | 204491.56 |
| safety+medical | task_arithmetic | 0.80 | 42.0 | 0.00% | 0.78% | 0.00% | 36.56% | 11.82% | 964.75 | 371.69 |
| safety+medical | task_arithmetic | 0.80 | 43.0 | 0.00% | 1.41% | 0.00% | 25.47% | 12.29% | 1373.34 | 467.01 |
| safety+medical | task_arithmetic | 0.80 | 44.0 | 0.00% | 0.62% | 0.00% | 27.81% | 11.96% | 979.18 | 354.54 |
| safety+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.56% | 36.23% | 1.91 | 2.90 |
| safety+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 0.62% | 2.19% | 39.84% | 16.53% | 1.97 | 3.01 |
| safety+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 3.75% | 8.31% | 59.06% | 16.63% | 1.98 | 3.03 |


---

### Alpha スイープ: Method = task_arithmetic, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: task_arithmetic, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.00 | 0.08 ± 0.00% | 0.10 ± 0.09% | 0.00 ± 0.00% | 21.25 ± 0.00% | 11.52 ± 0.00% | 8199.95 ± 0.00 | 12188.29 ± 0.04 |
| safety+math+code+medical | task_arithmetic | 0.20 | 0.00 ± 0.00% | 1.46 ± 0.09% | 0.00 ± 0.00% | 43.85 ± 8.17% | 12.28 ± 0.10% | 2252.59 ± 40.83 | 3182.48 ± 10.15 |
| safety+math+code+medical | task_arithmetic | 0.40 | 0.03 ± 0.05% | 1.15 ± 0.74% | 0.00 ± 0.00% | 34.79 ± 10.01% | 15.27 ± 0.40% | 134.88 ± 15.48 | 35.42 ± 0.54 |
| safety+math+code+medical | task_arithmetic | 0.60 | 5.97 ± 0.50% | 2.92 ± 0.36% | 0.00 ± 0.00% | 48.91 ± 6.99% | 14.56 ± 1.63% | 2.91 ± 0.06 | 4.50 ± 0.04 |
| safety+math+code+medical | task_arithmetic | 0.80 | 1.24 ± 1.69% | 3.85 ± 0.55% | 5.33 ± 1.10% | 35.47 ± 17.90% | 22.95 ± 4.43% | 1.88 ± 0.02 | 2.59 ± 0.03 |
| safety+math+code+medical | task_arithmetic | 1.00 | 0.00 ± 0.00% | 3.33 ± 2.92% | 7.22 ± 1.70% | 51.93 ± 15.36% | 22.97 ± 11.46% | 1.96 ± 0.04 | 2.98 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: task_arithmetic, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | task_arithmetic | 0.00 | 42.0 | 0.08% | 0.00% | 0.00% | 21.25% | 11.52% | 8199.94 | 12188.24 |
| safety+math+code+medical | task_arithmetic | 0.00 | 43.0 | 0.08% | 0.16% | 0.00% | 21.25% | 11.52% | 8199.95 | 12188.31 |
| safety+math+code+medical | task_arithmetic | 0.00 | 44.0 | 0.08% | 0.16% | 0.00% | 21.25% | 11.52% | 8199.95 | 12188.31 |
| safety+math+code+medical | task_arithmetic | 0.20 | 42.0 | 0.00% | 1.41% | 0.00% | 53.28% | 12.37% | 2225.31 | 3189.90 |
| safety+math+code+medical | task_arithmetic | 0.20 | 43.0 | 0.00% | 1.41% | 0.00% | 38.91% | 12.18% | 2232.93 | 3170.92 |
| safety+math+code+medical | task_arithmetic | 0.20 | 44.0 | 0.00% | 1.56% | 0.00% | 39.38% | 12.29% | 2299.53 | 3186.63 |
| safety+math+code+medical | task_arithmetic | 0.40 | 42.0 | 0.08% | 1.72% | 0.00% | 39.69% | 14.85% | 117.60 | 34.81 |
| safety+math+code+medical | task_arithmetic | 0.40 | 43.0 | 0.00% | 1.41% | 0.00% | 41.41% | 15.66% | 147.50 | 35.82 |
| safety+math+code+medical | task_arithmetic | 0.40 | 44.0 | 0.00% | 0.31% | 0.00% | 23.28% | 15.30% | 139.54 | 35.63 |
| safety+math+code+medical | task_arithmetic | 0.60 | 42.0 | 6.18% | 3.12% | 0.00% | 56.25% | 16.33% | 2.85 | 4.49 |
| safety+math+code+medical | task_arithmetic | 0.60 | 43.0 | 6.32% | 2.50% | 0.00% | 48.12% | 14.22% | 2.94 | 4.47 |
| safety+math+code+medical | task_arithmetic | 0.60 | 44.0 | 5.40% | 3.12% | 0.00% | 42.34% | 13.12% | 2.96 | 4.54 |
| safety+math+code+medical | task_arithmetic | 0.80 | 42.0 | 0.56% | 3.91% | 5.99% | 56.09% | 18.55% | 1.85 | 2.61 |
| safety+math+code+medical | task_arithmetic | 0.80 | 43.0 | 3.17% | 4.38% | 5.94% | 24.06% | 27.41% | 1.89 | 2.61 |
| safety+math+code+medical | task_arithmetic | 0.80 | 44.0 | 0.00% | 3.28% | 4.06% | 26.25% | 22.91% | 1.89 | 2.55 |
| safety+math+code+medical | task_arithmetic | 1.00 | 42.0 | 0.00% | 4.53% | 8.64% | 61.56% | 36.21% | 1.91 | 2.90 |
| safety+math+code+medical | task_arithmetic | 1.00 | 43.0 | 0.00% | 5.47% | 5.34% | 60.00% | 16.52% | 1.97 | 3.01 |
| safety+math+code+medical | task_arithmetic | 1.00 | 44.0 | 0.00% | 0.00% | 7.68% | 34.22% | 16.19% | 1.98 | 3.03 |


---

### Alpha スイープ: Method = safemerge, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: safemerge, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 4.63 ± 8.03% | 3.80 ± 1.19% | 7.32 ± 2.18% | 60.94 ± 0.68% | 18.10 ± 2.89% | 1.90 ± 0.30 | 2.93 ± 0.81 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: safemerge, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | safemerge | N/A | 42.0 | 13.90% | 4.84% | 7.18% | 61.41% | 21.24% | 1.59 | 2.12 |
| safety+math | safemerge | N/A | 43.0 | 0.00% | 2.50% | 5.21% | 60.16% | 15.55% | 2.19 | 3.74 |
| safety+math | safemerge | N/A | 44.0 | 0.00% | 4.06% | 9.56% | 61.25% | 17.50% | 1.92 | 2.94 |


---

### Alpha スイープ: Method = safemerge, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: safemerge, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 0.10 ± 0.18% | 2.19 ± 1.65% | 8.20 ± 3.95% | 55.21 ± 6.44% | 23.78 ± 9.09% | 1.98 ± 0.54 | 3.19 ± 1.54 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: safemerge, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | safemerge | N/A | 42.0 | 0.31% | 3.91% | 10.16% | 61.25% | 32.54% | 1.60 | 2.13 |
| safety+code | safemerge | N/A | 43.0 | 0.00% | 2.03% | 10.78% | 48.44% | 24.41% | 1.75 | 2.47 |
| safety+code | safemerge | N/A | 44.0 | 0.00% | 0.62% | 3.66% | 55.94% | 14.39% | 2.60 | 4.95 |


---

### Alpha スイープ: Method = safemerge, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: safemerge, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 0.03 ± 0.05% | 1.35 ± 2.35% | 3.23 ± 5.60% | 45.10 ± 14.55% | 14.87 ± 3.75% | 3.00 ± 1.27 | 6.06 ± 3.55 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: safemerge, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | safemerge | N/A | 42.0 | 0.00% | 4.06% | 9.70% | 61.09% | 19.15% | 1.64 | 2.23 |
| safety+medical | safemerge | N/A | 43.0 | 0.08% | 0.00% | 0.00% | 32.66% | 12.18% | 4.16 | 9.24 |
| safety+medical | safemerge | N/A | 44.0 | 0.00% | 0.00% | 0.00% | 41.56% | 13.29% | 3.20 | 6.72 |


---

### Alpha スイープ: Method = dare, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.00 | 32.80 ± 0.81% | 20.78 ± 0.95% | 7.48 ± 0.62% | 59.95 ± 0.70% | 34.57 ± 4.87% | 1.90 ± 0.00 | 2.57 ± 0.00 |
| safety+math | dare | 0.20 | 10.40 ± 1.49% | 19.38 ± 1.39% | 7.71 ± 0.55% | 60.42 ± 0.50% | 32.87 ± 5.75% | 2.15 ± 0.03 | 3.07 ± 0.06 |
| safety+math | dare | 0.40 | 8.85 ± 1.44% | 21.09 ± 0.78% | 8.59 ± 1.19% | 59.58 ± 0.18% | 30.44 ± 5.88% | 2.14 ± 0.04 | 3.12 ± 0.06 |
| safety+math | dare | 0.60 | 6.22 ± 5.24% | 20.00 ± 0.47% | 7.91 ± 0.50% | 60.16 ± 0.56% | 28.04 ± 8.60% | 2.14 ± 0.05 | 3.15 ± 0.09 |
| safety+math | dare | 0.80 | 3.51 ± 4.65% | 18.70 ± 0.18% | 8.65 ± 0.56% | 59.58 ± 1.10% | 18.29 ± 0.87% | 2.11 ± 0.05 | 3.20 ± 0.11 |
| safety+math | dare | 1.00 | 0.00 ± 0.00% | 3.96 ± 0.70% | 7.17 ± 2.69% | 60.47 ± 0.68% | 16.21 ± 0.71% | 1.96 ± 0.04 | 2.99 ± 0.08 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | dare | 0.00 | 42.0 | 32.31% | 21.41% | 7.85% | 60.00% | 38.71% | 1.89 | 2.56 |
| safety+math | dare | 0.00 | 43.0 | 32.36% | 21.25% | 7.82% | 59.22% | 29.21% | 1.90 | 2.57 |
| safety+math | dare | 0.00 | 44.0 | 33.74% | 19.69% | 6.76% | 60.62% | 35.79% | 1.90 | 2.57 |
| safety+math | dare | 0.20 | 42.0 | 11.95% | 18.91% | 7.26% | 60.78% | 39.51% | 2.11 | 3.01 |
| safety+math | dare | 0.20 | 43.0 | 10.24% | 18.28% | 8.32% | 60.62% | 29.70% | 2.16 | 3.07 |
| safety+math | dare | 0.20 | 44.0 | 8.99% | 20.94% | 7.56% | 59.84% | 29.42% | 2.18 | 3.13 |
| safety+math | dare | 0.40 | 42.0 | 10.49% | 21.09% | 9.89% | 59.69% | 26.39% | 2.10 | 3.05 |
| safety+math | dare | 0.40 | 43.0 | 8.25% | 21.88% | 8.33% | 59.38% | 37.18% | 2.15 | 3.13 |
| safety+math | dare | 0.40 | 44.0 | 7.81% | 20.31% | 7.56% | 59.69% | 27.73% | 2.17 | 3.17 |
| safety+math | dare | 0.60 | 42.0 | 0.32% | 20.47% | 7.71% | 59.53% | 19.57% | 2.08 | 3.06 |
| safety+math | dare | 0.60 | 43.0 | 7.99% | 19.53% | 8.48% | 60.62% | 27.78% | 2.16 | 3.16 |
| safety+math | dare | 0.60 | 44.0 | 10.35% | 20.00% | 7.55% | 60.31% | 36.77% | 2.18 | 3.23 |
| safety+math | dare | 0.80 | 42.0 | 0.00% | 18.59% | 9.28% | 59.69% | 18.98% | 2.05 | 3.08 |
| safety+math | dare | 0.80 | 43.0 | 8.78% | 18.91% | 8.49% | 60.62% | 18.57% | 2.12 | 3.23 |
| safety+math | dare | 0.80 | 44.0 | 1.74% | 18.59% | 8.18% | 58.44% | 17.31% | 2.16 | 3.28 |
| safety+math | dare | 1.00 | 42.0 | 0.00% | 3.28% | 9.57% | 61.25% | 15.49% | 1.92 | 2.91 |
| safety+math | dare | 1.00 | 43.0 | 0.00% | 4.69% | 4.27% | 60.16% | 16.23% | 1.97 | 3.04 |
| safety+math | dare | 1.00 | 44.0 | 0.00% | 3.91% | 7.68% | 60.00% | 16.90% | 1.99 | 3.03 |


---

### Alpha スイープ: Method = dare, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.00 | 0.03 ± 0.05% | 0.05 ± 0.09% | 0.00 ± 0.00% | 42.71 ± 16.62% | 11.73 ± 0.55% | 694070.90 ± 187353.32 | 894749.07 ± 430040.26 |
| safety+code | dare | 0.20 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 20.42 ± 5.11% | 11.72 ± 0.12% | 383950.20 ± 67553.87 | 671479.52 ± 135038.44 |
| safety+code | dare | 0.40 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 29.22 ± 17.83% | 11.86 ± 0.53% | 306695.55 ± 305628.99 | 656332.54 ± 543423.24 |
| safety+code | dare | 0.60 | 0.00 ± 0.00% | 0.26 ± 0.24% | 0.00 ± 0.00% | 31.56 ± 11.41% | 11.80 ± 0.92% | 398649.10 ± 507513.35 | 425860.14 ± 214984.80 |
| safety+code | dare | 0.80 | 0.00 ± 0.00% | 0.10 ± 0.09% | 0.00 ± 0.00% | 29.48 ± 8.52% | 12.06 ± 0.69% | 243088.00 ± 245330.74 | 419233.90 ± 277325.61 |
| safety+code | dare | 1.00 | 0.00 ± 0.00% | 2.86 ± 1.66% | 6.94 ± 3.12% | 52.60 ± 14.46% | 26.35 ± 10.13% | 1.96 ± 0.04 | 2.97 ± 0.06 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | dare | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 56.41% | 12.37% | 573035.61 | 454953.92 |
| safety+code | dare | 0.00 | 43.0 | 0.00% | 0.16% | 0.00% | 24.22% | 11.50% | 909875.73 | 1314320.87 |
| safety+code | dare | 0.00 | 44.0 | 0.08% | 0.00% | 0.00% | 47.50% | 11.34% | 599301.37 | 914972.42 |
| safety+code | dare | 0.20 | 42.0 | 0.00% | 0.00% | 0.00% | 16.72% | 11.74% | 315806.00 | 516499.26 |
| safety+code | dare | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 26.25% | 11.82% | 450897.85 | 734096.20 |
| safety+code | dare | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 18.28% | 11.59% | 385146.77 | 763843.10 |
| safety+code | dare | 0.40 | 42.0 | 0.08% | 0.00% | 0.00% | 15.00% | 12.42% | 651580.57 | 1257208.41 |
| safety+code | dare | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 49.22% | 11.79% | 199059.06 | 512483.09 |
| safety+code | dare | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 23.44% | 11.37% | 69447.03 | 199306.11 |
| safety+code | dare | 0.60 | 42.0 | 0.00% | 0.31% | 0.00% | 28.91% | 10.77% | 88574.49 | 332254.62 |
| safety+code | dare | 0.60 | 43.0 | 0.00% | 0.47% | 0.00% | 21.72% | 12.11% | 123035.62 | 273547.43 |
| safety+code | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 44.06% | 12.52% | 984337.19 | 671778.37 |
| safety+code | dare | 0.80 | 42.0 | 0.00% | 0.16% | 0.00% | 35.16% | 11.59% | 118817.68 | 503105.52 |
| safety+code | dare | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 33.59% | 12.84% | 525688.21 | 644942.73 |
| safety+code | dare | 0.80 | 44.0 | 0.00% | 0.16% | 0.00% | 19.69% | 11.74% | 84758.10 | 109653.44 |
| safety+code | dare | 1.00 | 42.0 | 0.00% | 4.38% | 9.42% | 61.88% | 36.30% | 1.91 | 2.90 |
| safety+code | dare | 1.00 | 43.0 | 0.00% | 1.09% | 3.44% | 35.94% | 16.06% | 1.97 | 3.01 |
| safety+code | dare | 1.00 | 44.0 | 0.00% | 3.12% | 7.98% | 60.00% | 26.70% | 1.99 | 3.01 |


---

### Alpha スイープ: Method = dare, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.00 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.96 ± 19.24% | 11.98 ± 0.70% | 35857934.16 ± 18835271.33 | 51171370.56 ± 20469414.31 |
| safety+medical | dare | 0.20 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.03 ± 1.56% | 12.35 ± 0.94% | 30084819.21 ± 18158973.84 | 46629447.22 ± 36397216.84 |
| safety+medical | dare | 0.40 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 18.07 ± 3.99% | 12.16 ± 0.77% | 14784640.46 ± 9533992.17 | 212655363.38 ± 347133928.25 |
| safety+medical | dare | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 19.79 ± 2.12% | 11.00 ± 1.11% | 20797785.11 ± 14399754.63 | 14708432.51 ± 16144047.41 |
| safety+medical | dare | 0.80 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 20.31 ± 8.37% | 11.67 ± 0.27% | 50411154.10 ± 57002591.36 | 76401979.17 ± 100285710.40 |
| safety+medical | dare | 1.00 | 0.00 ± 0.00% | 2.50 ± 1.76% | 5.27 ± 4.94% | 47.19 ± 14.14% | 22.22 ± 10.35% | 1.96 ± 0.04 | 2.98 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | dare | 0.00 | 42.0 | 0.08% | 0.00% | 0.00% | 28.59% | 11.60% | 34973053.79 | 70473589.84 |
| safety+medical | dare | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 55.31% | 11.56% | 55120049.86 | 53334031.27 |
| safety+medical | dare | 0.00 | 44.0 | 0.00% | 0.00% | 0.00% | 17.97% | 12.79% | 17480698.84 | 29706490.55 |
| safety+medical | dare | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 17.03% | 11.59% | 13713568.68 | 18198672.82 |
| safety+medical | dare | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 15.47% | 13.40% | 49616586.91 | 87650164.00 |
| safety+medical | dare | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 18.59% | 12.05% | 26924302.04 | 34039504.85 |
| safety+medical | dare | 0.40 | 42.0 | 0.08% | 0.00% | 0.00% | 14.22% | 12.53% | 7502680.49 | 7782432.54 |
| safety+medical | dare | 0.40 | 43.0 | 0.08% | 0.00% | 0.00% | 17.81% | 11.27% | 11275319.69 | 16725819.01 |
| safety+medical | dare | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 22.19% | 12.68% | 25575921.19 | 613457838.60 |
| safety+medical | dare | 0.60 | 42.0 | 0.00% | 0.00% | 0.00% | 21.09% | 9.83% | 31717047.76 | 33279831.89 |
| safety+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 20.94% | 11.14% | 4478586.08 | 4023586.47 |
| safety+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 17.34% | 12.03% | 26197721.48 | 6821879.17 |
| safety+medical | dare | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 11.72% | 11.77% | 31345314.16 | 23010242.87 |
| safety+medical | dare | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 20.78% | 11.88% | 5385245.88 | 14107872.71 |
| safety+medical | dare | 0.80 | 44.0 | 0.16% | 0.00% | 0.00% | 28.44% | 11.37% | 114502902.25 | 192087821.93 |
| safety+medical | dare | 1.00 | 42.0 | 0.00% | 3.59% | 10.96% | 61.41% | 34.17% | 1.91 | 2.90 |
| safety+medical | dare | 1.00 | 43.0 | 0.00% | 0.47% | 2.66% | 47.03% | 16.17% | 1.98 | 2.99 |
| safety+medical | dare | 1.00 | 44.0 | 0.00% | 3.44% | 2.19% | 33.12% | 16.30% | 1.99 | 3.05 |


---

### Alpha スイープ: Method = dare, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: dare, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.00 | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.84 ± 18.72% | 12.12 ± 0.60% | 7302514.82 ± 7460062.63 | 11880294.42 ± 3503725.18 |
| safety+math+code+medical | dare | 0.20 | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 30.26 ± 21.38% | 12.31 ± 0.72% | 7230430.12 ± 3418148.36 | 6230043.88 ± 1795222.09 |
| safety+math+code+medical | dare | 0.40 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.81 ± 2.89% | 11.96 ± 0.29% | 5300473.89 ± 4652204.12 | 3676141.77 ± 2600167.94 |
| safety+math+code+medical | dare | 0.60 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 34.64 ± 20.19% | 11.51 ± 0.16% | 4659204.25 ± 5454560.12 | 4988976.69 ± 3382670.49 |
| safety+math+code+medical | dare | 0.80 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 13.33 ± 3.61% | 11.92 ± 0.05% | 1108618.09 ± 987286.09 | 749856.57 ± 284860.35 |
| safety+math+code+medical | dare | 1.00 | 0.00 ± 0.00% | 2.86 ± 2.48% | 6.84 ± 3.08% | 50.83 ± 16.17% | 22.66 ± 11.23% | 1.96 ± 0.04 | 2.98 ± 0.06 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: dare, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | dare | 0.00 | 42.0 | 0.16% | 0.00% | 0.00% | 39.06% | 11.47% | 15909661.56 | 15631070.22 |
| safety+math+code+medical | dare | 0.00 | 43.0 | 0.08% | 0.00% | 0.00% | 51.09% | 12.65% | 2698436.41 | 11318242.27 |
| safety+math+code+medical | dare | 0.00 | 44.0 | 0.08% | 0.00% | 0.00% | 14.37% | 12.23% | 3299446.50 | 8691570.76 |
| safety+math+code+medical | dare | 0.20 | 42.0 | 0.16% | 0.00% | 0.00% | 54.22% | 12.66% | 5468037.58 | 4177561.21 |
| safety+math+code+medical | dare | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 13.12% | 12.79% | 5053159.85 | 7004673.39 |
| safety+math+code+medical | dare | 0.20 | 44.0 | 0.16% | 0.00% | 0.00% | 23.44% | 11.48% | 11170092.94 | 7507897.06 |
| safety+math+code+medical | dare | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 17.66% | 11.93% | 10009996.25 | 4684967.15 |
| safety+math+code+medical | dare | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 15.00% | 11.68% | 5183636.42 | 5620724.14 |
| safety+math+code+medical | dare | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 20.78% | 12.26% | 707789.01 | 722734.02 |
| safety+math+code+medical | dare | 0.60 | 42.0 | 0.16% | 0.00% | 0.00% | 57.03% | 11.37% | 10950640.94 | 8892188.86 |
| safety+math+code+medical | dare | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 29.06% | 11.68% | 1769599.74 | 2910245.81 |
| safety+math+code+medical | dare | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 17.81% | 11.49% | 1257372.06 | 3164495.39 |
| safety+math+code+medical | dare | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 17.50% | 11.97% | 2226477.01 | 1069357.98 |
| safety+math+code+medical | dare | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 11.09% | 11.89% | 355968.72 | 522396.51 |
| safety+math+code+medical | dare | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 11.41% | 11.89% | 743408.52 | 657815.22 |
| safety+math+code+medical | dare | 1.00 | 42.0 | 0.00% | 4.22% | 10.33% | 60.94% | 35.63% | 1.91 | 2.91 |
| safety+math+code+medical | dare | 1.00 | 43.0 | 0.00% | 4.38% | 5.66% | 59.38% | 16.24% | 1.97 | 3.00 |
| safety+math+code+medical | dare | 1.00 | 44.0 | 0.00% | 0.00% | 4.53% | 32.19% | 16.12% | 1.99 | 3.02 |


---

### Alpha スイープ: Method = della, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | della | 0.00 | 33.34 ± 1.01% | 20.68 ± 0.63% | 5.91 ± 2.71% | 60.42 ± 0.18% | 38.28 ± 1.64% | 1.91 ± 0.00 | 2.58 ± 0.01 |
| safety+math | della | 0.20 | 11.65 ± 0.80% | 21.41 ± 0.95% | 6.49 ± 2.57% | 60.26 ± 0.59% | 37.45 ± 2.43% | 2.17 ± 0.03 | 3.11 ± 0.06 |
| safety+math | della | 0.40 | 7.79 ± 3.07% | 22.45 ± 1.17% | 7.62 ± 0.54% | 60.52 ± 0.94% | 37.28 ± 2.03% | 2.16 ± 0.04 | 3.14 ± 0.07 |
| safety+math | della | 0.60 | 6.67 ± 5.52% | 21.77 ± 1.15% | 7.40 ± 0.93% | 59.74 ± 0.39% | 35.88 ± 3.59% | 2.16 ± 0.05 | 3.18 ± 0.08 |
| safety+math | della | 0.80 | 2.84 ± 3.94% | 18.96 ± 0.45% | 7.15 ± 0.81% | 59.95 ± 0.50% | 24.72 ± 5.76% | 2.13 ± 0.06 | 3.24 ± 0.13 |
| safety+math | della | 1.00 | 0.00 ± 0.00% | 4.38 ± 0.56% | 7.38 ± 2.42% | 59.64 ± 0.94% | 22.57 ± 10.96% | 1.99 ± 0.04 | 3.06 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | della | 0.00 | 42.0 | 33.90% | 20.78% | 7.07% | 60.62% | 38.21% | 1.91 | 2.59 |
| safety+math | della | 0.00 | 43.0 | 32.17% | 21.25% | 7.85% | 60.31% | 39.96% | 1.91 | 2.58 |
| safety+math | della | 0.00 | 44.0 | 33.94% | 20.00% | 2.81% | 60.31% | 36.69% | 1.91 | 2.58 |
| safety+math | della | 0.20 | 42.0 | 10.75% | 22.50% | 3.59% | 60.94% | 35.21% | 2.13 | 3.05 |
| safety+math | della | 0.20 | 43.0 | 12.27% | 20.94% | 7.39% | 59.84% | 40.02% | 2.18 | 3.10 |
| safety+math | della | 0.20 | 44.0 | 11.94% | 20.78% | 8.48% | 60.00% | 37.10% | 2.19 | 3.17 |
| safety+math | della | 0.40 | 42.0 | 11.29% | 23.59% | 7.11% | 61.41% | 36.29% | 2.12 | 3.06 |
| safety+math | della | 0.40 | 43.0 | 5.56% | 22.50% | 8.18% | 60.62% | 39.61% | 2.17 | 3.15 |
| safety+math | della | 0.40 | 44.0 | 6.53% | 21.25% | 7.56% | 59.53% | 35.93% | 2.20 | 3.21 |
| safety+math | della | 0.60 | 42.0 | 0.70% | 22.19% | 6.78% | 60.16% | 34.07% | 2.11 | 3.09 |
| safety+math | della | 0.60 | 43.0 | 11.61% | 22.66% | 8.47% | 59.38% | 33.56% | 2.17 | 3.20 |
| safety+math | della | 0.60 | 44.0 | 7.68% | 20.47% | 6.93% | 59.69% | 40.02% | 2.20 | 3.25 |
| safety+math | della | 0.80 | 42.0 | 0.00% | 19.22% | 8.03% | 60.16% | 28.83% | 2.07 | 3.10 |
| safety+math | della | 0.80 | 43.0 | 7.34% | 19.22% | 6.46% | 60.31% | 27.21% | 2.15 | 3.27 |
| safety+math | della | 0.80 | 44.0 | 1.19% | 18.44% | 6.94% | 59.38% | 18.13% | 2.19 | 3.35 |
| safety+math | della | 1.00 | 42.0 | 0.00% | 4.53% | 9.72% | 60.62% | 35.22% | 1.94 | 2.97 |
| safety+math | della | 1.00 | 43.0 | 0.00% | 4.84% | 4.89% | 59.53% | 15.86% | 2.00 | 3.09 |
| safety+math | della | 1.00 | 44.0 | 0.00% | 3.75% | 7.53% | 58.75% | 16.64% | 2.01 | 3.11 |


---

### Alpha スイープ: Method = della, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | della | 0.00 | 0.00 ± 0.00% | 0.05 ± 0.09% | 0.00 ± 0.00% | 35.52 ± 7.28% | 11.90 ± 0.49% | 587803.83 ± 179749.94 | 842451.77 ± 362569.96 |
| safety+code | della | 0.20 | 0.00 ± 0.00% | 0.42 ± 0.72% | 0.00 ± 0.00% | 20.73 ± 0.86% | 11.74 ± 0.46% | 268877.82 ± 179640.54 | 460959.19 ± 184233.15 |
| safety+code | della | 0.40 | 0.05 ± 0.05% | 0.10 ± 0.09% | 0.00 ± 0.00% | 25.05 ± 4.61% | 11.74 ± 0.21% | 199633.11 ± 117243.28 | 392132.66 ± 195746.02 |
| safety+code | della | 0.60 | 0.00 ± 0.00% | 0.26 ± 0.33% | 0.00 ± 0.00% | 31.41 ± 13.67% | 12.31 ± 0.88% | 120223.11 ± 54132.59 | 253194.63 ± 34087.44 |
| safety+code | della | 0.80 | 0.05 ± 0.09% | 0.68 ± 0.80% | 0.00 ± 0.00% | 27.29 ± 16.98% | 11.41 ± 0.68% | 104083.45 ± 46691.56 | 597551.07 ± 550913.12 |
| safety+code | della | 1.00 | 0.00 ± 0.00% | 2.81 ± 2.03% | 5.80 ± 4.43% | 51.93 ± 14.31% | 15.93 ± 0.64% | 1.98 ± 0.04 | 3.05 ± 0.08 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | della | 0.00 | 42.0 | 0.00% | 0.16% | 0.00% | 27.50% | 11.56% | 545901.97 | 974643.69 |
| safety+code | della | 0.00 | 43.0 | 0.00% | 0.00% | 0.00% | 41.72% | 12.46% | 432705.86 | 432334.08 |
| safety+code | della | 0.00 | 44.0 | 0.00% | 0.00% | 0.00% | 37.34% | 11.67% | 784803.66 | 1120377.54 |
| safety+code | della | 0.20 | 42.0 | 0.00% | 0.00% | 0.00% | 20.31% | 12.16% | 420726.50 | 610110.74 |
| safety+code | della | 0.20 | 43.0 | 0.00% | 1.25% | 0.00% | 21.72% | 11.26% | 70572.07 | 255016.70 |
| safety+code | della | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 20.16% | 11.80% | 315334.88 | 517750.12 |
| safety+code | della | 0.40 | 42.0 | 0.08% | 0.00% | 0.00% | 25.31% | 11.92% | 256947.46 | 296893.43 |
| safety+code | della | 0.40 | 43.0 | 0.00% | 0.16% | 0.00% | 20.31% | 11.51% | 277194.05 | 617273.04 |
| safety+code | della | 0.40 | 44.0 | 0.08% | 0.16% | 0.00% | 29.53% | 11.79% | 64757.84 | 262231.50 |
| safety+code | della | 0.60 | 42.0 | 0.00% | 0.62% | 0.00% | 20.94% | 13.26% | 174271.91 | 216049.68 |
| safety+code | della | 0.60 | 43.0 | 0.00% | 0.16% | 0.00% | 26.41% | 12.15% | 120390.29 | 260491.37 |
| safety+code | della | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 46.88% | 11.52% | 66007.11 | 283042.85 |
| safety+code | della | 0.80 | 42.0 | 0.16% | 1.56% | 0.00% | 16.72% | 12.13% | 64292.14 | 332857.24 |
| safety+code | della | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 46.88% | 11.34% | 155484.51 | 1230855.22 |
| safety+code | della | 0.80 | 44.0 | 0.00% | 0.47% | 0.00% | 18.28% | 10.77% | 92473.69 | 228940.76 |
| safety+code | della | 1.00 | 42.0 | 0.00% | 4.06% | 9.88% | 61.41% | 15.43% | 1.93 | 2.96 |
| safety+code | della | 1.00 | 43.0 | 0.00% | 0.47% | 1.09% | 35.47% | 15.71% | 2.00 | 3.09 |
| safety+code | della | 1.00 | 44.0 | 0.00% | 3.91% | 6.43% | 58.91% | 16.64% | 2.01 | 3.10 |


---

### Alpha スイープ: Method = della, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | della | 0.00 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 38.12 ± 17.17% | 11.81 ± 0.44% | 16091827.99 ± 14882810.80 | 33309554.41 ± 6600851.38 |
| safety+medical | della | 0.20 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 27.19 ± 21.59% | 11.71 ± 0.28% | 21090035.80 ± 17312335.19 | 18097875.79 ± 9447772.23 |
| safety+medical | della | 0.40 | 0.05 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 21.88 ± 9.72% | 12.79 ± 0.68% | 16049035122.39 ± 27778291897.93 | 1590313766.94 ± 2607092615.01 |
| safety+medical | della | 0.60 | 0.03 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 33.59 ± 10.90% | 12.34 ± 0.59% | 10981445.00 ± 6253371.40 | 12572823.50 ± 5352914.49 |
| safety+medical | della | 0.80 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 22.92 ± 9.33% | 11.89 ± 0.08% | 51262131.56 ± 67693503.75 | 24153482.68 ± 28153032.25 |
| safety+medical | della | 1.00 | 0.00 ± 0.00% | 1.25 ± 1.63% | 4.69 ± 4.61% | 44.48 ± 14.31% | 24.63 ± 8.87% | 1.98 ± 0.04 | 3.05 ± 0.07 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | della | 0.00 | 42.0 | 0.00% | 0.00% | 0.00% | 19.84% | 12.25% | 7945551.90 | 27540666.40 |
| safety+medical | della | 0.00 | 43.0 | 0.08% | 0.00% | 0.00% | 40.62% | 11.37% | 7060512.72 | 40508066.95 |
| safety+medical | della | 0.00 | 44.0 | 0.16% | 0.00% | 0.00% | 53.91% | 11.81% | 33269419.35 | 31879929.88 |
| safety+medical | della | 0.20 | 42.0 | 0.00% | 0.00% | 0.00% | 10.47% | 11.52% | 19521203.94 | 17179138.50 |
| safety+medical | della | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 19.53% | 11.58% | 4615511.31 | 9143034.88 |
| safety+medical | della | 0.20 | 44.0 | 0.00% | 0.00% | 0.00% | 51.56% | 12.02% | 39133392.17 | 27971453.99 |
| safety+medical | della | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 13.12% | 12.56% | 13459740.74 | 165559672.12 |
| safety+medical | della | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 20.16% | 13.55% | 48124643628.93 | 4599316323.71 |
| safety+medical | della | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 32.34% | 12.24% | 9001997.49 | 6065304.99 |
| safety+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 37.66% | 12.43% | 16881833.35 | 18702955.33 |
| safety+medical | della | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 41.88% | 12.88% | 11635930.70 | 10193181.80 |
| safety+medical | della | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 21.25% | 11.71% | 4426570.97 | 8822333.38 |
| safety+medical | della | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 32.97% | 11.79% | 10558527.12 | 8623054.56 |
| safety+medical | della | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 14.53% | 11.94% | 129405134.58 | 56651217.37 |
| safety+medical | della | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 21.25% | 11.93% | 13822732.99 | 7186176.11 |
| safety+medical | della | 1.00 | 42.0 | 0.00% | 3.12% | 10.02% | 60.94% | 33.76% | 1.93 | 2.97 |
| safety+medical | della | 1.00 | 43.0 | 0.00% | 0.47% | 2.19% | 37.50% | 24.09% | 1.99 | 3.07 |
| safety+medical | della | 1.00 | 44.0 | 0.00% | 0.16% | 1.88% | 35.00% | 16.05% | 2.02 | 3.11 |


---

### Alpha スイープ: Method = della, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: della, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.00 | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 49.27 ± 10.28% | 12.25 ± 0.71% | 5639261.14 ± 5027121.62 | 3498543.54 ± 2086832.67 |
| safety+math+code+medical | della | 0.20 | 0.11 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 27.55 ± 10.01% | 12.38 ± 0.38% | 4666277.94 ± 2585948.06 | 5892903.06 ± 4452380.63 |
| safety+math+code+medical | della | 0.40 | 0.13 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 17.86 ± 5.66% | 11.96 ± 0.55% | 3716221.54 ± 1623674.68 | 2664094.55 ± 2247228.00 |
| safety+math+code+medical | della | 0.60 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 21.98 ± 4.83% | 12.11 ± 0.51% | 1879414.85 ± 888079.34 | 2040741.79 ± 582209.44 |
| safety+math+code+medical | della | 0.80 | 0.05 ± 0.09% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.16 ± 12.39% | 12.17 ± 0.24% | 4737138.61 ± 4082277.64 | 20302784.13 ± 33884002.71 |
| safety+math+code+medical | della | 1.00 | 0.00 ± 0.00% | 2.71 ± 2.10% | 5.71 ± 2.88% | 51.35 ± 15.41% | 23.68 ± 12.39% | 1.99 ± 0.04 | 3.06 ± 0.09 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: della, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | della | 0.00 | 42.0 | 0.08% | 0.00% | 0.00% | 52.97% | 12.20% | 1131866.43 | 2258449.20 |
| safety+math+code+medical | della | 0.00 | 43.0 | 0.16% | 0.00% | 0.00% | 37.66% | 12.99% | 4725231.16 | 2329318.47 |
| safety+math+code+medical | della | 0.00 | 44.0 | 0.08% | 0.00% | 0.00% | 57.19% | 11.57% | 11060685.83 | 5907862.94 |
| safety+math+code+medical | della | 0.20 | 42.0 | 0.08% | 0.00% | 0.00% | 38.44% | 12.35% | 1910968.76 | 3404001.12 |
| safety+math+code+medical | della | 0.20 | 43.0 | 0.16% | 0.00% | 0.00% | 18.75% | 12.03% | 5047272.64 | 3241494.87 |
| safety+math+code+medical | della | 0.20 | 44.0 | 0.08% | 0.00% | 0.00% | 25.47% | 12.78% | 7040592.40 | 11033213.19 |
| safety+math+code+medical | della | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 18.59% | 11.89% | 5591011.04 | 5226341.29 |
| safety+math+code+medical | della | 0.40 | 43.0 | 0.16% | 0.00% | 0.00% | 11.88% | 12.54% | 2764944.14 | 1027721.45 |
| safety+math+code+medical | della | 0.40 | 44.0 | 0.08% | 0.00% | 0.00% | 23.12% | 11.45% | 2792709.45 | 1738220.90 |
| safety+math+code+medical | della | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 20.62% | 11.68% | 1422834.97 | 1400940.99 |
| safety+math+code+medical | della | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 17.97% | 11.98% | 1312509.21 | 2181871.31 |
| safety+math+code+medical | della | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 27.34% | 12.67% | 2902900.38 | 2539413.07 |
| safety+math+code+medical | della | 0.80 | 42.0 | 0.16% | 0.00% | 0.00% | 23.44% | 11.90% | 8640152.36 | 59426952.18 |
| safety+math+code+medical | della | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 48.12% | 12.36% | 5074704.34 | 1057314.86 |
| safety+math+code+medical | della | 0.80 | 44.0 | 0.00% | 0.00% | 0.00% | 33.91% | 12.25% | 496559.12 | 424085.34 |
| safety+math+code+medical | della | 1.00 | 42.0 | 0.00% | 3.59% | 8.95% | 61.25% | 37.98% | 1.94 | 2.96 |
| safety+math+code+medical | della | 1.00 | 43.0 | 0.00% | 4.22% | 4.73% | 59.22% | 16.51% | 2.00 | 3.10 |
| safety+math+code+medical | della | 1.00 | 44.0 | 0.00% | 0.31% | 3.44% | 33.59% | 16.55% | 2.02 | 3.12 |


---

### Alpha スイープ: Method = ties, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | ties | 0.00 | 31.39 ± 0.37% | 21.04 ± 0.33% | 7.53 ± 0.00% | 60.62 ± 0.00% | 18.51 ± 0.00% | 1.77 ± 0.00 | 2.42 ± 0.00 |
| safety+math | ties | 0.20 | 14.41 ± 1.04% | 22.14 ± 1.17% | 8.01 ± 3.24% | 60.16 ± 0.41% | 29.77 ± 0.82% | 1.97 ± 0.03 | 2.87 ± 0.04 |
| safety+math | ties | 0.40 | 14.65 ± 1.43% | 21.82 ± 0.59% | 9.31 ± 0.63% | 60.68 ± 0.45% | 35.24 ± 4.79% | 1.94 ± 0.03 | 2.83 ± 0.04 |
| safety+math | ties | 0.60 | 8.95 ± 5.41% | 20.83 ± 0.90% | 9.73 ± 0.43% | 60.42 ± 0.24% | 32.81 ± 3.39% | 1.94 ± 0.03 | 2.86 ± 0.06 |
| safety+math | ties | 0.80 | 0.50 ± 0.48% | 17.76 ± 1.15% | 10.56 ± 1.19% | 60.31 ± 0.72% | 29.63 ± 3.45% | 1.93 ± 0.04 | 2.93 ± 0.09 |
| safety+math | ties | 1.00 | 0.00 ± 0.00% | 4.27 ± 0.33% | 7.99 ± 2.61% | 60.36 ± 1.04% | 25.53 ± 8.52% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | ties | 0.00 | 42.0 | 31.18% | 21.41% | 7.53% | 60.62% | 18.51% | 1.77 | 2.42 |
| safety+math | ties | 0.00 | 43.0 | 31.18% | 20.94% | 7.53% | 60.62% | 18.51% | 1.77 | 2.42 |
| safety+math | ties | 0.00 | 44.0 | 31.82% | 20.78% | 7.53% | 60.62% | 18.51% | 1.77 | 2.42 |
| safety+math | ties | 0.20 | 42.0 | 14.10% | 22.81% | 10.04% | 59.69% | 29.41% | 1.94 | 2.82 |
| safety+math | ties | 0.20 | 43.0 | 15.57% | 20.78% | 9.71% | 60.31% | 30.71% | 1.98 | 2.87 |
| safety+math | ties | 0.20 | 44.0 | 13.55% | 22.81% | 4.27% | 60.47% | 29.19% | 1.99 | 2.90 |
| safety+math | ties | 0.40 | 42.0 | 16.11% | 21.41% | 9.42% | 60.16% | 37.19% | 1.92 | 2.79 |
| safety+math | ties | 0.40 | 43.0 | 14.61% | 21.56% | 9.87% | 60.94% | 38.75% | 1.95 | 2.84 |
| safety+math | ties | 0.40 | 44.0 | 13.24% | 22.50% | 8.64% | 60.94% | 29.79% | 1.97 | 2.86 |
| safety+math | ties | 0.60 | 42.0 | 3.20% | 20.31% | 10.06% | 60.47% | 28.90% | 1.90 | 2.80 |
| safety+math | ties | 0.60 | 43.0 | 9.69% | 21.88% | 9.25% | 60.62% | 34.87% | 1.95 | 2.87 |
| safety+math | ties | 0.60 | 44.0 | 13.95% | 20.31% | 9.88% | 60.16% | 34.68% | 1.97 | 2.91 |
| safety+math | ties | 0.80 | 42.0 | 0.00% | 17.34% | 11.92% | 61.09% | 26.66% | 1.88 | 2.83 |
| safety+math | ties | 0.80 | 43.0 | 0.55% | 19.06% | 9.71% | 60.16% | 28.81% | 1.94 | 2.96 |
| safety+math | ties | 0.80 | 44.0 | 0.95% | 16.88% | 10.03% | 59.69% | 33.41% | 1.96 | 3.01 |
| safety+math | ties | 1.00 | 42.0 | 0.00% | 3.91% | 10.35% | 61.56% | 33.97% | 1.86 | 2.78 |
| safety+math | ties | 1.00 | 43.0 | 0.00% | 4.53% | 5.18% | 59.84% | 16.94% | 1.92 | 2.86 |
| safety+math | ties | 1.00 | 44.0 | 0.00% | 4.38% | 8.45% | 59.69% | 25.67% | 1.93 | 2.88 |


---

### Alpha スイープ: Method = ties, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | ties | 0.00 | 9.87 ± 0.29% | 2.19 ± 0.27% | 0.21 ± 0.36% | 50.73 ± 5.86% | 14.00 ± 0.01% | 2.84 ± 0.00 | 5.29 ± 0.00 |
| safety+code | ties | 0.20 | 3.05 ± 0.44% | 1.35 ± 0.09% | 0.10 ± 0.18% | 49.58 ± 6.77% | 12.89 ± 0.82% | 4.92 ± 1.98 | 4.76 ± 0.03 |
| safety+code | ties | 0.40 | 0.45 ± 0.44% | 1.35 ± 0.48% | 0.00 ± 0.00% | 43.44 ± 12.59% | 10.79 ± 0.77% | 33.76 ± 43.61 | 6.12 ± 1.08 |
| safety+code | ties | 0.60 | 0.11 ± 0.13% | 1.25 ± 0.56% | 0.00 ± 0.00% | 30.89 ± 13.04% | 17.84 ± 9.74% | 137.44 ± 182.79 | 22.88 ± 22.58 |
| safety+code | ties | 0.80 | 0.03 ± 0.05% | 0.89 ± 0.24% | 0.00 ± 0.00% | 22.40 ± 3.73% | 12.37 ± 1.07% | 1251.61 ± 1745.34 | 401.26 ± 618.29 |
| safety+code | ties | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.04% | 7.62 ± 3.22% | 51.35 ± 16.08% | 30.48 ± 16.26% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | ties | 0.00 | 42.0 | 9.80% | 2.03% | 0.00% | 47.34% | 14.00% | 2.84 | 5.29 |
| safety+code | ties | 0.00 | 43.0 | 9.61% | 2.50% | 0.62% | 57.50% | 13.99% | 2.84 | 5.29 |
| safety+code | ties | 0.00 | 44.0 | 10.18% | 2.03% | 0.00% | 47.34% | 14.00% | 2.84 | 5.29 |
| safety+code | ties | 0.20 | 42.0 | 2.55% | 1.41% | 0.00% | 47.34% | 12.31% | 3.48 | 4.73 |
| safety+code | ties | 0.20 | 43.0 | 3.36% | 1.25% | 0.00% | 57.19% | 13.83% | 4.11 | 4.79 |
| safety+code | ties | 0.20 | 44.0 | 3.23% | 1.41% | 0.30% | 44.22% | 12.54% | 7.17 | 4.77 |
| safety+code | ties | 0.40 | 42.0 | 0.16% | 0.94% | 0.00% | 54.06% | 10.84% | 7.47 | 7.23 |
| safety+code | ties | 0.40 | 43.0 | 0.96% | 1.88% | 0.00% | 46.72% | 11.53% | 9.71 | 6.06 |
| safety+code | ties | 0.40 | 44.0 | 0.24% | 1.25% | 0.00% | 29.53% | 9.99% | 84.10 | 5.08 |
| safety+code | ties | 0.60 | 42.0 | 0.08% | 1.09% | 0.00% | 45.94% | 12.73% | 50.73 | 48.95 |
| safety+code | ties | 0.60 | 43.0 | 0.00% | 1.88% | 0.00% | 23.12% | 11.72% | 14.13 | 10.28 |
| safety+code | ties | 0.60 | 44.0 | 0.25% | 0.78% | 0.00% | 23.59% | 29.07% | 347.45 | 9.42 |
| safety+code | ties | 0.80 | 42.0 | 0.00% | 0.62% | 0.00% | 18.12% | 13.09% | 3251.99 | 1115.19 |
| safety+code | ties | 0.80 | 43.0 | 0.00% | 1.09% | 0.00% | 25.00% | 11.15% | 39.12 | 46.33 |
| safety+code | ties | 0.80 | 44.0 | 0.08% | 0.94% | 0.00% | 24.06% | 12.88% | 463.72 | 42.26 |
| safety+code | ties | 1.00 | 42.0 | 0.00% | 3.91% | 10.35% | 61.56% | 48.60% | 1.86 | 2.78 |
| safety+code | ties | 1.00 | 43.0 | 0.00% | 0.62% | 4.06% | 32.81% | 17.17% | 1.92 | 2.86 |
| safety+code | ties | 1.00 | 44.0 | 0.00% | 4.38% | 8.45% | 59.69% | 25.66% | 1.93 | 2.88 |


---

### Alpha スイープ: Method = ties, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | ties | 0.00 | 0.00 ± 0.00% | 1.82 ± 0.09% | 0.00 ± 0.00% | 17.66 ± 0.27% | 12.09 ± 0.02% | 6721.72 ± 0.01 | 6087.88 ± 0.15 |
| safety+medical | ties | 0.20 | 0.03 ± 0.05% | 1.25 ± 0.83% | 0.00 ± 0.00% | 18.80 ± 1.18% | 11.97 ± 0.21% | 13638.85 ± 2449.53 | 13212.53 ± 2638.35 |
| safety+medical | ties | 0.40 | 0.03 ± 0.05% | 0.26 ± 0.33% | 0.00 ± 0.00% | 20.21 ± 2.53% | 11.67 ± 0.93% | 19431.56 ± 3947.53 | 34857.27 ± 11037.23 |
| safety+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.93 ± 3.86% | 12.06 ± 1.23% | 39894.11 ± 10705.72 | 63613.99 ± 30155.00 |
| safety+medical | ties | 0.80 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 23.44 ± 20.44% | 11.82 ± 0.52% | 140476.49 ± 28732.28 | 221480.23 ± 86588.69 |
| safety+medical | ties | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.04% | 7.62 ± 3.22% | 51.35 ± 16.08% | 25.64 ± 8.45% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | ties | 0.00 | 42.0 | 0.00% | 1.88% | 0.00% | 17.50% | 12.10% | 6721.73 | 6088.05 |
| safety+medical | ties | 0.00 | 43.0 | 0.00% | 1.72% | 0.00% | 17.97% | 12.06% | 6721.71 | 6087.79 |
| safety+medical | ties | 0.00 | 44.0 | 0.00% | 1.88% | 0.00% | 17.50% | 12.10% | 6721.71 | 6087.79 |
| safety+medical | ties | 0.20 | 42.0 | 0.08% | 1.88% | 0.00% | 18.28% | 11.79% | 12826.72 | 16250.65 |
| safety+medical | ties | 0.20 | 43.0 | 0.00% | 0.31% | 0.00% | 20.16% | 11.93% | 16391.30 | 11889.15 |
| safety+medical | ties | 0.20 | 44.0 | 0.00% | 1.56% | 0.00% | 17.97% | 12.19% | 11698.52 | 11497.80 |
| safety+medical | ties | 0.40 | 42.0 | 0.08% | 0.16% | 0.00% | 18.59% | 12.29% | 22192.14 | 32985.21 |
| safety+medical | ties | 0.40 | 43.0 | 0.00% | 0.00% | 0.00% | 23.12% | 12.12% | 14910.03 | 24875.79 |
| safety+medical | ties | 0.40 | 44.0 | 0.00% | 0.62% | 0.00% | 18.91% | 10.60% | 21192.50 | 46710.81 |
| safety+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 17.50% | 12.78% | 38043.47 | 97897.33 |
| safety+medical | ties | 0.60 | 43.0 | 0.00% | 0.00% | 0.00% | 20.47% | 12.76% | 51404.50 | 41198.48 |
| safety+medical | ties | 0.60 | 44.0 | 0.08% | 0.00% | 0.00% | 12.81% | 10.64% | 30234.36 | 51746.15 |
| safety+medical | ties | 0.80 | 42.0 | 0.16% | 0.00% | 0.00% | 47.03% | 11.89% | 125609.42 | 311701.13 |
| safety+medical | ties | 0.80 | 43.0 | 0.00% | 0.00% | 0.00% | 12.34% | 12.30% | 173596.04 | 139050.30 |
| safety+medical | ties | 0.80 | 44.0 | 0.08% | 0.00% | 0.00% | 10.94% | 11.28% | 122224.00 | 213689.26 |
| safety+medical | ties | 1.00 | 42.0 | 0.00% | 3.91% | 10.35% | 61.56% | 34.08% | 1.86 | 2.78 |
| safety+medical | ties | 1.00 | 43.0 | 0.00% | 0.62% | 4.06% | 32.81% | 17.17% | 1.92 | 2.86 |
| safety+medical | ties | 1.00 | 44.0 | 0.00% | 4.38% | 8.45% | 59.69% | 25.66% | 1.93 | 2.88 |


---

### Alpha スイープ: Method = ties, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: ties, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.00 | 0.08 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 40.21 ± 22.37% | 11.59 ± 0.00% | 138597.22 ± 0.00 | 124557.00 ± 0.00 |
| safety+math+code+medical | ties | 0.20 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 29.90 ± 23.97% | 11.68 ± 0.13% | 146910.24 ± 57134.86 | 145135.43 ± 58076.86 |
| safety+math+code+medical | ties | 0.40 | 0.21 ± 0.24% | 0.00 ± 0.00% | 0.00 ± 0.00% | 15.52 ± 3.97% | 11.68 ± 0.19% | 207824.93 ± 178050.92 | 220190.56 ± 162922.41 |
| safety+math+code+medical | ties | 0.60 | 0.05 ± 0.05% | 0.00 ± 0.00% | 0.00 ± 0.00% | 16.51 ± 2.26% | 12.12 ± 0.48% | 216889.35 ± 204103.70 | 271395.89 ± 218392.59 |
| safety+math+code+medical | ties | 0.80 | 0.08 ± 0.08% | 0.00 ± 0.00% | 0.00 ± 0.00% | 35.47 ± 18.52% | 12.01 ± 0.51% | 229654.01 ± 198102.06 | 284236.98 ± 253493.80 |
| safety+math+code+medical | ties | 1.00 | 0.00 ± 0.00% | 2.97 ± 2.36% | 6.22 ± 4.17% | 52.29 ± 14.59% | 30.47 ± 16.30% | 1.90 ± 0.03 | 2.84 ± 0.06 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: ties, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | ties | 0.00 | 42.0 | 0.08% | 0.00% | 0.00% | 14.37% | 11.59% | 138597.22 | 124557.00 |
| safety+math+code+medical | ties | 0.00 | 43.0 | 0.08% | 0.00% | 0.00% | 53.12% | 11.59% | 138597.22 | 124557.00 |
| safety+math+code+medical | ties | 0.00 | 44.0 | 0.08% | 0.00% | 0.00% | 53.12% | 11.59% | 138597.22 | 124557.00 |
| safety+math+code+medical | ties | 0.20 | 42.0 | 0.00% | 0.00% | 0.00% | 17.81% | 11.61% | 174667.71 | 182084.16 |
| safety+math+code+medical | ties | 0.20 | 43.0 | 0.08% | 0.00% | 0.00% | 14.37% | 11.83% | 184863.29 | 175127.70 |
| safety+math+code+medical | ties | 0.20 | 44.0 | 0.08% | 0.00% | 0.00% | 57.50% | 11.59% | 81199.71 | 78194.42 |
| safety+math+code+medical | ties | 0.40 | 42.0 | 0.16% | 0.00% | 0.00% | 17.81% | 11.57% | 168979.47 | 205911.96 |
| safety+math+code+medical | ties | 0.40 | 43.0 | 0.47% | 0.00% | 0.00% | 10.94% | 11.90% | 402091.60 | 389782.32 |
| safety+math+code+medical | ties | 0.40 | 44.0 | 0.00% | 0.00% | 0.00% | 17.81% | 11.57% | 52403.72 | 64877.39 |
| safety+math+code+medical | ties | 0.60 | 42.0 | 0.08% | 0.00% | 0.00% | 17.81% | 11.57% | 130316.85 | 178652.70 |
| safety+math+code+medical | ties | 0.60 | 43.0 | 0.08% | 0.00% | 0.00% | 13.91% | 12.47% | 450010.32 | 520854.54 |
| safety+math+code+medical | ties | 0.60 | 44.0 | 0.00% | 0.00% | 0.00% | 17.81% | 12.30% | 70340.88 | 114680.44 |
| safety+math+code+medical | ties | 0.80 | 42.0 | 0.00% | 0.00% | 0.00% | 35.94% | 11.88% | 137070.32 | 129998.52 |
| safety+math+code+medical | ties | 0.80 | 43.0 | 0.08% | 0.00% | 0.00% | 53.75% | 12.57% | 457096.68 | 576802.21 |
| safety+math+code+medical | ties | 0.80 | 44.0 | 0.16% | 0.00% | 0.00% | 16.72% | 11.57% | 94795.04 | 145910.22 |
| safety+math+code+medical | ties | 1.00 | 42.0 | 0.00% | 3.75% | 10.81% | 61.56% | 48.56% | 1.86 | 2.78 |
| safety+math+code+medical | ties | 1.00 | 43.0 | 0.00% | 4.84% | 5.18% | 59.84% | 16.94% | 1.92 | 2.86 |
| safety+math+code+medical | ties | 1.00 | 44.0 | 0.00% | 0.31% | 2.66% | 35.47% | 25.90% | 1.93 | 2.88 |


---

### Alpha スイープ: Method = matena_fisher, Pattern = safety+math

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+math

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 4.26 ± 0.51% | 16.98 ± 1.15% | 9.32 ± 1.05% | 61.35 ± 0.39% | 31.80 ± 11.53% | 1.67 ± 0.01 | 2.39 ± 0.02 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+math

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math | matena_fisher | N/A | 42.0 | 4.79% | 16.09% | 8.11% | 61.41% | 44.12% | 1.66 | 2.37 |
| safety+math | matena_fisher | N/A | 43.0 | 4.22% | 18.28% | 9.84% | 60.94% | 21.26% | 1.68 | 2.41 |
| safety+math | matena_fisher | N/A | 44.0 | 3.77% | 16.56% | 10.01% | 61.72% | 30.01% | 1.68 | 2.40 |


---

### Alpha スイープ: Method = matena_fisher, Pattern = safety+code

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+code

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 3.38 ± 1.18% | 0.83 ± 0.09% | 0.00 ± 0.00% | 56.20 ± 0.74% | 13.27 ± 0.61% | 80.11 ± 15.69 | 63.11 ± 20.25 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+code

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+code | matena_fisher | N/A | 42.0 | 4.72% | 0.78% | 0.00% | 55.94% | 13.68% | 68.60 | 77.14 |
| safety+code | matena_fisher | N/A | 43.0 | 2.93% | 0.94% | 0.00% | 55.62% | 13.57% | 73.74 | 39.89 |
| safety+code | matena_fisher | N/A | 44.0 | 2.49% | 0.78% | 0.00% | 57.03% | 12.57% | 97.99 | 72.30 |


---

### Alpha スイープ: Method = matena_fisher, Pattern = safety+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 0.16 ± 0.00% | 0.00 ± 0.00% | 0.00 ± 0.00% | 12.08 ± 2.26% | 12.98 ± 0.17% | 384272.26 ± 81902.74 | 304225.05 ± 19087.67 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+medical | matena_fisher | N/A | 42.0 | 0.16% | 0.00% | 0.00% | 14.69% | 13.06% | 478783.02 | 325558.33 |
| safety+medical | matena_fisher | N/A | 43.0 | 0.16% | 0.00% | 0.00% | 10.78% | 12.78% | 339991.11 | 288761.78 |
| safety+medical | matena_fisher | N/A | 44.0 | 0.16% | 0.00% | 0.00% | 10.78% | 13.09% | 334042.64 | 298355.05 |


---

### Alpha スイープ: Method = matena_fisher, Pattern = safety+math+code+medical

#### 【集計】 Alpha スイープ (Mean ± Std) - Method: matena_fisher, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 0.00 ± 0.00% | 2.08 ± 1.17% | 0.00 ± 0.00% | 45.94 ± 16.65% | 13.09 ± 0.17% | 63.37 ± 3.09 | 102.90 ± 1.68 |


#### 【シード別詳細】 Alpha スイープ (Seeds 42, 43, 44) - Method: matena_fisher, Pattern: safety+math+code+medical

| Pattern | Method | Alpha | Seed | Safety Ave [Harmful Content] (ASR↓ %) | Math Ave (%) | Code Ave (%) | Medical Ave (%) | General/Inst Ave (%) | EvolCode (PPL↓) | MedAlpaca (PPL↓) |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| safety+math+code+medical | matena_fisher | N/A | 42.0 | 0.00% | 2.03% | 0.00% | 55.31% | 12.92% | 65.47 | 102.13 |
| safety+math+code+medical | matena_fisher | N/A | 43.0 | 0.00% | 3.28% | 0.00% | 55.78% | 13.08% | 59.82 | 101.75 |
| safety+math+code+medical | matena_fisher | N/A | 44.0 | 0.00% | 0.94% | 0.00% | 26.72% | 13.26% | 64.83 | 104.83 |


---
