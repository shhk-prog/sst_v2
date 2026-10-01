# Walkthrough: SafeMERGE 評価パイプラインの構築

## 目的
作成したマージ済みモデルが「タスク性能（GSM8K）」を維持しつつ、「安全性（有害プロンプトの拒否率）」を高めているかを検証するための評価パイプラインを実装しました。

## 実装内容
1. **[run_gsm8k_eval.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/run_gsm8k_eval.sh)**
   - 業界標準の `lm-evaluation-harness` を用いて、GSM8Kタスクの性能（Exact Match）を評価するスクリプトです。
   - モデル本体とLoRAアダプタのパスを受け取り、Few-shot推論を行います（実行時間短縮のため100件のサンプルに制限しています）。

2. **[eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/eval_safety.py)**
   - `PKU-SafeRLHF` データセットから有害（Unsafe）とされているプロンプトをランダムに50件抽出し、モデルに回答させます。
   - 回答テキストに "I cannot", "As an AI", "Sorry" などの安全な拒否（Refusal）を示すキーワードが含まれているかをチェックし、**Safety Rate（拒否率）** を算出します。

3. **[run_evaluation.sh](file:///mnt/nas/home/hiromi/src/sst_v2/baseline/SafeMERGE/run_evaluation.sh)**
   - 「マージ前のタスク用モデル（GSM8K LoRA）」と「SafeMERGE適用後のモデル」の両方に対して、上記2つの評価を連続で実行し、結果を比較しやすくするための統合スクリプトです。

## 確認事項・利用方法
> [!NOTE]
> スクリプトは `baseline/SafeMERGE` フォルダ内に作成されています。
> 以下のコマンドで実行可能です。
> ```bash
> bash run_evaluation.sh
> ```

## 実行結果の考察 (2026/05/27 実行)

今回の評価環境での結果は以下の通りでした。

| モデル | タスク性能 (GSM8K Exact Match) | 安全性 (Safety Refusal Rate) |
|---|---|---|
| **マージ前 (Unsafe/Base)** | 20.0% | 86.0% (43/50) |
| **SafeMERGE 適用後** | 16.0% | 86.0% (43/50) |

**【結果から読み取れること】**
1. **マージ前モデルの安全性がそもそも高い**: 今回ベースに用いた `meta-llama/Llama-2-7b-chat-hf` は元々非常に強固な安全対策が施されています。1エポック程度のGSM8K学習（タスク学習）ではその安全性が十分に破壊されず、マージ前から86%という高い拒否率を維持していました。
2. **SafeMERGEの挙動**: マージ前ですでに安全性が高かったため、SafeMERGEは元のタスク性能（20%）からわずかに低下（16%）させるトレードオフを生みつつも、安全性をしっかりと維持しました（閾値 `0.35` により、全224層中16層のみ安全用アダプタの重みがブレンドされました）。

論文が主張する「タスク学習によって安全性が劇的に低下したモデルを、タスク性能を維持したまま再び安全にする」という劇的な効果を確認するには、より長くタスク学習を行って安全性を意図的に「忘却」させたモデルを用意するか、あるいは元の安全性がそれほど強固ではないベースモデルを使用すると、より顕著な差が表れると考えられます。
