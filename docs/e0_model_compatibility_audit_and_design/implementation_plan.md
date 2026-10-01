# 実装・調査計画書: E0 モデル互換性監査と研究設計

## 1. 目的
コード修正ループが `f5fd784e` で確定したため、実験対象モデル（Base: Llama-2-7b, Math: WizardMath-7B, Code: WizardCoder-Python-7B, Safety: Safety-FT）の互換性不一致について実証的監査を行う。

差分を以下の4象限に分類する：
1. **重み空間マージを本当に不可能にする差（Incompatible in Weight Space）**
2. **config上の差だが parameter tensor は対応する差（Tensor-Compatible Config Discrepancy）**
3. **tokenizerの追加token等で明示的な整合処理が可能な差（Resolvable via Tokenizer / Embedding Normalization）**
4. **研究条件としてモデルを入れ替えるべき差（Fundamental Architecture / RoPE Discrepancy requiring Model Replacement）**

## 2. 調査項目
1. **Tokenizer & Added Tokens の実体調査**:
   - `vocab_size: 32000 vs 32001` の 32000 番目のトークンの正体
   - `bos_token_id: 1 vs 2` のマッピング実体
2. **Weight Tensor Shapes & Layer Counts**:
   - `embed_tokens.weight` および `lm_head.weight` の実際の shape
   - 32層の Transformer レイヤー（Attention / MLP / LayerNorm）のテンソル対応
3. **RoPE & Position Embeddings の数理的影響**:
   - `max_position_embeddings`: 4096 vs 2048 vs 16384
   - `rope_theta`: 10000 vs 1000000 による回転周波数の 100 倍差が Attention 重み空間マージに及ぼす影響
