# v3モデルマージ機能の動作検証および修正計画

この計画書では、`v3` におけるモデルマージ機能（各種ベースライン手法および提案手法）が正常に動作するか検証し、見つかったバグを修正する手順を提案します。

## 現状の課題と調査結果（静的解析）

静的解析の結果、外部リポジトリを使用するベースライン手法において、そのままでは確実に動作しない重大な不整合（バグ）が複数見つかりました。

### 1. MergeAlign (`baselines/MergeAlign/merging/lm_cocktail/lmcocktail_merge_align.py`)
- **課題1**: `merge.py` の `run_mergealign` 関数が、マージ対象モデルや出力ディレクトリなどの引数をコマンドライン引数として一切引き渡していません。
- **課題2**: `lmcocktail_merge_align.py` 内で、モデル名 (`model_names`) やデータセットパス (`--dataset_path`) が固定値（元著者のibexクラスタ環境のパスなど）としてハードコードされているため、実行すると確実にエラーになります。

### 2. LED-Merging (`baselines/LED-Merging/merge_llms.py`)
- **課題1**: `merge_llms.py` にマージ対象モデルの対応表 `MODEL_DIR` がハードコードされており、コマンド引数 `--models_to_merge` に渡された値が `MODEL_DIR` に存在しない場合は `KeyError` が発生します。
- **課題2**: `MODEL_DIR` の値自体も `/path/to/WizardLM-13B-V1.2` などの存在しないダミーパスになっています。

### 3. SafeMERGE (`baselines/SafeMERGE/get_safemerge_model.py`)
- **課題1**: `get_safemerge_model.py` で `dataset_name = args.finetuned_model_id.split("-")[-2]` や `safety_model_name = args.safety_model_id.split("-")[-2]` としており、引数に `-` が含まれないローカルパス（例: `models/temp_math_lora` など）を渡すと `IndexError: list index out of range` になります。

---

## 提案する修正内容

外部リポジトリのコードを最小限の変更で実用可能にし、かつ `merge.py` との整合性を取ります。

### 1. MergeAlign の修正
- [MODIFY] [lmcocktail_merge_align.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/baselines/MergeAlign/merging/lm_cocktail/lmcocktail_merge_align.py)
  - コマンドライン引数に `--model_names` (リスト形式) を追加し、ハードコードされているモデル名の代わりに指定されたものを使用するようにします。
  - `--output_path` のデフォルト値や挙動を整理します。
- [MODIFY] [merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/merge.py)
  - `run_mergealign` 関数内で、`--model_names`, `--dataset_path`, `--output_path` などの引数を正しく渡すように修正します。

### 2. LED-Merging の修正
- [MODIFY] [merge_llms.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/baselines/LED-Merging/merge_llms.py)
  - `MODEL_DIR` にキーが存在しない場合は、渡された引数をそのままモデルのパス/IDとして使用するようにフォールバック処理を追加します。
  - 同様に、`MODEL_DIR[args.pretrained_model_name]` についても、キーが存在しない場合は `args.pretrained_model_name` をそのままパスとして扱うように修正します。

### 3. SafeMERGE の修正
- [MODIFY] [get_safemerge_model.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/baselines/SafeMERGE/get_safemerge_model.py)
  - `args.finetuned_model_id` や `args.safety_model_id` を `-` で分割する処理で、要素数が不足している場合（`IndexError`）に備えて、フォールバックとしてパスのベース名を使用するように修正します。

---

## 検証計画

7Bなどの巨大モデルを実際にダウンロード・ロードしてテストすると、ディスク・メモリや時間の観点から現実的ではありません。
そこで、超軽量のダミーモデルを用いてマージ機能の全ルートが動くか検証します。

### 1. テスト環境の準備
- `scripts/create_dummy_models.py` を作成し、軽量なダミーモデル（例: `meta-llama/Llama-2-7b-hf` の構成を極小化したダミー、および LoRA アダプタのダミー）を作成してローカルに保存します。
  - `steering_hook.py` が `llama-2-7b` や `wizardmath` などの名前を含むモデルパスしか許可しないため、作成するダミーモデルのパス名にこれらを含めます。

### 2. テスト実行スクリプトの作成
- `scripts/test_merge_all.py` を作成し、以下の10種類の手法すべてを連続してダミーモデルで実行します。
  1. `diagonal_sst` (sst-merge)
  2. `data_free_sst` (data-free sst-merge)
  3. `ties` (mergekit)
  4. `dare` (mergekit)
  5. `task_arithmetic` (mergekit)
  6. `della` (mergekit)
  7. `fisher_weighted`
  8. `safemerge`
  9. `led_merging`
  10. `mergealign`

### 3. 実行と結果確認
- `scripts/test_merge_all.py` を実行し、全手法が正常にモデルマージを終えて、出力先にマージされたモデルファイルが保存されることを確認します。
- 検証結果を `walkthrough.md` にまとめます。
