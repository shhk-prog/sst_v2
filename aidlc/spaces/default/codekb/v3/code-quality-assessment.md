# コード品質評価: v3

## 概要評価（3 段階）

| 観点 | 評価 | 根拠 |
|---|---|---|
| 命名の分かりやすさ | good | 関数名と引数名が手法の用語と一致している（`merge_sst`, `sst_ratio`, `k_ratio`） |
| 関数の大きさ | fair | `merge_sst`（約 190 行）と `execute_merge`（約 370 行）が長く、分岐が深い |
| エラー処理 | fair | 失敗メタデータの記録と再試行はある。一方、黙ってフォールバックする箇所がある（StrongREJECT → string_matching、chat template なしでの再実行、data_prep のプレースホルダ） |
| テストの存在 | poor | 規約フックの unittest と、ダミーモデルでの統合スクリプトだけ。merge の数値（マスク比率、λ の分布）を検証するテストはない |
| 重複 | poor | `steering_hook.py` の重複。集計スクリプト間で指標抽出ロジックがコピーされている（`generate_*_tables.py` 各種）。手法グループの定数が `mergers/constants.py` と `merge_eval_parallel.py` L10-20 で二重定義 |
| 死にコード | fair | 一回限りの `fix_*.py` / `replace_*.py` が多い。README の記載パスが実体と違う。`config_*.yaml` の `data.fim.epsilon` は読まれない |

リポジトリ外の v1 / v2 は本評価の対象外である（照合のために読んだ範囲の所見は「論文・v1・v2・v3 の照合」節の末尾に分けて書いた）。

## テスト、Lint、CI

- テスト: `scripts/tests/`（`unittest` 1 本、統合スクリプト 1 本）。カバレッジ設定なし
- Lint / Formatter: なし（`pyproject.toml` もない）
- CI/CD: なし
- ドキュメント: `README.md` は詳細。コメントは日本語中心

## 技術的負債

1. 集計と論文表のスクリプトに、他マシンの絶対パス（`/Users/saki/lab/src/sst_v3/...`）と NAS の絶対パスが混在している
   - **後続の計画**: 本インテントで使う表の再生成スクリプトは、既存の `scripts/analysis/` を直すのではなく、`v5/` に新しく実装する。生成した表も `v5/` に出力する（研究者本人の方針。今回の逆解析では `v5/` もスクリプトも作っていない）
2. 結果ファイル名の新旧 2 方式が同じディレクトリに混在している（`api-documentation.md` の「カバレッジの偏り」）
3. 有害判定の定義が集計スクリプトごとに違う（`generate_flmsec_hyo.py` は HarmBench 分類器と各ベンチ分類器の OR。`recompute_all_tables_unified.py` はさらに `unsafe` / `compliant` も含める）
4. `evaluators/` と `baselines/` は gitlink だが `.gitmodules` がない。`論文/` は git 未追跡
5. 結果 JSON を事後に書き換える修正スクリプトがある（評価の再現手順が複数段になる）
6. merge の経路に乱数 seed の固定がない（`merge.py`, `mergers/` に `manual_seed` がない）。アブレーションの `random` マスクは実行ごとに変わる（`sst.py` L146, L171）
7. `merge.py` L125: `merge.main.k_values` が空の設定で `--k` を省略すると IndexError（アブレーション設定は空。`config_ablation.yaml` L66）
8. merge 済みモデルのマスク比率や λ の統計が記録されない（`merge_sst` は `fisher_weighted` 以外で統計を返さない。`sst.py` L28, L202）。SST が退化していても結果ファイルからは分からない
9. `fisher_weighted` は対象外のパラメータ（RMSNorm の weight など）を 0 にする（`sst.py` L74-101 が対象判定 L103 より前にあり、FIM にない名前は `get_fim_tensor` が 0 を返す。`fim.py` L159-160）。`fisher_weighted` の結果を使うかどうかを確認する必要がある（`config_main2.yaml` L65 で使われる）
10. SST の提案論文 SAGAI_EN_sst の設定のうち、v3 のコードで選べないものがある: モジュール種別の層重み（`lm_head` 1.5、attention 1.2、MLP 0.8。`main.tex` L1149-1164）、全パラメータでの top-k（L1133）、soft mask の「log-scale normalization」（L1132）、LoRA アダプタ単位の merge（L1093）。コードの層 prior は層番号の関数だけである（`utils.py` L84-101）。これらはリポジトリ外（v1）の実装にはある（「論文・v1・v2・v3 の照合」節）
11. SAGAI_EN_sst の実験（Llama-3.1-8B、A5 / A6 / A7 の LoRA、RepliQA / Alpaca）を走らせる設定やスクリプトは v3 にない。`configs/` と `scripts/` の grep で RepliQA と Llama-3.1 に当たるのは `scripts/steering_hook.py`（L44 の禁止キーワード、L117 と L123 の許可モデル）とそのコピーだけである。**論文の数値を出したコードと結果は、リポジトリ外の `v1/`（ワークスペース直下）にある**（`v1/core/sst_merge.py` ほか。根拠は「論文・v1・v2・v3 の照合」節の代表セル照合）。前回までの「所在は未確認」は、本実行で v1 を読んで解消した

## 本インテントに影響する所見

以下は、SST-Merge が他手法と差を出せなかった理由の考察と、結果の再集計に直接かかわる。SST-Merge の提案論文 `論文/SAGAI_EN_sst/main.tex` を仕様として読み、論文の数値を出した v1 と照合した。判定の語は次のとおり。

- **コードで確認**: コード（と config.json）を読んで確かめた事実
- **論文で確認**: SAGAI_EN_sst のソースに書かれている事実（行番号つき）。論文の表の数値を本エージェントが比べた結果もここに含め、その旨を書く
- **コードで否定**: コードを読んで成り立たないと分かったもの
- **未検証（要データ）**: 機構はコードから言えるが、実際に起きているかはキャッシュや結果を読まないと分からないもの
- **仮説**: 上記のどれでもない推測

### 仮説 (a)〜(d) の判定

#### (a) SST は「上位 20% の座標に限定した task_arithmetic」で、同じ α では注入する安全成分が少ない — **コードで確認 ＋ 論文で確認**（v3 での影響の大きさは未検証）
- コード: `task_arithmetic` は mergekit の `linear` に写像され（`scripts/mergers/constants.py` L19）、safety の重みは α、各 utility は (1−α)/n である（`scripts/mergers/mergekit.py` L28）。形状が同じテンソルでは θ₀ + (1−α)δ̄_u + αδ_s になる（mergekit の `linear` は重みの正規化付き平均という外部仕様による）。SST の主設定は、対象 7 モジュールの各テンソルで λ の上位 20% の座標にだけ同じ式を使い（`scripts/mergers/sst.py` L177-181, L190-192）、残りは θ̄_u のまま残す。対象モジュールでは SST = task_arithmetic ⊙ mask ＋ θ̄_u ⊙ (1−mask) が厳密に成り立つ
- 論文: これはコードの誤りではなく、論文が定義した手法そのものの性質である。interpolation の式は論文の L661-677 とコードで一致し、論文自身が「Task Arithmetic を座標ごとに一般化したもの」と書いている（L678）。TA の定義 θ_base + αΔ_s + (1−α)Δ_u（L982, L1101）も mergekit の `linear` の写像と同じである
- 論文の表（本エージェントの比較）: A5 + A7 では、SST Interpolation の点は TA の曲線とほぼ重なるか下にある（例: TA α=0.30 が JB 86.8% / RepliQA 40.40%、SST k=5% α=0.70 が 86.8% / 37.00%。`tab:res_a5_base` L1206、`tab:res_a5_sst_5` L1270）。同じ α で比べると SST は安全側に弱い（α=0.6 で TA 96.4% / 20.16%、SST k=20% 83.0% / 39.31%）。つまり (a) の構造は論文の実験でもそのまま現れている
- v1 の実装でも同じ構造である（リポジトリ外）。v1 の TA は LoRA の A / B 行列の要素に `[1−α, α]` の重みを掛けた和（`v1/scripts/merging/baseline_merge.py` L296-318、重みは `run_all_merges_hard.py` L272）、SST Interpolation は同じ式にマスクを掛けたもの（`v1/core/sst_merge_interpolation.py` L307-311）で、論文の TA の数値は「GEVP 無効の補間」の数値と 16 桁まで一致する（代表セル照合の No.1）
- 帰結: 論文は手法を α ごとではなく safety–utility 曲線（Pareto）で比べている（L806, L1772-1773）。FLMSEC と同じく α=0.6 だけで比べると、SST は「安全成分が少ない手法」として見える。これは評価方法の選び方による差であり、v3 の結果を SST に有利・不利なく読むには、同じ JB での有用性（または同じ有用性での JB）で比べる必要がある（仮説。v5 での再集計の方針）
- 2 手法が違うのは対象モジュール以外である。norm などは SST が θ̄_u のまま（L103-105）、`linear` では αθ_s + (1−α)θ_u（θ_s の norm は θ₀ と同じ）。語彙 32001 の embed / lm_head は SST では θ₀（L50-55）。mergekit での扱いは未確認（V9）
- 補足: SAGAI_EN_sst の表で SST が TA を上回るのは A6 + A7（Alpaca）で、特に Additive soft（`tab:res_a6_sst_soft`）である。v3 の主設定は Interpolation の hard mask で、Additive はアブレーションだけ、soft はどこでも使われていない（`config_ablation.yaml` L87-93）

#### (b) fp16 の FIM がアンダーフローしてマスクが全 1 になり、SST が task_arithmetic と同じになる — **機構の一部をコードで確認／一部をコードで否定、発生の有無は未検証（要データ）、論文に記載なし**
- 論文: SAGAI_EN_sst は FIM の数値精度、正規化、ラベルの取り方を書いていない。論文の設定（Llama-3.1-8B）でどの精度を使ったかも分からない。v1 では FIM を LoRA パラメータの勾配から作り、モデルは fp16 または bf16 で読む（`v1/core/sst_merge.py` L1047-1051、`run_all_merges_interpolation.py` L246-250）。勾配の累積は fp32 ではなくモデルの dtype のままの可能性があるが、未確認である
- 否定される部分（v3）: 勾配の二乗と累積は fp32 で行う（`scripts/mergers/fim.py` L21 で fp32 テンソルを用意し、L61 で `grad.float()**2` を累積）
- 確認できる部分（v3、0 に落ちうる箇所は 2 つ）:
  1. 逆伝播は fp16 モデルで、loss scaling も autocast もない（`fim.py` L55-56、モデルは `merge.py` L511-541 で fp16）。約 6e-8 未満の勾配要素は fp16 で 0 になる
  2. merge 時に FIM を fp16 にキャストする（`fim.py` L161）。約 3e-8 未満の値は 0 になる。勾配が 1e-4 程度なら二乗は 1e-8 で、この範囲に入る
- 全 1 になる条件: `mask = (λ >= threshold)`（`sst.py` L181）なので、テンソル内で λ>0 の座標が k=20% 未満なら閾値が 0 になり、マスクは全 1 になる。λ=0 になるのは F_h=0 の座標である。つまり「F_h を fp16 にしたとき、テンソルの 80% 超が 0」が退化の条件である
- 逆向きの退化: F̄_b が 0 で F_h>0 の座標では λ = F_h × 約 1e6 になり、F_h が約 0.065 を超えると fp16 で inf になる。inf がテンソルの 20% 超を占めるとマスク比率は 20% を超える
- 論文との関係: (a) により、マスクが全 1 に退化すると SST Interpolation は TA と同じになる。論文の A5 の表で SST Interpolation が TA とほぼ同じ曲線になるのは、(a) の構造だけでも説明できる（退化の証拠ではない）
- Data-Free SST も同じ型の問題を持つ（δ_s² を fp16 で計算、`sst.py` L152。仮説）
- 確認方法は V1、V2

#### (c) F_h と F_b が不一致な条件で推定されている — **コードで確認。論文との差は「F_h を評価するモデル」と「F_b のデータ」の 2 点。F_h を Safety モデルで評価する点は v1 の原実装から引き継いだもの（v3 固有のずれではない）**（λ への影響の大きさは未検証）
- モデル: コードは F_b を各 θ_u で、F_h を θ_s で推定する（`scripts/merge.py` L552-563, L572-583）。論文は損失を θ_util の近傍で二次近似し、その曲率として F_t（t ∈ {b, h}）を定義する（L522-529）。式どおりに読めば、F_b と F_h はどちらも θ_util（ユーティリティモデル）で評価するものである（解釈を含む。論文は評価点を明示していない）。**v1 も同じ構造である**: F_b は「ベース + Utility LoRA」、F_h は「ベース + Safety LoRA」にそれぞれのアダプターを載せて推定する（`v1/core/sst_merge.py` L454-475、`run_all_merges_interpolation.py` L258-262）。論文の数値を出した原実装が F_h を Safety 側のモデルで評価しているので、論文の式の読み方（θ_util 近傍で評価）のほうが曖昧で、v3 のずれは v1 からの引き継ぎである
- F_h のデータ: 論文も Safety の学習データ（Jailbreak Trigger）を FIM に使う（L792-797）ので、ここは論文どおりである（論文で確認）。v1 も `response_dataframe.csv`（prompt + response）を使い、Safety の学習データと同じである（`v1/core/sst_merge.py` L66, L960-992）。ただし、Safety モデル自身の学習データ上で勾配を取るため、損失が小さく勾配も小さいと考えられる（仮説）。θ_util で評価すれば、まだ拒否を学んでいないモデルの勾配になり、この問題は起きない（仮説）
- F_b のデータ: 論文はユーティリティモデル A5 自身の学習データ RepliQA を使う（L792-797, L1082）。v1 は HF の RepliQA（`repliqa_0`）または Alpaca（`train`）からランダムに 500 件を取る（`v1/core/sst_merge.py` L998-1033）ので、論文と同じ考え方である。v3 は公開の benign データ（GSM8K / Evol-Instruct-Code / medical flashcards）で、各ドメインモデルの学習データと同じかは未確認（`scripts/data_prep.py` L21-71）
- 入力形式: v3 は全モデルで Llama-2 チャットの `[INST]` 形式とベースのトークナイザを使う（`fim.py` L45、`merge.py` L505）。v1 は chat template を使わない生テキスト（質問 + 回答、または prompt + response）である。論文に記載なし
- 損失の対象: v3 は全トークン（プロンプト含む、`fim.py` L54）。v1 も全トークンで、パディング位置（pad = eos）も `labels=input_ids` に含まれる（`v1/core/sst_merge.py` L180-184）。論文に記載なし
- FIM の定義: v3 は 1 件ごとの勾配二乗の平均（経験的 Fisher）で、論文の E[∇ℓ∇ℓᵀ] と同じ。**v1 は勾配の分散**（バッチ 4 件の平均勾配をバッチ数ぶん集めて `var` を取り、1e-6 を足す。モデルは train モード＝LoRA dropout 有効。`v1/core/sst_merge.py` L150-210）で、平均勾配を引くため経験的 Fisher とは一致しない（論文の式とは不一致）。ほぼ収束したモデルでは平均勾配が小さく、近い値になる可能性がある（仮説）
- 正規化: 主設定では `fisher_normalization` が off（`sst.py` L129-135）。論文に記載なし
- 集約: 多ドメインのパターンでは F_b だけ 3 モデルの平均を取る（`sst.py` L119-125）。論文はユーティリティが 1 つの設定だけ

#### (d) code と medical のドメインモデルが Llama-2-7b-hf から派生していない — **config.json で確認 ＋ 論文の前提に反することを論文で確認**（math は未検証）。v1 はこの前提を満たす
- HF キャッシュの `config.json` を読んだ（重みは開いていない。根拠は `technology-stack.md` の「外部モデルの系統」）
  - WizardCoder-Python-7B-V1.0: `_name_or_path` が `.../7Bcodellamapython_v1_2048_e3_2e_5/checkpoint-195`、`rope_theta: 1000000`、`max_position_embeddings: 16384`。CodeLlama-Python-7B からの FT
  - medalpaca-7b: `_name_or_path: ../llama-7b-hf/`、`rms_norm_eps: 1e-06`、`transformers_version: 4.28.0.dev0`。LLaMA-1 7B からの FT
  - WizardMath-7B-V1.0: config からは判定できない（`_name_or_path: /model_weights/`、`max_position_embeddings: 2048`）
  - 3 モデルとも `vocab_size: 32001`（ベースは 32000）
- 論文: SAGAI_EN_sst は model merge を「同じ事前学習モデルを共有する FT モデルの merge」に限ると明記している（L438-444）。実験ではユーティリティも Safety も同じベースに学習した LoRA である（L784-790, L1074-1087）。理論も LoRA のような小さな摂動の局所領域に限る（L486, L912-917）。code と medical の θ_u − θ₀ は事前学習の差分を含むので、この前提を満たさない
- v1（リポジトリ外）は、A5 / A6 / A7 のすべてを同じ Llama-3.1-8B-Instruct に LoRA（r=16、alpha=32、dropout 0.05、7 種の proj）で学習するので、この前提を満たす（`v1/scripts/FT/repliqa_tune.py` L22, L93-102、`alpaca_tune.py` L23, L94-103、`safety_tune.py` L25, L80-89）
- 帰結（v3、コードで確認）:
  - SST の mask=1 の座標では (1−α)·θ_u + α·θ_s、つまり LLaMA-1（または CodeLlama）の重みと Llama-2+LoRA の重みが座標単位で混ざる（`sst.py` L190-192）
  - 語彙が違うため、SST では utility の embed / lm_head が捨てられ、θ₀ のものが使われる（`sst.py` L50-55）。論文は `lm_head` に層重み 1.5 で安全成分を入れる設定（L1159）だが、v1 の LoRA は `lm_head` を対象にしない（下の照合表）ので、実際には論文もここに注入していない
  - merge 済みモデルはベースの config で保存される（`merge.py` L622-633）。safety+code では CodeLlama 系の重みが `rope_theta` の既定値（10000）で動く（影響は仮説。V7）

### SST が他手法と区別しにくくなる構造上の要因（論文を踏まえた再評価）

| # | 要因 | 根拠 | 判定 |
|---|---|---|---|
| S1 | 対象モジュールで SST Interpolation = task_arithmetic の部分集合。同じ α での差は「どの 20% を選ぶか」だけ | `sst.py` L177-192, `mergekit.py` L28。論文 L678 | コードで確認 ＋ 論文で確認（論文の A5 の表でも曲線がほぼ重なる。v1 でも同じ構造） |
| S2 | マスクはテンソルごとの top-k で、どのテンソルにも一律 20% が入る | `sst.py` L178-180 | コードで確認。論文は k を「全パラメータのうちの割合」とし（L1133）、v1 の実装も全 LoRA 要素を連結したグローバルな top-k（`v1/core/sst_merge.py` L283-291）なので、v3 は論文・v1 の設定とは違う |
| S3 | λ の 0 が多いとマスクが全 1 になり task_arithmetic と同じ、inf が多いと 20% を超える | `sst.py` L179-181, `fim.py` L161 | 機構を確認、発生は未検証（V1、V2）。論文に記載なし |
| S4 | λ の順位が \|δ_s\| や一様乱数と大差なければ、FIM を使う意味がない | `sst.py` L143-146, `config_ablation.yaml` L80-85 | 未検証（V3）。論文も Data-Free（大きさの proxy）が Full SST と同等の傾向と書いており（L1182-1183, L1761-1762）、FIM の比を使う効果は論文でも分離されていない（論文で確認）。**訂正**: v1 の Data-Free は Utility と Safety のアダプターの重みの二乗を別々に求めて比を取るので、比は一定にならず、選択は二つのアダプターの大きさの比で決まる（`v1/core/sst_merge_data_free.py` L29-69, L246-251）。前回の「同じ \|W\| を両側に使うと選択は大きさの順位だけになる」は誤読だった |
| S5 | Safety は rank-16 の LoRA で δ_s は低ランクで密。座標の 20% だけを残すと低ランク構造が壊れる可能性がある | `fine_tuning.py` L156-167, `sst.py` L190-192 | 仮説（V5）。論文はユーティリティも LoRA で、アダプタ単位で merge する（L1093）。v1 は A / B 行列を要素ごとに別々に混ぜ、保存後に `merge_and_unload` する（下の照合表）ので、マスクはΔW ではなく A / B の座標にかかっている |
| S6 | merge の演算は fp16。α·δ_s が丸めの刻みより小さい座標では安全成分が消える | `sst.py` L40, L190-192, `mergekit.py` L36 | 仮説（V4）。論文に記載なし |
| S7 | code / medical の θ_u は Llama-2 からの直接の FT ではない | 各 `config.json`、`sst.py` L44-51 | 系統は確認。論文の前提（L438-444, L486）に反することを論文で確認。影響の大きさは仮説。v1 は前提を満たす |
| S8 | embed / lm_head と config は全 α で θ₀ のもの | `sst.py` L50-55, `merge.py` L622-633 | コードで確認。論文の層重み表は `lm_head` を含む（L1159）が、v1 の LoRA は `lm_head` を対象にしないので、論文の実験でも `lm_head` への注入はない |
| S9 | 評価条件: gibberish は asr=0、判定は HarmBench 分類器と各ベンチ分類器の OR | `generate_flmsec_hyo.py` L81-88 | コードで確認。論文の指標は「JB Res.」で、v1 では TrustLLM の longformer 分類器（500 プロンプト）の拒否率（下の照合表） |
| S10 | アブレーションの冗長: Data-Free の `Fh only` と `magnitude` は同じ順位、`layerwise_uniform` は `nolayerwise` と同じ | `sst.py` L144, L152, L165-169, `utils.py` L90-91 | コードで確認。論文側の「A5 の Data-Free k=10% と k=20% の表が全セル同じ」は貼り間違いではなく、v1 の結果ファイル自体が同じ値を持つことが原因と分かった（下の照合表の節） |

### SAGAI_EN_sst の主張を v3 の大規模実験で再現できるか（コードと設定だけからの判定）

| 論文の主張・設定 | v3 の設定 | 再現できるか | 根拠の種類 |
|---|---|---|---|
| ベースは Llama-3.1-8B（L784, L1064） | Llama-2-7b-hf（`config_main.yaml` L7） | できない（別のベース） | コードで確認 |
| ユーティリティは同じベースの LoRA（A5 RepliQA、A6 Alpaca、L1082-1083） | 外部のフル FT モデル 3 種、うち 2 種は系統が違う（`config_main.yaml` L8-11） | できない（論文の前提 L438-444 が崩れる） | コードと config.json で確認 |
| アダプタ単位の merge（L1093） | フルの重みで merge（`merge.py` L510-542） | できない | コードで確認 |
| Additive soft mask（主設定の一つ、L1132） | soft はコメントアウト（`config_ablation.yaml` L93） | v3 の結果には存在しない | コードで確認 |
| Interpolation hard、k = 5 / 10 / 20 / 50%（L1126） | 主設定 k=0.20 のみ。`config_ablation2.yaml` は 0.01〜0.20（L77） | k=20% のみ対応。5% と 10% は `config_ablation2.yaml` にあるが、結果があるかは未確認（V10）。50% はない | コードで確認、結果は未検証 |
| モジュール種別の層重み（L1149-1164） | 層番号の prior のみ、主設定は off | できない（実装がない） | コードで確認 |
| k は全パラメータでの割合（L1133） | テンソルごと | できない（実装がない。v1 はグローバルな割合） | コードで確認 |
| α を 0.05〜1.00 の細かい格子で掃引し曲線で比較 | α は 0.2 刻み、FLMSEC は α=0.6 で比較 | 部分的（曲線は 6 点で描けるが、小さい α の領域がない） | コードで確認 |
| F_b はユーティリティの学習データ（L792-797） | 公開 benign データ | 部分的（データの一致は未確認） | コードで確認 |
| F_b と F_h を θ_util の近傍で定義（L522-529） | F_h は θ_s で評価（v1 の原実装も同じ） | 論文の式の読み方による（原実装と同じ構造なので、「できない」とは言い切れない） | コードで確認、論文の読みは解釈 |
| ε=10⁻⁶、N=500、λ と補間の式 | 同じ | できる | コードと論文で確認 |
| 比較手法 TA / TIES / DARE（DARE は p=0.9、L1109-1120） | TA / TIES は対応、DARE は density 0.5 の `dare_ties` | 部分的 | コードで確認 |
| 指標 JB Res. と RepliQA / Alpaca | 4 ベンチの ASR と validity-aware 指標、Math / Code / Medical / General | できない（別の指標とタスク） | コードで確認 |
| 主張「SST は一貫して良いトレードオフ」（L846-848, L855） | — | 論文の表自体で A5 では支持されない（本エージェントの比較）。v3 で同じ傾向が出るかは結果の再集計による | 論文で確認（表の比較） |

まとめ: v3 の大規模実験は、SAGAI_EN_sst の数式（λ、hard mask、interpolation / additive、ε、N）をそのまま実装しているが、論文で SST の利点が出た条件（同じベースの LoRA どうしをアダプタ単位で merge、Additive soft、モジュール種別の層重み、グローバルな top-k、小さい α での曲線比較）はいずれも含んでいない。論文の数値を出したコードは v3 ではなく v1 である。さらに、論文の A5 の表では、v3 の主設定と同じ Interpolation hard でも SST の曲線は TA とほぼ重なる。したがって「v3 で SST が他手法と差を出せなかった」ことは、論文の結果とも矛盾しない（論文の表で確認、v3 の結果での確認は未実施）。

## 論文・v1・v2・v3 の照合

本節は、承認ゲートでの差し戻し（「v1〜v3 まで網羅的に確認して論文と照合して」）に対する照合結果である。貼り付けられた別の AI の照合メモ 7 項目は検証対象の主張として扱い、コードと結果ファイルを読んで一つずつ裏を取った。**v1 と v2 はこのリポジトリ（v3）の外にある**（ワークスペース直下の `v1/`、`v2/`）。読むだけで、プログラムも LaTeX のコンパイルも実行していない。数値は結果ファイル（JSON、`.tex`、`.txt`）を読んで確かめた。判定の語は「一致」「部分一致」「不一致」「論文が曖昧」「未確認」。

### 貼り付けメモ 1〜7 の判定

| # | 主張 | 判定 | 根拠（要点） |
|---|---|---|---|
| 1 | SAGAI 論文の数値を出したコードは v3 ではなく v1 にある（`v1/core/sst_merge.py` ほか 6 ファイル） | 概ね一致。ただし列挙のうち 2 つは誤り | 代表セル 7 件が v1 の結果ファイルと一致する（下の代表セル照合）。実装は `v1/core/sst_merge.py`（Additive）、`sst_merge_interpolation.py`、`sst_merge_data_free.py`。実際の掃引ドライバは `v1/scripts/merging/run_all_merges_hard.py`、`run_all_merges_interpolation.py`、`run_data_free_merge.py`、`baseline_merge.py`。`run_sst_merge_comparison.sh` は α=0.5 の単発で、FIM を使わない層重み付き補間（`merge_adapters.py` L235-275）を呼び、存在しない `sst_merge_v5/` に cd する。`run_all_experiments.sh` は v1 に存在しない `experiments/` と `analysis/` を呼ぶ（旧版は `v1/archive/experiments`, `archive/analysis`）。`latex_tables_output.tex` は A6 だけで、SST の Interpolation 列は `-`（`generate_latex_from_json.py` L55-65 が mask_type=hard だけ拾い、Interpolation 結果は mask_type=soft と記録されるため）。論文の k=5 Interpolation の列は 2 つの結果フォルダの混在（下の No.2） |
| 2 | Data-Free は Utility LoRA の重み二乗を F_b、Safety LoRA の重み二乗を F_h として別々に計算し、λ=(F_h+ε)/(F_b+ε)。前回の「同じ \|W\| を両側に使い比がほぼ一定」は誤り | 一致（前回の解釈を訂正） | `v1/core/sst_merge_data_free.py` L29-69（`compute_fim_from_lora`: アダプターの全テンソルの要素²を鍵のソート順に連結し 1e-6 を加算）、L246-251（`F_harm_reg / F_benign_reg`）、`run_data_free_merge.py` L196-203（Utility と Safety に別々に適用）。付録の `\|W\|`（L1142, L1762）は「両側に同じ値」ではなく各アダプターの大きさを指す、論文の表記の曖昧さ。ただし v1 の proxy は LoRA の A / B の各要素の二乗で、論文本文の Δ²（L747-761）でも v2 / v3 のフル重みのタスクベクトルの二乗でもない |
| 3 | ベースモデルの実体は Llama-3.1-8B-Instruct（付録が正。v1 `core/sst_merge.py` L42） | 一致 | `v1/core/sst_merge.py` L42 `meta-llama/Llama-3.1-8B-Instruct`。FT スクリプト（`repliqa_tune.py` L22、`alpaca_tune.py` L23、`safety_tune.py` L25）と全 merge ドライバも同じ。論文付録 L1064 が正で、本文 L784 の `meta-llama-3.1-8b` は略記 |
| 4 | α の刻み: Additive / Baseline は 15 点、Interpolation は 0.1〜1.00 の 0.1 刻み | 部分一致 | Additive / Baseline / Data-Free の 15 点は一致（`run_all_merges_hard.py` L56、`run_data_free_merge.py` L53）。Interpolation の 0.1 刻み 10 点は旧セット（`v1/eval/merged/ A7-7ep/interpolation/` の 20 ファイル/設定、`run_all_merges.py` L55）。現行ドライバ `run_all_merges_interpolation.py` L64 と結果フォルダ `v1/eval/merged/interpolation/` は 15 点。論文の Interpolation の列は 2 つの混在（No.2） |
| 5 | k: 表は soft, 5, 10, 20, 50%、v1 には 30% も含む | 一致（さらに 40% もある） | v1 の k は 5, 10, 20, 30, 40, 50（`run_all_merges_hard.py` L66、`run_all_merges_interpolation.py` L67、`run_data_free_merge.py` L50）。論文の表は 5, 10, 20, 50 と soft。v1 の「soft」の結果は `A5_A7_sst_k{5,10,20}_a*` のラベル付きで、k の値は名目だけ（論文 L1218 のコメント「sst soft k=20」で k=20 の run を使用） |
| 6 | F_h を Safety LoRA 側のモデルで評価する点は v1 の原実装でも同じで、v3 固有のずれではなく v1 からの引き継ぎ | 一致 | v1 は F_b を「ベース + Utility LoRA」、F_h を「ベース + Safety LoRA」で推定（`v1/core/sst_merge.py` L454-475、`run_all_merges_interpolation.py` L258-262）。v3 は θ_u,j と θ_s で推定（`scripts/merge.py` L552-583）で、構造は同じ。論文の式の読み方（θ_util 近傍）が曖昧 |
| 7 | v1 は全 LoRA 連結のグローバル top-k、soft mask は log の 5〜95 パーセンタイル正規化、モジュール種別 LAYER_WEIGHTS を実装。v3 はテンソル単位 top-k・層番号 prior・lm_head 除外 | 一致（補足あり） | v1: グローバル top-k は `sst_merge.py` L283-291、soft は L293-324（log(λ+1e-10) を 5〜95 パーセンタイルで [0,1] に線形正規化。10 万要素超はランダムサンプル）、LAYER_WEIGHTS は L344-353。補足: (1) v1 の LoRA は 7 種の proj だけで `lm_head` を持たないので `lm_head` 1.5 は実効なし、(2) v1 の Data-Free は別の重み（1.0 / 0.8 / 0.6）で既定は off（`sst_merge_data_free.py` L303-312, L320, docstring L329「未実装」）、soft も別方式（z-score のシグモイド、L287-290）。v3 側は KB の記述どおり（`sst.py` L177-192、`utils.py` L84-101） |

### 手順ごとの照合（論文・v1・v2・v3）

行番号は各版のルートからの相対パスで示す。v1 / v2 はリポジトリ外。

| 項目 | 論文（SAGAI_EN_sst） | v1（リポジトリ外） | v2（リポジトリ外） | v3 | 判定 |
|---|---|---|---|---|---|
| FIM の定義 | E[∇ℓ∇ℓᵀ]（L522-529） | バッチ勾配の分散 + 1e-6（`core/sst_merge.py` L150-210）。バッチ 4 件、train モード、パディングも損失対象 | バッチ勾配の二乗の平均（`scripts/merge/sst_merge_core.py` L4-36、eval モード）。ただし `run_sst_merge.py` はダミーテンソルで動くデモで実装は未接続 | 1 件ごとの勾配二乗の平均（`mergers/fim.py` L54-70） | v1 は論文と不一致（分散）。v2 core と v3 は一致 |
| FIM の対象 | アダプタ単位（L1093） | LoRA の A / B の全要素（`param_type='lora'`、L105-133） | requires_grad の全パラメータ | フル重みの 7 種の proj | v1 は論文と一致 |
| F_b の評価モデル・データ | θ_util の近傍、RepliQA / Alpaca（L792-797） | ベース + Utility LoRA。HF の RepliQA `repliqa_0` / Alpaca `train` からランダム 500 件、生テキスト（`sst_merge.py` L998-1033） | 設定のみ（`fim_benign_repliqa.json`、`llama2_sst_experiment.yaml` L18-19）。Fisher の merge は未実装 | 各 θ_u,j、公開 benign データ先頭 500 件 | v1 は論文と一致。v3 はデータが違う |
| F_h の評価モデル・データ | θ_util の近傍と読める。Safety の学習データ（L792-797） | ベース + Safety LoRA、`response_dataframe.csv`（prompt + response、`sst_merge.py` L960-992） | 設定のみ（`fim_harmful_beavertails.json`） | θ_s、`response_dataframe.csv` 由来の先頭 500 件 | 論文が曖昧。v1 → v3 は同じ構造（メモ 6） |
| λ と ε | f_h/(f_b+ε)、ε=10⁻⁶（L619-623, L1128） | `F_h/(F_b+1e-6)`。F にも 1e-6 が入っているので実効 ε は約 2e-6（`sst_merge.py` L210, L256） | `F_h/(F_b+1e-6)`（`sst_merge_core.py` L38-45） | `f_h/(f_b+1e-6)` 直書き（`sst.py` L137-138） | 一致（v1 の実効 ε が約 2 倍） |
| Data-Free の proxy | 本文 Δ²（L747-761）、付録・考察 \|W\|（L1142, L1762） | LoRA の A / B 要素² を Utility / Safety 別々に（`sst_merge_data_free.py` L29-69, L246-251）。Δ ではない | フル重みの (θ−θ₀)²（`sst_merge_core.py` L48-61）。suite は「自分 / 他モデル平均」の比で、Safety モデルを含まない（`merge_llama2_sst_suite.py` L226-243） | フル重みの Δ²（`sst.py` L150-163） | 論文が曖昧（本文と付録で違う）。付録 = v1、本文 = v2 / v3 |
| top-k の単位 | 全パラメータのうちの割合（L1133, L1144） | 全 LoRA 要素を連結したグローバル（`sst_merge.py` L283-291。argsort で k 個ちょうど。Data-Free は閾値 ≥ で同値すべて、`sst_merge_data_free.py` L280-285） | core はグローバル（`sst_merge_core.py` L64-82）、suite はテンソルごと（`merge_llama2_sst_suite.py` L246-253） | テンソルごと（`sst.py` L177-181） | v1 は論文と一致。v3 は不一致 |
| soft mask | σ(log(λ+δ)/τ)（L636-642）、Additive の既定で log-scale normalization（L1132） | log(λ+1e-10) を連結ベクトル全体の 5〜95 パーセンタイルで [0,1] に線形正規化（σ ではない。`sst_merge.py` L293-324）。Data-Free は z-score のシグモイド | テンソルごとの z-score のシグモイド（suite L238-244） | σ(log(λ+1e-8)/τ)、τ=k（`sst.py` L182-184）。未使用 | 付録の「log-scale normalization」は v1 の実装と一致。本文の式はどの版とも違う |
| 層重み | モジュール種別 1.5 / 1.2 / 0.8（L1149-1164） | `sst_merge.py` L344-353 と `sst_merge_interpolation.py` L56-65 が同じ値（鍵に部分文字列が含まれるか、`layer_type in key`）。`lm_head` は LoRA に無く実効なし。Data-Free は 1.0 / 0.8 / 0.6 で既定 off | なし | 層番号の関数（`utils.py` L84-101）、主設定は off | 論文 = v1（`lm_head` は名目のみ） |
| merge の単位と式 | アダプタ単位（L1093）。additive / interpolation（L651-677） | LoRA の A と B を別々に要素ごとに混ぜ（Additive: u + α·lw·mask·s、Interpolation: (1−w)·u + w·s）、保存後 `merge_and_unload`（`sst_merge.py` L521-626、`run_all_merges_interpolation.py` L336-367）。実効の ΔW は (B_u+wB_s)(A_u+wA_s) で交差項を含む | フル重み。core の "interpolation" は θ_util + α·mask·δ_s（論文の Additive に相当）、"additive" はノルムで正規化（`sst_merge_core.py` L85-106） | フル重みの差分。interpolation と additive は論文の定義どおり（`sst.py` L188-192） | 論文 = v1（交差項の影響は論文に記載なし）。v2 は名称が論文と逆 |
| interpolation の clip | clip(α·w_layer·m, 0, 1)（L661-677） | clip なし。layer-wise で α·1.2 > 1 なら Utility の重みが負になりうる（`sst_merge_interpolation.py` L307-311）。`merge_adapters.py` は min(·, 0.95) | — | `clamp(…, 0, 1)`（`sst.py` L191） | v1 は論文と不一致 |
| α の格子 | 表は 15 点（0.05〜1.00）、本文は 0.1 刻み（L806） | Additive / Baseline / Data-Free は 15 点。Interpolation は旧 10 点（0.1 刻み）と新 15 点が混在 | config は 0.0〜1.0 の 0.1 刻み 11 点。シェルは 0.3 / 0.5 / 0.7（`run_all_experiments_suite.sh`） | 0.0〜1.0 の 0.2 刻み 6 点 | 論文の表 = v1（混在） |
| k の格子 | soft と 5 / 10 / 20 / 50%（L1126） | 5 / 10 / 20 / 30 / 40 / 50 と soft。soft は k ラベルの run のうち k=20 を使用 | `soft, 0.05, 0.10, 0.20, 0.50`（config） | 主設定 0.20、アブレーションで 0.01〜0.20 | v1 は論文の上位集合 |
| 比較手法: TA | θ_base + αΔ_s + (1−α)Δ_u（L982, L1101） | 重み `[1−α, α]` の A / B 要素の和（`baseline_merge.py` L296-318）。数値は GEVP 無効の補間と同一 | mergekit `linear`（suite） | mergekit `linear`（`mergekit.py` L28） | 一致 |
| 比較手法: TIES / DARE | TIES density 0.5。DARE は p=0.9 で τ_s だけを疎にする（L1105-1120） | TIES は各アダプターの絶対値上位 50% を残して符号選出（L320-378）。DARE は**両方**のアダプターの A / B 要素を確率 0.9 で落として ×10（L381-416） | mergekit | `dare_ties` density 0.5、`normalize: True`（`mergekit.py` L40-47） | DARE の「τ_s だけ」は v1 のコードと不一致（論文の記述の誤りか、別実装かは未確認）。TIES は一致 |
| FT の LoRA | r=16、alpha=32、dropout 0.05、all-linear、A5 / A6 は 10 epoch、A7 は 5 epoch（L1065, L1082-1084） | 同じ値、7 種の proj（`safety_tune.py` L80-89）。A7 の epoch は 3 / 5 / 7 / 10 の結果が共存し、ドライバは 5ep（`run_all_merges_*.py`）、`run_sst_merge_comparison.sh` は 10ep、`safety_tune.py` 既定は 10（L81） | Llama-3-8B-Instruct の FT（`run_lora_ft.py`）。merge には未使用 | A7 に当たる Safety LoRA は r=16、3 epoch | 論文の A7 の epoch は、どのセルが何 epoch のアダプターか未確認 |
| 評価指標 | JB Res. と RepliQA / Alpaca のスコア。データ・判定器・件数の記載なし（L1772） | JB: LibrAI/longformer-harmful-ro（TrustLLM）の拒否率、500 プロンプト、greedy 256 トークン、判定不能時はキーワード（`scripts/FT/jailbreak_eval.py` L24-25, L77-123, L261）。有用性: ROUGE-1 の F 値の平均 ×100（`repliqa_eval.py` L57-60, L91-108）。RepliQA は `repliqa_0` の先頭 500 件、Alpaca は `train` の先頭 500 件 | 4 ベンチ + lm-eval（config のみ） | 4 ベンチの ASR と validity-aware 指標、Math / Code / Medical / General | 論文が曖昧。v1 で解決（未記載だった指標の実体） |

### v1 で新たに分かった事項（コードで確認。実行はしていない）

1. **ベンチ指標の実体**: JB Res. = TrustLLM の longformer 分類器による拒否率（`resistance_rate`）。RepliQA / Alpaca のスコアは ROUGE-1 F 値の平均（例: TA α=0.30 の `rouge1.mean` = 0.40396 → 40.40）。論文にこの記載はない
2. **評価データと学習データの重なり（未検証の影響）**: A5 は `repliqa_0` 全体で学習し（`repliqa_tune.py` L84）、評価は同じ `repliqa_0` の先頭 500 件である（`repliqa_eval.py` L57-60）。A6 も Alpaca の `train` で学習し、先頭 500 件で評価する（`alpaca_tune.py` L85、`alpaca_eval.py` L57-60）。学習時に件数を絞る処理（`select`）は見つからない。つまり有用性の指標は学習データ上のスコアである可能性が高い（学習と評価の分割は未確認）。FIM の F_b 用データも同じ分布から取る
3. **FIM のモデルにアダプターを載せる処理（実害は未検証）**: `v1/core/sst_merge.py` L498-519 の `_load_adapter_to_model` は、モデル側とアダプター側の鍵の末尾 3 要素（`q_proj`, `lora_A`, `weight` など）だけを比べて最初に一致したテンソルを代入する（L511-517）。末尾 3 要素にはレイヤー番号が含まれないので、標準的な PEFT の鍵形式を仮定すると、全レイヤーの同じ種類の LoRA に最初のレイヤーのテンソルが入る。`run_all_merges_hard.py` L382-403 は別の処理で、`adapter_key in name or name.endswith(adapter_key)` を使う。標準形式では名前に `.default` が入るため一致せず、何も載らない可能性がある（載った数のログもない）。どちらも、アダプターの実際の鍵と実行ログを開いていないので「疑い」の段階である。これらの経路の F_b / F_h は、意図した「ベース + 各アダプター」ではない点で勾配を取っている可能性がある
4. **マスクと FIM の並びの対応（未確認）**: FIM はモデルの `named_parameters` の順（`sst_merge.py` L117-120）、マスクの適用はアダプターの辞書の順（L548-575）で、並びが同じかの検査はなく、全長の一致だけを見る（L561）。Data-Free は FIM を鍵のソート順で作るが、merge は辞書の順に回す（`sst_merge_data_free.py` L49 と L433-451）。ソート済みの版は `FIMCalculatorDataFree` クラスの中に貼り付けられた別の `_merge_with_gevp`（L73-149）で、`self.fim_calc` などが存在せず呼ばれない（死にコード）
5. **Data-Free の k と layer-wise が結果に効いていない run（仮説）**: `v1/eval/merged/data_free/` の旧ラベル `A5_A7_data_free_k{5,10,20}_a*` では、k=5 / 10 / 20、layer-wise の有無で数値が同一である（`detailed_config_analysis.txt` L189-307）。A6 の `latex_tables_output.tex` では Data-Free の k=20 / 30 / 40 / 50 の 4 表（キャプションは L239, L268, L297, L326）が全セル同一で、k=5 と k=10 だけが違う。ドライバの `k_values` のコメントは「データフリー版では命名用」と書き（`run_data_free_merge.py` L50）、`use_layerwise` は「データフリー版では未実装」（`sst_merge_data_free.py` L329）。現行のドライバは k / 100 を `top_k_ratio` に渡す（L257-262）。仮説: 旧ドライバで作った soft mask の run が、k のラベルだけ違う複数の結果として残り、k=5 と 10 だけが修正後に再作成された。論文の A5 Data-Free で k=10% と k=20% の表が同一なのは、貼り間違いではなくこの元データによると考えられる
6. **soft mask の run は再現性が低い**: soft の log-percentile 正規化は 10 万要素超でランダムサンプルを使う（`sst_merge.py` L302-308）。A5 の α=0.3 で、同じ設定の `k5` / `k10` / `k20` ラベルの結果は JB 68.2 / 67.4 / 65.8% とばらつく（`sst_merge/merge_eval/A5_A7_sst_k{5,10,20}_a0.3`）。論文の soft の表はこのうち k=20 の run（65.8%）である
7. **合成の実体**: Additive / Interpolation / TA / TIES / DARE のどれも、LoRA の A と B を別々に要素ごとに混ぜる。ΔW の線形和ではないので、TA でも (B_u+wB_s)(A_u+wA_s) の交差項が入る。v3 のフル重みの差分を混ぜる実装とは別物で、論文の式（Δθ に対する式）とも直接は一致しない

### 論文の表と v1 の結果ファイルの代表セル照合

論文の数値は `論文/SAGAI_EN_sst/main.tex` の表、v1 の数値は結果 JSON（`resistance_rate`、`rouge1.mean`）を読んだもの。結果ファイルはすべて `v1/eval/merged/` 以下。

| No. | セル | 論文（JB, 有用性） | v1 の結果ファイル | 判定 |
|---|---|---|---|---|
| 1 | TA α=0.30（A5） | 86.8%, 40.40%（`tab:res_a5_base`） | `sst_merge/merge_eval/A5_A7_task_arithmetic_a0.3`: 0.868, 0.40396。`all_eval_results_summary.json` も 86.8（L12282-12288）。同じ値が ` A7-7ep/interpolation/merge_eval_interpolation/A5_A7_sst_interp_k5_nogevp_a0.3`（GEVP 無効）にもある（rouge1 が 16 桁まで同一） | 一致。論文の TA の数値は GEVP 無効の補間と同じモデルの結果 |
| 2 | SST Interpolation k=5% layer-wise なし α=0.70（A5） | 86.8%, 37.00%（`tab:res_a5_sst_5`） | ` A7-7ep/interpolation/merge_eval_interpolation/A5_A7_sst_interp_k5_a0.7`: 0.868, 0.36997（一致）。`interpolation/A5_A7_sst_interp_k5_a0.7`: 0.884, 0.36735（88.4%, 36.74% で不一致。`all_eval_results_summary.json` L29062 も 88.4） | 部分一致。論文の k=5 Interpolation の列は 2 つのフォルダの混在で、α=0.05 / 0.07 / 0.12 / 0.15 は `interpolation/`、α=0.1, 0.3, 0.7, 1.0 は ` A7-7ep/` の値と一致する（確認した点のみ。他の α は未確認） |
| 3 | SST Interpolation k=20% α=0.6（A5） | 83.0%, 39.31% | `interpolation/A5_A7_sst_interp_k20_a0.6`: 0.83, 0.39314 | 一致 |
| 4 | SST Interpolation k=50% α=1.0（A5） | 97.6%, 26.81% | `interpolation/A5_A7_sst_interp_k50_a1.0`: 0.976, 0.26814 | 一致 |
| 5 | Additive soft α=0.3、layer-wise なし（A5） | 65.80%, 60.66%（`tab:res_a5_sst_soft`、L1218 のコメント「sst soft k=20」） | `sst_merge/merge_eval/A5_A7_sst_k20_a0.3`: 0.658, 0.60659 | 一致（k のラベルは名目で、soft の run の一つ） |
| 6 | Additive soft α=0.40、layer-wise なし（A6） | 83.2%, 66.07%（`tab:res_a6_sst_soft`） | `sst_merge/merge_eval/A6_A7_sst_k20_a0.4`: 0.832, 0.66073 | 一致 |
| 7 | Additive hard k=5% layer-wise なし α=0.3（A5） | 70.80%, 60.58%（`tab:res_a5_sst_5`） | `sst_merge/merge_eval/A5_A7_sst_k5_a0.3_hard_full`: 0.708, 0.60576 | 一致（plain の `A5_A7_sst_k5_a0.3` は 0.682, 0.60512 で別の run） |
| 8 | A6 Interpolation k=5% α=0.80、TA α=0.50（A6） | 89.4%, 49.40% と 89.4%, 46.52%（KB の記録） | `detailed_config_analysis.txt` L118（GEVP 有効 α=0.80: 89.40, 49.40）と L145（GEVP 無効 α=0.50: 89.40, 46.52） | 一致（このファイルは ` A7-7ep/` のフォルダを読む） |
| 9 | A5 Data-Free k=5% Additive lw=False α=0.05 | 71.00%, 68.94%（`tab:res_a5_sst_data_5`） | 旧ラベルの `detailed_config_analysis.txt` L193（k=5 α=0.05: 68.40, 70.43） | 不一致（論文は修正後の新しい run と考えられる。新ラベル `data_free_k*_topk*` は未照合） |
| 10 | 論文の A5 Data-Free k=10% と k=20% の表が同一 | 全セル同一（L1411-1425, L1441-1455） | 旧ラベルの A5 Data-Free は k=5 / 10 / 20 が同一（`detailed_config_analysis.txt` L189-307） | 元データ側の性質（上の事項 5） |

論文の本文と付録の記述（A7 の 5 epoch、DARE が τ_s だけを疎にする、Data-Free の k が効く）は、この照合の範囲では次の点が未確認または不一致である: A7 の epoch（どのセルが何 epoch か）、DARE の対象（v1 は両方）、Data-Free の k の効き方（旧 run は効かない）。

### v1 → v2 → v3 の系譜と、数値を出した版

詳細は `architecture.md` の「v1 → v2 → v3 の系譜」。要点だけを書く。

- 論文（SAGAI_EN_sst）の数値を生んだのは **v1**（ベース Llama-3.1-8B-Instruct、A5 / A6 / A7 の LoRA、アダプター単位の merge、500 件の TrustLLM と ROUGE-1 の評価）。FIM の推定、グローバル top-k、soft の log-percentile 正規化、モジュール種別の層重みの 4 点は v1 にだけある
- **v2** は論文の数値を生んでいない。実装は Llama-2-7B の 3 ドメインモデルの merge（Safety モデルなし）のスキャフォールドで、ストリーミング merge で動くのは Data-Free（「自分 / 他モデル平均」の比）と Fisher 加重平均、LED、SafeMERGE 風、MergeAlign 風だけ。`sst_merge`（FIM 版）の指定は既定の TA の分岐に落ちる（`merge_llama2_sst_suite.py` L294-300）。`sst_merge_core.py` に FIM と λ とグローバル top-k の関数があるが、`run_sst_merge.py` はダミーテンソルで動くフック検証用のデモで、実モデルの merge には接続されていない。Llama-3 系の FT ベースライン（Safety Tax の確認）の結果とスクリプトも v2 にある
- **v3** は v2 の枠組み（Llama-2-7B、3 ドメインモデル、設定ファイル、steering_hook）に Safety LoRA と FIM 版 SST を実装し、評価を 4 ベンチの ASR と validity-aware 指標に替えた。論文の主張を再現する設定は持たない

### v1 / v2 の品質上の所見（照合のために読んだ範囲。評価の対象外）

- v1: ドライバは設定を先頭の定数で持ち、`input("gpu num:")` で GPU を尋ねる。`check_mask_stats.py` は存在しない引数 `top_k` を渡し（`SSTMerge` の引数は `top_k_ratio`）、`tests/test_data_free_merge.py` は自身のディレクトリから `sst_merge_data_free` を import するため、どちらも現状では動かない。`README.md` が指す `docs/` は v1 にない。`run_all_experiments.sh` は存在しないパスを呼ぶ
- v1: 結果フォルダが並存する（`eval/merged/{baseline,sst_merge,interpolation,data_free}` と先頭が空白の ` A7-7ep/`）。論文の表は複数のフォルダの値の混在で、どの表をどのフォルダから作ったかの記録が見つからない
- v2: `merge_llama2_sst_suite.py` は未実装の手法（`sst_merge`）を黙って TA に落とす。`run_sst_merge.py` はダミー実行

## 後続段階で要検証（数値の確認。今回は実行していない）

いずれも GPU ジョブは不要で、CPU で `torch.load` やファイル名の一覧を読めば足りる。テンソルや重み、結果を読むため、今回の逆解析では行っていない。V12 以降は v1 / v2（リポジトリ外）に関するもの。

| # | 確認内容 | 具体的な確認方法 |
|---|---|---|
| V1 | FIM の 0 の割合（fp16 キャスト後） | `cache/fim/harmful_safety_Llama2_SafetyFT_n500_seed{42,43,44}.pt` と `cache/fim/benign_{math,code,medical}_Llama2_*_n500_seed*.pt` を読み、各テンソル t について `(t.half() == 0).float().mean()` と `(t == 0).float().mean()`（fp32 のまま）を求める。F_h で 0.8 を超えるテンソルがあればマスクは全 1 に退化する |
| V2 | 実際のマスク比率と inf の数 | V1 のテンソルから `sst.py` L119-181 と同じ計算（fp16 キャスト、`λ = F_h/(F̄_b+1e-6)`、top-k、`>=`）を再現し、テンソルごとの `mask.mean()`（期待値 0.20）と `torch.isinf(λ).sum()` を記録する。パターンごとに F̄_b の組み合わせを変える |
| V3 | マスクの中身が FIM に依存しているか | 同じテンソルで `Fh/Fb`、`magnitude`（\|δ_s\|）、`random` のマスクの Jaccard 係数と、λ と \|δ_s\| の順位相関を求める |
| V4 | fp16 の丸めで安全成分が消える割合 | 対象テンソルで `|α·δ_s| < ulp_fp16(θ_u)/2` の座標の割合を求める（α=0.6） |
| V5 | 注入された安全成分の量 | 同じ α・seed・パターンの SST と task_arithmetic の merge 済みモデルについて、‖θ_merged − θ_u‖ と ⟨θ_merged − θ_u, δ_s⟩ をテンソルごとに比べる |
| V6 | WizardMath の系統 | WizardMath と Llama-2-7b-hf の各層の相対差分 ‖θ_u−θ₀‖/‖θ₀‖ を、WizardCoder、medalpaca と並べて比べる |
| V7 | merge 済み code モデルの位置符号化 | `models/merged/*safety+code*/config.json` の `rope_theta`（と `max_position_embeddings`）を読み、`base/` の WizardCoder 評価時の値（1000000）と比べる |
| V8 | FIM データが実データか | `data/fim/fim_benign_*.json` の先頭数件を読み、プレースホルダ（「Solve math problem 0」など）でないことを確かめる。`fim_harmful.json` の件数（1,400 の想定）も確かめる |
| V9 | mergekit 出力の語彙の扱い | mergekit 系の merge 済みモデルの `config.json` の `vocab_size` と、safetensors ヘッダの `lm_head.weight` の形状を比べ、embed / lm_head が θ₀ と θ_u のどちらに由来するかを確かめる |
| V10 | 論文に近い条件の結果が v3 にあるか | `results/vllm/debug_limit320/merged/seed*/*/*/ablation/sst/` のファイル名から、`k0.05` / `k0.1`（`config_ablation2.yaml`）、`additive`、`layerwise_*` の条件が実際に評価済みかを一覧する。あれば v5 の再集計で SAGAI_EN_sst の表と同じ形（k × variant × layer-wise、safety–utility 曲線）に並べる |
| V11 | 同じ JB での比較 | v3 の結果から、手法ごとに α を変えた safety–utility 曲線を作り、同じ安全性での有用性（または同じ有用性での安全性）で SST と task_arithmetic を比べる。論文の A5 / A6 の表と同じ読み方をするためで、(a) の影響の大きさを確かめる |
| V12 | v1 の FIM が意図したアダプターで計算されたか | v1 の `models/finetuned/adapters/FT_model/*/adapter_model.safetensors` の鍵（レイヤー番号を含むか）を読み、`_load_adapter_to_model` の鍵の末尾 3 要素の一致が全レイヤーで同じテンソルに当たるかを確かめる。`run_all_merges_hard.py` L387, L402 の一致条件が 1 件でも成立するかも同様に確かめる。実行ログ（「Applied N adapter parameters」）があれば照合する |
| V13 | v1 のマスクと FIM の並びの一致 | v1 のアダプターの辞書の順と、モデルの `named_parameters` の順（LoRA のみ）を比べる。Data-Free は `sorted(keys)` と辞書の順を比べる |
| V14 | v1 の各セルがどの A7（epoch）のアダプターか | `eval/finetuned/` の A7 の 3 / 5 / 7 / 10 epoch の結果と、各 merge 結果の `merged_model_path` のメタデータ、`merge_metadata.json`（models が残っていれば）から A7 の epoch を特定する。` A7-7ep/` と `interpolation/` の差（代表セル No.2）の原因もここで調べる |
| V15 | Data-Free の k が効かない run の特定 | `eval/merged/data_free/` の旧ラベルと新ラベル（`_topk*`）のファイルの更新日時と値を比べ、論文の `tab:res_a5_sst_data_*` と `tab:res_a6_data_free_*` がどのラベルから作られたかを確かめる |
| V16 | 評価データと学習データの重なり | v1 の A5 / A6 の学習に使った件数（`repliqa_tune.py` / `alpaca_tune.py` の `select` の有無）と、評価の先頭 500 件の重なりを確かめる |

### F5. 安全性の採点（コードで確認）
- 生成は greedy、最大 128 トークン、Llama-2 の `[INST]` 形式。θ₀ はチャット調整されていないベースモデルである
- 判定器はベンチごとに違う（HarmBench 分類器 / WildGuard / StrongREJECT の finetuned_gemma。StrongREJECT は例外時に黙って string_matching になり、スコアは連続値）
- gibberish（invalid）は `asr=0`（"assumed safe"）として記録される
- 表の有害判定は `harmbench_cls_output=="Yes"` OR `asr>0.5`（`generate_flmsec_hyo.py` L81-88）。論文本文は「共通の HarmBench Classifier」と書いており一致しない。表の "Original ASR" は、公式評価器の ASR_bench ではなく、この判定での全件比率である

### F6. 有用性の集計（コードで確認）
- ドメイン平均は構成ベンチの単純平均。General は mmlu、ifeval、alpaca_eval2 の平均（ヘッダは "General/Inst"）
- 同じ（手法, パターン, α, seed）に旧方式（`utility_math.json`）と新方式（`utility_math_gsm8k.json` など）の両方があると、後に読まれたファイルの値が採用される（glob の順序に依存）。`diagonal_sst_main` と `task_arithmetic` に該当する
- lm-eval は 0-shot、chat template あり。template を受け付けない場合は template なしで再実行される。条件がモデルごとに変わりうる

### F7. 結果の範囲と論文との対応（コードで確認）
- `results/vllm` には SST（`diagonal_sst_main`, `data_free_sst_main`）とアブレーションの結果がある。FLMSEC 論文は大規模評価の論文であり、提案手法の SST は意図的に載せていない（研究者本人の説明）
- SST-Merge の提案論文は SAGAI_EN_sst（`論文/SAGAI_EN_sst/main.tex`）で、SST の手順（FIM、λ、マスク、補間、Data-Free）とハイパーパラメータが書かれている。前回の「SST 固有の手順を書いた論文はない」は誤りだった。対応表は `architecture.md` の「論文（SAGAI_EN_sst）とコードの対応表」
- DLSP_hiromi2 は secure merge の提案論文で、SST はそれに特化した merge 手法という位置付けである。DLSP_hiromi2 には SST の手順は書かれていない
- SAGAI_EN_sst の数値は Llama-3.1-8B と A5 / A6 / A7 の LoRA による別の実験（リポジトリ外の v1）で、v3 の `results/vllm` とは対応しない（技術的負債 11、「論文・v1・v2・v3 の照合」節）
- 単発手法（safemerge, led_merging, mergealign, matena_fisher）は α スイープがない。4 ドメインパターンでは単一ドメイン専用の手法がなく、LED は medical にもない
- 予備実験（TrustLLM / BeaverTails、`results/vllm/preliminary/merged`）は主実験と別の指標体系である
- `data_prep.py` は取得に失敗するとプレースホルダの FIM データを書く（L31-35 ほか）。`data/fim/` の実データは未確認（V8）
