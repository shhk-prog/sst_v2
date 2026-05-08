# SST-Merge v5 実験結果サマリー

**総評価結果数**: 3539

## 主要な結果（A6_A7ペア、α=1.0）

### Jailbreak耐性

| 手法 | GEVP | Layer-wise | Resistance Rate | ASR |
|------|------|------------|-----------------|-----|
| DARE | ✗ | ✗ | 0.0% | 100.0% |
| SST-Merge (Additive) | ✓ | ✓ | 82.6% | 17.4% |
| SST-Merge (Additive) | ✓ | ✓ | 84.6% | 15.4% |
| SST-Merge (Additive) | ✓ | ✓ | 79.6% | 20.4% |
| SST-Merge (Additive) | ✓ | ✓ | 79.8% | 20.2% |
| SST-Merge (Additive) | ✓ | ✓ | 83.6% | 16.4% |
| SST-Merge (Additive) | ✓ | ✓ | 83.6% | 16.4% |
| SST-Merge (Additive) | ✓ | ✓ | 82.2% | 17.8% |
| SST-Merge (Additive) | ✓ | ✓ | 82.6% | 17.4% |
| SST-Merge (Additive) | ✓ | ✓ | 84.2% | 15.8% |
| SST-Merge (Additive) | ✓ | ✗ | 83.4% | 16.6% |
| SST-Merge (Additive) | ✓ | ✗ | 82.2% | 17.8% |
| SST-Merge (Additive) | ✓ | ✗ | 80.8% | 19.2% |
| SST-Merge (Additive) | ✓ | ✗ | 84.2% | 15.8% |
| SST-Merge (Additive) | ✓ | ✗ | 84.0% | 16.0% |
| SST-Merge (Additive) | ✓ | ✗ | 82.0% | 18.0% |
| SST-Merge (Additive) | ✓ | ✗ | 79.4% | 20.6% |
| SST-Merge (Additive) | ✓ | ✗ | 81.2% | 18.8% |
| SST-Merge (Additive) | ✓ | ✗ | 81.4% | 18.6% |
| SST-Merge (Additive) | ✗ | ✗ | 81.4% | 18.6% |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 77.2% | 22.8% |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 81.4% | 18.6% |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 84.6% | 15.4% |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 84.6% | 15.4% |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 84.6% | 15.4% |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 84.6% | 15.4% |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 82.8% | 17.2% |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 78.8% | 21.2% |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 82.8% | 17.2% |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 82.8% | 17.2% |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 76.4% | 23.6% |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 82.8% | 17.2% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 78.4% | 21.6% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 74.2% | 25.8% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 78.4% | 21.6% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 79.6% | 20.4% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 78.4% | 21.6% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 78.4% | 21.6% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 77.4% | 22.6% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 73.2% | 26.8% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 80.0% | 20.0% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 80.0% | 20.0% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 80.0% | 20.0% |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 80.0% | 20.0% |
| SST-Merge (Interpolation) | ✓ | ✓ | 92.0% | 8.0% |
| SST-Merge (Interpolation) | ✓ | ✓ | 84.2% | 15.8% |
| SST-Merge (Interpolation) | ✓ | ✓ | 92.4% | 7.6% |
| SST-Merge (Interpolation) | ✓ | ✓ | 82.2% | 17.8% |
| SST-Merge (Interpolation) | ✓ | ✓ | 88.4% | 11.6% |
| SST-Merge (Interpolation) | ✓ | ✓ | 94.4% | 5.6% |
| SST-Merge (Interpolation) | ✓ | ✗ | 81.8% | 18.2% |
| SST-Merge (Interpolation) | ✓ | ✗ | 93.4% | 6.6% |
| SST-Merge (Interpolation) | ✓ | ✗ | 94.4% | 5.6% |
| SST-Merge (Interpolation) | ✓ | ✗ | 80.4% | 19.6% |
| SST-Merge (Interpolation) | ✓ | ✗ | 90.0% | 10.0% |
| SST-Merge (Interpolation) | ✓ | ✗ | 93.6% | 6.4% |
| TIES | ✗ | ✗ | 99.6% | 0.4% |
| Task Arithmetic | ✗ | ✗ | 100.0% | 0.0% |

### Alpaca性能

| 手法 | GEVP | Layer-wise | ROUGE-1 | ROUGE-2 | ROUGE-L |
|------|------|------------|---------|---------|---------|
| DARE | ✗ | ✗ | 0.0187 | 0.0018 | 0.0183 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5926 | 0.3642 | 0.5138 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5931 | 0.3642 | 0.5134 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5987 | 0.3680 | 0.5171 |
| SST-Merge (Additive) | ✓ | ✓ | 0.6062 | 0.3767 | 0.5281 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5915 | 0.3622 | 0.5117 |
| SST-Merge (Additive) | ✓ | ✓ | 0.6065 | 0.3766 | 0.5280 |
| SST-Merge (Additive) | ✓ | ✓ | 0.6025 | 0.3746 | 0.5228 |
| SST-Merge (Additive) | ✓ | ✓ | 0.5979 | 0.3705 | 0.5197 |
| SST-Merge (Additive) | ✓ | ✓ | 0.6003 | 0.3734 | 0.5192 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5996 | 0.3712 | 0.5186 |
| SST-Merge (Additive) | ✓ | ✗ | 0.6059 | 0.3775 | 0.5244 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5950 | 0.3626 | 0.5156 |
| SST-Merge (Additive) | ✓ | ✗ | 0.6029 | 0.3725 | 0.5218 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5994 | 0.3711 | 0.5203 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5897 | 0.3602 | 0.5104 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5942 | 0.3637 | 0.5137 |
| SST-Merge (Additive) | ✓ | ✗ | 0.5989 | 0.3652 | 0.5198 |
| SST-Merge (Additive) | ✓ | ✗ | 0.6074 | 0.3785 | 0.5289 |
| SST-Merge (Additive) | ✗ | ✗ | 0.5577 | 0.3282 | 0.4758 |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 0.5910 | 0.3628 | 0.5099 |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 0.5910 | 0.3628 | 0.5099 |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 0.6513 | 0.4357 | 0.5771 |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 0.6139 | 0.3878 | 0.5338 |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 0.5910 | 0.3628 | 0.5099 |
| SST-Merge (Data-Free Additive) | ✗ | ✓ | 0.5910 | 0.3628 | 0.5099 |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 0.5902 | 0.3578 | 0.5058 |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 0.5902 | 0.3578 | 0.5058 |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 0.5902 | 0.3578 | 0.5058 |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 0.6445 | 0.4281 | 0.5711 |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 0.5902 | 0.3578 | 0.5058 |
| SST-Merge (Data-Free Additive) | ✗ | ✗ | 0.6084 | 0.3847 | 0.5299 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 0.6310 | 0.4090 | 0.5518 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 0.6317 | 0.4153 | 0.5564 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 0.6310 | 0.4090 | 0.5518 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 0.6310 | 0.4090 | 0.5518 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 0.6310 | 0.4090 | 0.5518 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✓ | 0.6578 | 0.4415 | 0.5838 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 0.6308 | 0.4027 | 0.5494 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 0.6297 | 0.4098 | 0.5529 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 0.6308 | 0.4027 | 0.5494 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 0.6308 | 0.4027 | 0.5494 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 0.6555 | 0.4469 | 0.5838 |
| SST-Merge (Data-Free Interpolation) | ✗ | ✗ | 0.6308 | 0.4027 | 0.5494 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.4655 | 0.2488 | 0.3859 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.4600 | 0.2459 | 0.3831 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.4708 | 0.2541 | 0.3918 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.5104 | 0.2842 | 0.4270 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.5364 | 0.3073 | 0.4513 |
| SST-Merge (Interpolation) | ✓ | ✓ | 0.4854 | 0.2631 | 0.4051 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.4715 | 0.2562 | 0.3933 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.4441 | 0.2331 | 0.3670 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.5002 | 0.2734 | 0.4175 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.4492 | 0.2374 | 0.3724 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.4472 | 0.2354 | 0.3701 |
| SST-Merge (Interpolation) | ✓ | ✗ | 0.5339 | 0.2998 | 0.4470 |
| TIES | ✗ | ✗ | 0.3054 | 0.1421 | 0.2368 |
| Task Arithmetic | ✗ | ✗ | 0.2690 | 0.1200 | 0.2075 |