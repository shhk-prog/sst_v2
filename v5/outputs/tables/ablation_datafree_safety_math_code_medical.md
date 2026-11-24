### SST アブレーション: safety+math+code+medical / datafree（data_free_sst）

固定した条件: 比=FhFb、層重み=nolayerwise、マスク=hard、n=None、seed=[42, 43, 44]、有害判定=harmbench_only。値は seed 平均 ± 標準偏差。
v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。

#### k x variant の表（α=0 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.24 ± 0.00 | 75.76 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 12.19 ± 0.00 | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.2 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.19 ± 0.00 | 43.28 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 1.56 ± 0.00 | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.4 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 51.86 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 6.25 ± 0.00 | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.6 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.22 ± 0.00 | 36.09 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 13.44 ± 0.00 | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.8 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.00 ± 0.00 | 56.74 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 30.00 ± 0.00 | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=1 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | 0.32 ± 0.00 | 33.98 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 32.19 ± 0.00 | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### α の効果の表（k=0.2、interpolation に固定。k x variant の表とは別）

| α | Cond. ASR (%↓) | VRR (%↑) | Math (%↑) | Code (%↑) | Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|
| 0 | 0.24 ± 0.00 | 75.76 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 12.19 ± 0.00 |
| 0.2 | 0.19 ± 0.00 | 43.28 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 1.56 ± 0.00 |
| 0.4 | 0.00 ± 0.00 | 51.86 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 6.25 ± 0.00 |
| 0.6 | 0.22 ± 0.00 | 36.09 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 13.44 ± 0.00 |
| 0.8 | 0.00 ± 0.00 | 56.74 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 30.00 ± 0.00 |
| 1 | 0.32 ± 0.00 | 33.98 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 32.19 ± 0.00 |

#### seed が一部しか揃わない条件

- α=0、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.2、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.4、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.6、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=0.8、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）
- α=1、k=0.2、interpolation: 存在 [42]（期待 [42, 43, 44]）

