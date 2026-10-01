# Table Generation Scripts (flmsec.tex) 修復・アーキテクチャ統一計画

ご要望の通り、`generate_case_study.py` や `generate_gpu_table.py` などの表生成・置換スクリプト群について、`generate_flmsec_hyo.py` と同様の「一旦別ファイル（LaTeX断片）に出力し、別の置換スクリプトで `flmsec.tex` に反映させる2段形式」にアーキテクチャを統一します。
また、現在ハードコードされているAUC値なども `vllm` の結果から動的に算出して埋め込むように改修します。

## 背景と課題
現在、`generate_gpu_table.py` は表文字列を生成した後、同一スクリプト内で直接 `flmsec.md`（現在は `.tex` が正）を置換しようとしています。また `replace_case_study.py` には `0.2935` などの Pareto AUC の値がハードコードされており、結果が変わっても追従できませんでした。

## 修正内容 (Proposed Changes)

1. **2段階パイプラインへの分離**
   - **Step 1 (Generate):** 各 `generate_*.py` は計算や抽出を行い、生成されたLaTeX表文字列を `/mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/` 下の中間ファイル（例: `case_study_latex.tex`, `gpu_table_latex.tex`, `auc_table_latex.tex`）に書き出します。
   - **Step 2 (Replace):** 各 `replace_*.py` はその中間ファイルを読み込み、`flmsec.tex` の該当箇所（表全体）を正規表現で安全に置換します。

2. **`generate_case_study.py` と `replace_case_study.py` の改修**
   - **AUCの動的算出:** `generate_case_study.py`（または共通モジュール）内で `pareto_auc.py` の関数を利用して、`vllm` の最新結果（`/mnt/nas/home/hiromi/src/sst_v2/v3/results/vllm/debug_limit320`）から Validity-aware Pareto AUC を計算します。ハードコードを撤廃し、算出した数値を `auc_table_latex.tex` として出力します。
   - **Case Study定性的評価の出力:** プロンプトと応答例を自動抽出した後、手動で付与している定性的ラベル（Output validity, Harmful compliance, Interpretation）と結合した **5列のLaTeX表** を組み立て、`case_study_latex.tex` として出力します。手動ラベルは辞書としてスクリプト内に持たせます。表のキャプション・表注（Valid / Invalidの定義など）も正確に出力に含めます。
   - **replace側:** `flmsec.tex` を開き、正規表現で AUC表 と Case Study 表の両方を中間ファイルの内容に置換します。

3. **`generate_gpu_table.py` の改修**
   - **generate側:** GPUプロファイルから時間を集計してLaTeX表を組み立てる機能のみを残し、結果を `gpu_table_latex.tex` に出力します。
   - **replace側:** 新たに `replace_gpu_table.py` を作成（または既存の `replace_cost_tables.py` などに統合）し、`flmsec.tex` 内のGPU表を置換します。

4. **対象ファイルパスの修正 (`flmsec.md` -> `flmsec.tex`)**
   - 全ての置換スクリプトで、最終的な置換対象を `.tex` ファイルに変更します。

## 実行環境についての制約
スクリプトの実行時には、ご指定通り必ず `source venv_v3/bin/activate` を実行してから処理を行うか、スクリプト内でパスを解決するよう徹底いたします。

## 懸念事項・確認事項 (User Review Required)

> [!IMPORTANT]
> - Case Studyの表を「応答例」と「手動ラベル」の5列で統合しますが、モデル（vLLM）を再実行して応答例（Response Example）が変わった場合、スクリプト内に固定で持たせる手動ラベル（Valid等）と矛盾する可能性があります。再実行時にはこの矛盾が無いか、著者が手動でラベル側の辞書を修正する必要があるという前提でスクリプトを構築してよろしいでしょうか？

この統一方針でよろしければ、お知らせください。直ちに実装に入ります。
