# SST-Merge v5 実験結果サマリー

**総評価結果数**: 1667

## 主要な結果（A6_A7ペア、α=1.0）

### Jailbreak耐性

| 手法 | GEVP | Layer-wise | Resistance Rate | ASR |
|------|------|------------|-----------------|-----|
| DARE | ✗ | ✗ | 0.0% | 100.0% |
| DARE | ✗ | ✗ | 0.0% | 100.0% |
| SST-Merge (Additive) | ✓ | ✓ | 82.6% | 17.4% |
| SST-Merge (Additive) | ✓ | ✓ | 84.6% | 15.4% |
| SST-Merge (Additive) | ✓ | ✓ | 83.6% | 16.4% |
| SST-Merge (Additive) | ✓ | ✓ | 82.6% | 17.4% |
| SST-Merge (Additive) | ✓ | ✓ | 84.6% | 15.4% |
| SST-Merge (Additive) | ✓ | ✓ | 83.6% | 16.4% |
| SST-Merge (Additive) | ✓ | ✗ | 82.2% | 17.8% |
| SST-Merge (Additive) | ✓ | ✗ | 84.0% | 16.0% |
| SST-Merge (Additive) | ✓ | ✗ | 82.0% | 18.0% |
| SST-Merge (Additive) | ✓ | ✗ | 82.2% | 17.8% |
| SST-Merge (Additive) | ✓ | ✗ | 84.0% | 16.0% |
| SST-Merge (Additive) | ✓ | ✗ | 82.0% | 18.0% |
| SST-Merge (Additive) | ✗ | ✗ | 81.4% | 18.6% |
| SST-Merge (Additive) | ✗ | ✗ | 81.4% | 18.6% |
| SST-Merge (Interpolation) | ✓ | ✓ | 91.6% | 8.4% |
| SST-Merge (Interpolation) | ✓ | ✗ | 93.2% | 6.8% |
| SST-Merge (Interpolation) | ✗ | ✓ | 99.8% | 0.2% |
| SST-Merge (Interpolation) | ✗ | ✗ | 100.0% | 0.0% |
| TIES | ✗ | ✗ | 99.6% | 0.4% |
| TIES | ✗ | ✗ | 99.6% | 0.4% |
| Task Arithmetic | ✗ | ✗ | 100.0% | 0.0% |
| Task Arithmetic | ✗ | ✗ | 100.0% | 0.0% |
| Unknown | ✗ | ✓ | 87.0% | 13.0% |
| Unknown | ✗ | ✓ | 87.0% | 13.0% |
| Unknown | ✗ | ✓ | 87.0% | 13.0% |
| Unknown | ✗ | ✗ | 87.0% | 13.0% |
| Unknown | ✗ | ✗ | 87.0% | 13.0% |
| Unknown | ✗ | ✗ | 87.0% | 13.0% |

### Alpaca性能

| 手法 | GEVP | Layer-wise | ROUGE-1 | ROUGE-2 | ROUGE-L |
|------|------|------------|---------|---------|---------|
| DARE | ✗ | ✗ | 0.0187 | 0.0018 | 0.0183 |
| DARE | ✗ | ✗ | 0.0187 | 0.0018 | 0.0183 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5926 | 0.3642 | 0.5138 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5931 | 0.3642 | 0.5134 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5915 | 0.3622 | 0.5117 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5926 | 0.3642 | 0.5138 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5931 | 0.3642 | 0.5134 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5915 | 0.3622 | 0.5117 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5897 | 0.3602 | 0.5104 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5942 | 0.3637 | 0.5137 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5989 | 0.3652 | 0.5198 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5897 | 0.3602 | 0.5104 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5942 | 0.3637 | 0.5137 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5989 | 0.3652 | 0.5198 |
| SST-Merge (Additive) | ✗ | ✗ | 0.5577 | 0.3282 | 0.4758 |
| SST-Merge (Additive) | ✗ | ✗ | 0.5577 | 0.3282 | 0.4758 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.4691 | 0.2514 | 0.3902 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.4472 | 0.2384 | 0.3697 |
| SST-Merge (Interpolation) | ✗ | ✓ | 0.2967 | 0.1420 | 0.2340 |
| SST-Merge (Interpolation) | ✗ | ✗ | 0.2690 | 0.1200 | 0.2075 |
| TIES | ✗ | ✗ | 0.3054 | 0.1421 | 0.2368 |
| TIES | ✗ | ✗ | 0.3054 | 0.1421 | 0.2368 |
| Task Arithmetic | ✗ | ✗ | 0.2690 | 0.1200 | 0.2075 |
| Task Arithmetic | ✗ | ✗ | 0.2690 | 0.1200 | 0.2075 |
| Unknown | ✗ | ✓ | 0.6163 | 0.3904 | 0.5407 |
| Unknown | ✗ | ✓ | 0.6163 | 0.3904 | 0.5407 |
| Unknown | ✗ | ✓ | 0.6163 | 0.3904 | 0.5407 |
| Unknown | ✗ | ✗ | 0.6163 | 0.3904 | 0.5407 |
| Unknown | ✗ | ✗ | 0.6163 | 0.3904 | 0.5407 |
| Unknown | ✗ | ✗ | 0.6163 | 0.3904 | 0.5407 |