# FLMSEC 論文 (flmsec_EN.tex) ベースモデル表記標準化 (Walkthrough)

ユーザー様からのご質問に基づき、`Llama-2-7B-base` という非公式・不正確なハイフン付き表記を検証し、学術論文・公式ハブ（Hugging Face Hub）として正確な表記へ完全に標準化いたしました。

---

## 修正内容の要約

### 1. 表記の不整合と修正理由
- **問題点**: `Llama-2-7B-base` は Meta 公式および Hugging Face Hub の正式識別名ではなく、非公式な通称表記でした。査読者から「独自のモデルか？」等の誤解を招くリスクがありました。
- **標準化後の表記**:
  - **本文 (Section 3.1 冒頭)**: `pretrained \texttt{Llama-2-7B} checkpoint (\texttt{meta-llama/Llama-2-7b-hf}) [31]`
  - **リスト・説明本文**: `pretrained \texttt{Llama-2-7B}`
  - **Asset Table (Table 5 / Appendix C.1)**: `Llama-2-7B & \texttt{meta-llama/Llama-2-7b-hf} & Base model initialization & Llama 2 Community License`

### 2. 影響範囲
- 本文 (Section 3.1), Appendix (Appendix C.1, Asset Table) 内の旧表記 `\texttt{Llama-2-7B-base}` をすべて一括置換し、論文全体で完全統一いたしました。

---

## 最終コンパイル結果

仮想環境 (`source venv_v3/bin/activate`) にて `pdflatex` コンパイルを実行し、全64ページの PDF ([`flmsec_EN.pdf`](file:///mnt/nas/home/hiromi/src/sst_v2/v3/docs/flmsec/flmsec_EN.pdf)) をエラー 0 件で生成完了いたしました。
