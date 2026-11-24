### SST アブレーション: safety+math / datafree（data_free_sst）

固定した条件: 比=FhFb、層重み=nolayerwise、マスク=hard、n=None、seed=[42, 43, 44]、有害判定=harmbench_only。値は seed 平均 ± 標準偏差。
v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。

#### k x variant の表（α=0 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 35.91 ± 0.00 | 95.37 ± 0.00 | 5.94 ± 0.00 | 35.65 ± 0.00 | 95.37 ± 0.00 | 6.25 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.2 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 34.79 ± 0.00 | 96.61 ± 0.00 | 4.53 ± 0.00 | 33.29 ± 0.00 | 97.23 ± 0.00 | 5.47 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.4 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 32.26 ± 0.00 | 98.42 ± 0.00 | 5.31 ± 0.00 | 30.82 ± 0.00 | 96.55 ± 0.00 | 5.31 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.6 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 10.73 ± 0.00 | 100.00 ± 0.00 | 5.31 ± 0.00 | 17.85 ± 0.00 | 99.52 ± 0.00 | 5.47 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.8 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 9.78 ± 0.00 | 100.00 ± 0.00 | 5.62 ± 0.00 | 8.21 ± 0.00 | 99.92 ± 0.00 | 5.00 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=1 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.87 ± 0.00 | 100.00 ± 0.00 | 5.94 ± 0.00 | 6.07 ± 0.00 | 100.00 ± 0.00 | 4.84 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### α の効果の表（k=0.2、interpolation に固定。k x variant の表とは別）

| α | Cond. ASR (%↓) | VRR (%↑) | Math (%↑) |
|:---|:---:|:---:|:---:|
| 0 | 35.91 ± 0.00 | 95.37 ± 0.00 | 5.94 ± 0.00 |
| 0.2 | 34.79 ± 0.00 | 96.61 ± 0.00 | 4.53 ± 0.00 |
| 0.4 | 32.26 ± 0.00 | 98.42 ± 0.00 | 5.31 ± 0.00 |
| 0.6 | 10.73 ± 0.00 | 100.00 ± 0.00 | 5.31 ± 0.00 |
| 0.8 | 9.78 ± 0.00 | 100.00 ± 0.00 | 5.62 ± 0.00 |
| 1 | 0.87 ± 0.00 | 100.00 ± 0.00 | 5.94 ± 0.00 |

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

