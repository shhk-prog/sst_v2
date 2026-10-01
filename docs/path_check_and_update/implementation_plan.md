# .envによるパス管理の導入計画

個別のコードにハードコードされている絶対パスを廃止し、`.env` ファイルで定義した環境変数を使用するように修正します。

## 変更内容

### 1. .env ファイルの更新
- 場所: `$HOME/src/.env`
- 内容: プロジェクトのルートパスを定義する変数を追加します。
  ```bash
  SST_HOME="/mnt/nas/home/hiromi/src/sst_v2"
  ```

### 2. v1 スクリプトの修正
以下のファイルに含まれる古いパス（`/mnt/iag-02/...`）を、環境変数 `SST_HOME` を使った形式に置き換えます。

#### 修正対象ファイル例:
- `v1/run_all_experiments.sh`
- `v1/scripts/evaluation/eval_sft_checkpoints.py`
- 他、grep で抽出されたファイル群

### 3. v2 スクリプトへの適用
- 現在相対パスで記述されている箇所も、必要に応じて `$SST_HOME` を起点とした記述に整理し、実行場所によらず正しく動作するようにします。

## 具体的な修正手法

### Bash スクリプトの場合
`.env` を source した後、変数を展開します。
```bash
source "$HOME/src/.env"
cd "$SST_HOME/v1"
```

### Python スクリプトの場合
`python-dotenv` または `os.environ` を使用します。
```python
import os
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/src/.env"))
project_root = os.getenv("SST_HOME")
```

## オープンクエスチョン
- 環境変数名は `SST_HOME` でよろしいでしょうか？（より適切な名前があれば変更します）
- `v2` のスクリプトについても、現在相対パス（`../../` など）で書かれている部分を `$SST_HOME` を使った絶対パス指定に切り替えますか？それとも現状維持（相対パス）を優先しますか？

## 修正計画

### [Environment]
- [MODIFY] `$HOME/src/.env`

### [v1 Scripts]
- [MODIFY] 各 `.sh`, `.py` ファイル

## 確認方法
- 修正後に `.env` のパスを変更しても、スクリプトが正しくパスを認識することを確認します。
