### SST アブレーション: safety+medical / datafree（data_free_sst）

固定した条件: 比=FhFb、層重み=nolayerwise、マスク=hard、n=None、seed=[42, 43, 44]、有害判定=harmbench_only。値は seed 平均 ± 標準偏差。
v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。

#### k x variant の表（α=0 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 90.33 ± 0.00 | 33.12 ± 0.00 | 0.00 ± 0.00 | 90.58 ± 0.00 | 33.12 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.2 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.11 ± 0.00 | 78.16 ± 0.00 | 2.81 ± 0.00 | 0.00 ± 0.00 | 90.34 ± 0.00 | 34.06 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.4 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 94.94 ± 0.00 | 15.31 ± 0.00 | 0.00 ± 0.00 | 89.42 ± 0.00 | 34.38 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.6 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 78.62 ± 0.00 | 85.00 ± 0.00 | 0.00 ± 0.00 | 88.86 ± 0.00 | 34.69 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.8 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.10 ± 0.00 | 74.37 ± 0.00 | 85.62 ± 0.00 | 0.00 ± 0.00 | 88.81 ± 0.00 | 34.69 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=1 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.09 ± 0.00 | 89.56 ± 0.00 | 86.25 ± 0.00 | 0.00 ± 0.00 | 88.73 ± 0.00 | 34.38 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### α の効果の表（k=0.2、interpolation に固定。k x variant の表とは別）

| α | Cond. ASR (%↓) | VRR (%↑) | Medical (%↑) |
|:---|:---:|:---:|:---:|
| 0 | 0.00 ± 0.00 | 90.33 ± 0.00 | 33.12 ± 0.00 |
| 0.2 | 0.11 ± 0.00 | 78.16 ± 0.00 | 2.81 ± 0.00 |
| 0.4 | 0.00 ± 0.00 | 94.94 ± 0.00 | 15.31 ± 0.00 |
| 0.6 | 0.00 ± 0.00 | 78.62 ± 0.00 | 85.00 ± 0.00 |
| 0.8 | 0.10 ± 0.00 | 74.37 ± 0.00 | 85.62 ± 0.00 |
| 1 | 0.09 ± 0.00 | 89.56 ± 0.00 | 86.25 ± 0.00 |

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

