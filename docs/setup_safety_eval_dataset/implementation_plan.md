# 安全性評価ベンチマークの個別公式判定導入計画

## 概要
安全性評価において、単にデータセットを分けるだけでなく、各ベンチマーク（HarmBench, JailbreakBench, StrongREJECT, WildJailbreak）が公式に採用・確立している判定ロジックおよび判定モデル（Classifier / Evaluator）を用いて、それぞれのベンチマークの基準に完全準拠した評価（ASR等の算出）を実行・記録するようパイプラインを拡張します。

VRAM制限やAPIキーの未設定によるクラッシュを防ぐため、外部API（GPT-4等）への依存は避け、各ベンチマークが公開している公式判定モデルを `transformers` によりローカルでロード・実行して評価します。

各ベンチマークの判定アプローチ：
1. **HarmBench**: 公式判定モデル **`cais/HarmBench-Llama-2-13b-cls`** を使用し、プロンプトと応答を入力して有害動作に加担しているか (`Yes` / `No`) を判定します。
2. **JailbreakBench / WildJailbreak**: 安全判定モデル **`allenai/wildguard`** を使用し、応答が拒否 (`Response refusal: yes`) または有害加担していないか (`Harmful response: no`) を判定します。
3. **StrongREJECT**: `strong_reject` パッケージまたは公式のファインチューン判定モデル（Gemmaベース）を使用し、StrongREJECT の公式採点ルーブリックに沿って 0〜1 点の実数値スコアを算出します。

## Proposed Changes (提案される変更点)

### [requirements.txt](file:///mnt/nas/home/hiromi/src/sst_v2/v3/requirements.txt)

#### [MODIFY] [requirements.txt](file:///mnt/nas/home/hiromi/src/sst_v2/v3/requirements.txt)
- 必要に応じて `strong_reject` 等の公式判定モジュールのインストールを追加します（または git 直接指定）。

### [data_prep.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/data_prep.py)

#### [MODIFY] [data_prep.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/data_prep.py)
- 各ベンチマークデータセットからプロンプトを個別のファイル名（`eval_harmful_harmbench.json` 等）で保存します。

### [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py)

#### [MODIFY] [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py)
- 評価対象モデルでの推論終了後、メモリを解放した上で、指定されたタスク（ベンチマーク）に応じた**公式判定器**をロードして判定を実行します。
  - **`harmbench`**: `cais/HarmBench-Llama-2-13b-cls` による判定
  - **`jailbreakbench` / `wildjailbreak`**: `allenai/wildguard` による判定
  - **`strongreject`**: `strong_reject` 公式の評価ロジック（`strong_reject.evaluate` 等）による判定

### [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)

#### [MODIFY] [run_experiments.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/run_experiments.py)
- `safety_tasks` ごとに `eval_safety.py` を個別に呼び出し、結果を `{model}_{task}_safety.json` として記録します。

### [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)

#### [MODIFY] [pareto_auc.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/pareto_auc.py)
- タスクごとの ASR 結果ファイルをパースし、各ベンチマークのスコアを個別に可視化・分析できるようにパーサーを拡張します。

## Verification Plan (検証計画)

### Automated Tests
修正適用後、以下の手順で動作を検証します：
1. `data_prep.py` により各データセットのJSONが生成されることを確認。
2. `eval_safety.py` で `harmbench`, `strongreject` 等をそれぞれ実行した際、対応する公式モデル（`HarmBench-Llama-2-13b-cls` 等）がロードされ、判定が正しく行われることを確認。
3. `pareto_auc.py` でタスクごとの評価結果が正常に処理・可視化されることを確認。

### Manual Verification
- 出力された JSON 内の各 ASR 判定が、ルールベースではなく各ベンチマークの公式基準に基づいて判定されていることを確認。
