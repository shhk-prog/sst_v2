# 評価時における推論崩壊および各種実行時エラーの修正計画（+ 評価スキップ機能追加）

## 概要
評価および実験プロセスにおいて発生していたエラーを修正することに加え、ユーザーからの追加要求に基づき、すでに評価結果が `results/` 内に存在する場合に該当評価コマンドをスキップして実験を再開（レジューム）できる機能を追加します。

---

## 修正詳細と提案内容

### 1. 評価結果が存在する場合のスキップ機能（Resume機能）
実験ランナーである `run_experiments.py` において、`--resume` オプションを追加します。
コマンドを実行する前に、そのコマンドの引数に指定されている出力先ファイル (`--output_file` または `--output_path`) がすでに存在しているかどうかを検知し、存在している場合は評価コマンドの実行を自動でスキップするロジックを `run_cmd` に追加します。

#### 修正ファイル:
- [v3/scripts/run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)

#### 具体的な変更内容:
```python
args = None

def run_cmd(cmd):
    global args
    # --resume が指定されている場合、結果ファイルの存在をチェック
    if args and getattr(args, "resume", False):
        output_file = None
        for i in range(len(cmd) - 1):
            if cmd[i] in ["--output_file", "--output_path"]:
                output_file = cmd[i+1]
                break
        if output_file and os.path.exists(output_file):
            print(f"Result file {output_file} already exists. Skipping command execution.")
            return 0

    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd, text=True)
    if res.returncode != 0:
        print(f"Command failed with exit code {res.returncode}")
    return res.returncode

def main():
    global args
    args = parse_args()
    ...
```

引数パーサーの修正:
```python
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="configs/config.yaml")
    parser.add_argument("--skip_ft", action="store_true", help="Skip fine-tuning phase")
    parser.add_argument("--skip_base_eval", action="store_true", help="Skip base model evaluation")
    parser.add_argument("--skip_merge", action="store_true", help="Skip merge phase")
    parser.add_argument("--skip_merge_eval", action="store_true", help="Skip merged model evaluation")
    parser.add_argument("--limit", type=int, default=10, help="lm-eval limit samples for debugging")
    parser.add_argument("--resume", action="store_true", help="Resume from existing evaluation results")
    return parser.parse_args()
```

---

### 2. モデルの推論崩壊（無限生成ループ）対策
各評価スクリプトでの `model.generate()` において、`eos_token_id=tokenizer.eos_token_id` を明示的に指定するように修正し、EOSトークン検出時に正しく生成を終了させます。

#### 修正ファイル:
- [v3/scripts/eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py#L124-L132)
- [v3/scripts/eval_instruction_datasets.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_instruction_datasets.py#L123-L130)
- [v3/scripts/eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py#L68-L75)

---

### 3. StrongREJECT 評価時の型エラー対策
`eval_safety.py` 内の `eval_strongreject` 関数において、`strong_reject.evaluate` の戻り値 `list[dict]` からスコアを抽出する際、辞書型から値を安全に取り出すように修正します。

#### 修正ファイル:
- [v3/scripts/eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py#L80-L94)

---

### 4. AlpacaEval データセットの読み込みエラー対策
Hugging Face の `datasets` ライブラリのセキュリティ強化に伴うエラーを回避するため、`load_dataset` の呼び出しに `trust_remote_code=True` を明示的に指定します。

#### 修正ファイル:
- [v3/scripts/eval_alpaca.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_alpaca.py#L178-L182)

---

### 5. WizardCoder リポジトリ 404 エラー対策
Hugging Face 上の組織名が `WizardLM` から `WizardLMTeam` に変更されたことに伴い、`configs/config.yaml` の記述を正しいリポジトリ名に更新します。

#### 修正ファイル:
- [v3/configs/config.yaml](file:///mnt/nas/home/hiromi/src/sst_v2/v3/configs/config.yaml#L7-L12)

---

### 6. lm-eval mathタスク評価用の依存パッケージの追加と自動インストール
`minerva_math` 等の数学系タスクを `lm-eval` で読み込む際に発生していた `ModuleNotFoundError: No module named 'antlr4'` を解消するため、`v3/requirements.txt` に依存パッケージを追加したうえで、`eval_utility.py` の開始時に自動で pip インストールを実行するラッパーロジックを組み込みます。

#### 修正ファイル:
- [v3/requirements.txt](file:///mnt/nas/home/hiromi/src/sst_v2/v3/requirements.txt)
- [v3/scripts/eval_utility.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_utility.py#L7-L20)

---

## 検証計画
### 1. 手動検証
修正後、以下の検証用コマンドを個別に実行し、それぞれエラーが発生せず完了することを確認します。

**A. 安全評価の実行 (StrongREJECT 判定エラーおよび推論崩壊の解消確認):**
```bash
python v3/scripts/eval_safety.py \
  --model_path WizardLMTeam/WizardMath-7B-V1.0 \
  --output_file test_output_dir/eval_safety_test.json \
  --task strongreject
```

**B. レジューム機能の動作確認:**
事前に `test_output_dir/eval_safety_test.json` が存在する状態で `--resume` を指定して `run_experiments.py` を実行した際、評価がスキップされることを確認します。
```bash
python v3/scripts/run_experiments.py --resume --limit 1
```
