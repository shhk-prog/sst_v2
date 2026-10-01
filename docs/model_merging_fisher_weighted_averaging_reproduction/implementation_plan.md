# Fisher-Weighted Averaging 再現実験計画（全タスク拡張版）

NeurIPS 2022 に採択された論文 "Merging Models with Fisher-Weighted Averaging" のリファレンス実装 (`baseline/model_merging`) を用いて、論文に記載されている Intermediate-task training の全例（GLUEタスク間のマージ）の再現実験を行います。

## User Review Required

> [!IMPORTANT]
> - 本リポジトリのスクリプトは現状 **GLUEタスク** に特化して実装されています。
> - そのため、「論文にある全ての例」として、論文の Figure 4 および 6 にある **GLUEタスクにおける全てのドナーモデルとターゲットモデルの組み合わせ（Intermediate-task training）** を実行する計画としています。
> - 対象となるタスクモデル（RoBERTa-base想定）: `RTE`, `MNLI`, `MRPC`, `SST-2`, `STS-B`, `QNLI`, `QQP`, `CoLA`
> - 画像分類(ViT)や生物・CS系のDomain Adaptation(ChemProt等)は現在のスクリプトが対応していないため、今回はGLUEタスクに絞った再現となりますがよろしいでしょうか？（もしそちらも必要な場合、データローダー等の大幅な新規実装が必要となります）
> - GPUを使用し、8つ以上のモデルダウンロードとFisher計算、マージ処理を行うため、数時間以上の計算時間がかかる可能性があります。

## Proposed Changes

既存のスクリプトを連続して実行するためのシェルスクリプトを作成します。
全てのタスクモデルに対するFisherの計算と、RTEタスクをターゲットとした各モデルとのマージ・評価を網羅的に行います。

### Scripts

#### [NEW] [run_all_experiments.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/model_merging/run_all_experiments.sh)
以下の処理を順次実行するスクリプトを作成します：
1. Fisher行列の保存先ディレクトリの作成
2. 以下の全モデルに対する `compute_fisher.py` の実行：
   - `textattack/roberta-base-RTE`
   - `textattack/roberta-base-MNLI`
   - `textattack/roberta-base-MRPC`
   - `textattack/roberta-base-SST-2`
   - `textattack/roberta-base-STS-B`
   - `textattack/roberta-base-QNLI`
   - `textattack/roberta-base-QQP`
   - `textattack/roberta-base-CoLA`
3. `textattack/roberta-base-RTE` をターゲットモデルとして、他の全てのドナーモデルと `merge_and_evaluate.py` でマージと評価（Isometric および Fisher）を実行

## Verification Plan

### Automated Tests
- 作成した `run_all_experiments.sh` をバックグラウンド処理（必要であれば）またはターミナル上で実行します。

### Manual Verification
- 全タスク組み合わせのマージ結果の出力をログに保存し、Isometric mergeとFisher mergeのそれぞれで出力される評価スコア（RTE accuracyなど）を確認し、論文の傾向（Fisher mergeの優位性）と一致するかを確認します。
