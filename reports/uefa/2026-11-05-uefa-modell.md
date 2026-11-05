# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 05.11.2026 14:27 (Wien), Spiele 05.11. bis 07.11.2026

## Datenbasis
- Elo: ClubElo live (485 Teams zugeordnet)
- Ergebnisbasis: 39135 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1152 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Bosnia (-215 Elo, 70 Sp.), Croatia (-25 Elo, 83 Sp.), Denmark (+15 Elo, 112 Sp.), Dnipro-1 (-175 Elo, 2 Sp.), Gibraltar (-355 Elo, 48 Sp.), Iceland (-110 Elo, 4 Sp.), Moldova (-320 Elo, 58 Sp.), Norway (+15 Elo, 125 Sp.), Poland (+5 Elo, 136 Sp.), San-Marino (-465 Elo, 28 Sp.), Slovenia (-135 Elo, 95 Sp.), Sweden (-70 Elo, 110 Sp.), Wales (-355 Elo, 40 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 790 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 64 Elo, Heimteam Außenseiter 68 Elo (reiner Fit 65 / 70, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 44 Teams, Europapokal-xG aus 151 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 261 | 3.61 | 3.01 | ×1.127 | 51 % |
| Conference League | 285 | 2.62 | 2.99 | ×0.920 | 47 % |
| Europa League | 244 | 2.76 | 2.95 | ×0.960 | 48 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 384 | 68.2 % | 63.2 % |
| Heimteam Außenseiter | 403 | 30.3 % | 29.4 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Do 05.11. 21:00 | Benfica – Lech Poznan | 2 | 14 % | 5 % | 17.00 | +141.0 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 2 | 8 % | 3 % | 29.00 | +122.4 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | X | 16 % | 7 % | 13.00 | +105.4 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | X | 21 % | 10 % | 9.50 | +97.8 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 2 | 22 % | 13 % | 7.00 | +53.0 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 2 | 29 % | 19 % | 5.00 | +46.8 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | U2.5 | 40 % | 26 % | 3.60 | +42.4 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 2 | 32 % | 22 % | 4.20 | +34.1 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | U2.5 | 49 % | 35 % | 2.75 | +33.9 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 2 | 28 % | 20 % | 4.75 | +31.6 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | U2.5 | 50 % | 36 % | 2.62 | +31.5 % |
| Do 05.11. 21:00 | Twente – Pafos | X | 21 % | 16 % | 6.25 | +31.2 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1 | 49 % | 37 % | 2.62 | +29.3 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1 | 20 % | 15 % | 6.50 | +29.1 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | U2.5 | 43 % | 31 % | 3.00 | +28.6 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | X | 24 % | 18 % | 5.25 | +27.2 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | U2.5 | 51 % | 38 % | 2.50 | +26.9 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | X | 21 % | 16 % | 6.00 | +25.8 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 2 | 28 % | 19 % | 4.50 | +24.5 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | X | 25 % | 19 % | 5.00 | +23.4 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | U2.5 | 49 % | 37 % | 2.50 | +22.3 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | U2.5 | 53 % | 40 % | 2.30 | +21.1 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | U2.5 | 50 % | 41 % | 2.38 | +19.4 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 2 | 13 % | 11 % | 9.50 | +18.9 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | 2 | 18 % | 14 % | 6.50 | +18.7 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | 2 | 15 % | 11 % | 8.00 | +17.0 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | X | 27 % | 21 % | 4.33 | +16.3 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1 | 29 % | 22 % | 4.00 | +16.1 % |
| Do 05.11. 21:00 | St. Truiden – Brann | X | 27 % | 22 % | 4.33 | +15.4 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | U2.5 | 37 % | 29 % | 3.10 | +14.3 % |
| Do 05.11. 18:45 | KuPS – Gent | 1 | 23 % | 19 % | 5.00 | +14.0 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 2 | 39 % | 33 % | 2.88 | +13.4 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | U2.5 | 49 % | 40 % | 2.30 | +13.2 % |
| Do 05.11. 21:00 | Twente – Pafos | 2 | 13 % | 11 % | 8.50 | +12.1 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | U2.5 | 43 % | 36 % | 2.62 | +11.6 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1 | 37 % | 33 % | 3.00 | +11.4 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | X | 27 % | 23 % | 4.10 | +11.0 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | U2.5 | 33 % | 26 % | 3.40 | +10.9 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | U2.5 | 46 % | 39 % | 2.38 | +8.8 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | X | 27 % | 25 % | 3.90 | +6.8 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | U2.5 | 53 % | 48 % | 2.00 | +5.8 % |
| Do 05.11. 21:00 | FC Copenhagen – FC Iberia 1999 | O2.5 | 70 % | 64 % | 1.50 | +5.3 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- FC Midtjylland – Ajax: U2.5 Modell 51 % vs. Pinnacle 35 %
- FC Thun – Heart Of Midlothian: U2.5 Modell 53 % vs. Pinnacle 38 %
- Mjallby AIF – Borac Banja Luka: 2 Modell 47 % vs. Pinnacle 29 %
- Benfica – Lech Poznan: U2.5 Modell 43 % vs. Pinnacle 24 %
- Hapoel Beer Sheva – OFI: 1 Modell 62 % vs. Pinnacle 45 %
- Monaco – FC Nordsjaelland: U2.5 Modell 50 % vs. Pinnacle 33 %
- Twente – Pafos: U2.5 Modell 46 % vs. Pinnacle 30 %
- St. Truiden – Brann: U2.5 Modell 50 % vs. Pinnacle 34 %

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | 1780 : 1755 | 1.62 : 1.11 | 49 % | 26 % | 26 % | 51 % | 54 % | 52 % / 23 % / 25 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | 1549 : 1622 | 1.31 : 1.34 | 36 % | 27 % | 37 % | 49 % | 54 % | 33 % / 25 % / 43 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 1583 : 1616 | 1.43 : 1.24 | 41 % | 27 % | 32 % | 50 % | 55 % | 55 % / 23 % / 22 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 1829 : 1662 | 2.17 : 0.82 | 68 % | 20 % | 13 % | 57 % | 50 % | 72 % / 17 % / 11 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 1772 : 1784 | 1.49 : 1.18 | 44 % | 27 % | 29 % | 50 % | 54 % | 59 % / 21 % / 19 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 1678 : 1688 | 1.52 : 1.19 | 44 % | 27 % | 29 % | 51 % | 55 % | 47 % / 25 % / 28 % |
| Do 05.11. 18:45 | Sparta Praha – Bournemouth | 1630 : 1913 | 0.85 : 2.10 | 14 % | 21 % | 66 % | 56 % | 51 % | 14 % / 19 % / 67 % |
| Do 05.11. 18:45 | Levski Sofia – Jagiellonia | 1591 : 1591 | 1.53 : 1.17 | 45 % | 27 % | 28 % | 51 % | 55 % | 47 % / 28 % / 25 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | 1864 : 1725 | 2.08 : 0.89 | 64 % | 21 % | 15 % | 57 % | 52 % | 73 % / 16 % / 11 % |
| Do 05.11. 21:00 | AZ Alkmaar – Juventus | 1694 : 1839 | 1.08 : 1.50 | 27 % | 27 % | 46 % | 48 % | 52 % | 25 % / 26 % / 48 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 1861 : 1717 | 2.09 : 0.87 | 65 % | 21 % | 14 % | 57 % | 51 % | 85 % / 10 % / 5 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1666 : 1729 | 1.37 : 1.35 | 37 % | 27 % | 36 % | 51 % | 56 % | 33 % / 24 % / 43 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | 1758 : 1807 | 1.39 : 1.29 | 39 % | 27 % | 34 % | 50 % | 55 % | 40 % / 29 % / 31 % |
| Do 05.11. 21:00 | Hapoel Beer Sheva – OFI | 1618 : 1493 | 1.98 : 0.90 | 62 % | 22 % | 16 % | 55 % | 52 % | 45 % / 27 % / 28 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | 1633 : 1514 | 1.95 : 0.91 | 61 % | 22 % | 16 % | 54 % | 52 % | 64 % / 20 % / 16 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 1751 : 1691 | 1.75 : 1.04 | 53 % | 25 % | 22 % | 53 % | 54 % | 68 % / 19 % / 13 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 1445 : 1439 | 1.55 : 1.15 | 46 % | 26 % | 28 % | 51 % | 54 % | 55 % / 25 % / 20 % |

<details><summary>Herleitung je Team</summary>

- **Crystal Palace**: Elo 1810 → 1780; Liga (football-data-xg, 9 Sp.): xG 1.24:2.14/Sp., Elo-Erwartung -0.16; Europapokal (2 Sp.): xG-Residuum -0.32/Sp.; xG-Korrektur -30 Elo; Tempo ×1.03
- **1899 Hoffenheim**: Elo 1734 → 1755; Liga (matchpulse, 8 Sp.): xG 1.81:1.26/Sp., Elo-Erwartung -0.09; Europapokal (2 Sp.): xG-Residuum -0.10/Sp.; xG-Korrektur +21 Elo; Tempo ×0.98
- **Lillestrom**: Elo 1527 → 1549; Liga (matchpulse, 25 Sp.): xG 1.53:1.43/Sp., Elo-Erwartung -0.19; Europapokal (2 Sp.): xG-Residuum +1.03/Sp.; xG-Korrektur +22 Elo; Tempo ×0.98
- **Plzen**: Elo 1620 → 1622; Europapokal (2 Sp.): xG-Residuum +0.19/Sp.; xG-Korrektur +3 Elo
- **NEC Nijmegen**: Elo 1590 → 1583; Liga (matchpulse, 11 Sp.): xG 1.66:1.72/Sp., Elo-Erwartung +0.17; Europapokal (2 Sp.): xG-Residuum +0.42/Sp.; xG-Korrektur -6 Elo; Tempo ×0.99
- **Omonia Nicosia**: Elo 1636 → 1616; Europapokal (3 Sp.): xG-Residuum -0.99/Sp.; xG-Korrektur -20 Elo
- **AC Milan**: Elo 1831 → 1829; Liga (football-data-xg, 10 Sp.): xG 1.77:1.32/Sp., Elo-Erwartung +0.53; Europapokal (3 Sp.): xG-Residuum +0.09/Sp.; xG-Korrektur -2 Elo; Tempo ×1.00
- **Ferencvarosi TC**: Elo 1667 → 1662; Europapokal (2 Sp.): xG-Residuum -0.36/Sp.; xG-Korrektur -5 Elo
- **Real Sociedad**: Elo 1789 → 1772; Liga (football-data-xg, 11 Sp.): xG 1.39:1.68/Sp., Elo-Erwartung +0.09; Europapokal (2 Sp.): xG-Residuum -0.24/Sp.; xG-Korrektur -17 Elo; Tempo ×1.01
- **Lyon**: Elo 1792 → 1784; Liga (football-data-xg, 9 Sp.): xG 1.59:1.15/Sp., Elo-Erwartung +0.48; Europapokal (3 Sp.): xG-Residuum -0.60/Sp.; xG-Korrektur -9 Elo; Tempo ×0.97
- **Anderlecht**: Elo 1663 → 1678; Liga (matchpulse, 10 Sp.): xG 1.75:1.01/Sp., Elo-Erwartung +0.36; Europapokal (3 Sp.): xG-Residuum +0.07/Sp.; xG-Korrektur +15 Elo; Tempo ×0.98
- **Red Bull Salzburg**: Elo 1660 → 1688; Liga (matchpulse, 11 Sp.): xG 2.75:1.03/Sp., Elo-Erwartung +0.78; Europapokal (2 Sp.): xG-Residuum -1.40/Sp.; xG-Korrektur +28 Elo; Tempo ×1.03
- **Sparta Praha**: Elo 1644 → 1630; Europapokal (2 Sp.): xG-Residuum -1.00/Sp.; xG-Korrektur -14 Elo
- **Bournemouth**: Elo 1887 → 1913; Liga (football-data-xg, 9 Sp.): xG 1.75:1.12/Sp., Elo-Erwartung +0.27; Europapokal (2 Sp.): xG-Residuum +1.64/Sp.; xG-Korrektur +26 Elo; Tempo ×1.00
- **Levski Sofia**: Elo 1594 → 1591; Europapokal (2 Sp.): xG-Residuum -0.16/Sp.; xG-Korrektur -2 Elo
- **Jagiellonia**: Elo 1613 → 1591; Liga (matchpulse, 11 Sp.): xG 1.57:1.56/Sp., Elo-Erwartung +0.35; Europapokal (3 Sp.): xG-Residuum -0.77/Sp.; xG-Korrektur -22 Elo; Tempo ×1.00
- **Bayer Leverkusen**: Elo 1865 → 1864; Liga (matchpulse, 8 Sp.): xG 1.88:1.75/Sp., Elo-Erwartung +0.66; Europapokal (3 Sp.): xG-Residuum +1.30/Sp.; xG-Korrektur -1 Elo; Tempo ×1.01
- **Marseille**: Elo 1765 → 1725; Liga (football-data-xg, 9 Sp.): xG 1.63:2.25/Sp., Elo-Erwartung +0.32; Europapokal (2 Sp.): xG-Residuum -0.67/Sp.; xG-Korrektur -40 Elo; Tempo ×1.04
- **AZ Alkmaar**: Elo 1681 → 1694; Liga (matchpulse, 11 Sp.): xG 2.19:1.23/Sp., Elo-Erwartung +0.71; Europapokal (3 Sp.): xG-Residuum +0.31/Sp.; xG-Korrektur +13 Elo; Tempo ×1.00
- **Juventus**: Elo 1828 → 1839; Liga (football-data-xg, 10 Sp.): xG 1.37:0.58/Sp., Elo-Erwartung +0.51; Europapokal (2 Sp.): xG-Residuum +0.05/Sp.; xG-Korrektur +11 Elo; Tempo ×0.91
- **Benfica**: Elo 1866 → 1861; Liga (matchpulse, 10 Sp.): xG 2.22:0.80/Sp., Elo-Erwartung +1.68; Europapokal (3 Sp.): xG-Residuum +0.45/Sp.; xG-Korrektur -5 Elo; Tempo ×1.03
- **Lech Poznan**: Elo 1754 → 1717; Liga (matchpulse, 11 Sp.): xG 1.83:1.10/Sp., Elo-Erwartung +1.21; Europapokal (2 Sp.): xG-Residuum -2.36/Sp.; xG-Korrektur -37 Elo; Tempo ×0.99
- **Celtic**: Elo 1650 → 1666; Liga (matchpulse, 12 Sp.): xG 2.72:1.09/Sp., Elo-Erwartung +1.18; Europapokal (2 Sp.): xG-Residuum -0.44/Sp.; xG-Korrektur +16 Elo; Tempo ×1.05
- **Beşiktaş**: Elo 1707 → 1729; Liga (matchpulse, 10 Sp.): xG 1.76:0.90/Sp., Elo-Erwartung +0.51; Europapokal (2 Sp.): xG-Residuum +1.15/Sp.; xG-Korrektur +23 Elo; Tempo ×0.99
- **Celta Vigo**: Elo 1746 → 1758; Europapokal (3 Sp.): xG-Residuum +0.59/Sp.; xG-Korrektur +12 Elo
- **Union St. Gilloise**: Elo 1818 → 1807; Liga (matchpulse, 10 Sp.): xG 2.07:1.03/Sp., Elo-Erwartung +1.31; Europapokal (2 Sp.): xG-Residuum +0.06/Sp.; xG-Korrektur -10 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1630 → 1618; Europapokal (2 Sp.): xG-Residuum -0.81/Sp.; xG-Korrektur -12 Elo
- **OFI**: Elo 1490 → 1493; Liga (football-data-xg, 9 Sp.): xG 1.28:1.35/Sp., Elo-Erwartung -0.20; Europapokal (2 Sp.): xG-Residuum -0.30/Sp.; xG-Korrektur +3 Elo; Tempo ×1.00
- **Sturm Graz**: Elo 1631 → 1633; Liga (matchpulse, 11 Sp.): xG 1.86:1.23/Sp., Elo-Erwartung +0.60; Europapokal (2 Sp.): xG-Residuum +0.20/Sp.; xG-Korrektur +3 Elo; Tempo ×0.99
- **Celje**: Elo 1502 → 1514; Europapokal (3 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur +12 Elo
- **Sunderland**: Elo 1732 → 1751; Liga (football-data-xg, 9 Sp.): xG 1.47:1.75/Sp., Elo-Erwartung -0.62; Europapokal (3 Sp.): xG-Residuum +0.64/Sp.; xG-Korrektur +19 Elo; Tempo ×1.02
- **Dinamo Zagreb**: Elo 1688 → 1691; Europapokal (2 Sp.): xG-Residuum +0.23/Sp.; xG-Korrektur +3 Elo
- **Torreense**: Elo 1452 → 1445; Europapokal (2 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur -7 Elo
- **Ararat-Armenia**: Elo 1439 → 1439; Europapokal (2 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur -0 Elo

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1743 : 1707 | 1.58 : 1.04 | 49 % | 26 % | 24 % | 49 % | 52 % | 37 % / 24 % / 39 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1586 : 1711 | 1.11 : 1.41 | 29 % | 28 % | 43 % | 46 % | 51 % | 22 % / 27 % / 51 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | 1758 : 1437 | 2.90 : 0.58 | 84 % | 11 % | 5 % | 67 % | 42 % | 87 % / 9 % / 4 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 1668 : 1419 | 2.46 : 0.66 | 77 % | 16 % | 8 % | 60 % | 45 % | 90 % / 7 % / 3 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1338 : 1701 | 0.69 : 2.37 | 9 % | 17 % | 74 % | 59 % | 46 % | 11 % / 18 % / 70 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 1697 : 1790 | 1.21 : 1.35 | 33 % | 28 % | 39 % | 47 % | 53 % | 41 % / 26 % / 33 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | 1526 : 1544 | 1.41 : 1.14 | 42 % | 28 % | 30 % | 47 % | 52 % | 41 % / 26 % / 32 % |
| Do 05.11. 18:45 | KuPS – Gent | 1465 : 1648 | 0.98 : 1.58 | 23 % | 26 % | 51 % | 47 % | 50 % | 19 % / 23 % / 59 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1443 : 1594 | 1.08 : 1.54 | 26 % | 27 % | 47 % | 49 % | 53 % | 42 % / 28 % / 29 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | 1760 : 1662 | 1.78 : 0.90 | 58 % | 24 % | 18 % | 50 % | 50 % | 68 % / 18 % / 14 % |
| Do 05.11. 21:00 | FC Copenhagen – FC Iberia 1999 | 1747 : 1378 | 3.12 : 0.51 | 88 % | 9 % | 3 % | 70 % | 38 % | 82 % / 13 % / 5 % |
| Do 05.11. 21:00 | Twente – Pafos | 1730 : 1570 | 2.04 : 0.80 | 66 % | 21 % | 13 % | 54 % | 48 % | 73 % / 16 % / 11 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1685 : 1898 | 0.92 : 1.69 | 20 % | 25 % | 55 % | 48 % | 50 % | 15 % / 24 % / 61 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | 1664 : 1377 | 2.65 : 0.61 | 80 % | 14 % | 6 % | 63 % | 43 % | 83 % / 11 % / 6 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1709 : 1543 | 2.09 : 0.80 | 67 % | 20 % | 13 % | 55 % | 49 % | 69 % / 18 % / 13 % |
| Do 05.11. 21:00 | Universitatea Craiova – Egnatia Rrogozhinë | 1598 : 1439 | 2.04 : 0.80 | 66 % | 21 % | 13 % | 54 % | 48 % | 68 % / 20 % / 12 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 1617 : 1610 | 1.53 : 1.14 | 46 % | 27 % | 28 % | 50 % | 54 % | 59 % / 22 % / 19 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | 1505 : 1572 | 1.28 : 1.27 | 36 % | 28 % | 36 % | 47 % | 53 % | 40 % / 27 % / 33 % |

<details><summary>Herleitung je Team</summary>

- **FC Midtjylland**: Elo 1791 → 1743; Liga (matchpulse, 13 Sp.): xG 1.66:1.36/Sp., Elo-Erwartung +1.31; Europapokal (2 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur -49 Elo; Tempo ×1.00
- **Ajax**: Elo 1701 → 1707; Liga (matchpulse, 10 Sp.): xG 2.33:1.34/Sp., Elo-Erwartung +0.84; Europapokal (2 Sp.): xG-Residuum -0.08/Sp.; xG-Korrektur +5 Elo; Tempo ×1.01
- **Aarhus**: Elo 1600 → 1586; Liga (matchpulse, 13 Sp.): xG 1.46:1.52/Sp., Elo-Erwartung +0.15; Europapokal (2 Sp.): xG-Residuum -0.79/Sp.; xG-Korrektur -15 Elo; Tempo ×0.99
- **SC Braga**: Elo 1707 → 1711; Liga (matchpulse, 10 Sp.): xG 1.37:0.69/Sp., Elo-Erwartung +0.66; Europapokal (2 Sp.): xG-Residuum +0.38/Sp.; xG-Korrektur +4 Elo; Tempo ×0.96
- **Atalanta**: Elo 1781 → 1758; Liga (football-data-xg, 10 Sp.): xG 1.53:1.88/Sp., Elo-Erwartung +0.23; Europapokal (2 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur -23 Elo; Tempo ×1.02
- **Kairat Almaty**: Elo 1444 → 1437; Europapokal (2 Sp.): xG-Residuum -0.51/Sp.; xG-Korrektur -7 Elo
- **FK Crvena Zvezda**: Elo 1663 → 1668; Europapokal (2 Sp.): xG-Residuum +0.33/Sp.; xG-Korrektur +5 Elo
- **Inter Club d'Escaldes**: Elo 1431 → 1419; Europapokal (2 Sp.): xG-Residuum -0.86/Sp.; xG-Korrektur -12 Elo
- **Lincoln Red Imps FC**: Elo 1361 → 1338; Europapokal (2 Sp.): xG-Residuum -1.60/Sp.; xG-Korrektur -23 Elo
- **HNK Hajduk Split**: Elo 1700 → 1701; Europapokal (2 Sp.): xG-Residuum +0.05/Sp.; xG-Korrektur +1 Elo
- **Trabzonspor**: Elo 1700 → 1697; Liga (matchpulse, 10 Sp.): xG 1.93:1.49/Sp., Elo-Erwartung +0.46; Europapokal (2 Sp.): xG-Residuum -0.26/Sp.; xG-Korrektur -3 Elo; Tempo ×1.04
- **SC Freiburg**: Elo 1786 → 1790; Liga (matchpulse, 8 Sp.): xG 1.70:1.14/Sp., Elo-Erwartung +0.19; Europapokal (2 Sp.): xG-Residuum -0.94/Sp.; xG-Korrektur +5 Elo; Tempo ×0.97
- **FC Thun**: Elo 1546 → 1526; Liga (matchpulse, 12 Sp.): xG 1.40:1.86/Sp., Elo-Erwartung +0.04; Europapokal (2 Sp.): xG-Residuum +0.17/Sp.; xG-Korrektur -20 Elo; Tempo ×0.99
- **Heart Of Midlothian**: Elo 1545 → 1544; Liga (matchpulse, 11 Sp.): xG 1.67:1.38/Sp., Elo-Erwartung +0.53; Europapokal (2 Sp.): xG-Residuum +1.15/Sp.; xG-Korrektur -1 Elo; Tempo ×1.00
- **KuPS**: Elo 1468 → 1465; Europapokal (2 Sp.): xG-Residuum -0.22/Sp.; xG-Korrektur -3 Elo
- **Gent**: Elo 1642 → 1648; Liga (matchpulse, 10 Sp.): xG 1.36:0.93/Sp., Elo-Erwartung +0.23; Europapokal (2 Sp.): xG-Residuum -0.18/Sp.; xG-Korrektur +6 Elo; Tempo ×0.95
- **Mjallby AIF**: Elo 1445 → 1443; Liga (matchpulse, 27 Sp.): xG 1.49:1.66/Sp., Elo-Erwartung -0.06; Europapokal (2 Sp.): xG-Residuum +1.03/Sp.; xG-Korrektur -2 Elo; Tempo ×1.02
- **Borac Banja Luka**: Elo 1613 → 1594; Europapokal (2 Sp.): xG-Residuum -1.31/Sp.; xG-Korrektur -19 Elo
- **Monaco**: Elo 1790 → 1760; Liga (football-data-xg, 9 Sp.): xG 1.18:1.36/Sp., Elo-Erwartung +0.47; Europapokal (2 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -30 Elo; Tempo ×0.96
- **FC Nordsjaelland**: Elo 1671 → 1662; Liga (matchpulse, 13 Sp.): xG 2.03:1.36/Sp., Elo-Erwartung +0.56; Europapokal (2 Sp.): xG-Residuum -1.89/Sp.; xG-Korrektur -8 Elo; Tempo ×1.03
- **FC Copenhagen**: Elo 1773 → 1747; Liga (matchpulse, 13 Sp.): xG 1.64:1.02/Sp., Elo-Erwartung +1.19; Europapokal (2 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur -26 Elo; Tempo ×0.97
- **FC Iberia 1999**: Elo 1383 → 1378; Europapokal (2 Sp.): xG-Residuum -0.37/Sp.; xG-Korrektur -5 Elo
- **Twente**: Elo 1683 → 1730; Liga (matchpulse, 11 Sp.): xG 2.49:0.95/Sp., Elo-Erwartung +0.73; Europapokal (2 Sp.): xG-Residuum +1.84/Sp.; xG-Korrektur +47 Elo; Tempo ×1.00
- **Pafos**: Elo 1580 → 1570; Europapokal (2 Sp.): xG-Residuum -0.64/Sp.; xG-Korrektur -9 Elo
- **Getafe**: Elo 1684 → 1685; Liga (football-data-xg, 11 Sp.): xG 0.70:1.30/Sp., Elo-Erwartung -0.51; Europapokal (2 Sp.): xG-Residuum +0.73/Sp.; xG-Korrektur +2 Elo; Tempo ×0.93
- **Brighton**: Elo 1903 → 1898; Liga (football-data-xg, 9 Sp.): xG 1.91:1.45/Sp., Elo-Erwartung +0.37; Europapokal (2 Sp.): xG-Residuum -1.06/Sp.; xG-Korrektur -5 Elo; Tempo ×1.03
- **FC Lugano**: Elo 1675 → 1664; Liga (matchpulse, 12 Sp.): xG 1.91:1.32/Sp., Elo-Erwartung +0.81; Europapokal (2 Sp.): xG-Residuum -0.28/Sp.; xG-Korrektur -12 Elo; Tempo ×0.98
- **Kauno Žalgiris**: Elo 1384 → 1377; Europapokal (2 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur -7 Elo
- **Panathinaikos**: Elo 1671 → 1709; Liga (football-data-xg, 9 Sp.): xG 2.24:0.73/Sp., Elo-Erwartung +0.84; Europapokal (2 Sp.): xG-Residuum +1.72/Sp.; xG-Korrektur +39 Elo; Tempo ×1.02
- **CSKA Sofia**: Elo 1515 → 1543; Europapokal (2 Sp.): xG-Residuum +1.97/Sp.; xG-Korrektur +28 Elo
- **Universitatea Craiova**: Elo 1599 → 1598; Europapokal (2 Sp.): xG-Residuum -0.10/Sp.; xG-Korrektur -1 Elo
- **Egnatia Rrogozhinë**: Elo 1432 → 1439; Europapokal (2 Sp.): xG-Residuum +0.51/Sp.; xG-Korrektur +7 Elo
- **St. Truiden**: Elo 1618 → 1617; Liga (matchpulse, 10 Sp.): xG 1.85:1.80/Sp., Elo-Erwartung +0.09; Europapokal (2 Sp.): xG-Residuum +0.09/Sp.; xG-Korrektur -1 Elo; Tempo ×1.04
- **Brann**: Elo 1636 → 1610; Liga (matchpulse, 25 Sp.): xG 1.65:1.72/Sp., Elo-Erwartung +0.43; Europapokal (2 Sp.): xG-Residuum +0.60/Sp.; xG-Korrektur -26 Elo; Tempo ×1.02
- **Riga**: Elo 1499 → 1505; Europapokal (2 Sp.): xG-Residuum +0.45/Sp.; xG-Korrektur +6 Elo
- **FK Jablonec**: Elo 1547 → 1572; Europapokal (2 Sp.): xG-Residuum +1.76/Sp.; xG-Korrektur +25 Elo

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 53 Spiele ausgewertet, Log-Loss 1X2 Modell 0.930
- Gegen Pinnacle (53 Spiele): Modell 0.930 vs. Pinnacle 0.915 (kleiner = besser)
- Value-Wetten: 73, Ergebnis -17.02 Einheiten, ROI -23.3 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
