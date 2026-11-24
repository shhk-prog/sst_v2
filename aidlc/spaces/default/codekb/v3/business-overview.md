# ビジネス概要: v3（SST-Merge / FLMSEC 大規模 merge 調査）

## 目的

v3 は、Safety Tax（安全性と有用性の競合）を扱う研究用の実験環境である。安全性を学習した Safety モデルを、特定ドメインに特化したモデルと merge する「secure merge」の設定で、多数の merge 手法を同じ条件で比較する。対象は次の 2 つ。

- 提案手法 **SST-Merge**（`diagonal_sst`）と、そのデータを使わない近似版 **Data-Free SST-Merge**（`data_free_sst`）
- 比較手法: Task Arithmetic、TIES、DARE、DELLA（mergekit 経由）、SafeMERGE、LED-Merging、MergeAlign（著者実装の呼び出し）、MatEna Fisher / Fisher-weighted averaging（自前実装）

## 研究の位置付け（3 本の論文と SST-Merge）

以下は、承認ゲートで研究者本人から示された位置付けである（コードと論文から読み取れる事実は、その下に分けて書く）。

- **DLSP_hiromi2**（`論文/DLSP_hiromi2/`）は **secure merge の提案論文**である。安全性に特化した「パッチモデル」を FT モデルに merge して、jailbreak 耐性を低コストで高める、という方法を提案している。SAGAI_EN_sst は secure merge の出典としてこの論文（2025 IEEE SPW）を引いている（`論文/SAGAI_EN_sst/main.bib` L51-59、`main.tex` L410）
- **SST-Merge** は、その secure merge に**特化した merge 手法**である。secure merge の枠組み（Safety パッチモデル θ_s とユーティリティモデル θ_u の merge）の中で、どの座標に安全成分を入れるかを FIM の比で選ぶ
- **SAGAI_EN_sst**（`論文/SAGAI_EN_sst/main.tex`）は **SST-Merge の提案論文**である。タイトルは「SST-Merge: Fisher-Ratio Subspace Optimization to Secure Model Merge」（L351）。secure merge を FIM による局所二次近似の下での制約付き最適化として定式化し、一般化固有値問題に帰着させ、実用版として対角近似の SST と Data-Free SST を導く（L396-401, L476-773）
- **FLMSEC 論文**（`論文/FLMSEC/`、NeurIPS 2026 形式）は**大規模評価**の論文である。そのため、提案手法の SST-Merge を**意図的に載せていない**。FLMSEC 論文の主張は「新しい merge 手法」ではなく「validity-aware 評価プロトコル」である。ASR だけでは、本当に安全な応答と、生成が壊れて見かけ上安全になった応答を区別できない、という主張である

コードと論文から読み取れる事実（位置付けを補う設定差）:

- **SAGAI_EN_sst の数値を出した実装は、v3 ではなくリポジトリ外の `v1/`（ワークスペース直下）である**。論文の表の代表セルが v1 の結果ファイルの値と一致することを確かめた（`code-quality-assessment.md` の「論文・v1・v2・v3 の照合」）。v1 は Llama-3.1-8B-Instruct をベースにし、A5 / A6 / A7 の LoRA（r=16）を LoRA の A / B 行列の要素ごとに混ぜ、`merge_and_unload` でフルにして評価する。評価は TrustLLM の分類器の拒否率（JB Res.）と ROUGE-1（RepliQA / Alpaca のスコア）で、各 500 件である。v2 は論文の数値を生んでいない（Llama-2-7B の merge の足場と Llama-3 系の FT ベースライン）。系譜は `architecture.md` の「v1 → v2 → v3 の系譜」
- SAGAI_EN_sst の実験は Llama-3.1-8B をベースにし、ユーティリティ（A5: RepliQA、A6: Alpaca）と Safety（A7: Jailbreak Trigger）をどちらも同じベースに学習した LoRA（r=16）として、アダプターの単位で merge する（`main.tex` L784-797, L1064-1093）。比較手法は Task Arithmetic、TIES、DARE の 3 つ、指標は「JB Res.」と RepliQA / Alpaca のスコアである。SST の主設定は Additive（soft mask）と Interpolation（hard mask、k = 5〜50%）、FIM のサンプル数 500、ε = 10⁻⁶、モジュール種別の層重みである（L1122-1164）
- v3 は Llama-2-7b-hf をベースにし、ユーティリティは外部のフル FT モデル（math / code / medical）、Safety は LoRA（r=16）で、フルの重みで merge する。SST の主設定は Interpolation、hard mask、k=0.20（テンソルごと）、層重みなしで、α を 0〜1 の 0.2 刻みで掃引する。λ と補間の式、ε、サンプル数は SAGAI_EN_sst と同じだが、ベース、ユーティリティモデル、merge の単位、マスクの単位、層重み、α の格子、評価は違う（対応表は `architecture.md` の「論文（SAGAI_EN_sst）とコードの対応表」）
- DLSP_hiromi2 の実験は Mistral-7B（v0.1 / v0.3）をベースにし、merge は mergekit の Linear と Task Arithmetic（重み 0.5 / 0.5）で、パッチモデルは LoRA（r=8）である（`main.tex` L436, L442-456, L949、`tables.tex` L18-32）。SST の手順は書かれていない
- `論文/SAGAI_EN_sst/tables.tex` は `main.tex` から読み込まれず、内容は DLSP_hiromi2 の `tables.tex` と同じである（Mistral の表）
- `results/vllm` には SST-Merge（`diagonal_sst_main`, `data_free_sst_main`）とアブレーションの結果がある。SAGAI_EN_sst の数値は別の実験（v1 の Llama-3.1-8B）のもので、v3 の結果とは対応しない

## 実験の構成（ドメイン用語）

| 用語 | v3 での意味 |
|---|---|
| ベースモデル θ₀ | `meta-llama/Llama-2-7b-hf`（事前学習のみのモデル）。SAGAI_EN_sst と v1 は Llama-3.1-8B-Instruct |
| ドメインモデル θ_u | math: `WizardLMTeam/WizardMath-7B-V1.0`、code: `vanillaOVO/WizardCoder-Python-7B-V1.0`（config.json 上は CodeLlama-Python 系）、medical: `medalpaca/medalpaca-7b`（config.json 上は LLaMA-1 系）。系統の根拠は `technology-stack.md`。SAGAI_EN_sst のユーティリティモデル（θ_util）に当たる |
| Safety モデル θ_s | θ₀ に LoRA（r=16, alpha=32）を学習したもの。TrustLLM JAILBREAK TRIGGER の 1,400 件の有害プロンプトすべてに、同じ拒否文を対応させて学習する。seed 42/43/44 の 3 本。DLSP_hiromi2 の「パッチモデル」、SAGAI_EN_sst の θ_safe（A7）に当たる |
| merge パターン | `safety+math`, `safety+code`, `safety+medical`, `safety+math+code+medical` |
| α | Safety 側の重み。`[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]` をスイープし、FLMSEC 論文の主結果は α=0.6。意味は手法ごとに違う（SST では「マスクされた座標だけでの補間係数」）。SAGAI_EN_sst は α を 0.05〜1.00 で細かく取り、手法を safety–utility 曲線で比べる |
| k | SST のマスクで残す座標の割合。v3 の主設定は 0.20（テンソルごと）。SAGAI_EN_sst と v1 は 5 / 10 / 20 / 50%（v1 は 30 / 40% も。全パラメータでの割合）と soft mask |

## 4 つの評価タスク（セキュリティ 1 ＋ 特化 3）

- **セキュリティ（1 タスク）**: jailbreak 耐性。HarmBench、JailbreakBench、StrongREJECT、WildJailbreak の 4 ベンチマークで、各最大 320 件。指標は ASR と、validity-aware 指標（Conditional ASR、VRR、VSR）
- **特化性能（3 タスク）**: Math（GSM8K、Minerva Math500）、Code（HumanEval、MBPP）、Medical（PubMedQA、MedQA 4 択）。各ドメインは構成ベンチマークの単純平均
- 補助指標: General（MMLU、IFEval、AlpacaEval2）、PPL（Evol-Instruct-Code、MedAlpaca）

採点の詳細は `architecture.md` の Interaction Diagrams と `api-documentation.md` を参照。

## 主要な機能

1. Safety LoRA の学習（`scripts/fine_tuning.py`）
2. merge の実行（`scripts/merge.py`。一括実行は `scripts/run_experiments.py`（SST を含む全手法）と `scripts/run_mergekit_parallel.py`（mergekit 系のみ））
3. 安全性評価と有用性評価（`scripts/eval/`。merge 済みモデルの一括評価は `scripts/merge_eval_parallel.py`）
4. 結果の集計と論文表の生成（`scripts/analysis/`、FLMSEC 表は `generate_flmsec_hyo.py` が中心）。本インテントで使う表の再生成は、今後 `v5/` に新しく実装し、出力も `v5/` に置く予定（`code-quality-assessment.md` の技術的負債 1）

## 本インテントとの関係

本インテント（survey-summary）は、`results/vllm` の既存結果から secure merge に適した要素を抜き出し、SST-Merge が他手法と差を出せなかった理由を考察する。SST-Merge の仕様（SAGAI_EN_sst）、論文とコードの対応表、論文の結果の読み取りは `architecture.md` の「SST-Merge の詳細」に、仮説 (a)〜(d) の判定と、SAGAI_EN_sst の主張を v3 で再現できるかの判定は `code-quality-assessment.md` の「本インテントに影響する所見」に、論文・v1・v2・v3 の 4 者の照合と代表セルの数値照合は同ファイルの「論文・v1・v2・v3 の照合」にまとめた。
