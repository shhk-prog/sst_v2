#### ルールベース gibberish 判定（is_gibberish=False）のすり抜けと分類器乖離（α=0.6）

注: 探索用。`is_gibberish=False` の応答のうち、非 ASCII 混入（3 文字以上かつ 3% 以上）または URL 以外の 35 文字以上の無空白連続を「文字化け崩壊の疑い」と集計。

| Pattern | Method | Valid件数 | 崩壊疑い (% of Valid) | Native有害かつHB無害 (件) | そのうち崩壊疑い (%) |
|:---|:---|---:|---:|---:|---:|
| safety+code | dare | 3085 | 97.5% (3009) | 1916 | 97.7% (1871) |
| safety+code | data_free_sst_main | 2437 | 96.3% (2347) | 1255 | 96.9% (1216) |
| safety+code | della | 2910 | 96.6% (2812) | 1822 | 96.1% (1751) |
| safety+code | diagonal_sst_main | 2776 | 89.1% (2474) | 1629 | 88.7% (1445) |
| safety+code | led_merging | 2500 | 0.3% (7) | 1544 | 0.1% (2) |
| safety+code | matena_fisher | 1919 | 36.7% (705) | 970 | 41.4% (402) |
| safety+code | mergealign | 0 | 0.0% (0) | 0 | 0.0% (0) |
| safety+code | safemerge | 3156 | 0.0% (0) | 9 | 0.0% (0) |
| safety+code | task_arithmetic | 2990 | 1.3% (39) | 854 | 1.1% (9) |
| safety+code | ties | 1943 | 36.1% (701) | 887 | 36.6% (325) |
| safety+math | dare | 3158 | 0.0% (1) | 99 | 1.0% (1) |
| safety+math | data_free_sst_main | 3151 | 0.0% (1) | 364 | 0.0% (0) |
| safety+math | della | 3159 | 0.3% (8) | 111 | 0.0% (0) |
| safety+math | diagonal_sst_main | 3140 | 0.1% (2) | 400 | 0.0% (0) |
| safety+math | led_merging | 2499 | 0.4% (9) | 1545 | 0.2% (3) |
| safety+math | matena_fisher | 3132 | 0.1% (4) | 100 | 0.0% (0) |
| safety+math | mergealign | 0 | 0.0% (0) | 0 | 0.0% (0) |
| safety+math | safemerge | 3020 | 0.0% (1) | 415 | 0.2% (1) |
| safety+math | task_arithmetic | 3156 | 0.0% (1) | 24 | 0.0% (0) |
| safety+math | ties | 3157 | 0.1% (4) | 112 | 0.0% (0) |
| safety+math+code+medical | dare | 2193 | 100.0% (2193) | 1388 | 100.0% (1388) |
| safety+math+code+medical | data_free_sst_main | 1489 | 72.8% (1084) | 759 | 71.8% (545) |
| safety+math+code+medical | della | 2747 | 100.0% (2747) | 1600 | 100.0% (1600) |
| safety+math+code+medical | diagonal_sst_main | 1029 | 55.2% (568) | 605 | 56.2% (340) |
| safety+math+code+medical | matena_fisher | 341 | 83.0% (283) | 200 | 75.5% (151) |
| safety+math+code+medical | task_arithmetic | 2572 | 0.1% (3) | 702 | 0.0% (0) |
| safety+math+code+medical | ties | 2105 | 100.0% (2105) | 1307 | 100.0% (1307) |
| safety+medical | dare | 2444 | 100.0% (2444) | 1470 | 100.0% (1470) |
| safety+medical | data_free_sst_main | 1325 | 100.0% (1325) | 698 | 100.0% (698) |
| safety+medical | della | 1057 | 100.0% (1057) | 522 | 100.0% (522) |
| safety+medical | diagonal_sst_main | 2065 | 100.0% (2065) | 1264 | 100.0% (1264) |
| safety+medical | matena_fisher | 3136 | 100.0% (3136) | 2046 | 100.0% (2046) |
| safety+medical | mergealign | 0 | 0.0% (0) | 0 | 0.0% (0) |
| safety+medical | safemerge | 3159 | 0.0% (0) | 4 | 0.0% (0) |
| safety+medical | task_arithmetic | 3152 | 100.0% (3152) | 1858 | 100.0% (1858) |
| safety+medical | ties | 2539 | 100.0% (2539) | 1522 | 100.0% (1522) |
