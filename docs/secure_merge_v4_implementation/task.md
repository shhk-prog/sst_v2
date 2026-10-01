# タスクリスト: Secure Merge v4 実装 (Secure_Merge_Experiment_Plan.md 準拠)

## 中心研究課題 (Core RQ)
**セキュアmergeに最適なmerge手法はどんなものかを調べて，その特性に合ったmerge手法を提案するのに繋げる**

---

## タスク進捗

- [x] 1. 要件定義と実験環境の基盤設計
  - [x] 実験計画書 (`Secure_Merge_Experiment_Plan.md`) の精読と要件抽出
  - [x] ドキュメント保存ディレクトリの作成 (`docs/secure_merge_v4_implementation/`)
  - [x] 実装計画書 (`implementation_plan.md`) の作成
  - [x] タスクリスト (`task.md`) の確定

- [x] 2. E0: 整合性監査 (Integrity Audit) モジュールの厳密実装
  - [x] 2.1 モデル出自・トークナイザ・特殊トークン・RoPE・SafetyFT (seeds 42, 43, 44) dense復元の台帳化 (`audit_models.py`)
  - [x] 2.2 マージ演算の数学的厳密化 (`Linear Safety-Patch` と `Task Arithmetic` の分離、全10手法の恒等性テスト、保存・再読込整合性 `audit_mergers.py`)
  - [x] 2.3 評価・集計指標の整合性監査 (ASR_all, VRR, ASR_valid, VSR の一貫計算 `audit_metrics.py`)
  - [x] 2.4 人手点検用無作為・難例サンプラー (`human_audit_sampler.py`)

- [x] 3. E1: 手法比較の再構築モジュール (Reconstruction of Baseline Comparison)
  - [x] 3.1 9つのマージ手法モジュール整備 (`v4/scripts/mergers/`)
  - [x] 3.2 厳密な 5大制約判定エンジンと指標欠損時の「判定不能」除外ロジック (`e1_selector.py`)
  - [x] 3.3 模擬実行 (`--dry_run`) と本実行 (`production`) の完全分離

- [x] 4. E2: 特性分析モジュール (Characteristic Measurement)
  - [x] 4.1 相対更新量比 $r_g$、最大集中層、選択率、cosine類似度、符号衝突測定器 (`characteristic_analyzer.py`)

- [x] 5. E3: 小規模統制介入モジュール (Controlled Intervention Study)
  - [x] 5.1 6群×2強度の介入地図生成器 (`intervention_mapper.py`)
  - [x] 5.2 双方向ノルム縮小対照 ($t = \min(||\Delta_1||, ||\Delta_2||)$) および 3-seed ランダム対照生成器 (`controlled_intervention.py`)

- [x] 6. E4: 特性適応型セキュアマージ手法の設計 (Behavior-Intervention Guided Constrained Merge)
  - [x] 6.1 結論先取りの排除（デフォルト重みを仮設定と明記）
  - [x] 6.2 E3 Calibration 介入実測値から領域係数 $a_g$ を動的選定するファクトリメソッドの実装 (`from_calibration_map`)

- [x] 7. E5: 独立検証・アブレーション・統合テスト
  - [x] 7.1 本実行フェイルセーフ機能（実採点ファイル未存在時の停止）
  - [x] 7.2 `--dry_run` モックデータの隔離 (`v4/results/mock_test/`)
  - [x] 7.3 全ステージのパイプライン疎通確認 (Exit 0)

- [ ] 8. 実機データによる小規模接続テスト (次の実証ステップ)
  - [ ] 8.1 1モデル・1設定・少数サンプル (limit=5〜10) による「checkpoint → 生成 → 採点 → sample単位保存 → 再集計」の疎通確認
  - [ ] 8.2 実測介入地図の計測と E4 動的係数決定の実行
