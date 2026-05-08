# LaTeXからMarkdownへの変換および不要部分の削除計画

現在の `論文.md` はLaTeXの文法（`\section`、`\begin{equation}`、大量の `%` コメントなど）で書かれています。これを読みやすい**純粋なMarkdown形式の詳細な論文**へと変換します。

## Proposed Changes (変換内容)

1. **不要なコメント・メモの完全削除**
   - 行頭や行中にある `%` 以降のコメント文（過去のメモ、古い表のデータなど）をすべて削除し、文書をスッキリさせます。
   - 不要なLaTeXのレイアウトコマンド（`\maketitle`, `\FloatBarrier`, `\onecolumn`, `\appendix` など）を削除します。

2. **見出しと装飾のMarkdown化**
   - `\section{...}` $\rightarrow$ `# ...`
   - `\subsection{...}` $\rightarrow$ `## ...`
   - `\subsubsection{...}` $\rightarrow$ `### ...`
   - `\paragraph{...}` $\rightarrow$ `#### ...`
   - `\textbf{...}` $\rightarrow$ `**...**`
   - `\emph{...}` $\rightarrow$ `*...*`

3. **数式のMarkdownネイティブ化**
   - `\begin{equation} ... \end{equation}` $\rightarrow$ ブロック数式 `$$ ... $$`
   - インライン数式はそのまま `$ ... $` として維持します。
   - 論文中の不要な `\label{...}` や `\ref{...}` は読みやすいテキスト参照（「図X」など）に変換するか削除します。

4. **リストと図表の変換**
   - `\begin{itemize}` や `\begin{description}` をMarkdownの箇条書き（`- ` や `- **項目**:`）に変換します。
   - `\begin{figure}` 環境を Markdownの画像リンク `![caption](figures/...)` に変換します。
   - `\begin{table}` 環境のLaTeXテーブルを、可能な限りMarkdownの表形式（`| Column | Column |`）にパースして変換します。

5. **引用の整理**
   - `\cite{...}` を `[Cite: ...]` のような読めるテキストに変換し、生コード感をなくします。

## Verification Plan
Pythonの変換スクリプトを作成し、`docs/07_paper/論文.md` を直接上書きしてフォーマットを綺麗にします。
処理後、数式や表が正しくMarkdownとしてレンダリングできる状態になっているかを確認します。

---
## User Review Required
この計画で変換処理を一気に実行してよろしいでしょうか？（LaTeXのソースコードは失われ、純粋なMarkdownファイルになります）
よろしければ承認をお願いいたします。承認後、直ちにスクリプトを実行してクリーンな論文ドキュメントを生成します。
