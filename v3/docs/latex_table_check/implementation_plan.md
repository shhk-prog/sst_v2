# LaTeX表数値確認および不足データの追記計画

## 背景
ユーザーからの依頼により、`/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec.tex` 内の表において、全ての結果が含まれているか、および数値が `vllm` の結果として正しいかを確認しました。

## 確認結果

1. **数値の正当性 (vllm結果との一致)**
   `scripts/analysis/generate_flmsec_hyo.py` を修正して `vllm` ディレクトリ (`results/vllm`) の結果を再集計したところ、`flmsec.tex` の表 `tab:evaluation_main_alpha=0.6_1` に記載されている数値は**完全に一致しており、間違いはありません**でした。

2. **結果の網羅性 (不足データの有無)**
   集計結果によると、`safety+code`, `safety+math`, `safety+medical` の3パターンの他に、**`safety+math+code+medical` (4つの専門モデルと安全モデルの同時マージ) の結果が存在しますが、現在の `flmsec.tex` のメイン表からは欠落しています。**

   `safety+math+code+medical` パターンで集計された手法:
   - `dare`
   - `data_free_sst`
   - `della`
   - `sst` (diagonal_sst_main)
   - `matena_fisher`
   - `task_arithmetic`
   - `ties`
   *(※ `safemerge`, `led_merging`, `mergealign` については当該パターンでの実行結果がないようです)*

## 提案する変更 (Proposed Changes)

`flmsec.tex` の表 `tab:evaluation_main_alpha=0.6_1` に、不足している `safety+math+code+medical` の行を追記します。

### [MODIFY] `flmsec.tex`
- 行 391 付近 (`safety+medical` の後、`\bottomrule` の前) に、`safety+math+code+medical` パターンの結果を追記します。
- `data_free_sst_main` を `data_free_sst` に、`diagonal_sst_main` を `sst` に置換するなど、他の行の表記ルールに統一します。

## Open Questions

- メインの表 `tab:evaluation_main_alpha=0.6_1` に `safety+math+code+medical` パターンを追加してしまってよろしいでしょうか？（ページ幅や論文の構成上、付録に回す予定だった等があればお知らせください）
