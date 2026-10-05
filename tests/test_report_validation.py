from oddswatch import report
from oddswatch.selection import Candidate


def _c(league="nations"):
    return Candidate(
        event="A – B",
        kickoff="2026-10-06T18:45:00+00:00",
        market="home",
        selection="A Sieg (90 Min.)",
        source="bet365",
        odds=9.0,
        p_model=0.16,
        fair_odds=8.91,
        min_odds=8.91,
        edge=0.01,
        ev=0.04,
        stake_eh=0.25,
        estimate=False,
        reason="test",
        observed_at="2026-10-05T05:00:00+00:00",
        liquidity=None,
        p_ref=0.112,
        p_final=0.112,
        league=league,
        flags=["Fußball-Freigaben ausgesetzt: Modell im Backtest nicht besser als der Markt – nur Watchlist"],
    )


def test_unvalidated_soccer_watch_hides_ev_and_playable_to():
    txt = report.telegram_text("05.10.2026 07:00 MESZ", [], [_c()])
    assert "KEINE EV-FREIGABE" in txt
    assert "Modell fair" in txt
    assert "Pinnacle fair" in txt
    assert "spielbar ab" not in txt
    assert "EV 4" not in txt


def test_unvalidated_rule_applies_across_soccer_leagues():
    for league in ("bundesliga", "2bundesliga", "austria", "ucl", "uel", "uecl", "nations"):
        txt = report.telegram_text("05.10.2026 07:00 MESZ", [], [_c(league)])
        assert "KEINE EV-FREIGABE" in txt
