# Hirundo と Secure Merge の比較検証実験計画

本計画は、LLM の重みから直接、危険な知識や脆弱性を「忘れさせる」マシンアンラーニング基盤 **Hirundo** と、安全モデルの重み差分を良性モデルへ統合する **Secure Merge**（および SST-Merge）の性能・防御効果・有用性のトレードオフを定量的に比較評価するための実験計画です。

既存 of コードベース（`v3/`）を一切変更せず、独立した新規検証スクリプトおよび設定ファイルを導入することで、既存の実験環境の健全性を維持したまま検証を実行します。

---

## User Review Required

> [!IMPORTANT]
> **比較用モデルの選定**
> 本検証では、Hugging Face 上で公開されている `hirundo-io` の Hirundo 調整モデルと、それに対応するオープンベースモデルを使用します。
> 以下のいずれかのペアを主軸として実験を行います。環境のリソースおよび API の利用状況に合わせて、検証対象を絞り込むか順次適用します。
> 1. **Llama 3.2-3B ペア** (軽量で実行しやすい)
>    - ベースモデル: `meta-llama/Llama-3.2-3B-Instruct`
>    - Hirundoモデル: `hirundo-io/Llama-3.2-3B-Instruct-improved-security`
> 2. **Gemma 3 1B ペア**
>    - ベースモデル: `google/gemma-3-1b-it`
>    - Hirundoモデル: `hirundo-io/Gemma-3-1B-it-Instruction-Following-Unlearned`
> 3. **Gemma 4 E4B ペア** (論文等で言及されている hardened モデル)
>    - ベースモデル: `google/gemma-4-E4B-it` (もしくはそれに相当するモデル)
>    - Hirundoモデル: `hirundo-io/gemma-4-E4B-it-reduced-prompt-injection`

> [!WARNING]
> Hugging Face からモデルをダウンロードする際、特に Llama および Gemma 系のモデルは Hugging Face の利用規約（Gated model）の同意および `HF_TOKEN` が必要になります。検証実行前に環境変数 `HF_TOKEN` が適切に設定されていることを確認する必要があります。

---

## Open Questions

- **検証に用いるベンチマークのサイズ制限（サンプル数）について**:
  - `eval_safety.py` などと同様に、評価時間短縮のために各タスクの評価プロンプト数を `--limit 100` 等で制限して初期評価を進めるか、あるいはフルのデータセットで実行するか。
  - 初期段階では `--limit 50` もしくは `100` での動作確認と初期指標算出を推奨します。

---

## Proposed Changes

### 実験用新規コンポーネント

#### [NEW] [eval_hirundo_unlearning.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_hirundo_unlearning.py)
Hirundoモデルの評価、Secure Mergeとのマージモデルの作成、ガードレールとの複合防御の評価を独立して行う新規 Python スクリプトです。
主な機能：
1. **ASR 評価**: 指定したモデル（ベース、Hirundo、Secure Merge、マージ複合）に対して、`harmbench` / `jailbreakbench` などのタスクを実行し、脱獄攻撃成功率（ASR）を算出する。
2. **Utility 評価**: lm-evaluation-harness などを内部で呼び出すか、軽量な評価タスクを実行して有用性（GSM8K、MMLU など）の劣化幅を測定する。
3. **複合防御 (Hirundo + Guardrail)**: WildGuard などの外付け分類器、または安全システムプロンプトの追加適用による ASR の変動を測定する。
4. **相互作用評価 (Hirundo + Secure Merge)**: Hirundo モデルにさらに安全LoRAマージを適用した際の挙動確認。

#### [NEW] [config_hirundo.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v3/configs/config_hirundo.yaml)
Hirundo 比較検証用モデル、評価タスク、ハイパーパラメータなどを定義する専用の YAML 設定ファイルです。

---

## Verification Plan

### Automated Tests
- 新規作成した `eval_hirundo_unlearning.py` がエラーなく動作し、ベースラインおよび Hirundo モデルの ASR を算出できることを検証します。
- 実行コマンド例：
  ```bash
  python v3/scripts/eval_hirundo_unlearning.py --config v3/configs/config_hirundo.yaml --limit 20
  ```

### Manual Verification
- `results/hirundo_analysis/` ディレクトリに評価結果（JSON）および Pareto トレードオフのプロット（PNG/CSV）が正常に出力されることを確認します。
- 以下の観点で出力データをチェックします：
  1. ASR の低減幅（Hirundo vs Base vs Secure Merge）
  2. 通常タスク（MMLU等）の性能スコア
  3. 各攻撃タイプに対する拒否反応のカバー範囲（防御集合の差分）
