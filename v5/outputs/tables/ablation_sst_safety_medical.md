### SST アブレーション: safety+medical / sst（diagonal_sst）

固定した条件: 比=FhFb、層重み=nolayerwise、マスク=hard、n=500、seed=[42, 43, 44]、有害判定=harmbench_only。値は seed 平均 ± 標準偏差。
v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。

#### k x variant の表（α=0 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 90.50 ± 0.00 | 33.12 ± 0.00 | 0.00 ± 0.00 | 90.55 ± 0.00 | 33.12 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.2 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.16 ± 0.00 | 100.00 ± 0.00 | 13.75 ± 0.00 | 0.00 ± 0.00 | 91.32 ± 0.00 | 33.75 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.4 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.44 ± 0.00 | 79.49 ± 0.00 | 85.00 ± 0.00 | 0.00 ± 0.00 | 89.39 ± 0.00 | 34.06 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.6 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.08 ± 0.00 | 100.00 ± 0.00 | 13.44 ± 0.00 | 0.09 ± 0.00 | 89.31 ± 0.00 | 34.38 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.8 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 76.56 ± 0.00 | 12.19 ± 0.00 | 0.00 ± 0.00 | 89.04 ± 0.00 | 34.06 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=1 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 76.48 ± 0.00 | 7.81 ± 0.00 | 0.00 ± 0.00 | 88.01 ± 0.00 | 33.75 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### α の効果の表（k=0.2、interpolation に固定。k x variant の表とは別）

| α | Cond. ASR (%↓) | VRR (%↑) | Medical (%↑) |
|:---|:---:|:---:|:---:|
| 0 | 0.00 ± 0.00 | 90.50 ± 0.00 | 33.12 ± 0.00 |
| 0.2 | 0.16 ± 0.00 | 100.00 ± 0.00 | 13.75 ± 0.00 |
| 0.4 | 0.44 ± 0.00 | 79.49 ± 0.00 | 85.00 ± 0.00 |
| 0.6 | 0.08 ± 0.00 | 100.00 ± 0.00 | 13.44 ± 0.00 |
| 0.8 | 0.00 ± 0.00 | 76.56 ± 0.00 | 12.19 ± 0.00 |
| 1 | 0.00 ± 0.00 | 76.48 ± 0.00 | 7.81 ± 0.00 |

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

