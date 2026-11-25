# SoK 実証 2: fp32 SST-Merge マージ直後検証レポート（CPU）

| Seed | 総合 | Check1 (α=0 vs WM) | Check2 (α=1 置換率) | Check3 (α=0.6 注入比 vs TA) | Check4 (config P4無) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 44 | PASS | max_diff=2e-06 (PASS) | 0.1998 [0.1993, 0.2003] | median=0.1981 (norm=0.4353) | rope_theta=10000.0 (PASS) |
