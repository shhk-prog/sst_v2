# 正確な実験のための実装計画（簡易ベンチからの昇格）

本計画は、現状の `measure_overhead.py` / `analyze_fim_overlap.py` / `eval_logic_bench.py` が簡易的であること（詳細は `experimental_results_accurate_report.md`）を前提に、**論文記述・査読・再現性**に耐える実験へ置き換えるための工程を定義する。

---

## 0. 目的と非目標

### 0.1 目的

1. **計測プロトコルの単一化**: モデル、LoRA 対象、データローダ、シード、GPU ウォームアップ、バッチ構造を論文・本番パイプラインと一致させ、数値の意味を一意にする。
2. **FIM 推定コストの正当化**: 「ダミー 1 ステップ比」ではなく、**実データ上の N サンプル FIM の総時間**、および **Safety SFT と同条件の学習ステップ／1 epoch の実測または線形外挿**を併記できるようにする。
3. **Utility / Safety FIM 幾何の頑健性**: データ定義を明示し、**サンプル数・上位 k%・シード**に対する感度と区間推定を付ける。
4. **知能指標の独立検証**: ARC 50 件・先頭 1 文字一致から脱却し、**テンプレ固定の多肢・採点ルール**と十分な件数を確保する。
5. **失敗モードの証拠化**: Over-refusal / Collapse をルールベースでタグ付けし、**付録用に固定 ID のログ**を出力する。

### 0.2 非目標（スコープ外として明記）

- **Llama Guard 3 等の本番ガードレールの同一条件ベンチ**（インフラ依存）。計画では「オプション拡張」に留める。
- **DPO / RLHF のフル再学習比較**（嗜好データ・人間評価のコスト）。必要なら「引用＋小規模プロトタイプ」の二段構えとする。

---

## 1. 現状ギャップ（対応表）

| 領域 | 現状 | 正確化で満たす条件 |
| :--- | :--- | :--- |
| コスト | ランダムバッチ・20 反復・L2 7B | **論文と同一ベースモデル**、**実コーパス**、**ウォームアップ後の総時間**、SFT は **optimizer 込み**と **FIM 累積**を別計測 |
| FIM 重なり | Alpaca 50 vs CSV 50、L2 7B、LoRA 幅がベンチと不一致 | **論文で主張する分布**（例: RepliQA 系 utility / Jailbreak 系 safety）に揃えるか、**両方を実施して表を分ける** |
| 論理評価 | ARC 50・先頭文字一致・3 モデルのみ | **件数増**、**プロンプトテンプレ統一**、可能なら **logprob 採点**または **厳密な抽出正規表現** |
| 再現性 | ハードコード CUDA、相対パス依存 | **YAML 設定**、**シード**、**環境メタデータ**（CUDA/PyTorch/コミットハッシュ）の自動記録 |
| データ移動コスト | 未実装 | **仮定を明示したバイト数モデル**（下記 §6）をスクリプト化 |

---

## 2. 共通インフラ（フェーズ A：最優先）

### 2.1 実装物

| 成果物 | 役割 |
| :--- | :--- |
| `configs/experiments/robustness_eval.yaml`（名称例） | `base_model`, `adapter_paths`, `lora_target_modules`, `max_length`, `batch_size`, `num_workers`, `seed`, `cuda_device`, データパス |
| `scripts/benchmarks/run_experiment.py`（名称例） | 設定読み込み → ログディレクトリ作成 → 子実験ディスパッチ |
| `scripts/benchmarks/_logging.py` | `git rev-parse HEAD`, `pip freeze` 要約, `torch.version.cuda`, GPU 名, 開始終了時刻 ISO8601 を `run_meta.json` に保存 |

### 2.2 受け入れ基準

- 同一 YAML を指定した二回実行で、**決定的処理**（同一シード・同一データ順）における主要指標が一致する、または浮動差が文書化閾値内である。
- すべての新スクリプトが **`python ... --config path/to.yaml`** で動く。

---

## 3. フェーズ B：FIM および学習コストの実測

### 3.1 新スクリプト案: `scripts/benchmarks/measure_fim_and_sft_cost.py`

**計測ブロック（いずれも実データ）**

1. **ウォームアップ**: 同一バッチで `W` 回 forward（推奨 W=5〜10）、`torch.cuda.synchronize()` 後に本計測。
2. **FIM 総時間**: 論文で主張する **N サンプル**（例: 100、500、可変）について、既存 `fim_validation_ablation.py` 系と同じ **loss.backward ＋勾配二乗のパラメータ単位累積**を行い、`t_fim_total`, `t_fim_per_sample_mean`, `t_fim_per_sample_std` を記録。
3. **SFT 比較軸（二段）**
   - **軸 1（公平な 1 ステップ）**: 同一 `batch` で `forward+backward+optimizer.step` の平均時間 `t_sft_step`（反復 M≥50）。
   - **軸 2（運用コスト）**: 実際の Safety FT の **1 epoch 相当ステップ数 × `t_sft_step`**、または既存ジョブの `trainer_state.json` から **実 wall** を取り込み `t_sft_1epoch_wall` として別行で報告（推測と実測を混ぜない）。

**出力**

- `artifacts/benchmarks/fim_sft_cost_<timestamp>.json` に上記スカラー＋設定ハッシュ。
- 論文用 Markdown 表を生成するオプション `--emit-table docs/...md`。

### 3.2 受け入れ基準

- 論文に書く一文が **JSON のキーと 1 対 1** で対応する（モデル名・N・データセット名が一致）。
- 「FIM が SFT より軽い／重い」は **どの軸（ステップ比 vs 総作業量比）** の話か表頭で分離されている。

---

## 4. フェーズ C：Utility / Safety FIM 重なりの頑健化

### 4.1 新スクリプト案: `scripts/analyze_fim_overlap_rigorous.py`

**データ定義（必須の明示）**

- **Primary スイート**: 論文主張に使う分布（例: RepliQA 評価用 JSON からローダ構築、Jailbreak 評価用プロンプト集合）。
- **Secondary スイート**（任意）: Alpaca 等。結果は **別表・別 JSON** に出力し、本文で混同しない。

**統計**

- サンプル数 `N ∈ {100, 500, 2000}` のスイープ（計算資源に応じ段階化）。
- **上位 k%** を `k ∈ {1, 5, 10, 20}` で Jaccard を記録。
- **ブートストラップ**（例: 200 回、サンプル復元抽出）で Jaccard の 95% 区間（オプションで Spearman も同様）。
- **層別**: 層ごとに FIM 質量を正規化し、層レベル Jaccard／cosine をオプション出力（「全体 Spearman が高いが集合がずれる」現象の説明材料）。

### 4.2 モデル・LoRA

- **マージ実験と同一**のベース重み・**同一 target_modules** で FIM を取る（現状のベンチと overlap スクリプトの不一致を解消）。

### 4.3 受け入れ基準

- 論文の「RepliQA / Jailbreak」と主張するなら、**そのローダをコードに存在させ、設定 YAML でパス指定**する。
- 少なくとも **1 指標は区間付き**（ブートストラップ or 複数シード）で報告できる。

---

## 5. フェーズ D：論理・知能評価の強化

### 5.1 新／改修スクリプト案: `scripts/evaluation/eval_reasoning_suite.py`

**データ**

- **ARC-Challenge**: `test` 全件、または検証で十分な **500 件の層化サンプル**（難易度タグがあれば均等化）。
- **MMLU**（採用する場合）: **STEM サブセットのみ**（ユーザー合意済み想定）で `mmlu` ローダー、**5-shot テンプレ**を固定（論文にテンプレ全文またはハッシュを記載）。

**採点**

- 多肢問題: **最初に出現する A/B/C/D 形式**を正規表現で抽出、なければ **invalid** として別カウント（先頭 1 文字一致のみは廃止）。
- 集計: `accuracy`, `invalid_rate`, `refusal_rate`（拒絶フレーズ辞書は `analyze_utility_loss.py` と共通化）。

**モデル**

- 論文と整合する **Baseline / SFT_ckpt / SST_merge_ckpt** を YAML で列挙し、現状の 3 点に限定しない（TA/TIES/DARE を追加するかは工数見合いでフェーズ分割）。

### 5.2 受け入れ基準

- 各モデルについて **生ログ JSONL**（`id`, `prompt`, `raw_output`, `parsed_answer`, `correct`）が保存される。
- ROUGE 系評価と**独立した**「知能指標」表を自動生成できる。

---

## 6. フェーズ E：失敗モード・付録ログのパイプライン

### 6.1 実装物

| 成果物 | 内容 |
| :--- | :--- |
| `scripts/analysis/tag_failure_modes.py` | 出力を **Over-refusal** / **Collapse** / **Benign** / **Other** に分類（反復 n-gram、拒絶フレーズ、非 ASCII 比率、最大ラン長などの合成ルール）。 |
| `scripts/analysis/pick_appendix_examples.py` | 各手法・各モードから **固定シードで 3 件**抽出し、`appendix_failure_examples.md` を生成。 |

### 6.2 受け入れ基準

- 査読者が **プロンプト ID で再実行**できる形で、同じ例が再現される。

---

## 7. フェーズ F：組織間データ移動の仮想コスト（オプション）

### 7.1 方針

- **観測可能な量**のみを入力: Utility コーパスのバイト数推定、Safety コーパスのバイト数、LoRA アダプタ safetensors のバイト数、FIM 推定に必要な「勾配統計を送る場合」のバイト数（設計仮定）。
- **単価**（$/GB や社内転送コスト）は設定ファイルで **仮定**として与え、論文では「Illustrative」として脚注化。

### 7.2 成果物

- `scripts/benchmarks/estimate_transfer_cost.py` → `transfer_cost_model.json` と前提一覧 `ASSUMPTIONS.md`（短い箇条書きで可）。

---

## 8. 工数・依存関係（推奨順序）

```text
A（設定・ログ） → B（コスト実測） → C（FIM 重なり） → D（推論スイート） → E（失敗モード） → F（転送コスト・任意）
```

| フェーズ | おおよその工数感 | 主な依存 |
| :--- | :--- | :--- |
| A | 0.5〜1 日 | なし |
| B | 1〜2 日 | 実データローダ、GPU |
| C | 2〜4 日 | B と LoRA 定義の共有 |
| D | 2〜5 日 | モデル複数ロード、ディスク |
| E | 1〜2 日 | D の JSONL |
| F | 0.5 日 | ファイルサイズ計測のみ |

---

## 9. 論文・レポートとの同期ルール

1. **数値の単一ソース**: 生成された `artifacts/...json` を唯一の根拠とし、`論文.md` / `detailed_robustness_report.md` は **生成表を貼るかスクリプトで同期**する。
2. **`experimental_results_accurate_report.md`**: 各フェーズ完了ごとに「確定した事実」節を追記し、旧簡易数値は「deprecated」とマークする。

---

## 10. 完了定義（Definition of Done）

- [ ] すべての新計測が **YAML 駆動**で、**`run_meta.json`** 付き。
- [ ] 論文に載せる表の各行が **JSON のキー**に対応し、モデル名・N・データセット名が**本文と矛盾しない**。
- [ ] FIM 重なりについて **少なくとも 1 つ**区間推定または多 N 曲線が付いている。
- [ ] 論理評価で **invalid 率**が報告され、採点ルールがリポジトリ内にコードとして固定されている。
- [ ] 付録用失敗例が **ID 固定**で 3 件以上／モード抽出可能。

---

*本計画は `experimental_results_accurate_report.md` の「測っていないもの」を埋めることを主目的とする。実装着手時はフェーズ A から順に PR／コミット単位で切るとレビューしやすい。*
