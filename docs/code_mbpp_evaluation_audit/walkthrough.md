# code_mbpp 評価プロセスの修正・検証完了報告 (Walkthrough Report)

`code_mbpp`（MBPPベンチマーク）における評価データの修正が一括完了し、評価スコアが正常値へと復元されたことを確認しました。

---

## 修正前後の Pass@1 スコア比較

| モデル / 設定 | 修正前 Pass@1 | 修正後 Pass@1 (復元値) | 状況 |
| :--- | :---: | :---: | :--- |
| **WizardCoder-Python-7B-V1.0** (ベース) | 0.0000 (0.0%) | **0.4375 (43.75%)** | 正常復元 (320件中140件正解) |
| **MedAlpaca-7b** (ベース) | 0.0000 (0.0%) | **0.1250 (12.50%)** | 正常復元 |
| **SafetyFT (seed42)** (ベース) | 0.0000 (0.0%) | **0.0813 (8.13%)** | 正常復元 |
| **WizardMath-7B-V1.0** (ベース) | 0.0000 (0.0%) | **0.0656 (6.56%)** | 正常復元 |
| **LED-Merging** (マージモデル) | 0.0000 (0.0%) | **0.1406 (14.06%)** | 正常復元 |
| **Task Arithmetic** (マージモデル) | 0.0000 (0.0%) | **0.1156 (11.56%)** | 正常復元 |
| **MATENA Fisher** (マージモデル) | 0.0000 (0.0%) | **0.1063 (10.63%)** | 正常復元 |
| **TIES-Merging** (マージモデル) | 0.0000 (0.0%) | **0.1031 (10.31%)** | 正常復元 |
| **Data-Free SST** (マージモデル) | 0.0000 (0.0%) | **0.0906 (9.06%)** | 正常復元 |

---

## 検証結論

362 件すべての `*_utility_code_mbpp.json` ファイルに対して、`[END]` タグ起因の SyntaxError が除去され、各モデル本来の Pass@1 正解率が正確に反映されていることを確認いたしました。

---

## 関連ドキュメント

- [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/code_mbpp_evaluation_audit/task.md)
- [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/code_mbpp_evaluation_audit/implementation_plan.md)
- [walkthrough.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/code_mbpp_evaluation_audit/walkthrough.md)
- [eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval/eval_utility.py)
- [fix_mbpp_jsons.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/fixes/fix_mbpp_jsons.py)
