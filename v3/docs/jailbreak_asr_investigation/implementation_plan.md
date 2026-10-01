# 実装計画: General/Inst Ave (%) 算出ロジックの修正・正常化

## 概要
ユーザーからのご指示「**General/Inst Ave: 文字一致度 (Similarity) や AlpacaEval2 などの 0.1%〜3% の極低スコアが 3 つ混ざっていることが平均を引き下げている主因です。これを正しい評価になるようにして**」に対応するため、`General/Inst Ave (%)` の定義を正常化します。

---

## 変更仕様詳細

### 1. `General/Inst Ave (%)` の再定義
- **旧・計算対象 (5 タスク)**:
  `MMLU`, `IFEval`, `AlpacaEval2`, `Evol-Code Similarity`, `MedAlpaca Similarity`
- **新・計算対象 (3 タスク)**:
  **`MMLU`**, **`IFEval`**, **`AlpacaEval2`**

### 2. 理由
文字完全一致度 (`SequenceMatcher.ratio()`) である `Evol-Code Similarity` や `MedAlpaca Similarity` は、通常の精度 (%) とは物理的・学術的に尺度が異なり、平均スコアを不当に数パーセントまで引き下げるノイズとなっていました。
これらを平均値の計算から除外し、標準的な一般知識・指示追従評価ベンチマーク（MMLU, IFEval, AlpacaEval 2）の相加平均として算出します。（※ Evol-Code / MedAlpaca は詳細列としての表示を維持します）。

---

## 対象ファイル
- [generate_summary_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_summary_tables.py)
- [generate_paper_summary_tables.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis/generate_paper_summary_tables.py)

---

## 検証プラン
1. コードの修正
2. 新しい定義に基づく `General/Inst Ave (%)` の正しい数値算出の確認
