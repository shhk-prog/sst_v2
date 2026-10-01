# 修正内容の確認 (Pareto AUCスクリプトの拡張)

`v3/scripts/pareto_auc.py` に対し、マージターゲットごとの集計、パレートフロンティア計算、プロットの可視化が行えるよう以下の拡張を行いました。

## 変更内容

### 1. コマンドライン引数 `--merge_target` の追加
以下の選択肢を指定できるオプションを追加しました。
- `all` (デフォルト: フィルタリングなし)
- `base` (結合文字列を含まない、純粋なベースモデルのみ)
- `safety+math`
- `safety+code`
- `safety+medical`
- `safety+math+code+medical`

### 2. ロードデータのフィルタリング
ファイル名に基づいてマージドメインの組み合わせを判定し、指定された `--merge_target` に一致するもののみを処理対象とするようロジックを実装しました。

### 3. 出力ファイル名の上書き防止
出力されるCSVファイル（要約データおよびレコード）やプロット画像（PNGファイル）のファイル名に、指定されたターゲット名がサフィックスとして自動付与されるようにしました（例: `pareto_frontier_harmbench_safety+math.png`）。これにより、異なるターゲットドメインで連続実行した際の上書きを防ぎます。

### 4. 17指標の完全個別ロード対応
ご指定いただいた全17個の評価タスク・指標に完全対応しました。
- **PPL (Perplexity) の対応**:
  - `Evol-Instruct-Code (PPL↓)` および `MedAlpaca (PPL↓)` を集計対象に追加しました。
  - PPLは値が低いほど優れている（ASRとは逆で、Utilityとして扱うため高いほど良いというパレートの前提と逆行する）ため、スコアをマイナス（`-perplexity`）として記録し、パレート計算（AUC）の最大化モデルが正常に稼働するように処理しています。
- **個別タスクの分離抽出**:
  - `utility_{domain}.json` 内の `results` から、ドメイン内の個別タスク（例: `human_eval`, `mbpp`, `medqa`, `pubmedqa`, `gsm8k`, `minerva_math500`, `ifeval`, `mmlu` 等）の評価値を個別に抽出し、ドメイン平均とは別に個別の utility 指標レコードとして集計できるようにしました。

### 5. YAML Config の動的読み込み対応
評価対象となる安全タスク名やユーティリティタスクのドメイン名・個別タスク定義を、ハードコードせずに YAML ファイルから動的にロードする仕組みを追加しました。
- `--config` 引数の追加 (デフォルト: `configs/config_main.yaml`)。
- **実用評価結果ファイルパスの修正**:
  - 実用指標（GSM8KやHumanEval等）のファイル命名規則が `{base_name}_utility_{domain}_{task}.json` （例: `utility_math_gsm8k.json`）になっていることに対応するため、config上のドメイン（`math` 等）と個別タスク名（`gsm8k` 等）を組み合わせたファイルパスを正しく生成して検索・ロードするように修正しました。これにより、各ユーティリティ指標が漏れなくロードされます。
- ロードした `utility_task_groups` に基づき、指定されたドメインおよびタスク名に一致するスコアのみを厳密にフィルタリングして抽出します。これにより、config上の実験定義の変更に自動で追従します。

### 6. メソッド名パースのバグ修正
ファイル名のプレフィックス `sst_merge_v3_main_` が原因で、マージアルゴリズム名がすべて `sst` として誤判定され、同一手法として集計されてしまうバグを修正しました。
- 既知のベースライン/提案手法リストを内部定義し、プレフィックスに依存せず正確に `dare`, `ties`, `della` 等のアルゴリズム名を抽出・区別できるように `parse_model_params` をアップデートしました。
- これにより、CSVファイル内の `method` 列に正しいアルゴリズムが記録され、手法・実験条件（`alpha` や `seed`）ごとに区別されたパレート分析が可能になります。

### 7. 出力ディレクトリの自動作成
- [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) でMarkdownファイルを出力する際、および [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py) で結果のCSVファイル (`raw_csv`) を書き出す際に、指定した親ディレクトリが存在しない場合にエラーを起こさず自動でディレクトリを作成（`os.makedirs`）して追記できるようにバグを修正しました。

### 8. 評価スコア抽出優先度の修正（複合キーバグ修正）
- GSM8K などの評価結果において、`exact_match,strict-match` (0.0) と `exact_match,flexible-extract` (41.5%等) が混在している場合に、部分一致によって誤って `strict-match` (0.0) を優先して抽出してしまっていたバグを修正しました。
- `extract_utility_score` の `preferred_keys` の先頭に `exact_match,flexible-extract` や `math_verify,flexible-extract` などの複合キーを最優先で配置するように修正し、本来の正しい評価スコアが確実に記録・集約されるようにしました。

### 9. フィルタリングとロード順序の適正化
- `load_evaluation_data` において、`merge_target` による判定の前に全ファイルの JSON ロードおよび失敗判定 (`is_failed_result`) を行っていたため、対象外マージグループの mock ファイルに対する警告ログが大量に出力されるノイズが発生していました。
- 先にファイル名から `merge_target` を判定し、対象外の場合はサイレントに `continue`（スキップ）してからファイルをロードするように処理の順序を変更しました。これにより、実行時の無駄なファイルオープンが抑止され、不要な警告ログ出力が完全に解消されました。

### 10. 失敗モデルのテーブル（比較表）組み込み対応
- 評価プロセスが失敗または未完了だったモデル（例: `mergealign`）について、従来は解析から完全に除外（スキップ）していましたが、表の中で漏れなく表示できるように仕様を変更しました。
- `is_failed_result` に該当した場合や、実用評価 JSON が存在しない場合であっても、スコア値を `None`（空）としたレコードを生成して CSV に記録するようにし、パレート描画処理の直前で `dropna` で取り除くことでプロット計算に不具合を起こさないようにしました。
- これにより、[generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) でMarkdown比較表にする際に、失敗したモデルの行も自動で組み込まれ、各スコアが `"-"` （ハイフン）で埋められた状態で行が生成されるようになります。

### 11. テーブル列名（ヘッダー名）のフレンドリー化（高低インジケータ統合）
- [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) で Markdown の比較表を出力する際、ヘッダーに表示される列名（`gsm8k`, `humaneval` などの小文字識別子）を人間に読みやすく、かつ高低（↑/↓）の意味が一目でわかる正式名称に自動でリネーム（マッピング）してテーブル化するように修正しました。
  - 例：`gsm8k` -> `GSM8K (Flex EM↑ %)`、`humaneval` -> `HumanEval (Pass@1↑ %)` 等

### 12. インデント崩れによる SyntaxError の修正
- 前回の `merge_target` フィルタリング条件順序の入れ替えの際、ループ最外周の `try-except` の対応関係とインデントが一部ずれてしまい、Line 370 付近で発生していた `SyntaxError` をインデント修復により解消しました。

### 13. 全体比較およびマージ手法別テーブルの分割出力対応
- [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) で Markdown 表を生成する際、全モデルをまとめた「総合比較テーブル」に加え、マージアルゴリズム（`DARE`, `TIES`, `DELLA`, `TASK ARITHMETIC` 等）ごとに自動でデータをグループ化して「手法別個別テーブル」を分割生成する機能を追加しました。
- 重複追記を避けるため、出力ファイルへの書き込み方法を追記 (`"a"`) から新規書き出し/上書き (`"w"`) に変更し、実行するたびに最新の状態でテーブルが綺麗に整理・更新されるように堅牢化しました。

---

## 実行コマンド例

### 1. ベースモデルのみの集計・可視化
```bash
python3 v3/scripts/pareto_auc.py \
  --results_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320 \
  --output_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/pareto_summary \
  --merge_target base
```

### 2. safety+mathマージモデルのみの集計・可視化
```bash
python3 v3/scripts/pareto_auc.py \
  --results_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged \
  --output_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/pareto_summary \
  --merge_target safety+math
```

### 3. safety+codeマージモデルのみの集計・可視化
```bash
python3 v3/scripts/pareto_auc.py \
  --results_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged \
  --output_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/pareto_summary \
  --merge_target safety+code
```

### 4. safety+medicalマージモデルのみの集計・可視化
```bash
python3 v3/scripts/pareto_auc.py \
  --results_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged \
  --output_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/pareto_summary \
  --merge_target safety+medical
```

### 5. 全てのマージ対象を個別に順次集計するシェルスクリプトの例
```bash
for target in base safety+math safety+code safety+medical safety+math+code+medical; do
  echo "Processing: $target"
  python3 v3/scripts/pareto_auc.py \
    --results_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/merged \
    --output_dir /mnt/nas/home/hiromi/src/sst_v2/v3/results/debug_limit320/pareto_summary \
    --merge_target "$target"
done
```

---

## 網羅された全モデル・全指標 Markdown テーブルの自動生成手順

実験条件（アルゴリズムや `alpha`）ごとに区別された全てのモデルを一つの表にまとめるには、作成した [generate_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/generate_tables.py) を実行します。

### 実行コマンド例

`safety+math` の全マージモデルおよび実験条件の集計表を `docs/pareto_frontier_analysis/walkthrough.md` に追記する場合：

```bash
python3 v3/scripts/generate_tables.py \
  v3/results/pareto_summary/debug_limit320/safety+math/pareto_loaded_records_safety+math.csv \
  docs/pareto_frontier_analysis/walkthrough.md
```

これにより、すべてのマージ手法および `alpha` ごとの 17 指標を網羅した Markdown テーブルが、指定したドキュメントファイルの末尾に自動的に追加・追記されます。
他のマージターゲット（`safety+code` 等）についても、CSVを指定して同様にテーブルを自動生成・統合できます。

