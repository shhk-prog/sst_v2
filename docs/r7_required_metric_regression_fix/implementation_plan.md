# 実装計画書: 必須benchmark個別指標のnull拒否検査の復元 (R7)

## 1. 背景と監査指示
コミット `8fe3ddc45660f94e1ca5318f4e8cc0e66c65bfb3` において、HarmBench の公式 7 規則 fixture 照合および件数検査（`validate_benchmark_counts`）、コード実行停止（方針A）が受入確認された。
しかし、`v4/scripts/analysis/e1_selector.py` の `evaluate_feasible_region_strict` 内で、必須 benchmark の件数検査への置換時に以前存在していた「必須指標（`asr_all`, `asr_valid`, `vrr`）の null / 範囲拒否」が削除されていた。
後段の閾値比較は `if b_asr is not None` のような条件付きであるため、件数が正常であれば個別指標が欠測していても検査を素通りして `FEASIBLE` と判定され得る回帰不具合となっていた。

本計画では指示書に基づき、この検査を最小差分で復元する。

## 2. 変更仕様
`v4/scripts/analysis/e1_selector.py` の `for rb in required_benchmarks:` 内において、`validate_benchmark_counts` 呼び出しの直後に以下を追加する：

```python
            # Require both valid counts and complete per-benchmark metrics.
            for metric_name in ("asr_all", "asr_valid", "vrr"):
                value = rb_data.get(metric_name)
                if value is None or not is_valid_ratio(value):
                    return (
                        "INSUFFICIENT_DATA",
                        f"NULL_OR_INVALID_REQUIRED_BENCHMARK_"
                        f"{rb.upper()}_{metric_name.upper()}",
                    )
```

- 指標を全体平均から補完しない。
- 欠測を 0 にしない。
- 指標がないときに benchmark を必須集合から除外しない。
- 既存の件数検査および後段の閾値比較はそのまま維持する。

## 3. 検証計画
1. **追加回帰テスト (`test_e1_required_metric_regression.py`)**:
   - 修正前に実行し、27 件の Failure が発生することを確認（回帰不具合の再現）。
   - 修正後に実行し、全 7 件のテスト（必須 benchmark の null / 欠落、件数のみ存在、非有限値、範囲外、件数型検査、select_best、sensitivity）がすべて PASS することを確認。
2. **公式参照元照合 (`verify_harmbench_reference.py`)**:
   - 公式 7 規則テンプレートとの照合が維持されていること（終了コード 0）を確認。
3. **全回帰テストスイート (`run_v4_pipeline.py --smoke_test`)**:
   - 37 件すべての回帰テストが PASS することを確認。
4. **主実験トラック (`run_v4_pipeline.py`)**:
   - 実モデルの tokenizer / RoPE 不整合により、E0 ゲート停止（`NO_GO`）が安全に機能することを再確認。
