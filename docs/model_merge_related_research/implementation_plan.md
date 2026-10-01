# 関連研究におけるモデルマージ手法の調査

指定された10本の論文（URL）を精読し、関連研究においてどのようなモデルがマージされているかを調査します。

## 調査目的
- 各論文におけるマージ対象のモデルが「既存のモデル」か「ファインチューニング（FT）されたモデル」かを特定する。
- 既存のモデルの場合は、そのモデル名を抽出する。
- FTされたモデルの場合は、使用されたハイパーパラメータおよびFTデータセットの情報を抽出する。

## 調査対象論文
1. [LREC 2024](https://aclanthology.org/2024.lrec-main.647.pdf)
2. [OpenReview](https://openreview.net/pdf?id=uV8LGh2DCx)
3. [NAACL 2025](https://aclanthology.org/2025.naacl-long.254.pdf)
4. [NeurIPS 2022](https://proceedings.neurips.cc/paper_files/paper/2022/file/70c26937fbf3d4600b69a129031b66ec-Paper-Conference.pdf)
5. [arXiv:2310.12808](https://arxiv.org/pdf/2310.12808)
6. [arXiv:2603.21705](https://arxiv.org/pdf/2603.21705)
7. [arXiv:2512.16245](https://arxiv.org/pdf/2512.16245)
8. [arXiv:2411.06824](https://arxiv.org/pdf/2411.06824)
9. [ACL 2025](https://aclanthology.org/2025.acl-long.1055.pdf)
10. [arXiv:2503.17239](https://arxiv.org/pdf/2503.17239)

## 実施計画
1. `wget` を用いてPDFをダウンロードし、`pdftotext` でテキスト化する。
2. 各論文のテキストから、モデル名、ハイパーパラメータ、データセットに関する記述を検索・抽出する。
3. 調査結果をまとめ、ユーザーに報告する。
