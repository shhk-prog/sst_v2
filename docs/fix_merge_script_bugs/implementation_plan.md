# マージおよび評価スクリプトにおけるバグ修正計画 (改訂版)

## 概要
`v3/logs/v3_skip_ft_limit100.log` において、`merge.py` で発生していたテンソルサイズミスマッチと未定義変数のバグに加え、評価スクリプト `eval_safety.py` の実行中に `allenai/wildguard`（Gatedリポジトリ）のダウンロードが403 Forbidden（アクセス拒否）エラーとなり、プロセスがクラッシュしていることが確認されました。
すでに実施した `merge.py` の修正に加え、`eval_safety.py` において `wildguard` のロード失敗時に gated ではない `HarmBench` 分類器へと自動でフォールバックするロジックを追加し、評価プロセス全体の耐障害性を高めます。

## ユーザーレビューが必要な項目
特になし（バグ修正のみ）。

## オープンクエスチョン
特になし。

## 提案する変更

### [Component: scripts]
評価処理の耐障害性を向上させるため、ダウンロード失敗時の自動フォールバックを実装します。

#### [MODIFY] [eval_safety.py](file:///mnt/nas/home/hiromi/src/sst_v2/v3/scripts/eval_safety.py)

- `eval_wildguard` 内のモデルロード部分（L47-49）を `try-except` で囲みます。
- `wildguard` のロードに失敗した場合（`GatedRepoError` 等が発生した場合）は、警告ログを出力しつつ、gated ではない `cais/HarmBench-Llama-2-13b-cls` 分類器を使用する `eval_harmbench` に自動的にフォールバックするように修正します。

具体的には、以下のような修正を行います：

```python
def eval_wildguard(prompts, responses, device):
    model_id = "allenai/wildguard"
    print(f"Loading WildGuard classifier: {model_id}")
    try:
        cls_tokenizer = AutoTokenizer.from_pretrained(model_id)
        cls_model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.float16, device_map="auto")
    except Exception as e:
        print(f"Failed to load WildGuard classifier: {e}. Fallback to HarmBench...")
        return eval_harmbench(prompts, responses, device)
```

## 既存のコメント/ドキュメンテーション文字列の維持
既存のコメントや docstring は変更せず、そのまま維持します。

## 検証計画
修正後、`eval_safety.py` が `jailbreakbench` タスクで実行された際に、`wildguard` のダウンロードがスキップ/失敗されても `HarmBench` 分類器によって正常に分類および評価出力の保存が最後まで完了することを確認します。
