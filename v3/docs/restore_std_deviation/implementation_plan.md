# 標準偏差(帯)の再追加

## 概要
以前のステップで削除した標準偏差の塗りつぶし帯 (`fill_between`) を、パネル(a)およびパネル(b)のグラフに再度追加します。

## 変更内容
1. **パネル(a)への再追加**:
   - `ax1.fill_between` を用いて、`means_saf - stds_saf` と `means_saf + stds_saf` の領域を塗りつぶします。SST系は不透明度0.15、ベースライン系は不透明度0.08で描画します。
2. **パネル(b)への再追加**:
   - `ax2.fill_between` を用いて、`retention_means - retention_stds` と `retention_means + retention_stds` の領域をパネル(a)と同じ不透明度設定で塗りつぶします。
