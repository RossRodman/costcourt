from __future__ import annotations

from typing import Any

import pytest

from app import __main__ as cli


def test_main_starts_uvicorn_with_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(cli.uvicorn, "run", lambda app, **kw: calls.append({"app": app, **kw}))

    cli.main(["--port", "9100", "--host", "0.0.0.0"])

    assert calls == [
        {
            "app": "app.main:create_app",
            "factory": True,
            "host": "0.0.0.0",
            "port": 9100,
            "reload": True,  # dev default
            "log_level": "info",
        }
    ]


def test_reload_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(cli.uvicorn, "run", lambda app, **kw: calls.append(kw))

    cli.main(["--no-reload"])

    assert calls[0]["reload"] is False
