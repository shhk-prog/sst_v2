# flmsec.tex 修正の確認

## 変更内容
ユーザーからの指摘に基づき、`flmsec.tex` 内の複数の不整合および説明不足を修正しました。

1. **Safety Ave の定義と表現**
   - 誤って「Refusal-Filtered」と記載されていた箇所を `Safety Ave [Conditional ASR]` に修正しました。
   - `Safety Ave [Harmful Content]` が対象4ベンチマークのOriginal ASRのマクロ平均であることを明記しました。
   - 表内のヘッダーを `Safety Ave (Conditional ASR)↓` に修正しました。

2. **Validity-aware Pareto AUC の数式化**
   - 単なる文章による説明から、数式的な定義（$x$をConditional ASR、$y$を正規化有用性とし、$x \in [0, 1]$の範囲で台形則により積分）を追加しました。

3. **生成パラメータの具体化**
   - 「十分なサンプル数」という曖昧な表現を削除し、実際のコード（`eval_utility.py`）に基づき、「$n=1$ 個のシングルサンプル」および「温度 $T=0$ (greedy decoding)」であることを明記しました。
   - AlpacaEval 2 において「100件に固定」に表現を統一し、Judgeモデルを「`gpt-4-1106-preview`」と具体化しました。

4. **安全モデルとFisher推定データの説明**
   - 安全モデルの学習に用いたデータがTrustLLMの有害プロンプトと定型拒否文（"I'm sorry, but I cannot assist with that request."）の組み合わせであること、およびLoRAのパラメータ（rank=16, alpha=32, batch_size=4, max_length=512, epoch=3）を追記しました。
   - Fisher情報量推定に用いた有用性校正データが、各専門モデルの学習データそのものではなく、各ドメインを代表する公開データセットのサンプルであることを明記しました。

5. **評価ベンチマーク表 (Table 2)**
   - カラムを分割し、「データセット規模（全体の数）」と「本研究の評価件数（上限320件などのサンプリング後）」を明示することで、表内の矛盾を解消しました。

6. **文章の細かな修正**
   - taxonomy節の末尾を「安全性、有効応答率、有用性、および計算コストを併せて報告し、単一の指標に基づいて手法の優劣を結論づけない。」に変更しました。
   - Gibberish Nの定義を「Gibberish検出規則により無効応答と判定された応答数」と明確化しました。

## 確認事項
- `flmsec.tex` は正しくコンパイル可能な状態を維持しています。
- 全ての修正が実装コード(`pareto_auc.py`, `eval_utility.py`, `fine_tuning.py`)と矛盾しないことを確認しています。
