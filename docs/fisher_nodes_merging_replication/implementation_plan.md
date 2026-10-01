# fisher-nodes-merging 再現実験 実装計画

Thennal D K et al. (LREC-COLING 2024) による `fisher-nodes-merging` の再現実験を実行し、その結果の正確性と再現性を検証する計画です。

> [!IMPORTANT]
> **環境上の制約と実行方法について**
> 現在、エージェント環境（Antigravity IDE）のコマンド実行機能において `sandbox not available with IDE command terminal` というエラーが発生しており、エージェント側から直接コマンドを起動できません。
> そのため、本計画におけるコマンド実行ステップは、**ユーザーご自身のターミナルで実行していただく**形で進めます。
> エージェントはファイルの編集（`requirements.txt` の修正等）、実行結果の解析、およびレポートの自動生成を担当します。

## 概要

`baseline/fisher-nodes-merging` ディレクトリのコードを用い、GLUEタスク（MNLI, QQP, QNLI, SST-2, STS-B, MRPC, RTE）のモデルマージおよび評価を行う再現実験を実行します。
専用の仮想環境 `venv_fisher` を用い、他手法と競合しないクリーンな環境で実験を行います。
評価時（特に相関係数の算出等）に `scipy` が必要となるため、依存関係に追加してインストールを行います。
実験完了後、新しく得られた評価結果を既存の測定結果（`metrics/2026-05-29_22-40-19_name_of_run.json`）と比較し、再現性を検証します。

---

## 提案する手順（ユーザー様での実行をお願いします）

### 1. 依存関係のインストールと更新
`scipy` を含む必要なパッケージを仮想環境 `venv_fisher` にインストール・更新します。以下のコマンドをターミナルで実行してください。
```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/fisher-nodes-merging
./venv_fisher/bin/python3 -m pip install -r requirements.txt
```

### 2. 再現実験の実行
再現実験を実行し、ログをタイムスタンプ付きのファイルに書き出します。以下のコマンドを実行してください。
```bash
cd /mnt/nas/home/hiromi/src/sst_v2/baseline/fisher-nodes-merging
./venv_fisher/bin/python3 eval_compare.py --config config.json > logs/fisher_nodes_merging_reproduce_$(date +%Y%m%d_%H%M%S).log 2>&1
```

### 3. 結果の検証とレポート作成
実行終了後、エージェントが以下を自動で行います：
- `metrics` ディレクトリ配下に生成される JSON ファイルの解析。
- 既存の測定結果 `2026-05-29_22-40-19_name_of_run.json` との比較検証。
- 日本語での再現実験レポート（Walkthrough）の作成（`docs/fisher_nodes_merging_replication/walkthrough.md` に保存）。

---

## 変更対象ファイル

### [MODIFY]
- [requirements.txt](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/fisher-nodes-merging/requirements.txt) (scipy の追加 - 変更済み)
- [task.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/fisher_nodes_merging_replication/task.md)
- [implementation_plan.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/fisher_nodes_merging_replication/implementation_plan.md) (本ファイル)

### [NEW]
- [walkthrough.md](file:///mnt/nas/home/hiromi/src/sst_v2/docs/fisher_nodes_merging_replication/walkthrough.md)

---

## 検証計画

### 実行確認
- ユーザー様の環境で `requirements.txt` のインストールおよび `eval_compare.py` の実行が正常に完了すること。
- `baseline/fisher-nodes-merging/metrics` フォルダに新しい JSON 結果ファイルが書き出されていること。

### 再現性検証
- 新旧の評価指標（Accuracy、F1、Pearson/Spearman相関など）をエージェントがプログラムまたは目視で比較し、決定論的に結果が一致するか、あるいは誤差の範囲に収まっているかを分析します。
