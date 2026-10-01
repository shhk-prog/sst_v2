# FLMSEC 論文修正タスクリスト (Task List)

## 1. 調査と集計ロジックの検証
- [x] `/mnt/nas/home/hiromi/src/sst_v2/v3/scripts/analysis` 内の集計スクリプト（`compute_safety_diagnostics.py`, `generate_flmsec_hyo.py`, `generate_specific_tables.py` など）を解析
- [x] Original ASR, Conditional ASR ($\mathrm{ASR}_{\text{valid}}$), VRR, VSR の計算定義および同じ harmfulness ラベルを使用しているか調査
- [x] 数値矛盾（Table 2 と本文の Task Arithmetic safety+code、Table 10 等）の原因特定とデータソースからの正しい数値算出

## 2. 実装・集計結果の確定と修正
- [x] 定義恒等式 $\mathrm{VSR} = \mathrm{VRR}(1 - \mathrm{ASR}_{\text{valid}})$ および $\mathrm{ASR}_{\text{all}} = \mathrm{VRR} \cdot \mathrm{ASR}_{\text{valid}} + (1 - \mathrm{VRR}) \cdot \mathrm{ASR}_{\text{invalid}}$ に基づく集計・修正
- [x] Table 2, Table 10, Table 11（VRR, Cond. ASR, VSR 追加）などの表データの更新・整合化
- [x] MergeAlign と AlignMerge の用語・評価有無の記述整理（Table 14 等の実行時間表との一致）

## 3. 本文 (flmsec_EN.tex) の論旨・記述修正
- [x] Abstract / Introduction の英語表現・文法・用語の修正（`metrics` -> `protocol`, `indicates` -> `indicate`, `a identical` -> `an identical`, `be assessed` -> `should be assessed`, `SafetyUtility` -> `safety--utility`）
- [x] Validity チェックの定義の修正（実効ルールである empty, word repetition <20%, numeric >60% に限定・整合）
- [x] "linguistically valid" 等の過大表現の置き換え（`non-degenerate output under our rule-based checks` 等）
- [x] Harmfulness Evaluator の統合規則・判定基準の明記および要約表（Table X）の作成
- [x] "False Unsafe" / "False Safe" の表現緩和（`Apparent Unsafe under a Single Evaluator`, `Apparent safety under degeneration` 等）
- [x] 新規性の主張の再構築（単なる新指標提案ではなく、 Secure Merge におけるパラメータ干渉・測定交錯の定式化）
- [x] Llama-2 checkpoint 名表記、LoRA 訓練時の prompt loss に関する制限記述の追加
- [x] Appendix C.3 の誤字修正 ("Tabless 6" -> "Table 6")

## 4. 表・図および付録・Checklist の改善
- [x] Valid responses / Total responses ($N_{\text{valid}}/N$) または分母の明記
- [x] Utility の集約方法（算術平均等）の定義明記
- [x] NeurIPS / FLMSEC Checklist の全項目（Theory [N/A], Broader Impacts, Safeguards, Licenses/Asset Table, LLM Usage）の正確な記述への修正
- [x] Asset / License 表を Appendix に追加

## 5. 検証と最終確認
- [x] 仮想環境 (`source venv_v3/bin/activate`) 下での `flmsec_EN.tex` の LaTeX コンパイル確認（PDF 62 ページ出力成功）
- [x] 表、本文、付録間の数値・用語の完全な整合性確認
- [x] `walkthrough.md` の作成
