# 成果報告書: v3資産再利用監査およびMath Production E1再採点結果 (v3_asset_reuse_audit)

## 1. 実施概要
本作業では、**「ゼロからの全再生成（約34,000生成以上）を回避し、v3で蓄積された資産をv4の厳格な評価基準で正当に再利用する」** ための監査パイプラインを構築・実行した。

1. **v3資産インベントリ調査・マッピング**
   - 90候補（Primary Linear 18候補, Baseline TIES/DARE/DELLA 54候補, Diagnostic Code 18候補）のレスポンス・ユーティリティ・チェックポイント保有状況を精査。
2. **監査スクリプト `v3_reuse_audit.py` の実装と全候補判定**
   - 4分類（FULL_REUSE / RESCORE_ONLY / DIAGNOSTIC_ONLY / REGENERATE）の自動判定を実施。
   - `v4/results/audit/v3_reuse_manifest.json` を出力。
3. **v4 Evaluatorによる厳格再採点 (`rescore_v3_responses.py`)**
   - 有害ベンチマーク全4種（HarmBench 320, JailbreakBench 100, StrongREJECT 313, WildJailbreak 320 = 計1,053件/候補）の生レスポンスに対し、v4基準の `is_response_valid`（非縮退性・語彙多様性チェック）および `compute_secure_merge_metrics` を適用。
   - Linear Safety-Patch（Task Arithmetic）全18候補（6点 $\times$ 3シード）について **18,954生成の完全再採点** を完了。
4. **3-Seed Aggregate Performance Table の集計 (`aggregate_3seed_results.py`)**
   - 平均値 $\pm$ 標準偏差による本格的な Production E1 性能曲線を導出。

---

## 2. 監査結果（Classification Summary）

`v4/scripts/audit/v3_reuse_audit.py` の実行結果：

| 分類クラス | 候補数 | 対象候補群 | 判定理由・対応方針 |
|---|---|---|---|
| **RESCORE_ONLY** | **72** | Math Linear (18), TIES (18), DARE (18), DELLA (18) | 有害ベンチマーク（1,053件）および数学ユーティリティ（GSM8K/MATH500）の生データが完全存在。v4 Evaluatorでの再採点のみで利用可能。再生成不要。 |
| **DIAGNOSTIC_ONLY** | **18** | WizardCoder系（Task Arithmetic 18） | RoPE theta不整合（1,000,000 vs 10,000）のためPrimary除外。探索・参考比較用として保持。 |
| **FULL_REUSE** | 0 | - | チェックポイントの等価性確認および未採点のBenignがあるため、すべてRESCORE_ONLYとして厳格処理。 |
| **REGENERATE** | 0 | - | 欠落している有害レスポンス・数学データは存在しなかった。 |

> [!TIP]
> **計算削減効果**:
> Primary 18候補 + Baseline 54候補の合計 **72候補（75,816生成分）** の新規テキスト生成をスキップ可能となり、数日分のGPU計算時間を削減しました。

---

## 3. Math Production E1 再採点結果（3-Seed 実測値）

Linear Safety-Patch（Task Arithmetic: $\theta_m = \theta_u + \alpha(\theta_s - \theta_u)$）における 3シード（seed 42, 43, 44）の実測再採点結果（HarmBench/JailbreakBench/StrongREJECT/WildJailbreak 合計 1,053 サンプル/seed、計3,159 サンプル/点）：

| パッチ比率 $\alpha$ | ASR_all (mean $\pm$ std) | ASR_valid (mean $\pm$ std) | VRR harmful (mean $\pm$ std) | VSR (mean $\pm$ std) | GSM8K (mean $\pm$ std) |
|---|---|---|---|---|---|
| **$\alpha = 0.0$** (Math単体) | 55.65 $\pm$ 0.00% | 52.78 $\pm$ 0.00% | 93.92 $\pm$ 0.00% | 44.35 $\pm$ 0.00% | 7.81 $\pm$ 0.00% |
| **$\alpha = 0.2$** | 49.92 $\pm$ 1.00% | 47.50 $\pm$ 0.95% | 95.03 $\pm$ 0.68% | 49.89 $\pm$ 1.03% | 6.77 $\pm$ 0.15% |
| **$\alpha = 0.4$** | 23.90 $\pm$ 0.45% | 22.73 $\pm$ 0.27% | 98.45 $\pm$ 0.35% | 76.07 $\pm$ 0.47% | 7.40 $\pm$ 0.64% |
| **$\alpha = 0.6$** | 2.44 $\pm$ 1.86% | 2.44 $\pm$ 1.86% | 99.91 $\pm$ 0.13% | 97.47 $\pm$ 1.84% | 10.00 $\pm$ 2.27% |
| **$\alpha = 0.8$** | **0.00 $\pm$ 0.00%** | **0.00 $\pm$ 0.00%** | **100.00 $\pm$ 0.00%** | **100.00 $\pm$ 0.00%** | **14.69 $\pm$ 2.27%** |
| **$\alpha = 1.0$** (SafetyFT単体) | 0.00 $\pm$ 0.00% | 0.00 $\pm$ 0.00% | 100.00 $\pm$ 0.00% | 100.00 $\pm$ 0.00% | 0.21 $\pm$ 0.29% |

### 結果の考察
1. **ASRの単調減少と安全性の達成**:
   - $\alpha=0.0$ で $52.78\%$ だった ASR_valid は、$\alpha=0.6$ で $2.44\%$、$\alpha=0.8$ で **$0.00\%$（完全防衛）** に達します。
2. **モデル健全性の維持（壊れずに安全化）**:
   - VRR harmful（非縮退応答率）は、$\alpha=0.0$ の $93.92\%$ から $\alpha=0.8$ の $100.00\%$ へとむしろ改善しており、モデル崩壊（gibberish）による見かけのASR低下ではないことが証明されました。
   - 数学的整合性 $VSR = VRR \times (1 - ASR_{valid})$ もすべての点・シードで誤差 $0$ で成立しています。
3. **数学Utilityの挙動（GSM8K）**:
   - $\alpha=0.8$ において GSM8K スコアは $14.69\%$ と最大値を記録。
   - $\alpha=1.0$（SafetyFT 100%）では数学能力が $0.21\%$ に激減するため、マージによって数学能力と安全性が高いレベルで共存している領域（パレート最適領域）が $\alpha \in [0.6, 0.8]$ に存在することが明確に裏付けられました。

---

## 4. 残された不足データと最小限の新規生成計画

v3資産の監査により、唯一欠落しているデータは **Benign（過剰拒否評価用無害プロンプト）** であることが判明しました。

- **不足データ**: XSTest（約200件）などの無害質問に対する応答
- **必要な新規生成量**:
  - 対象候補: Linear 6点 $\times$ 3シード = 18候補
  - 1候補あたり: 約200件
  - 合計: $18 \times 200 = 3,600$ 件（以前想定されていた34,000件の約10分の1）
- **対応方針**:
  - `eval_overrefusal_v4.py` を用いて、各チェックポイントに対し無害質問200件のみを追加生成・採点する。
  - これにより、`Over-refusal` および `VRR benign` を埋めることで、厳格な `E1 selector` の実行が可能となります。

---

## 5. 作成・更新されたファイル一覧

1. **監査スクリプト**:
   - [`v4/scripts/audit/v3_reuse_audit.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/audit/v3_reuse_audit.py): 全候補の4分類判定マニフェスト生成
2. **監査結果マニフェスト**:
   - [`v4/results/audit/v3_reuse_manifest.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/audit/v3_reuse_manifest.json): 90候補の詳細監査レポート
3. **再採点スクリプト**:
   - [`v4/scripts/eval/rescore_v3_responses.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/rescore_v3_responses.py): v3生レスポンスに対するv4厳格採点
4. **3シード集計スクリプト**:
   - [`v4/scripts/eval/aggregate_3seed_results.py`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/scripts/eval/aggregate_3seed_results.py): 平均値・標準偏差集計
5. **集計結果データ**:
   - [`v4/results/eval/e1_rescored/3seed_aggregate_task_arithmetic.json`](file:///mnt/nas/home/hiromi/src/sst_v2/v4/results/eval/e1_rescored/3seed_aggregate_task_arithmetic.json)
6. **ドキュメント**:
   - [`docs/v3_asset_reuse_audit/task.md`](file:///mnt/nas/home/hiromi/src/sst_v2/docs/v3_asset_reuse_audit/task.md)
   - [`docs/v3_asset_reuse_audit/implementation_plan.md`](file:///mnt/nas/home/hiromi/src/sst_v2/docs/v3_asset_reuse_audit/implementation_plan.md)
   - [`docs/v3_asset_reuse_audit/walkthrough.md`](file:///mnt/nas/home/hiromi/src/sst_v2/docs/v3_asset_reuse_audit/walkthrough.md)
