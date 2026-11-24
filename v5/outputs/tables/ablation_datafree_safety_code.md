### SST アブレーション: safety+code / datafree（data_free_sst）

固定した条件: 比=FhFb、層重み=nolayerwise、マスク=hard、n=None、seed=[42, 43, 44]、有害判定=harmbench_only。値は seed 平均 ± 標準偏差。
v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。

#### k x variant の表（α=0 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Code (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Code (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.10 ± 0.00 | 77.03 ± 0.00 | 0.00 ± 0.00 | 0.10 ± 0.00 | 77.05 ± 0.00 | 0.00 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.2 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Code (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Code (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.22 ± 0.00 | 70.47 ± 0.00 | 0.00 ± 0.00 | 0.10 ± 0.00 | 75.28 ± 0.00 | 0.00 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.4 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Code (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Code (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.29 ± 0.00 | 80.97 ± 0.00 | 0.00 ± 0.00 | 0.10 ± 0.00 | 76.37 ± 0.00 | 0.00 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.6 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Code (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Code (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 78.40 ± 0.00 | 0.00 ± 0.00 | 0.10 ± 0.00 | 75.68 ± 0.00 | 0.00 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.8 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Code (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Code (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.22 ± 0.00 | 69.09 ± 0.00 | 0.00 ± 0.00 | 0.20 ± 0.00 | 77.50 ± 0.00 | 0.00 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=1 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Code (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Code (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 80.72 ± 0.00 | 0.00 ± 0.00 | 0.10 ± 0.00 | 80.23 ± 0.00 | 0.00 ± 0.00 |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A |

#### α の効果の表（k=0.2、interpolation に固定。k x variant の表とは別）

| α | Cond. ASR (%↓) | VRR (%↑) | Code (%↑) |
|:---|:---:|:---:|:---:|
| 0 | 0.10 ± 0.00 | 77.03 ± 0.00 | 0.00 ± 0.00 |
| 0.2 | 0.22 ± 0.00 | 70.47 ± 0.00 | 0.00 ± 0.00 |
| 0.4 | 0.29 ± 0.00 | 80.97 ± 0.00 | 0.00 ± 0.00 |
| 0.6 | 0.00 ± 0.00 | 78.40 ± 0.00 | 0.00 ± 0.00 |
| 0.8 | 0.22 ± 0.00 | 69.09 ± 0.00 | 0.00 ± 0.00 |
| 1 | 0.00 ± 0.00 | 80.72 ± 0.00 | 0.00 ± 0.00 |

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

