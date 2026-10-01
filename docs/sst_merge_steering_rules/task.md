# タスクリスト

- [ ] 1. AAAI-27 向け仕様・計画書 (`kiro/specs/sst-merge-aaai27/`) の大幅拡充
    - [ ] `requirements.md` の更新 (必須比較手法、11アブレーション項目、評価最低構成、統計的報告)
    - [ ] `design.md` の更新 (FIM推定と評価データの物理分離、YAML構成管理、評価/解析スクリプト設計)
    - [ ] `tasks.md` の更新 (評価スクリプト作成、マージ手法追加、Paretoプロット自動化等の詳細タスク)
- [ ] 2. Steering Rules (`kiro/steering/`) の更新
    - [ ] `product.md` の更新 (アブレーション設計やデータ分割ルールの厳格化)
    - [ ] `tech.md` の更新 (評価スクリプト要件、YAML構成管理の強制)
- [ ] 3. 新規評価・解析スクリプトおよび YAML 構成ファイルの新規作成
    - [ ] `v2/scripts/evaluation/eval_safety_suite.py` の作成 (HarmBench, JailbreakBench, StrongREJECT, WildJailbreak対応)
    - [ ] `v2/scripts/evaluation/eval_utility_suite.py` の作成 (lm-evaluation-harnessを用いたMMLU, IFEval, GSM8K等対応)
    - [ ] `v2/scripts/analysis/pareto_auc.py` の作成 (ASR-Utility曲線のAUC, Safety@95% Utility等の自動計算とプロット)
    - [ ] `v2/configs/aaai27/config_example.yaml` の作成 (実験管理用YAML)
- [ ] 4. 既存マージスクリプトへの手法追加と検証フックの同期
    - [ ] `v1/scripts/merging/baseline_merge.py` に DELLA, Breadcrumbs, SafeMERGE, LED-Merging などの YAML 生成/実行を追加
    - [ ] `v2/scripts/steering_hook.py` にデータ重複チェック、Data-Free statistical cached 利用禁止フックを追加
    - [ ] `v2/scripts/test_steering_hook.py` を更新しテストを実行して検証
    - [ ] `walkthrough.md` の作成と保存
