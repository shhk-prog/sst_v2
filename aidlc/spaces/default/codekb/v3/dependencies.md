# 依存関係: v3

ライブラリのバージョン一覧は `technology-stack.md` にある。本ファイルは依存の向きと、外部リポジトリ・データ・モデルへの依存だけを書く。

## 内部の依存（モジュール間）

```text
scripts/merge.py
  -> steering_hook
  -> mergers (__init__)
       -> mergers.constants
       -> mergers.utils        -> mergers.constants
       -> mergers.fim          -> mergers.utils
       -> mergers.sst          -> mergers.utils, mergers.fim
       -> mergers.mergekit     -> steering_hook, mergers.constants
       -> mergers.baselines    -> merging/matena_fisher.py（遅延 import）
scripts/run_experiments.py（SHALLOW）                 -subprocess-> merge.py, eval/*.py
scripts/run_mergekit_parallel.py                      -subprocess-> merge.py（mergekit 系 4 手法のみ）
scripts/merge_eval_parallel.py                        -subprocess-> eval/*.py, fixes/*.py（merge.py は呼ばない）
scripts/eval/eval_safety.py                           -subprocess-> fixes/fix_gibberish_safety_jsons.py
scripts/analysis/generate_table1_latex.py, generate_latex_tables_custom.py, generate_specific_tables.py
  -> analysis/generate_flmsec_hyo.py
scripts/analysis/generate_three_panel_plot.py  -reads-> docs/flmsec/flmsec_hyo_vllm_latex.md（generate_flmsec_hyo.py の出力）
```

循環参照は見つからなかった。`merge_eval_parallel.py` と `run_mergekit_parallel.py` は `mergers` を import せず、手法グループを自前で定義している。

## 外部リポジトリ（gitlink、`.gitmodules` なし）

| パス | 用途 | 呼び出し元 |
|---|---|---|
| `baselines/SafeMERGE` | `get_safemerge_model.py` | `mergers/baselines.py` の `run_safemerge` |
| `baselines/LED-Merging` | `merge_llms.py`（`venv_led` で実行）、`locate/score` の事前計算スコア | `run_led_merging`, `merging/prepare_led_scores.py` |
| `baselines/MergeAlign` | `merging/lm_cocktail/lmcocktail_merge_align.py` | `run_mergealign` |
| `baselines/mergekit` | mergekit 本体（`mergekit-yaml` コマンド） | `mergers/mergekit.py` |
| `baselines/model_merging` | 未初期化の submodule（ブリーフより） | 未確認 |
| `evaluators/HarmBench`, `evaluators/jailbreakbench`, `evaluators/strong_reject` | 評価データと StrongREJECT 実装 | `data_prep.py`（clone と editable install も行う）, `eval/eval_safety.py` |

`baselines/` は本スキャンでは開いていない。

## データへの依存（`data/` は未オープン。コード上のパスのみ）

| パス | 作成元 | 使用先 |
|---|---|---|
| `data/response_dataframe.csv` | 手動配置（TrustLLM JAILBREAK TRIGGER、固定の拒否文） | Safety SFT（全行）、F_h 用データの元、MergeAlign |
| `data/fim/fim_benign_{math,code,medical}.json` | `data_prep.py`（GSM8K train、Evol-Instruct-Code-80k、medical_meadow_medical_flashcards の各先頭 1,000 件）。取得に失敗するとプレースホルダ 500 件 | F_b（先頭 n 件、主設定 500） |
| `data/fim/fim_harmful.json` | `data_prep.py`（`response_dataframe.csv` の全行を変換） | F_h（先頭 n 件、主設定 500）。Safety SFT と同じデータ。SST の提案論文 SAGAI_EN_sst も F_h に Safety の学習データ（Jailbreak Trigger）を使う（`論文/SAGAI_EN_sst/main.tex` L792-797） |
| `data/eval/eval_harmful_{harmbench,jailbreakbench,...}.json` | `data_prep.py` | `eval_safety.py` |

## 生成物への依存

- `models/safety_lora_seed{42,43,44}` → `merge.py`（seed は Safety LoRA の seed）
- `models/temp_safety_full_seed{N}` → mergekit / SafeMERGE / LED / MergeAlign
- `cache/fim/*.pt` → SST と Fisher 系（キャッシュがあれば再推定しない。キーはデータの中身を含まない）
- `models/merged/*/merge_metadata.json`（`status: success`）→ `merge_eval_parallel.py` が評価対象を選ぶ
- `results/vllm/...` → `analysis/*`（契約は `api-documentation.md`）

## 外部モデルの系統への依存

SST と mergekit 系の手法は、ドメインモデルがベースモデル θ₀ から派生していること（θ_u − θ₀ がタスクベクトルであること）を前提にしている。SST の提案論文 SAGAI_EN_sst も、merge を「同じ事前学習モデルを共有する FT モデルの merge」に限ると明記している（`論文/SAGAI_EN_sst/main.tex` L438-444）。config.json では、code（CodeLlama-Python 系）と medical（LLaMA-1 系）がこの前提を満たさない（`technology-stack.md` の「外部モデルの系統」）。論文の数値を出した v1 は、ユーティリティも Safety も同じ Llama-3.1-8B-Instruct の LoRA で、この前提を満たす。

## リポジトリ外（v1 / v2）との関係

- v3 のコードは `v1/` や `v2/` を import せず、パスでも参照しない（`scripts/`、`configs/`、`README.md` の `.py` / `.sh` / `.yaml` / `.md` を grep しても、`v1/`、`v2/`、`sst_v2/v1`、`sst_v2/v2` への参照は見つからなかった）。つながりは設計と設定の引き継ぎだけである（`architecture.md` の「v1 → v2 → v3 の系譜」）
- 論文 `論文/SAGAI_EN_sst` の数値は、ワークスペース直下の `v1/eval/merged/` の結果ファイルから来ている。v3 の `results/vllm` とは対応しない（`code-quality-assessment.md` の代表セル照合）
- v1 の内部依存: `core/sst_merge_interpolation.py` が `core/sst_merge.py` の `FIMCalculator`, `GEVPSolver`, データローダー関数を import する。`core/sst_merge_data_free.py` は自前の `GEVPSolver` を持つ（`sst_merge.py` から流用したコピー）。ドライバ（`scripts/merging/run_all_merges*.py`, `run_data_free_merge.py`）が `core/` と `scripts/merging/baseline_merge.py` を import する
- v1 の外部依存: HF Hub（`meta-llama/Llama-3.1-8B-Instruct`、データセット `ServiceNow/repliqa`, `tatsu-lab/alpaca`、分類器 `LibrAI/longformer-harmful-ro`）、`rouge_score`、PEFT。mergekit は `baseline_merge.py` の `MergekitMerger` にあるが、論文の数値は自前実装（`CustomBaselineMerger`）の経路のもの（推定。ドライバの呼び出しから）
- v2 の外部依存: `scripts/setup_env.sh` が mergekit と lm-evaluation-harness を取得する。`run_all_experiments_suite.sh` が SafeMERGE を `../third_party/SafeMERGE` に clone する。`v2/mergekit/` と `v2/lm-evaluation-harness/` は外部ライブラリで未オープン

## 外部サービス

- Hugging Face Hub（モデルとデータセットのダウンロード）
- OpenAI API（AlpacaEval2 の judge）
