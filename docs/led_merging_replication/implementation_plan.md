# LED-Merging 再現実験の実装計画

Qianli Ma et al. (ACL 2025) による論文 **"LED-Merging: Mitigating Safety-Utility Conflicts in Model Merging with Location-Election-Disjoint"** の再現実験を、仮想環境 `venv_LED` を構築して実行するための計画です。

---

## ユーザーレビューが必要な事項

> [!IMPORTANT]
> - 本再現実験では、Meta-Llama-3-8B（ベース、Instruct、Math、Code等）を使用します。Hugging Face Hubからこれらのモデルを自動ダウンロードするため、実行するマシン上で事前に `huggingface-cli login` 等によるログインが完了している必要があります。また、Llama-3ファミリーへのアクセス権限がHugging Faceアカウントに付与されていることをご確認ください。
> - 再現実験の実行にはGPUリソースと、モデルのダウンロードおよびマージ成果物の保存のために約100GB程度のディスク空き容量が必要です。

---

## オープンな質問

> [!NOTE]
> 特にありません。承認をいただきましたら、変更ファイルの適用と実行用シェルスクリプトの作成に進みます。

---

## 提案する変更内容

Hugging Face Hub からモデルやデータセットを自動的に取得し、ローカルへのデータセット手動配置やモデルの手動ダウンロードを不要にするための修正を行います。

### 1. データセットの自動ダウンロード対応

#### [MODIFY] [data.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/locate/lib/data.py)
- `get_code()` 内で、存在しないローカルファイル `data/humaneval.parquet` ではなく、Hugging Face Hub から `openai_humaneval` データセットの `test` スプリットを直接ロードするように修正します。
- `get_math()` 内で、存在しないローカルファイル `data/train-00000-of-00001.parquet` ではなく、Hugging Face Hub から `gsm8k` データセット（`main`構成、`train`スプリット）を直接ロードするように修正します。

---

### 2. ハードコードされたモデルパスの修正（Hugging Face IDへの変更）

#### [MODIFY] [main.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/locate/main.py)
- `modeltype2path` 内の `/path/to/` となっているモデルパスを、Hugging Face Hubの対応するモデルIDに変更します。
  - `llama3-base` $\rightarrow$ `meta-llama/Meta-Llama-3-8B`
  - `llama3-instruct` $\rightarrow$ `meta-llama/Meta-Llama-3-8B-Instruct`
  - `llama3-math` $\rightarrow$ `TIGER-Lab/MAmmoTH2-8B-Plus`
  - `llama3-code` $\rightarrow$ `Replete-AI/Replete-Coder-Llama3-8B`

#### [MODIFY] [mask_generate.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/mask_generate.py)
- `llama3` 指定時の `model_path` を `"meta-llama/Meta-Llama-3-8B-Instruct"` に変更します。

#### [MODIFY] [merge_llms.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging/merge_llms.py)
- `MODEL_DIR` 内の Llama-3 関連のダミーパス `/path/to/...` を、Hugging Face Hub のモデルID（上記と同様）に変更します。

---

## 検証計画

### 自動テスト / 実行手順
ローカルでのコマンド実行（`run_command`）の制約を回避するため、以下の手順を自動化するシェルスクリプト `run_led_replication.sh` を `/mnt/nas/home/hiromi/src/sst_v2/baseline/LED-Merging` 直下に作成します。

1. **仮想環境の構築**:
   ```bash
   python3 -m venv venv_LED
   source venv_LED/bin/activate
   pip install --upgrade pip
   ```
2. **依存ライブラリのインストールと競合回避**:
   ```bash
   # PyTorch関連のバージョンをCUDA 12.1に統一してインストール
   pip install torch==2.4.1+cu121 torchvision==0.19.1+cu121 torchaudio==2.4.1+cu121 --index-url https://download.pytorch.org/whl/cu121
   
   # requirements.txt のインストール
   pip install -r requirements.txt
   
   # vLLM/xformersなどの依存関係による競合を防ぐため、再度PyTorch関連を強制上書き
   pip install torch==2.4.1+cu121 torchvision==0.19.1+cu121 torchaudio==2.4.1+cu121 --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
   ```
3. **Locateステップの実行**:
   ```bash
   cd locate/
   bash scripts/locate_inst.sh
   cd ../
   ```
4. **Electステップの実行**:
   ```bash
   python3 mask_generate.py 0.1 0.4 0.5 11 llama3
   ```
5. **Disjoint & Mergingステップの実行**:
   ```bash
   python3 merge_llms.py \
       --models_to_merge llama3-instruct llama3-math llama3-code \
       --pretrained_model_name llama3-base \
       --merging_method_name top_merging \
       --scaling_coefficient 0.9 \
       --mask_apply_method task_arithmetic \
       --fuse_rates 0.1 0.4 0.5 \
       --orders safety math code \
       --lambdas 1.0 1.0 1.0 \
       --fuse_types o o o \
       --fuse_patterns 11 11 11 \
       --model_ft_name llama3 \
       --model_base_name llama3-base
   ```

### 手動検証
- 各ステップの実行後にログを出力し、エラーなく終了するかどうかを確認します。
- マージされたモデルが `./save_merge_llms/llama3-base/` 配下に保存されていることを確認します。
