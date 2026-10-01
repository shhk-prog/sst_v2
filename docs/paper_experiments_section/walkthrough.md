# [Walkthrough] SST-Merge 論文 第5章「実験 (Experiments)」執筆と整理の記録

ユーザーから依頼のあった「5. Experiments」草稿に基づき、リポジトリ `/mnt/nas/home/hiromi/src/sst_v2/v3/scripts` の実験・評価設定と完全に紐づけた学術論文品質の日本語「第5章 実験 (Experiments)」ドキュメントを作成・更新しました。

## 変更点・作成物一覧

### ドキュメントフォルダ: [paper_experiments_section](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section)

1. **[task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section/task.md)**
   - フェーズ1・フェーズ2の全タスクおよび完了状態を記録。
2. **[implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section/implementation_plan.md)**
   - 本執筆作業の計画・設計ドキュメント。
3. **[experiments_section.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section/experiments_section.md)**
   - 論文の第5章「5. Experiments」および第6章「6. Analysis and Ablations」の完全版学術テキスト（詳細4指標、2区分Safety Ave, Pareto AUC, TrustLLM/BeaverTails位置づけ反映済み）。

---

## 主な記述ポイントとリポジトリ実証データとの整合

### フェーズ 1: 基本構成の構築
- **5.1 Research Questions (RQ1 ~ RQ5)**:
  - Pareto Frontier (RQ1), Data-free Setting (RQ2), Granularity (RQ3), Efficiency (RQ4), Robustness (RQ5) の 5 つの研究質問を定義。
- **5.2 Detailed Experimental Design & Setup**:
  - Target Models (`Llama-2-7b-hf`, `WizardMath-7B`, `WizardCoder-Python-7B`, `medalpaca-7b`, `safety_lora`)
  - Fisher Datasets (`fim_harmful.json`, `fim_benign_*.json`, $N=500, \epsilon=10^{-6}$)
  - Baselines (Standard 4種: `task_arithmetic`, `ties`, `dare`, `della` / Safety-Preserving 4種: `mergealign`, `safemerge`, `led_merging`, `matena_fisher`)

### フェーズ 2: 指標精密化および質問対応の追記
- **JailbreakBench / StrongReject / WildJailbreak の詳細 4 指標の導入**:
  1. `Original ASR (%)` (排除前 ASR)
  2. `Filtered ASR (%)` (排除後 ASR)
  3. `Gibberish N` (推論崩壊排除数)
  4. `Gibberish Filter Ratio (%)` (排除率)
- **Safety Ave の 2 区分分離表示**:
  1. `Safety Ave [Refusal-Filtered] (ASR↓ %)`: 拒否・無害化表現を含むか（Filtered ASR ベース 4 タスク平均）
  2. `Safety Ave [Harmful Content] (ASR↓ %)`: 明確な有害情報が含まれるか（HarmBench 統一基準 4 タスク平均）
- **Pareto AUC の定量的数値化**:
  - `Diagonal SST`: AUC **0.945** (最高精度)
  - `Data-Free SST-V`: AUC **0.912** (FIM-SST の 96% 以上の性能をデータフリーで達成)
- **`TrustLLM` / `BeaverTails` の利用位置づけの明記**:
  - **TrustLLM**: 予備実験 (Preliminary Validation) において、Jailbreak 耐性の自動判定プロトコルとして **Longformer 分類器 `LibrAI/longformer-harmful-ro` を用いた拒否応答率 (RtA: Refusal to Answer) の測定**に活用。
  - **BeaverTails**: 予備実験での 500 サンプル有害プロンプトセットとして使用。
  - 本実験ではこれらのプロトコル・知見を基盤とし、`HarmBench`, `JailbreakBench`, `StrongReject`, `WildJailbreak`, `XSTest` へと拡張・昇華。

---

## 今後のおすすめアクション
- 論文全文の執筆・更新時に [experiments_section.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/paper_experiments_section/experiments_section.md) を [AAAI.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/07_paper/AAAI.md) 等のメイン論文稿へ組み込むことが可能です。
