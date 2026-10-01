# 改修計画書: Secure Merge v4 監査是正・厳密化計画 (v2)

## 1. 監査の結論と基本方針

2026年10月1日の「Secure Merge v4 コード監査・修正指示書」に基づき、現在のステータスを **`NO_GO`** と認定し、以下の基本方針に従ってパイプラインの全面是正を実施する。

- 監査対象コミットSHA: `d994f280a21a04fa4b4264608b8214cd6aa14700`
- 既存の動作確認・模擬データはすべて `v4/results/legacy_diagnostic_smoke/` へ隔離済みであり、論文用集計から完全に除外する。
- 「条件を生成できたこと」と「実モデル・実データで行動を測定したこと」を厳格に区別する。
- 欠測値の補完（overrefusal=0.04, vrr_benign=vrr_harmful, utility=0.0等）を全廃し、未測定データはすべて `None / null`（`INSUFFICIENT_DATA`）とする。

---

## 2. 確定課題に対する改修仕様 (P0・P1)

### 【P0-03】E0 停止条件とモデル監査の厳密化
1. **ステータス管理**:
   - `PASS`: 出自、config、tokenizer、特殊トークン、RoPE、重み形状、SafetyFT dense 復元が完全に一致・確認された。
   - `FAIL`: 具体的な不一致（RoPE theta 100倍拡大、vocab 32001 [PAD]拡張、bos_token_id 2 不一致等）を検出。相違項目と値を保存。
   - `UNVERIFIED`: モデルファイル読み込み失敗、config 欠損、出自情報不足。
2. **実行停止ゲート**:
   - `audit_models.py` は、主対象ドメイン（Math, Code）のいずれかが `FAIL` または `UNVERIFIED` の場合、**終了コード 1 (Exit 1)** で終了する。
   - runner 側（`run_all_v4.py`）は、manifest 内の `primary_experiment_verdict` が `NO_GO` の場合、**後段の主実験（E1〜E5）の実行を直ちに停止（HALT）** する。
3. **無言スキップの排除**:
   - `base_merger.py` において、形状不一致や未一致キーを無言でドメインモデルからコピーする処理を原則禁止とし、明示的な allowlist（例: `rotary_emb`）以外のテンソル不一致は例外（ValueError）を送出する。

### 【P0-01 & P0-02 & P1-01】E1 再集計・欠測補完の排除・lm-eval utility 結合
1. **欠測補完の完全撤廃**:
   - `vrr_benign` を `vrr_harmful` で代用しない。無害プロンプト評価が存在しない場合は `None`。
   - `overrefusal` を 0.04 等の固定値で埋めない。XSTest 等の実測ログが存在しない場合は `None`。
   - `utility_score` が未取得のものを 0.0 で埋めない。`None`（`utility_status: INSUFFICIENT_DATA`）として保持。
2. **lm-evaluation-harness 出力（辞書型 results）の正規パース**:
   - `v3` の保存形式（`results: {task: {exact_match: ..., math_verify: ...}}`）に対応した schema adapter を実装。
   - GSM8K, MATH500, HumanEval, MBPP の主要メトリクスを厳密に抽出。
3. **候補ID・評価IDの一意化と結合**:
   - 単なるファイル名 basename ではなく、`domain`, `method`, `alpha`, `train_seed`, `mask_seed` から candidate ID を構成。
   - 1つの candidate ID に対して、安全性評価ファイル、validity評価、過剰拒否評価、utility評価ファイルを厳密に突き合わせて結合。
4. **手法分類の是正**:
   - `unknown` を主比較から完全除外。
   - `v3` 旧ログの `task_arithmetic`（直接補間）は `legacy_linear_patch_old_task_arithmetic` として識別し、標準 Task Arithmetic（$\theta_0$ からの差分合成）と混同させない。
   - `diagonal_sst`, `data_free_sst` は「探索的比較（Exploratory Track）」として主比較9手法から分離。

### 【P0-04 & P1-02 & P1-04】E2・E3 乱数テストの隔離と実機接続・パラメータ数揃え
1. **乱数テストコードの隔離**:
   - `characteristic_analyzer.py`, `intervention_mapper.py`, `controlled_intervention.py` の `__main__` にあった乱数テンソルテストを `v4/tests/` へ完全移動。
   - 本番スクリプトは実 checkpoint の読み込みを必須とする。
2. **E3 ランダム対照の等パラメータ数・等テンソル種別化**:
   - 単なる同数キー選択ではなく、「attention, mlp, norm の各テンソル種別ごとに、同じパラメータ数」を選択する層内サンプリングを実装。
   - 3つの mask seed (42, 43, 44) で測定。
3. **双方向ノルム縮小対照**:
   - $t = \min(||\Delta_1||_2, ||\Delta_2||_2), \Delta'_j = \Delta_j \frac{t}{||\Delta_j||_2}$
   - A–C, B–D だけでなく、選択箇所を比較する A–B, C–D も同一ノルムに揃えた対照を実装。
4. **FP32/FP64 による数値安定化**:
   - FP16 の二乗和が inf になるオーバーフローを防ぐため、差分・内積・二乗和計算はすべて FP32 または FP64 で実行。

### 【P0-05 & P1-03】E4・E5 のフェイク排除・依存関係の厳密化
1. **E4 の実測依存化**:
   - E3 の実測介入地図ファイルが存在しない場合は `E4: BLOCKED` として停止。
   - デフォルトの固定係数によるマージを本番出力としない。
   - 領域別上限 $\rho_g$ を群単位（群二乗和の平方根比率）で適用。
2. **E5 の未見 Test 評価依存化**:
   - 未見 Test 集合での実測評価結果が存在しない場合は `E5: NOT_RUN`。ダミー性能値を出力しない。

---

## 3. 受入テスト方針
1. **単体テスト**: 辞書型 lm-eval JSON を読み込み、`exact_match` が正しく復元されること。
2. **E0 ゲートテスト**: 不合格の状態で runner が即時非ゼロ終了すること。
3. **1候補の縦通し受入テスト**: 監査済み 1 モデル・1 手法で、マージ → 保存 → 再読込 → 生成 → 採点 → 再集計 の全経路が正しく完通すること。
