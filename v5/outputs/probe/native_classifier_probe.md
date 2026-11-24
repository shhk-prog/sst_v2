#### 有害判定の違いと Conditional ASR（α=0.6、4 ベンチマークの単純平均、seed 平均 ± 標準偏差）

注: 探索用。論文の表の値との照合は `paper_comparison.md` を参照。集計の細部は未確認。

| Pattern | Method | seed 数 | Cond. ASR: ベンチマーク別の分類器 (%) | Cond. ASR: HarmBench 単独 (%) |
|:---|:---|---:|:---:|:---:|
| safety+code | dare | 3 | 68.30 ± 2.33 | 0.00 ± 0.00 |
| safety+code | data_free_sst_main | 3 | 58.86 ± 1.78 | 0.04 ± 0.07 |
| safety+code | della | 3 | 68.53 ± 1.44 | 0.00 ± 0.00 |
| safety+code | diagonal_sst_main | 3 | 63.91 ± 1.62 | 1.09 ± 0.43 |
| safety+code | led_merging | 3 | 70.89 ± 0.04 | 3.64 ± 0.18 |
| safety+code | matena_fisher | 3 | 63.24 ± 2.13 | 5.72 ± 1.95 |
| safety+code | safemerge | 3 | 0.31 ± 0.55 | 0.10 ± 0.18 |
| safety+code | task_arithmetic | 3 | 59.29 ± 2.19 | 30.47 ± 3.30 |
| safety+code | ties | 3 | 47.03 ± 7.19 | 0.18 ± 0.05 |
| safety+math | dare | 3 | 8.78 ± 7.25 | 5.98 ± 4.98 |
| safety+math | data_free_sst_main | 3 | 25.42 ± 5.04 | 14.71 ± 3.37 |
| safety+math | della | 3 | 10.03 ± 7.96 | 6.64 ± 5.48 |
| safety+math | diagonal_sst_main | 3 | 29.57 ± 8.60 | 17.04 ± 4.81 |
| safety+math | led_merging | 3 | 70.92 ± 0.00 | 3.54 ± 0.00 |
| safety+math | matena_fisher | 3 | 7.14 ± 0.49 | 4.21 ± 0.29 |
| safety+math | safemerge | 3 | 21.42 ± 37.09 | 5.12 ± 8.86 |
| safety+math | task_arithmetic | 3 | 2.89 ± 3.59 | 2.40 ± 2.75 |
| safety+math | ties | 3 | 11.08 ± 6.15 | 8.90 ± 5.39 |
| safety+math+code+medical | dare | 3 | 71.71 ± 2.88 | 0.08 ± 0.08 |
| safety+math+code+medical | data_free_sst_main | 3 | 55.41 ± 6.19 | 0.20 ± 0.08 |
| safety+math+code+medical | della | 3 | 65.74 ± 5.55 | 0.09 ± 0.01 |
| safety+math+code+medical | diagonal_sst_main | 3 | 68.40 ± 1.61 | 0.00 ± 0.00 |
| safety+math+code+medical | matena_fisher | 3 | 58.65 ± 2.94 | 0.00 ± 0.00 |
| safety+math+code+medical | task_arithmetic | 3 | 36.06 ± 7.20 | 6.50 ± 0.63 |
| safety+math+code+medical | ties | 2 | 68.22 ± 1.33 | 0.08 ± 0.00 |
| safety+medical | dare | 3 | 68.04 ± 2.00 | 0.03 ± 0.05 |
| safety+medical | data_free_sst_main | 2 | 65.36 ± 3.87 | 0.13 ± 0.18 |
| safety+medical | della | 3 | 62.92 ± 11.69 | 0.23 ± 0.40 |
| safety+medical | diagonal_sst_main | 2 | 67.04 ± 1.99 | 0.08 ± 0.00 |
| safety+medical | matena_fisher | 3 | 70.98 ± 0.01 | 0.16 ± 0.00 |
| safety+medical | safemerge | 3 | 0.22 ± 0.38 | 0.03 ± 0.05 |
| safety+medical | task_arithmetic | 3 | 63.87 ± 4.81 | 0.16 ± 0.00 |
| safety+medical | ties | 3 | 64.34 ± 6.74 | 0.06 ± 0.05 |
