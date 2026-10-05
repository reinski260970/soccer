from oddswatch.sources import football_mongo as fm
import pytest


def test_selection_is_unambiguous_and_excludes_tennis():
    assert fm.choose_database(["admin", "tennis_db", "football_db"]) == "football_db"
    for names in (["tennis_db"], ["football_db", "soccer_db"]):
        with pytest.raises(ValueError):
            fm.choose_database(names)


def test_missing_mongo_does_not_use_tennis(monkeypatch, capsys):
    monkeypatch.delenv("MONGO", raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://tennis-secret")
    assert fm.run() == 2
    assert "tennis-secret" not in capsys.readouterr().out


def test_failure_does_not_leak_uri(monkeypatch, capsys):
    monkeypatch.setenv("MONGO", "not-a-uri://private-password")
    assert fm.run() == 2
    assert "private-password" not in capsys.readouterr().out


def test_schema_discovery_omits_document_values():
    from pymongo.errors import ConfigurationError
    class Cursor:
        def sort(self, *a): return self
        def limit(self, n): assert n == 10; return self
        def max_time_ms(self, n): return self
        def __iter__(self): return iter([{'password': 'NEVER_PRINT_ME', 'prob': .6}])
    class DB:
        name = 'Soccer'
        def list_collection_names(self): return ['predictions']
        def __getitem__(self, n): return self
        def find(self, q): return Cursor()
    class Client:
        def get_default_database(self): raise ConfigurationError('no default')
        def list_database_names(self): return ['Soccer', 'tennis_db']
        def __getitem__(self, n): assert n == 'Soccer'; return DB()
    result = fm.inspect(Client())
    assert result['database'] == 'Soccer'
    assert 'NEVER_PRINT_ME' not in str(result)
    assert result['collections'][0]['fields']['prob'] == ['float']
