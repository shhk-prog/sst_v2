# 開発者コードスキャン: v3（改訂版 — SST-Merge の詳細検証）

- リポジトリ: `v3`（プロジェクトルート `/mnt/nas/home/hiromi/src/sst_v2` からの相対パス `v3/`）
- 実施種別: 承認ゲートでの差し戻しを受けた改訂（REVISION）。既存の CURRENT ストア（`kind: partial`）に統合する FOCUSED スキャン
- 深さ: Minimal。ただし SST-Merge の検証だけは詳細に行った
- スナップショット head_commit: `4959ba3151ceb574b63e202bd66a0a2317afb53b`
- 実施日: 2026-11-23。プロジェクトのテスト、ビルド、プログラムは一切実行していない（読むだけ）。重み、`.pt`、blob は開いていない

## Developer Code Scan Results

### Scan Coverage
- **Analyzed deeply**（今回の実行で精読したもの。前回の精読範囲は統合後のストアに残す）:
  - `scripts/mergers/`（`sst.py`, `fim.py`, `utils.py`, `constants.py`, `__init__.py`, `mergekit.py` を行単位で再読）
  - `scripts/merge.py`
  - `scripts/merge_eval_parallel.py`
  - `scripts/run_mergekit_parallel.py`
  - `scripts/data_prep.py`
  - `configs/`（`config_main.yaml`, `config_main2.yaml`, `config_ablation.yaml`, `config_ablation2.yaml`, `config_ablation_n500_tmp.yaml`）
  - `scripts/fine_tuning.py`（LoRA 設定と学習テキストの形式を再確認）
  - `README.md`（§3 提案手法、§4 アブレーション仕様）
  - `論文/DLSP_hiromi2/main.tex`, `論文/DLSP_hiromi2/tables.tex`
- **Skimmed only**:
  - `scripts/run_experiments.py`（SST の merge コマンドが `--k` などを明示して `merge.py` を呼ぶことだけを grep で確認。L475-523）
  - Hugging Face キャッシュの `config.json` 4 件（リポジトリ外。`~/.cache/huggingface/hub/models--{meta-llama--Llama-2-7b-hf, WizardLMTeam--WizardMath-7B-V1.0, vanillaOVO--WizardCoder-Python-7B-V1.0, medalpaca--medalpaca-7b}/snapshots/*/config.json`）。ブリーフが許可した小さな設定ファイルだけを読み、重みは開いていない
- **Left out**:
  - `baselines/`（第三者 merge ライブラリ。ブリーフの指示で未オープン。mergekit の `linear` の挙動は外部仕様として記載し、コードでは確認していない）
  - `models/`（重み）、`cache/`（FIM テンソル）、`data/`、`logs/`、`venv_*`（ブリーフの指示）
  - `__pycache__/`、`._*` と `.DS_Store`（macOS 生成物）
  - `.claude/`, `aidlc/`（AI-DLC の導入物。読み書きしたのは codekb とこのハンドオフだけ）

### Packages Found
- `scripts/mergers` — Python パッケージ — Python — SST-Merge 本体（`sst.py`）、対角 FIM（`fim.py`）、mergekit / 外部実装ラッパー
- `scripts`（トップレベル） — CLI 群 — Python — `merge.py`（単一 merge）、`merge_eval_parallel.py`（merge 済みモデルの並列評価）、`run_mergekit_parallel.py`（mergekit 系の並列 merge）、`data_prep.py`（FIM / 評価データ作成）

### Build System
- **Type**: なし（素の Python スクリプト。pip + venv）
- **Config Files**: `requirements.txt`, `configs/*.yaml`
- **Build Dependencies**: `merge.py` → `mergers`（`sst` → `fim`, `utils`）。`run_experiments.py`（SHALLOW）と `run_mergekit_parallel.py` が `merge.py` をサブプロセスで起動する。`merge_eval_parallel.py` は merge を行わず、`merge_metadata.json` が `success` のモデルを集めて `eval/*.py` を起動する（`merge_eval_parallel.py` L288-335, L977）

### APIs Discovered
- CLI — `scripts/merge.py` — SST 関連の引数 10 種（`--alpha`, `--k`, `--sample_size`, `--sst_ratio`, `--variant`, `--mask_type`, `--layer_wise`, `--layer_prior`, `--norm_standardization`, `--fisher_normalization` ほか）。省略時は config の `merge.main` を読む（`merge.py` L121-148）
- Python 関数 — `merge_sst(...)`（`sst.py` L8-202）、`estimate_fim(...)`（`fim.py` L10-72）、`load_or_estimate_fim(...)`（`fim.py` L95-155）、`get_fim_tensor(...)`（`fim.py` L158-161）、`run_mergekit(...)`（`mergekit.py` L10-66）

### Frameworks & Libraries
- torch — 勾配計算、テンソル演算（merge は fp16）
- transformers — `AutoModelForCausalLM`（fp16 読み込み）
- peft — Safety LoRA の `merge_and_unload`
- mergekit — 比較手法（`task_arithmetic` は `linear` に写像。`constants.py` L16-21）

### Test Coverage
- **Test Directories**: `scripts/tests/`（前回から変更なし）
- **Test Frameworks**: unittest、自作統合スクリプト
- **Coverage Config**: absent。SST の数値（マスク比率、λ の分布）を検証するテストはない

### Code Quality Indicators
- **Linting**: なし
- **CI/CD**: なし
- **Documentation**: README が SST の式（λ、interpolation、additive、hard mask）を記載。マスクがテンソル単位であることと w の定義は README にない。DLSP_hiromi2 には SST の記載がない

### Technical Debt Signals
- `merge.py` L125: config の `merge.main.k_values` が空のとき `--k` を省略すると IndexError になる（アブレーション設定は空。`config_ablation.yaml` L66）
- `sst.py` L146 / L171: `random` の λ は `torch.rand_like` だが、merge の経路に乱数 seed の固定がない（`merge.py`, `mergers/` に `manual_seed` がない）
- `config_main.yaml` L26 の `epsilon: 1e-6` は使われない（`sst.py` L84, L138 などで 1e-6 を直書き）
- `utils.py` L64-71: FIM キャッシュ名が全ドメインを `Llama2_*` と命名する（medalpaca は LLaMA-1 系）
- `merge.py` L622-633: merge 済みモデルは常にベースモデルの config とトークナイザで保存される
- `sst.py` L74-101: `fisher_weighted` の分岐が対象判定（L103）より前にあり、FIM にない名前（RMSNorm の weight など）は `get_fim_tensor` が 0 を返す（`fim.py` L159-160）ため、merge 後の値が 0 になる（`config_main2.yaml` L65 で使われる）

## SST-Merge 検証の要点

### アルゴリズム（主設定、コードから復元）
1. 入力: θ₀ = `meta-llama/Llama-2-7b-hf`（fp16、`merge.py` L510-514）。θ_s = θ₀ に Safety LoRA（seed 42/43/44）を `merge_and_unload`（fp16、L518-527）。θ_u,j = パターンの各ドメインモデル（fp16、L533-542）。トークナイザはベースのもの（L505）
2. FIM: F_b,j は θ_u,j と `data/fim/fim_benign_{j}.json` の先頭 500 件、F_h は θ_s と `data/fim/fim_harmful.json` の先頭 500 件（`fim.py` L31、シャッフルなし）。各サンプルは `<s>[INST] p [/INST] r</s>`（L45）、最大 2048 トークン（L47-52）、ラベルは全トークン（L54。プロンプトも損失に含む）。fp16 モデルで `backward`（L55-56。loss scaling も autocast もない）、`grad.float()**2` を CPU の fp32 に累積（L21, L61）し、件数で割る（L69-70）。対象は 7 種の proj の weight だけ（L18-21）。経験的対角 Fisher である
3. 正規化: 主設定ではなし（`fisher_normalization` は off。`sst.py` L129-135 はテンソル平均での正規化）
4. merge 時に F を θ₀ の dtype（fp16）へキャスト（`fim.py` L161）。F̄_b = mean_j F_b,j（`sst.py` L119-125）
5. λ = F_h / (F̄_b + 1e-6)（`sst.py` L137-138）。ε は直書き
6. hard mask: テンソルごとに k_elements = max(1, int(numel·k)) を取り、k 番目に大きい λ を閾値として mask = (λ ≥ 閾値)（`sst.py` L177-181）。同値の座標はすべて 1 になる
7. interpolation: w = clamp(α·w_layer·mask, 0, 1)、θ = (1−w)·θ̄_u + w·θ_s（`sst.py` L190-192）。mask=1 では θ₀ + (1−α)δ̄_u + αδ_s、mask=0 では θ₀ + δ̄_u
8. 対象外のパラメータ（norm など）: θ̄_u + α·δ_s（`sst.py` L103-105）。δ_s は LoRA の対象外なので 0
9. 形状が違うテンソル（語彙 32001 の embed / lm_head）: utility の差分を捨て、θ₀ をそのまま使う（`sst.py` L50-55）
10. 保存: 新しく読み込んだベースモデルに `load_state_dict(strict=False)` し、ベースの config とトークナイザで保存（`merge.py` L622-633）

### ハイパーパラメータ
| 項目 | 主設定 | アブレーション | 根拠 |
|---|---|---|---|
| k | 0.20 | `config_ablation.yaml`: 0.20 のみ。`config_ablation2.yaml`: 0.01, 0.05, 0.10, 0.20 | `config_main.yaml` L74, `config_ablation.yaml` L77, `config_ablation2.yaml` L77 |
| FIM n | 500 | {50, 100, 500}（`config_ablation2.yaml` は 250 も） | `config_main.yaml` L75, `config_ablation.yaml` L78, `config_ablation2.yaml` L78 |
| sst_ratio | `Fh/Fb` | `Fh/Fb`, `Fh only`, `1/Fb only`, `magnitude`, `random` | `config_ablation.yaml` L80-85 |
| variant | interpolation | additive, interpolation | `config_ablation.yaml` L87-89 |
| mask | hard mask | hard mask のみ（soft はコメントアウト） | `config_ablation.yaml` L91-93 |
| layer_wise / prior | false / uniform | true（uniform, sin, linear, exp）/ false | `config_ablation.yaml` L95-103 |
| α | 0.0〜1.0（0.2 刻み） | 同じ | `config_main.yaml` L71 |
| ε | 1e-6（直書き） | 同じ | `sst.py` L138 |
| 掃引方式 | — | 1 因子ずつ（2 軸以上を変えた条件は飛ばす） | `merge_eval_parallel.py` L219-228 |

### 仮説の判定（読める範囲）
- (a) SST = 上位 20% 座標に限定した task_arithmetic → **コードで確認**（対象モジュールでは厳密に成立。差は対象外パラメータと embed / lm_head の扱いだけ）。「同じ α で注入する安全成分が少ない」も構造的に確認。ASR への影響は未検証（要データ）
- (b) fp16 FIM のアンダーフローでマスクが全 1 になる → **機構はコードで確認、発生の有無は未検証（要データ）**。FIM の二乗と累積は fp32（`fim.py` L21, L61）なので二乗の段階では落ちない。落ちうるのは (i) fp16 の逆伝播での勾配そのもの（L55-56）、(ii) merge 時の fp16 キャスト（L161）。全 1 になる条件は「テンソル内で λ>0 の座標が k=20% 未満」（`sst.py` L179-181 の `>=`）
- (c) F_h と F_b の推定条件の不一致 → **コードで確認**（別モデル、別データ、F_h は θ_s の学習データそのもの、正規化なし、多ドメインでは F_b だけ平均）。λ への影響の大きさは未検証（要データ）
- (d) code / medical モデルが Llama-2-7b-hf 派生でない → **config.json で確認**。WizardCoder-Python は `_name_or_path` が `.../7Bcodellamapython_v1_...`、`rope_theta: 1000000`、`max_position_embeddings: 16384`（CodeLlama-Python 系）。medalpaca は `_name_or_path: ../llama-7b-hf/`、`rms_norm_eps: 1e-06`、`transformers_version: 4.28.0.dev0`（LLaMA-1 系）。WizardMath は config からは判定できない（`_name_or_path: /model_weights/`）。3 モデルとも `vocab_size: 32001`（ベースは 32000）

## Handoff Summary
- **Intent-relevant finding**: SST の主設定は、対象 7 モジュールの各テンソルで λ の上位 20% の座標だけに θ = (1−α)θ̄_u + αθ_s を適用し、残りは θ̄_u のまま残す（`scripts/mergers/sst.py` L177-192）。task_arithmetic（mergekit `linear`、safety の重み α、`scripts/mergers/mergekit.py` L28、`constants.py` L19）を座標の部分集合に制限したものに等しく、同じ α では安全成分が少ない。加えて、code（CodeLlama 系）と medical（LLaMA-1 系）は Llama-2-7b-hf からの直接の派生ではない（各 `config.json`）。そのため θ_u−θ₀ はタスクベクトルではなく、20% の座標で LLaMA-1 / CodeLlama の重みと Llama-2+LoRA の重みが混ざる。DLSP_hiromi2 は secure merge の提案論文だが、SST のアルゴリズム（FIM、λ、マスク）は記載されていない。SST の仕様の出典は README §3-4 とコードだけである
- **Risks / follow-up**: 数値の確認は後続段階で行う（`code-quality-assessment.md` の「後続段階で要検証」V1〜V9）。特に V1/V2（`cache/fim/*.pt` を fp16 にキャストしたときの 0 の割合と、実際のマスク比率）、V7（merge 済み code モデルの `config.json` の `rope_theta`）。表再生成スクリプトは今後 `v5/` に新規実装し、出力も `v5/` に置く（今回は作成していない）
