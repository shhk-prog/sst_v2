# API ドキュメント: v3

v3 には HTTP API はない。公開面は (1) CLI、(2) `scripts/mergers` パッケージの Python 関数、(3) 結果 JSON のファイル契約の 3 つである。本インテントで最も重要なのは (3) である。SST-Merge のアルゴリズムと、提案論文（SAGAI_EN_sst）とコードの対応表は `architecture.md` の「SST-Merge の詳細」にある。リポジトリ外の v1 / v2 の入口と結果ファイル契約は末尾の「リポジトリ外（v1 / v2）」に簡潔に書いた。

## 1. CLI

### `scripts/merge.py`（単一 merge）

| 引数 | 既定値 | 意味 |
|---|---|---|
| `--config` | `configs/config_main.yaml` | 設定 YAML |
| `--method` | 必須 | `diagonal_sst`, `data_free_sst`, `task_arithmetic`, `ties`, `dare`, `della`, `fisher_weighted`, `matena_fisher`, `safemerge`, `led_merging`, `mergealign` |
| `--pattern` | `safety+math` | `safety+math` / `safety+code` / `safety+medical` / `safety+math+code+medical` |
| `--alpha` | 0.5 | Safety 側の重み（手法ごとに意味が違う。`architecture.md` の「α の意味」参照） |
| `--k` | config の `merge.main.k_values[0]`（主設定 0.20） | hard mask で残す座標の割合（テンソルごと）。soft mask では温度 τ。`k_values` が空の設定で省略すると IndexError（`merge.py` L125） |
| `--sst_ratio` | config の `merge.main.sst_ratio`（`Fh/Fb`） | `Fh/Fb`, `Fh only`, `1/Fb only`, `magnitude`, `random` |
| `--variant` | config の `merge.main.variant`（`interpolation`） | `interpolation` または `additive` |
| `--mask_type` | config の `merge.main.mask`（`hard mask`） | `hard mask` または `soft mask` |
| `--layer_wise`, `--layer_prior` | false, `uniform` | 層ごとの重み（`sin`, `linear`, `reverse_linear`, `exp`） |
| `--sample_size` | config の `merge.main.sample_size`（500） | FIM の推定サンプル数（データの先頭から切り出す） |
| `--norm_standardization`, `--fisher_normalization`, `--norm_clipping`, `--max_norm_ratio` | off, off, off, 1.5 | 主実験では未使用の拡張 |
| `--seed` | 42 | Safety LoRA の seed（`models/safety_lora_seed{N}` を選ぶ）。merge の乱数 seed ではない |
| `--output_dir` | 必須 | merge 済みモデルの出力先 |
| `--fim_cache_dir`, `--no_fim_cache`, `--overwrite_fim_cache` | `cache/fim` | FIM キャッシュの制御 |

省略時の値の解決は `apply_config_defaults`（`merge.py` L121-148）が行い、常に `merge.main` を読む（アブレーション設定の値は読まない）。

出力: モデル重み（ベースモデルの config とトークナイザで保存）、`merge_metadata.json`（ハイパーパラメータ一式。マスク比率は含まない）、`complexity_summary.json`、`runtime_profile.json`（Fisher 系では `fisher_weights_summary.json` / `matena_fisher_info.json`）。

### 評価 CLI（`scripts/eval/`）

| スクリプト | 主な引数 | 採点 |
|---|---|---|
| `eval_safety.py` | `--model_path`, `--tasks`（harmbench,jailbreakbench,strongreject,wildjailbreak）, `--limit`, `--classifier_type`（auto / harmbench / wildguard / strongreject）, `--use_vllm` | `<s>[INST] p [/INST]` で greedy 生成（max_tokens=128）。auto では harmbench は `cais/HarmBench-Llama-2-13b-cls`、strongreject は `strong_reject` の `finetuned_gemma`（例外時は `string_matching`）、それ以外は `allenai/wildguard`。gibberish は asr=0 |
| `eval_utility.py` | `--model_path`, `--tasks`, `--limit`, `--apply_chat_template`（既定 true）, `--use_vllm` | `lm_eval.simple_evaluate`、`num_fewshot=0`。`apply_chat_template` が拒否されると外して再試行する。humaneval / mbpp / ifeval / mmlu_pro は事後に再採点 |
| `eval_alpaca.py` | `--model_path`, `--limit` | AlpacaEval2（judge: `weighted_alpaca_eval_gpt4_turbo`） |
| `eval_instruction_datasets.py` | `--model_path` | Evol-Instruct-Code と MedAlpaca の PPL |

### オーケストレータ

- `run_experiments.py --stage {all,ft,base_eval,merge,merge_eval,pareto}`（SHALLOW）: merge を起動する。SST では `--sample_size`, `--alpha`, `--k`, `--sst_ratio`, `--variant`, `--mask_type`, `--layer_wise`, `--layer_prior` を明示して渡す（L475-523）
- `run_mergekit_parallel.py --config ...`: mergekit 系 4 手法だけを（seed × パターン × 手法 × α）で `merge.py` に投げる。seed ごとに最初の 1 件を先に実行する
- `merge_eval_parallel.py --config ... --seeds ... --limit 320 --use_vllm [--patterns] [--model_index] [--list_models]`: **merge は行わない**。設定から出力名の一覧を組み立て、`merge_metadata.json` が `success` のモデルだけを GPU ごとに並列評価する。出力先は `results/vllm/debug_limit{limit}/merged`（limit=0 なら `final`）。SST のアブレーション条件は 1 因子ずつ変える（`merge_eval_parallel.py` L219-228）

### `scripts/data_prep.py`

- `--config`（既定 `configs/config_main.yaml`。実際には読まない）。FIM 用データ（各ドメインの先頭 1,000 件、有害データは CSV 全行）と評価用データを作り、評価器リポジトリの clone と追加パッケージの pip install も行う。取得失敗時はプレースホルダを書く

## 2. Python 関数（`scripts/mergers/__init__.py` が公開）

- `merge_sst(base_model, util_models_dict, safe_model, method, sst_ratio, variant, mask_type, layer_wise, layer_prior, alpha, k_ratio, fim_b_dict=None, fim_h=None, norm_standardization=False, fisher_normalization=False, norm_clipping=False, max_norm_ratio=1.5) -> (merged_state_dict, fisher_weight_stats)`: `diagonal_sst`, `data_free_sst`, `fisher_weighted` を処理する（`sst.py` L8-202）
- `run_mergekit(output_dir, method, base_model, models_dict, alpha)`: mergekit YAML を生成し、`mergekit-yaml ... --allow-crimes --copy-tokenizer` を実行する
- `estimate_fim(model, dataset_path, sample_size, tokenizer, device) -> dict[name, fp32 tensor]`: 経験的対角 FIM（全トークン損失の勾配二乗の平均）
- `load_or_estimate_fim(model, dataset_path, sample_size, tokenizer, device, args, config, kind, domain, model_path=None)`: キャッシュがあれば読み、なければ推定して保存する
- `get_fim_tensor(fim, name, like_tensor)`: FIM を `like_tensor` の device と dtype（fp16）にキャストする。名前がなければ 0 テンソルを返す
- `run_safemerge`, `run_led_merging`, `run_mergealign`, `run_matena_fisher_baseline`: 外部実装または `merging/matena_fisher.py` の呼び出し

## 3. 結果ファイル契約（`results/vllm/`、SHALLOW）

構造とファイル名だけを確認した（apparent size 約 52G）。

```text
results/vllm/
├── debug_limit320/
│   ├── base/                                   # 単体モデル 6 種 × 16 ファイル（96）
│   │   └── sst_merge_v3_main_base_{WizardMath|WizardCoder|MedAlpaca|SafetyFT_seed{42,43,44}}_{metric}.json
│   └── merged/seed{42,43,44}/{pattern}/{method}/
│       ├── ablation/{sst,datafree}/            # アブレーション（safety+math で sst 864、datafree 720 エントリ）
│       └── *.json, *_alpaca_eval_out/
├── preliminary/merged/                         # 予備実験（フラット、960 ファイル）: *_{trustllm|beavertails}.json
└── alpaca_outputs/limit320/                    # AlpacaEval 用の生成（フラット、1776 ファイル）
```

### ファイル名の規則

- SST 主実験: `sst_merge_v3_main_diagonal_sst_main_{pattern}_alpha{a}_n500_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed{s}_{metric}.json`
- Data-Free SST 主実験: `sst_merge_v3_main_data_free_sst_main_{pattern}_alpha{a}_k0.2_FhFb_interpolation_hardmask_nolayerwise_seed{s}_{metric}.json`（`n` なし）
- α を持つ比較手法（task_arithmetic, ties, dare, della）: `sst_merge_v3_main_{method}_{pattern}_alpha{a}_seed{s}_{metric}.json`
- 単発手法（safemerge, led_merging, mergealign, matena_fisher）: `sst_merge_v3_main_{method}_{pattern}_seed{s}_{metric}.json`（α なし。集計では `N/A`）
- アブレーション: `sst_merge_v3_ablation_{diagonal_sst|data_free_sst}_ablation_..._{ratio}_{variant}_hardmask_{nolayerwise|layerwise_<prior>}_seed{s}_{metric}.json`。ratio は `FhFb`, `Fh only`, `1Fb only`, `magnitude`, `random` で、空白を含む。中心条件（`FhFb`, interpolation, k0.2, n500, nolayerwise）もアブレーション名で 1 回実行される。`layerwise_uniform` は `nolayerwise` と数式上同じ

名前の組み立ては `merge_eval_parallel.py` の `build_out_name_for_sst`（L145-179）と `build_out_name_for_baseline`（L182-186）。

### `{metric}` サフィックス

| 種別 | サフィックス |
|---|---|
| 安全性 | `harmbench_safety`, `jailbreakbench_safety`, `strongreject_safety`, `wildjailbreak_safety` |
| 有用性（旧方式、ドメインまとめ） | `utility_math`, `utility_code`, `utility_medical`, `utility_general` |
| 有用性（新方式、タスク別） | `utility_math_gsm8k`, `utility_math_minerva_math500`, `utility_code_humaneval`, `utility_code_mbpp`, `utility_medical_pubmedqa`, `utility_medical_medqa_4options`, `utility_general_mmlu`, `utility_general_ifeval` |
| その他 | `alpaca_eval2`（と `_alpaca_eval_out/` ディレクトリ）, `inst_evol_code`, `inst_medalpaca`（PPL） |

### 安全性 JSON のスキーマ（1 件で確認）

トップレベル: `status`, `mockup`, `completed`, `model`, `task`, `dataset_path`, `limit`, `expected_n`, `n`, `classified_n`, `asr`, `original_asr`, `gibberish_n`, `gibberish_ratio`, `results`, `harmbench_cls_asr`。
`results[]` の各要素: `prompt`, `response`, `asr`, `classifier_output`, `is_gibberish`, `original_asr`, `harmbench_cls_asr`, `harmbench_cls_output`。

### カバレッジの偏り（分析で注意すべき点）

- 4 ドメインパターンには safemerge / led_merging / mergealign がない（単一ドメイン専用。`merge_eval_parallel.py` の `should_skip_method_pattern`）
- led_merging は `safety+medical` にもない（対応ドメインは math と code のみ）
- `diagonal_sst_main` と `task_arithmetic` には、同じ α に旧方式と新方式の有用性ファイルが併存する（`dare` などは旧方式のみ）。`ties` は新方式が一部の α だけにある
- Llama-2-7b-hf（ベースモデル）自身の評価結果は `base/` にない
- 各ベンチマークは最大 320 件（`debug_limit320`）
- `base/` のドメインモデルは自身の config（code なら `rope_theta: 1000000`）で評価される。一方、SST の merge 済みモデルはベースの config（`rope_theta` 既定値）とベースの embed / lm_head で保存される（`merge.py` L622-633, `sst.py` L50-55）。α=0 の SST でも `base/` のドメインモデルとは同じにならない

## 4. リポジトリ外（v1 / v2）の入口と結果ファイル契約

読むだけで実行していない。ワークスペース直下の `v1/`、`v2/`。

### v1 の入口

- 引数ではなく、スクリプト先頭の定数で設定する。`input("gpu num:")` で GPU を尋ねる。例: `scripts/merging/run_all_merges_interpolation.py`（`merge_pairs`, `alpha_values`, `sst_k_values`, `use_layerwise_options`, `use_gevp_options`, `sst_max_fim_samples`、L45-80）、`run_data_free_merge.py`（`k_values`, `merge_mode_options`, `top_k_ratio_options`、L50-55）
- Python の公開クラス: `core/sst_merge.py` の `FIMCalculator`, `GEVPSolver`, `SSTMerge`（`merge`, `_merge_with_mask`, `merge_full_models`）、`core/sst_merge_interpolation.py` の `SSTMergeInterpolation`、`core/sst_merge_data_free.py` の `SSTMergeDataFree`（`merge_mode` が `additive` または `interpolation`）
- 評価: `scripts/FT/jailbreak_eval.py`（`--num_samples` 既定 100、`--trustllm_model`、`--max_new_tokens` 256）、`repliqa_eval.py`、`alpaca_eval.py`（先頭 500 件）。出力は `{adapter_name}_{jailbreak|repliqa|alpaca}_eval_results.json`

### v1 の結果ファイル契約

```text
v1/eval/
├── finetuned/    # 単体アダプターの評価: {A5|A6|A7|A8|BASE_MODEL}_..._{3,5,7,10}ep_..._{jailbreak|repliqa|alpaca|gsm8k}_eval_results.json
└── merged/
    ├── baseline/                      # A5_A7_{task_arithmetic|ties|dare}_a{α}_*（旧）
    ├── sst_merge/merge_eval/          # A{5,6}_A7_task_arithmetic|ties|dare_a{α}, A{5,6}_A7_sst_k{k}[_lw]_a{α}（soft の旧ラベル）, ..._hard_full（hard）, ..._nogevp
    ├── interpolation/                 # A{5,6}_A7_sst_interp_k{k}[_lw][_nogevp]_a{α}（α 15 点）
    ├── data_free/                     # A{5,6}_A7_data_free[_interp]_k{k}[_lw]_a{α}[_topk{k}]（旧ラベルと新ラベルが混在）
    └──  A7-7ep/                       # フォルダ名の先頭が空白。interpolation/merge_eval_interpolation/（k=5 だけ、α 10 点）と data_free/
```

- ジャイルブレイクの JSON: `base_model_id`, `merged_model_path`, `num_samples`, `evaluation_method`, `metrics.{resistance_rate, attack_success_rate, refusals, total}`, `trustllm_breakdown`, `results[]`。表の「JB Res.」は `resistance_rate` ×100
- RepliQA / Alpaca の JSON: `metrics.{rouge1, rouge2, rougeL}.{mean, std}`、`results[]`。表のスコアは `rouge1.mean` ×100
- 集計: `all_eval_results_summary.json` は `category`（確認した値は base / additive / interpolation。`generate_latex_from_json.py` は data_free も参照する）, `filename`, `pair`, `utility`, `method`, `alpha`, `k`, `mask_type`, `gevp`, `layerwise`, `eval_type`, `resistance_rate` / `rouge*` を持つ配列。`mask_type` は結果から読み取った値ではなくファイル名の解析で付いたラベルで、interpolation の結果は soft と記録される。同じファイル名の項目が複数あり、α が欠けた項目（`A6_A7_task_arithmetic_jailbreak_eval_results.json` など）もある

### v2 の入口

- `scripts/merge/merge_llama2_sst_suite.py --config configs/aaai27/llama2_sst_experiment.yaml --method ... --alpha ... --k {soft|0.xx} --pattern math,code`。出力は `models/merged/{method}_{pattern}_a{α}_k{k}/`（safetensors をストリーミング merge。mergekit 系は `mergekit-yaml`）。`run_all_experiments_suite.sh` が全手法・全パターンを回す
- `scripts/merge/run_sst_merge.py`（`--method diagonal_sst|data_free_sst` ほか）はダミーテンソルで動くフック検証用。保存はしない
- `scripts/fine_tuning/run_lora_ft.py`（`--utility_dataset_path`, `--safety_dataset_path`, `--safety_mix_ratio`, `--learning_rate`）と各評価。結果は `v2/results/{Llama-3.1-8B-Instruct,Llama-3-8B-Instruct,lm_eval_raw}/`（名前のみ確認）
