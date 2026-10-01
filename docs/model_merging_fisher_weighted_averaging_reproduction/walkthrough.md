# Walkthrough: Fisher-Weighted Averaging 再現実験

## 目的
NeurIPS 2022 にて発表された論文「[Resolution of Multiple Tasks in Model Merging](https://proceedings.neurips.cc/paper_files/paper/2022/hash/70c26937fbf3d4600b69a129031b66ec-Abstract-Conference.html)」の主要な手法である **Fisher-Weighted Averaging** の再現実験を行いました。
公式リポジトリ ([mmatena/model_merging](https://github.com/mmatena/model_merging)) のコードをベースに、GLUEタスク向けにチューニングされた複数のRoBERTaモデル (`textattack/roberta-base-*`) 間でのマージと評価を実施しました。

## 解決した環境構築の課題
近年のTensorFlowやHugging Faceエコシステムのアップデートにより、元のコードそのままでは最新環境（H100 GPUなど）で動作しない問題がありました。以下の修正を実施することでパイプラインを完走させました。

> [!WARNING]
> **XLA JITコンパイルエラー (`libdevice not found`)**
> TensorFlow 2.16以降および最新のGPUアーキテクチャでは、XLAの利用が必須となる場面があり、システムに依存するCUDAライブラリ不足で実行が停止しました。
> 対策として、`nvidia-cuda-nvcc-cu12` を追加インストールし、スクリプト内で自動的に `XLA_FLAGS` パスを解決するよう [run_all_experiments.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/model_merging/run_all_experiments.sh) に環境変数を設定しました。

> [!NOTE]
> **TensorFlow Datasetsのパディング不整合 (`Cannot batch tensors with different shapes`)**
> TransformersのTokenizerとTensorFlow Datasets間の連携において、バッチ内のテンソル形状が不揃いになる問題が発生しました。
> [data.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/model_merging/model_merging/data.py) の `py_map_fn` 内で、Pythonリストの操作を用いて明示的に固定長 (128トークン) にパディングとトランケーションを行うことでバッチ処理を安定化させました。

> [!TIP]
> **評価ライブラリのアップデート (`module 'datasets' has no attribute 'Metric'`)**
> 古い `datasets` ライブラリの `load_metric` が廃止されていたため、最新のHugging Face標準である `evaluate` パッケージに移行しました。([evaluation.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/model_merging/model_merging/evaluation.py))

## 実験の実行内容
Hugging Face Hub 上で公開が取り下げられていた `QQP`, `CoLA` の2タスクを除外し、**RTE, MNLI, MRPC, SST-2, STS-B, QNLI** の合計6タスクで実行しました。

1. **Fisher行列の計算**
   各タスクにファインチューニングされたモデル上で、訓練データを用いた対角Fisher情報行列を計算し、`./fishers/` ディレクトリに保存しました。
2. **モデルマージと評価**
   **Targetタスク = RTE** とし、他の5つのタスクのモデル（Donor）を順にマージしました。
   それぞれのペアについて、単純な係数マージ（**Isometric Merge**）と、Fisher行列を重み付けに用いた（**Fisher Merge**）による探索を行い、様々な混合比率でのRTEタスクのAccuracyを算出しました。

実験結果は `experiment_output.log` にすべて記録されており、Fisherマージによるスコアの推移（係数に応じたAccuracyの山）を確認することができます。
