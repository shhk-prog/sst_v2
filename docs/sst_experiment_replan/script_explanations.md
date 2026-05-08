# SST-Merge (v2_experiments) スクリプト構成と役割の解説

本ドキュメントでは、`v2_experiments/scripts` 配下に構築された各スクリプトの役割と、論文（`docs/07_paper/論文.md`）との整合性について解説します。

---

## 1. 環境構築とデータ準備

### `setup_env.sh`
* **役割**: `lm-evaluation-harness` や `Mergekit` といった標準化された外部評価・マージツールのクローンとインストールを行います。
* **意図**: 自前実装のバグや仕様の違いを排除し、公式コミュニティツールに依存することで評価の客観性を担保します。

### `data_prep/prepare_datasets.py`
* **役割**: HuggingFace からデータセットをダウンロードし、SFT（Supervised Fine-Tuning）用に `{"instruction": "...", "output": "..."}` の形式に整形するスクリプトです。
* **データ内容**:
  * **Utility側**: `Financial PhraseBank (FPB)` などの金融ドメインデータ。
  * **Safety側**: `AdvBench` や `TrustLLM JailbreakTrigger` の攻撃データに対する安全な拒絶応答。

---

## 2. モデル学習 (Fine-Tuning)

### `fine_tuning/run_lora_ft.py`
* **役割**: 提供されたデータセットを用いて、ベースモデル（Llama-3-8B等）をLoRAでファインチューニングするスクリプトです。
* **特徴**: 
  * 単純な Utility FT と Safety FT の両方を実行可能です。
  * 論文の「Direct Safety FT (Mixed FT)」の比較検証のため、`--utility_dataset_path` と `--safety_dataset_path` を同時に渡し、`--safety_mix_ratio` の比率でデータを混ぜて学習する機能を搭載しています。

---

## 3. マージ実行と提案手法 (SST-Merge)

### `merge/run_mergekit.sh`
* **役割**: 比較対象であるベースライン手法（Task Arithmetic, TIES）を、Arcee.aiの公式 `Mergekit` を用いて実行するスクリプトです。
* **意図**: 既存実装や自作実装のバイアスを排除し、「マージ手法の標準実装で比較した」と主張するための根拠となります。

### `merge/sst_merge_core.py` (提案手法コアロジック)
* **役割**: 提案手法である **SST-Merge** の理論（GEVP）を実装した中核スクリプトです。論文内の数式定義と完全に整合するように実装されています。
* **論文との整合性チェック**:
    1. **FIMの計算**: `compute_diagonal_fim` 関数は、論文式の $\mathbb{E}_{x \sim \mathcal{D}}[(\nabla_\theta \ell)^2]$ の通り、クロスエントロピーLossの勾配二乗をバッチごとに累積・平均して計算しています。
    2. **SST比（GEVP固有値）**: `compute_sst_ratio` は $\lambda_i = F_{h,i} / F_{b,i}$ を計算し、論文の式(10)周辺と整合しています。
    3. **Data-Free SST (新しく追加)**: 今回の整合性確認に伴い、FIMを計算できない環境用に論文で定義されている「タスクベクトル二乗比 $\hat{\lambda}_i = \Delta_{h,i}^2 / \Delta_{b,i}^2$」を計算する `compute_data_free_sst_ratio` 関数を追記実装しました。
    4. **マージ適用 (Interpolation/Additive)**: `apply_sst_merge` では、論文の式 $\theta_{\mathrm{merged}} = \theta_{\mathrm{util}} + \alpha\,(m \odot \Delta_s)$ に従って、Safetyパッチのタスクベクトル（`delta_s`）にマスクを掛けて加算する処理を実装しています。

以上の通り、実装されたスクリプト群は既存のコードを一切変更・破壊することなく独立して動作し、かつ論文内の理論的な定式化と完全に一致していることを確認・保証いたしました。
