# 実装計画書: v3資産再利用監査およびMath Production E1移行 (v3_asset_reuse_audit)

## 1. 背景と目的
v4の目的は「壊れずに安全になるマージは何が違うのか？」を解明することであり、現在地は **Math Pilotの全段疎通完了** から **Math Production E1（本格比較実験）** への移行段階にある。
Production E1では1候補あたり約1,900生成（Safety 1,053 + Math 640 + Benign 200）、Linear 6点・3 seedで約34,000生成規模に達するため、ゼロから全生成を行うと莫大な計算コストがかかる。
そこで、**v3で蓄積された資産（checkpoint, generated response, utility results）を監査し、信頼できるデータを厳格に再利用** することで、不要な再計算を大幅に削減しつつ、v4の厳格な評価基準（Validity, HarmBench classifier, ASR_valid, Over-refusal）を担保する。

---

## 2. v3資産の4分類基準（Classification Taxonomy）

| クラス | 定義 | 対応方針 |
|---|---|---|
| **FULL_REUSE** | チェックポイントがcanonical等価であり、生成設定・プロンプト・シード・プロベナンスがv4基準と完全一致 | チェックポイントおよび生成レスポンスをそのまま再利用（evaluator採点のみ確認） |
| **RESCORE_ONLY** | 生成レスポンス（生テキスト）は信用できるが、旧evaluatorの判定（単純キーワード一致や欠測等）に不備がある | 生成レスポンスをv4 evaluator（HarmBench classifier, Validity checker）で再採点 |
| **DIAGNOSTIC_ONLY** | WizardCoder系（RoPE不整合）、旧実装バグあり、またはcanonical等価性が満たされないモデル | Primary研究結果には採用せず、探索・診断・参考比較用として保持 |
| **REGENERATE** | レスポンス欠落、サンプルID/プロンプト不明、チェックポイント由来不明、またはBenign等の未評価項目 | v4環境で新規生成を実行 |

---

## 3. 実装計画

### 3.1 資産インベントリ突合 (`v3_reuse_audit.py`)
- **対象ディレクトリ**:
  - `v3/results/vllm/debug_limit320/merged/` (seed42, 43, 44)
  - `v3/models/merged/`
- **対象候補群（Math Production E1 Primary）**:
  - `task_arithmetic` (Linear Safety-Patch)
  - $\alpha \in \{0.0, 0.2, 0.4, 0.6, 0.8, 1.0\}$
  - seeds $\in \{42, 43, 44\}$
  - ユーティリティ: `safety+math`
- **チェック項目**:
  1. `harmbench_safety.json`: limit=320 の生プロンプト・レスポンスの存在
  2. `jailbreakbench_safety.json`: limit=100
  3. `strongreject_safety.json`: limit=313
  4. `wildjailbreak_safety.json`: limit=320
  5. `utility_math_gsm8k.json`: limit=320 の生生成ログ (`samples`)
  6. `utility_math_minerva_math500.json`: limit=320 の生生成ログ
  7. `benign` (XSTest / AlpacaEval): 存在有無（多くは未評価のためREGENERATE対象）
  8. チェックポイント本体（weights）: 保存されているか、およびcanonicalize等価性

### 3.2 判定マニフェスト出力 (`v4/results/audit/v3_reuse_manifest.json`)
各候補について以下の構造でJSON出力する：
```json
{
  "candidate_id": "math_linear_a0.2_seed42",
  "method": "linear",
  "alpha": 0.2,
  "seed": 42,
  "v3_checkpoint_dir": "v3/models/merged/...",
  "classification": "RESCORE_ONLY",
  "reuse_breakdown": {
    "harmful_responses": "REUSE_RESCORE",
    "math_utility": "REUSE_VERIFIED",
    "benign_responses": "REGENERATE"
  },
  "required_actions": [
    "rescore_harmbench",
    "rescore_jailbreakbench",
    "rescore_strongreject",
    "rescore_wildjailbreak",
    "generate_benign_eval"
  ]
}
```

### 3.3 再採点パイプラインプロトタイプ (`rescore_v3_responses.py`)
- v3の生レスポンスを取り出し、v4の採点エンジン（`HarmBenchClassifier` + `ValidityEvaluator`）を通して、
  - `ASR_all`
  - `ASR_valid`
  - `VRR harmful`
  - `VSR`
  を計算してv4フォーマットの評価結果テーブルを出力できることを確認する。

---

## 4. 期待される効果
- 1候補あたり有害ベンチマーク約1,053生成＋数学約640生成の計算をスキップ可能。
- 6点×3シード（18候補）のうち、既存レスポンスがあるものについては最大約30,000生成を再利用し、GPU計算時間を大幅に短縮（数日分相当）。
- 不足しているBenign（XSTest等 200件程度）および未評価点のみを新規生成するだけで、完全なE1データセットが迅速に揃う。
