# Task: Math Production E1 比較実験および正規化振る舞い等価性実証 (E0c)

## 概要
Math Pilot による全実験配線の実測縦通し（E0→マージ→リロード→生成→採点→再集計→E1セレクタ）の成功を受け、Pilot（小標本）から**本物の Math Production 比較実験**へ昇格させる。

### 主要タスク
1. **Tokenizer Consistency Gate の厳格化**:
   - `len(tokenizer) == 32000`
   - `model.config.vocab_size == 32000`
   - `input_embeddings.num_embeddings == 32000`
   - `lm_head.out_features == 32000`
   - `pad_token_id == 2`
   - Base Llama-2-7b-hf のトークナイザを canonicalized モデルへ完全統一。
2. **E0c 振る舞い等価性検証 (Canonicalization Behavioral Equivalence Test)**:
   - Original vs Canonical (WizardMath & SafetyFT) において、同一入力トークン列（input ids < 32000, seq_len <= 2048）での推論比較：
     - `max_abs_logit_diff`
     - `mean_abs_logit_diff`
     - `argmax_agreement`
     - `generation_exact_match`
   - 「語彙正規化は単に未使用の PAD 行を除去しただけであり、共有語彙上の振る舞いを一切改変していない」ことを数値で実証。
3. **`max_position_embeddings = 2048` の Runtime 固定**:
   - `min(Base, Math, Safety) = 2048`
   - 全モデルを共通にサポートされるコンテキスト長内で評価。
4. **Standalone Reference Evaluator (実測ベースライン)**:
   - WizardMath ($\alpha=0.0$), SafetyFT ($\alpha=1.0$), Base (Llama-2) の単体実測。
   - `baseline_overrefusal` を固定値（0.02）ではなく、同一プロンプト集合・同一 detector からの実測値として取得・保存。
5. **Math Production E1 Runner (Phase E1-a: Linear Safety-Patch)**:
   - $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$（seed 42）
   - 本番データセット規模での ASR_all, ASR_valid, VRR, overrefusal, utility の実測比較。

## タスクリスト
- [x] Canonicalized モデルのトークナイザを Base Llama-2-7b-hf に統一（len=32000, pad_token_id=2）
- [ ] `v4/scripts/audit/test_canonical_equivalence.py` の実装と実機検証（E0c）
- [ ] `v4/scripts/eval/eval_standalone_references.py` の実装と実測ベースライン取得
- [ ] `v4/scripts/analysis/run_math_production_e1.py` の実装
- [ ] Linear Safety-Patch 6 候補（$\alpha=0.0, 0.2, 0.4, 0.6, 0.8, 1.0$）の実測実行と E1 Selector 判定
- [ ] ドキュメント（`task.md`, `implementation_plan.md`, `walkthrough.md`）の作成と報告
