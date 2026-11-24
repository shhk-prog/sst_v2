"""run_pipeline のテスト（FR2.4）。"""

import json
import subprocess

import pytest

import run_pipeline


def test_dry_run_prints_commands_and_writes_nothing(write_root, monkeypatch, capsys):
    """(a) --dry-run（既定）は何も書かず、何も実行せず、事前登録の順序でコマンドを表示する。"""
    def boom(*a, **k):
        raise AssertionError("dry-run で subprocess を呼んではいけない")

    monkeypatch.setattr(subprocess, "run", boom)
    assert run_pipeline.main(["--log-dir", str(write_root / "logs")]) == 0  # 既定は dry-run
    out = capsys.readouterr().out
    order = [out.index(f"[{s}]") for s in run_pipeline.STAGES]
    assert order == sorted(order)
    assert "v5/scripts/check_v1_v9.py" in out and "何も実行していません" in out
    assert list(write_root.iterdir()) == []  # 何も書いていない
    assert run_pipeline.main(["--dry-run", "--stages", "plots,inputs", "--v1-v9-args", "--seed 42"]) == 0
    sel = capsys.readouterr().out
    assert sel.index("[inputs]") < sel.index("[plots]") and "[tables]" not in sel  # 順序は固定、選んだ段階だけ


def test_execute_without_approval_is_refused(write_root, monkeypatch, capsys):
    """(b) --approved-by-user なしの --execute は拒否される。実行も記録もしない。"""
    def boom(*a, **k):
        raise AssertionError("許可なしで subprocess を呼んではいけない")

    monkeypatch.setattr(subprocess, "run", boom)
    assert run_pipeline.main(["--execute", "--stages", "inputs", "--log-dir", str(write_root / "logs")]) == 3
    assert "許可" in capsys.readouterr().err
    assert list(write_root.iterdir()) == []


def test_execute_with_approval_runs_selected_stages_and_logs(write_root, monkeypatch):
    """許可があれば、指定した段階だけを実行し、コマンド、時刻、終了コードを記録する。GPU は見えなくする。"""
    calls = []

    def fake_run(argv, cwd=None, env=None):
        calls.append((argv, env))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    code = run_pipeline.main(["--execute", "--approved-by-user", "--stages", "inputs,v1_v9",
                              "--v1-v9-args", "--seed 42 --max-tensors 8", "--log-dir", str(write_root / "logs")])
    assert code == 0 and len(calls) == 2
    assert all(env["CUDA_VISIBLE_DEVICES"] == "" for _, env in calls)
    v1_argv = calls[1][0]
    assert "--max-tensors" in v1_argv and "--approved-by-user" in v1_argv
    logs = sorted((write_root / "logs").glob("*.json"))
    assert len(logs) == 2
    record = json.loads(logs[0].read_text(encoding="utf-8"))
    assert set(record) == {"stage", "command", "started_at", "finished_at", "return_code"} and record["return_code"] == 0


def test_failure_stops_pipeline_and_unknown_stage_is_rejected(write_root, monkeypatch, capsys):
    """異常系: 段階が失敗したら以降を実行せず、その終了コードを返す。未知の段階は拒否する。"""
    calls = []

    def fake_run(argv, cwd=None, env=None):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 7)

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert run_pipeline.main(["--execute", "--approved-by-user", "--stages", "inputs,tables",
                              "--log-dir", str(write_root / "logs")]) == 7
    assert len(calls) == 1  # inputs で止まり、tables は実行しない
    assert run_pipeline.main(["--stages", "inputs,nonsense"]) == 2
    assert "未知の段階" in capsys.readouterr().err
