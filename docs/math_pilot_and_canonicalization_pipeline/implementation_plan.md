# 実装計画書: Math 単独領域パイロット実験および正規化パイプライン

## 1. 背景と基本方針
コード監査ループ（`f5fd784e`）の完了を受け、研究を実証段階へ進める。
WizardCoder は RoPE 周波数の 100 倍差（10,000 vs 1,000,000）により Primary 実験から分離（Stress Test 扱い）とし、まずは **Math 領域（WizardMath-7B-V1.0 + SafetyFT seed42 + Llama-2-7b-hf）** にて 1 本の縦通し（Pilot）を完成させる。

### 単一正規化（Canonicalization）の厳格定義
1. **Canonical Vocabulary = 32000**:
   - Base（Llama-2-7b-hf: vocab_size=32000）を真の基準とする。
   - WizardMath および SafetyFT の index 32000 (`[PAD]`) 行は、バッチ学習時の便宜的追加行であるため、マージ対象外としてスライス除去（`embedding[0:32000]`, `lm_head[0:32000]`）。
   - 推論時の PAD トークンは LLaMA-2 標準の `eos_token_id` (2) に再設定。
   - 0〜31999 の SentencePiece 語彙は実機検証で 100% 同一（SHA256: `f88fa5c5f23d10390aa651f9ac9b119fb0cbfbf4c49f098af0b3a4b3f350e9fa`）であることを確認済み。
2. **RoPE & 評価シーケンス長**:
   - `rope_theta = 10000.0`
   - `max_eval_length <= 2048`（GSM8K/MATH の問題・回答は通常 1000 トークン未満）

## 2. 実装コンポーネント
### 2.1 `v4/scripts/audit/canonicalize_vocab.py`
- 入力モデル（HuggingFace ID またはローカルパス）を読み込む。
- `model.embed_tokens.weight` と `lm_head.weight` をスライス `[0:32000, :]`。
- `config.json` の `vocab_size` を 32000、`pad_token_id` を 2 に設定。
- 出力先に safetensors 形式で重みと config, tokenizer を保存。
- `canonicalization_manifest.json` を生成・保存。

### 2.2 `v4/scripts/audit/audit_canonicalized_models.py`
- Base, Canonicalized Math, Canonicalized Safety の 3 者について E0 整合性監査を実施。
- `canonicalization_manifest.json` の完全性、テンソル shape の完全一致、tokenizer ハッシュの一致を検証。
- Math Domain の適合性を判定。

### 2.3 `v4/scripts/run_math_pilot.py`
- Linear Safety-Patch ($\alpha=0.6$) による 1 候補のマージ実行。
- 重みの保存とリロード検証。
- 有害プロンプト生成および無害プロンプト生成（small subset）。
- 数学効用評価（GSM8K/MATH small subset）。
- HarmBench 判定、有効性判定。
- ログ保存と再集計（`reaggregate_v3_logs.py` / `e1_selector.py`）。
- E1 selector による実測判定。
