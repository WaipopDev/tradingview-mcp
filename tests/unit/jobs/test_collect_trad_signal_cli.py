from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "collect_trad_signal.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("collect_trad_signal", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_collect_cli_passes_explicit_db_path_and_prints_json(capsys, tmp_path):
    module = _load_script_module()
    db_path = tmp_path / "signals.sqlite3"
    calls = {}

    def fake_analyze(**kwargs):
        calls.update(kwargs)
        return {"stored": True, "symbol": kwargs["symbol"], "db_path": kwargs["db_path"]}

    rc = module.main(["--db-path", str(db_path), "--json"], analyze_fn=fake_analyze)

    assert rc == 0
    assert calls["db_path"] == str(db_path)
    assert '"stored": true' in capsys.readouterr().out


def test_collect_cli_is_silent_and_successful_for_retryable_error(capsys):
    module = _load_script_module()

    def fake_analyze(**kwargs):
        return {"stored": False, "error": {"code": "UPSTREAM_ERROR", "message": "timeout", "retryable": True}}

    rc = module.main([], analyze_fn=fake_analyze)

    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == ""
    assert captured.err == ""


def test_collect_cli_prints_retryable_error_when_json_requested(capsys):
    module = _load_script_module()

    def fake_analyze(**kwargs):
        return {"stored": False, "error": {"code": "UPSTREAM_ERROR", "message": "timeout", "retryable": True}}

    rc = module.main(["--json"], analyze_fn=fake_analyze)

    captured = capsys.readouterr()
    assert rc == 0
    assert '"retryable": true' in captured.out
    assert captured.err == ""