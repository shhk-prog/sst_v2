### SST アブレーション: safety+math / sst（diagonal_sst）

固定した条件: 比=FhFb、層重み=nolayerwise、マスク=hard、n=500、seed=[42, 43, 44]、有害判定=harmbench_only。値は seed 平均 ± 標準偏差。
v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。

#### k x variant の表（α=0 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 35.91 ± 0.00 | 95.37 ± 0.00 | 5.94 ± 0.00 | 35.40 ± 0.00 | 95.37 ± 0.00 | 5.94 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.2 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 32.70 ± 0.00 | 95.25 ± 0.00 | 6.25 ± 0.00 | 34.31 ± 0.00 | 96.54 ± 0.00 | 5.47 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.4 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 34.84 ± 0.00 | 97.22 ± 0.00 | 6.25 ± 0.00 | 33.78 ± 0.00 | 95.59 ± 0.00 | 6.09 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.6 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 23.11 ± 0.00 | 99.84 ± 0.00 | 6.72 ± 0.00 | 30.37 ± 0.00 | 97.40 ± 0.00 | 5.78 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.8 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 3.99 ± 0.00 | 100.00 ± 0.00 | 7.50 ± 0.00 | 15.11 ± 0.00 | 99.92 ± 0.00 | 5.62 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=1 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 100.00 ± 0.00 | 9.69 ± 0.00 | 10.23 ± 0.00 | 100.00 ± 0.00 | 5.16 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### α の効果の表（k=0.2、interpolation に固定。k x variant の表とは別）

| α | Cond. ASR (%↓) | VRR (%↑) | Math (%↑) |
|:---|:---:|:---:|:---:|
| 0 | 35.91 ± 0.00 | 95.37 ± 0.00 | 5.94 ± 0.00 |
| 0.2 | 32.70 ± 0.00 | 95.25 ± 0.00 | 6.25 ± 0.00 |
| 0.4 | 34.84 ± 0.00 | 97.22 ± 0.00 | 6.25 ± 0.00 |
| 0.6 | 23.11 ± 0.00 | 99.84 ± 0.00 | 6.72 ± 0.00 |
| 0.8 | 3.99 ± 0.00 | 100.00 ± 0.00 | 7.50 ± 0.00 |
| 1 | 0.00 ± 0.00 | 100.00 ± 0.00 | 9.69 ± 0.00 |

#### seed が一部しか揃わない条件

- α=0、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0、k=0.2、additive: 存在 [42]（期待 [42, 43, 44]）
- α=0.2、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.2、k=0.2、additive: 存在 [42]（期待 [42, 43, 44]）
- α=0.4、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.4、k=0.2、additive: 存在 [42]（期待 [42, 43, 44]）
- α=0.6、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.6、k=0.2、additive: 存在 [42]（期待 [42, 43, 44]）
- α=0.8、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.8、k=0.2、additive: 存在 [42]（期待 [42, 43, 44]）
- α=1、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=1、k=0.2、additive: 存在 [42]（期待 [42, 43, 44]）

