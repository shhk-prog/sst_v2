# タスクリスト: Secure Merge v4 改修・厳密化タスク

## 判定ステータス
**`CURRENT STATUS: NO_GO` (監査指示書受領・P0/P1是正完了・主実験停止ゲート確立)**
- 監査対象コミットSHA: `d994f280a21a04fa4b4264608b8214cd6aa14700`
- 旧出力の隔離先: `v4/results/legacy_diagnostic_smoke/` (完了)
- 整合性監査: Math/Code 不整合を検出し、主実験は正当に `NO_GO`（非ゼロ終了）
- 全受入回帰テスト: `v4/tests/` 下のテストスイート（5件）全合格

---

## 改修タスク進捗

### Phase 1: E0 停止条件と監査の厳密化 (P0-03)
- [x] 1.1 過去の動作確認・模擬結果を `v4/results/legacy_diagnostic_smoke/` へ完全隔離
- [x] 1.2 `audit_models.py` の厳密化:
  - モデル読込失敗時の `UNVERIFIED` 分類と `FAIL` の分離
  - 両モデル未読込時の欠損同士比較による誤PASS防止
  - SafetyFT (seed 42, 43, 44) の dense 復元確認を主実験 GO の必須条件に追加
  - `FAIL` または `UNVERIFIED` 検出時に **非ゼロ終了 (Exit 1)** する仕様の実装
- [x] 1.3 runner 側 (`run_v4_pipeline.py`, `run_all_v4.py`) で E0 判定が `NO_GO` の場合に主実験を強制停止（HALT）させるゲートの実装
- [x] 1.4 `base_merger.py` で形状不一致・欠損テンソルを無言スキップせず、厳格にエラー化（明示的 allowlist のみ許可）

### Phase 2: E1 再集計・欠測補完の排除・lm-eval utility 結合 (P0-01, P0-02, P1-01)
- [x] 2.1 未測定値の補完（`rec["overrefusal"] = 0.04`, `rec["vrr_benign"] = rec["vrr_harmful"]`, utility=0.0）を全廃
  - 欠測はすべて `None` (null) とし、`status: INSUFFICIENT_DATA` とする
  - 無害VRR・過剰拒否は無害プロンプトへの実測結果からのみ算出
- [x] 2.2 v3 の lm-evaluation-harness 出力（辞書型 results）に対する schema adapter を実装
  - `exact_match,flexible-extract`, `math_verify,none`, `pass@1` をタスク別に一貫抽出
  - 1候補について元ファイルと再集計値の一致を検証するテストの作成（`test_utility_parser.py` 合格）
- [x] 2.3 候補ID（Candidate ID）および評価ID（Evaluation ID）の体系化:
  - 単なる basename ではなく、`domain`, `method`, `alpha`, `train_seed`, `mask_seed` から一意に生成
  - `unknown` を主比較から完全除外
  - v3 旧ログの `task_arithmetic`（実質 Linear 補間）を `legacy_linear_patch_old_task_arithmetic` として識別
  - 1候補の詳細突き合わせ情報（安全性元ファイル・件数・判定器、validity、過剰拒否、utility元ファイル・指標名・件数・値）の保持（324候補バインド完了）
- [x] 2.4 `e1_selector.py` の厳密化:
  - ドメイン×手法ごとの主選定
  - 必須 benchmark の個別制約判定（平均による誤魔化しの排除）
  - NaN/Inf、欠測 utility、未承認手法、未見性不明候補の完全除外（`test_e1_selector.py` 合格）

### Phase 3: E2・E3 乱数テンソル排除・実モデル接続・同一パラメータ数対照 (P0-04, P1-02, P1-04)
- [x] 3.1 `characteristic_analyzer.py`, `intervention_mapper.py`, `controlled_intervention.py` 内の乱数テストを `v4/tests/` へ完全分離
- [x] 3.2 E2 本番処理を実 checkpoint の重み読込に接続し、対象 key 数・パラメータ数・欠損を確認して測定する CLI 実装
- [x] 3.3 E3 ランダム対照の修正:
  - 単なる同数キーではなく、「同じテンソル種別かつ同じ変更パラメータ数」を持つ層内ブロック等で対照を構築
  - 選択箇所を調べる A-B, C-D も同一ノルムに揃えた双方向対照 ($t = \min(||\Delta_1||, ||\Delta_2||)$) を実装（縮小のみ）
  - 3つの mask seed (42, 43, 44) で測定（`test_controlled_intervention.py` 合格）
- [x] 3.4 数値計算のオーバーフロー防止:
  - FP16 の二乗和が inf になる問題を防ぐため、差分・内積・二乗和・ノルム計算を FP32 / FP64 で実施（`test_characteristic_analyzer.py` 合格）

### Phase 4: E4・E5 フェイク排除・実測依存関係の厳密化 (P0-05, P1-03)
- [x] 4.1 E4 において、実測された E3 介入地図が存在しない場合は実行を停止 (`BLOCKED`)
  - 未 calibrate の既定重みでの生成・保存を厳格に拒否
  - 実測地図から安全寄与・退化リスクを評価して動的に候補を生成（退化群や改善なし群は重み 0.0）
  - テンソル別上限と群別上限の区別（`test_proposed_intervention_merge.py` 合格）
- [x] 4.2 E5 において、独立未見 Test 評価ログが存在しない場合は `NOT_RUN` とし、ダミー性能出力を禁止
  - `proposed_full: Utility=0.63, ASR=0.028, VRR=0.980` 等の固定辞書を完全排除

### Phase 5: 評価器仕様と既存手法再現の整理 (P0-06, P0-07)
- [x] 5.1 `eval_safety_v4.py` の単語ヒューリスティックをテスト用指標として明示・隔離（HarmBench公式判定器と混同しない）
- [x] 5.2 比較手法（SafeMERGE, LED, Fisher 等）の実装差分台帳をコード docstring に明記
- [x] 5.3 回帰テストスイートによる各ステージの受入基準クリア確認
