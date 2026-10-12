from oddswatch.nhl_v5_diagnostics import _edge_band, _market_role


def _r(p=.6, ho=2.0, ao=1.9):
    return {"p_home":p,"home_open":ho,"away_open":ao}


def test_edge_band_uses_model_vs_open_only():
    r=_r(.60,2.0,1.9)
    assert _edge_band(r) in {"10-15%","15%+"}


def test_market_role_is_diagnostic_only_shape():
    r=_r(.60,2.0,1.9)
    assert _market_role(r) in {"FAVORITE","UNDERDOG"}
