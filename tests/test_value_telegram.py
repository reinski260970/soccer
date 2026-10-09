from datetime import datetime, timezone

from oddswatch.sources.surebet import SurebetValue
from oddswatch.surebet_values import Audit, telegram_actionable_text
from oddswatch.sql.valuebet import _alert_key


def _value(odds=2.10):
    return SurebetValue(
        id="vb-1",
        sport="Basketball",
        tournament="NBA",
        teams=("Home", "Away"),
        kickoff=datetime(2026, 10, 10, 18, 0, tzinfo=timezone.utc),
        selection="Gesamt-Punkte Über 55.5",
        market="Gesamt-Punkte · 1. Viertel",
        odds=odds,
        probability=None,
        overvalue=None,
        bookmaker="bet365",
        back=True,
        bet_type="over",
        condition="55.5",
        period="q1",
        base="overall",
    )


def _audit(status="BESTÄTIGT", ev=0.05, odds=2.10, validated=False):
    v = _value(odds)
    return Audit(
        v, status,
        our_probability=0.50,
        our_fair=2.00,
        our_ev=ev,
        note="NBA q1 PointsModel",
        validated_for_release=validated,
    )


def test_telegram_actionable_empty_for_nonplays():
    assert telegram_actionable_text([]) == ""
    assert telegram_actionable_text([_audit("BESTÄTIGT", 0.06, validated=False)]) == ""
    assert telegram_actionable_text([_audit("WIDERLEGT", -0.08)]) == ""
    assert telegram_actionable_text([_audit("REDUZIERT", 0.02)]) == ""
    assert telegram_actionable_text([_audit("KONFLIKT", 0.08)]) == ""


def test_telegram_actionable_only_confirmed_positive_value():
    txt = telegram_actionable_text([_audit("BESTÄTIGT", 0.06, validated=True)])
    assert "🎯 VALUEBET" in txt
    assert "Unser Fair 2,00" in txt
    assert "EV 6,0%" in txt
    assert "NO_MODEL" not in txt
    assert "Feed:" not in txt


def test_alert_key_dedupes_same_market_even_if_odds_change():
    a = _audit("BESTÄTIGT", 0.05, odds=2.10)
    b = _audit("BESTÄTIGT", 0.08, odds=2.25)
    assert _alert_key(a) == _alert_key(b)


def test_alert_key_changes_when_market_line_changes():
    a = _audit("BESTÄTIGT", 0.05)
    v = _value()
    object.__setattr__(v, "condition", "56.5")
    b = Audit(v, "BESTÄTIGT", our_probability=0.50, our_fair=2.0, our_ev=0.05)
    assert _alert_key(a) != _alert_key(b)


def test_run_does_not_send_api_errors(monkeypatch):
    from oddswatch import surebet_values

    monkeypatch.setattr(
        surebet_values.surebet,
        "fetch_valuebets",
        lambda **kwargs: ([], "HTTP 403"),
    )
    sent = []

    def _send(text):
        sent.append(text)
        return {"sent": True, "message_ids": [999], "error": None}

    monkeypatch.setattr(surebet_values.telegram, "send", _send)

    lines = surebet_values.run(send=True, limit=1)

    assert sent == []
    assert any("nicht gesendet" in line.lower() for line in lines)
    assert any("HTTP 403" in line for line in lines)


def test_unvalidated_positives_never_enter_release_or_dedupe():
    from oddswatch.sql.valuebet import filter_unsent_actionable
    fresh, status = filter_unsent_actionable([_audit("BESTÄTIGT", 0.12, validated=False)])
    assert fresh == []
    assert status["reason"] == "no_actionable"
