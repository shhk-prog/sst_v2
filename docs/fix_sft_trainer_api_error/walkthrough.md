# Walkthrough: フェーズ2 スクリプト更新（コーディングモデル追加 + 評価）

## 変更概要

### 1. `prepare_datasets.py` — Magicoderデータ追加

`prepare_coding_data()` 関数を追加し、`ise-uiuc/Magicoder-OSS-Instruct-75K` から
先頭5000件を `data/utility_coding.json` として保存するようにしました。

### 2. `run_eval.py` — 新規作成

| 評価軸 | 手法 | データ |
|---|---|---|
| **Safety** | AdvBenchプロンプトへの拒否率 | `safety_advbench.json` |
| **Utility-金融** | センチメントラベル正答率 | `utility_fpb.json` |
| **Utility-コーディング** | コードブロック含有率 | `utility_coding.json` |

各モデルにプロンプトを投入し、応答をキーワードマッチングで採点します。
結果は `results/phase2_eval_results.json` に蓄積されます（モデル名でインデックス管理）。

### 3. `run_phase2.sh` — 全面更新

実行フロー:

```
[データ準備]
  utility_coding.json が未存在なら prepare_datasets.py を実行

[Fine-Tuning]
  1. Utility FT (金融)   → models/utility_lora
  2. Utility FT (コーディング) → models/coding_lora   ★新規
  3. Safety FT           → models/safety_lora
  4. Mixed FT (Baseline) → models/mixed_lora

[評価] ← ★新規セクション
  各モデルを run_eval.py で評価 (safety / finance / coding の3軸)
  - base_model (LoRAなし)
  - utility_lora
  - coding_lora
  - safety_lora
  - mixed_lora
```

## 実行コマンド

```bash
# venv_sst をactivateした状態で
cd ~/src/sst_v2/v2
chmod +x scripts/fine_tuning/run_phase2.sh
./scripts/fine_tuning/run_phase2.sh > /mnt/nas/home/hiromi/src/sst_v2/docs/sst_experiment_replan/phase2_ft_log.txt 2>&1
```

## 評価結果の確認

```bash
cat v2/results/phase2_eval_results.json
```
