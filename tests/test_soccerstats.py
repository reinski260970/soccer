from oddswatch.sources import soccerstats


def test_soccerstats_historical_url_uses_season_end_year():
    assert soccerstats.url("D1", 2024).endswith("league=germany_2025")
    assert soccerstats.url("D2", 2024).endswith("league=germany2_2025")


def test_soccerstats_parse_summary():
    html = """
    <html><body>
    306 matches played / 306
    Home wins: 45% Draws: 28% Away wins: 27%
    Goals per match: 2.72
    Over 1.5 goals: 76% Over 2.5 goals: 53% Over 3.5 goals: 29%
    Both teams scored: 55%
    </body></html>
    """
    c = soccerstats.parse_summary(html)
    assert c.matches_played == 306
    assert abs(c.goals_per_match - 2.72) < 1e-12
    assert abs(c.home_win_pct - 0.45) < 1e-12
    assert abs(c.over25_pct - 0.53) < 1e-12
    assert abs(c.btts_pct - 0.55) < 1e-12


def test_soccerstats_core_mapping():
    for code in ("D1","D2","E0","E1","SP1","I1","F1","N1","P1","B1",
                 "T1","SC0","G1","AUT","SUI","SWE","NOR","DEN","POL"):
        assert soccerstats.url(code) is not None


def test_soccerstats_parse_homeaway_team_tables():
    html = """
    <html><body>
    <table>
      <tr><th>#</th><th>Team</th><th>GP</th><th>W</th><th>D</th><th>L</th>
          <th>GF</th><th>GA</th><th>GD</th><th>Pts</th><th>PPG</th></tr>
      <tr><td>1</td><td>Bayern Munich</td><td>17</td><td>14</td><td>2</td><td>1</td>
          <td>52</td><td>14</td><td>+38</td><td>44</td><td>2.59</td></tr>
      <tr><td>2</td><td>Dortmund</td><td>17</td><td>12</td><td>3</td><td>2</td>
          <td>40</td><td>18</td><td>+22</td><td>39</td><td>2.29</td></tr>
      <tr><td>3</td><td>Leverkusen</td><td>17</td><td>11</td><td>4</td><td>2</td>
          <td>38</td><td>17</td><td>+21</td><td>37</td><td>2.18</td></tr>
      <tr><td>4</td><td>Leipzig</td><td>17</td><td>10</td><td>4</td><td>3</td>
          <td>35</td><td>19</td><td>+16</td><td>34</td><td>2.00</td></tr>
      <tr><td>5</td><td>Freiburg</td><td>17</td><td>8</td><td>5</td><td>4</td>
          <td>30</td><td>22</td><td>+8</td><td>29</td><td>1.71</td></tr>
      <tr><td>6</td><td>Mainz</td><td>17</td><td>7</td><td>5</td><td>5</td>
          <td>28</td><td>23</td><td>+5</td><td>26</td><td>1.53</td></tr>
    </table>
    <table>
      <tr><th>#</th><th>Team</th><th>GP</th><th>W</th><th>D</th><th>L</th>
          <th>GF</th><th>GA</th><th>GD</th><th>Pts</th><th>PPG</th></tr>
      <tr><td>1</td><td>Bayern Munich</td><td>17</td><td>12</td><td>3</td><td>2</td>
          <td>45</td><td>20</td><td>+25</td><td>39</td><td>2.29</td></tr>
      <tr><td>2</td><td>Dortmund</td><td>17</td><td>9</td><td>4</td><td>4</td>
          <td>34</td><td>25</td><td>+9</td><td>31</td><td>1.82</td></tr>
      <tr><td>3</td><td>Leverkusen</td><td>17</td><td>10</td><td>4</td><td>3</td>
          <td>36</td><td>21</td><td>+15</td><td>34</td><td>2.00</td></tr>
      <tr><td>4</td><td>Leipzig</td><td>17</td><td>8</td><td>5</td><td>4</td>
          <td>31</td><td>23</td><td>+8</td><td>29</td><td>1.71</td></tr>
      <tr><td>5</td><td>Freiburg</td><td>17</td><td>7</td><td>4</td><td>6</td>
          <td>27</td><td>26</td><td>+1</td><td>25</td><td>1.47</td></tr>
      <tr><td>6</td><td>Mainz</td><td>17</td><td>6</td><td>5</td><td>6</td>
          <td>24</td><td>27</td><td>-3</td><td>23</td><td>1.35</td></tr>
    </table>
    </body></html>
    """
    rows = soccerstats.parse_homeaway_html(html)
    assert len(rows) == 6
    b = next(x for x in rows if x.team == "Bayern Munich")
    assert abs(b.home_ppg - 2.59) < 1e-12
    assert abs(b.away_ppg - 2.29) < 1e-12
    assert abs(b.home_gf_pg - 52 / 17) < 1e-12
