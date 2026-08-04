from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[3] / "scripts" / "ai_alert_if_needed.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("ai_alert_if_needed", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _signal(*, cached_response: str | None = None) -> dict:
    return {
        "symbol": "XAUUSD",
        "exchange": "OANDA",
        "timeframe": "15m",
        "price": 4078.2,
        "bias": "SELL",
        "decision": "TRADE",
        "score": 74,
        "plan": {"entry_zone": "4088-4093", "sl": 4102, "tp": [4075, 4062, 4050]},
        "ai_gate": {"should_ask_ai": cached_response is None, "signal_fingerprint": "fp123", "cached_response": cached_response},
    }


class FakeTradeRepo:
    def __init__(self, signal: dict | None):
        self.signal = signal

    def get_latest_trade_signal(self, symbol: str, timeframe: str | None = None) -> dict | None:
        return self.signal


class FakeAiRepo:
    def __init__(self, *, already_delivered: bool = False, cached_response: str | None = None):
        self.already_delivered = already_delivered
        self.cached_response = cached_response
        self.inserted: list[dict] = []
        self.marked: list[tuple[str, str, str, str]] = []

    def fingerprint_signal(self, signal: dict) -> str:
        return "fallback-fp"

    def has_alert_delivery(self, symbol: str, timeframe: str, signal_fingerprint: str, target: str) -> bool:
        return self.already_delivered

    def get_cached_response(self, symbol: str, timeframe: str, signal_fingerprint: str) -> str | None:
        return self.cached_response

    def insert_ai_response(self, **kwargs) -> int:
        self.inserted.append(kwargs)
        return 1

    def mark_alert_delivered(self, symbol: str, timeframe: str, signal_fingerprint: str, target: str) -> int:
        self.marked.append((symbol, timeframe, signal_fingerprint, target))
        return 1


def test_dry_run_prints_prompt_without_asking_ai_or_sending(capsys):
    module = _load_script_module()
    calls = []

    rc = module.main(
        ["--dry-run"],
        trade_repo=FakeTradeRepo(_signal()),
        ai_repo=FakeAiRepo(),
        run_fn=lambda cmd, input_text=None: calls.append(cmd),
    )

    out = capsys.readouterr().out
    assert rc == 0
    assert "Signal JSON:" in out
    assert "Do not call tools" in out
    assert calls == []


def test_no_send_asks_ai_when_gate_true_and_caches_without_telegram(capsys):
    module = _load_script_module()
    ai_repo = FakeAiRepo()
    calls = []

    def fake_run(cmd, input_text=None):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="SELL เข้า 4088-4093 SL 4102 TP 4075/4062/4050\n", stderr="")

    rc = module.main(["--no-send"], trade_repo=FakeTradeRepo(_signal()), ai_repo=ai_repo, run_fn=fake_run)

    assert rc == 0
    assert "SELL เข้า 4088-4093" in capsys.readouterr().out
    assert len(calls) == 1
    assert calls[0][:3] == ["hermes", "chat", "-Q"]
    assert ai_repo.inserted[0]["signal_fingerprint"] == "fp123"
    assert ai_repo.marked == []


def test_cached_response_sends_once_without_asking_ai():
    module = _load_script_module()
    ai_repo = FakeAiRepo()
    calls = []

    def fake_run(cmd, input_text=None):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    rc = module.main(
        ["--target", "telegram:trad"],
        trade_repo=FakeTradeRepo(_signal(cached_response="SELL cached alert")),
        ai_repo=ai_repo,
        run_fn=fake_run,
    )

    assert rc == 0
    assert len(calls) == 1
    assert calls[0][:5] == ["hermes", "send", "--quiet", "--to", "telegram:trad"]
    assert "SELL cached alert" in calls[0]
    assert ai_repo.inserted == []
    assert ai_repo.marked == [("XAUUSD", "15m", "fp123", "telegram:trad")]


def test_repository_cached_response_is_used_when_gate_was_stale():
    module = _load_script_module()
    ai_repo = FakeAiRepo(cached_response="SELL cached from repository")
    calls = []

    def fake_run(cmd, input_text=None):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    rc = module.main(
        ["--target", "telegram:trad"],
        trade_repo=FakeTradeRepo(_signal()),
        ai_repo=ai_repo,
        run_fn=fake_run,
    )

    assert rc == 0
    assert len(calls) == 1
    assert calls[0][:3] == ["hermes", "send", "--quiet"]
    assert "SELL cached from repository" in calls[0]
    assert ai_repo.inserted == []


def test_duplicate_delivery_exits_silent_without_chat_or_send():
    module = _load_script_module()
    calls = []

    rc = module.main(
        ["--target", "telegram:trad"],
        trade_repo=FakeTradeRepo(_signal(cached_response="SELL cached alert")),
        ai_repo=FakeAiRepo(already_delivered=True),
        run_fn=lambda cmd, input_text=None: calls.append(cmd),
    )

    assert rc == 0
    assert calls == []


def test_target_required_for_real_send(capsys, monkeypatch):
    module = _load_script_module()
    monkeypatch.delenv("TRAD_TELEGRAM_TARGET", raising=False)

    rc = module.main([], trade_repo=FakeTradeRepo(_signal(cached_response="SELL cached alert")), ai_repo=FakeAiRepo())

    assert rc == 2
    assert "TRAD_TELEGRAM_TARGET" in capsys.readouterr().err
