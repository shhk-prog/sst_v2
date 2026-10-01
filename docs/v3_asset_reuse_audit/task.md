# タスクリスト: v3資産再利用監査およびMath Production E1準備 (v3_asset_reuse_audit)

## 状態凡例
- [ ] 未着手 (TODO)
- [/] 進行中 (IN_PROGRESS)
- [x] 完了 (DONE)

---

## 1. 資産インベントリ調査・マッピング
- [x] 1.1 v3 の `results/`（生成レスポンス・評価結果）の保有状況調査
  - Safetyベンチマーク: HarmBench, JailbreakBench, StrongREJECT, WildJailbreak (全1053件完全保有を確認)
  - Mathユーティリティ: GSM8K, MATH500 (完全保有を確認)
  - その他: Benign/Harmless (XSTest等) の有無確認 (未評価のため新規生成対象と特定)
- [x] 1.2 v3 の `models/merged/`（チェックポイント）の保有状況調査
  - Math Linear (Task Arithmetic) $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$, seeds 42, 43, 44 (全18モデル完全保有)
  - TIES, DARE, DELLA 等のベースライン (全54モデル完全保有)
- [x] 1.3 候補モデルのプロベナンス（モデル構成・元重み・ハイパーパラメータ）突合

## 2. 監査スクリプト `v3_reuse_audit.py` の設計・実装
- [x] 2.1 4分類（FULL_REUSE, RESCORE_ONLY, DIAGNOSTIC_ONLY, REGENERATE）の判定ロジック設計
  - Checkpoint Canonical Equivalence 判定（PAD行削除との可換性・差分検証）
  - Response provenance / format 判定
  - 不足データ（benign, over-refusal）の検出
- [x] 2.2 `v4/scripts/audit/v3_reuse_audit.py` の実装
- [x] 2.3 全90候補（Primary 18, Baselines 54, Code 18）の監査実行とマニフェスト出力 (`v4/results/audit/v3_reuse_manifest.json`)
  - RESCORE_ONLY: 72候補
  - DIAGNOSTIC_ONLY: 18候補 (WizardCoder)

## 3. レスポンス再採点・不足分補完・E1セレクター連携
- [x] 3.1 v3レスポンスに対する v4 Evaluator（HarmBench Classifier / Validity / ASR_valid / VRR）再採点 (`rescore_v3_responses.py`)
  - Linear Safety-Patch 3シード（18候補・計18,954生成）の再採点完了
- [x] 3.2 3-Seed Aggregate Performance Table の集計・出力 (`aggregate_3seed_results.py`)
- [x] 3.3 不足データ（Benign評価等）の最小限新規生成計画の策定
- [x] 3.4 結果のまとめと `walkthrough.md` の作成
