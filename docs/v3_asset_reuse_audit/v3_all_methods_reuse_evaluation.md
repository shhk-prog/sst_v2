# 全マージ手法における v3 モデル・応答結果（vllm/）再利用可否判定レポート

## 1. エグゼクティブサマリー

| 対象コンポーネント | 再利用可否の結論 | 条件および対応方針 |
|---|---|---|
| **応答結果（`v3/results/vllm/`）** | **全手法で再利用可能**（`RESCORE_ONLY`） | 有害1,053件＋数学640件の生テキストが完全に存在。v4 Evaluator（HarmBench Classifier / 非縮退判定）で**再採点**すれば全生成をスキップ可能。ただしBenign（XSTest 200件）のみ新規補完が必要。 |
| **モデル重み（`v3/models/merged/`）** | **手法により異なる**<br>・Linear: **完全再利用可能**<br>・その他（TIES等）: **E2段階でv4再マージ推奨** | Linear（Task Arithmetic）はPAD削除とマージが数学的に完全可換。非線形・スパース・統計的手法はPAD行がtop-kや統計量に影響するため、重み空間解析（E2）時はv4で再マージが安全。 |

---

## 2. v3 `results/vllm/` に存在する全マージ手法一覧

`v3/results/vllm/debug_limit320/merged/` 配下を精査した結果、以下の **11手法** が存在することを確認した：

1. **`task_arithmetic`** (Linear Safety-Patch)
2. **`ties`** (TIES-Merging: Trimming, Elect Sign, Disjoint Merge)
3. **`dare`** (DARE: Drop And REscale)
4. **`della`** (DELLA: Drop-Early-and-Scale-Low-Rank)
5. **`safemerge`** (SafeMerge: Task Vector Alignment)
6. **`led_merging`** (LED Merging: Layer-wise/direction-based)
7. **`matena_fisher`** (Fisher Weighted Averaging)
8. **`mergealign`** (MergeAlign)
9. **`data_free_sst_main`** (Data-Free Safety Space Transfer)
10. **`diagonal_sst_main`** (Diagonal Fisher SST)
11. **`ablation`** (SST Ablation Variants)

---

## 3. 手法別・再利用可否マトリクス

### 【Math ドメイン (`safety+math`) の場合】（Primary 対象）

| 手法名 | 応答結果 (`vllm/`) | 応答再利用判定 | モデル重み (`models/`) | モデル再利用判定 | 判定理由・技術的背景 |
|---|---|---|---|---|---|
| **`task_arithmetic`** | 完全存在 (全seed, 全alpha) | **RESCORE_ONLY** | 完全存在 | **FULL_REUSE** | 線形演算 $\theta_u + \alpha(\theta_s - \theta_u)$ は要素ごと独立。PAD行削除とマージが完全可換（誤差0）。 |
| **`ties`** | 完全存在 (全seed, 全alpha) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | Top-k トリミングおよびサイン一致判定を含むため、32001行目の存在が閾値選定に微小影響の可能性。 |
| **`dare`** | 完全存在 (全seed, 全alpha) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | ベルヌーイ・ドロップとリスケーリングにおいて、全パラメータ数基準のスケーリング係数に微小影響の可能性。 |
| **`della`** | 完全存在 (全seed, 全alpha) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | DARE同様、大きさに基づくドロップ率選定にPAD行が微小影響の可能性。 |
| **`safemerge`** | 完全存在 (全seed) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | 安全ベクトルとタスクベクトルの射影・コサイン類似度計算に32001行目が微小影響の可能性。 |
| **`led_merging`** | 完全存在 (全seed) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | 層ごとの主成分・直交基底計算（SVD）にPAD行が微小影響の可能性。 |
| **`matena_fisher`** | 完全存在 (全seed) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | Fisher情報量対角成分の正規化・重み付け加重平均の分母に影響の可能性。 |
| **`mergealign`** | 完全存在 (全seed) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | アライメント重みの算出ステップにPAD行が微小影響の可能性。 |
| **`data_free_sst_main`** | 完全存在 (全seed, 全alpha) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | SST安全空間マスクおよび補間処理にPAD行が微小影響の可能性。 |
| **`diagonal_sst_main`** | 完全存在 (全seed, 全alpha) | **RESCORE_ONLY** | 完全存在 | **要差分検証 / 再マージ推奨** | 対角Fisherマスク選定にPAD行が微小影響の可能性。 |

---

## 4. ドメイン別の再利用可否（Code / Medical / 4-Domain）

| ドメイン | 判定 | 理由 |
|---|---|---|
| **`safety+math`** | **Primary 採用** (再利用可) | Base (Llama-2) と WizardMath の RoPE theta (10,000) が一致。PAD行のみの差であり共通32000空間で完全に正当化。 |
| **`safety+code`** | **DIAGNOSTIC_ONLY** (Primary 除外) | WizardCoder の RoPE theta (1,000,000) が Llama-2 (10,000) と根本的に不整合。E0で落とすべき対象。探索・失敗分析用には再利用可能。 |
| **`safety+medical`** | **要E0監査** | MedAlpaca の RoPE/Tokenizer/BOS/EOS 監査を経てから決定。 |
| **4-Domain** | **要E0監査** | WizardCoder を含むため、現状のままでは RoPE 不整合が混入する。 |

---

## 5. 実務的アプローチの推奨

1. **E1（性能比較・パレート最適選定）段階**:
   - **モデル重みをリロードする必要はない**。
   - `v3/results/vllm/` にある全11手法の生レスポンスに対して `rescore_v3_responses.py` を実行するだけで、**全手法の厳格な ASR_valid, VRR, VSR, Utility 比較表が即座に完成**する。
   - 不足している Benign（XSTest 200件）のみ新規生成する。
2. **E2（重み空間解析）・E3（因果介入）段階**:
   - `task_arithmetic`（Linear）は v3 checkpoint をそのまま Canonical 変換して再利用可能。
   - TIES, DARE, DELLA, SST 等の非線形手法については、E2で「重みの差分そのもの」を解析するため、念のため **v4の正規化済み単体モデル（Canonical WizardMath & SafetyFT）からv4スクリプトで再マージ** して比較・検証を行うのが最も科学的かつ安全。
