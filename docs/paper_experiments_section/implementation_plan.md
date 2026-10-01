# [Implementation Plan] SST-Merge 論文 第5章「実験 (Experiments)」完全整理と学術稿構築

本計画書は、提示された実験草案（RQ1〜RQ5、評価ベンチマーク、ハイパーパラメータ、ベースライン等）に基づき、`/mnt/nas/home/hiromi/src/sst_v2/v3/scripts` の実験環境および実証データと完全に適合する形で、トップ国際会議（AAAI / NeurIPS 等）に提出可能なレベルの「第5章 実験 (Experiments)」を日本語で精緻に体系化・ドキュメント化することを目的とします。

## User Review Required

- 本ドキュメント作成にあたり、`/mnt/nas/home/hiromi/src/sst_v2/v3/configs/config_main.yaml` および `/mnt/nas/home/hiromi/src/sst_v2/v3/scripts` にて定義されたモデル構造、ハイパーパラメータ（$k=0.20, \epsilon=10^{-6}, \alpha \in [0.0..1.0]$）、評価データセット（$N=500, limit=320$）、ベースライン（Standard 4種 + Safety 4種）との完全な整合性を保持します。
- 作成されるファイル群はプロジェクトの規約に沿って `docs/paper_experiments_section/` ディレクトリ内に配置し、過去の作業履歴が把握できるように保存します。

## Open Questions

特に追加の疑問点はありません。提示された草案の5つの研究質問（RQ1〜RQ5）および `v3/scripts` 内の実装仕様に基づいて網羅的かつ精緻な実験章を構築します。

## Proposed Changes

### ドキュメント構造とファイル構成

#### [NEW] [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section/task.md)
タスクリストおよび進捗管理ドキュメント。

#### [NEW] [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section/implementation_plan.md)
本計画書のプロジェクト内永続化ファイル。

#### [NEW] [experiments_section.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section/experiments_section.md)
論文第5章「5. Experiments」および第6章「6. Analysis and Ablation」を統合・洗練させた完全版学術稿ドキュメント。

---

### 追加改訂内容 (Phase 2)
1. **安全性詳細 4 指標の追加**: `Original ASR (%)`, `Filtered ASR (%)`, `Gibberish N`, `Gibberish Filter Ratio (%)`
2. **Safety Ave の 2 区分分離表示**: `Safety Ave [Refusal-Filtered] (ASR↓ %)` と `Safety Ave [Harmful Content] (ASR↓ %)`
3. **Pareto AUC の定量的数値化**: SST-Merge (0.945), Data-Free SST-V (0.912)
4. **TrustLLM / BeaverTails の利用位置づけの解説**: 予備実験 (Preliminary Evaluation) における `TrustLLM` 評価プロトコル（Longformer 分類器 `LibrAI/longformer-harmful-ro` による RtA 測定）および `BeaverTails` 500 件データセットの役割の補足。

---

### 第5章「5. Experiments」および「6. Analysis and Ablations」の構成案

1. **5.1 Research Questions (RQ1 ~ RQ5)**
   - RQ1: Pareto Frontier & Safety-Utility Trade-off
   - RQ2: Data-free Setting (Data-Free SST-V vs FIM-SST vs SST-M)
   - RQ3: Granularity of Subspace Selection (Element-wise vs Layer-wise)
   - RQ4: Computational & Memory Efficiency
   - RQ5: Sensitivity & Robustness ($k$, $\alpha$, Random Seeds)

2. **5.2 Detailed Experimental Setup & Protocol**
   - **Target Models**: Base (`Llama-2-7b-hf`), Utility Domain Models (`WizardMath-7B-V1.0`, `WizardCoder-Python-7B-V1.0`, `medalpaca-7b`), Safety Model (`models/safety_lora`)
   - **Fisher Calibration Datasets**: Harmful (`fim_harmful.json`), Benign (`fim_benign_math.json`, `fim_benign_code.json`, `fim_benign_medical.json`), Sample size $N=500$, Epsilon $\epsilon=10^{-6}$
   - **Evaluation Benchmarks & Metrics**:
     - Safety: HarmBench, JailbreakBench, StrongReject, WildJailbreak, Over-refusal (XSTest) + TrustLLM / BeaverTails (予備実験)
     - Metrics: Detailed 4 Metrics (Original ASR, Filtered ASR, Gibberish N, Gibberish Filter Ratio) & 2-way Safety Ave (Refusal-Filtered vs Harmful Content)
     - Utility: Math (GSM8K, Minerva Math500), Code (HumanEval, MBPP), Medical (PubMedQA, MedQA 4-options), General (MMLU, IFEval)
   - **Evaluation Protocol**: `diagonal_sst` (Interpolation, Hard mask, $k=0.20$), Alpha Sweep ($\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$), Seeds ($42, 43, 44$), 4 Merge Patterns (`safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical`)
   - **Baselines**:
     - Standard: `task_arithmetic`, `ties`, `dare`, `della`
     - Safety-Preserving / Fisher: `mergealign`, `safemerge`, `led_merging`, `matena_fisher`

3. **5.3 Preliminary & Main Benchmark Results**
   - GSM8K vs HarmBench / Safety Ave の定量的比較結果テーブル (詳細 4 指標付き)
   - アライメント発現の閾値効果（Criticality Threshold Transition at $\alpha=0.8$）の理論的・実験的分析
   - 他手法でのPerplexity発散・リピート崩壊モード（Failure Mode）の回避現象と Pareto AUC 分析

4. **5.4 Detailed Ablation & Analytical Studies (RQs 2-5)**
   - Granularity (Element-wise vs Layer-wise) の解像度評価
   - Data-free Proxies (`SST-V`, `SST-M`) の近似精度と効果 (Pareto AUC 0.912)
   - 計算効率とメモリ overhead の比較
   - ハイパーパラメータ $k$ および $\alpha$ の感度分析

## Verification Plan

### Automated Verification
- 作成されたドキュメントの構文およびリンク構造の検証。
- リポジトリ内設定ファイル (`v3/configs/config_main.yaml`) との数値・名称の整合性確認。

### Manual Verification
- 提示された全研究質問（RQ1〜RQ5）および全セットアップ項目（モデル、データセット、指標、ハイパーパラメータ、ベースライン）が漏れなく網羅され、学術表現として洗練されているか確認。
