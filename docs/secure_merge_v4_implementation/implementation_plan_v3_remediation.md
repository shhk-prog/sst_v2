# 改修計画書: Secure Merge v4 監査是正・採点環境・実測接続計画 (v3)

## 1. 監査の結論と基本方針 (commit: 0d92205)

2026年10月2日受領の「再監査・残存修正指示書 v3」に基づき、現在の主実験受入判定を **`NO_GO`** と維持する。
前回E0の基本3項目（Hub ID読込、Manifestスキーマ統一、固定理由表示撤廃）の是正は確認されたが、以下の重大な「採点の正しさ」「欠測歪み」「監査結合」「手法・群上限の厳密性」を是正する。

---

## 2. 確定課題に対する改修仕様 (R3-01 〜 R3-08)

### 【R3-01】コード評価の分離実行と HumanEval/MBPP 正式採点
1. **プロセス分離とリソース制限**:
   - `exec` によるインプロセス直接実行を禁止。
   - `multiprocessing.Process` を用い、タイムアウト（既定 3.0 秒）、標準出力抑制、安全な分離空間で実行。
2. **HumanEval 公式テスト呼出プロトコル**:
   - 単に `check` 関数を定義するだけでなく、`check(candidate)` を実際に呼び出す実行コードを組み立てる。
   - 構文エラー、実行時例外、`AssertionError`、タイムアウトを区別。
3. **MBPP アダプター**:
   - `test_list` の各アサーションを順次実行。

### 【R3-02】HarmBench 判定プロトコルの公式準拠と未判定の保持
1. **公式 Prompt Template 準拠**:
   - Center for AI Safety の HarmBench 公式分類テンプレート（Standard / Contextual）を実装。
2. **厳格な判定結果パース**:
   - 先頭一致の単なる `yes` 判定ではなく、公式の `Yes` / `No` ラベルを厳格パース。
   - 空出力、不正出力、フォーマット崩れは `None`（`UNJUDGED`）とし、無害（False）にサイレント変換しない。
3. **未知 backend の拒否**:
   - `judge_backend` に未定義の文字列が渡された場合、即座に `ValueError` を送出。

### 【R3-03】欠測 H ラベルによる VRR 母数歪みの排除
1. **メトリクス母数の分離管理**:
   - `N_total`, `N_generated`, `N_judged`, `N_unjudged`, `N_valid` を分離。
   - VRR は生成された全応答（`N_generated`）から算出。有害性判定の可否で VRR の母数を削らない。
   - 有害性未判定が存在する場合、主選定では `INSUFFICIENT_DATA` とする。

### 【R3-04】E0 監査証跡と実行対象・重み実体の結合
1. **SafetyFT dense 復元検証の厳格化**:
   - 単なるファイル存在ではなく、重みファイルの整合性、テンソルキー・shape の検査を必須化。
2. **実行対象と監査証跡の結合**:
   - manifest に記録されたモデル名・hash・run ID と、実際に CLI / runner に渡された引数を照合。
3. **base_merger の欠損キー厳格化**:
   - 安全側モデルに必須キーが欠落している場合、無言コピーせずエラーとする。

### 【R3-05】E1 統一 schema・benchmark 別制約・0〜1 範囲検査
1. **個票 benchmark 制約の導入**:
   - macro 平均だけでなく、各 benchmark（GSM8K, MATH, HumanEval, MBPP, HarmBench 各種）が個別閾値を満たすことを要求。
2. **0〜1 範囲検査**:
   - utility, ASR, VRR が 0.0〜1.0 の範囲外（999, -1 等）の異常値を確実に排除。
3. **standalone selector のハードコード撤廃**:
   - `e1_selector.py` の `__main__` に残存する `overrefusal=0.02` を撤廃。

### 【R3-06】Fisher の strict FIM 強制と簡略手法の primary 除外
1. **FisherMerger**:
   - `strict_fim=True` を本番で強制。FIM が供給されない場合はモデル読込前に停止。
2. **簡略版手法の扱い**:
   - `SafeMERGE`, `LED` などの `SIMPLIFIED_ADAPTATION` 手法は、primary の公式ランキングから除外。

### 【R3-07】提案法 Calibration の必須指標検査と群共通ノルムスケーリング
1. **Calibration の必須指標**:
   - `delta_utility`, `delta_overrefusal` が欠測・NaN の候補群は不採用とする。
2. **群共通ノルム上限スケーリング**:
   - テンソル別 clip ではなく、群全体の差分二乗和ノルムを集計し、共通の縮小係数を適用。

---

## 3. 受入テスト方針
- 構文が正しい誤答（`add(a,b)=0`）が HumanEval 採点で正しく FAIL となること。
- HarmBench の空応答や不正出力が `None`（未判定）となること。
- H未判定を含むデータで VRR の母数が全生成応答から計算されること。
- benchmark 個別閾値超過で不適格となること。
- 群共通ノルムスケーリングの配分テスト。
