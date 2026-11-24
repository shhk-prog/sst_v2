### SST アブレーション: safety+math+code+medical / sst（diagonal_sst）

固定した条件: 比=FhFb、層重み=nolayerwise、マスク=hard、n=500、seed=[42, 43, 44]、有害判定=harmbench_only。値は seed 平均 ± 標準偏差。
v3 に結果が無い条件は N/A とし、別の条件では代用していない（欠損の一覧は manifest にある）。

#### k x variant の表（α=0 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.2 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.4 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.6 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=0.8 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### k x variant の表（α=1 に固定）

| k | interpolation: Cond. ASR (%↓) | interpolation: VRR (%↑) | interpolation: Math (%↑) | interpolation: Code (%↑) | interpolation: Medical (%↑) | additive: Cond. ASR (%↓) | additive: VRR (%↑) | additive: Math (%↑) | additive: Code (%↑) | additive: Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.05 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.1 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.2 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| 0.5 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

#### α の効果の表（k=0.2、interpolation に固定。k x variant の表とは別）

| α | Cond. ASR (%↓) | VRR (%↑) | Math (%↑) | Code (%↑) | Medical (%↑) |
|:---|:---:|:---:|:---:|:---:|:---:|
| 0 | N/A | N/A | N/A | N/A | N/A |
| 0.2 | N/A | N/A | N/A | N/A | N/A |
| 0.4 | N/A | N/A | N/A | N/A | N/A |
| 0.6 | N/A | N/A | N/A | N/A | N/A |
| 0.8 | N/A | N/A | N/A | N/A | N/A |
| 1 | N/A | N/A | N/A | N/A | N/A |

