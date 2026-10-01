# 修正内容の確認 (Walkthrough)

SST-Merge の実験環境（`v2`）において、`kiro` の「仕様駆動開発」および「Steering (常時ルール) と Specs (実装計画)」の構成に完全準拠し、論文の科学的・統計的厳密性を担保するための仕様書の再設計と自動検証フックの強化がすべて完了しました。

---

## 変更内容の概要

### 1. 仕様書および実装計画書の再配置と修正
Kiro の公式の思想に従い、永続的ルールを `kiro/steering/` に、AAAI-27 実装計画を `kiro/specs/sst-merge-aaai27/` に配置しました。

#### A. 常時適用ルール (`kiro/steering/` 配下)
- [product.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/steering/product.md): 
  - ベースモデルをメイン `meta-llama/Meta-Llama-3.1-8B-Instruct` に修正し、Mistral/Qwen、および先行研究比較用に `Llama-2-7B-Chat` を追加。
  - 現論文再現用ベンチと AAAI 向け拡張ベンチを分離。
  - Fisher 感度（$F_h$）の物理的意味を「感度 proxy」として緩和し、安全方向はパッチベクトル $\Delta_s$ から与えられることを明記。
  - 学習、FIM推定、評価データの完全物理分離（データ役割割り当て表）を追加し、HELM-Safety, HumanEval, MT-Bench などの全指定ベンチマークを網羅。
  - DELLA, Breadcrumbs, SafeMERGE, LED-Merging, AlignMerge などの必須比較手法および評価指標（ASR, Over-refusal, Pareto AUC 等）を明記。
  - アブレーションにおける **F_h/F_b vs F_h only vs magnitude** 比較の重要性を追記。
  - 実験グリッド（$\alpha$ スイープ、Top-$k$、シード数 $N=500$）を固定。
  - 禁止事項を追加（評価データのチューニング利用禁止、cherry-picking禁止、seed固定、公式実装commit hash記録、キャッシュ統計利用禁止、archiveコード使用禁止）。
- [tech.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/steering/tech.md): 技術スタック制約、`mergekit` 必須化（カスタムフォールバックの禁止）、シード・バージョン記録の要請。
- [structure.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/structure.md): リポジトリ構成、データ規約、ドキュメント読み順を定義。
- **旧仕様書の非推奨化**: 旧 [v2/steering/](file:///mnt/nas/home/hiromi/src/sst_v2/v2/steering/) 内のファイルを非推奨化し、新配置先への誘導を追記。

#### B. AAAI-27 向け Specs (`kiro/specs/sst-merge-aaai27/` 配下)
- [requirements.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/specs/sst-merge-aaai27/requirements.md): AAAI 通過に必要な要件、対象モデル（Llama-2を含む）、採択基準、追加ベンチマーク（HELM-Safety, HumanEval, MT-Bench等）およびアブレーション注記、データ役割分離表。
- [design.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/specs/sst-merge-aaai27/design.md): パイプライン設計、データリーク（カンニング）防止の工学設計（用途別データ割り当て対応表を明記）。
- [tasks.md](file:///mnt/nas/home/hiromi/src/sst_v2/kiro/specs/sst-merge-aaai27/tasks.md): 比較手法整理、 ablaton 計画、図表生成などの TODO 管理表。

---

### 2. コード側におけるカスタムフォールバックの完全排除
- [baseline_merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v1/scripts/merging/baseline_merge.py):
  `MergekitMerger` 内で `mergekit` が使えない場合のフォールバックや、実行失敗時に `CustomBaselineMerger` へ自動移行する処理をすべて排除し、即時 `RuntimeError` を発生させてプロセスを停止させるように変更しました。これにより、Kiro が誤って古いカスタム実装を使用するのを完全に防ぎます。

---

### 3. 自動検証フック (`steering_hook.py`) の強化と組み込み
- [steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/steering_hook.py):
  ルール違反を検知し例外を送出する `verify_experiment_config(args)` を実装しました。
  - **ベースモデル**: Llama-3.1 系統、Mistral, Qwen 以外のモデル時に例外送出。
  - **公式実装の強制**: TIES/DAREなどの実行時に `implementation="mergekit"` などの公式・公開実装でない場合に例外送出。
  - **Data-Free キャッシュ統計の遮断**: `data_free_sst` 時に、データセット引数や cached FIM 等が渡された場合に例外送出。
  - **データセットの重複禁止**: FIM用データ・学習用データが、評価用データと物理的に重複している場合に例外送出（リーク防止）。
- **フックの組み込み**:
  [run_lora_ft.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/fine_tuning/run_lora_ft.py), [run_official_safemerge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/merge/run_official_safemerge.py), [run_sst_merge.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/merge/run_sst_merge.py) に `steering_hook.verify_experiment_config(args)` を組み込みました。

---

## 検証方法と結果

仕様書のルール違反がフックで正しく検出されることを確認するため、ユニットテストスクリプトを更新しました。
- [test_steering_hook.py](file:///mnt/nas/home/hiromi/src/sst_v2/v2/scripts/test_steering_hook.py)

### テスト実行手順
以下のコマンドを実行し、すべてのテストがパスすることを確認してください。

```bash
cd /mnt/nas/home/hiromi/src/sst_v2/v2
python scripts/test_steering_hook.py
```

#### テストされる項目：
- 正常な設定（Llama-3.1-8B-Instruct, FIMと評価データの非重複等）を指定した場合は正常に通過する。
- 許可されていないベースモデル（例: `gpt-2`）を指定した場合は例外が発生し停止する。
- TIESマージ時に `implementation` が `mergekit` でない（カスタムマージの実行を試みた）場合は例外が発生する。
- Data-Free マージ実行中に `open()` で実データファイルを開こうとした場合、および引数にデータセットやキャッシュ統計を指定した場合は例外が発生する（リーク防止）。
- 学習用・FIM用データと評価用データが重複している場合は例外が発生する。
