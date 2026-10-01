# SST-Merge

このリポジトリは、主に2つのバージョンで構成されています：

- **`v1/`**: 従来のコードベース（レガシー）。SST-Mergeの主要な実装、コアルーチン、評価パイプライン、過去の実験スクリプトなどが含まれます。詳細は [`v1/README.md`](v1/README.md) をご参照ください。
- **`v2/`**: 新しい実験環境（旧 `v2_experiments`）。トップ会議への投稿に向け、厳密性を重視してゼロから再構築されました。Mergekitの統合やクリーンな実験パイプラインが含まれます。詳細は [`v2/README.md`](v2/README.md) をご参照ください。
- **`docs/`**: プロジェクト共通のドキュメントや参考資料が格納されています。

## 環境構築

ルートディレクトリでの環境構築は以下の手順で行います：

```bash
python3 -m venv venv_sst
source venv_sst/bin/activate
# その後、作業するバージョンに応じてパッケージをインストールしてください：
# pip install -r v1/requirements.txt
# または
# pip install -r v2/requirements.txt
```
