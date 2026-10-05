from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from oddswatch import outlook
from oddswatch.selection import Candidate

NOW = datetime(2026, 9, 30, 19, tzinfo=timezone.utc)


def _fx(league, days, priced=True):
    game = SimpleNamespace(kickoff=NOW + timedelta(days=days))
    return SimpleNamespace(league=league, game=game, offers={"home": 1} if priced else {})


def _c(league, ev, event="A – B", market="home", days=2):
    ko = (NOW + timedelta(days=days)).isoformat(timespec="minutes")
    return Candidate(event, ko, market, "A Sieg", "bet365", 2.0, 0.5, 2.0, 2.06, 0.0, ev, 0.0,
                     False, "", "", None, p_ref=0.5, league=league)


def test_build_groups_by_sport_and_horizon():
    fx = [_fx("nfl", 2), _fx("nfl", 3), _fx("nfl", 9), _fx("icehl", 1, priced=False), _fx("nba", 4)]
    cs = [_c("nfl", 0.01, "X – Y"), _c("nfl", -0.02, "Z – W"), _c("nfl", 0.02, "Q – R", days=9),
          _c("nba", 0.05, "N – M")]
    picks = [cs[3]]
    rows = {r["name"]: r for r in outlook.build(fx, cs, picks, now=NOW)}
    assert rows["NFL"]["games"] == 2 and rows["NFL"]["priced"] == 2
    assert [c.event for c in rows["NFL"]["near"]] == ["X – Y", "Z – W"]  # Tag 9 außerhalb
    assert rows["Eishockey Europa"]["games"] == 1 and rows["Eishockey Europa"]["priced"] == 0
    assert len(rows["NBA"]["picks"]) == 1 and rows["NBA"]["near"] == []
    assert rows["Fußball"]["games"] == 0 and rows["NHL"]["games"] == 0


def test_lines_without_tennis():
    rows = outlook.build([_fx("nhl", 1)], [_c("nhl", 0.0)], [], now=NOW)
    tg = outlook.telegram_lines(rows, tennis=False, notes=outlook.soccer_note(
        ["Fußball: Freigaben ausgesetzt, bis …"]))
    txt = "\n".join(tg)
    assert "🔭 AUSBLICK NACH SPORTART" in txt and "🏒 NHL: 1 Spiele (1 mit Buchmacherpreis), 0 PLAY" in txt
    assert "⚽ Fußball: keine Spiele in 7 Tagen" in txt and "Freigaben ausgesetzt" in txt
    assert "Eishockey Europa" in "\n".join(outlook.report_lines(rows, tennis=False))


def test_next_matchday_model_only_and_notes():
    fx = [_fx("bundesliga", 9), _fx("bundesliga", 10), _fx("bundesliga", 20), _fx("shl", 1)]
    c = _c("shl", -0.05)
    c.p_ref = None
    rows = {r["name"]: r for r in outlook.build(fx, [c], [], now=NOW)}
    assert rows["Fußball"]["games"] == 0 and rows["Fußball"]["next"][1] == 2
    assert rows["Eishockey Europa"]["model_only"] and rows["Eishockey Europa"]["near"] == [c]
    txt = "\n".join(outlook.telegram_lines(list(rows.values()), tennis=False))
    assert "nächster Spieltag ab Fr 09.10." in txt and "nur Modell – nicht validiert" in txt
    notes = outlook.soccer_note(["NBA: keine Spiele (Saisonstart 20.10.)"],
                                ["eloratings: HTTP 403", "ClubElo nicht erreichbar"])
    assert len(notes) == 3 and "Saisonstart" in notes[0]


def test_tennis_without_connection(monkeypatch):
    monkeypatch.delenv("MONGODB_URI", raising=False)
    tg, md = outlook._tennis()
    assert tg[0].startswith("🎾 Tennis: keine Daten")
