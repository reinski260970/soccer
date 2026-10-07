from datetime import datetime, timezone
from types import SimpleNamespace
from pathlib import Path
import pytest
from oddswatch import bookmaker, guard, daily, news, settle
from oddswatch.journal import Journal
from oddswatch.scan import Fixture, evaluate_fixture
from oddswatch.sources.espn import EspnGame, Team


def test_provider_modules_and_runtime_references_removed():
    root = Path(__file__).parents[1] / 'oddswatch'
    assert not list(root.rglob('*kalshi*py'))
    assert all('kalshi' not in p.read_text().lower() for p in root.rglob('*.py'))


def test_bookmaker_prices_are_separate_from_reference(monkeypatch):
    game = EspnGame('1', 'nations', datetime(2026, 10, 6, tzinfo=timezone.utc), Team('A'), Team('B'), 'STATUS_SCHEDULED')
    fx = Fixture('nations', 'soccer', game, {'home': .5, 'draw': .2, 'away': .3}, '')
    api = bookmaker.apifootball
    monkeypatch.setattr(api, 'api_key', lambda: 'configured')
    match = SimpleNamespace(id=7)
    monkeypatch.setattr(api, 'fixtures_on', lambda d: ([match], None))
    monkeypatch.setattr(api, 'find_fixture', lambda *a: match)
    monkeypatch.setattr(api, 'odds', lambda i: ({'Pinnacle': {'home': 2, 'draw': 4, 'away': 4}, 'Bet365': {'home': 2.2}, 'Betfair': {'home': 2.1}}, None))
    issues = []
    bookmaker.attach_prices([fx], issues)
    assert not issues
    assert fx.ref_probs['home'] == pytest.approx(.5)
    assert {o.source for o in fx.offers['home']} == {'bet365', 'betfair'}
    assert len(evaluate_fixture(fx, {})) == 2


def test_removed_provider_not_republished_and_journal_unchanged(tmp_path):
    j = Journal(tmp_path / 'journal')
    row = {'event': 'Old A – Old B', 'market': 'home', 'selection': 'Old A', 'source': 'kalshi', 'league': 'nations', 'kickoff': '2026-10-06T12:00:00+00:00', 'odds': 2, 'stake_eh': 1, 'fair_odds': 1.8, 'min_odds': 1.9}
    j.append('valuebets', [row])
    before = j.read('valuebets')
    text = daily.daily_text(j, now=datetime(2026, 10, 5, tzinfo=timezone.utc))
    assert 'Old A' not in text
    assert news.load_targets(j, tmp_path / 'missing.json') == []
    assert 'SQL' in ' '.join(settle.settle_all(j))
    assert j.read('valuebets') == before


def test_strict_guard_missing_key_and_api_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, 'STATUS', tmp_path / 'status')
    monkeypatch.setattr(guard, 'STATE', tmp_path / 'state')
    monkeypatch.setattr(guard.apifootball, 'api_key', lambda: '')
    with pytest.raises(RuntimeError, match='APIKEY'):
        guard.run(strict=True)
    monkeypatch.setattr(guard.apifootball, 'api_key', lambda: 'set')
    target = news.Target('WATCH','nations','A – B','2026-10-06T12:00:00+00:00','home','A',2,2,2.06,['A'],['B'])
    monkeypatch.setattr(guard, '_targets', lambda *a: [target])
    monkeypatch.setattr(guard.apifootball, 'fixtures_on', lambda d: ([], 'HTTP 401'))
    with pytest.raises(RuntimeError, match='Abruf'):
        guard.run(strict=True)


def test_strict_guard_send_failure_is_red_and_retryable(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, 'STATUS', tmp_path / 'status')
    monkeypatch.setattr(guard, 'STATE', tmp_path / 'state')
    monkeypatch.setattr(guard.apifootball, 'api_key', lambda: 'set')
    target = news.Target('WATCH','nations','A – B','2026-10-06T12:00:00+00:00','home','A',2,2,2.06,['A'],['B'])
    monkeypatch.setattr(guard, '_targets', lambda *a: [target])
    monkeypatch.setattr(guard.apifootball, 'fixtures_on', lambda d: ([], None))
    monkeypatch.setattr(guard.apifootball, 'find_fixture', lambda *a: SimpleNamespace(id=1))
    monkeypatch.setattr(guard.apifootball, 'odds', lambda i: ({'Pinnacle': {'home': 2, 'draw': 4, 'away': 4}, 'Bet365': {'home': 2.2}}, None))
    monkeypatch.setattr(guard.telegram, 'send', lambda t: {'sent': False, 'message_ids': [], 'error': 'failure'})
    with pytest.raises(RuntimeError, match='Telegram'):
        guard.run(send=True, strict=True)
    assert (tmp_path / 'state').read_text() == '[]'
