import importlib
import sqlite3
import sys

import pytest
from fastapi.testclient import TestClient


def load_app(tmp_path, monkeypatch, verify_token=None):
    """Import the app fresh in a temp cwd (app.database opens ./db.sqlite3 on import)."""
    monkeypatch.chdir(tmp_path)
    if verify_token is None:
        monkeypatch.delenv("WHATSAPP_VERIFY_TOKEN", raising=False)
    else:
        monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", verify_token)
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]
    main = importlib.import_module("app.main")
    router_module = importlib.import_module("app.routers.whatsapp")
    return TestClient(main.app), router_module


def handshake(client, token):
    return client.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": token, "hub.challenge": "abc123"},
    )


def message_payload(phone, text, name="Asha"):
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "contacts": [{"profile": {"name": name}}],
                            "messages": [{"from": phone, "text": {"body": text}}],
                        }
                    }
                ]
            }
        ]
    }


def test_handshake_accepts_default_verify_token(tmp_path, monkeypatch):
    client, _ = load_app(tmp_path, monkeypatch)
    response = handshake(client, "goldrate123")
    assert response.status_code == 200
    assert response.text == "abc123"


def test_handshake_rejects_wrong_token(tmp_path, monkeypatch):
    client, _ = load_app(tmp_path, monkeypatch)
    assert handshake(client, "wrong").status_code == 403


def test_verify_token_can_be_set_from_environment(tmp_path, monkeypatch):
    client, _ = load_app(tmp_path, monkeypatch, verify_token="s3cret-value")
    assert handshake(client, "s3cret-value").status_code == 200
    assert handshake(client, "goldrate123").status_code == 403


def test_hi_message_sends_welcome_and_records_user(tmp_path, monkeypatch):
    client, router_module = load_app(tmp_path, monkeypatch)
    sent = []
    monkeypatch.setattr(router_module, "send_template_message", lambda to, msg: sent.append((to, msg)))

    response = client.post("/webhook", json=message_payload("15550001111", "HI"))

    assert response.json() == {"status": "ok"}
    assert len(sent) == 1
    assert sent[0][0] == "15550001111"
    assert "Asha" in sent[0][1]
    rows = sqlite3.connect(tmp_path / "db.sqlite3").execute("select phone from users").fetchall()
    assert rows == [("15550001111",)]


def test_other_text_records_user_without_replying(tmp_path, monkeypatch):
    client, router_module = load_app(tmp_path, monkeypatch)
    sent = []
    monkeypatch.setattr(router_module, "send_template_message", lambda to, msg: sent.append((to, msg)))

    client.post("/webhook", json=message_payload("15550002222", "rates please"))

    assert sent == []
    rows = sqlite3.connect(tmp_path / "db.sqlite3").execute("select phone from users").fetchall()
    assert rows == [("15550002222",)]


def test_empty_body_and_status_updates_are_ignored(tmp_path, monkeypatch):
    client, router_module = load_app(tmp_path, monkeypatch)
    monkeypatch.setattr(router_module, "send_template_message", lambda *a: pytest.fail("should not send"))

    assert client.post("/webhook", content=b"").json() == {"status": "empty"}
    status_only = {"entry": [{"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}]}
    assert client.post("/webhook", json=status_only).json() == {"status": "ok"}
