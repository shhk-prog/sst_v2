# Task: Math 単独領域パイロット実験および正規化パイプライン (Math Pilot & Canonicalization)

## 概要
コミット `f5fd784e25224e6f8aede6667430c99c6da7ddd8` によりコード監査ループが完了した。
次のフェーズとして、RoPE周波数不整合（100倍差）を抱える WizardCoder は Stress Test 枠へ移し、Primary 実験は同一起源の LLaMA-2-7B ファミリーである **Math 領域（WizardMath-7B-V1.0 + SafetyFT seed42 + Llama-2-7b-hf）に絞って縦通し（Pilot）を完成させる**。

### コア設計方針
1. **Canonical Vocabulary = 32000**:
   - Base に人工的な 32000 行目を作らず、Math および Safety の index 32000 (`[PAD]`) 行をマージ対象外としてスライス除去。
   - `pad_token_id = eos_token_id = 2` に統一。
   - 実機検証済みの 0..31999 共通語彙（SHA256: `f88fa5c5...`）だけで weight-space merge を定義。
2. **E0 Canonicalization Manifest**:
   - 何を正規化したか（dropped token, pad token, max eval length 2048, rope_theta 10000 等）を明示的に manifest に記録。
   - 正規化前後のテンソル数、パラメータ数、削減パラメータ数、トークナイザハッシュ、embedding/lm_head shape を完全記録。
3. **Math Pilot 縦通し**:
   - E0 PASS → Linear Safety-Patch ($\alpha=0.6$) → 重み保存 → リロード → 有害プロンプト生成 → 無害プロンプト生成 → 数学効用評価（GSM8K/MATH subset） → HarmBench 判定 → 有効性判定 → 再集計 → E1 selector
   - 全段を実測値で 1 本接続する。

## タスクリスト
- [x] 実機での Base と WizardMath のトークン 0..31999 完全一致実証（Mismatches: 0, SHA256 一致確認）
- [ ] `v4/scripts/audit/canonicalize_vocab.py` の実装
- [ ] `v4/scripts/audit/audit_canonicalized_models.py` の実装
- [ ] WizardMath および Safety-Full の canonical モデル生成と manifest 出力
- [ ] `v4/scripts/run_math_pilot.py` (または `run_math_pilot.sh`) の実装
- [ ] Pilot 実行による全段（E0〜E1）の実測 End-to-End 接続確認
- [ ] ドキュメント（`task.md`, `implementation_plan.md`, `walkthrough.md`）の作成と報告
