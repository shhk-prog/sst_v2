# タスクリスト: v4 実験計画に基づく Legacy E1 スクリーニングおよびパイプライン構築 (secure_merge_v4_legacy_e1_and_screening)

## 状態凡例
- [ ] 未着手 (TODO)
- [/] 進行中 (IN_PROGRESS)
- [x] 完了 (DONE)

---

## 1. 全体ロードマップ進捗サマリー (Phase A 〜 Phase J)
- [x] **Phase A: v3 全10手法 Legacy screening**
  - 10手法・120候補（126,360生成）の再採点および $U_{math}$ 算出完了
- [/] **Phase B: Human Validity (200件) ＆ XSTest (30候補+3基準) の並行実行**
  - 人手評価: 二重盲検シート (`blinded_human_audit_sheet.json`) 生成完了、評価ツール実装完了
  - XSTest: 評価スクリプト (`eval_overrefusal_v4.py`) 準備完了、33モデルのベンチマーク実行準備
- [x] **Phase C: 各手法 Seed42 Development で1設定固定 $\to$ 3-Seed 正式集計**
  - 全10手法の代表設定固定および 3-Seed Mean ± SD 正式表 (`formal_legacy_e1_table.json`) 出力完了
  - Linear Safety-Patch の candidate-level equivalence 実測検証完了 (100% 一致)
- [ ] **Phase D: Math Canonical Production (30候補)**
  - Linear Safety-Patch (3候補): FULL_REUSE 適用
  - 非Linear 9手法 (27候補): canonical sources から再マージ・再生成
- [ ] **Phase E: 共通・専門ベンチマークの全10手法統合比較**
  - Safety 4種 + XSTest + Math 2種 + General 4種
- [ ] **Phase F: 正式 Math E1 確定（Final Table）**
  - 5段階 Gate 判定（Gate 0〜4）に基づく最終成立判定
- [ ] **Phase G: E2 重み空間の機序解析**
  - 成功モデル vs 3大失敗類型（Safety, Degeneration, Utility Failure）
- [ ] **Phase H: E3 統制介入実験**
- [ ] **Phase I: Code / Medical への展開**
- [ ] **Phase J: 発展検証 (E4/E5)**
