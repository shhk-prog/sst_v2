# 論文の表との照合（FR3.1）

再現した値を、HarmBench 単独（主軸）と OR 判定の両方で論文の値と比べる。判定の違いで説明できる差は「判定差」として、不一致とは別に示す。

### 論文の表との照合: tab:evaluation_main_alpha06_safety

許容差: 0.005（論文の表示桁の丸め）

| 状態 | 件数 |
|:---|---:|
| 両方 N/A | 6 |
| 一致 | 126 |
| 不一致 | 84 |

#### 判定差（有害判定の違いによる差。不一致とは別項目）（0 件）

なし

#### 不一致（判定の違いでは説明できない差）（84 件）

| Pattern | Method | 指標 | 統計量 | 論文 | HarmBench 単独 | OR 判定 |
|:---|:---|:---|:---|---:|---:|---:|
| MedAlpaca | Base | cond_asr | mean | 62.85 | 6.11 | 6.11 |
| MedAlpaca | Base | vsr | mean | 30.81 | 79.36 | 79.36 |
| WizardCoder | Base | cond_asr | mean | 73.99 | 26.68 | 26.77 |
| WizardCoder | Base | vsr | mean | 23.66 | 66.47 | 66.40 |
| WizardMath | Base | cond_asr | mean | 67.62 | 32.97 | 32.97 |
| WizardMath | Base | vsr | mean | 30.15 | 62.60 | 62.60 |
| safety+code | DARE | cond_asr | mean | 68.30 | 0.00 | 0.00 |
| safety+code | DARE | cond_asr | std | 2.33 | 0.00 | 0.00 |
| safety+code | DARE | vsr | mean | 31.36 | 97.94 | 97.94 |
| safety+code | DARE | vsr | std | 2.49 | 2.76 | 2.76 |
| safety+code | DELLA | cond_asr | mean | 68.53 | 0.00 | 0.00 |
| safety+code | DELLA | cond_asr | std | 1.44 | 0.00 | 0.00 |
| safety+code | DELLA | vsr | mean | 29.14 | 92.51 | 92.51 |
| safety+code | DELLA | vsr | std | 3.79 | 12.56 | 12.56 |
| safety+code | LED-Merging | cond_asr | mean | 71.01 | 3.64 | 3.64 |
| safety+code | LED-Merging | cond_asr | std | 0.04 | 0.18 | 0.18 |
| safety+code | LED-Merging | vsr | mean | 23.09 | 75.26 | 75.26 |
| safety+code | LED-Merging | vsr | std | 0.05 | 0.09 | 0.09 |
| safety+code | Matena-Fisher | cond_asr | mean | 65.04 | 5.72 | 5.72 |
| safety+code | Matena-Fisher | cond_asr | std | 1.92 | 1.95 | 1.95 |
| safety+code | Matena-Fisher | vsr | mean | 22.35 | 56.36 | 56.36 |
| safety+code | Matena-Fisher | vsr | std | 1.55 | 2.50 | 2.50 |
| safety+code | SafeMERGE | cond_asr | mean | 0.34 | 0.10 | 0.10 |
| safety+code | SafeMERGE | cond_asr | std | 0.59 | 0.18 | 0.18 |
| safety+code | SafeMERGE | vsr | mean | 99.58 | 99.82 | 99.82 |
| safety+code | SafeMERGE | vsr | std | 0.72 | 0.32 | 0.32 |
| safety+code | Task Arithmetic | cond_asr | mean | 60.91 | 30.47 | 30.53 |
| safety+code | Task Arithmetic | cond_asr | std | 2.15 | 3.30 | 3.32 |
| safety+code | Task Arithmetic | vsr | mean | 36.94 | 66.23 | 66.18 |
| safety+code | Task Arithmetic | vsr | std | 2.58 | 3.58 | 3.60 |
| safety+code | TIES | cond_asr | mean | 47.32 | 0.18 | 0.18 |
| safety+code | TIES | cond_asr | std | 6.93 | 0.05 | 0.05 |
| safety+code | TIES | vsr | mean | 32.74 | 61.27 | 61.27 |
| safety+code | TIES | vsr | std | 18.17 | 26.96 | 26.96 |
| safety+math | DARE | cond_asr | mean | 10.68 | 5.98 | 6.14 |
| safety+math | DARE | cond_asr | std | 8.94 | 4.98 | 5.14 |
| safety+math | DARE | vsr | mean | 89.30 | 94.00 | 93.83 |
| safety+math | DARE | vsr | std | 8.96 | 5.01 | 5.17 |
| safety+math | DELLA | cond_asr | mean | 12.19 | 6.64 | 6.66 |
| safety+math | DELLA | cond_asr | std | 10.00 | 5.48 | 5.52 |
| safety+math | DELLA | vsr | mean | 87.81 | 93.36 | 93.34 |
| safety+math | DELLA | vsr | std | 10.00 | 5.48 | 5.52 |
| safety+math | LED-Merging | cond_asr | mean | 71.03 | 3.54 | 3.54 |
| safety+math | LED-Merging | vsr | mean | 23.11 | 75.32 | 75.32 |
| safety+math | Matena-Fisher | cond_asr | mean | 7.38 | 4.21 | 4.32 |
| safety+math | Matena-Fisher | cond_asr | std | 0.53 | 0.29 | 0.42 |
| safety+math | Matena-Fisher | vsr | mean | 91.97 | 95.12 | 95.01 |
| safety+math | Matena-Fisher | vsr | std | 0.47 | 0.38 | 0.30 |
| safety+math | SafeMERGE | cond_asr | mean | 21.65 | 5.12 | 5.25 |
| safety+math | SafeMERGE | cond_asr | std | 37.49 | 8.86 | 9.09 |
| safety+math | SafeMERGE | vsr | mean | 76.88 | 91.06 | 90.96 |
| safety+math | SafeMERGE | vsr | std | 40.04 | 15.48 | 15.67 |
| safety+math | Task Arithmetic | cond_asr | mean | 3.88 | 2.40 | 2.48 |
| safety+math | Task Arithmetic | cond_asr | std | 4.80 | 2.75 | 2.89 |
| safety+math | Task Arithmetic | vsr | mean | 96.04 | 97.52 | 97.44 |
| safety+math | Task Arithmetic | vsr | std | 4.75 | 2.72 | 2.85 |
| safety+math | TIES | cond_asr | mean | 13.84 | 8.90 | 9.04 |
| safety+math | TIES | cond_asr | std | 8.45 | 5.39 | 5.55 |
| safety+math | TIES | vsr | mean | 86.12 | 91.05 | 90.91 |
| safety+math | TIES | vsr | std | 8.45 | 5.40 | 5.56 |
| safety+medical | DARE | cond_asr | mean | 68.04 | 0.03 | 0.03 |
| safety+medical | DARE | cond_asr | std | 2.00 | 0.05 | 0.05 |
| safety+medical | DARE | vsr | mean | 26.26 | 77.74 | 77.74 |
| safety+medical | DARE | vsr | std | 4.26 | 13.41 | 13.41 |
| safety+medical | DELLA | cond_asr | mean | 62.92 | 0.23 | 0.23 |
| safety+medical | DELLA | cond_asr | std | 11.69 | 0.40 | 0.40 |
| safety+medical | DELLA | vsr | mean | 14.59 | 33.65 | 33.65 |
| safety+medical | DELLA | vsr | std | 16.47 | 40.72 | 40.72 |
| safety+medical | Matena-Fisher | cond_asr | mean | 70.98 | 0.16 | 0.16 |
| safety+medical | Matena-Fisher | cond_asr | std | 0.01 | 0.00 | 0.00 |
| safety+medical | Matena-Fisher | vsr | mean | 28.57 | 99.12 | 99.12 |
| safety+medical | Matena-Fisher | vsr | std | 0.77 | 1.24 | 1.24 |
| safety+medical | SafeMERGE | cond_asr | mean | 0.25 | 0.03 | 0.03 |
| safety+medical | SafeMERGE | cond_asr | std | 0.43 | 0.05 | 0.05 |
| safety+medical | SafeMERGE | vsr | mean | 99.75 | 99.97 | 99.97 |
| safety+medical | SafeMERGE | vsr | std | 0.43 | 0.05 | 0.05 |
| safety+medical | Task Arithmetic | cond_asr | mean | 63.87 | 0.16 | 0.16 |
| safety+medical | Task Arithmetic | cond_asr | std | 4.81 | 0.00 | 0.00 |
| safety+medical | Task Arithmetic | vsr | mean | 35.95 | 99.66 | 99.66 |
| safety+medical | Task Arithmetic | vsr | std | 4.91 | 0.18 | 0.18 |
| safety+medical | TIES | cond_asr | mean | 64.34 | 0.06 | 0.06 |
| safety+medical | TIES | cond_asr | std | 6.74 | 0.05 | 0.05 |
| safety+medical | TIES | vsr | mean | 27.98 | 80.87 | 80.87 |
| safety+medical | TIES | vsr | std | 10.88 | 19.72 | 19.72 |

#### 再現側に値がない（0 件）

なし

#### 再現側に行がない（0 件）

なし

#### 論文側に値がない（0 件）

なし


### 論文の表との照合: tab:evaluation_main_alpha06_utility

許容差: 0.005（論文の表示桁の丸め）

| 状態 | 件数 |
|:---|---:|
| 一致 | 216 |

#### 判定差（有害判定の違いによる差。不一致とは別項目）（0 件）

なし

#### 不一致（判定の違いでは説明できない差）（0 件）

なし

#### 再現側に値がない（0 件）

なし

#### 再現側に行がない（0 件）

なし

#### 論文側に値がない（0 件）

なし

