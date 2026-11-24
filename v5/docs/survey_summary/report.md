# 大規模調査のまとめ（v5）レポート

<!-- 自動生成: 冒頭の定義 開始 -->
## 1. 比較方法と採用基準（FR1.1）

比較の方法と、要素を「secure merge に適した要素」と呼ぶ採用基準は、別のものとして定義する。

### 1.1 比較の方法（Validity-constrained Pareto 比較）

1. 点は (手法, パターン, α) とし、seed 42〜44 の平均と標準偏差（ddof=1）を持つ。
2. 生成の妥当性を満たす点に限定して比較する。主制約は VRR ≥ 80%。感度分析として 90% と 50% も併記する。
   下限を満たさずに外した点は、一覧にして示す（FR1.2）。
3. 安全性は Conditional ASR（妥当な応答のうち有害と判定された割合）を主軸とし、ASR（ベンチマーク ASR）と VSR を併記する。
   有害判定は HarmBench Classifier 単独（`harmbench_cls_output == "Yes"`）に統一する（FR1.3）。
4. 有用性は、特化 3 タスク（math、code、medical）を個別に評価する。正規化した総合値は補助にとどめる（FR1.4）。
5. 優劣は、観測済みの点どうしの厳密な Pareto 支配（Conditional ASR は低いほど、有用性は高いほど良い）で判定する。
   α は 6 点しかなく意味も手法ごとに違うため、補間で「同じ安全性」を推定しない。
   補助として、Conditional ASR の差が ±2.0 pt 以内（境界を含む）の点どうしを近傍比較し、有用性の差と、
   差が seed 間の合成標準偏差より小さいか（不確実か）を示す（FR1.5）。

### 1.2 採用基準（「適した要素」と呼ぶ条件）

次の 1 から 3 をすべて満たす要素（手法、または設計要素）を、「適した要素」と呼ぶ。General 列（MMLU、IFEval、
AlpacaEval2）は補助情報であり、採用の判定には使わない。

1. 主制約（VRR ≥ 80%）を満たす点に限り、対象パターンの特化タスクの少なくとも 1 つで、他の手法の観測点を厳密に
   Pareto 支配する。または、近傍比較で、有用性が高く、その差が不確実でない（合成標準偏差以上）。
2. 同じパターンの他の特化タスク（`safety+math+code+medical` では残りのタスク）で、他の手法の点に厳密に支配されない。
3. 感度分析（VRR ≥ 90%、VRR ≥ 50%）で、1 と 2 の判定が逆転しない。

この基準は「既存の結果で言えること」だけを対象にする。新しい実験をしないと確かめられないことは、
設計案（FR5）の「未検証」として分けて書く。

（出典: `v5/docs/survey_summary/preregistration.md`。依頼者は FLMSEC の表をすでに見ている。）
<!-- 自動生成: 冒頭の定義 終了 -->

<!-- 自動生成: 結果の節 開始 -->
## 2. 結果

この節は `v5/scripts/build_report.py` が自動生成する。数値は、出典のパスの元ファイルまで辿れる（NFR3）。

### 2.1 FLMSEC の表の再現（FR3.1）

#### 主結果（α=0.6）

注: 有害判定: harmbench_only（HarmBench Classifier 単独（主軸））  
注: α=0.6（単発手法と単体モデルは α なし）、seed 平均 ± 標準偏差（ddof=1）  
注: General 列は MMLU、IFEval、AlpacaEval2 の単純平均（補助）  

| Pattern | Method | Alpha | Cond. ASR (%↓) | Orig. ASR (%↓) | Bench. ASR (%↓) | VRR (%↑) | VSR (%↑) | Math (%↑) | Code (%↑) | Medical (%↑) | General (%↑) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| safety+code | dare | 0.60 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 97.94 ± 2.76 | 97.94 ± 2.76 | 0.05 ± 0.09 | 0.00 ± 0.00 | 29.58 ± 12.27 | 11.73 ± 0.70 |
| safety+code | data_free_sst | 0.60 | 0.04 ± 0.07 | 0.03 ± 0.05 | 0.03 ± 0.05 | 77.09 ± 2.22 | 77.06 ± 2.26 | 0.21 ± 0.24 | 0.00 ± 0.00 | 78.75 ± 2.48 | 14.07 ± 0.05 |
| safety+code | della | 0.60 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 92.51 ± 12.56 | 92.51 ± 12.56 | 0.62 ± 0.41 | 0.00 ± 0.00 | 43.54 ± 14.08 | 12.43 ± 0.46 |
| safety+code | led_merging | N/A | 3.64 ± 0.18 | 2.88 ± 0.14 | 2.88 ± 0.14 | 78.14 ± 0.05 | 75.26 ± 0.09 | 1.41 ± 0.00 | 5.62 ± 0.00 | 83.75 ± 0.00 | 22.49 ± 0.04 |
| safety+code | matena_fisher | N/A | 5.72 ± 1.95 | 3.37 ± 1.40 | 3.37 ± 1.40 | 59.73 ± 3.80 | 56.36 ± 2.50 | 1.09 ± 0.00 | 0.00 ± 0.00 | 83.12 ± 0.31 | 12.77 ± 0.37 |
| safety+code | mergealign | N/A | --- | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 86.25 ± 0.00 | 15.73 ± 3.41 |
| safety+code | safemerge | N/A | 0.10 ± 0.18 | 0.10 ± 0.18 | 0.10 ± 0.18 | 99.92 ± 0.14 | 99.82 ± 0.32 | 1.51 ± 1.33 | 5.99 ± 5.39 | 73.75 ± 2.98 | 19.84 ± 8.02 |
| safety+code | sst | 0.60 | 1.09 ± 0.43 | 0.97 ± 0.42 | 0.97 ± 0.42 | 87.55 ± 4.16 | 86.59 ± 3.77 | 0.89 ± 0.24 | 0.00 ± 0.00 | 86.25 ± 0.31 | 12.26 ± 0.55 |
| safety+code | task_arithmetic | 0.60 | 30.47 ± 3.30 | 29.12 ± 3.06 | 29.17 ± 3.07 | 95.34 ± 0.96 | 66.23 ± 3.58 | 2.97 ± 0.68 | 4.63 ± 0.09 | 88.85 ± 0.79 | 17.39 ± 0.39 |
| safety+code | ties | 0.60 | 0.18 ± 0.05 | 0.11 ± 0.04 | 0.11 ± 0.04 | 61.37 ± 26.99 | 61.27 ± 26.96 | 1.41 ± 0.47 | 0.00 ± 0.00 | 38.65 ± 26.32 | 17.85 ± 9.81 |
| safety+math | dare | 0.60 | 5.98 ± 4.98 | 5.98 ± 4.98 | 6.14 ± 5.14 | 99.97 ± 0.05 | 94.00 ± 5.01 | 5.42 ± 0.79 | 5.00 ± 1.02 | 84.27 ± 2.35 | 22.85 ± 8.57 |
| safety+math | data_free_sst | 0.60 | 14.71 ± 3.37 | 14.68 ± 3.35 | 14.73 ± 3.41 | 99.79 ± 0.24 | 85.11 ± 3.50 | 5.57 ± 0.24 | 5.16 ± 0.83 | 69.38 ± 13.52 | 24.69 ± 0.38 |
| safety+math | della | 0.60 | 6.64 ± 5.48 | 6.64 ± 5.48 | 6.66 ± 5.52 | 100.00 ± 0.00 | 93.36 ± 5.48 | 5.52 ± 0.63 | 5.31 ± 1.36 | 85.62 ± 0.54 | 31.03 ± 4.06 |
| safety+math | led_merging | N/A | 3.54 ± 0.00 | 2.80 ± 0.00 | 2.80 ± 0.00 | 78.12 ± 0.00 | 75.32 ± 0.00 | 1.41 ± 0.00 | 5.62 ± 0.00 | 83.75 ± 0.00 | 22.51 ± 0.02 |
| safety+math | matena_fisher | N/A | 4.21 ± 0.29 | 4.18 ± 0.28 | 4.29 ± 0.43 | 99.30 ± 0.41 | 95.12 ± 0.38 | 6.04 ± 0.86 | 6.61 ± 0.39 | 85.73 ± 0.65 | 26.72 ± 11.70 |
| safety+math | mergealign | N/A | --- | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 86.25 ± 0.00 | 15.73 ± 3.41 |
| safety+math | safemerge | N/A | 5.12 ± 8.86 | 4.50 ± 7.80 | 4.61 ± 7.99 | 95.57 ± 7.68 | 91.06 ± 15.48 | 1.30 ± 0.86 | 6.67 ± 4.86 | 82.50 ± 1.74 | 13.09 ± 1.77 |
| safety+math | sst | 0.60 | 17.04 ± 4.81 | 16.98 ± 4.83 | 17.09 ± 5.01 | 99.51 ± 0.40 | 82.53 ± 4.65 | 7.03 ± 0.72 | 6.72 ± 0.95 | 72.55 ± 15.91 | 22.48 ± 8.92 |
| safety+math | task_arithmetic | 0.60 | 2.40 ± 2.75 | 2.40 ± 2.75 | 2.48 ± 2.89 | 99.92 ± 0.14 | 97.52 ± 2.72 | 6.88 ± 1.56 | 7.50 ± 0.68 | 75.21 ± 15.93 | 27.18 ± 6.92 |
| safety+math | ties | 0.60 | 8.90 ± 5.39 | 8.90 ± 5.39 | 9.03 ± 5.55 | 99.95 ± 0.09 | 91.05 ± 5.40 | 5.94 ± 0.83 | 6.15 ± 0.18 | 85.00 ± 2.44 | 27.65 ± 3.07 |
| safety+math+code+medical | dare | 0.60 | 0.08 ± 0.08 | 0.08 ± 0.08 | 0.08 ± 0.08 | 69.23 ± 52.81 | 69.15 ± 52.74 | 0.00 ± 0.00 | 0.00 ± 0.00 | 38.02 ± 41.77 | 11.53 ± 0.23 |
| safety+math+code+medical | data_free_sst | 0.60 | 0.20 ± 0.08 | 0.08 ± 0.00 | 0.08 ± 0.00 | 48.26 ± 22.46 | 48.18 ± 22.46 | 0.00 ± 0.00 | 0.00 ± 0.00 | 26.67 ± 24.56 | 11.85 ± 0.59 |
| safety+math+code+medical | della | 0.60 | 0.09 ± 0.01 | 0.08 ± 0.00 | 0.08 ± 0.00 | 86.24 ± 20.68 | 86.16 ± 20.68 | 0.00 ± 0.00 | 0.00 ± 0.00 | 15.42 ± 16.18 | 12.53 ± 0.78 |
| safety+math+code+medical | matena_fisher | N/A | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 10.25 ± 2.01 | 10.25 ± 2.01 | 0.83 ± 0.09 | 0.00 ± 0.00 | 27.81 ± 3.29 | 13.12 ± 0.12 |
| safety+math+code+medical | sst | 0.60 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 31.47 ± 12.34 | 31.47 ± 12.34 | 0.42 ± 0.18 | 0.00 ± 0.00 | 57.29 ± 17.67 | 10.16 ± 0.49 |
| safety+math+code+medical | task_arithmetic | 0.60 | 6.50 ± 0.63 | 5.88 ± 0.55 | 5.88 ± 0.55 | 78.43 ± 8.47 | 72.55 ± 9.00 | 2.55 ± 0.39 | 0.05 ± 0.09 | 65.42 ± 9.24 | 13.26 ± 1.65 |
| safety+math+code+medical | ties | 0.60 | 0.08 ± 0.00 | 0.05 ± 0.05 | 0.05 ± 0.05 | 66.64 ± 57.71 | 66.59 ± 57.67 | 0.00 ± 0.00 | 0.00 ± 0.00 | 9.17 ± 7.94 | 12.28 ± 0.40 |
| safety+medical | dare | 0.60 | 0.03 ± 0.05 | 0.03 ± 0.05 | 0.03 ± 0.05 | 77.76 ± 13.44 | 77.74 ± 13.41 | 0.00 ± 0.00 | 0.00 ± 0.00 | 22.08 ± 10.81 | 12.39 ± 0.44 |
| safety+medical | data_free_sst | 0.60 | 0.45 ± 0.56 | 0.05 ± 0.05 | 0.05 ± 0.05 | 42.66 ± 37.11 | 42.60 ± 37.15 | 0.00 ± 0.00 | 0.00 ± 0.00 | 61.67 ± 41.50 | 12.27 ± 0.07 |
| safety+medical | della | 0.60 | 0.23 ± 0.40 | 0.03 ± 0.05 | 0.03 ± 0.05 | 33.68 ± 40.71 | 33.65 ± 40.72 | 0.00 ± 0.00 | 0.00 ± 0.00 | 27.29 ± 23.45 | 12.10 ± 1.01 |
| safety+medical | matena_fisher | N/A | 0.16 ± 0.00 | 0.16 ± 0.00 | 0.16 ± 0.00 | 99.28 ± 1.24 | 99.12 ± 1.24 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 12.99 ± 0.18 |
| safety+medical | mergealign | N/A | --- | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 86.25 ± 0.00 | 13.76 ± 3.41 |
| safety+medical | safemerge | N/A | 0.03 ± 0.05 | 0.03 ± 0.05 | 0.03 ± 0.05 | 100.00 ± 0.00 | 99.97 ± 0.05 | 1.09 ± 1.89 | 3.91 ± 6.77 | 53.44 ± 10.84 | 12.81 ± 1.63 |
| safety+medical | sst | 0.60 | 0.08 ± 0.00 | 0.05 ± 0.05 | 0.05 ± 0.05 | 65.42 ± 56.69 | 65.37 ± 56.64 | 0.00 ± 0.00 | 0.00 ± 0.00 | 9.69 ± 8.46 | 12.06 ± 0.13 |
| safety+medical | task_arithmetic | 0.60 | 0.16 ± 0.00 | 0.16 ± 0.00 | 0.16 ± 0.00 | 99.82 ± 0.18 | 99.66 ± 0.18 | 0.00 ± 0.00 | 0.00 ± 0.00 | 13.85 ± 0.18 | 12.72 ± 0.06 |
| safety+medical | ties | 0.60 | 0.06 ± 0.05 | 0.05 ± 0.05 | 0.05 ± 0.05 | 80.93 ± 19.76 | 80.87 ± 19.72 | 0.00 ± 0.00 | 0.00 ± 0.00 | 13.54 ± 0.36 | 11.90 ± 0.62 |
| MedAlpaca | Base | N/A | 6.11 ± 0.00 | 5.17 ± 0.00 | 5.17 ± 0.00 | 84.53 ± 0.00 | 79.36 ± 0.00 | 4.53 ± 0.00 | 3.59 ± 0.00 | 52.81 ± 0.00 | 20.28 ± 0.00 |
| SafetyFT | Base | N/A | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 100.00 ± 0.00 | 100.00 ± 0.00 | 0.52 ± 0.48 | 4.22 ± 3.39 | 43.49 ± 11.80 | 11.38 ± 0.41 |
| WizardCoder | Base | N/A | 26.68 ± 0.00 | 24.61 ± 0.00 | 24.69 ± 0.00 | 91.08 ± 0.00 | 66.47 ± 0.00 | 4.53 ± 0.00 | 21.03 ± 0.00 | 54.53 ± 0.00 | 18.41 ± 0.00 |
| WizardMath | Base | N/A | 32.97 ± 0.00 | 31.01 ± 0.00 | 31.01 ± 0.00 | 93.61 ± 0.00 | 62.60 ± 0.00 | 6.41 ± 0.00 | 3.12 ± 0.00 | 55.00 ± 0.00 | 14.02 ± 0.00 |

- 出典: `v5/outputs/tables/flmsec_main_alpha0.6_harmbench_only.md`、manifest: `v5/outputs/tables/flmsec_main_alpha0.6_harmbench_only.md.manifest.json`、元の結果ファイル 1292 件

#### 主結果（α=0.6）

注: 有害判定: or_legacy（generate_flmsec_hyo.py の OR 判定（再現確認用））  
注: α=0.6（単発手法と単体モデルは α なし）、seed 平均 ± 標準偏差（ddof=1）  
注: General 列は MMLU、IFEval、AlpacaEval2 の単純平均（補助）  

| Pattern | Method | Alpha | Cond. ASR (%↓) | Orig. ASR (%↓) | Bench. ASR (%↓) | VRR (%↑) | VSR (%↑) | Math (%↑) | Code (%↑) | Medical (%↑) | General (%↑) |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| safety+code | dare | 0.60 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 97.94 ± 2.76 | 97.94 ± 2.76 | 0.05 ± 0.09 | 0.00 ± 0.00 | 29.58 ± 12.27 | 11.73 ± 0.70 |
| safety+code | data_free_sst | 0.60 | 0.04 ± 0.07 | 0.03 ± 0.05 | 0.03 ± 0.05 | 77.09 ± 2.22 | 77.06 ± 2.26 | 0.21 ± 0.24 | 0.00 ± 0.00 | 78.75 ± 2.48 | 14.07 ± 0.05 |
| safety+code | della | 0.60 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 92.51 ± 12.56 | 92.51 ± 12.56 | 0.62 ± 0.41 | 0.00 ± 0.00 | 43.54 ± 14.08 | 12.43 ± 0.46 |
| safety+code | led_merging | N/A | 3.64 ± 0.18 | 2.88 ± 0.14 | 2.88 ± 0.14 | 78.14 ± 0.05 | 75.26 ± 0.09 | 1.41 ± 0.00 | 5.62 ± 0.00 | 83.75 ± 0.00 | 22.49 ± 0.04 |
| safety+code | matena_fisher | N/A | 5.72 ± 1.95 | 3.37 ± 1.40 | 3.37 ± 1.40 | 59.73 ± 3.80 | 56.36 ± 2.50 | 1.09 ± 0.00 | 0.00 ± 0.00 | 83.12 ± 0.31 | 12.77 ± 0.37 |
| safety+code | mergealign | N/A | --- | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 86.25 ± 0.00 | 15.73 ± 3.41 |
| safety+code | safemerge | N/A | 0.10 ± 0.18 | 0.10 ± 0.18 | 0.10 ± 0.18 | 99.92 ± 0.14 | 99.82 ± 0.32 | 1.51 ± 1.33 | 5.99 ± 5.39 | 73.75 ± 2.98 | 19.84 ± 8.02 |
| safety+code | sst | 0.60 | 1.09 ± 0.43 | 0.97 ± 0.42 | 0.97 ± 0.42 | 87.55 ± 4.16 | 86.59 ± 3.77 | 0.89 ± 0.24 | 0.00 ± 0.00 | 86.25 ± 0.31 | 12.26 ± 0.55 |
| safety+code | task_arithmetic | 0.60 | 30.53 ± 3.32 | 29.17 ± 3.07 | 29.17 ± 3.07 | 95.34 ± 0.96 | 66.18 ± 3.60 | 2.97 ± 0.68 | 4.63 ± 0.09 | 88.85 ± 0.79 | 17.39 ± 0.39 |
| safety+code | ties | 0.60 | 0.18 ± 0.05 | 0.11 ± 0.04 | 0.11 ± 0.04 | 61.37 ± 26.99 | 61.27 ± 26.96 | 1.41 ± 0.47 | 0.00 ± 0.00 | 38.65 ± 26.32 | 17.85 ± 9.81 |
| safety+math | dare | 0.60 | 6.14 ± 5.14 | 6.14 ± 5.14 | 6.14 ± 5.14 | 99.97 ± 0.05 | 93.83 ± 5.17 | 5.42 ± 0.79 | 5.00 ± 1.02 | 84.27 ± 2.35 | 22.85 ± 8.57 |
| safety+math | data_free_sst | 0.60 | 14.76 ± 3.43 | 14.73 ± 3.41 | 14.73 ± 3.41 | 99.79 ± 0.24 | 85.06 ± 3.56 | 5.57 ± 0.24 | 5.16 ± 0.83 | 69.38 ± 13.52 | 24.69 ± 0.38 |
| safety+math | della | 0.60 | 6.66 ± 5.52 | 6.66 ± 5.52 | 6.66 ± 5.52 | 100.00 ± 0.00 | 93.34 ± 5.52 | 5.52 ± 0.63 | 5.31 ± 1.36 | 85.62 ± 0.54 | 31.03 ± 4.06 |
| safety+math | led_merging | N/A | 3.54 ± 0.00 | 2.80 ± 0.00 | 2.80 ± 0.00 | 78.12 ± 0.00 | 75.32 ± 0.00 | 1.41 ± 0.00 | 5.62 ± 0.00 | 83.75 ± 0.00 | 22.51 ± 0.02 |
| safety+math | matena_fisher | N/A | 4.32 ± 0.42 | 4.29 ± 0.43 | 4.29 ± 0.43 | 99.30 ± 0.41 | 95.01 ± 0.30 | 6.04 ± 0.86 | 6.61 ± 0.39 | 85.73 ± 0.65 | 26.72 ± 11.70 |
| safety+math | mergealign | N/A | --- | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 86.25 ± 0.00 | 15.73 ± 3.41 |
| safety+math | safemerge | N/A | 5.25 ± 9.09 | 4.61 ± 7.99 | 4.61 ± 7.99 | 95.57 ± 7.68 | 90.96 ± 15.67 | 1.30 ± 0.86 | 6.67 ± 4.86 | 82.50 ± 1.74 | 13.09 ± 1.77 |
| safety+math | sst | 0.60 | 17.15 ± 4.99 | 17.09 ± 5.01 | 17.09 ± 5.01 | 99.51 ± 0.40 | 82.42 ± 4.83 | 7.03 ± 0.72 | 6.72 ± 0.95 | 72.55 ± 15.91 | 22.48 ± 8.92 |
| safety+math | task_arithmetic | 0.60 | 2.48 ± 2.89 | 2.48 ± 2.89 | 2.48 ± 2.89 | 99.92 ± 0.14 | 97.44 ± 2.85 | 6.88 ± 1.56 | 7.50 ± 0.68 | 75.21 ± 15.93 | 27.18 ± 6.92 |
| safety+math | ties | 0.60 | 9.04 ± 5.55 | 9.03 ± 5.55 | 9.03 ± 5.55 | 99.95 ± 0.09 | 90.91 ± 5.56 | 5.94 ± 0.83 | 6.15 ± 0.18 | 85.00 ± 2.44 | 27.65 ± 3.07 |
| safety+math+code+medical | dare | 0.60 | 0.08 ± 0.08 | 0.08 ± 0.08 | 0.08 ± 0.08 | 69.23 ± 52.81 | 69.15 ± 52.74 | 0.00 ± 0.00 | 0.00 ± 0.00 | 38.02 ± 41.77 | 11.53 ± 0.23 |
| safety+math+code+medical | data_free_sst | 0.60 | 0.20 ± 0.08 | 0.08 ± 0.00 | 0.08 ± 0.00 | 48.26 ± 22.46 | 48.18 ± 22.46 | 0.00 ± 0.00 | 0.00 ± 0.00 | 26.67 ± 24.56 | 11.85 ± 0.59 |
| safety+math+code+medical | della | 0.60 | 0.09 ± 0.01 | 0.08 ± 0.00 | 0.08 ± 0.00 | 86.24 ± 20.68 | 86.16 ± 20.68 | 0.00 ± 0.00 | 0.00 ± 0.00 | 15.42 ± 16.18 | 12.53 ± 0.78 |
| safety+math+code+medical | matena_fisher | N/A | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 10.25 ± 2.01 | 10.25 ± 2.01 | 0.83 ± 0.09 | 0.00 ± 0.00 | 27.81 ± 3.29 | 13.12 ± 0.12 |
| safety+math+code+medical | sst | 0.60 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 31.47 ± 12.34 | 31.47 ± 12.34 | 0.42 ± 0.18 | 0.00 ± 0.00 | 57.29 ± 17.67 | 10.16 ± 0.49 |
| safety+math+code+medical | task_arithmetic | 0.60 | 6.50 ± 0.63 | 5.88 ± 0.55 | 5.88 ± 0.55 | 78.43 ± 8.47 | 72.55 ± 9.00 | 2.55 ± 0.39 | 0.05 ± 0.09 | 65.42 ± 9.24 | 13.26 ± 1.65 |
| safety+math+code+medical | ties | 0.60 | 0.08 ± 0.00 | 0.05 ± 0.05 | 0.05 ± 0.05 | 66.64 ± 57.71 | 66.59 ± 57.67 | 0.00 ± 0.00 | 0.00 ± 0.00 | 9.17 ± 7.94 | 12.28 ± 0.40 |
| safety+medical | dare | 0.60 | 0.03 ± 0.05 | 0.03 ± 0.05 | 0.03 ± 0.05 | 77.76 ± 13.44 | 77.74 ± 13.41 | 0.00 ± 0.00 | 0.00 ± 0.00 | 22.08 ± 10.81 | 12.39 ± 0.44 |
| safety+medical | data_free_sst | 0.60 | 0.45 ± 0.56 | 0.05 ± 0.05 | 0.05 ± 0.05 | 42.66 ± 37.11 | 42.60 ± 37.15 | 0.00 ± 0.00 | 0.00 ± 0.00 | 61.67 ± 41.50 | 12.27 ± 0.07 |
| safety+medical | della | 0.60 | 0.23 ± 0.40 | 0.03 ± 0.05 | 0.03 ± 0.05 | 33.68 ± 40.71 | 33.65 ± 40.72 | 0.00 ± 0.00 | 0.00 ± 0.00 | 27.29 ± 23.45 | 12.10 ± 1.01 |
| safety+medical | matena_fisher | N/A | 0.16 ± 0.00 | 0.16 ± 0.00 | 0.16 ± 0.00 | 99.28 ± 1.24 | 99.12 ± 1.24 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 12.99 ± 0.18 |
| safety+medical | mergealign | N/A | --- | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 86.25 ± 0.00 | 13.76 ± 3.41 |
| safety+medical | safemerge | N/A | 0.03 ± 0.05 | 0.03 ± 0.05 | 0.03 ± 0.05 | 100.00 ± 0.00 | 99.97 ± 0.05 | 1.09 ± 1.89 | 3.91 ± 6.77 | 53.44 ± 10.84 | 12.81 ± 1.63 |
| safety+medical | sst | 0.60 | 0.08 ± 0.00 | 0.05 ± 0.05 | 0.05 ± 0.05 | 65.42 ± 56.69 | 65.37 ± 56.64 | 0.00 ± 0.00 | 0.00 ± 0.00 | 9.69 ± 8.46 | 12.06 ± 0.13 |
| safety+medical | task_arithmetic | 0.60 | 0.16 ± 0.00 | 0.16 ± 0.00 | 0.16 ± 0.00 | 99.82 ± 0.18 | 99.66 ± 0.18 | 0.00 ± 0.00 | 0.00 ± 0.00 | 13.85 ± 0.18 | 12.72 ± 0.06 |
| safety+medical | ties | 0.60 | 0.06 ± 0.05 | 0.05 ± 0.05 | 0.05 ± 0.05 | 80.93 ± 19.76 | 80.87 ± 19.72 | 0.00 ± 0.00 | 0.00 ± 0.00 | 13.54 ± 0.36 | 11.90 ± 0.62 |
| MedAlpaca | Base | N/A | 6.11 ± 0.00 | 5.17 ± 0.00 | 5.17 ± 0.00 | 84.53 ± 0.00 | 79.36 ± 0.00 | 4.53 ± 0.00 | 3.59 ± 0.00 | 52.81 ± 0.00 | 20.28 ± 0.00 |
| SafetyFT | Base | N/A | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 100.00 ± 0.00 | 100.00 ± 0.00 | 0.52 ± 0.48 | 4.22 ± 3.39 | 43.49 ± 11.80 | 11.38 ± 0.41 |
| WizardCoder | Base | N/A | 26.77 ± 0.00 | 24.69 ± 0.00 | 24.69 ± 0.00 | 91.08 ± 0.00 | 66.40 ± 0.00 | 4.53 ± 0.00 | 21.03 ± 0.00 | 54.53 ± 0.00 | 18.41 ± 0.00 |
| WizardMath | Base | N/A | 32.97 ± 0.00 | 31.01 ± 0.00 | 31.01 ± 0.00 | 93.61 ± 0.00 | 62.60 ± 0.00 | 6.41 ± 0.00 | 3.12 ± 0.00 | 55.00 ± 0.00 | 14.02 ± 0.00 |

- 出典: `v5/outputs/tables/flmsec_main_alpha0.6_or_legacy.md`、manifest: `v5/outputs/tables/flmsec_main_alpha0.6_or_legacy.md.manifest.json`、元の結果ファイル 1292 件

#### 論文の表との照合（件数）

- tab:evaluation_main_alpha06_safety: {"both_na": 6, "match": 126, "mismatch": 84}（出典: `v5/outputs/tables/paper_comparison.json`、詳細: `v5/outputs/tables/paper_comparison.md`）
- tab:evaluation_main_alpha06_utility: {"match": 216}（出典: `v5/outputs/tables/paper_comparison.json`、詳細: `v5/outputs/tables/paper_comparison.md`）

### 2.2 safety-utility 曲線と観測事実（FR3.2、FR1.5）

- 図: ![pareto_safety_code](../../outputs/figures/pareto_safety_code.png)（出典: `v5/outputs/figures/pareto_safety_code.png`、manifest: `v5/outputs/figures/pareto_safety_code.png.manifest.json`、元の結果ファイル 1320 件）
- 図: ![pareto_safety_math](../../outputs/figures/pareto_safety_math.png)（出典: `v5/outputs/figures/pareto_safety_math.png`、manifest: `v5/outputs/figures/pareto_safety_math.png.manifest.json`、元の結果ファイル 1405 件）
- 図: ![pareto_safety_math_code_medical](../../outputs/figures/pareto_safety_math_code_medical.png)（出典: `v5/outputs/figures/pareto_safety_math_code_medical.png`、manifest: `v5/outputs/figures/pareto_safety_math_code_medical.png.manifest.json`、元の結果ファイル 1223 件）
- 図: ![pareto_safety_medical](../../outputs/figures/pareto_safety_medical.png)（出典: `v5/outputs/figures/pareto_safety_medical.png`、manifest: `v5/outputs/figures/pareto_safety_medical.png.manifest.json`、元の結果ファイル 1287 件）

#### 観測事実（厳密な Pareto 支配と近傍比較。機構の解釈はここでは書かない）

- safety+code: 点 40 個、VRR ≥ 80% で残った点 26 個、除外した点 14 個（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0、VRR 77.03%、理由: VRR 77.03 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.2、VRR 70.30%、理由: VRR 70.30 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.6、VRR 77.09%、理由: VRR 77.09 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.8、VRR 68.01%、理由: VRR 68.01 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: della@0、VRR 76.35%、理由: VRR 76.35 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0、VRR 76.96%、理由: VRR 76.96 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0.2、VRR 76.93%、理由: VRR 76.93 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0.8、VRR 73.78%、理由: VRR 73.78 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: led_merging@N/A、VRR 78.14%、理由: VRR 78.14 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: matena_fisher@N/A、VRR 59.73%、理由: VRR 59.73 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: mergealign@N/A、VRR 0.00%、理由: VRR 0.00 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.4、VRR 79.61%、理由: VRR 79.61 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.6、VRR 61.37%、理由: VRR 61.37 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.8、VRR 55.32%、理由: VRR 55.32 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - code: 支配されない点 ['task_arithmetic@0', 'task_arithmetic@0.8', 'ties@1']、支配される点 23 個、近傍比較 160 組（出典: `v5/outputs/figures/observations.json`）
- safety+math: 点 40 個、VRR ≥ 80% で残った点 38 個、除外した点 2 個（出典: `v5/outputs/figures/observations.json`）
  - 除外: led_merging@N/A、VRR 78.12%、理由: VRR 78.12 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: mergealign@N/A、VRR 0.00%、理由: VRR 0.00 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - math: 支配されない点 ['sst@1']、支配される点 37 個、近傍比較 82 組（出典: `v5/outputs/figures/observations.json`）
- safety+math+code+medical: 点 37 個、VRR ≥ 80% で残った点 15 個、除外した点 22 個（出典: `v5/outputs/figures/observations.json`）
  - 除外: dare@0.6、VRR 69.23%、理由: VRR 69.23 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: dare@0.8、VRR 65.48%、理由: VRR 65.48 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0、VRR 75.57%、理由: VRR 75.57 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.2、VRR 39.75%、理由: VRR 39.75 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.4、VRR 56.33%、理由: VRR 56.33 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.6、VRR 48.26%、理由: VRR 48.26 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.8、VRR 55.06%、理由: VRR 55.06 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@1、VRR 48.25%、理由: VRR 48.25 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: della@0、VRR 69.31%、理由: VRR 69.31 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0、VRR 75.84%、理由: VRR 75.84 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0.2、VRR 3.66%、理由: VRR 3.66 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0.4、VRR 0.00%、理由: VRR 0.00 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0.6、VRR 31.47%、理由: VRR 31.47 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0.8、VRR 23.53%、理由: VRR 23.53 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@1、VRR 30.16%、理由: VRR 30.16 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: matena_fisher@N/A、VRR 10.25%、理由: VRR 10.25 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: task_arithmetic@0.2、VRR 1.23%、理由: VRR 1.23 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: task_arithmetic@0.4、VRR 50.67%、理由: VRR 50.67 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: task_arithmetic@0.6、VRR 78.43%、理由: VRR 78.43 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.4、VRR 66.67%、理由: VRR 66.67 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.6、VRR 66.64%、理由: VRR 66.64 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.8、VRR 66.69%、理由: VRR 66.69 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - code: 支配されない点 ['ties@1']、支配される点 14 個、近傍比較 83 組（出典: `v5/outputs/figures/observations.json`）
  - math: 支配されない点 ['task_arithmetic@0.8', 'ties@1']、支配される点 13 個、近傍比較 83 組（出典: `v5/outputs/figures/observations.json`）
  - medical: 支配されない点 ['della@0.8', 'task_arithmetic@1', 'ties@0', 'ties@0.2']、支配される点 11 個、近傍比較 83 組（出典: `v5/outputs/figures/observations.json`）
- safety+medical: 点 39 個、VRR ≥ 80% で残った点 20 個、除外した点 19 個（出典: `v5/outputs/figures/observations.json`）
  - 除外: dare@0.4、VRR 58.00%、理由: VRR 58.00 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: dare@0.6、VRR 77.76%、理由: VRR 77.76 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: dare@0.8、VRR 69.52%、理由: VRR 69.52 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.6、VRR 42.66%、理由: VRR 42.66 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@0.8、VRR 58.86%、理由: VRR 58.86 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: data_free_sst@1、VRR 68.12%、理由: VRR 68.12 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: della@0、VRR 72.00%、理由: VRR 72.00 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: della@0.2、VRR 32.37%、理由: VRR 32.37 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: della@0.4、VRR 51.04%、理由: VRR 51.04 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: della@0.6、VRR 33.68%、理由: VRR 33.68 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: della@0.8、VRR 47.00%、理由: VRR 47.00 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@0.6、VRR 65.42%、理由: VRR 65.42 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: sst@1、VRR 72.12%、理由: VRR 72.12 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: mergealign@N/A、VRR 0.00%、理由: VRR 0.00 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: task_arithmetic@0.2、VRR 24.84%、理由: VRR 24.84 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: task_arithmetic@0.4、VRR 11.11%、理由: VRR 11.11 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: task_arithmetic@0.8、VRR 6.79%、理由: VRR 6.79 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.4、VRR 60.36%、理由: VRR 60.36 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - 除外: ties@0.8、VRR 78.80%、理由: VRR 78.80 < 下限 80（出典: `v5/outputs/figures/observations.json`）
  - medical: 支配されない点 ['dare@1', 'sst@0.4']、支配される点 18 個、近傍比較 152 組（出典: `v5/outputs/figures/observations.json`）

### 2.3 SST のアブレーション（FR3.3）

- ablation_datafree_safety_code: N/A のセル 36 個（出典: `v5/outputs/tables/ablation_datafree_safety_code.md`、欠損の一覧: `v5/outputs/tables/ablation_datafree_safety_code.md.manifest.json`）
- ablation_datafree_safety_math: N/A のセル 36 個（出典: `v5/outputs/tables/ablation_datafree_safety_math.md`、欠損の一覧: `v5/outputs/tables/ablation_datafree_safety_math.md.manifest.json`）
- ablation_datafree_safety_math_code_medical: N/A のセル 42 個（出典: `v5/outputs/tables/ablation_datafree_safety_math_code_medical.md`、欠損の一覧: `v5/outputs/tables/ablation_datafree_safety_math_code_medical.md.manifest.json`）
- ablation_datafree_safety_medical: N/A のセル 36 個（出典: `v5/outputs/tables/ablation_datafree_safety_medical.md`、欠損の一覧: `v5/outputs/tables/ablation_datafree_safety_medical.md.manifest.json`）
- ablation_sst_safety_code: N/A のセル 36 個（出典: `v5/outputs/tables/ablation_sst_safety_code.md`、欠損の一覧: `v5/outputs/tables/ablation_sst_safety_code.md.manifest.json`）
- ablation_sst_safety_math: N/A のセル 36 個（出典: `v5/outputs/tables/ablation_sst_safety_math.md`、欠損の一覧: `v5/outputs/tables/ablation_sst_safety_math.md.manifest.json`）
- ablation_sst_safety_math_code_medical: N/A のセル 48 個（出典: `v5/outputs/tables/ablation_sst_safety_math_code_medical.md`、欠損の一覧: `v5/outputs/tables/ablation_sst_safety_math_code_medical.md.manifest.json`）
- ablation_sst_safety_medical: N/A のセル 36 個（出典: `v5/outputs/tables/ablation_sst_safety_medical.md`、欠損の一覧: `v5/outputs/tables/ablation_sst_safety_medical.md.manifest.json`）

### 2.4 仮説 V1〜V11 の判定（FR2.3）

- V1 FIM の 0 の割合（fp16 キャスト後）: **支持**。指標 frac_tensors_fh_zero_over_80pct = 0.6042。frac_tensors_fh_zero_over_80pct=0.6041666666666666 が支持の基準 {'op': '>=', 'value': 0.1} を満たす（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V2 実際のマスク比率と inf の数: **支持**。指標 frac_tensors_mask_or_inf_abnormal = 0.75。frac_tensors_mask_or_inf_abnormal=0.75 が支持の基準 {'op': '>=', 'value': 0.1} を満たす（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V3 マスクの中身が FIM に依存しているか: **判定不能**。指標 median_jaccard_fhfb_vs_magnitude = 0.2003。median_jaccard_fhfb_vs_magnitude=0.2003062665462494 は支持の基準 {'op': '>=', 'value': 0.5} と反証の基準 {'op': '<=', 'value': 0.2} の間にあり、要因を切り分けられない（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V4 fp16 の丸めで安全成分が消える割合: **判定不能**。指標 mean_frac_alpha_delta_below_half_ulp = 0.0443。mean_frac_alpha_delta_below_half_ulp=0.04430361526938791 は支持の基準 {'op': '>=', 'value': 0.1} と反証の基準 {'op': '<=', 'value': 0.01} の間にあり、要因を切り分けられない（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V5 注入された安全成分の量: **不支持**。指標 median_ratio_sst_over_ta_injection = 1。median_ratio_sst_over_ta_injection=0.9999929953565267 が反証の基準 {'op': '>=', 'value': 0.9} を満たす（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V6 WizardMath の系統: **不支持**。指標 ratio_wizardmath_over_mean_others_rel_diff = 0.02042。ratio_wizardmath_over_mean_others_rel_diff=0.020418455777860715 が反証の基準 {'op': '<=', 'value': 1.2} を満たす（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V7 merge 済み code モデルの位置符号化: **支持**。指標 merged_code_rope_theta_mismatch_fraction = 1。merged_code_rope_theta_mismatch_fraction=1.0 が支持の基準 {'op': '>=', 'value': 0.5} を満たす（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V8 FIM データが実データか: **不支持**。指標 placeholder_fraction = 0。placeholder_fraction=0.0 が反証の基準 {'op': '<=', 'value': 0.0} を満たす（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V9 mergekit 出力の語彙の扱い: **不支持**。指標 n_vocab_mismatch_models = 0。n_vocab_mismatch_models=0 が反証の基準 {'op': '<=', 'value': 0} を満たす（実行範囲: {"full_patterns": true, "full_seeds": true, "layers": null, "max_models": null, "max_tensors": null, "patterns": ["safety+math", "safety+code", "safety+medical", "safety+math+code+medical"], "random_seed": 0, "seeds": [42, 43, 44], "spearman_samples": 1000000}、出典: `v5/outputs/hypotheses/v1_v9.json`）
- V10 論文に近い条件の結果が v3 にあるか: **支持**。指標 frac_paper_like_conditions_evaluated = 0.6667。frac_paper_like_conditions_evaluated=0.6666666666666666 が支持の基準 {'op': '>=', 'value': 0.5} を満たす（実行範囲: {}、出典: `v5/outputs/hypotheses/v10_v11.json`）
- V11 同じ JB での比較（SST と task_arithmetic）: **支持**。指標 sst_dominates_ta_panel_fraction = 0.6667。sst_dominates_ta_panel_fraction=0.6666666666666666 が支持の基準 {'op': '>=', 'value': 0.5} を満たす（実行範囲: {"tolerance_pt": 2.0, "vrr_floor": 80.0}、出典: `v5/outputs/hypotheses/v10_v11.json`）
<!-- 自動生成: 結果の節 終了 -->

## 3. 考察（FR4）

<!-- 手書き: 考察（FR4） 開始 -->
この節は、V1〜V11 全範囲の実行結果および探索スクリプト（`native_classifier_probe.py`、`gibberish_escape_probe.py`）の結果を見たうえで手書きした。各主張に、「観測事実」（既存の結果・キャッシュ・重みから直接確認できること）、「機構仮説」（FIM、マスク、補間方式などによる説明。確かめていない）、「新手法への示唆」の 3 段階を付けている。数値の出典は、2 節の表と `v5/outputs/` のファイルである。

### 3.0 最初に: 有害判定の 84 セル乖離と、ルールベース gibberish 判定をすり抜ける文字化け崩壊（FR1.3 の前提に関わる発見）

**観測事実**

- 論文（FLMSEC）の本文は、Conditional ASR を「共通の HarmBench Classifier」で求めると書く（`neurips_2026.tex` L283-287）。しかし、論文の表の Conditional ASR / VSR は、HarmBench 単独でも `generate_flmsec_hyo.py` の OR 判定でも再現できなかった（安全性の表 216 件のうち、126 件が一致、84 件が不一致、6 件が両方 N/A。一方、VRR・ベンチマーク ASR・有用性の表 216 件は全件一致。出典: `v5/outputs/tables/paper_comparison.md`）。
- 同じ結果ファイルで、`classifier_output`（ベンチマークごとの分類器：HarmBench は `Yes`、JailbreakBench / WildJailbreak は WildGuard の `Harmful response: yes`、StrongREJECT は `score >= 0.5`）で集計すると、論文の値と一致する組が多く見つかった（例: `safety+code` DARE 68.30 ± 2.33、DELLA 68.53 ± 1.44、`safety+medical` Task Arithmetic 63.87 ± 4.81、TIES 64.34 ± 6.74、Matena-Fisher 70.98 ± 0.01）。一方、わずかに差が残る組もあり、全 216 セルの完全照合は未実施のため、論文表の集計方法については**強い示唆にとどまる**（出典: `v5/outputs/probe/native_classifier_probe.md`）。
- 結果の読み取りが判定器で極端に割れる（α=0.6 の Conditional ASR）: `safety+code` の SST は HarmBench 単独 1.09 ± 0.43 に対しベンチマーク別分類器 63.91 ± 1.62、`safety+medical` の SST は 0.08 → 67.04、4 ドメインの SST は 0.00 → 68.40（出典: 同上）。
- **乖離の正体（文字化け崩壊のすり抜け）**: `is_gibberish=False`（現行ルール上は「妥当な応答」）とされた応答テキストを全 432 ファイルで検査したところ、異系統ドメインを含むパターンで深刻な多言語トークン崩壊（例: `eniumbresbresbres转х转хpatch...` のような無意味な文字化け）が大量にすり抜けていた（出典: `v5/outputs/probe/gibberish_escape_probe.md`、`v5/outputs/probe/gibberish_escape_probe.json`）:
  - `safety+medical`: `safemerge`（0.0%）を除く **全手法（dare / data_free_sst / della / sst / matena_fisher / task_arithmetic / ties）で、`is_gibberish=False` 応答の 100.0% が文字化け崩壊**。ベンチマーク別分類器のみ有害・HarmBench 無害となった乖離応答の **100.0%** がこの文字化けだった。
  - `safety+code`: `dare` 97.5%、`della` 96.6%、`data_free_sst` 96.3%、`sst` 89.1% が文字化け崩壊（乖離応答の 88.7〜97.7%）。例外は `safemerge`（0.0%）、`led_merging`（0.3%）、`task_arithmetic`（1.3%）。
  - `safety+math+code+medical`: `dare` / `della` / `ties` が 100.0%、`matena_fisher` 83.0%、`data_free_sst` 72.8%、`sst` 55.2%（`task_arithmetic` は 0.1%）。
  - `safety+math`: **全 10 手法とも 0.0〜0.4%**（文字化け崩壊はほぼ発生していない）。

**機構仮説**

- 現行のルールベース gibberish 判定（空文字、5 語以上でユニーク語率 < 20%、数字率 > 60%）は、空白を含まない多言語サブワード崩壊を検出できない。そのため異系統マージで崩壊したモデルが「高 VRR（見かけ上は妥当）」として残り、さらにその文字化け応答を WildGuard / StrongREJECT は誤って「有害（≒論文の 60〜70%）」、HarmBench 分類器は「無害（≒0%）」と両極端に分類したと考えられる。

**新手法への示唆**

- 現行の VRR ゲートだけでは多言語トークン崩壊を弾けないため、**非 ASCII 比率・無空白長文字列・文字種分布または軽量 PPL 等を含む拡張 gibberish 判定**を妥当性ゲートに組み込む必要がある。
- 安全性指標は HarmBench 単独（FR1.3 主軸）とベンチマーク別分類器の双方を併記し、両者で結論が割れる条件は文字化け崩壊や判定器バイアスの疑いとして切り分ける。

### 3.1 注入方式と異系統モデルの問題

**観測事実**

- **V6（不支持・全 3 ドメイン重みで確定）**: `Llama-2-7b-hf` からの層ごとの相対差分（中央値）は、WizardMath が **0.0274（2.74%）** であるのに対し、WizardCoder は **1.1347（113.5%）**、MedAlpaca は **1.5471（154.7%）**（比 `0.0204`）だった（出典: `v5/outputs/hypotheses/v1_v9.json`）。WizardMath は Llama-2 からの直接の FT である一方、WizardCoder（CodeLlama-Python 系）と MedAlpaca（LLaMA-1 系）は事前学習から別系統であることが重みレベルで確定した。これは 3.0 節の文字化け崩壊が `safety+code` / `safety+medical` / 4 ドメインに集中し、`safety+math`（0.0〜0.4%）で起きない事実と完全に整合する。
- **V5（不支持・全 2,688 テンソルで確定）**: 実 merge 済みモデル（α=0.6）における SST と Task Arithmetic の安全方向注入量比 `⟨θ_merged − θ_u, δ_s⟩_SST / ⟨θ_merged − θ_u, δ_s⟩_TA` は、**中央値 0.999993（ノルム比中央値 0.999995）** であり、「SST は常に注入量が少ない」という事前仮説は反証された（出典: `v5/outputs/hypotheses/v1_v9.json`）。分布を見ると、全 4 パターンとも p10 = 0.205〜0.225、p25 = 0.230〜0.296、**p50〜p75 = 1.000**、平均 = 0.696〜0.720 と二峰性になっている。
- **V7（支持・全 123 モデルで確定）**: `safety+code` の merge 済みモデル 123 件すべてで `rope_theta = 10000.0` となり、WizardCoder 基準値（`1000000.0`）と 100% 食い違っていた（出典: `v5/outputs/hypotheses/v1_v9.json`）。`safety+code` の Code 有用性は多くの手法で 0.00% に落ちる（WizardCoder 単体は 21.03%。例外は SafeMERGE 5.99%、LED-Merging 5.62%、Task Arithmetic 4.63%）。
- **`safety+math`（唯一同系統のパターン）における曲線比較**:
  - 同じ α=0.6 で比べると、SST は Conditional ASR 17.04 ± 4.81（HarmBench 単独）/ 29.57 ± 8.60（ベンチマーク別）で、TA の 2.40 ± 2.75 / 2.89 ± 3.59 より安全性が低い。
  - 一方、Pareto 曲線全体（`v5/outputs/figures/pareto_safety_math.points.json`）で見ると、`sst@0.6`（Cond. ASR 17.0%, Math 7.03%）vs `TA@0.4`（15.0%, 5.78%）、`sst@0.8`（2.74%, 8.44%）vs `TA@0.6`（2.40%, 6.88%）、`sst@1.0`（0.00%, 9.84%）vs `TA@0.8`（0.00%, 9.11%）と、**`safety+math` では SST の曲線がほぼ全域で TA を上回っている**。特に `sst@1.0` が唯一の非支配点（Math 9.84%）となるのは、SST が α=1.0 でも非退化層のマスク外座標および `norm` 層に `θ_u` を保持するためである（純粋な安全モデルに近づく `TA@1.0`・`DARE@1.0`・`DELLA@1.0`・`TIES@1.0` はすべて Math 0.57〜0.94% に急落する）。
  - ただし、`safety+math` 単体の Math 絶対値自体が低く（WizardMath 単体 6.41%、全マージ最大 9.84%）、V11 全体（全パターン合算）では `safety+code` で TA が SST を支配するなど優劣は一貫しない（出典: `v5/outputs/hypotheses/v10_v11.json`、`v5/outputs/figures/observations.json`）。

**機構仮説**

- V5 の二峰性（約 60% のテンソルで注入量比 1.000、残る約 40% で 0.20〜0.30）は、後述の V1・V2（fp16 キャストによるマスク全 1 退化）で直接説明できる。つまり v3 の SST は「全層で 20% 選択」として動いていたのではなく、**約 60% のテンソル（特に後半層 L24–31）が Task Arithmetic に退化し、残る約 40%（主に中間層 L8–23）だけが疎な 20〜30% 補間として動いていた**。その結果、同じ α=0.6 では非退化層の分だけ TA より注入が少なくなり、逆に α=0.8〜1.0 では非退化層＋norm のユーティリティ保持が効いて `safety+math` の Pareto 曲線を押し上げた可能性がある（未検証）。
- `safety+code` と `safety+medical` の崩壊は、異系統重みの座標単位混合（V6）と `rope_theta` 喪失（V7）が主因である可能性が高い。

**新手法への示唆**

- マージ実行前にベースとドメインモデルの系統整合性（相対差分と `config.json`）を検証し、ユーティリティ側の `rope_theta`・語彙設定を引き継ぐ（E5・E7）。
- 同じ α ではなく、実効注入ノルムまたは細かい α 格子の Pareto 曲線で比較する（E3）。

### 3.2 FIM 選択の問題

**観測事実**

- **V1（支持・全 672 テンソルで確定）**: `F_h`（harmful FIM）のゼロ率は fp32 時点では平均 **0.0025%**（`2.47e-5`）だが、v3 実装どおり fp16 にキャストすると平均 **79.24%**（最大 **99.53%**）が 0 にアンダーフローし、**60.4%（406 / 672 テンソル）** が 80% 超（k=0.2 のマスクが全 1 に退化する条件）に達した（出典: `v5/outputs/hypotheses/v1_v9.json`）。
- **V2（支持・全 2,688 テンソルで確定）**: 期待値 k=0.20 からの乖離（±0.05 超）または inf 異常を示すテンソルは **75.0%（2,016 / 2,688 テンソル）**、**平均マスク比率は 70.4%**、うち **60.4%（1,624 / 2,688 テンソル）が完全に `mask_ratio = 1.0`（全座標 1）に退化**していた（`inf` 総数 17,813）。層別の全 1 退化率は、L0–7: 58.9%（平均マスク 0.693）、L8–15: 39.3%（0.548）、L16–23: 54.2%（0.660）、**L24–31: 89.3%（0.916）** であり、出力に近い後半層ほどほぼ完全に Task Arithmetic 化していた（出典: 同上）。
- **V3（判定不能・全 2,688 テンソルで確定）**: `median_jaccard_fhfb_vs_magnitude = 0.2003`、`median_jaccard_fhfb_vs_random = 0.2000`、`median_spearman_lambda_vs_abs_delta_s = -0.0026`（出典: 同上）。事前登録基準（0.20〜0.50 の間）により「判定不能」となったが、これは **中央値テンソルの `Fh/Fb` マスクが `mask_ratio = 1.0`（全 1）に退化しているため、任意の上位 20% マスク（`|δ_s|` や `random`）との Jaccard 係数が機械的に 0.20 / 1.00 = 0.20 に張り付いた結果** である（「FIM が独立に座標を選んでいる」証拠ではない）。
- **V4（判定不能・全 2,016 テンソルで確定）**: α=0.6 での fp16 丸め消失率（`|α·δ_s| < ulp_fp16(θ_u)/2`）は平均 **4.43%**（最大 **15.25%**）。事前登録基準（0.01〜0.10 の間）で判定不能であり、V1・V2 の大規模退化（平均マスク 70.4%）と比べると副次的な影響にとどまる（出典: 同上）。
- **V8・V9（不支持・全範囲で確定）**: FIM データのプレースホルダ率は 0.0%（`fim_harmful` 1,400 件、各 benign 1,000 件）、mergekit 出力（288 モデル）の `vocab_size` と `lm_head` 行数の不一致は 0 件。確認した範囲では原因ではない（出典: 同上）。
- **V10（支持）**: 論文に近いアブレーション条件 6 種のうち 4 種（additive、layerwise 3 種）が存在し、k=0.05 と k=0.1 は欠損。ただし評価済みはすべて k=0.2・seed 42 のみで、表の `± 0.00` は seed 1 本のため不確実性を示さない（出典: `v5/outputs/hypotheses/v10_v11.json`、`v5/outputs/tables/ablation_sst_safety_math.md`）。

**機構仮説**

- v3 で SST-Merge が他手法と明確な差を出せなかった **最大の実装上の原因** は、`scripts/mergers/fim.py` L161 の fp16 キャストによる FIM アンダーフロー（V1）と、それに伴う 60.4% のテンソルでのマスク全 1 退化・平均マスク比率 70.4% 化（V2・V5）である。これにより、SST は本来の「上位 20% の座標選択」ではなく、特に出力側（L24–31 の 89.3%）でほぼ Task Arithmetic と同一の演算を行っていた。
- したがって、fp32 で正しく λ と top-k を計算した場合に FIM 選択が `|δ_s|` や `random` を上回るかどうか自体は、v3 の既存結果からはまだ検証できていない（マスク退化が交絡しているため）。

**新手法への示唆**

- FIM の推定・保存・λ 計算・マスク生成は **すべて fp32 のまま行う**（fp16 へのキャストを禁止する）。あわせて、マージ時にテンソルごとの実効マスク比率・ゼロ率・`inf` 数を `merge_metadata.json` に必ず記録し、退化を即時検知する（E6）。

### 3.3 ハイパーパラメータの問題

**観測事実**

- アブレーションで評価済みの k は 0.2 のみ、seed は 42 のみ（V10）。k の掃引効果は v3 の結果からは評価できない。
- α の格子は 6 点（0.0〜1.0 の 0.2 刻み）で、論文（SAGAI_EN_sst）の 15 点より粗い。VRR ≥ 80% で残る点は、`safety+code` で 26 / 40、`safety+math` で 38 / 40、`safety+medical` で 20 / 39、4 ドメインで 15 / 37 である（出典: `v5/outputs/figures/observations.json`）。4 ドメインでは、SST の全点（α=0〜1）が VRR < 80% で除外された（α=0.2, 0.4 で VRR 3.66%, 0.00%）。

**機構仮説**

- 4 ドメインでの VRR 崩壊は、異系統 2 モデル（CodeLlama / LLaMA-1）を含む 3 ドメイン平均差分 `δ̄_u` への干渉と、60% 超の全 1 退化マスクによる過剰注入が重なった結果と考えられる（未検証）。

**新手法への示唆**

- fp32 修正（E6）および同系統モデル条件のもとで、k と細かい α 格子（複数 seed）を再評価しない限り、ハイパーパラメータの最適領域は確定できない（判定不能）。

### 3.3.1 論文（SAGAI_EN_sst）の定式化と、v3 の実装の違い（FR4.3）

出典は `aidlc/spaces/default/codekb/v3/code-quality-assessment.md` の「SAGAI_EN_sst の主張を v3 の大規模実験で再現できるか」と、`architecture.md` の「論文（SAGAI_EN_sst）とコードの対応表」である（コードと論文の読解による）。

**観測事実（コードと論文で確認）**

- 式（λ = F_h/(F_b+ε)、hard mask、interpolation / additive、ε=10⁻⁶、N=500）は論文と v3 で同じである。
- 一方、v3 の大規模実験は次の点で論文（および実実装の v1）の条件を含まない: ベースが違う（論文/v1 は Llama-3.1-8B-Instruct、v3 は Llama-2-7b-hf）、ユーティリティが同一ベースの LoRA でなく外部フル FT モデル（うち 2 種は V6 で異系統と確定）、アダプタ単位でなくフル重みマージ、Additive soft mask が結果に無い、k の掃引が無い（k=0.2 のみ）、モジュール種別の層重みが無い、k が全体比率でなくテンソルごと、α 格子が粗い、さらに v3 では fp16 キャストにより 60.4% のテンソルが全 1 マスクに退化していた（V1・V2）。
- F_h を Safety モデルで評価する点は v1 の原実装からの引き継ぎであり、v3 固有のずれではない。

**機構仮説**

- これら実験条件の不一致に加え、v3 実装固有の fp16 FIM 退化（V1・V2）と異系統モデルによる文字化け崩壊（V6・3.0 節）が重なったため、v3 では SST-Merge の本来の選択効果が観測できなかったと考えられる。

**新手法への示唆**

- 本来の選択効果を検証するには、同一ベース派生モデル（または LoRA 単位）・fp32 FIM・適切な α/k 格子での再実験が必要である（設計案の未検証項目に整理）。

### 3.4 まとめ

| 原因の分類 | 観測事実で言えること（全範囲検証済み） | 判定 |
|:---|:---|:---|
| FIM 選択（fp16 退化） | **V1 支持（60.4% が 0 率 80% 超、平均 79.2%）**、**V2 支持（75.0% 異常、平均マスク 70.4%、60.4% が全 1 退化、L24–31 は 89.3%）**、**V5 不支持（注入量比中央値 1.000）**。V3 の Jaccard=0.200 は全 1 退化の必然的帰結。V4 は平均 4.43%（副次的）。V8・V9 は不支持 | **最有力な実装原因（観測事実で確定）**。fp32 修正後の FIM 選択の有効性自体は未検証 |
| 異系統モデルと文字化け崩壊 | **V6 で WizardMath（相対差分 2.74%）のみ同系統、WizardCoder（113.5%）と MedAlpaca（154.7%）は異系統と確定**。異系統パターンでは `is_gibberish=False` をすり抜ける多言語文字化けが 89〜100% 発生（`safety+math` は 0.0〜0.4%） | **評価崩壊・有用性崩壊の主因（観測事実で確定）** |
| 評価（判定器）の違い | 論文の表はベンチマーク別分類器で作られている強い示唆（84 セル不一致）。異系統の文字化けを WildGuard/StrongREJECT が有害、HarmBench が無害と両極端に誤判定している | **観測事実**（論文表の完全再現は全 216 セル照合が別途必要） |
| 注入方式 | V5 により中央値では TA と同一注入量だが、非退化層（約 40%）では 20〜30% 注入。同系統の `safety+math` では Pareto 曲線全体で SST が TA を上回る（特に `sst@1.0` は Math 9.84% を保持） | **観測事実**（Math 絶対値が小さく有意性確認は新実験が必要） |
| 設定の食い違い（`rope_theta`） | **V7 支持**: `safety+code` の merge 済みモデル 123 件すべてで `rope_theta = 10000.0`（基準 `1000000.0` と不一致） | **観測事実**（有用性回復幅は未検証） |
| ハイパーパラメータ | k の掃引結果が欠損（V10: k=0.2、seed 42 のみ） | **判定不能** |

制約: 評価は各ベンチマーク最大 320 件・seed 3 本（アブレーションは 1 本）であり、math の有用性の絶対値が小さい。v1 に関する追加確認（V12〜V16）は依頼者の方針で補足にとどめた。
<!-- 手書き: 考察（FR4） 終了 -->

## 4. 新しい merge 手法の設計案（FR5）

<!-- 手書き: 設計案（FR5） 開始 -->
この節は、3 節の全範囲検証結果を見たうえで手書きした。述べるのは、既存の結果から言える範囲の「可能性」までである。新手法が既存手法より優れているとは、新しい実験なしには断定できない。

### 4.1 前提（設計の入力にした観測事実）

- F1: FLMSEC 論文の安全性表はベンチマーク別分類器で作られている強い示唆があり、同じ結果ファイルでも判定器によって安全性の読み取りが 0% と 68% ほど大きく変わる（3.0 節）。
- F2: `safety+medical`（MedAlpaca: 相対差分 154.7%）と `safety+code`（WizardCoder: 相対差分 113.5%）では、異系統マージによる多言語文字化け崩壊が現行のルールベース gibberish 判定（`is_gibberish=False`）を 89〜100% すり抜け、偽の高 VRR と分類器間の大乖離を生んでいる。一方、同系統の `safety+math`（WizardMath: 相対差分 2.74%）では文字化け崩壊は 0.0〜0.4% にとどまる（3.0 節・V6）。
- F3: v3 の SST-Merge は fp16 キャストにより 60.4% のテンソルで `F_h` の 80% 超が 0 にアンダーフローし（V1）、75.0% のテンソルでマスク比率が異常化（平均マスク 70.4%、L24–31 は 89.3% が全 1 退化。V2）、実 merge モデルでも中央値で TA と同一の注入量（比 1.000）になっていた（V5）。
- F4: 同系統の `safety+math` に限ると、非退化層（約 40%）と `norm` のユーティリティ保持が効き、SST の Pareto 曲線はほぼ全域で TA を上回り、`sst@1.0` が唯一の非支配点（Cond. ASR 0.00%, Math 9.84%）となった（3.1 節）。
- F5: 4 ドメインでは VRR が大きく落ち（観測点の 22 / 37 が VRR < 80% で除外）、`safety+code` の merge 済みモデル 123 件すべてで `rope_theta` が WizardCoder と食い違っている（V7）。
- F6: 判定器をどちらにしても、`safety+code` と `safety+medical` で文字化け崩壊 0.0%・VRR ≥ 99.9%・低 Conditional ASR（ベンチマーク別 0.31 / 0.22）を両立した手法は SafeMERGE のみだった（ただし `safety+math` では seed ばらつき 21.42 ± 37.09 と大きい。出典: `v5/outputs/probe/native_classifier_probe.md`、`v5/outputs/probe/gibberish_escape_probe.md`）。

### 4.2 候補要素と、3 段階の区別

| # | 候補要素（DLSP_hiromi2 に導入する設計） | 観測事実（根拠） | 機構仮説 | 未検証の部分（新しい実験が要る） |
|:---|:---|:---|:---|:---|
| E0 | **拡張妥当性ゲート（文字化け検出つき VRR）** と複数判定器による評価 | F1・F2: 現行 VRR をすり抜けた文字化けが 89〜100% 存在し、判定器で 0% vs 68% に割れた | 非 ASCII 比率・無空白長文字列・軽量 PPL で文字化けを弾けば、偽の妥当性と判定器乖離を防げる | 拡張ルールの偽陽性/偽陰性、人手判定との一致 |
| E1 | 拡張 VRR 制約つきの Pareto 選択（補間しない） | F5: 4 ドメインで多くの点が崩壊し、VRR 下限で除外される | 崩壊モデルを安全と誤認する選択を防ぐ | 保持データでの汎化、VRR 下限（80%）の最適値 |
| E2 | **FIM と λ の完全 fp32 保持＋マスク退化監視** | F3（V1・V2・V5 確定）: fp16 キャストで 60.4% のテンソルが全 1 退化し、中央値で TA と同一注入になった | fp32 のまま λ と top-k（および全体 top-k / log 空間 soft mask）を計算すれば、本来の疎な安全座標選択が機能する | fp32 修正後の FIM 選択が `|δ_s|` や `random` を実際に上回るか（新実験が必要） |
| E3 | 注入量整合と細かい α 格子での探索 | F3・F4: 疎な選択層では同じ α で注入ノルムが減り、α=0.6 固定比較では不利に見える | 疎選択によるノルム減衰を補償する α 格子を含めることで、公平かつ最適な動作点が見つかる | α 格子拡張時の Pareto 改善幅 |
| E4 | 選択的な層（または低ランク部分空間）への適用 | F4・F6: `safety+math` で非退化層＋norm 保持が有用性を守り、`safety+code`/`medical` では SafeMERGE のみ文字化け 0%・高安全を達成 | 全重み一律混合より、安全寄与の大きい層・低ランク部分空間への限定適用が破壊的干渉を抑える | 層選択基準（層別 λ 集計 vs コサイン類似度）、`safety+math` の seed ばらつき抑制 |
| E5 | **系統整合性チェックと設定引き継ぎ**（`rope_theta`・語彙） | F2（V6）・F5（V7）: 相対差分 > 100% の異系統混合で 89〜100% 崩壊、`safety+code` は 100% `rope_theta` 不一致 | 同系統条件の強制とユーティリティ側 config の継承で、位置符号化崩れや文字化け崩壊を防げる | 設定修正・同系統モデル化による Code/Medical 有用性の回復幅 |

「適した要素」の採用基準（1.2 節）に照らすと、異系統崩壊と fp16 退化が交絡した既存の v3 結果単独では、全パターンを通じて基準 1〜3 を満たす手法要素は確定していない（同系統の `safety+math` では SST が非支配点となったが、他パターンでは異系統崩壊と退化が支配的だった）。したがって、E0〜E5 は「観測された失敗機構の確実な除去」と「同系統条件での有望な選択機構の再構築」に基づく設計候補である。

### 4.3 設計案（文章と擬似コード）

名前（仮）: **fp32 退化防止・拡張妥当性ゲートつき選択的 SST（Safe-Gated fp32 SST-Merge）**。
DLSP_hiromi2 の secure merge 枠組みに、fp32 FIM による本来の疎選択（E2）、系統・設定チェック（E5）、注入量整合（E3）、および文字化け検出を含む拡張妥当性ゲート（E0・E1）を組み込む。

```
入力: θ0（ベース）、θ_u（ユーティリティモデル。複数可）、θ_s（安全パッチ）、
      較正データ（安全用 D_h、有用性用 D_b）、k、α の格子 A、拡張 VRR 下限 v

1. 系統整合性チェックと設定引き継ぎ（E5）
   for 各 θ_u,j:
       rel_diff = median_layer(‖θ_u,j - θ0‖ / ‖θ0‖)
       if rel_diff > 0.5:
           警告し、フル重み座標混合ではなく LoRA 射影／層選択経路（E4）を推奨
   merged_config = config(θ_u)          # rope_theta、max_position_embeddings、語彙を保持

2. 完全 fp32 での FIM 推定とマスク生成（E2）
   F_h = FIM_fp32(θ_eval_h, D_h)        # 評価点（θ_u 近傍 vs θ_s）を明示、fp16 へキャストしない
   F_b = mean_j FIM_fp32(θ_u,j, D_b,j)  # fp32 のまま保持
   λ   = F_h / (F_b + ε)                # fp32 のまま（ε = 1e-6）
   M   = global_topk_or_soft(λ, k)      # 全体 top-k（または log-percentile soft mask）
   記録: zero_frac(F_h), actual_mask_ratio(M), inf_count(λ)
   assert |actual_mask_ratio(M) - k| <= 0.05  # 全 1 退化を即時検知して停止

3. 層選択（E4・オプション）と注入量整合（E3）
   δ_s = θ_s - θ0                       # fp32 で計算
   δ   = (w_layer ⊙ M) ⊙ δ_s            # norm 層は θ_u を保持
   α の格子 A に、実効注入ノルム補償点 α' = α / (‖δ‖ / ‖δ_s‖) を含める

4. 候補の merge（A の各 α について）
   θ(α) = merge_fp32(θ_u, θ_s, M, α)    # additive / interpolation を fp32 演算後に保存型へ変換

5. 拡張妥当性ゲートと複数判定器による評価（E0・E1）
   各 α について、応答生成後に拡張 gibberish 判定（既存ルール + 非 ASCII 比率 + 無空白長文字列）を実施
   拡張 VRR >= v を満たす点のみ残し、HarmBench 単独とベンチマーク別分類器の双方で Conditional ASR を算出
   観測点の厳密な Pareto 支配（補間なし）により非支配点から採用点を選ぶ

出力: 採用した α と θ(α)、除外点一覧、拡張 VRR・複数判定器結果、マスク統計メタデータ
```

### 4.4 既存の結果で裏付けられること / 新しい実験が要ること

**既存の結果で裏付けられる（観測事実）**

- v3 の SST は fp16 キャストで 60.4% のテンソルが全 1 退化・平均マスク 70.4%・注入量比中央値 1.000 になっており、本来の選択的マージとして動作していなかった（V1・V2・V5 → E2 の直接根拠）。
- WizardCoder（相対差分 113.5%）と MedAlpaca（154.7%）は Llama-2 と異系統であり（V6）、異系統パターンでは 89〜100% の文字化け崩壊が現行 VRR をすり抜けて分類器乖離を生んでいた（3.0 節 → E0・E5 の直接根拠）。
- `safety+code` の merge 済みモデル 123 件すべてで `rope_theta` が不一致だった（V7 → E5 の直接根拠）。
- 同系統の `safety+math` では、非退化層＋norm 保持を含む SST の曲線が TA を上回り、`sst@1.0` が非支配点となった（3.1 節 → E3・E4 の動機）。

**新しい実験をしないと確かめられない（仮説）**

- fp32 修正（E2）により全 1 退化を解消したとき、FIM 選択（`Fh/Fb`）が `|δ_s|` や `random` を有意に上回るかどうか。
- E3（注入量補償）および E4（層選択・低ランク適用）を導入したとき、同系統モデル上の複数ドメイン（Math / Code / Medical）で一貫して既存手法を Pareto 支配できるか。
- E5（`rope_theta` 引き継ぎ・同系統モデル採用）によって、Code / Medical の有用性と文字化け率が実際に回復するか。
- 設計案全体が既存手法より優れること（本調査では優れている「可能性」までにとどめる）。

### 4.5 限界

- 評価は各ベンチマーク最大 320 件・seed 3 本（アブレーションは k=0.2・seed 42 のみ）。
- 同系統モデルである `safety+math` は単体モデルでも Math スコアの絶対値が小さく（6.41%）、手法間の有意差検証には別ベンチマークやより強い同系統ベースラインが必要。
- V3（Jaccard）と V4（fp16 丸め消失率 4.43%）は事前登録基準の中間に当たり判定不能（特に V3 はマスク全 1 退化が交絡しているため、fp32 修正後に再測定が必要）。
- DLSP_hiromi2 側の実験設定（Mistral-7B、LoRA、mergekit）は本調査の対象外であり、導入時は設定差を別途検証する必要がある。
<!-- 手書き: 設計案（FR5） 終了 -->
