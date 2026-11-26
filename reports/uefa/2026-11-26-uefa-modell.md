# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 26.11.2026 16:42 (Wien), Spiele 26.11. bis 28.11.2026

## Datenbasis
- Elo: ClubElo live (589 Teams zugeordnet)
- Ergebnisbasis: 40008 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1157 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-180 Elo, 2 Sp.), Gibraltar (-345 Elo, 49 Sp.), Hungary (-120 Elo, 4 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-470 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 843 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 56 Elo, Heimteam Außenseiter 72 Elo (reiner Fit 55 / 75, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 45 Teams, Europapokal-xG aus 204 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 279 | 3.54 | 3.00 | ×1.118 | 51 % |
| Conference League | 303 | 2.60 | 2.98 | ×0.915 | 48 % |
| Europa League | 261 | 2.77 | 2.94 | ×0.963 | 47 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 412 | 66.7 % | 62.4 % |
| Heimteam Außenseiter | 428 | 31.1 % | 29.8 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | 1 | 23 % | 8 % | 13.00 | +197.8 % |
| Do 26.11. 18:45 | Beşiktaş – Hapoel Beer Sheva | 2 | 16 % | 9 % | 9.50 | +55.6 % |
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | X | 26 % | 16 % | 5.75 | +51.9 % |
| Do 26.11. 18:45 | Ajax – FC Thun | 2 | 12 % | 8 % | 13.00 | +50.0 % |
| Do 26.11. 21:00 | 1899 Hoffenheim – Sturm Graz | 2 | 16 % | 11 % | 9.00 | +46.6 % |
| Do 26.11. 18:45 | Beşiktaş – Hapoel Beer Sheva | X | 22 % | 13 % | 6.50 | +45.1 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | 2 | 8 % | 5 % | 17.00 | +39.8 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | 2 | 9 % | 6 % | 15.00 | +39.3 % |
| Do 26.11. 18:45 | Beşiktaş – Hapoel Beer Sheva | U2.5 | 45 % | 31 % | 3.00 | +35.8 % |
| Do 26.11. 21:00 | SC Braga – KuPS | 2 | 8 % | 6 % | 17.00 | +33.5 % |
| Do 26.11. 21:00 | Sunderland – Jagiellonia | 2 | 12 % | 8 % | 11.00 | +33.3 % |
| Do 26.11. 18:45 | Marseille – Levski Sofia | 2 | 15 % | 11 % | 9.00 | +31.1 % |
| Do 26.11. 18:45 | Brann – Aarhus | U2.5 | 52 % | 38 % | 2.50 | +30.8 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | X | 17 % | 11 % | 7.50 | +30.8 % |
| Do 26.11. 18:45 | Brighton – Universitatea Craiova | 2 | 6 % | 5 % | 21.00 | +29.5 % |
| Do 26.11. 18:45 | Ajax – FC Thun | X | 20 % | 11 % | 6.50 | +28.9 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | U2.5 | 37 % | 25 % | 3.50 | +28.7 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | 2 | 23 % | 20 % | 5.50 | +27.2 % |
| Do 26.11. 18:45 | Plzen – Benfica | U2.5 | 46 % | 33 % | 2.75 | +25.3 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | X | 16 % | 10 % | 8.00 | +25.2 % |
| Do 26.11. 18:45 | Pafos – FC Midtjylland | U2.5 | 53 % | 39 % | 2.35 | +24.6 % |
| Do 26.11. 21:00 | NEC Nijmegen – Rennes | U2.5 | 47 % | 36 % | 2.62 | +23.9 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | U2.5 | 41 % | 31 % | 3.00 | +23.8 % |
| Do 26.11. 18:45 | Dinamo Zagreb – Bayer Leverkusen | U2.5 | 47 % | 36 % | 2.62 | +23.4 % |
| Do 26.11. 18:45 | Heart Of Midlothian – Monaco | U2.5 | 51 % | 38 % | 2.35 | +20.3 % |
| Do 26.11. 21:00 | CSKA Sofia – Trabzonspor | 1 | 27 % | 21 % | 4.50 | +20.1 % |
| Do 26.11. 21:00 | SC Freiburg – Twente | U2.5 | 53 % | 42 % | 2.25 | +19.6 % |
| Do 26.11. 21:00 | Lyon – Lillestrom | U2.5 | 40 % | 34 % | 3.00 | +19.5 % |
| Do 26.11. 21:00 | CSKA Sofia – Trabzonspor | U2.5 | 51 % | 39 % | 2.35 | +19.1 % |
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | U2.5 | 53 % | 43 % | 2.25 | +18.9 % |
| Do 26.11. 21:00 | Torreense – Celtic | U2.5 | 45 % | 34 % | 2.62 | +18.7 % |
| Do 26.11. 18:45 | Plzen – Benfica | X | 24 % | 19 % | 5.00 | +17.6 % |
| Do 26.11. 21:00 | 1899 Hoffenheim – Sturm Graz | X | 22 % | 16 % | 5.25 | +17.4 % |
| Do 26.11. 18:45 | Brighton – Universitatea Craiova | X | 14 % | 9 % | 8.50 | +17.4 % |
| Do 26.11. 21:00 | Crystal Palace – Real Sociedad | U2.5 | 47 % | 36 % | 2.50 | +17.2 % |
| Do 26.11. 21:00 | Lyon – Lillestrom | X | 17 % | 12 % | 7.00 | +16.9 % |
| Do 26.11. 18:45 | Union St. Gilloise – Lech Poznan | U2.5 | 44 % | 36 % | 2.62 | +16.4 % |
| Do 26.11. 21:00 | Sunderland – Jagiellonia | X | 19 % | 15 % | 6.00 | +16.2 % |
| Do 26.11. 18:45 | Union St. Gilloise – Lech Poznan | X | 21 % | 17 % | 5.50 | +16.1 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | U2.5 | 51 % | 42 % | 2.25 | +15.8 % |
| Do 26.11. 21:00 | Borac Banja Luka – Atalanta | U2.5 | 46 % | 36 % | 2.50 | +15.0 % |
| Do 26.11. 21:00 | SC Braga – KuPS | X | 16 % | 12 % | 7.00 | +14.5 % |
| Do 26.11. 18:45 | Brighton – Universitatea Craiova | U2.5 | 36 % | 32 % | 3.10 | +12.8 % |
| Do 26.11. 18:45 | FK Jablonec – FC Lugano | U2.5 | 54 % | 43 % | 2.08 | +11.6 % |
| Do 26.11. 18:45 | Plzen – Benfica | 1 | 19 % | 16 % | 5.75 | +11.3 % |
| Do 26.11. 21:00 | FC Nordsjaelland – Panathinaikos | U2.5 | 51 % | 43 % | 2.15 | +10.6 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | X | 26 % | 22 % | 4.20 | +9.6 % |
| Do 26.11. 21:00 | Gent – FK Crvena Zvezda | U2.5 | 55 % | 48 % | 2.00 | +9.6 % |
| Do 26.11. 21:00 | Sparta Praha – AZ Alkmaar | U2.5 | 50 % | 45 % | 2.20 | +9.2 % |
| Do 26.11. 18:45 | Marseille – Levski Sofia | X | 21 % | 17 % | 5.25 | +9.1 % |
| Do 26.11. 21:00 | HNK Hajduk Split – St. Truiden | U2.5 | 52 % | 44 % | 2.10 | +8.9 % |
| Do 26.11. 18:45 | Kauno Žalgiris – Riga | 1 | 30 % | 25 % | 3.60 | +8.7 % |
| Do 26.11. 21:00 | Ferencvarosi TC – Celje | U2.5 | 43 % | 38 % | 2.50 | +8.4 % |
| Do 26.11. 18:45 | Heart Of Midlothian – Monaco | 1 | 19 % | 16 % | 5.75 | +8.0 % |
| Do 26.11. 21:00 | Borac Banja Luka – Atalanta | X | 22 % | 18 % | 5.00 | +7.7 % |
| Do 26.11. 21:00 | SC Braga – KuPS | U2.5 | 41 % | 35 % | 2.60 | +7.7 % |
| Do 26.11. 18:45 | Heart Of Midlothian – Monaco | X | 25 % | 21 % | 4.33 | +7.2 % |
| Do 26.11. 21:00 | SC Freiburg – Twente | X | 26 % | 24 % | 4.00 | +6.0 % |
| Do 26.11. 18:45 | FC Iberia 1999 – Getafe | 1 | 15 % | 13 % | 7.00 | +5.9 % |
| Do 26.11. 21:00 | Torreense – Celtic | X | 23 % | 22 % | 4.50 | +5.6 % |
| Do 26.11. 18:45 | FC Iberia 1999 – Getafe | O2.5 | 51 % | 44 % | 2.08 | +5.1 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- Ajax – FC Thun: U2.5 Modell 45 % vs. Pinnacle 23 %
- 1899 Hoffenheim – Sturm Graz: U2.5 Modell 46 % vs. Pinnacle 29 %

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 26.11. 18:45 | Marseille – Levski Sofia | 1728 : 1581 | 2.10 : 0.90 | 65 % | 21 % | 15 % | 58 % | 53 % | 72 % / 17 % / 11 % |
| Do 26.11. 18:45 | Celta Vigo – Bournemouth | 1749 : 1919 | 1.10 : 1.65 | 25 % | 26 % | 50 % | 52 % | 54 % | 25 % / 26 % / 49 % |
| Do 26.11. 18:45 | Beşiktaş – Hapoel Beer Sheva | 1742 : 1615 | 1.96 : 0.91 | 61 % | 22 % | 16 % | 55 % | 52 % | 78 % / 13 % / 9 % |
| Do 26.11. 18:45 | Olympiakos Piraeus – AC Milan | 1750 : 1818 | 1.35 : 1.33 | 37 % | 27 % | 36 % | 50 % | 55 % | 34 % / 28 % / 38 % |
| Do 26.11. 18:45 | Plzen – Benfica | 1641 : 1863 | 1.00 : 1.86 | 19 % | 24 % | 57 % | 54 % | 54 % | 16 % / 19 % / 65 % |
| Do 26.11. 18:45 | Red Bull Salzburg – Ararat-Armenia | 1682 : 1440 | 2.53 : 0.73 | 76 % | 16 % | 8 % | 63 % | 48 % | 85 % / 10 % / 5 % |
| Do 26.11. 18:45 | Dinamo Zagreb – Bayer Leverkusen | 1667 : 1870 | 1.02 : 1.77 | 21 % | 24 % | 54 % | 53 % | 54 % | 20 % / 21 % / 59 % |
| Do 26.11. 18:45 | Union St. Gilloise – Lech Poznan | 1816 : 1662 | 2.05 : 0.85 | 65 % | 21 % | 14 % | 56 % | 51 % | 71 % / 17 % / 12 % |
| Do 26.11. 21:00 | Crystal Palace – Real Sociedad | 1768 : 1774 | 1.59 : 1.21 | 46 % | 26 % | 28 % | 53 % | 56 % | 47 % / 24 % / 29 % |
| Do 26.11. 21:00 | Lyon – Lillestrom | 1775 : 1539 | 2.40 : 0.71 | 75 % | 17 % | 9 % | 60 % | 47 % | 81 % / 12 % / 7 % |
| Do 26.11. 21:00 | 1899 Hoffenheim – Sturm Graz | 1752 : 1625 | 1.95 : 0.91 | 61 % | 22 % | 16 % | 54 % | 52 % | 73 % / 16 % / 11 % |
| Do 26.11. 21:00 | NEC Nijmegen – Rennes | 1590 : 1730 | 1.20 : 1.59 | 28 % | 26 % | 46 % | 53 % | 56 % | 30 % / 24 % / 46 % |
| Do 26.11. 21:00 | Juventus – Omonia Nicosia | 1837 : 1611 | 2.33 : 0.71 | 73 % | 17 % | 9 % | 59 % | 46 % | 83 % / 11 % / 6 % |
| Do 26.11. 21:00 | Sparta Praha – AZ Alkmaar | 1628 : 1709 | 1.32 : 1.37 | 35 % | 27 % | 37 % | 50 % | 55 % | 32 % / 27 % / 41 % |
| Do 26.11. 21:00 | Ferencvarosi TC – Celje | 1690 : 1531 | 2.10 : 0.85 | 66 % | 21 % | 14 % | 57 % | 51 % | 69 % / 18 % / 13 % |
| Do 26.11. 21:00 | Sunderland – Jagiellonia | 1751 : 1571 | 2.21 : 0.82 | 69 % | 19 % | 12 % | 58 % | 50 % | 77 % / 15 % / 8 % |
| Do 26.11. 21:00 | OFI – Anderlecht | 1502 : 1691 | 1.03 : 1.69 | 23 % | 25 % | 52 % | 51 % | 53 % | 21 % / 25 % / 54 % |
| Do 26.11. 21:00 | Torreense – Celtic | 1447 : 1668 | 1.00 : 1.87 | 19 % | 23 % | 57 % | 55 % | 54 % | 21 % / 22 % / 58 % |

<details><summary>Herleitung je Team</summary>

- **Marseille**: Elo 1769 → 1728; Liga (football-data-xg, 11 Sp.): xG 1.66:2.39/Sp., Elo-Erwartung +0.32; Europapokal (3 Sp.): xG-Residuum -0.00/Sp.; xG-Korrektur -41 Elo; Tempo ×1.05
- **Levski Sofia**: Elo 1588 → 1581; Europapokal (3 Sp.): xG-Residuum -0.38/Sp.; xG-Korrektur -8 Elo
- **Celta Vigo**: Elo 1742 → 1749; Europapokal (4 Sp.): xG-Residuum +0.29/Sp.; xG-Korrektur +7 Elo
- **Bournemouth**: Elo 1895 → 1919; Liga (football-data-xg, 11 Sp.): xG 1.90:1.21/Sp., Elo-Erwartung +0.29; Europapokal (3 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur +24 Elo; Tempo ×1.01
- **Beşiktaş**: Elo 1709 → 1742; Liga (matchpulse, 12 Sp.): xG 1.94:0.82/Sp., Elo-Erwartung +0.51; Europapokal (3 Sp.): xG-Residuum +0.71/Sp.; xG-Korrektur +32 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1630 → 1615; Europapokal (3 Sp.): xG-Residuum -0.74/Sp.; xG-Korrektur -15 Elo
- **Olympiakos Piraeus**: Elo 1748 → 1750; Liga (football-data-xg, 11 Sp.): xG 1.85:0.81/Sp., Elo-Erwartung +1.30; Europapokal (4 Sp.): xG-Residuum +0.85/Sp.; xG-Korrektur +2 Elo; Tempo ×1.00
- **AC Milan**: Elo 1825 → 1818; Liga (football-data-xg, 12 Sp.): xG 1.76:1.28/Sp., Elo-Erwartung +0.46; Europapokal (4 Sp.): xG-Residuum -0.65/Sp.; xG-Korrektur -8 Elo; Tempo ×1.00
- **Plzen**: Elo 1632 → 1641; Europapokal (3 Sp.): xG-Residuum +0.45/Sp.; xG-Korrektur +9 Elo
- **Benfica**: Elo 1872 → 1863; Liga (matchpulse, 11 Sp.): xG 2.11:0.85/Sp., Elo-Erwartung +1.66; Europapokal (4 Sp.): xG-Residuum +0.43/Sp.; xG-Korrektur -9 Elo; Tempo ×1.03
- **Red Bull Salzburg**: Elo 1660 → 1682; Liga (matchpulse, 13 Sp.): xG 2.59:1.00/Sp., Elo-Erwartung +0.76; Europapokal (3 Sp.): xG-Residuum -1.43/Sp.; xG-Korrektur +21 Elo; Tempo ×1.03
- **Ararat-Armenia**: Elo 1439 → 1440; Europapokal (3 Sp.): xG-Residuum +0.08/Sp.; xG-Korrektur +2 Elo
- **Dinamo Zagreb**: Elo 1655 → 1667; Europapokal (3 Sp.): xG-Residuum +0.58/Sp.; xG-Korrektur +12 Elo
- **Bayer Leverkusen**: Elo 1866 → 1870; Liga (matchpulse, 10 Sp.): xG 2.06:1.61/Sp., Elo-Erwartung +0.64; Europapokal (4 Sp.): xG-Residuum +0.73/Sp.; xG-Korrektur +4 Elo; Tempo ×1.01
- **Union St. Gilloise**: Elo 1827 → 1816; Liga (matchpulse, 12 Sp.): xG 1.94:0.96/Sp., Elo-Erwartung +1.32; Europapokal (3 Sp.): xG-Residuum +0.25/Sp.; xG-Korrektur -12 Elo; Tempo ×0.99
- **Lech Poznan**: Elo 1678 → 1662; Liga (matchpulse, 13 Sp.): xG 1.90:1.07/Sp., Elo-Erwartung +0.81; Europapokal (3 Sp.): xG-Residuum -1.70/Sp.; xG-Korrektur -16 Elo; Tempo ×0.99
- **Crystal Palace**: Elo 1796 → 1768; Liga (football-data-xg, 11 Sp.): xG 1.41:2.18/Sp., Elo-Erwartung -0.20; Europapokal (3 Sp.): xG-Residuum -0.49/Sp.; xG-Korrektur -28 Elo; Tempo ×1.04
- **Real Sociedad**: Elo 1785 → 1774; Liga (football-data-xg, 13 Sp.): xG 1.59:1.76/Sp., Elo-Erwartung +0.05; Europapokal (3 Sp.): xG-Residuum -0.16/Sp.; xG-Korrektur -11 Elo; Tempo ×1.03
- **Lyon**: Elo 1789 → 1775; Liga (football-data-xg, 11 Sp.): xG 1.44:1.20/Sp., Elo-Erwartung +0.44; Europapokal (4 Sp.): xG-Residuum -0.51/Sp.; xG-Korrektur -15 Elo; Tempo ×0.96
- **Lillestrom**: Elo 1536 → 1539; Liga (matchpulse, 27 Sp.): xG 1.55:1.50/Sp., Elo-Erwartung +0.04; Europapokal (3 Sp.): xG-Residuum +0.45/Sp.; xG-Korrektur +3 Elo; Tempo ×0.99
- **1899 Hoffenheim**: Elo 1733 → 1752; Liga (matchpulse, 10 Sp.): xG 1.86:1.49/Sp., Elo-Erwartung -0.05; Europapokal (3 Sp.): xG-Residuum +0.26/Sp.; xG-Korrektur +19 Elo; Tempo ×0.99
- **Sturm Graz**: Elo 1631 → 1625; Liga (matchpulse, 13 Sp.): xG 1.74:1.38/Sp., Elo-Erwartung +0.58; Europapokal (3 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur -6 Elo; Tempo ×1.00
- **NEC Nijmegen**: Elo 1598 → 1590; Liga (matchpulse, 13 Sp.): xG 1.70:1.84/Sp., Elo-Erwartung +0.18; Europapokal (3 Sp.): xG-Residuum +0.55/Sp.; xG-Korrektur -8 Elo; Tempo ×1.01
- **Rennes**: Elo 1745 → 1730; Liga (football-data-xg, 11 Sp.): xG 1.96:2.07/Sp., Elo-Erwartung +0.17; Europapokal (3 Sp.): xG-Residuum -0.34/Sp.; xG-Korrektur -15 Elo; Tempo ×1.05
- **Juventus**: Elo 1834 → 1837; Liga (football-data-xg, 12 Sp.): xG 1.50:0.74/Sp., Elo-Erwartung +0.51; Europapokal (3 Sp.): xG-Residuum -0.66/Sp.; xG-Korrektur +4 Elo; Tempo ×0.93
- **Omonia Nicosia**: Elo 1636 → 1611; Europapokal (4 Sp.): xG-Residuum -1.01/Sp.; xG-Korrektur -25 Elo
- **Sparta Praha**: Elo 1637 → 1628; Europapokal (3 Sp.): xG-Residuum -0.42/Sp.; xG-Korrektur -8 Elo
- **AZ Alkmaar**: Elo 1686 → 1709; Liga (matchpulse, 13 Sp.): xG 2.28:1.27/Sp., Elo-Erwartung +0.70; Europapokal (4 Sp.): xG-Residuum +0.79/Sp.; xG-Korrektur +23 Elo; Tempo ×1.01
- **Ferencvarosi TC**: Elo 1678 → 1690; Europapokal (3 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur +13 Elo
- **Celje**: Elo 1526 → 1531; Europapokal (4 Sp.): xG-Residuum +0.23/Sp.; xG-Korrektur +6 Elo
- **Sunderland**: Elo 1732 → 1751; Liga (football-data-xg, 11 Sp.): xG 1.44:1.58/Sp., Elo-Erwartung -0.58; Europapokal (4 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur +20 Elo; Tempo ×1.00
- **Jagiellonia**: Elo 1581 → 1571; Liga (matchpulse, 13 Sp.): xG 1.65:1.56/Sp., Elo-Erwartung +0.23; Europapokal (4 Sp.): xG-Residuum -0.33/Sp.; xG-Korrektur -10 Elo; Tempo ×1.01
- **OFI**: Elo 1501 → 1502; Liga (football-data-xg, 11 Sp.): xG 1.26:1.30/Sp., Elo-Erwartung -0.10; Europapokal (3 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur +1 Elo; Tempo ×1.00
- **Anderlecht**: Elo 1675 → 1691; Liga (matchpulse, 12 Sp.): xG 1.71:1.02/Sp., Elo-Erwartung +0.38; Europapokal (4 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur +17 Elo; Tempo ×0.98
- **Torreense**: Elo 1452 → 1447; Europapokal (3 Sp.): xG-Residuum -0.28/Sp.; xG-Korrektur -6 Elo
- **Celtic**: Elo 1660 → 1668; Liga (matchpulse, 14 Sp.): xG 2.66:1.20/Sp., Elo-Erwartung +1.22; Europapokal (3 Sp.): xG-Residuum -0.30/Sp.; xG-Korrektur +8 Elo; Tempo ×1.04

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 26.11. 18:45 | Brighton – Universitatea Craiova | 1900 : 1612 | 2.65 : 0.63 | 80 % | 14 % | 6 % | 64 % | 44 % | 86 % / 9 % / 5 % |
| Do 26.11. 18:45 | Ajax – FC Thun | 1719 : 1527 | 2.13 : 0.75 | 69 % | 20 % | 12 % | 55 % | 47 % | 81 % / 11 % / 8 % |
| Do 26.11. 18:45 | Heart Of Midlothian – Monaco | 1539 : 1768 | 0.90 : 1.73 | 19 % | 25 % | 56 % | 49 % | 49 % | 16 % / 21 % / 63 % |
| Do 26.11. 18:45 | Brann – Aarhus | 1563 : 1590 | 1.41 : 1.17 | 42 % | 28 % | 31 % | 48 % | 53 % | 47 % / 24 % / 29 % |
| Do 26.11. 18:45 | FK Jablonec – FC Lugano | 1558 : 1654 | 1.20 : 1.33 | 33 % | 28 % | 39 % | 46 % | 52 % | 32 % / 27 % / 42 % |
| Do 26.11. 18:45 | Egnatia Rrogozhinë – Lincoln Red Imps FC | 1434 : 1378 | 1.61 : 1.01 | 51 % | 26 % | 23 % | 49 % | 51 % | 59 % / 22 % / 20 % |
| Do 26.11. 18:45 | Pafos – FC Midtjylland | 1561 : 1673 | 1.17 : 1.38 | 31 % | 28 % | 41 % | 47 % | 52 % | 33 % / 26 % / 41 % |
| Do 26.11. 18:45 | FC Iberia 1999 – Getafe | 1388 : 1660 | 0.81 : 1.88 | 15 % | 23 % | 62 % | 51 % | 48 % | 13 % / 22 % / 65 % |
| Do 26.11. 18:45 | Kauno Žalgiris – Riga | 1387 : 1506 | 1.15 : 1.41 | 30 % | 28 % | 42 % | 47 % | 52 % | 25 % / 28 % / 46 % |
| Do 26.11. 21:00 | SC Freiburg – Twente | 1805 : 1747 | 1.57 : 0.98 | 51 % | 26 % | 23 % | 47 % | 50 % | 53 % / 24 % / 23 % |
| Do 26.11. 21:00 | SC Braga – KuPS | 1720 : 1465 | 2.39 : 0.65 | 76 % | 16 % | 8 % | 59 % | 44 % | 82 % / 12 % / 6 % |
| Do 26.11. 21:00 | FC Nordsjaelland – Panathinaikos | 1644 : 1714 | 1.31 : 1.30 | 36 % | 28 % | 36 % | 49 % | 54 % | 39 % / 27 % / 34 % |
| Do 26.11. 21:00 | HNK Hajduk Split – St. Truiden | 1605 : 1628 | 1.43 : 1.16 | 43 % | 27 % | 30 % | 48 % | 53 % | 47 % / 26 % / 28 % |
| Do 26.11. 21:00 | Gent – FK Crvena Zvezda | 1646 : 1676 | 1.35 : 1.13 | 41 % | 28 % | 31 % | 45 % | 51 % | 43 % / 27 % / 30 % |
| Do 26.11. 21:00 | CSKA Sofia – Trabzonspor | 1553 : 1704 | 1.11 : 1.54 | 27 % | 27 % | 47 % | 49 % | 53 % | 21 % / 23 % / 56 % |
| Do 26.11. 21:00 | Inter Club d'Escaldes – FC Copenhagen | 1486 : 1671 | 0.98 : 1.58 | 23 % | 26 % | 51 % | 47 % | 50 % | 8 % / 16 % / 76 % |
| Do 26.11. 21:00 | Borac Banja Luka – Atalanta | 1473 : 1755 | 0.83 : 2.01 | 14 % | 22 % | 64 % | 54 % | 49 % | 14 % / 18 % / 68 % |

<details><summary>Herleitung je Team</summary>

- **Brighton**: Elo 1896 → 1900; Liga (football-data-xg, 11 Sp.): xG 1.96:1.40/Sp., Elo-Erwartung +0.30; Europapokal (3 Sp.): xG-Residuum -0.55/Sp.; xG-Korrektur +4 Elo; Tempo ×1.03
- **Universitatea Craiova**: Elo 1607 → 1612; Europapokal (3 Sp.): xG-Residuum +0.25/Sp.; xG-Korrektur +5 Elo
- **Ajax**: Elo 1719 → 1719; Liga (matchpulse, 12 Sp.): xG 2.12:1.36/Sp., Elo-Erwartung +0.90; Europapokal (3 Sp.): xG-Residuum +0.60/Sp.; xG-Korrektur +1 Elo; Tempo ×1.00
- **FC Thun**: Elo 1550 → 1527; Liga (matchpulse, 14 Sp.): xG 1.32:1.86/Sp., Elo-Erwartung +0.01; Europapokal (3 Sp.): xG-Residuum +0.21/Sp.; xG-Korrektur -22 Elo; Tempo ×0.98
- **Heart Of Midlothian**: Elo 1534 → 1539; Liga (matchpulse, 13 Sp.): xG 1.85:1.40/Sp., Elo-Erwartung +0.44; Europapokal (3 Sp.): xG-Residuum +0.52/Sp.; xG-Korrektur +5 Elo; Tempo ×1.00
- **Monaco**: Elo 1787 → 1768; Liga (football-data-xg, 11 Sp.): xG 1.27:1.27/Sp., Elo-Erwartung +0.42; Europapokal (3 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur -19 Elo; Tempo ×0.96
- **Brann**: Elo 1583 → 1563; Liga (matchpulse, 27 Sp.): xG 1.64:1.73/Sp., Elo-Erwartung +0.32; Europapokal (3 Sp.): xG-Residuum +0.60/Sp.; xG-Korrektur -20 Elo; Tempo ×1.02
- **Aarhus**: Elo 1601 → 1590; Liga (matchpulse, 15 Sp.): xG 1.56:1.45/Sp., Elo-Erwartung +0.21; Europapokal (3 Sp.): xG-Residuum -0.63/Sp.; xG-Korrektur -11 Elo; Tempo ×1.00
- **FK Jablonec**: Elo 1540 → 1558; Europapokal (3 Sp.): xG-Residuum +0.96/Sp.; xG-Korrektur +19 Elo
- **FC Lugano**: Elo 1669 → 1654; Liga (matchpulse, 14 Sp.): xG 1.87:1.31/Sp., Elo-Erwartung +0.72; Europapokal (3 Sp.): xG-Residuum -0.80/Sp.; xG-Korrektur -15 Elo; Tempo ×0.98
- **Egnatia Rrogozhinë**: Elo 1432 → 1434; Europapokal (3 Sp.): xG-Residuum +0.11/Sp.; xG-Korrektur +2 Elo
- **Lincoln Red Imps FC**: Elo 1402 → 1378; Europapokal (3 Sp.): xG-Residuum -1.21/Sp.; xG-Korrektur -24 Elo
- **Pafos**: Elo 1580 → 1561; Europapokal (3 Sp.): xG-Residuum -0.96/Sp.; xG-Korrektur -19 Elo
- **FC Midtjylland**: Elo 1700 → 1673; Liga (matchpulse, 15 Sp.): xG 1.71:1.29/Sp., Elo-Erwartung +0.80; Europapokal (3 Sp.): xG-Residuum -0.97/Sp.; xG-Korrektur -27 Elo; Tempo ×1.00
- **FC Iberia 1999**: Elo 1383 → 1388; Europapokal (3 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur +5 Elo
- **Getafe**: Elo 1671 → 1660; Liga (football-data-xg, 13 Sp.): xG 0.70:1.60/Sp., Elo-Erwartung -0.53; Europapokal (3 Sp.): xG-Residuum +0.47/Sp.; xG-Korrektur -11 Elo; Tempo ×0.95
- **Kauno Žalgiris**: Elo 1384 → 1387; Europapokal (3 Sp.): xG-Residuum +0.15/Sp.; xG-Korrektur +3 Elo
- **Riga**: Elo 1499 → 1506; Europapokal (3 Sp.): xG-Residuum +0.38/Sp.; xG-Korrektur +7 Elo
- **SC Freiburg**: Elo 1800 → 1805; Liga (matchpulse, 10 Sp.): xG 1.66:1.05/Sp., Elo-Erwartung +0.24; Europapokal (3 Sp.): xG-Residuum -0.69/Sp.; xG-Korrektur +6 Elo; Tempo ×0.95
- **Twente**: Elo 1690 → 1747; Liga (matchpulse, 13 Sp.): xG 2.52:0.87/Sp., Elo-Erwartung +0.72; Europapokal (3 Sp.): xG-Residuum +1.82/Sp.; xG-Korrektur +58 Elo; Tempo ×1.00
- **SC Braga**: Elo 1711 → 1720; Liga (matchpulse, 11 Sp.): xG 1.41:0.65/Sp., Elo-Erwartung +0.64; Europapokal (3 Sp.): xG-Residuum +0.41/Sp.; xG-Korrektur +9 Elo; Tempo ×0.96
- **KuPS**: Elo 1468 → 1465; Europapokal (3 Sp.): xG-Residuum -0.17/Sp.; xG-Korrektur -3 Elo
- **FC Nordsjaelland**: Elo 1638 → 1644; Liga (matchpulse, 15 Sp.): xG 2.09:1.24/Sp., Elo-Erwartung +0.43; Europapokal (3 Sp.): xG-Residuum -1.49/Sp.; xG-Korrektur +5 Elo; Tempo ×1.03
- **Panathinaikos**: Elo 1681 → 1714; Liga (football-data-xg, 11 Sp.): xG 2.23:0.77/Sp., Elo-Erwartung +0.87; Europapokal (3 Sp.): xG-Residuum +0.96/Sp.; xG-Korrektur +34 Elo; Tempo ×1.03
- **HNK Hajduk Split**: Elo 1602 → 1605; Europapokal (3 Sp.): xG-Residuum +0.17/Sp.; xG-Korrektur +3 Elo
- **St. Truiden**: Elo 1623 → 1628; Liga (matchpulse, 12 Sp.): xG 1.85:1.65/Sp., Elo-Erwartung +0.08; Europapokal (3 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur +5 Elo; Tempo ×1.03
- **Gent**: Elo 1638 → 1646; Liga (matchpulse, 12 Sp.): xG 1.39:0.97/Sp., Elo-Erwartung +0.16; Europapokal (3 Sp.): xG-Residuum -0.20/Sp.; xG-Korrektur +8 Elo; Tempo ×0.95
- **FK Crvena Zvezda**: Elo 1669 → 1676; Europapokal (3 Sp.): xG-Residuum +0.35/Sp.; xG-Korrektur +7 Elo
- **CSKA Sofia**: Elo 1526 → 1553; Europapokal (3 Sp.): xG-Residuum +1.39/Sp.; xG-Korrektur +28 Elo
- **Trabzonspor**: Elo 1702 → 1704; Liga (matchpulse, 12 Sp.): xG 2.02:1.50/Sp., Elo-Erwartung +0.47; Europapokal (3 Sp.): xG-Residuum +0.04/Sp.; xG-Korrektur +3 Elo; Tempo ×1.05
- **Inter Club d'Escaldes**: Elo 1504 → 1486; Europapokal (3 Sp.): xG-Residuum -0.94/Sp.; xG-Korrektur -19 Elo
- **FC Copenhagen**: Elo 1684 → 1671; Liga (matchpulse, 15 Sp.): xG 1.51:1.01/Sp., Elo-Erwartung +0.71; Europapokal (3 Sp.): xG-Residuum -0.37/Sp.; xG-Korrektur -13 Elo; Tempo ×0.96
- **Borac Banja Luka**: Elo 1491 → 1473; Europapokal (3 Sp.): xG-Residuum -0.90/Sp.; xG-Korrektur -18 Elo
- **Atalanta**: Elo 1779 → 1755; Liga (football-data-xg, 12 Sp.): xG 1.63:1.96/Sp., Elo-Erwartung +0.19; Europapokal (3 Sp.): xG-Residuum -0.36/Sp.; xG-Korrektur -25 Elo; Tempo ×1.03

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 106 Spiele ausgewertet, Log-Loss 1X2 Modell 0.969
- Gegen Pinnacle (106 Spiele): Modell 0.969 vs. Pinnacle 0.935 (kleiner = besser)
- Value-Wetten: 146, Ergebnis -6.61 Einheiten, ROI -4.5 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
