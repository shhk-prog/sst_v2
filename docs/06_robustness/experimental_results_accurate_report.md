# SST-Merge 安全性・頑健性関連：実験結果の正確な記録

本書は、`detailed_robustness_report.md` や `論文.md` の記述ではなく、**リポジトリ内のスクリプトと生成物（JSON）に基づく事実**として実験条件と数値をまとめたものである。再現性と査読対応のため、**論文本文と食い違う箇所は第5章で明示**する。

---

## 0. 成果物一覧（生成ファイル）

| ファイル | 生成元スクリプト | 内容 |
| :--- | :--- | :--- |
| `scripts/benchmarks/benchmark_results.json` | `scripts/benchmarks/measure_overhead.py` | SFT 1ステップ vs FIM相当処理の平均 Wall-clock |
| `scripts/benchmarks/fim_overlap_results.json` | `scripts/analyze_fim_overlap.py` | Utility / Safety 別 FIM の順位・集合の比較指標 |
| `scripts/benchmarks/logic_eval_results.json` | `scripts/evaluation/eval_logic_bench.py` | ARC-Challenge 部分集合の正答率とケーススタディ生成文 |

**前提**: 各スクリプトは作業ディレクトリをリポジトリルート `sst_merge_v5/` とし、上記相対パスで JSON を書き出す想定で実装されている。

---

## 1. マイクロベンチマーク：SFT 1ステップ vs FIM 相当 1反復

### 1.1 実装の要約

- **スクリプト**: `scripts/benchmarks/measure_overhead.py`
- **モデル**: `meta-llama/Llama-2-7b-hf`（FP16）
- **適用**: PEFT LoRA（`r=16`, `alpha=32`, 対象 `q_proj`, `v_proj`, `k_proj`, `o_proj`）
- **データ**: 実データではなく、語彙サイズ 32000、`batch_size=4`, `seq_len=128` の**ランダム整数トークン**と同一テンソルを `labels` に使用
- **計測**: 各ループ **20 回**、GPU 同期後の `time.time()` で区間計測し、**1 反復あたりの平均秒**
  - **SFT 側**: `forward` → `backward` → `AdamW.step`
  - **FIM 側**: `forward` → `backward` → 全 `requires_grad` パラメータについて `grad ** 2` を参照（蓄積はしないが、勾配二乗参照でコストを近似）

### 1.2 実測値（`benchmark_results.json`）

| 指標 | 値 |
| :--- | ---: |
| `sft_step_avg`（秒／ステップ） | 0.210155499 |
| `fim_step_avg`（秒／反復） | 0.135813200 |
| `overhead_ratio`（= `fim_step_avg` / `sft_step_avg`） | **0.646251** |

**読み替え**: この設定では、記録された 1 反復あたり時間は **FIM 近似ループの方が SFT 1 ステップより短い**（比率約 0.65）。これは **optimizer.step の有無**およびループ内処理の差によるものであり、「FIM が SFT より常に軽い」と一般化する根拠にはならない。

### 1.3 本ベンチで測っていないもの（明示的な限界）

- **実データ**上の 100 サンプル（または任意 N サンプル）FIM の**総 Wall-clock**
- **LoRA 1 epoch** 全体の学習時間
- **組織間データ移動のバイト数・金額**などのコストモデル
- **Llama-3.1-8B** など別アーキテクチャでの同条件再計測

---

## 2. Utility / Safety 二分布における対角 FIM の比較

### 2.1 実装の要約

- **スクリプト**: `scripts/analyze_fim_overlap.py`
- **モデル**: `meta-llama/Llama-2-7b-hf`（FP16）
- **LoRA**: `r=16`, `alpha=32`, 対象に **`gate_proj`, `up_proj`, `down_proj` を含む**（§1 のベンチマークより広い）
- **Utility 分布**: Hugging Face `tatsu-lab/alpaca` の `train` 分割を整形した `text` フィールド
- **Safety 分布**: `../data/response_dataframe.csv` または `./data/response_dataframe.csv`（存在する方）を読み、`prompt` / `response` から `text` を構成
- **サンプル数**: 各分布 **最大 50 サンプル**（`compute_fim_diag(..., num_samples=50)` を二度呼び出し）
- **FIM 定義**: 各サンプルで損失に対する勾配を計算し、パラメータごとに **勾配の二乗を加算**し、最後にサンプル数で平均（対角の経験的 Fisher の典型的な近似）
- **指標**:
  - 全 LoRA パラメータをフラット化したベクトル間の **スピアマン順位相関**
  - 各分布で **上位 10%** のパラメータインデックス集合の **Jaccard 係数**（`intersection / union`）

### 2.2 実測値（`fim_overlap_results.json`）

| 指標 | 値 |
| :--- | ---: |
| `spearman_correlation` | **0.960477** |
| `jaccard_top_10v10` | **0.499674** |
| `overlap_count`（上位10% 交集合の要素数） | 2,663,972 |
| `total_top_k`（一方の上位10% の要素数） | 3,997,696 |

### 2.3 解釈上の注意（査読用）

- **スピアマンが高い**: パラメータ全体の順位として、Utility 側と Safety 側の FIM 強度は**大枠で似た形**になりやすい（スケールや層構造の共通性）。
- **Jaccard が約 0.5**: 「最も感度が高い」とされる **上位 10% の集合**に限ると、両分布で指す座標の**重なりは約半数**であり、「急所集合のかなりの部分が分布依存で入れ替わる」ことを示す。
- 論文や他文書で **「RepliQA / Jailbreak」** と書く場合、**本スクリプトのデータソース（Alpaca + CSV）は別物**である。数値を引用するときはデータ定義を揃える必要がある。

---

## 3. 論理推論タスク（ARC-Challenge）短縮評価

### 3.1 実装の要約

- **スクリプト**: `scripts/evaluation/eval_logic_bench.py`
- **ベースモデル**: `meta-llama/Llama-3.1-8B-Instruct`
- **データ**: `ai2_arc` の `ARC-Challenge` / `test` 先頭 **50 件**のみ
- **正答判定**: 生成文字列の**先頭文字**を正解ラベル `answerKey` と大文字小文字無視で比較
- **評価モデル**:
  1. **Baseline**: アダプタなし
  2. **SFT_Epoch_1**: `models/finetuned/adapters/FT_model/Safety_FT_Baseline_on_A5/checkpoint-15` をロードし `merge_and_unload`
  3. **SST_Merge_k20**: `models/merged/sst_merge/adapters/merge_adapters/A5_A7_sst_k20_a0.5_adapter` を同様にマージ
- **ケーススタディ**: 5 件の固定英語プロンプト（熱力学説明、Fibonacci スクリプト、有害依頼拒否、火星の夕焼け、窃盗の倫理）に対する `generate(max_new_tokens=256)` の全文を JSON に保存

### 3.2 実測値（`logic_eval_results.json` から集約）

| モデル名（JSON キー） | ARC-Challenge（50 件）正答率 |
| :--- | ---: |
| `Baseline` | **0.66** |
| `SFT_Epoch_1` | **0.68** |
| `SST_Merge_k20` | **0.82** |

### 3.3 ケーススタディに関する事実メモ（断定を避ける）

- **SFT_Epoch_1** は、プロンプト「火星の夕焼けの色」の応答で、**事実上の拒否・話題回避に近い**文言（例: 仮想イベントに情報提供できない、等）が含まれる。**これは ARC 数値とは独立した定性観察**であり、「過剰拒否」の正式な定義付きカウントではない。
- **SST_Merge_k20** の一部応答では、**ユーザー発話の模倣や多ターン風の追記**が見られ、対話形式プロンプトとの相互作用としての生成癖が観測される。ARC の先頭文字一致スコアとは別次元の挙動である。

---

## 4. 再現手順（参考）

リポジトリルートを `sst_merge_v5/` とする。

```bash
# GPU 番号は各スクリプト内の CUDA_VISIBLE_DEVICES に依存（既定は "2"）
python scripts/benchmarks/measure_overhead.py
python scripts/analyze_fim_overlap.py
python scripts/evaluation/eval_logic_bench.py
```

- 初回はモデル・データセットのダウンロードが必要
- `analyze_fim_overlap.py` は Safety CSV のパス解決に依存する
- `eval_logic_bench.py` はローカルにチェックポイントが存在することを前提とする

---

## 5. `論文.md` 等との対応関係（整合性チェックリスト）

| 論文・周辺文書で言いがちな主張 | 実装・JSONに基づく正確な状態 |
| :--- | :--- |
| FIM コストを **Llama-3.1-8B** で実測 | マイクロベンチは **Llama-2-7b** |
| **100 サンプル**の FIM 時間 | マイクロベンチは **ダミーバッチ 20 反復の平均**；重なり実験は **各 50 サンプル** |
| Utility/Safety FIM が **RepliQA / Jailbreak** | 重なり実験は **Alpaca / response_dataframe 由来** |
| 組織間データ移動の**バイトコスト表** | **未実装**（該当スクリプトなし） |

査読用には、**論文側の文言を本レポートの条件に合わせて修正する**か、**スクリプトを論文記述に合わせて改修したうえで JSON を更新する**のいずれかが必要である。

---

## 6. 一言まとめ

- **再現可能な数値**として確定しているのは、(1) Llama-2-7B LoRA 上のマイクロベンチ比率 **約 0.646**、(2) Alpaca vs Safety CSV に基づく FIM で **Jaccard ≈ 0.500**・**Spearman ≈ 0.960**、(3) Llama-3.1-8B-Instruct 上の **ARC-Challenge 50 件**で **0.66 / 0.68 / 0.82**、の三点である。
- それ以外の運用コストや MMLU 全件評価などは、**本レポートの範囲外**（未実施または別実験）として扱うのが正確である。

---

*最終更新: リポジトリ上のスクリプト・JSON の内容に基づき整理（JSON のタイムスタンプは環境依存のため本書では言及しない）。*
