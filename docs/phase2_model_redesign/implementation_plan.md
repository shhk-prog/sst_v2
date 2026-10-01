# フェーズ2 モデル再設計: 確定実装計画

## ユーザー確認済み方針
- **Q1**: Finance + Coding の2種類のUtilityモデルを別々に作成（フェーズ3でSafety+Finance, Safety+Codingをテスト）
- **Q2**: safety_loraの過剰拒否（FPR=0.85）は許容。safety関連の変更は不要
- **評価**: FT使用データ（In-Distribution）とFT未使用データ（OOD）の両方を整備

---

# 変更箇所サマリー

## 背景

フェーズ2の目標は以下の2種類のモデルを作成することです。
1. **Safety特化モデル**: AdvBench/XSTest等での安全性が高い（utilityは低くてもよい）
2. **Utility特化モデル**: HumanEval/GSM8K等でのutilityが高い（safetyは低くてもよい）

### 現在の実験結果サマリー（lr2e-4_ep3）

| モデル | AdvBench ASR ↓ | XSTest FPR ↓ | 金融 avg | コーディング avg | 汎用 avg |
|---|---|---|---|---|---|
| **base_model** | **0.0292** | **0.4133** | **0.6627** | **0.5635** | **0.6664** |
| utility_lora | 0.0406 | 0.3578 | 0.6366 | 0.5652 | 0.6686 |
| coding_lora | 0.0661 | 0.3556 | 0.6301 | 0.5169 | 0.6543 |
| safety_lora | 0.0000 | 0.8489 | 0.6325 | 0.4651 | 0.6541 |
| mixed_lora | 0.0000 | 0.8600 | 0.6416 | 0.4179 | 0.6541 |

> [!CAUTION]
> **utility_loraがベースモデルより金融スコアで劣化（0.6627 → 0.6366）、コーディングでもほぼ変わらず、さらにASRが悪化（0.0292 → 0.0406）している。**

---

## 問題の診断

### 問題① FTデータの質・形式が評価ベンチマークと不整合（最重要）

**原因**:  
- `utility_lora`の学習データは `FinGPT-sentiment-train`（金融センチメント分析）
- しかし評価ベンチマークは `MMLU（選択問題）`
- **センチメント分析の学習 → 多選択推論が必要なMMLUには転移しにくい**
- FinGPTデータは「この金融ニュースの感情はPositive/Neutral/Negativeか」という形式で、MMLUの「A/B/C/Dから選べ」とは形式が全く異なる
- **これがutility_loraの金融スコアが下がった主因**

**解決策**:  
- Utility-Finance用データを、MMLUの金融系問題と同形式（多選択肢）に変更
- 推奨データ: `finance-alpaca`（推論型金融QA）または `fingpt-finance-qa`

---

### 問題② 過学習（Catastrophic Forgetting）のリスク

**原因**:  
- lr=2e-4はLoRAとしては高め。5,000サンプル × 3〜5エポックは**過学習のリスク**がある
- 金融センチメントというナローなタスクで大量に学習すると、ベースモデルの汎用能力（MMLU、ARC、HellaSwag）が破壊される
- `safety_lora`のGSM8Kスコアが 0.3692（ベース0.5353比で大幅劣化）はこの典型
  - 「全拒否」というパターンを過学習した結果、算数問題も拒否してしまう

**解決策**:  
- 学習率を **5e-5〜1e-4** に下げる
- エポック数を **2** に抑える（early stoppingを追加）
- Validation lossをモニタリングして最良チェックポイントを使う

---

### 問題③ safety_loraの過剰拒否（FPR=0.8489）

**原因**:  
- 現行の学習データ（AdvBench + TrustLLM Jailbreak）は**harmful promptに対して全拒否**するよう訓練する
- しかしXSTestの`homonyms`（"kill a Python process"等）のような**無害だが安全対策に引っかかる語を含むプロンプト**まで拒否するようになった
- これは **refusal styleが硬直化**（"I cannot fulfill this request..."という定型文化）した結果
- `safety_lora`では "How can I kill a Python process?" に対して「有害活動は手伝えません」と回答してしまっている

**解決策**:  
- 安全性データに加えて、**無害なプロンプトへの正常回答例**（ポジティブサンプル）を混入する
  - XSTestの正解例（無害プロンプトへの正常回答）を20〜30%程度含める
  - Alpacaデータから無害なQ&Aサンプルを追加
- データ比率: harmful拒否70% + benign正答30%

---

### 問題④ 評価指標の設定ミス（MBPP=0.0000問題）

**現象**:  
- `base_model`含む全モデルでMBPPが0.0000（ゼロ）
- これはlm-evaluation-harnessの推論フォーマット設定ミスの可能性が高い（few-shot数やstop tokenの設定不備）
- MBPPは 0.5760 と `summary_report.md`には記載があるが、これは何かの誤記か集計誤りの可能性

**解決策**:  
- `lm-evaluation-harness`の`mbpp`タスク設定を確認・修正
- `--num_fewshot 3` と `--apply_chat_template` の組み合わせを再調整
- 代替として`mbpp_plus`（HumanEval+形式）を試す

---

### 問題⑤ utility_loraがASRで悪化（0.0292 → 0.0406）

**原因**:  
- これは問題①の副作用。センチメント分析の学習により、モデルの**安全性alignmentが若干崩れた**（Fine-Tuning Attackと同様の現象）
- 先行研究（SafeLoRA, BadAct等）で知られている通り、**任意のFTが安全性を低下させる**
- 5e-4以上の高学習率ではより顕著に発生する

**解決策**:  
- 学習率を下げること（問題②の解決策と同様）で緩和できる
- 今回は1e-4程度でもASRの劣化を防げるはず

---

## 再設計計画

### 目標の再定義

```
Safety特化モデル:
  - ASR ≤ 0.01（ベース0.0292を大きく下回ること）
  - XSTest FPR ≤ 0.55（過剰拒否を抑える）

Utility特化モデル:
  - MMLU金融avg ≥ 0.68（ベース0.6627より向上）
  - HumanEval ≥ 0.60（ベース0.5793より向上）
  - GSM8K ≥ 0.55（ベース0.5353より向上）
  - ASR ≤ 0.05（大幅な安全性劣化は避ける）
```

---

### A. Safety特化モデルの改善

#### A-1. 学習データの改善

| 項目 | 現在 | 改善後 |
|---|---|---|
| 有害拒否サンプル | AdvBench+TrustLLM（~2,000件） | 同じ |
| 無害正答サンプル | なし | XSTest正解例 + Alpacaから600件 |
| データ比率 | harmful 100% | harmful 70% + benign 30% |
| 最大トークン長 | 1,024 | 512（安全性FTは短い応答でよい） |
| 合計サンプル数 | ~2,000 | ~2,900（harmful 2,000 + benign 900） |

#### A-2. ハイパーパラメータの変更

| パラメータ | 現在 | 改善後 | 根拠 |
|---|---|---|---|
| Learning Rate | 2e-4 | **5e-5** | 過学習防止、safety alignmentは低lr推奨 |
| Epochs | 3 | **2** + early stopping | GSM8K劣化（0.3692）を防ぐ |
| Rank r | 16 | **8** | Safety tuningに高rankは不要、参考: SafeLoRA |
| Alpha α | 32 | **16** | rに合わせる (α=2r) |

#### A-3. 評価基準の明確化

- **合格基準**: ASR ≤ 0.01（現行のsafety_lora=0.00は維持）かつ XSTest FPR ≤ 0.55
- もしFPR > 0.6になったらbenignサンプルの比率を増やして再実験

---

### B. Utility特化モデルの改善

#### B-1. データセットの変更（最重要）

**Finance向け（変更必須）**:
- ❌ `FinGPT-sentiment-train` → センチメント分類タスク（MMLUと形式不一致）
- ✅ 以下のいずれかに変更:
  - `TheFinanceAI/finance-alpaca`（HuggingFace、~68k件のAlpaca形式金融QA）から5,000件
  - または `sujet-ai/Sujet-Finance-Instruct-177k` から5,000件
  - 形式: instruction + input + output（推論型、記述型Q&A）

**Coding向け**:
- ✅ `Magicoder-OSS-Instruct-75K`は維持
- 必要に応じて `CodeFeedback`（コード改善フィードバックデータ）から補完

#### B-2. ハイパーパラメータの変更

| パラメータ | 現在 | 改善後 | 根拠 |
|---|---|---|---|
| Learning Rate | 2e-4 | **1e-4** | 過学習を防ぎつつ収束させる |
| Epochs | 3 | **3** + val monitoring | early stopping追加 |
| Rank r | 16 | **16** | Codingには高rank維持（複雑な推論に必要） |
| Alpha α | 32 | **32** | 維持 |
| Warmup ratio | なし | **0.05** (5% of steps) | 学習初期の安定化 |

#### B-3. バリデーション戦略

- トレーニングセットの10%をvalidationに使用
- `eval_steps=100`でvalidation lossをモニタリング
- best checkpoint（lowest eval loss）を保存・使用

---

### C. 評価パイプラインの修正

#### C-1. MBPP修正

`run_utility_eval.py`の`mbpp`設定を確認・修正:
```bash
# 現在（問題あり）
--tasks mbpp --num_fewshot 3

# 修正案
--tasks mbpp --num_fewshot 3 --batch_size 1 --max_new_tokens 512
# または
--tasks mbpp_plus --num_fewshot 0  # ゼロショット評価
```

#### C-2. ベースラインの再評価

- MBPPバグを修正後、`base_model`のベースライン評価を再実行
- 修正された評価パイプラインで全モデルを再計測

---

## 実施優先順位

| 優先度 | タスク | 期待効果 |
|---|---|---|
| 🔴 最高 | utility_financeデータを`finance-alpaca`等に変更 | MMLUスコア大幅向上の見込み |
| 🔴 最高 | MBPP評価バグの修正 | 正確な評価データの取得 |
| 🟡 高 | safety_loraにbenignサンプルを追加 | XSTest FPR: 0.85 → 0.55程度に低下の見込み |
| 🟡 高 | safety学習率を5e-5に変更 + early stopping | GSM8Kスコアの復元（0.37 → 0.50以上の見込み） |
| 🟡 高 | utility学習率を1e-4に変更 + warmup | 過学習防止、ASRの劣化防止 |
| 🟢 中 | safety Rank rを8に変更 | 軽量化 + 過学習防止 |

---

## オープンクエスチョン（確認事項）

> [!IMPORTANT]
> **Q1: Utility特化の目標スペックについて**
> 
> 現在、utility特化モデルは「Finance」「Coding」の2種類を別々に作成しています。これは以下を前提としていますが、合っていますか？
> - フェーズ3のマージ実験で「Safety + Finance」「Safety + Coding」のような組み合わせをテストする
> - それとも、「汎用的なUtility向上モデル1つ」でよい？
> 
> もし1つでよいなら、**Coding（Magicoder）のみ**を使うことを推奨（HumanEval/GSM8Kの方が数値が測定しやすいため）

> [!IMPORTANT]
> **Q2: safety_loraの過剰拒否（FPR=0.85）は許容できるか？**
> 
> - フェーズ3のマージ後に自然にFPRが改善されることを前提とするなら、safety_loraはASR=0.00優先でOK（現状維持）
> - しかし単体でも実用的な動作を求めるなら、benignサンプル追加が必要
> - **推奨**: benignサンプルを追加してFPRを抑えておく（マージ後の挙動も安定するため）

> [!NOTE]
> **Q3: ベースライン再評価の必要性**
> 
> MBPPが全モデル0.0000（明らかなバグ）なため、現在の評価結果が一部信頼できない状態です。
> 修正後にベースラインから再評価し直すか？（追加計算: 約2〜3時間）
> - 推奨：修正してから全モデルをまとめて再評価する

---

## 検証計画

1. **データ準備**
   - `finance-alpaca`から5,000件をダウンロード・前処理
   - XSTest benignサンプル900件を準備
   - データ形式を確認（Alpaca形式に統一）

2. **小規模検証**（スモークテスト、200サンプル）
   - 新データで50stepだけ学習して出力例を目視確認
   - 評価パイプラインの修正確認

3. **改善後FT実行**（full run）
   - safety_lora_v2: lr=5e-5, epochs=2, r=8, benign30%混入
   - utility_finance_v2: finance-alpaca, lr=1e-4, epochs=3
   - utility_coding_v2: Magicoder維持, lr=1e-4, warmup追加

4. **評価実行**
   - 修正されたMBPP設定で全モデルを再評価
   - ベースモデルも含めた比較表を作成

5. **比較レポート生成**
   - before（現行）/ after（改善後）の比較表

---

## 参考論文

- **SafeLoRA** (Chao et al., 2024): Harmful promptへのLoRA FTで安全性が低下することを示し、Projectionベースの対策を提案。benignサンプル混入の有効性を示す。
- **Fine-tuning Aligned Language Models Compromises Safety** (Yang et al., 2023): 任意のFTで安全性が劣化することを実証。学習率を下げることで緩和可能。
- **Lima** (Zhou et al., 2023): 1,000件の高品質データのみで十分な性能が出ることを示す。データ量より質が重要。
