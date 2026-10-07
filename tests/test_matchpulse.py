from oddswatch.sources import matchpulse


def test_matchpulse_parse_public_xg_table():
    html = """
    <table><thead><tr><th>#</th><th>Team</th><th>MP</th><th>xGF</th><th>xGF/g</th>
    <th>xGA</th><th>xGA/g</th><th>GF</th><th>GA</th><th>Diff</th></tr></thead>
    <tbody>
      <tr><td>1</td><td>Red Bull Salzburg</td><td>7</td><td>19.9</td><td>2.85</td>
          <td>7.0</td><td>1.01</td><td>18</td><td>4</td><td>-1.9</td></tr>
      <tr><td>2</td><td>Austria Vienna</td><td>7</td><td>6.4</td><td>0.91</td>
          <td>12.8</td><td>1.83</td><td>7</td><td>13</td><td>+0.6</td></tr>
    </tbody></table>
    """
    rows = matchpulse.parse_xg_html(html)
    assert len(rows) == 2
    assert rows[0].team == "Red Bull Salzburg"
    assert rows[0].matches == 7
    assert abs(rows[0].xgf_per_game - 2.85) < 1e-12
    assert abs(rows[0].xga_per_game - 1.01) < 1e-12


def test_matchpulse_rejects_zero_placeholder():
    html = """
    <table><tr><td>1</td><td>Locked FC</td><td>8</td><td>0.0</td><td>0.0</td>
    <td>0.0</td><td>0.0</td><td>0</td><td>0</td><td>0</td></tr></table>
    """
    assert matchpulse.parse_xg_html(html) == []


def test_matchpulse_core_non_understat_mappings():
    for code in ("D2", "E1", "AUT", "N1", "P1", "B1", "T1", "SC0",
                 "SUI", "SWE", "NOR", "DEN", "POL"):
        assert code in matchpulse.LEAGUE_IDS
