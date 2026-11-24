"""仮説 V1〜V11 の検証層のテスト（FR2.1〜FR2.4、NFR4）。合成の小さなテンソルだけを使う。"""

import copy
import json
import os
from pathlib import Path

import numpy as np
import pytest

from v5lib import hypotheses, tensor_checks as tc, verify


@pytest.fixture
def torch():
    return pytest.importorskip("torch")


@pytest.fixture
def prereg():
    return hypotheses.load_preregistration()


# ---------------------------------------------------------------------------
# テンソル計算（V1〜V4）
# ---------------------------------------------------------------------------


def test_v1_zero_fraction_after_fp16_cast(torch):
    """(a) fp16 で 0 に落ちる値（1e-9）を含むテンソルで、fp16 と fp32 の 0 の割合が違う。"""
    t = torch.tensor([1e-9] * 6 + [0.0] * 2 + [1.0] * 2, dtype=torch.float32)
    assert tc.zero_fraction(t, via_fp16=False) == pytest.approx(0.2)
    assert tc.zero_fraction(t, via_fp16=True) == pytest.approx(0.8)


def test_v2_mask_ratio_degenerates_when_zeros_exceed_80_percent_and_inf_count(torch):
    """(b) F_h の 0 が 80% 超だとマスクが全 1 に退化する。比が大きすぎる座標は inf になる。"""
    n = 100
    fb = torch.ones(n)
    fh_degenerate = torch.zeros(n)
    fh_degenerate[:15] = torch.linspace(1.0, 2.0, 15)  # 0 が 85%
    mask = tc.topk_mask(tc.lambda_fhfb(fh_degenerate, [fb]), 0.2)
    assert tc.mask_ratio(mask) == 1.0  # 閾値が 0 になり、>= で全座標が選ばれる
    fh_ok = torch.linspace(0.01, 1.0, n)  # 0 は無い。値が全部異なる
    assert tc.mask_ratio(tc.topk_mask(tc.lambda_fhfb(fh_ok, [fb]), 0.2)) == pytest.approx(0.2)
    # inf: F̄_b = 0 で F_h が大きいと、fp16 の演算が溢れる（sst.py と同じ fp16）
    # F̄_b=0 のとき分母は fp16 の 1e-6（約 9.5e-7）なので、F_h が約 0.0625 を超えると 65504 を超えて inf になる
    fh_big = torch.tensor([60000.0, 1.0, 0.01, 0.0])
    lam = tc.lambda_fhfb(fh_big, [torch.zeros(4)])
    assert tc.inf_count(lam) == 2 and lam.dtype == torch.float16
    assert torch.isfinite(lam[2]) and lam[3].item() == 0.0


def test_v3_jaccard_and_rank_correlation(torch):
    """(c) 同じ順位なら Jaccard=1、無関係なら 0 に近い（k=0.2 の乱数の期待値は約 0.11）。"""
    g = torch.Generator().manual_seed(0)
    a = torch.rand(20000, generator=g)
    same = tc.topk_mask(a, 0.2)
    assert tc.jaccard(same, tc.topk_mask(a * 3.0 + 1.0, 0.2)) == 1.0
    unrelated = tc.jaccard(same, tc.random_mask(a.shape, 0.2, seed=123))
    assert unrelated < 0.2
    assert tc.random_mask(a.shape, 0.2, 5).equal(tc.random_mask(a.shape, 0.2, 5))  # seed 固定（NFR1）
    assert tc.spearman(a, a * 2 + 1) == pytest.approx(1.0)
    assert tc.spearman(a, -a) == pytest.approx(-1.0)
    assert tc.spearman(torch.ones(10), torch.arange(10.0)) is None  # 定数は相関を定義できない
    ties = tc.rankdata_average(np.array([1.0, 1.0, 3.0]))
    assert ties.tolist() == [1.5, 1.5, 3.0]


def test_v4_ulp_decides_whether_alpha_delta_is_rounded_away(torch):
    """(d) θ_u=1.0 の fp16 の 1 ulp は 2^-10。α·δ が 半 ulp 未満の座標だけが「消える」と数える。"""
    theta_u = torch.ones(4)
    assert tc.ulp_fp16(theta_u)[0].item() == pytest.approx(2.0 ** -10)
    delta_s = torch.tensor([8e-4, 2e-3, 8e-4, 2e-3])  # α=0.5 で 4e-4（半 ulp=4.88e-4 未満）と 1e-3
    assert tc.frac_below_half_ulp(theta_u, delta_s, alpha=0.5) == pytest.approx(0.5)
    for x in (0.001, 0.5, 1.0, 3.7, 100.0):  # numpy の fp16 の間隔と一致
        assert tc.ulp_fp16(torch.tensor([x]))[0].item() == pytest.approx(float(np.spacing(np.float16(x))), rel=1e-6)
    # 数値の実験: 半 ulp 未満の足し算は fp16 で θ_u を変えない
    assert (torch.tensor([1.0]).half() + torch.tensor([4e-4]).half()).item() == 1.0


# ---------------------------------------------------------------------------
# 判定ロジック（事前登録の値を使う）
# ---------------------------------------------------------------------------


def test_judge_follows_preregistered_thresholds(prereg):
    """(e) 「支持」「不支持」「判定不能」を、事前登録の閾値どおりに返す。コードに閾値を直書きしない。"""
    v1 = prereg["hypotheses"]["V1"]
    hi, lo = v1["support_if"]["value"], v1["refute_if"]["value"]
    metric = v1["metric"]
    assert hypotheses.judge("V1", prereg, {metric: hi})["verdict"] == hypotheses.VERDICT_SUPPORT
    assert hypotheses.judge("V1", prereg, {metric: lo})["verdict"] == hypotheses.VERDICT_REFUTE
    mid = hypotheses.judge("V1", prereg, {metric: (hi + lo) / 2})
    assert mid["verdict"] == hypotheses.VERDICT_UNDETERMINED and mid["reason_code"] == "between_criteria"
    none = hypotheses.judge("V1", prereg, {})
    assert none["verdict"] == hypotheses.VERDICT_UNDETERMINED and none["reason_code"] == "data_missing"
    missing = hypotheses.judge("V1", prereg, {metric: hi}, missing_inputs=["fim_cache_harmful"])
    assert missing["verdict"] == hypotheses.VERDICT_UNDETERMINED and "fim_cache_harmful" in missing["reason"]
    # 閾値を事前登録の側で変えると、同じ値の判定が変わる（コードに直書きしていない証拠）
    changed = copy.deepcopy(prereg)
    changed["hypotheses"]["V1"]["support_if"]["value"] = hi + 0.5
    assert hypotheses.judge("V1", changed, {metric: hi})["verdict"] == hypotheses.VERDICT_UNDETERMINED
    # Step 8.3: ファイルの値と、読み込んだ値が同じ
    raw = json.loads(hypotheses.DEFAULT_PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    for hid in hypotheses.HYPOTHESIS_IDS:
        assert raw["hypotheses"][hid]["support_if"] == prereg["hypotheses"][hid]["support_if"]
    assert hypotheses.vrr_floors(prereg) == (80.0, [90.0, 50.0])
    assert hypotheses.neighborhood_tolerance(prereg) == 2.0


def test_preregistration_validation_rejects_overlap_and_unknown_hypotheses(prereg):
    """異常系: 支持と反証の基準が重なる、V12 以降が混ざる、必須項目が欠ける事前登録は拒否する。"""
    overlap = copy.deepcopy(prereg)
    overlap["hypotheses"]["V3"]["refute_if"] = {"op": "<=", "value": 0.6}  # support は >= 0.5 と重なる
    with pytest.raises(hypotheses.PreregistrationError):
        hypotheses.validate_preregistration(overlap)
    extra = copy.deepcopy(prereg)
    extra["hypotheses"]["V12"] = copy.deepcopy(prereg["hypotheses"]["V1"])
    with pytest.raises(hypotheses.PreregistrationError):
        hypotheses.validate_preregistration(extra)
    broken = copy.deepcopy(prereg)
    del broken["hypotheses"]["V5"]["metric"]
    with pytest.raises(hypotheses.PreregistrationError):
        hypotheses.validate_preregistration(broken)
    with pytest.raises(hypotheses.PreregistrationError):
        hypotheses.load_preregistration("/nonexistent/prereg.json")


# ---------------------------------------------------------------------------
# 範囲の絞り込み（V1）と mmap の読み込み
# ---------------------------------------------------------------------------


def _make_fim_dir(tmp_path, torch, zero_fraction_value=0.9):
    fim_dir = tmp_path / "cache" / "fim"
    fim_dir.mkdir(parents=True)
    for seed in (42, 43, 44):
        tensors = {}
        for layer in range(3):
            t = torch.ones(10, 10)
            t[: int(100 * zero_fraction_value)] = 0.0  # 0 の割合を指定
            tensors[f"model.layers.{layer}.self_attn.q_proj.weight"] = t
        tensors["model.embed_tokens.weight"] = torch.ones(4, 4)  # 対象外のテンソル
        torch.save(tensors, fim_dir / f"harmful_safety_Llama2_SafetyFT_n500_seed{seed}.pt")
    return fim_dir


def _ctx(tmp_path, **scope_kwargs):
    return verify.Context(
        fim_dir=tmp_path / "cache" / "fim", data_fim_dir=tmp_path / "data" / "fim",
        merged_dir=tmp_path / "models" / "merged", scope=verify.Scope(**scope_kwargs),
    )


def test_restricted_scope_makes_hypothesis_undetermined(tmp_path, torch, prereg):
    """(f) --max-tensors などで範囲外が出た仮説は「判定不能」になる。全範囲なら同じデータで「支持」。"""
    _make_fim_dir(tmp_path, torch, zero_fraction_value=0.9)
    full = verify.run_v1(_ctx(tmp_path))
    assert full["complete"] is True and full["metrics"]["n_tensors"] == 9  # 3 seed x 3 層（対象外は除く）
    judged_full = hypotheses.judge("V1", prereg, full["metrics"], full["complete"], full["missing_inputs"], full["scope"])
    assert judged_full["verdict"] == hypotheses.VERDICT_SUPPORT

    limited = verify.run_v1(_ctx(tmp_path, max_tensors=1))
    assert limited["complete"] is False and limited["metrics"]["n_tensors"] == 3
    assert limited["scope"]["max_tensors"] == 1  # 実行した範囲が記録される
    judged = hypotheses.judge("V1", prereg, limited["metrics"], limited["complete"], limited["missing_inputs"], limited["scope"])
    assert judged["verdict"] == hypotheses.VERDICT_UNDETERMINED and judged["reason_code"] == "scope_restricted"
    assert judged["scope"]["max_tensors"] == 1

    by_layer = verify.run_v1(_ctx(tmp_path, layers={0}))
    assert by_layer["complete"] is False and by_layer["metrics"]["n_tensors"] == 3
    one_seed = verify.run_v1(_ctx(tmp_path, seeds=[42]))
    assert one_seed["complete"] is False  # seed を絞っても判定不能


def test_small_pt_is_read_with_mmap_and_load_errors_are_explicit(tmp_path, torch):
    """(g) 小さな .pt を mmap で読める。壊れたファイルや無いファイルは、理由つきの例外にする。"""
    path = tmp_path / "fim.pt"
    torch.save({"a.weight": torch.arange(6.0).reshape(2, 3)}, path)
    fim = tc.load_fim_lazy(path)
    assert list(fim.keys()) == ["a.weight"] and fim["a.weight"].shape == (2, 3)
    assert fim["a.weight"].sum().item() == 15.0
    (tmp_path / "broken.pt").write_bytes(b"not a torch file")
    with pytest.raises(tc.TensorLoadError):
        tc.load_fim_lazy(tmp_path / "broken.pt")
    with pytest.raises(tc.TensorLoadError):
        tc.load_fim_lazy(tmp_path / "missing.pt")
    torch.save([1, 2, 3], tmp_path / "list.pt")
    with pytest.raises(tc.TensorLoadError):
        tc.load_fim_lazy(tmp_path / "list.pt")
    # 入力が無い仮説は、例外にせず「入力なし」で返る
    res = verify.run_v1(_ctx(tmp_path / "nowhere"))
    assert res["metrics"] == {} and res["missing_inputs"] == ["fim_cache_harmful"]


def test_safetensors_source_reads_one_tensor_at_a_time(tmp_path, torch):
    """safetensors はテンソル単位で読む（safe_open）。ヘッダだけで形を読める。"""
    st = pytest.importorskip("safetensors.torch")
    model = tmp_path / "m"
    model.mkdir()
    st.save_file({"x.weight": torch.arange(4.0).reshape(2, 2), "lm_head.weight": torch.zeros(5, 2)}, str(model / "model.safetensors"))
    src = tc.TensorSource(model)
    assert src.names() == ["lm_head.weight", "x.weight"] and src.get("x.weight").sum().item() == 6.0
    assert tc.safetensors_header_shapes(model / "model.safetensors")["lm_head.weight"] == [5, 2]
    with pytest.raises(tc.TensorLoadError):
        src.get("nope")
    with pytest.raises(tc.TensorLoadError):
        tc.TensorSource(tmp_path / "no_such_dir")


def test_pytorch_bin_source_reads_single_and_sharded(tmp_path, torch):
    """PyTorch .bin（単一・分割シャード）も TensorSource で読め、compute_availability でも検出される。"""
    single = tmp_path / "bin_single"
    single.mkdir()
    torch.save({"a.weight": torch.ones(2, 2), "b.weight": torch.full((2, 2), 3.0)}, single / "pytorch_model.bin")
    src_single = tc.TensorSource(single)
    assert src_single.names() == ["a.weight", "b.weight"]
    assert src_single.get("b.weight").sum().item() == 12.0

    sharded = tmp_path / "bin_sharded"
    sharded.mkdir()
    torch.save({"model.layers.0.self_attn.q_proj.weight": torch.ones(2, 2)}, sharded / "pytorch_model-00001-of-00002.bin")
    torch.save({"model.layers.1.self_attn.q_proj.weight": torch.full((2, 2), 2.0)}, sharded / "pytorch_model-00002-of-00002.bin")
    index = {
        "metadata": {},
        "weight_map": {
            "model.layers.0.self_attn.q_proj.weight": "pytorch_model-00001-of-00002.bin",
            "model.layers.1.self_attn.q_proj.weight": "pytorch_model-00002-of-00002.bin",
        },
    }
    (sharded / "pytorch_model.bin.index.json").write_text(json.dumps(index), encoding="utf-8")
    src_sharded = tc.TensorSource(sharded)
    assert len(src_sharded.names()) == 2
    assert src_sharded.get("model.layers.0.self_attn.q_proj.weight").sum().item() == 4.0
    assert src_sharded.get("model.layers.1.self_attn.q_proj.weight").sum().item() == 8.0

    ctx = _ctx(tmp_path, seeds=[42], patterns=["safety+math"])
    ctx.base_dir = single
    ctx.util_dirs = {"math": sharded, "code": sharded, "medical": single}
    avail = verify.compute_availability(ctx)
    assert avail["model_weights_base"] and avail["model_weights_util"]


def test_v7_v8_v9_on_synthetic_files(tmp_path, torch, prereg):
    """V7（rope_theta）、V8（プレースホルダ）、V9（語彙）が、合成ファイルで動く。"""
    st = pytest.importorskip("safetensors.torch")
    merged = tmp_path / "models" / "merged"
    d = merged / "sst_merge_v3_main_ties_safety+code_alpha0.6_seed42"
    d.mkdir(parents=True)
    (d / "config.json").write_text(json.dumps({"rope_parameters": {"rope_theta": 10000.0}, "vocab_size": 4}))
    st.save_file({"lm_head.weight": torch.zeros(5, 2)}, str(d / "model.safetensors"))
    ctx = _ctx(tmp_path)
    ctx.params = {hid: e.get("params", {}) for hid, e in prereg["hypotheses"].items()}
    v7 = verify.run_v7(ctx)
    assert v7["metrics"]["merged_code_rope_theta_mismatch_fraction"] == 1.0
    assert hypotheses.judge("V7", prereg, v7["metrics"], v7["complete"], v7["missing_inputs"])["verdict"] == hypotheses.VERDICT_SUPPORT
    v9 = verify.run_v9(ctx)
    assert v9["metrics"]["n_vocab_mismatch_models"] == 1 and v9["metrics"]["lm_head_rows"] == [5]
    data = tmp_path / "data" / "fim"
    data.mkdir(parents=True)
    placeholders = [{"prompt": f"Solve math problem {i}", "response": f"Math answer {i}"} for i in range(30)]
    real = [{"prompt": "Natalia sold clips to 48 of her friends in April, and then half as many in May.", "response": "x"}] * 30
    (data / "fim_benign_math.json").write_text(json.dumps(placeholders))
    (data / "fim_benign_code.json").write_text(json.dumps(real))
    (data / "fim_benign_medical.json").write_text(json.dumps(real))
    (data / "fim_harmful.json").write_text(json.dumps(real))
    v8 = verify.run_v8(ctx)
    assert v8["metrics"]["placeholder_fraction"] == pytest.approx(1 / 3) and v8["metrics"]["harmful_count"] == 30
    assert hypotheses.judge("V8", prereg, v8["metrics"], v8["complete"], v8["missing_inputs"])["verdict"] == hypotheses.VERDICT_UNDETERMINED
    # merged が空のときは入力なし -> 判定不能
    empty = verify.run_v7(_ctx(tmp_path / "other"))
    assert empty["missing_inputs"] == ["merged_model_configs"]


def test_v2_to_v6_runners_on_tiny_models(tmp_path, torch, prereg):
    """V2〜V6 の実行部分を、小さな合成のモデルと FIM（8x8 の 2 テンソル）で動かす。実データは使わない。"""
    st = pytest.importorskip("safetensors.torch")
    g = torch.Generator().manual_seed(0)
    names = ["model.layers.0.self_attn.q_proj.weight", "model.layers.1.mlp.up_proj.weight"]
    base = {n: torch.randn(8, 8, generator=g) for n in names}
    delta = {n: torch.randn(8, 8, generator=g) * 0.1 for n in names}

    def save(dirname, tensors):
        d = tmp_path / dirname
        d.mkdir(parents=True, exist_ok=True)
        st.save_file({k: v.contiguous() for k, v in tensors.items()}, str(d / "model.safetensors"))
        return d

    ctx = _ctx(tmp_path, seeds=[42], patterns=["safety+math"])
    ctx.params = {hid: e.get("params", {}) for hid, e in prereg["hypotheses"].items()}
    ctx.base_dir = save("base", base)
    util = {n: base[n] + 0.05 * torch.randn(8, 8, generator=g) for n in names}
    # math だけ大きく離す（V6 の比が 1 を超える）
    ctx.util_dirs = {
        "math": save("util_math", {n: base[n] + 0.5 * torch.randn(8, 8, generator=g) for n in names}),
        "code": save("util_code", util),
        "medical": save("util_medical", util),
    }
    ctx.safety_dir_template = str(tmp_path / "safety_seed{seed}")
    save("safety_seed42", {n: base[n] + delta[n] for n in names})
    # FIM: harmful と benign(math)。0 の割合は低めにする
    fim_dir = ctx.fim_dir
    fim_dir.mkdir(parents=True)
    torch.save({n: torch.rand(8, 8, generator=g) for n in names}, fim_dir / "harmful_safety_Llama2_SafetyFT_n500_seed42.pt")
    torch.save({n: torch.rand(8, 8, generator=g) + 0.1 for n in names}, fim_dir / "benign_math_Llama2_WizardMath_n500_seed42.pt")
    # merge 済み: TA は δ_s の全量を足し、SST は 20% だけを足す
    util_math = {n: st.load_file(str(ctx.util_dirs["math"] / "model.safetensors"))[n] for n in names}
    ta = {n: util_math[n] + 0.6 * delta[n] for n in names}
    sst = {n: util_math[n] + 0.6 * (torch.rand(8, 8, generator=g) < 0.2).float() * delta[n] for n in names}
    ctx.merged_dir.mkdir(parents=True)
    for method, tensors in (("task_arithmetic", ta), ("diagonal_sst_main", sst)):
        target = verify.merged_dir_for(ctx, method, "safety+math", 42, 0.6)
        target.mkdir(parents=True)
        st.save_file({k: v.contiguous() for k, v in tensors.items()}, str(target / "model.safetensors"))

    avail = verify.compute_availability(ctx)
    assert avail["fim_cache_harmful"] and avail["fim_cache_benign"] and avail["model_weights_base"]
    assert avail["model_weights_util"] and avail["model_weights_safety"]
    assert avail["merged_models_sst"] and avail["merged_models_ta"] and not avail["fim_data_json"]

    pair = verify.run_v2_v3(ctx)
    m2, m3 = pair["V2"]["metrics"], pair["V3"]["metrics"]
    assert m2["n_tensors"] == 2 and 0.0 <= m2["frac_tensors_mask_or_inf_abnormal"] <= 1.0
    assert 0.0 < m2["mean_mask_ratio"] <= 1.0
    assert 0.0 <= m3["median_jaccard_fhfb_vs_magnitude"] <= 1.0 and m3["n_tensors"] == 2
    # 全範囲（seed と pattern を全部）ではないので、判定は「判定不能」になる
    assert pair["V2"]["complete"] is False
    assert hypotheses.judge("V2", prereg, m2, pair["V2"]["complete"])["verdict"] == hypotheses.VERDICT_UNDETERMINED

    v4 = verify.run_v4(ctx)
    assert 0.0 <= v4["metrics"]["mean_frac_alpha_delta_below_half_ulp"] <= 1.0 and len(v4["details"]) == 6
    v5 = verify.run_v5(ctx)
    assert v5["metrics"]["median_ratio_sst_over_ta_injection"] < 0.6  # SST は TA より少ない注入量
    v6 = verify.run_v6(ctx)
    assert v6["metrics"]["ratio_wizardmath_over_mean_others_rel_diff"] > 2.0  # math だけ離した

    # モデルが無い入力は、例外にせず「入力なし」で返す（判定不能の理由になる）
    ctx.base_dir = None
    assert verify.run_v6(ctx)["missing_inputs"] == ["model_weights_base"]
    assert verify.run_v5(ctx)["metrics"] == {}


# ---------------------------------------------------------------------------
# スクリプト（FR2.4、NFR2）
# ---------------------------------------------------------------------------


def test_scripts_refuse_without_approval_and_never_write_outside_v5(tmp_path, write_root, monkeypatch, capsys, torch):
    """(h) 許可なしでは実行しない。出力先が v5/ の外なら失敗し、何も書かない。"""
    import check_v1_v9
    import check_inputs

    v3 = tmp_path / "v3"
    (v3 / "data" / "fim").mkdir(parents=True)
    for name in ("fim_benign_math.json", "fim_benign_code.json", "fim_benign_medical.json", "fim_harmful.json"):
        (v3 / "data" / "fim" / name).write_text(json.dumps([{"prompt": "a real question about things", "response": "r"}]))
    base_args = ["--v3-dir", str(v3), "--results-root", str(tmp_path / "nores"), "--hypotheses", "V8"]
    out_inside = write_root / "outputs" / "hypotheses"

    assert check_v1_v9.main(base_args + ["--dry-run", "--out-dir", str(out_inside)]) == 0
    assert not out_inside.exists()  # dry-run は何も書かない
    assert check_v1_v9.main(base_args + ["--out-dir", str(out_inside)]) == 3  # 許可なし
    assert not out_inside.exists()
    assert check_v1_v9.main(base_args + ["--approved-by-user", "--out-dir", str(out_inside)]) == 0
    written = sorted(p.name for p in out_inside.iterdir())
    assert "v1_v9.json" in written and "v1_v9.md" in written
    doc = json.loads((out_inside / "v1_v9.json").read_text(encoding="utf-8"))
    assert doc["verdicts"]["V8"]["verdict"] in hypotheses.VERDICTS
    assert doc["details"]["V8"]["scope"]["layers"] is None  # 実行した範囲が記録される

    monkeypatch.delenv("V5_WRITE_ROOT_FOR_TESTS")
    outside = tmp_path / "outside"
    assert check_v1_v9.main(base_args + ["--approved-by-user", "--out-dir", str(outside)]) == 1
    assert not outside.exists()
    assert check_inputs.main(["--v3-dir", str(v3), "--out-dir", str(outside)]) == 1
    assert not outside.exists()
    assert check_v1_v9.main(["--hypotheses", "V10", "--dry-run"]) == 2  # この段階で扱わない仮説


def test_device_is_fixed_to_cpu():
    """GPU を使わない（NFR4）: device は cpu 固定、スクリプトは CUDA を見えなくする。"""
    assert tc.DEVICE == "cpu"
    import _common
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert _common.os.environ["CUDA_VISIBLE_DEVICES"] == ""
