# パネル(a) の構成変更 (Alpha vs Safety)

## 概要
パネル(a)のX軸を「Utility」から「Merge Strength ($\alpha$)」に変更し、パネル(b)の「Alpha vs Utility」と同様の形式で「Alpha vs Safety」を描画するように修正する。

## 変更内容
1. **プロット変数の変更**: 
   - `ax1.plot` の X軸に `means_util` ではなく `alphas` を指定する。
   - Y軸は引き続き `means_saf` を使用する。
2. **標準偏差の帯 (fill_between) の追加**:
   - パネル(b)に合わせて、`means_saf - stds_saf` から `means_saf + stds_saf` までの領域を `fill_between` で塗りつぶす。
3. **不要な描画要素の削除**:
   - X軸が Utility ではなくなるため、`Invalid utility` の背景領域や破線、および `Baseline collapse` の注釈を削除する。
   - `Better` の矢印や `alpha=0`, `alpha=1` の手動のテキスト注釈も、X軸が $\alpha$ になることで自明となるため削除（または最小化）する。
4. **軸範囲とラベルの更新**:
   - X軸の範囲を `(-0.05, 1.05)` に設定し、ラベルを `Merge Strength ($\alpha$)` に変更。
   - タイトルを `(a) Safety across merge strength` 等に変更。
