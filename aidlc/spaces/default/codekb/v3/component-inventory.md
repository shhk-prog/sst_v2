# コンポーネント一覧: v3

見出しはコンポーネント名である（`reverse-engineering-timestamp.md` の Scope of Analysis と一致させている）。ファイルの配置は `code-structure.md` を参照。v1 / v2 のコンポーネントはリポジトリ外（ワークスペース直下）のもので、読んだ範囲だけを「リポジトリ外（v1 / v2）」の節に書いた。

## 精読したコンポーネント

### mergers-sst
- **場所**: `scripts/mergers/sst.py`（`merge_sst`、L8-202）
- **責務**: SST-Merge（`diagonal_sst`）、Data-Free SST（`data_free_sst`）、Fisher-weighted averaging（`fisher_weighted`）の座標ごとの merge
- **仕様の出典**: SST-Merge の提案論文 `sagai-sst-paper`（`論文/SAGAI_EN_sst/main.tex`）。λ、hard / soft mask、additive、interpolation、Data-Free の式は論文と一致する。マスクの単位（テンソルごと）、層重み（層番号の関数）、`lm_head` の扱いは論文と違う（`architecture.md` の対応表）。論文の数値を出した実装は v1（`v1-sst-core`）で、そちらは論文と同じグローバル top-k とモジュール種別の層重みを持つ
- **入力**: θ₀（`base_model`）、θ_u,j の辞書（`util_models_dict`）、θ_s（`safe_model`）、F_b,j の辞書（`fim_b_dict`）、F_h（`fim_h`）、ハイパーパラメータ（`sst_ratio`, `variant`, `mask_type`, `layer_wise`, `layer_prior`, `alpha`, `k_ratio`、拡張 3 種）
- **出力**: `(merged_state_dict, fisher_weight_stats)`。後者は `fisher_weighted` のときだけ中身がある。マスク比率は記録しない
- **アルゴリズム（主設定: `Fh/Fb`, interpolation, hard mask, k=0.20, layer_wise なし）**:
  - パラメータ名ごとに処理する（L33）。θ_s にない名前は θ₀（L36-38）
  - δ_s = θ_s − θ₀（形状が違えば 0、L40-42）。δ_u,j は形状が同じモデルだけ（L44-51）。1 つもなければ θ₀（L53-55）。語彙 32001 のドメインモデルでは embed / lm_head がこれに当たる
  - δ̄_u = mean_j δ_u,j、θ̄_u = θ₀ + δ̄_u（L71-72）
  - 対象外のパラメータ（norm など）: θ̄_u + α·δ_s（L103-105）。δ_s は 0 なので実質 θ̄_u
  - 対象モジュール（7 種の proj の weight）: F̄_b = mean_j F_b,j、λ = F_h / (F̄_b + 1e-6)（L119-138）。テンソルごとに k_elements = max(1, ⌊numel·k⌋)、閾値 = k 番目に大きい λ、mask = (λ ≥ 閾値)（L177-181）
  - `soft mask`: σ(log(λ + 1e-8)/τ)、τ = k（L182-184）。v3 の設定では使われない
  - `interpolation`: w = clamp(α·w_layer·mask, 0, 1)、θ = (1−w)·θ̄_u + w·θ_s（L190-192）。mask=1 では θ₀ + (1−α)δ̄_u + αδ_s、mask=0 では θ̄_u
  - `additive`: θ = θ̄_u + α·w_layer·mask·δ_s（L188-189）
  - `fisher_weighted`: θ = (F̄_b·θ̄_u + F_h·θ_s) / (F̄_b + F_h + 1e-6)（L74-101）。この分岐は対象判定（L103）より前にあるため、対象外のパラメータ（RMSNorm の weight など）にも適用される。対象外の名前は FIM にないので `get_fim_tensor` が 0 を返し（`fim.py` L159-160）、重みが 0/1e-6 = 0 になって、merge 後の値は 0 になる（コードで確認。`fisher_weighted` の結果を使う場合は要注意。FLMSEC の FWA がどちらの実装かは未確認）
- **重要度の代替（アブレーション）**: `Fh only` = F_h、`1/Fb only` = 1/(F̄_b+1e-6)、`magnitude` = |δ_s|、`random` = 一様乱数（L139-146）。Data-Free では F_h → δ_s²、F̄_b → mean_j δ_u,j²（L150-163）。Data-Free の `Fh only`（δ_s²）と `magnitude`（|δ_s|）は順位が同じなので、同値の扱いを除き同じマスクになる。論文に出てくる重要度は `Fh/Fb` だけで、ほかの 4 種はコード側のアブレーションである
- **依存**: `mergers-fim`（`get_fim_tensor`）、`mergers-utils`（`is_target_weight`, `get_layer_prior`）
- **数値の注記**: 演算はすべて θ₀ の dtype（fp16）で行う。F も fp16 にキャストされる（`fim.py` L161）。fp16 の正規化数の最小値は約 6.1e-5、非正規化数の最小値は約 6e-8、最大値は 65504 である。λ の分母 F̄_b が 0 に落ちると λ = F_h × 約 1e6 になり、F_h が約 0.065 を超えると inf になる。`random` は乱数 seed を固定しない（merge の経路に `manual_seed` がない）。論文は数値精度を書いていない
- **詳細**: アルゴリズムの全体、ハイパーパラメータ表、論文との対応表は `architecture.md` の「SST-Merge の詳細」

### mergers-fim
- **場所**: `scripts/mergers/fim.py`（`estimate_fim` L10-72、`build_fim_cache_path` L75-92、`load_or_estimate_fim` L95-155、`get_fim_tensor` L158-161）
- **責務**: 経験的対角 FIM の推定と、`cache/fim/{kind}_{domain}_{model_short}_n{N}_seed{S}.pt` へのキャッシュ
- **推定の手順**: `model.eval()`（L14）。対象パラメータだけ fp32 の CPU テンソルを用意（L18-21）。データの先頭 `sample_size` 件（L31）を 1 件ずつ `<s>[INST] p [/INST] r</s>`（L45）にし、最大 2048 トークンで切る（L47-52）。ラベルは入力全体（L54）。fp16 モデルで `loss.backward()`（L55-56）し、`grad.float()**2` を累積（L61）、件数で割る（L69-70）
- **入力**: F_b は各 utility モデルと `data/fim/fim_benign_{math,code,medical}.json`（GSM8K / Evol-Instruct-Code / medical_meadow_medical_flashcards）。F_h は Safety モデルと `data/fim/fim_harmful.json`（Safety SFT と同じ `response_dataframe.csv` 由来）
- **論文との差**: SAGAI_EN_sst は F_t を θ_util の近傍で定義する（`main.tex` L522-529）。コードは F_h を Safety モデルで推定する（`merge.py` L572-583）が、v1 の原実装も F_h を Safety LoRA を載せたモデルで推定しており、v1 からの引き継ぎである。F_b のデータは論文ではユーティリティモデル自身の学習データ（RepliQA、L792-797）。v1 の FIM は勾配の分散で、v3 の経験的 Fisher（勾配二乗の平均）とは定義が違う
- **キャッシュの注記**: キー（L87-90）はデータの種類、ドメイン、モデル短縮名、n、seed だけで、データの中身や入力形式を含まない。F_b はドメインモデルが seed に依存しないのに seed ごとに推定される。モデル短縮名はドメインに関係なく `Llama2_*`（`utils.py` L58-73）
- **依存**: torch、`mergers-utils`

### mergers-mergekit
- **場所**: `scripts/mergers/mergekit.py`（`run_mergekit` L10-66）、写像は `scripts/mergers/constants.py` L16-21 の `MERGEKIT_METHOD_MAP`
- **責務**: mergekit YAML を生成し、サブプロセスで実行する
- **写像**: `task_arithmetic` → `linear`、`ties` → `ties`、`dare` → `dare_ties`、`della` → `della`
- **重み**: safety = α、各 utility = (1−α)/n（L28）。density は ties / dare / della で 0.5、linear で 1.0（L29）。ties と dare は `normalize: True`（L40-47）、della は `epsilon 0.05, lambda 1.0`（L48-49）。`dtype: float16`（L36）。`--allow-crimes --copy-tokenizer`（L56）
- **SST との関係**: `linear` の source に θ₀ は含まれない。形状が同じテンソルでは θ₀ + (1−α)δ̄_u + αδ_s になり、SST の mask=1 の座標と同じ式になる（`architecture.md` の「α の意味」）
- **論文との差**: SAGAI_EN_sst の TA（θ_base + αΔ_s + (1−α)Δ_u、`main.tex` L982）とは同じ。DARE は論文では drop rate 0.9 で Safety の τ_s だけを疎にする（L1109-1120）が、コードは density 0.5 の `dare_ties` で両方のベクトルを扱う。v1 の DARE も両方のアダプターを疎にする（`v1-baseline-merge`）

### mergers-baselines
- **場所**: `scripts/mergers/baselines.py`
- **責務**: SafeMERGE、LED-Merging、MergeAlign の著者実装をサブプロセスで呼ぶ。MatEna Fisher は `scripts/merging/matena_fisher.py` を呼ぶ（fp32、FIM を L2 正規化する対称な Fisher 平均）
- **固定パラメータ**: LED は `top_merging`, scaling 0.9, fuse_rates 0.5/0.5。MergeAlign は temp 1.0, max_per_task 100, `data/response_dataframe.csv`。SafeMERGE は SafeLoRA の aligned / unaligned として θ₀ と θ_s を渡す
- **制約**: いずれも単一ドメインのパターンだけに対応。LED は math と code だけ

### mergers-utils
- **場所**: `scripts/mergers/utils.py`, `scripts/mergers/constants.py`, `scripts/mergers/__init__.py`
- **責務**: モデル読み込み、パターンからモデル集合を作る（`build_models_to_merge` L116-139）、Safety LoRA を full モデルに展開する（`create_full_safety_model` L179-232）、full モデルを rank-16 の疑似 LoRA に SVD 変換する（`convert_full_to_lora` L235-317、SafeMERGE 用）、層 prior（`get_layer_prior` L84-101。層番号 x を [0, 1] に正規化し、`uniform` は常に 1.0、`sin` は 1+0.5·sin(πx)、`linear` は 0.5+x、`reverse_linear` は 1.5−x、`exp` は exp(x−0.5)）、対象判定（`is_target_weight` L76-77）、定数（対象 7 モジュール、手法の 4 グループ、`FIM_REQUIRED_METHODS`）
- **論文との差**: SAGAI_EN_sst の層重みはモジュール種別（`lm_head` 1.5、`q/k/v/o_proj` 1.2、`gate/up/down_proj` 0.8、`main.tex` L1149-1164）で、`get_layer_prior` のどのモードとも違う。対象 7 モジュールに `lm_head` は含まれない（`constants.py` L6-14）。モジュール種別の重みは v1 に実装がある

### merge-cli
- **場所**: `scripts/merge.py`
- **責務**: 引数と設定の解決（`apply_config_defaults` L121-148）、手法ごとの分岐（`execute_merge` L344-718）、FIM の取得（L544-584）、`merge_sst` の呼び出し（L599-617）、保存（L622-633）、メタデータ・計算量・実行時間の記録
- **SST の経路**: ベース、Safety（LoRA を merge）、各ドメインモデルをすべて fp16 で同じ GPU に載せる（L510-542）。保存は新しく読み込んだベースモデルへの `load_state_dict(strict=False)` で、config とトークナイザはベースのもの（L622-633）。SAGAI_EN_sst はアダプタ単位で merge する（`main.tex` L1093）が、`merge.py` の SST 経路はフルの重みで merge する
- **注記**: 引数を省略すると config の `merge.main` を読む。`k_values` が空の設定（アブレーション設定）で `--k` を省略すると IndexError になる（L125）。オーケストレータは常に明示的に渡す
- **依存**: `mergers-*`、`steering_hook`

### safety-lora-training
- **場所**: `scripts/fine_tuning.py`
- **責務**: θ₀（Llama-2-7b-hf）に LoRA（r=16, alpha=32, dropout 0.05, 7 モジュール、L156-167）を SFT する。lr 2e-4（L25）、既定 3 epoch（L24）、batch 4×4、fp16、max_length 512（L176-185）。テキストは `<s>[INST] {prompt} [/INST] {response} </s>`（L87-88、プロンプトも損失に含む）
- **論文との差**: SAGAI_EN_sst の A7 は LoRA r=16、alpha=32、dropout 0.05、`all-linear`、5 epoch、lr 2e-4（`main.tex` L1065, L1084）で、epoch 数だけが違う。DLSP_hiromi2 のパッチモデル（LoRA r=8、1,200 件で学習）とも設定が違う。v1 の A7 は同じ LoRA 設定で、epoch の結果が 3 / 5 / 7 / 10 と共存する

### eval-safety
- **場所**: `scripts/eval/eval_safety.py`
- **責務**: 4 ベンチマークでの生成、gibberish 判定（`is_gibberish_or_invalid`）、ベンチ別の分類器での判定、checkpoint 保存、vLLM 出力パスへの振り替え
- **依存**: vllm、transformers、`strong_reject`、HF 分類器モデル。後処理は `scripts/tools/reclassify_safety_with_harmbench.py`（`harmbench_cls_*` の付与）、`scripts/fixes/fix_gibberish_safety_jsons.py`

### eval-utility
- **場所**: `scripts/eval/eval_utility.py`
- **責務**: lm-eval（0-shot、chat template）での有用性評価、コードタスクと IFEval の事後再採点、結果 JSON の保存

### eval-orchestrator
- **場所**: `scripts/merge_eval_parallel.py`
- **責務**: 設定から、あるべき merge 済みモデルの一覧（出力名）を組み立て（L288-335）、`merge_metadata.json` が `success` のものだけを GPU ごとに並列で評価する（L949-977）。**merge 自体は行わない**
- **SST の条件の組み立て**: 主条件は α × `main.k_values`（L189-202）。アブレーションは α × n × k × 比率 × variant × mask × layer_wise × prior から、中心条件から 2 軸以上を変えたものを飛ばす（L205-240、判定は L219-228）。`layer_wise=true` で prior が `uniform` の条件は、`nolayerwise` と数式上同じになる（`utils.py` L90-91）。SAGAI_EN_sst は k × variant × layer-wise の全組み合わせを評価している（表 `tab:res_a5_sst_*`）
- **出力名**: `{experiment}_{method}_{type}_{pattern}_alpha{a}[_n{n}]_k{k}_{ratio}_{variant}_{mask}_{layer}_seed{s}`（L145-179）。結果ディレクトリの手法名は正規表現で取り出す（`diagonal_sst_main` など、L743-763）。アブレーションは `ablation/sst` か `ablation/datafree`（L744-750）
- **その他**: 単一ドメイン専用手法の除外（`should_skip_method_pattern` L78-92）、評価前の `config.json` の語彙サイズ補正（`fix_model_vocab_size_if_needed` L614-719。merge 済みモデルの重みの形状に合わせて書き換える）

### mergekit-orchestrator
- **場所**: `scripts/run_mergekit_parallel.py`
- **責務**: mergekit 系 4 手法だけを（seed × パターン × 手法 × α）で `merge.py` に投げる（L105-127、手法の絞り込みは L108）。共有の `temp_safety_full_seed{N}` を作るため、seed ごとに最初の 1 件を先に実行する（L157-167）

### fim-data-prep
- **場所**: `scripts/data_prep.py`
- **責務**: FIM 用データと評価用データを作る
- **FIM 用データ**: math は GSM8K train の先頭 1,000 件（L21-30）、code は Evol-Instruct-Code-80k の先頭 1,000 件（L40-49）、medical は medical_meadow_medical_flashcards の先頭 1,000 件（L59-71）、harmful は `data/response_dataframe.csv` の全行（L78-92）。FIM の推定はこの先頭 n 件を使う
- **論文との差**: SAGAI_EN_sst の F_h のデータ（Jailbreak Trigger）は同じ。F_b のデータは論文ではユーティリティモデル自身の学習データ（RepliQA）で、コードの公開 benign データとは考え方が違う（`main.tex` L792-797）。v1 は RepliQA / Alpaca から取る
- **注記**: 取得に失敗すると、benign はプレースホルダ（「Solve math problem i」など 500 件）を書く（L31-35, L50-54, L72-76）。評価データも失敗時は 1 件のプレースホルダ、WildJailbreak は BeaverTails にフォールバックする（L145-170）。`data/` の実データは未確認

### flmsec-table-generator
- **場所**: `scripts/analysis/generate_flmsec_hyo.py`（`generate_table1_latex.py`, `generate_latex_tables_custom.py`, `generate_specific_tables.py` がこれを import する）
- **責務**: `results/vllm` 以下の JSON を再帰的に glob し、ファイル名を解析して seed ごとの指標を集め、平均±標準偏差の Markdown / LaTeX 表を `docs/flmsec/flmsec_hyo_vllm{,_latex}.md` に出力する
- **指標の定義**:
  - valid = `not is_gibberish`。有害 = `harmbench_cls_output == "Yes"` または `asr > 0.5`
  - Original ASR = 有害 ∧ valid の件数 / 全件、Conditional ASR = 有害 ∧ valid / valid、VRR = valid / 全件、VSR = (valid − 有害 ∧ valid) / 全件
  - Safety は 4 ベンチの単純平均。Math = mean(gsm8k, minerva_math500)、Code = mean(humaneval, mbpp)、Medical = mean(pubmedqa, medqa_4options)、General = mean(mmlu, ifeval, alpaca_eval2)
  - 主表は α=0.60 と単発手法（N/A）を抽出する。`diagonal_sst_main` は `sst` に改名される
- **注記**: 入出力パスが `/Users/saki/lab/src/sst_v3/...` にハードコードされている。本インテントの表再生成は、このスクリプトを直さずに `v5/` へ新規実装し、出力も `v5/` に置く予定（`code-quality-assessment.md`）

### experiment-configs
- **場所**: `configs/config_main.yaml`（主実験）、`config_main2.yaml`（mmlu_pro と `fisher_weighted` を追加）、`config_ablation.yaml`（比率 5 種、variant 2 種、layer prior、FIM n∈{50,100,500}、k=0.20）、`config_ablation2.yaml`（k∈{0.01,0.05,0.10,0.20}、n∈{50,100,250,500}）、`config_ablation_n500_tmp.yaml`（n=500 だけの一時設定）、`config_dummy.yaml`, `config_hirundo.yaml`
- **責務**: モデル ID、データパス、評価タスク、パターン、手法、α スイープ `[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]`、SST 主設定（k=0.20, n=500, `Fh/Fb`, interpolation, hard mask, layer_wise なし）
- **注記**: `data.fim.epsilon: 1e-6` はコードから読まれない。アブレーション設定は `merge.main.k_values: []` で、主条件を生成しない。soft mask はどの設定でもコメントアウトされている（`config_ablation.yaml` L93, `config_ablation2.yaml` L93）。SAGAI_EN_sst の設定（Llama-3.1-8B、A5 / A6 / A7、k=50%、モジュール種別の層重み）に当たる設定ファイルはない

### flmsec-paper
- **場所**: `論文/FLMSEC/Formatting_Instructions_For_NeurIPS_2026/neurips_2026.tex`（本文）、`tables/table1-4.tex`、`appendix.tex`
- **責務**: 比較手法 8 種（TA, TIES, DARE, DELLA, MergeAlign, SafeMERGE, LED-Merging, FWA）の validity-aware 再評価。主結果は α=0.6、3 seed
- **位置付け**: 大規模評価の論文であり、提案手法の SST-Merge は意図的に載せていない（研究者本人の説明）

### dlsp-paper
- **場所**: `論文/DLSP_hiromi2/main.tex`、`論文/DLSP_hiromi2/tables.tex`
- **位置付け**: secure merge の提案論文（研究者本人の説明）。SST-Merge は、この secure merge に特化した merge 手法という位置付けである。SAGAI_EN_sst が secure merge の出典として引く `\cite{11050841}`（`論文/SAGAI_EN_sst/main.tex` L410, L450）は、`論文/SAGAI_EN_sst/main.bib` L51-59 の書誌（2025 IEEE SPW、pp. 111-117）とタイトルが一致する（書誌で確認）
- **内容（ソースから読み取れる事実）**: タイトルは「Enhancing Jailbreak Resistance in Large Language Models Using Model Merge」（L351）。JAILBREAK TRIGGER（1,400 件、1,200 / 200 に分割）でパッチモデルを作り（L1383, L1527）、FT モデルと mergekit の Linear / Task Arithmetic（重み 0.5 / 0.5、`dtype: float16`）で merge する（L442-456, L1541-1552）。ベースは Mistral-7B-v0.1 / v0.3、FT モデルは Mistral 系 3 種（`tables.tex` L18-32）。LoRA は r=8（L949）。評価は TrustLLM の RtA、StrongREJECT、AdvBench / GCG / PAIR / TAP の RtA、MT-Bench（L478-528）
- **SST との対応**: FIM、λ、マスクなど SST 固有の手順は記載がない。SST の仕様は `sagai-sst-paper` にある。対応表は `architecture.md` の「補足: DLSP_hiromi2 との対応」
- **ソースの状態**: L422 の `\iffalse` から L1344 の `\fi` までが本文を囲んでおり、コンパイルするとタイトルと付録だけが出力される（コンパイル結果は未確認）。`tables.tex` の表のキャプションは「Caption HERE!!!!!」のまま

### sagai-sst-paper
- **場所**: `論文/SAGAI_EN_sst/main.tex`（2,119 行、IEEEtran conference / compsoc 形式）、`論文/SAGAI_EN_sst/tables.tex`（72 行）。`main.bib`（56 項目。secure merge の出典 `11050841` の項目だけを確認）。同じディレクトリの `figures/`, `appen_fig/` は画像のため未オープン
- **位置付け**: **SST-Merge の提案論文**（研究者本人の説明）。タイトルは「SST-Merge: Fisher-Ratio Subspace Optimization to Secure Model Merge」（L351）。著者は「anonymous author」で、実名のブロックは `\iffalse` で隠されている（L357-387）。数値を出した実装はリポジトリ外の v1（`v1-sst-core`）
- **内容（ソースから読み取れる事実）**:
  - 定式化: θ_merged = θ_util + Δθ（L490-494）。θ_util の近傍で FIM による局所二次近似（L522-529）、F_b + εI（L531）、Tax = ½ΔθᵀF_bΔθ、Gain = ΔθᵀF_hΔθ（L536-546）。max Gain s.t. Tax ≤ c は一般化固有値問題 F_h v = λF_b v（L551-573）。Safety subspace への F_b 直交射影（L575-594）
  - Diagonal SST: λ_i = f_h,i/(f_b,i+ε)（L619-623）、hard mask（top-k、L631-634）、soft mask σ(log(λ+δ)/τ)（L636-642）、層の prior w_layer（L644-649）、additive（L651-659）、interpolation w = clip(α(w_layer⊙m), 0, 1)（L661-677、「Task Arithmetic の座標ごとの一般化」L678）、境界の差 δ_k（L682-690）
  - Data-Free SST: 本文は λ̂ = Δ_h²/(Δ_b²+ε)（L747-761）、付録は |W|（L1142）。v1 の実装は Utility / Safety の LoRA 重みの二乗を別々に求めて比を取る
  - 実験: Llama-3.1-8B（L784 / L1064）、LoRA r=16 / alpha=32 / dropout 0.05 / `all-linear`（L1065）、A5 = RepliQA、A6 = Alpaca（各 10 epoch）、A7 = Jailbreak Trigger（5 epoch）（L1082-1084）。アダプタ単位で merge（L1093）。比較手法は TA / TIES（density 0.5）/ DARE（p=0.9）（L1097-1120）。SST は k ∈ {5, 10, 20, 50}% と soft、N=500、ε=10⁻⁶、Additive は soft mask、Interpolation は hard mask、δ_k による切り替えはなし（L1122-1136）。層重みはモジュール種別（L1149-1164）。α は 0.05〜1.00 の 15 点（表）
  - 結果: A5 + A7（`tab:res_a5_*`、L1190-1458）と A6 + A7（`tab:res_a6_*`、L1465-1739）の表。指標は JB Res. と RepliQA / Alpaca。本文の図は A5 + A7 だけ（L823-844）。主張は「SST は有用性の低下が緩やかで、interpolation は有用性を保ちつつ jailbreak 耐性を大きく上げる」（L846-848, L855）
- **ソースの状態**: `tables.tex` は `main.tex` から読み込まれない（`\include{tables}` が L69 でコメントアウト）。内容は `論文/DLSP_hiromi2/tables.tex` と同一（`diff` で確認）。付録は `\iffalse` で囲まれていない（L866 と L2116 の `\iffalse` / `\fi` はコメントアウトされている）ので、本文と付録の両方がコンパイル対象である（コンパイル結果は未確認）
- **論文内の不整合**: ベースモデル名（L784 と L1064）、α の刻み（L806 と表）、k の集合（L807-808 と L1126）、Data-Free の proxy（L747-761 と L1142, L1762）、A5 の Data-Free k=10% と k=20% の表が同一（L1411-1425 と L1441-1455。v1 の旧ラベルの結果自体が同一）、表の外に残った地の文（L1526, L1649, L1680, L1712）、DARE の対象（論文は τ_s だけ、v1 のコードは両方）
- **コードとの対応**: λ、ε、N、additive / interpolation の式は `mergers-sst` と一致する。ベース、ユーティリティモデル、merge の単位、マスクの単位、層重み、α の格子、評価は v3 と違う。全体の対応表は `architecture.md` の「論文（SAGAI_EN_sst）とコードの対応表」、v1 との 4 者照合と代表セルの数値照合、再現できるかの判定は `code-quality-assessment.md`

## リポジトリ外（v1 / v2）

ワークスペース直下の `v1/` と `v2/` を、論文との照合のために読んだ。読んだ範囲は下のとおりで、スナップショットの外にあり、`analyzed.paths` には入れていない。実行はしていない。

### v1-sst-core
- **場所**: `v1/core/sst_merge.py`（FIM・GEVP・Additive）、`v1/core/sst_merge_interpolation.py`（補間型）、`v1/core/sst_merge_data_free.py`（Data-Free）。リポジトリ外
- **責務**: SAGAI_EN_sst の SST-Merge を LoRA アダプター上で実装する。ベースは `meta-llama/Llama-3.1-8B-Instruct`（`sst_merge.py` L42）
- **FIM**: LoRA 要素（`'lora' in name`）の勾配を、バッチ 4 件・train モードで集め、バッチ間の分散に 1e-6 を足す（`FIMCalculator`、L76-216）。F_b は「ベース + Utility LoRA」、F_h は「ベース + Safety LoRA」（L454-475）。データは Utility が HF の RepliQA `repliqa_0` / Alpaca `train` のランダム 500 件（L998-1033）、Safety が `data/response_dataframe.csv` の prompt + response（L960-992）
- **λ とマスク**: `F_h / (F_b + 1e-6)`（`GEVPSolver`、L219-266）。hard は全 LoRA 要素を連結したグローバルな top-k（L283-291）、soft は log(λ+1e-10) を 5〜95 パーセンタイルで [0,1] に線形正規化（L293-324）
- **merge**: LoRA の A と B の各要素を別々に混ぜる。Additive は `u + α·lw·mask·s`（L521-626）、Interpolation は `(1−w)·u + w·s`（w = α·lw·mask。clip なし、`sst_merge_interpolation.py` L248-346）。層重みは `lm_head` 1.5 / attention 1.2 / MLP 0.8（`sst_merge.py` L344-353。`lm_head` は LoRA の対象外で実効なし）
- **Data-Free**: Utility と Safety の LoRA 重みの二乗（+1e-6）を別々の F とし、λ=(F_h+ε)/(F_b+ε)（`sst_merge_data_free.py` L29-69, L246-251）。層重みは別の値（1.0 / 0.8 / 0.6）で既定 off、soft は z-score のシグモイド（L287-290）。`FIMCalculatorDataFree` クラス内に貼り付けられた `_merge_with_gevp`（L73-149）は呼ばれない死にコード
- **注記（要検証）**: FIM モデルにアダプターを載せる 2 通りの処理（`_load_adapter_to_model` L498-519 と `run_all_merges_hard.py` L382-403）に、標準的な PEFT の鍵形式を仮定すると意図どおりに載らない疑いがある（`code-quality-assessment.md` の事項 3、V12）。マスクと FIM の並びの一致の検査がない（事項 4、V13）

### v1-merge-drivers
- **場所**: `v1/scripts/merging/`（`run_all_merges_hard.py`: Additive hard、k=5〜50、α 15 点。`run_all_merges_interpolation.py`: 補間型、k=5〜50 × layer-wise × α 15 点。`run_data_free_merge.py`: Data-Free の加算型と補間型。`run_all_merges.py`: 旧版（soft、α 0.1〜1.0）。`run_all_merges_adapter_based.py`、`run_all_merges_full.py`）。リポジトリ外
- **責務**: 設定を先頭の定数で持ち、`input("gpu num:")` で GPU を決め、アダプター単位で merge して `merge_and_unload` でフルモデルに変換する。FIM と λ はペアごとに 1 回計算し、k ごとにマスクをキャッシュする
- **注記**: 論文の表は、これらのドライバの複数の版が作った結果の混在である（`code-quality-assessment.md` の代表セル照合）。`run_sst_merge_comparison.sh` と `run_all_experiments.sh` は存在しないパスを呼ぶ古いシェルで、数値の生成元ではない

### v1-baseline-merge
- **場所**: `v1/scripts/merging/baseline_merge.py`（`CustomBaselineMerger`、L286-437）、`merge_adapters.py`。リポジトリ外
- **責務**: TA は重み `[1−α, α]` の A / B 要素の和（L296-318）。TIES は各アダプターの絶対値上位 density=0.5 を残して符号選出（L320-378）。DARE は両方のアダプターの A / B 要素を確率 0.9 で落として 10 倍にし、重み付き和（L381-416）。論文の「DARE は τ_s だけを疎にする」とは一致しない。`merge_adapters.py` の `sst_merge` は FIM を使わない層重み付き補間（min(α·w, 0.95)）

### v1-eval-scripts
- **場所**: `v1/scripts/FT/`（`safety_tune.py`, `repliqa_tune.py`, `alpaca_tune.py` と `jailbreak_eval.py`, `repliqa_eval.py`, `alpaca_eval.py`）。リポジトリ外
- **責務**: LoRA（r=16, alpha=32, dropout 0.05、7 種の proj）を学習し、評価する。JB Res. は `LibrAI/longformer-harmful-ro`（TrustLLM）の拒否率（500 プロンプト、greedy、最大 256 トークン、判定不能時はキーワード）、RepliQA / Alpaca は ROUGE-1 の F 値の平均（それぞれ `repliqa_0` と `train` の先頭 500 件）。A5 / A6 の学習データは評価データと同じ split である（重なりの有無は要検証、V16）

### v1-results-and-tables
- **場所**: `v1/eval/merged/{baseline,sst_merge,interpolation,data_free}/` と先頭が空白の ` A7-7ep/`、`v1/all_eval_results_summary.json`、`latex_tables_output.tex`、`detailed_config_analysis.txt`、`generate_latex_from_json.py`、`scripts/analysis/`。リポジトリ外
- **責務**: 結果 JSON（`resistance_rate`、`rouge1.mean` など）と、その集計。論文の表の数値の出所（代表セルの照合は `code-quality-assessment.md`）。`latex_tables_output.tex` は A6 の SST と Data-Free の表で、Interpolation の SST 列は `-`。`detailed_config_analysis.txt` は ` A7-7ep/` のフォルダを読んだ集計
- **注記**: 旧ラベルの Data-Free は k と layer-wise が結果に効いていない（`code-quality-assessment.md` の事項 5）。先頭が空白のフォルダ名は参照時に注意が要る

### v2-sst-merge-scaffold
- **場所**: `v2/scripts/merge/`（`sst_merge_core.py`, `run_sst_merge.py`, `merge_llama2_sst_suite.py`）、`v2/configs/aaai27/`、`v2/scripts/steering_hook.py`、`v2/run_all_experiments_suite.sh`。リポジトリ外
- **責務**: Llama-2-7B と 3 ドメインモデル（WizardMath、WizardCoder、medalpaca）のパターン merge の足場。`sst_merge_core.py` は FIM（バッチ勾配二乗の平均）、λ、Data-Free（フル重みの Δ²）、グローバル top-k、適用の関数を持つが、`run_sst_merge.py` はダミーテンソルで動くフック検証用で、実モデルには接続されていない。`merge_llama2_sst_suite.py` は safetensors をテンソルごとにストリーミングで merge し、動く SST は Data-Free（各ドメインモデルについて自分 / 他モデル平均の Δ² の比、テンソルごとの top-k または z-score のシグモイド、加算）だけである。`sst_merge`（FIM 版）の指定は既定の TA の分岐に落ちる（L294-300）。Safety モデルを含まない
- **v3 との関係**: 3 ドメインモデルと Llama-2-7b-hf の組、`fim` 設定の形、`steering_hook.py` の存在が v3 に引き継がれている。コードの import はない

### v2-finetuning-baselines
- **場所**: `v2/scripts/fine_tuning/`（`run_lora_ft.py`、各評価、Phase 2 のスクリプト）、`v2/docs/fine_tuning_phase2_results/`、`v2/results/`（Llama-3.1-8B-Instruct、Llama-3-8B-Instruct、`lm_eval_raw` の名前のみ確認）。リポジトリ外
- **責務**: Llama-3-8B-Instruct への Utility / Safety / Mixed / Coding の LoRA FT と、ID / OOD の評価（HumanEval 等、HarmBench、XSTest の過剰拒否）。Safety Tax の確認用ベースラインで、SST の merge には使われない（`walkthrough.md` で結果の要約を確認）

## 構造だけ確認したコンポーネント（SHALLOW）

### orchestrators
- `scripts/run_experiments.py`（SST を含む全手法の merge を起動する。SST の引数は L475-523 で明示して渡す）、`scripts/run_base_eval_parallel.py`, `scripts/slurm_*.sh`, `scripts/submit_*.sh`

### merging-precompute
- `scripts/merging/`（`compute_datafree_importance.py`, `matena_fisher.py`, `prepare_led_scores.py`, `elect_led_masks.py`）

### analysis-misc
- `scripts/analysis/` の残り（`compute_safety_diagnostics.py`, `recompute_all_tables_unified.py`, `generate_paper_tables_4_and_5.py`, `generate_summary_tables.py`, `pareto_auc.py`, `calculate_observed_range_auc.py`, `generate_three_panel_plot.py`, tex 置換スクリプト群）

### eval-auxiliary
- `scripts/eval/eval_alpaca.py`, `eval_instruction_datasets.py`, `eval_preliminary.py`（TrustLLM / BeaverTails）, `eval_hirundo_unlearning.py`, `check_harmbench_results.py`

### fixes-tools
- `scripts/fixes/`, `scripts/tools/`, `scripts/fix_*_fast.py`

### steering-hook-tests
- `scripts/steering_hook.py`（規約の動的検査。許可するベースモデルに `meta-llama/Meta-Llama-3.1-8B-Instruct` を含む（L114-133）。Data-Free の実行中に RepliQA などのデータファイルを開くことを禁じる（L38-56））、`scripts/tests/`

### third-party-evaluators
- `evaluators/HarmBench`, `evaluators/jailbreakbench`, `evaluators/strong_reject`（gitlink）

### results-vllm-store
- `results/vllm/`（結果ファイル契約は `api-documentation.md`）
