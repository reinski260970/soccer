from oddswatch.sources import oddalerts


def test_oddalerts_parse_xg_and_xga_tables():
    html = """
    <html><body>
    <table>
      <tr><th>#</th><th>Team</th><th>P</th><th>G</th><th>xG</th><th>/90</th><th>+/-</th></tr>
      <tr><td>1</td><td>Alpha</td><td>7</td><td>12</td><td>10.5</td><td>1.50</td><td>+1.5</td></tr>
      <tr><td>2</td><td>Beta</td><td>7</td><td>8</td><td>8.4</td><td>1.20</td><td>-0.4</td></tr>
    </table>
    <table>
      <tr><th>#</th><th>Team</th><th>P</th><th>GA</th><th>xGA</th><th>/90</th><th>+/-</th></tr>
      <tr><td>1</td><td>Alpha</td><td>7</td><td>6</td><td>7.0</td><td>1.00</td><td>-1.0</td></tr>
      <tr><td>2</td><td>Beta</td><td>7</td><td>11</td><td>10.5</td><td>1.50</td><td>+0.5</td></tr>
    </table>
    </body></html>
    """
    rows = oddalerts.parse_html(html)
    assert len(rows) == 2
    a = next(x for x in rows if x.team == "Alpha")
    assert a.matches == 7
    assert abs(a.xg_per90 - 1.5) < 1e-12
    assert abs(a.xga_per90 - 1.0) < 1e-12


def test_oddalerts_verified_scope():
    for code in ("D2","E1","AUT","N1","P1","B1","T1","SC0","SUI","SWE","NOR","DEN"):
        assert code in oddalerts.SLUGS
