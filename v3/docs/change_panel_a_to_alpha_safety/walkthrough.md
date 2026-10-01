# パネル(a) の Alpha vs Safety 図への変更確認 (Walkthrough)

## 修正内容

パネル(a) をパネル(b)の構成と同様に、「Merge Strength ($\alpha$) vs Safety」 の図に変更しました。

### 1. 軸の設定とプロットデータ
- **X軸**: `Utility` から `Merge Strength ($\alpha$)` (0.0 から 1.0) に変更しました。
- **Y軸**: 引き続き `Harmful ASR (%) ↓` として、$\alpha$の変化に応じた安全性の推移をプロットしています。
- これにより、(a) が「$\alpha$ vs Safety」、(b) が「$\alpha$ vs Utility」と、横軸を統一した比較が可能になりました。

### 2. 標準偏差の帯 (fill_between)
- パネル(b)と同様に、各モデルの `means_saf - stds_saf` から `means_saf + stds_saf` の範囲を `fill_between` で塗りつぶし、データにばらつきの帯を追加しました。
- SST（Ours / Data-Free）は濃いめ（$\alpha=0.15$）、ベースラインは薄め（$\alpha=0.08$）とすることで、主要な手法がより目立つようにしています。

### 3. 不要な要素の削除
- X軸が Utility ではなくなったため、パネル(a)にあった `Invalid utility` のグレー背景や破線を削除しました。
- 同様に、`Baseline collapse` のテキストと矢印、また `Better` 矢印や `\alpha=0`, `\alpha=1` のマニュアルテキスト注釈など、これまでの Utility-Safety ペアに対する注釈を全て削除しました。

### 4. グラフのタイトルと凡例
- タイトルを `(a) Safety across merge strength` に変更しました。
- 凡例はパネル(b)同様にすっきりとまとめ、グラフの右上に配置しました。

## 確認事項
スクリプト `generate_three_panel_plot.py` を実行し、変更後の `pareto_three_panel.png` が正常に出力されることを確認しました。
