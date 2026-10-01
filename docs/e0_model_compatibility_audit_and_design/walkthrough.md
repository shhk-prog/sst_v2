# E0 モデル互換性監査および研究設計レポート (Walkthrough)

## 1. 監査サマリーと 4 分類マトリクス

`f5fd784e` におけるコード監査ループ完了を受け、E0 ゲートで検出された不整合について実機上のキャッシュ・重みテンソル・トークナイザ実体を詳細に監査しました。

本監査の結果、各不整合は以下のように明確に 4 分類されます。

| 分類 | 該当項目 | 対象モデル | 実態と判定根拠 | 処置・対応方針 |
| :--- | :--- | :--- | :--- | :--- |
| **① 重み空間マージを本当に不可能にする差** | なし（バックボーン層） | 全モデル | 32層の Transformer 層（Attention $W_q, W_k, W_v, W_o$、MLP $W_{\text{gate}}, W_{\text{up}}, W_{\text{down}}$、LayerNorm）はすべて完全同型（4096 / 11008）。テンソル次元の不一致による物理的マージ不能箇所は存在しない。 | バックボーンの重み補間自体は全層で可能。 |
| **② config上の差だが parameter tensor は対応する差** | `max_position_embeddings` (2048 vs 4096) | Math (WizardMath) | LLaMA-2 は RoPE（回転位置埋め込み）を採用しており、絶対位置埋め込みテーブルを持たないためパラメータテンソルは変化しない。Math は `rope_theta = 10000.0` で Base と同一であり、2048 トークン以内では相対位置計算が完全一致する。 | 評価入力長を 2048 トークン以内（GSM8K/MATH は通常数百トークン）に制限することで、推論の幾何的歪みなしに Base config (4096) 下で運用可能。 |
| **③ tokenizerの追加token等で明示的な整合処理が可能な差** | `vocab_size` (32000 vs 32001)<br>`bos_token_id` (1 vs 2) | Math, Code, Safety | **実体解明**: Math, Code, Safety の 3 モデルすべてにおいて、index 32000 は共通の `[PAD]` トークン。0〜31999 は LLaMA-2 標準 SentencePiece 語彙と完全同一。Code の `bos_token_id=2` は tokenizer_config 上で `</s>` が割り当てられているのみ。 | **正規化処理**: Base の Embedding / LM-Head を 32001（`[PAD]` 行を追加）に拡張してマージするか、マージ時に index 32000 をスライスして 32000 で揃え、PAD は LLaMA-2 標準の EOS(2) / UNK(0) で代用。 |
| **④ 研究条件としてモデルを入れ替えるべき差** | **`rope_theta` (10000 vs 1000000)**<br>`max_position_embeddings` (16384) | Code (WizardCoder) | **致命的差分**: CodeLlama-Python-7B 由来の `rope_theta = 1,000,000` は、Base (Llama-2, 10,000) と **100 倍の周波数差** を持つ。Attention の Query-Key 重みが学習した回転角度空間が根本的に異なり、重み補間により自然言語安全注意またはコード長距離注意のいずれかが機能不全（Attention 崩壊）を起こす。 | **モデル入替推奨**: Base (Llama-2-7b, `rope_theta=10000`) を共通祖先とするコードモデル（例: LLaMA-2-7b ベースの CodeAlpaca, Magicoder, または Llama-2-7b-hf 上でファインチューニングされたコードモデル）に差し替える。 |

---

## 2. 実証調査データ詳細

### 2.1 Tokenizer & Added Tokens の実体
実機上の Hugging Face キャッシュから各モデルのトークナイザをロードして調査した結果：

```text
=== base: meta-llama/Llama-2-7b-hf ===
  vocab_size: 32000, len(tokenizer): 32000
  bos_token: <s> (id: 1), eos_token: </s> (id: 2), pad_token: None
  added_tokens: {'<unk>': 0, '<s>': 1, '</s>': 2}

=== math: WizardLMTeam/WizardMath-7B-V1.0 ===
  vocab_size: 32000, len(tokenizer): 32001
  bos_token: <s> (id: 1), eos_token: </s> (id: 2), pad_token: [PAD] (id: 32000)
  added_tokens: {'<unk>': 0, '<s>': 1, '</s>': 2, '[PAD]': 32000}

=== code: vanillaOVO/WizardCoder-Python-7B-V1.0 ===
  vocab_size: 32000, len(tokenizer): 32001
  bos_token: </s> (id: 2), eos_token: </s> (id: 2), pad_token: [PAD] (id: 32000)
  added_tokens: {'<unk>': 0, '<s>': 1, '</s>': 2, '[PAD]': 32000}

=== safety: v3/models/temp_safety_full_seed42 ===
  vocab_size: 32001, len(tokenizer): 32001
  pad_token: [PAD] (id: 32000)
```

**判明した重要事実**:
1. `vocab_size: 32000 -> 32001` の 1 トークン差は、**Math, Code, Safety の全ファインチューンドモデルにおいて完全に共通の `[PAD]` (id 32000)** である。
2. Base モデルのみが 32000（PAD なし）であり、FT 時にバッチ学習の便宜上 `[PAD]` が 1 行追加されただけである。
3. 語彙テーブル 0〜31999 は 4 モデルすべてで完全に同一のトークン列・ID 体系を共有している。

---

### 2.2 重みテンソル Shape の完全一致性
モデルの重みパラメータ（全層）を調査した結果：

| レイヤー / パラメータ名 | Base (Llama-2-7b) | Math (WizardMath) | Code (WizardCoder) | Safety (Safety-Full) |
| :--- | :--- | :--- | :--- | :--- |
| `model.embed_tokens.weight` | `[32000, 4096]` | `[32001, 4096]` | `[32001, 4096]` | `[32001, 4096]` |
| `lm_head.weight` | `[32000, 4096]` | `[32001, 4096]` | `[32001, 4096]` | `[32001, 4096]` |
| `layers.*.self_attn.q_proj` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` |
| `layers.*.self_attn.k_proj` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` |
| `layers.*.self_attn.v_proj` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` |
| `layers.*.self_attn.o_proj` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` | `[4096, 4096]` |
| `layers.*.mlp.gate_proj` | `[11008, 4096]` | `[11008, 4096]` | `[11008, 4096]` | `[11008, 4096]` |
| `layers.*.mlp.up_proj` | `[11008, 4096]` | `[11008, 4096]` | `[11008, 4096]` | `[11008, 4096]` |
| `layers.*.mlp.down_proj` | `[4096, 11008]` | `[4096, 11008]` | `[4096, 11008]` | `[4096, 11008]` |
| レイヤー数 (Layers Count) | **32** | **32** | **32** | **32** |

バックボーンの重みテンソルは 32 層すべてにおいて 1 対 1 に対応しており、テンソル shape 上の不整合は `embed_tokens` と `lm_head` の 32000 行目（PAD トークン）の有無のみである。

---

### 2.3 RoPE周波数と Attention 幾何学の数理的分析（最重要課題）

#### RoPE の定式化
LLaMA の Rotary Position Embedding では、次元 $d$ の各周波数基底 $\theta_i$ は以下で定義されます：
$$\theta_i = \text{rope\_theta}^{-2(i-1)/d}, \quad i \in \{1, \dots, d/2\}$$

Query $q_m = W_q x_m$ と Key $k_n = W_k x_n$ の Attention スコアは、相対位置 $n-m$ の回転行列 $R_{\Theta, n-m}$ を介して計算されます：
$$q_m^\top k_n = x_m^\top W_q^\top R_{\Theta, n-m} W_k x_n$$

#### 100 倍の基底差（10,000 vs 1,000,000）がもたらす影響
- **Base (Llama-2-7b) & Math (WizardMath) & Safety**: $\text{rope\_theta} = 10,000$
  最小周波数は $\theta_{d/2} = 10000^{-1} = 0.0001$。
- **Code (WizardCoder-Python-7B)**: $\text{rope\_theta} = 1,000,000$ (CodeLlama 由来)
  最小周波数は $\theta_{d/2} = 1000000^{-1} = 0.000001$。

#### モデルマージ時の幾何学的衝突
Attention 重み行列 $W_q, W_k$ は、学習時に適用された特定の回転周波数分布 $\Theta$ に適合するように最適化されています。
1. **WizardMath**:
   $\text{rope\_theta} = 10,000$ で学習されているため、Base および Safety と回転幾何学が完全に一致しています。最大長 2048 という制約は学習データの切り捨て長に過ぎず、RoPE の周波数スケール自体は Base と完全同一です。
2. **WizardCoder-Python**:
   $\text{rope\_theta} = 1,000,000$ で事前学習（CodeLlama）および事後学習されています。
   重み空間において $W_q^{(\text{code})}$ と $W_q^{(\text{base})}$ または $W_q^{(\text{safety})}$ を線形結合した場合：
   - マージ後モデルの推論を `rope_theta = 10000` で行うと、Code 由来の成分は想定の 100 倍速い回転を受け、コードの文脈・スコープ理解が破綻します。
   - `rope_theta = 1000000` で行うと、Base / Safety 由来の成分は想定の 1/100 の回転しか受けず、安全性の拒否判断や自然言語指示への注意が失われます。

---

## 3. 研究設計としての結論と推奨アクション

### 結論
1. **Math (WizardMath-7B) は正規化により E0 を正当に通過可能**:
   - `vocab_size: 32001`: `[PAD]` トークンのスライシングまたはパディングによる明示的整合処理。
   - `max_position_embeddings: 2048`: 評価入力長制限の明示的仕様化（GSM8K/MATH は通常 < 1024 トークン）。
2. **Code (WizardCoder-Python-7B) は「4. 研究条件としてモデルを入れ替えるべき差」に該当**:
   - 祖先モデルが CodeLlama-Python (RoPE $\theta=10^6$) であり、Llama-2 (RoPE $\theta=10^4$) との重み空間マージは推論幾何学を破綻させます。
   - 単に config を `rope_theta=10000` に上書きしてマージすることは、科学的・実証的に妥当なマージになり得ません。

### 次の具体的ステップの提案
- **選択肢 1 (推奨・厳格)**:
  Code 領域のモデルとして、**Llama-2-7b-hf を共通祖先とし `rope_theta = 10000.0` を保持しているコードモデル**（例: Llama-2 上で学習された CodeAlpaca-7b や Magicoder-OSS-Instruct-7B 等）へ入れ替える。
  これにより、Math, Code, Safety の 3 領域すべてが真に同一起源・同一幾何空間の Llama-2-7b ファミリーとなり、科学的に正当な多ドメイン安全マージ実験が成立する。
- **選択肢 2 (段階的実証)**:
  まずは **Math 単独領域**（WizardMath + Safety + Base）について、上記の Tokenizer/PAD 正規化アダプタを導入して E0 を正式通過させ、1 領域・1 seed・1 手法での生成・採点・保存・再集計の End-to-End 接続を先行して実証・完了する。
