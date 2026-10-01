# FLMSEC 論文 (flmsec_EN.tex) 修正および数値再集計・整合化計画 (Implementation Plan)

## 概要 (Overview)
本計画は、`/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_EN.tex` を `/mnt/nas/home/hiromi/src/sst_v2/v3/results` および `/mnt/nas/home/hiromi/src/sst_v2/v3/scripts` の実データと整合させ、論文としての精度・整合性・査読耐性を大幅に高めるための包括的な修正計画です。

主な焦点は以下の通りです：
1. **数値の数学的整合性の確立**: $\mathrm{VSR} = \mathrm{VRR}(1 - \mathrm{ASR}_{\text{valid}})$ および $\mathrm{ASR}_{\text{all}} = \mathrm{VRR} \cdot \mathrm{ASR}_{\text{valid}} + (1 - \mathrm{VRR}) \cdot \mathrm{ASR}_{\text{invalid}}$ の関係を保つ統一集計ロジックの適用と全表・本文数値の再生成・統一。
2. **方法と実装の不整合修正**: Validity 判定規則の正確な明記（未実装項目の削除／実効ルールの開示）、評価器の統合規則の明記と Evaluator 要約表 (Table X) の追加。
3. **過大主張の緩和と表現適正化**: 人手監査未実施に伴う "False Safe" / "False Unsafe" から "Apparent safety under degeneration" / "Apparent Unsafe under a single evaluator" への改称、および "linguistically valid" 等の言葉の適正化。
4. **本文と表の記述矛盾の解消**: Table 2 / Table 10 と本文数値の一致、MergeAlign vs AlignMerge の記述整理、Multi-domain 表 (Table 11/14) への VRR / Cond ASR / VSR 列の追加。
5. **Checklist / Broader Impacts / Asset-License 表の整備**: NeurIPS/FLMSEC Checklist を実状に合わせて修正し、Broader Impacts 節および Asset-License 表を Appendix に追加。

---

## ユーザー確認・検討事項 (User Review Required)

> [!IMPORTANT]
> **1. ASR と Conditional ASR の定義統一方針**
> 論文の最も中心的な修正点として、Original ASR ($\mathrm{ASR}_{\text{all}}$) と Conditional ASR ($\mathrm{ASR}_{\text{valid}}$) を**同じ harmful compliance ラベル $H_i \in \{0,1\}$** に基づいて定義し、
> $\mathrm{ASR}_{\text{all}} = \frac{1}{N}\sum_i H_i$, $\mathrm{ASR}_{\text{valid}} = \frac{\sum_i V_i H_i}{\sum_i V_i}$, $\mathrm{VRR} = \frac{1}{N}\sum_i V_i$, $\mathrm{VSR} = \frac{1}{N}\sum_i V_i(1-H_i)$
> として集計スクリプトを再実行・表数値を全修正します。これにより恒等式 $\mathrm{VSR} = \mathrm{VRR}(1-\mathrm{ASR}_{\text{valid}})$ が全ての表で完全に成立し、「生成崩壊によって従来の ASR が低く見える現象」が数学的に厳密な分解として示されます。

> [!NOTE]
> **2. 人手評価を行わない前提での用語変更**
> 現状のデータセットにおいて人手評価（Human adjudication）は含まれていないため、評価器の誤り率を断定する表現（"False Safe", "False Unsafe"）を、査読耐性のある客観的な診断表現（"Apparent safety under degeneration", "Apparent Unsafe under a Single Evaluator"）に変更します。

---

## 変更内容の詳細 (Proposed Changes)

---

### Component 1: 集計スクリプトと数値の再集計 (`v3/scripts/analysis`)

#### [MODIFY] [`compute_safety_diagnostics.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/compute_safety_diagnostics.py)
#### [MODIFY] [`generate_flmsec_hyo.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_flmsec_hyo.py)
#### [MODIFY] [`generate_specific_tables.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_specific_tables.py)

- **変更点**:
  - `compute_diagnostics` において、同じ有害フラグ $H_i$（HarmBench/LlamaGuard 等の判定）に基づいて $\mathrm{ASR}_{\text{all}}$ (Original ASR), $\mathrm{ASR}_{\text{valid}}$ (Conditional ASR), $\mathrm{VRR}$, $\mathrm{VSR}$ を一貫して算出するように統一。
  - 各実験条件（safety+code, safety+math, safety+medical, multi-domain）における平均値と標準偏差、および分母 ($N_{\text{valid}}/N$) を正しく集計。
  - Multi-domain (Table 14) の出力テーブルに Conditional ASR, VRR, VSR の各列を組み込む処理を追加。

---

### Component 2: 主論文 LaTeX ファイルの修正 (`v3/docs/flmsec`)

#### [MODIFY] [`flmsec_EN.tex`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_EN.tex)

##### 2.1 Abstract & Introduction
- **英文・文法修正**:
  - `we propose a validity-aware evaluation metrics` $\rightarrow$ `we propose a validity-aware evaluation protocol`
  - `These findings indicates that...` $\rightarrow$ `These findings indicate that...`
  - `model merge methods under a identical` $\rightarrow$ `under an identical`
  - `be assessed` $\rightarrow$ `should be assessed`
  - `SafetyUtility` $\rightarrow$ `safety--utility`
- **主張の限定と再構造化**:
  - 「ASR 単独では不十分」の文脈を、「本研究で指定したルールに基づく生成崩壊モードと有害非追従を区別する上で ASR 単独では不十分である」という限定的な表現に変更。
  - 新規性の主張を、単なる4指標の追加から「Secure Mergeにおけるパラメータ干渉による応答妥当性の低下と、それによる安全性の見かけ上の測定交錯 (measurement confound) の定式化」へと前面に出す。

##### 2.2 Methodology & Validity Rules
- **Validity Check の操作的定義への修正**:
  - Appendix C.3 の実際の実装（(i) whitespace 除外後に空出力、(ii) 5単語以上でユニーク語率 <20%、(iii) 5単語以上で数字のみの単語率 >60%）に記述を厳密に合致させる。
  - 未実装の special-token repetition や prompt repetition の自動検出は主張せず、「操作的なルールベースチェック」として範囲を限定。
- **過大表現の置き換え**:
  - `linguistically valid output` $\rightarrow$ `non-degenerate output under our rule-based checks`
  - `meaningful response` $\rightarrow$ `response that passes the specified validity checks`
  - `valid safety refusal` $\rightarrow$ `a non-degenerate response classified as non-compliant`
- **Evaluator 統合規則と Table X の追加**:
  - 各ベンチマーク（HarmBench, JailbreakBench, StrongREJECT, WildJailbreak）で使用されたプロンプトテンプレート、評価器（Classifier）、バージョン、および二値 Harmful-compliance ラベルへのマッピング規則をまとめた表 (Table X) を本文または Section 3 に追加・記述。

##### 2.3 Main Experiments & Table Corrections
- **Table 2 / Table 10 と本文の数値矛盾解消**:
  - Task Arithmetic (safety+code) などの本文の記述と Table 2 / Table 10 の数値を、再集計した同一スクリプト出力値に完全に統一。
- **MergeAlign と AlignMerge の記述整理**:
  - Section 3 / 4 にて「MergeAlign [14] を評価した一方で、AlignMerge [25] は公式実装が公開されていないため評価対象外とした」旨を明記。Table 14 や cost / GPU 時間表に MergeAlign が含まれることと不整合がないようにする。
- **Multi-domain 表 (Table 11 / Table 14) の更新**:
  - Multi-domain 実験表に VRR, Cond. ASR, VSR の各列を追加し、本文で述べられている multi-domain における崩壊と指標の有用性の記述を直接裏付ける。
- **指標の分母 ($N_{\text{valid}}/N$) と Utility 集約方法の定義追加**:
  - 各ドメインの Utility 平均は「各ベンチマークの百分率スコアの非重み付け算術平均」であることを明記し、個別の構成ベンチマーク結果を付録参照とする旨を追加。

##### 2.4 Section & Appendix 追加・修正
- **Broader Impacts 節の追加**:
  - `\section{Broader Impacts}` を本文または付録に追加し、本プロトコルが安全なデプロイに与えるポジティブな影響と、誤用リスクについての議論を明記。
- **Asset & License 表の追加**:
  - Appendix C に、使用モデル (Llama-2-7B, WizardMath, WizardCoder, MedAlpaca)、ベンチマーク (HarmBench, TrustLLM, etc.)、評価モデル (GPT-4) のバージョン、ライセンス、利用条件をまとめた Asset Table を追加。
- **Checklist の全項目改訂**:
  - Theory: `[N/A]` （理論定理・証明を含まないため）
  - Broader Impacts: `[Yes]` （追加した Broader Impacts 節に言及）
  - Safeguards: `[Yes]` / `[N/A]` （モデル・有害データの新規公開を行わないこと等の明確な理由を提示）
  - Licenses: `[Yes]` （Asset 表への参照を追加）
  - LLM Usage: `[Yes]` （AlpacaEval 2 での GPT-4 判定モデルの使用実態に即して正確に記述）

---

## 検証計画 (Verification Plan)

### 1. 自動計算・集計スクリプトの検証
- スクリプト `compute_safety_diagnostics.py` および `generate_specific_tables.py` を実行し、全条件において恒等式 $\mathrm{VSR} = \mathrm{VRR}(1-\mathrm{ASR}_{\text{valid}})$ が誤差なく成り立つか自動チェック。
- 再生成された LaTeX テーブル内の全数値と、`flmsec_EN.tex` 本文で言及される数値（Task Arithmetic safety+code 等）の差分比較（diff）を行って数値不一致が 0 であることを確認。

### 2. LaTeX コンパイルと見た目の確認
- `flmsec_EN.tex` を LaTeX コンパイル（`pdflatex` / `xelatex` または環境依存コンパイラ）し、エラーなく PDF が出力されることを確認。
- 追加・変更した Table X、Multi-domain 表、Broader Impacts、Asset 表、Checklist のレイアウト崩れがないか確認。

### 3. チェックリストと指示への適合チェック
- ユーザーから指摘された全問題点（1〜8項目および提出前優先順位リスト）が全てクリアされているか、最終確認用チェックリストで照合。
