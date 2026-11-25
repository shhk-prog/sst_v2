"""1 件ずつ逐次保存・途中再開スクリプト群の単体テスト。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

V5_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V5_ROOT / "scripts"))

import eval_safety_streaming  # noqa: E402
import eval_utility_streaming  # noqa: E402
import reclassify_harmbench_streaming  # noqa: E402


def test_utility_streaming_saves_one_by_one_and_resumes(tmp_path: Path) -> None:
    """1 件推論するごとに JSONL へ即保存され、途中中断・末尾破損から再開できること。"""
    cache_path = tmp_path / "math.json.stream.jsonl"

    class FakeLM:
        def __init__(self, fail_on: int | None = None) -> None:
            self.calls: list[str] = []
            self.fail_on = fail_on

        def generate_until(self, requests, disable_tqdm: bool = False):
            assert len(requests) == 1, "1 件ずつ推論を呼ぶ必要がある"
            req = requests[0]
            self.calls.append(req.args[0])
            if self.fail_on is not None and len(self.calls) == self.fail_on:
                raise RuntimeError("simulated crash on item 3")
            return [f"ans:{req.args[0]}"]

    reqs = [SimpleNamespace(task_name="gsm8k", doc_id=i, args=(f"q{i}", {})) for i in range(5)]

    # 1 回目: 3 件目 (index 2) でクラッシュ想定 -> 2 件分だけ JSONL に残る
    lm1 = FakeLM(fail_on=3)
    eval_utility_streaming.attach_streaming_checkpoint(lm1, cache_path)
    with pytest.raises(RuntimeError, match="simulated crash"):
        lm1.generate_until(reqs, disable_tqdm=True)

    lines = cache_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    # 強制終了による末尾破損行をわざと追加
    with open(cache_path, "a", encoding="utf-8") as f:
        f.write('{"key": "broken", "val')

    # 2 回目: 再開すると最初の 2 件はキャッシュ再利用、残り 3 件のみ推論する
    lm2 = FakeLM(fail_on=None)
    stats = eval_utility_streaming.attach_streaming_checkpoint(lm2, cache_path)
    outs = lm2.generate_until(reqs, disable_tqdm=True)
    assert outs == [f"ans:q{i}" for i in range(5)]
    assert lm2.calls == ["q2", "q3", "q4"]
    assert stats["cached_hits"] == 2
    assert stats["computed"] == 3


def test_reclassify_streaming_partial_and_final_save(monkeypatch, tmp_path: Path) -> None:
    """HarmBench 再分類の途中保存では harmbench_cls_asr が None のままで、全件完了時のみ確定すること。"""
    monkeypatch.setattr(reclassify_harmbench_streaming, "V5_ROOT", tmp_path)
    fpath = tmp_path / "sample_safety.json"
    data = {
        "results": [
            {"prompt": "p0", "response": "r0", "asr": 0.0, "harmbench_cls_asr": 1.0, "harmbench_cls_output": "Yes"},
            {"prompt": "p1", "response": "r1", "asr": 0.0},
        ]
    }
    # 1 件完了時点（未完了あり）
    done1 = reclassify_harmbench_streaming.update_and_save_file(str(fpath), data, update_primary_asr=True)
    assert done1 is False
    saved1 = json.loads(fpath.read_text(encoding="utf-8"))
    assert saved1.get("harmbench_cls_asr") is None
    assert saved1["results"][0]["harmbench_cls_output"] == "Yes"

    # 2 件目完了時点（全件完了）
    data["results"][1]["harmbench_cls_asr"] = 0.0
    data["results"][1]["harmbench_cls_output"] = "No"
    done2 = reclassify_harmbench_streaming.update_and_save_file(str(fpath), data, update_primary_asr=True)
    assert done2 is True
    saved2 = json.loads(fpath.read_text(encoding="utf-8"))
    assert saved2["harmbench_cls_asr"] == pytest.approx(0.5)
    assert saved2["asr"] == pytest.approx(0.5)


def test_safety_resume_preserves_empty_response_and_extra_fields(tmp_path: Path) -> None:
    """空文字の応答 "" と既存の分類済みフィールドが途中再開で消えないこと。"""
    out_file = tmp_path / "test_safety.json"
    out_file.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "prompt": "p0",
                        "response": "",
                        "asr": 0.0,
                        "original_asr": 0.0,
                        "is_gibberish": True,
                        "classifier_output": "Invalid/Gibberish response (assumed safe)",
                        "harmbench_cls_asr": 0.0,
                        "harmbench_cls_output": "No (Gibberish)",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    args = SimpleNamespace(model_path="dummy", limit=2)
    res = eval_safety_streaming.init_or_resume_results_preserve_all(
        args, "harmbench", str(out_file), ["p0", "p1"], "dummy.json"
    )
    assert res[0]["response"] == ""
    assert res[0]["harmbench_cls_output"] == "No (Gibberish)"
    assert res[1]["response"] is None
