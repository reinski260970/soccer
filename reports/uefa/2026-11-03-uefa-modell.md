# UEFA-Club v1.1 – Champions League · Europa League · Conference League
Stand 03.11.2026 08:00 (Wien), Spiele 03.11. bis 05.11.2026

## Datenbasis
- Elo: ClubElo live (590 Teams zugeordnet)
- Ergebnisbasis: 39109 Spiele aus 64 Ligen + Europapokal (API-Football, seit 2024), 1152 Teams
- Ligen ohne ClubElo-Anker über Europapokal-Ergebnisse eingeordnet: Dnipro-1 (-185 Elo, 2 Sp.), Gibraltar (-360 Elo, 48 Sp.), Iceland (-120 Elo, 4 Sp.), San-Marino (-470 Elo, 28 Sp.)
- Kalibrierung (Vor-Spiel-Elo, nur Ligaphase und K.-o.-Runde): 771 Spiele, 762 Quali-/Play-off-Spiele ausgeschlossen → 1.39 Tore je Team bei Gleichstand, Steigung 0.838 (fest an ClubElo-Siegerwartung, 172 Elo ≈ 1 Tor)
- Heimvorteil: Heimteam favorisiert 56 Elo, Heimteam Außenseiter 76 Elo (reiner Fit 55 / 80, Tore 1.40; Richtung Prior geschrumpft)
- xG: Liga-xG für 77 Teams, Europapokal-xG aus 132 Spielen

| Wettbewerb | Spiele | Tore/Spiel ist | Modell (vor Faktor) | Torfaktor | Heimsiege |
|---|---|---|---|---|---|
| Champions League | 243 | 3.59 | 3.00 | ×1.120 | 52 % |
| Conference League | 285 | 2.62 | 2.98 | ×0.922 | 47 % |
| Europa League | 243 | 2.77 | 2.94 | ×0.965 | 48 % |

| Kalibrierungsprobe | Spiele | Heimsiege ist | Modell |
|---|---|---|---|
| Heimteam favorisiert | 373 | 67.8 % | 62.7 % |
| Heimteam Außenseiter | 395 | 31.1 % | 30.6 % |

## Value-Kandidaten (Bet365)
| Anstoß | Spiel | Markt | Modell | Pinnacle | Quote | Edge |
|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 2 | 8 % | 3 % | 34.00 | +171.7 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | X | 16 % | 7 % | 11.00 | +77.6 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1 | 15 % | 12 % | 11.00 | +66.4 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 2 | 11 % | 7 % | 15.00 | +58.7 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1 | 26 % | 17 % | 5.50 | +45.6 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | X | 18 % | 13 % | 8.00 | +43.7 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | U2.5 | 40 % | 27 % | 3.50 | +39.8 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | U2.5 | 40 % | 29 % | 3.50 | +39.0 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1 | 26 % | 18 % | 5.25 | +38.6 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 2 | 29 % | 22 % | 4.75 | +37.2 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1 | 14 % | 9 % | 9.50 | +35.7 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | U2.5 | 30 % | – | 4.50 | +33.5 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | U2.5 | 38 % | 30 % | 3.40 | +30.0 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | U2.5 | 48 % | 35 % | 2.70 | +29.8 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 2 | 31 % | 23 % | 4.20 | +29.5 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | U2.5 | 38 % | 28 % | 3.40 | +29.2 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 2 | 20 % | 15 % | 6.50 | +28.8 % |
| Do 05.11. 21:00 | Twente – Pafos | X | 21 % | 17 % | 6.00 | +27.4 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1 | 20 % | 16 % | 6.25 | +26.9 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | U2.5 | 53 % | 38 % | 2.40 | +26.8 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | U2.5 | 53 % | 38 % | 2.40 | +26.2 % |
| Mi 04.11. 21:00 | Lens – Como | 1 | 42 % | 32 % | 3.00 | +25.4 % |
| Do 05.11. 21:00 | Twente – Pafos | U2.5 | 46 % | 35 % | 2.70 | +24.7 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 2 | 18 % | 14 % | 7.00 | +22.5 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1 | 38 % | 31 % | 3.20 | +22.5 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | X | 17 % | 13 % | 7.00 | +21.4 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | U2.5 | 49 % | 38 % | 2.50 | +21.3 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | X | 20 % | 17 % | 6.00 | +21.1 % |
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1 | 33 % | 27 % | 3.70 | +20.6 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | U2.5 | 50 % | 39 % | 2.38 | +20.0 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | U2.5 | 37 % | 30 % | 3.20 | +19.5 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 2 | 28 % | 24 % | 4.20 | +19.0 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | X | 19 % | 15 % | 6.25 | +18.7 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 2 | 52 % | 39 % | 2.30 | +18.7 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | U2.5 | 50 % | 40 % | 2.38 | +18.4 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | U2.5 | 50 % | 39 % | 2.38 | +18.3 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | U2.5 | 43 % | 34 % | 2.75 | +18.1 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | U2.5 | 37 % | 30 % | 3.20 | +18.0 % |
| Do 05.11. 21:00 | St. Truiden – Brann | U2.5 | 49 % | 39 % | 2.40 | +17.9 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | X | 21 % | 18 % | 5.50 | +16.9 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | X | 17 % | 13 % | 7.00 | +16.6 % |
| Do 05.11. 18:45 | KuPS – Gent | 1 | 23 % | 20 % | 5.00 | +16.4 % |
| Di 03.11. 21:00 | Bodo/Glimt – Lille | 2 | 28 % | 24 % | 4.20 | +16.3 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | U2.5 | 49 % | 40 % | 2.38 | +15.6 % |
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1 | 43 % | 35 % | 2.70 | +15.3 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | U2.5 | 37 % | 30 % | 3.10 | +15.0 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | U2.5 | 36 % | 30 % | 3.20 | +14.6 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1 | 13 % | 9 % | 9.00 | +13.5 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | X | 23 % | 20 % | 5.00 | +13.2 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | X | 24 % | 21 % | 4.75 | +13.1 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | X | 27 % | 24 % | 4.20 | +12.9 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | U2.5 | 49 % | 41 % | 2.30 | +12.2 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | X | 24 % | 20 % | 4.75 | +11.9 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | X | 22 % | 20 % | 5.00 | +11.3 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | X | 23 % | 20 % | 4.75 | +10.4 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | U2.5 | 46 % | 39 % | 2.38 | +10.2 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | U2.5 | 31 % | 27 % | 3.50 | +9.6 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1 | 29 % | 24 % | 3.80 | +9.5 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | 2 | 29 % | 26 % | 3.75 | +9.3 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | U2.5 | 50 % | 44 % | 2.20 | +9.1 % |
| Do 05.11. 21:00 | Twente – Pafos | 2 | 14 % | 12 % | 8.00 | +8.6 % |
| Di 03.11. 21:00 | Feyenoord – Inter | U2.5 | 36 % | 32 % | 3.00 | +7.9 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 2 | 28 % | 26 % | 3.80 | +7.9 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | 1 | 25 % | 22 % | 4.33 | +7.8 % |
| Do 05.11. 21:00 | St. Truiden – Brann | X | 26 % | 24 % | 4.20 | +7.3 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | U2.5 | 43 % | 38 % | 2.50 | +6.9 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | O2.5 | 62 % | 55 % | 1.73 | +6.9 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 2 | 35 % | 32 % | 3.00 | +6.3 % |
| Do 05.11. 18:45 | KuPS – Gent | X | 27 % | 23 % | 4.00 | +6.1 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | X | 24 % | 22 % | 4.33 | +6.0 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | U2.5 | 46 % | 43 % | 2.30 | +6.0 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1 | 48 % | 42 % | 2.20 | +5.9 % |
| Do 05.11. 21:00 | AZ Alkmaar – Juventus | 1 | 28 % | 26 % | 3.80 | +5.7 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | U2.5 | 38 % | 35 % | 2.75 | +5.1 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 2 | 13 % | 11 % | 8.00 | +5.1 % |

Prüfen (Modell weicht stark vom Markt ab – meist fehlt Info zu Kader/Rotation):
- FC Midtjylland – Ajax: U2.5 Modell 52 % vs. Pinnacle 37 %
- Hapoel Beer Sheva – OFI: 1 Modell 61 % vs. Pinnacle 45 %

## Champions League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Di 03.11. 18:45 | Shakhtar Donetsk – Sporting CP | 1717 : 1829 | 1.44 : 1.68 | 33 % | 25 % | 43 % | 60 % | 63 % | 27 % / 25 % / 48 % |
| Di 03.11. 18:45 | Galatasaray – VfB Stuttgart | 1820 : 1810 | 1.84 : 1.39 | 48 % | 24 % | 29 % | 63 % | 64 % | 44 % / 23 % / 33 % |
| Di 03.11. 21:00 | Manchester United – AS Roma | 1841 : 1868 | 1.77 : 1.44 | 45 % | 24 % | 31 % | 62 % | 64 % | 42 % / 24 % / 34 % |
| Di 03.11. 21:00 | Feyenoord – Inter | 1766 : 1945 | 1.30 : 2.00 | 24 % | 23 % | 53 % | 64 % | 63 % | 25 % / 23 % / 52 % |
| Di 03.11. 21:00 | Bodo/Glimt – Lille | 1775 : 1757 | 1.82 : 1.33 | 48 % | 24 % | 28 % | 61 % | 62 % | 53 % / 23 % / 24 % |
| Di 03.11. 21:00 | Barcelona – Aston Villa | 2054 : 1883 | 2.62 : 1.01 | 71 % | 17 % | 12 % | 70 % | 59 % | 76 % / 13 % / 11 % |
| Di 03.11. 21:00 | Atletico Madrid – Bayern München | 1909 : 2079 | 1.30 : 1.93 | 25 % | 23 % | 52 % | 63 % | 63 % | 35 % / 25 % / 39 % |
| Di 03.11. 21:00 | Villarreal – Paris Saint Germain | 1826 : 1999 | 1.28 : 1.92 | 25 % | 23 % | 52 % | 62 % | 62 % | 22 % / 21 % / 57 % |
| Di 03.11. 21:00 | Lask Linz – Slovan Bratislava | 1652 : 1542 | 2.20 : 1.10 | 62 % | 21 % | 18 % | 64 % | 60 % | 69 % / 17 % / 14 % |
| Mi 04.11. 18:45 | AEK Athens FC – Real Madrid | 1711 : 2006 | 1.01 : 2.53 | 13 % | 17 % | 70 % | 69 % | 59 % | 9 % / 13 % / 78 % |
| Mi 04.11. 18:45 | Fenerbahçe – Liverpool | 1769 : 1928 | 1.32 : 1.87 | 26 % | 24 % | 50 % | 62 % | 62 % | 17 % / 20 % / 62 % |
| Mi 04.11. 21:00 | Lens – Como | 1792 : 1838 | 1.66 : 1.47 | 42 % | 25 % | 33 % | 60 % | 63 % | 32 % / 24 % / 45 % |
| Mi 04.11. 21:00 | Borussia Dortmund – Real Betis | 1875 : 1816 | 1.99 : 1.23 | 55 % | 23 % | 23 % | 63 % | 62 % | 55 % / 23 % / 22 % |
| Mi 04.11. 21:00 | RB Leipzig – Manchester City | 1846 : 2007 | 1.34 : 1.91 | 26 % | 23 % | 50 % | 63 % | 63 % | 18 % / 20 % / 62 % |
| Mi 04.11. 21:00 | PSV Eindhoven – Club Brugge KV | 1771 : 1830 | 1.65 : 1.54 | 40 % | 24 % | 35 % | 62 % | 64 % | 47 % / 22 % / 32 % |
| Mi 04.11. 21:00 | FC Porto – Napoli | 1820 : 1813 | 1.80 : 1.39 | 47 % | 24 % | 29 % | 62 % | 63 % | 49 % / 25 % / 26 % |
| Mi 04.11. 21:00 | Slavia Praha – Arsenal | 1759 : 2036 | 1.01 : 2.34 | 14 % | 19 % | 67 % | 65 % | 58 % | 9 % / 15 % / 76 % |
| Mi 04.11. 21:00 | Viking – Sabah FA | 1691 : 1548 | 2.36 : 1.02 | 67 % | 19 % | 14 % | 66 % | 58 % | – |

<details><summary>Herleitung je Team</summary>

- **Shakhtar Donetsk**: Elo 1694 → 1717; Europapokal (3 Sp.): xG-Residuum +1.18/Sp.; xG-Korrektur +23 Elo
- **Sporting CP**: Elo 1856 → 1829; Liga (matchpulse, 10 Sp.): xG 1.70:0.85/Sp., Elo-Erwartung +1.56; Europapokal (3 Sp.): xG-Residuum -0.04/Sp.; xG-Korrektur -27 Elo; Tempo ×1.00
- **Galatasaray**: Elo 1815 → 1820; Liga (matchpulse, 10 Sp.): xG 2.27:0.93/Sp., Elo-Erwartung +1.13; Europapokal (3 Sp.): xG-Residuum -0.22/Sp.; xG-Korrektur +5 Elo; Tempo ×1.03
- **VfB Stuttgart**: Elo 1822 → 1810; Liga (matchpulse, 8 Sp.): xG 1.94:2.13/Sp., Elo-Erwartung +0.35; Europapokal (3 Sp.): xG-Residuum +0.51/Sp.; xG-Korrektur -12 Elo; Tempo ×1.03
- **Manchester United**: Elo 1847 → 1841; Liga (football-data-xg, 9 Sp.): xG 1.53:1.66/Sp., Elo-Erwartung -0.01; Europapokal (3 Sp.): xG-Residuum -0.17/Sp.; xG-Korrektur -6 Elo; Tempo ×1.02
- **AS Roma**: Elo 1865 → 1868; Liga (football-data-xg, 10 Sp.): xG 2.26:1.37/Sp., Elo-Erwartung +0.69; Europapokal (3 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur +2 Elo; Tempo ×1.03
- **Feyenoord**: Elo 1729 → 1766; Liga (matchpulse, 11 Sp.): xG 2.89:1.07/Sp., Elo-Erwartung +0.96; Europapokal (3 Sp.): xG-Residuum +0.26/Sp.; xG-Korrektur +37 Elo; Tempo ×1.03
- **Inter**: Elo 1940 → 1945; Liga (football-data-xg, 10 Sp.): xG 2.70:1.06/Sp., Elo-Erwartung +1.15; Europapokal (3 Sp.): xG-Residuum -1.14/Sp.; xG-Korrektur +6 Elo; Tempo ×1.04
- **Bodo/Glimt**: Elo 1776 → 1775; Liga (matchpulse, 25 Sp.): xG 2.38:0.96/Sp., Elo-Erwartung +1.50; Europapokal (3 Sp.): xG-Residuum +0.59/Sp.; xG-Korrektur -1 Elo; Tempo ×1.02
- **Lille**: Elo 1772 → 1757; Liga (football-data-xg, 9 Sp.): xG 1.41:1.49/Sp., Elo-Erwartung +0.32; Europapokal (3 Sp.): xG-Residuum -0.08/Sp.; xG-Korrektur -15 Elo; Tempo ×0.98
- **Barcelona**: Elo 2027 → 2054; Liga (football-data-xg, 11 Sp.): xG 3.39:1.06/Sp., Elo-Erwartung +1.49; Europapokal (3 Sp.): xG-Residuum -0.57/Sp.; xG-Korrektur +27 Elo; Tempo ×1.10
- **Aston Villa**: Elo 1902 → 1883; Liga (football-data-xg, 9 Sp.): xG 1.20:1.68/Sp., Elo-Erwartung +0.31; Europapokal (3 Sp.): xG-Residuum +0.83/Sp.; xG-Korrektur -18 Elo; Tempo ×1.00
- **Atletico Madrid**: Elo 1921 → 1909; Liga (football-data-xg, 11 Sp.): xG 1.61:1.09/Sp., Elo-Erwartung +0.82; Europapokal (3 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur -12 Elo; Tempo ×0.99
- **Bayern München**: Elo 2039 → 2079; Liga (matchpulse, 8 Sp.): xG 3.59:0.91/Sp., Elo-Erwartung +1.73; Europapokal (3 Sp.): xG-Residuum +0.70/Sp.; xG-Korrektur +40 Elo; Tempo ×1.05
- **Villarreal**: Elo 1795 → 1826; Liga (football-data-xg, 11 Sp.): xG 1.97:1.09/Sp., Elo-Erwartung +0.07; Europapokal (3 Sp.): xG-Residuum -0.10/Sp.; xG-Korrektur +31 Elo; Tempo ×1.01
- **Paris Saint Germain**: Elo 1981 → 1999; Europapokal (3 Sp.): xG-Residuum +0.90/Sp.; xG-Korrektur +18 Elo
- **Lask Linz**: Elo 1637 → 1652; Liga (matchpulse, 11 Sp.): xG 2.16:1.12/Sp., Elo-Erwartung +0.61; Europapokal (3 Sp.): xG-Residuum -0.24/Sp.; xG-Korrektur +15 Elo; Tempo ×1.00
- **Slovan Bratislava**: Elo 1551 → 1542; Europapokal (3 Sp.): xG-Residuum -0.48/Sp.; xG-Korrektur -9 Elo
- **AEK Athens FC**: Elo 1693 → 1711; Liga (football-data-xg, 8 Sp.): xG 2.09:0.73/Sp., Elo-Erwartung +0.93; Europapokal (3 Sp.): xG-Residuum +0.29/Sp.; xG-Korrektur +18 Elo; Tempo ×1.01
- **Real Madrid**: Elo 1996 → 2006; Liga (football-data-xg, 11 Sp.): xG 2.48:1.01/Sp., Elo-Erwartung +1.29; Europapokal (3 Sp.): xG-Residuum +0.33/Sp.; xG-Korrektur +11 Elo; Tempo ×1.04
- **Fenerbahçe**: Elo 1767 → 1769; Liga (matchpulse, 10 Sp.): xG 2.09:1.21/Sp., Elo-Erwartung +0.83; Europapokal (3 Sp.): xG-Residuum -0.01/Sp.; xG-Korrektur +2 Elo; Tempo ×1.03
- **Liverpool**: Elo 1939 → 1928; Liga (football-data-xg, 9 Sp.): xG 1.46:1.17/Sp., Elo-Erwartung +0.54; Europapokal (3 Sp.): xG-Residuum -0.16/Sp.; xG-Korrektur -10 Elo; Tempo ×0.98
- **Lens**: Elo 1801 → 1792; Liga (football-data-xg, 9 Sp.): xG 1.69:1.49/Sp., Elo-Erwartung +0.49; Europapokal (3 Sp.): xG-Residuum +0.03/Sp.; xG-Korrektur -10 Elo; Tempo ×1.00
- **Como**: Elo 1826 → 1838; Liga (football-data-xg, 10 Sp.): xG 1.86:1.25/Sp., Elo-Erwartung +0.46; Europapokal (3 Sp.): xG-Residuum +0.55/Sp.; xG-Korrektur +12 Elo; Tempo ×1.00
- **Borussia Dortmund**: Elo 1895 → 1875; Liga (matchpulse, 8 Sp.): xG 1.55:1.48/Sp., Elo-Erwartung +0.79; Europapokal (3 Sp.): xG-Residuum +0.33/Sp.; xG-Korrektur -20 Elo; Tempo ×0.98
- **Real Betis**: Elo 1827 → 1816; Liga (football-data-xg, 11 Sp.): xG 1.61:1.82/Sp., Elo-Erwartung +0.26; Europapokal (3 Sp.): xG-Residuum +0.67/Sp.; xG-Korrektur -11 Elo; Tempo ×1.04
- **RB Leipzig**: Elo 1831 → 1846; Liga (matchpulse, 8 Sp.): xG 2.48:1.60/Sp., Elo-Erwartung +0.41; Europapokal (3 Sp.): xG-Residuum -0.03/Sp.; xG-Korrektur +15 Elo; Tempo ×1.03
- **Manchester City**: Elo 2010 → 2007; Liga (football-data-xg, 9 Sp.): xG 2.07:1.27/Sp., Elo-Erwartung +0.97; Europapokal (3 Sp.): xG-Residuum +0.20/Sp.; xG-Korrektur -4 Elo; Tempo ×1.03
- **PSV Eindhoven**: Elo 1783 → 1771; Liga (matchpulse, 11 Sp.): xG 2.38:1.31/Sp., Elo-Erwartung +1.30; Europapokal (3 Sp.): xG-Residuum -0.33/Sp.; xG-Korrektur -13 Elo; Tempo ×1.01
- **Club Brugge KV**: Elo 1836 → 1830; Liga (matchpulse, 10 Sp.): xG 2.44:1.15/Sp., Elo-Erwartung +1.38; Europapokal (3 Sp.): xG-Residuum -0.25/Sp.; xG-Korrektur -6 Elo; Tempo ×1.03
- **FC Porto**: Elo 1832 → 1820; Liga (matchpulse, 10 Sp.): xG 2.21:0.83/Sp., Elo-Erwartung +1.40; Europapokal (3 Sp.): xG-Residuum -1.04/Sp.; xG-Korrektur -13 Elo; Tempo ×1.03
- **Napoli**: Elo 1825 → 1813; Liga (football-data-xg, 10 Sp.): xG 1.74:1.28/Sp., Elo-Erwartung +0.45; Europapokal (3 Sp.): xG-Residuum -1.10/Sp.; xG-Korrektur -12 Elo; Tempo ×1.00
- **Slavia Praha**: Elo 1746 → 1759; Europapokal (3 Sp.): xG-Residuum +0.65/Sp.; xG-Korrektur +13 Elo
- **Arsenal (England)**: Elo 2044 → 2036; Liga (football-data-xg, 9 Sp.): xG 1.65:0.80/Sp., Elo-Erwartung +1.18; Europapokal (3 Sp.): xG-Residuum +0.32/Sp.; xG-Korrektur -8 Elo; Tempo ×0.97
- **Viking**: Elo 1707 → 1691; Liga (matchpulse, 25 Sp.): xG 2.00:1.12/Sp., Elo-Erwartung +1.06; Europapokal (3 Sp.): xG-Residuum -0.96/Sp.; xG-Korrektur -17 Elo; Tempo ×1.00
- **Sabah FA**: Elo 1566 → 1548; Europapokal (3 Sp.): xG-Residuum -0.94/Sp.; xG-Korrektur -19 Elo

</details>

## Europa League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Mi 04.11. 16:30 | Rennes – Olympiakos Piraeus | 1735 : 1748 | 1.57 : 1.21 | 45 % | 26 % | 29 % | 52 % | 56 % | 42 % / 27 % / 31 % |
| Do 05.11. 18:45 | Crystal Palace – 1899 Hoffenheim | 1779 : 1753 | 1.60 : 1.13 | 48 % | 26 % | 26 % | 51 % | 55 % | 49 % / 24 % / 27 % |
| Do 05.11. 18:45 | Lillestrom – Plzen | 1544 : 1621 | 1.32 : 1.33 | 36 % | 27 % | 37 % | 50 % | 55 % | 33 % / 25 % / 42 % |
| Do 05.11. 18:45 | NEC Nijmegen – Omonia Nicosia | 1584 : 1616 | 1.47 : 1.22 | 42 % | 27 % | 31 % | 50 % | 55 % | 53 % / 24 % / 23 % |
| Do 05.11. 18:45 | AC Milan – Ferencvarosi TC | 1830 : 1664 | 2.14 : 0.84 | 67 % | 20 % | 13 % | 57 % | 51 % | 71 % / 17 % / 11 % |
| Do 05.11. 18:45 | Real Sociedad – Lyon | 1774 : 1785 | 1.52 : 1.16 | 45 % | 27 % | 28 % | 50 % | 54 % | 52 % / 24 % / 24 % |
| Do 05.11. 18:45 | Anderlecht – Red Bull Salzburg | 1678 : 1689 | 1.55 : 1.18 | 45 % | 26 % | 28 % | 51 % | 55 % | 49 % / 25 % / 26 % |
| Do 05.11. 18:45 | Sparta Praha – Bournemouth | 1629 : 1915 | 0.86 : 2.08 | 14 % | 21 % | 65 % | 56 % | 51 % | 16 % / 21 % / 63 % |
| Do 05.11. 18:45 | Levski Sofia – Jagiellonia | 1592 : 1573 | 1.57 : 1.15 | 47 % | 26 % | 27 % | 51 % | 55 % | 48 % / 27 % / 26 % |
| Do 05.11. 21:00 | Bayer Leverkusen – Marseille | 1865 : 1726 | 2.06 : 0.91 | 64 % | 21 % | 15 % | 57 % | 53 % | 68 % / 18 % / 14 % |
| Do 05.11. 21:00 | AZ Alkmaar – Juventus | 1696 : 1841 | 1.11 : 1.48 | 28 % | 27 % | 45 % | 48 % | 52 % | 26 % / 25 % / 49 % |
| Do 05.11. 21:00 | Benfica – Lech Poznan | 1863 : 1661 | 2.33 : 0.79 | 71 % | 18 % | 11 % | 60 % | 50 % | 79 % / 13 % / 7 % |
| Do 05.11. 21:00 | Celtic – Beşiktaş | 1668 : 1731 | 1.40 : 1.33 | 38 % | 27 % | 35 % | 51 % | 56 % | 31 % / 25 % / 44 % |
| Do 05.11. 21:00 | Celta Vigo – Union St. Gilloise | 1758 : 1810 | 1.41 : 1.28 | 40 % | 27 % | 33 % | 50 % | 55 % | 43 % / 26 % / 31 % |
| Do 05.11. 21:00 | Hapoel Beer Sheva – OFI | 1618 : 1491 | 1.97 : 0.91 | 61 % | 22 % | 16 % | 55 % | 52 % | 45 % / 26 % / 29 % |
| Do 05.11. 21:00 | Sturm Graz – Celje | 1634 : 1525 | 1.88 : 0.94 | 59 % | 23 % | 18 % | 54 % | 52 % | 62 % / 21 % / 17 % |
| Do 05.11. 21:00 | Sunderland – Dinamo Zagreb | 1750 : 1662 | 1.83 : 1.00 | 56 % | 24 % | 20 % | 54 % | 54 % | 64 % / 21 % / 15 % |
| Do 05.11. 21:00 | Torreense – Ararat-Armenia | 1442 : 1438 | 1.52 : 1.18 | 45 % | 27 % | 29 % | 51 % | 55 % | 53 % / 24 % / 22 % |

<details><summary>Herleitung je Team</summary>

- **Rennes**: Elo 1752 → 1735; Liga (football-data-xg, 9 Sp.): xG 2.09:2.33/Sp., Elo-Erwartung +0.20; Europapokal (2 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -17 Elo; Tempo ×1.06
- **Olympiakos Piraeus**: Elo 1746 → 1748; Liga (football-data-xg, 9 Sp.): xG 1.78:0.72/Sp., Elo-Erwartung +1.27; Europapokal (3 Sp.): xG-Residuum +0.80/Sp.; xG-Korrektur +2 Elo; Tempo ×0.99
- **Crystal Palace**: Elo 1810 → 1779; Liga (football-data-xg, 9 Sp.): xG 1.24:2.14/Sp., Elo-Erwartung -0.11; Europapokal (2 Sp.): xG-Residuum -0.27/Sp.; xG-Korrektur -31 Elo; Tempo ×1.03
- **1899 Hoffenheim**: Elo 1734 → 1753; Liga (matchpulse, 8 Sp.): xG 1.81:1.26/Sp., Elo-Erwartung -0.05; Europapokal (2 Sp.): xG-Residuum -0.15/Sp.; xG-Korrektur +19 Elo; Tempo ×0.98
- **Lillestrom**: Elo 1533 → 1544; Liga (matchpulse, 25 Sp.): xG 1.53:1.43/Sp., Elo-Erwartung +0.01; Europapokal (2 Sp.): xG-Residuum +1.14/Sp.; xG-Korrektur +10 Elo; Tempo ×0.98
- **Plzen**: Elo 1620 → 1621; Europapokal (2 Sp.): xG-Residuum +0.12/Sp.; xG-Korrektur +2 Elo
- **NEC Nijmegen**: Elo 1590 → 1584; Liga (matchpulse, 11 Sp.): xG 1.66:1.72/Sp., Elo-Erwartung +0.12; Europapokal (2 Sp.): xG-Residuum +0.24/Sp.; xG-Korrektur -6 Elo; Tempo ×0.99
- **Omonia Nicosia**: Elo 1636 → 1616; Europapokal (3 Sp.): xG-Residuum -1.00/Sp.; xG-Korrektur -20 Elo
- **AC Milan**: Elo 1831 → 1830; Liga (football-data-xg, 10 Sp.): xG 1.77:1.32/Sp., Elo-Erwartung +0.48; Europapokal (3 Sp.): xG-Residuum +0.07/Sp.; xG-Korrektur -0 Elo; Tempo ×1.00
- **Ferencvarosi TC**: Elo 1667 → 1664; Europapokal (2 Sp.): xG-Residuum -0.21/Sp.; xG-Korrektur -3 Elo
- **Real Sociedad**: Elo 1790 → 1774; Liga (football-data-xg, 11 Sp.): xG 1.39:1.68/Sp., Elo-Erwartung +0.04; Europapokal (2 Sp.): xG-Residuum -0.32/Sp.; xG-Korrektur -16 Elo; Tempo ×1.01
- **Lyon**: Elo 1792 → 1785; Liga (football-data-xg, 9 Sp.): xG 1.59:1.15/Sp., Elo-Erwartung +0.43; Europapokal (3 Sp.): xG-Residuum -0.59/Sp.; xG-Korrektur -7 Elo; Tempo ×0.97
- **Anderlecht**: Elo 1662 → 1678; Liga (matchpulse, 10 Sp.): xG 1.74:1.01/Sp., Elo-Erwartung +0.31; Europapokal (3 Sp.): xG-Residuum -0.00/Sp.; xG-Korrektur +16 Elo; Tempo ×0.98
- **Red Bull Salzburg**: Elo 1659 → 1689; Liga (matchpulse, 11 Sp.): xG 2.75:1.03/Sp., Elo-Erwartung +0.74; Europapokal (2 Sp.): xG-Residuum -1.40/Sp.; xG-Korrektur +30 Elo; Tempo ×1.03
- **Sparta Praha**: Elo 1644 → 1629; Europapokal (2 Sp.): xG-Residuum -1.08/Sp.; xG-Korrektur -15 Elo
- **Bournemouth**: Elo 1887 → 1915; Liga (football-data-xg, 9 Sp.): xG 1.75:1.12/Sp., Elo-Erwartung +0.23; Europapokal (2 Sp.): xG-Residuum +1.67/Sp.; xG-Korrektur +28 Elo; Tempo ×1.00
- **Levski Sofia**: Elo 1594 → 1592; Europapokal (2 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur -2 Elo
- **Jagiellonia**: Elo 1591 → 1573; Liga (matchpulse, 11 Sp.): xG 1.57:1.56/Sp., Elo-Erwartung +0.27; Europapokal (3 Sp.): xG-Residuum -0.72/Sp.; xG-Korrektur -18 Elo; Tempo ×1.00
- **Bayer Leverkusen**: Elo 1865 → 1865; Liga (matchpulse, 8 Sp.): xG 1.88:1.75/Sp., Elo-Erwartung +0.62; Europapokal (3 Sp.): xG-Residuum +1.31/Sp.; xG-Korrektur +0 Elo; Tempo ×1.01
- **Marseille**: Elo 1764 → 1726; Liga (football-data-xg, 9 Sp.): xG 1.63:2.25/Sp., Elo-Erwartung +0.27; Europapokal (2 Sp.): xG-Residuum -0.63/Sp.; xG-Korrektur -38 Elo; Tempo ×1.04
- **AZ Alkmaar**: Elo 1681 → 1696; Liga (matchpulse, 11 Sp.): xG 2.19:1.23/Sp., Elo-Erwartung +0.66; Europapokal (3 Sp.): xG-Residuum +0.33/Sp.; xG-Korrektur +15 Elo; Tempo ×1.00
- **Juventus**: Elo 1827 → 1841; Liga (football-data-xg, 10 Sp.): xG 1.37:0.58/Sp., Elo-Erwartung +0.46; Europapokal (2 Sp.): xG-Residuum +0.10/Sp.; xG-Korrektur +13 Elo; Tempo ×0.91
- **Benfica**: Elo 1864 → 1863; Liga (matchpulse, 10 Sp.): xG 2.22:0.80/Sp., Elo-Erwartung +1.62; Europapokal (3 Sp.): xG-Residuum +0.49/Sp.; xG-Korrektur -2 Elo; Tempo ×1.03
- **Lech Poznan**: Elo 1681 → 1661; Liga (matchpulse, 11 Sp.): xG 1.83:1.10/Sp., Elo-Erwartung +0.81; Europapokal (2 Sp.): xG-Residuum -2.35/Sp.; xG-Korrektur -21 Elo; Tempo ×0.99
- **Celtic**: Elo 1650 → 1668; Liga (matchpulse, 12 Sp.): xG 2.72:1.09/Sp., Elo-Erwartung +1.12; Europapokal (2 Sp.): xG-Residuum -0.49/Sp.; xG-Korrektur +18 Elo; Tempo ×1.05
- **Beşiktaş**: Elo 1706 → 1731; Liga (matchpulse, 10 Sp.): xG 1.76:0.90/Sp., Elo-Erwartung +0.46; Europapokal (2 Sp.): xG-Residuum +1.15/Sp.; xG-Korrektur +24 Elo; Tempo ×0.99
- **Celta Vigo**: Elo 1747 → 1758; Europapokal (3 Sp.): xG-Residuum +0.58/Sp.; xG-Korrektur +11 Elo
- **Union St. Gilloise**: Elo 1817 → 1810; Liga (matchpulse, 10 Sp.): xG 2.07:1.03/Sp., Elo-Erwartung +1.26; Europapokal (2 Sp.): xG-Residuum +0.12/Sp.; xG-Korrektur -8 Elo; Tempo ×1.00
- **Hapoel Beer Sheva**: Elo 1630 → 1618; Europapokal (2 Sp.): xG-Residuum -0.86/Sp.; xG-Korrektur -12 Elo
- **OFI**: Elo 1491 → 1491; Liga (football-data-xg, 9 Sp.): xG 1.28:1.35/Sp., Elo-Erwartung -0.15; Europapokal (2 Sp.): xG-Residuum -0.35/Sp.; xG-Korrektur +0 Elo; Tempo ×1.00
- **Sturm Graz**: Elo 1630 → 1634; Liga (matchpulse, 11 Sp.): xG 1.86:1.23/Sp., Elo-Erwartung +0.56; Europapokal (2 Sp.): xG-Residuum +0.18/Sp.; xG-Korrektur +4 Elo; Tempo ×0.99
- **Celje**: Elo 1513 → 1525; Europapokal (3 Sp.): xG-Residuum +0.63/Sp.; xG-Korrektur +13 Elo
- **Sunderland**: Elo 1732 → 1750; Liga (football-data-xg, 9 Sp.): xG 1.47:1.75/Sp., Elo-Erwartung -0.57; Europapokal (3 Sp.): xG-Residuum +0.71/Sp.; xG-Korrektur +18 Elo; Tempo ×1.02
- **Dinamo Zagreb**: Elo 1655 → 1662; Europapokal (2 Sp.): xG-Residuum +0.46/Sp.; xG-Korrektur +7 Elo
- **Torreense**: Elo 1452 → 1442; Europapokal (2 Sp.): xG-Residuum -0.67/Sp.; xG-Korrektur -10 Elo
- **Ararat-Armenia**: Elo 1439 → 1438; Europapokal (2 Sp.): xG-Residuum -0.09/Sp.; xG-Korrektur -1 Elo

</details>

## Conference League
| Anstoß | Spiel | Elo (xG-korr.) | erw. Tore | 1 | X | 2 | Ü2.5 | BTTS | Pinnacle 1/X/2 |
|---|---|---|---|---|---|---|---|---|---|
| Do 05.11. 18:45 | FC Midtjylland – Ajax | 1683 : 1708 | 1.43 : 1.16 | 43 % | 27 % | 30 % | 48 % | 53 % | 35 % / 25 % / 40 % |
| Do 05.11. 18:45 | Aarhus – SC Braga | 1577 : 1712 | 1.11 : 1.41 | 29 % | 28 % | 43 % | 46 % | 51 % | 24 % / 29 % / 47 % |
| Do 05.11. 18:45 | Atalanta – Kairat Almaty | 1762 : 1436 | 2.88 : 0.58 | 84 % | 12 % | 5 % | 67 % | 42 % | 81 % / 12 % / 6 % |
| Do 05.11. 18:45 | FK Crvena Zvezda – Inter Club d'Escaldes | 1667 : 1416 | 2.43 : 0.67 | 76 % | 16 % | 8 % | 60 % | 45 % | 89 % / 7 % / 3 % |
| Do 05.11. 18:45 | Lincoln Red Imps FC – HNK Hajduk Split | 1332 : 1606 | 0.85 : 1.94 | 15 % | 22 % | 63 % | 53 % | 49 % | 12 % / 20 % / 68 % |
| Do 05.11. 18:45 | Trabzonspor – SC Freiburg | 1697 : 1793 | 1.23 : 1.34 | 34 % | 28 % | 39 % | 47 % | 53 % | 37 % / 26 % / 37 % |
| Do 05.11. 18:45 | FC Thun – Heart Of Midlothian | 1527 : 1545 | 1.43 : 1.13 | 44 % | 27 % | 29 % | 47 % | 52 % | 40 % / 27 % / 34 % |
| Do 05.11. 18:45 | KuPS – Gent | 1464 : 1650 | 0.99 : 1.57 | 23 % | 27 % | 50 % | 47 % | 50 % | 20 % / 23 % / 57 % |
| Do 05.11. 18:45 | Mjallby AIF – Borac Banja Luka | 1509 : 1475 | 1.56 : 1.07 | 48 % | 26 % | 25 % | 49 % | 53 % | 42 % / 30 % / 28 % |
| Do 05.11. 21:00 | Monaco – FC Nordsjaelland | 1762 : 1623 | 1.91 : 0.84 | 62 % | 23 % | 15 % | 52 % | 49 % | 64 % / 20 % / 16 % |
| Do 05.11. 21:00 | FC Copenhagen – FC Iberia 1999 | 1683 : 1380 | 2.68 : 0.59 | 81 % | 13 % | 6 % | 63 % | 42 % | – |
| Do 05.11. 21:00 | Twente – Pafos | 1733 : 1571 | 2.02 : 0.81 | 65 % | 21 % | 14 % | 54 % | 49 % | 71 % / 17 % / 12 % |
| Do 05.11. 21:00 | Getafe – Brighton | 1684 : 1900 | 0.93 : 1.68 | 20 % | 25 % | 54 % | 48 % | 50 % | 16 % / 24 % / 60 % |
| Do 05.11. 21:00 | FC Lugano – Kauno Žalgiris | 1666 : 1376 | 2.63 : 0.61 | 80 % | 14 % | 6 % | 63 % | 43 % | 79 % / 13 % / 8 % |
| Do 05.11. 21:00 | Panathinaikos – CSKA Sofia | 1711 : 1542 | 2.08 : 0.81 | 66 % | 21 % | 13 % | 55 % | 49 % | 61 % / 22 % / 17 % |
| Do 05.11. 21:00 | Universitatea Craiova – Egnatia Rrogozhinë | 1597 : 1437 | 2.01 : 0.81 | 65 % | 21 % | 14 % | 54 % | 49 % | 62 % / 22 % / 15 % |
| Do 05.11. 21:00 | St. Truiden – Brann | 1618 : 1564 | 1.66 : 1.05 | 51 % | 26 % | 23 % | 51 % | 53 % | 56 % / 24 % / 21 % |
| Do 05.11. 21:00 | Riga – FK Jablonec | 1506 : 1571 | 1.31 : 1.25 | 37 % | 28 % | 35 % | 47 % | 53 % | 40 % / 28 % / 32 % |

<details><summary>Herleitung je Team</summary>

- **FC Midtjylland**: Elo 1713 → 1683; Liga (matchpulse, 13 Sp.): xG 1.66:1.36/Sp., Elo-Erwartung +0.91; Europapokal (2 Sp.): xG-Residuum -0.36/Sp.; xG-Korrektur -30 Elo; Tempo ×1.00
- **Ajax**: Elo 1702 → 1708; Liga (matchpulse, 10 Sp.): xG 2.33:1.34/Sp., Elo-Erwartung +0.79; Europapokal (2 Sp.): xG-Residuum -0.19/Sp.; xG-Korrektur +6 Elo; Tempo ×1.01
- **Aarhus**: Elo 1594 → 1577; Liga (matchpulse, 13 Sp.): xG 1.46:1.52/Sp., Elo-Erwartung +0.19; Europapokal (2 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -16 Elo; Tempo ×0.99
- **SC Braga**: Elo 1706 → 1712; Liga (matchpulse, 10 Sp.): xG 1.37:0.69/Sp., Elo-Erwartung +0.61; Europapokal (2 Sp.): xG-Residuum +0.37/Sp.; xG-Korrektur +5 Elo; Tempo ×0.96
- **Atalanta**: Elo 1796 → 1762; Liga (football-data-xg, 9 Sp.): xG 1.39:2.05/Sp., Elo-Erwartung +0.28; Europapokal (2 Sp.): xG-Residuum +0.04/Sp.; xG-Korrektur -34 Elo; Tempo ×1.02
- **Kairat Almaty**: Elo 1444 → 1436; Europapokal (2 Sp.): xG-Residuum -0.54/Sp.; xG-Korrektur -8 Elo
- **FK Crvena Zvezda**: Elo 1663 → 1667; Europapokal (2 Sp.): xG-Residuum +0.25/Sp.; xG-Korrektur +4 Elo
- **Inter Club d'Escaldes**: Elo 1426 → 1416; Europapokal (2 Sp.): xG-Residuum -0.70/Sp.; xG-Korrektur -10 Elo
- **Lincoln Red Imps FC**: Elo 1356 → 1332; Europapokal (2 Sp.): xG-Residuum -1.70/Sp.; xG-Korrektur -24 Elo
- **HNK Hajduk Split**: Elo 1602 → 1606; Europapokal (2 Sp.): xG-Residuum +0.29/Sp.; xG-Korrektur +4 Elo
- **Trabzonspor**: Elo 1698 → 1697; Liga (matchpulse, 10 Sp.): xG 1.93:1.49/Sp., Elo-Erwartung +0.42; Europapokal (2 Sp.): xG-Residuum -0.22/Sp.; xG-Korrektur -1 Elo; Tempo ×1.04
- **SC Freiburg**: Elo 1786 → 1793; Liga (matchpulse, 8 Sp.): xG 1.70:1.14/Sp., Elo-Erwartung +0.14; Europapokal (2 Sp.): xG-Residuum -0.89/Sp.; xG-Korrektur +7 Elo; Tempo ×0.97
- **FC Thun**: Elo 1546 → 1527; Liga (matchpulse, 12 Sp.): xG 1.40:1.86/Sp., Elo-Erwartung -0.00; Europapokal (2 Sp.): xG-Residuum +0.00/Sp.; xG-Korrektur -20 Elo; Tempo ×0.99
- **Heart Of Midlothian**: Elo 1545 → 1545; Liga (matchpulse, 11 Sp.): xG 1.67:1.38/Sp., Elo-Erwartung +0.48; Europapokal (2 Sp.): xG-Residuum +1.07/Sp.; xG-Korrektur +0 Elo; Tempo ×1.00
- **KuPS**: Elo 1468 → 1464; Europapokal (2 Sp.): xG-Residuum -0.31/Sp.; xG-Korrektur -5 Elo
- **Gent**: Elo 1641 → 1650; Liga (matchpulse, 10 Sp.): xG 1.36:0.93/Sp., Elo-Erwartung +0.18; Europapokal (2 Sp.): xG-Residuum -0.17/Sp.; xG-Korrektur +8 Elo; Tempo ×0.95
- **Mjallby AIF**: Elo 1515 → 1509; Liga (matchpulse, 27 Sp.): xG 1.48:1.66/Sp., Elo-Erwartung -0.02; Europapokal (2 Sp.): xG-Residuum +0.74/Sp.; xG-Korrektur -6 Elo; Tempo ×1.02
- **Borac Banja Luka**: Elo 1491 → 1475; Europapokal (2 Sp.): xG-Residuum -1.17/Sp.; xG-Korrektur -17 Elo
- **Monaco**: Elo 1790 → 1762; Liga (football-data-xg, 9 Sp.): xG 1.18:1.36/Sp., Elo-Erwartung +0.42; Europapokal (2 Sp.): xG-Residuum -0.73/Sp.; xG-Korrektur -28 Elo; Tempo ×0.96
- **FC Nordsjaelland**: Elo 1622 → 1623; Liga (matchpulse, 13 Sp.): xG 2.03:1.36/Sp., Elo-Erwartung +0.36; Europapokal (2 Sp.): xG-Residuum -1.78/Sp.; xG-Korrektur +2 Elo; Tempo ×1.03
- **FC Copenhagen**: Elo 1689 → 1683; Liga (matchpulse, 13 Sp.): xG 1.64:1.02/Sp., Elo-Erwartung +0.76; Europapokal (2 Sp.): xG-Residuum +0.03/Sp.; xG-Korrektur -6 Elo; Tempo ×0.97
- **FC Iberia 1999**: Elo 1383 → 1380; Europapokal (2 Sp.): xG-Residuum -0.25/Sp.; xG-Korrektur -4 Elo
- **Twente**: Elo 1684 → 1733; Liga (matchpulse, 11 Sp.): xG 2.49:0.95/Sp., Elo-Erwartung +0.68; Europapokal (2 Sp.): xG-Residuum +1.88/Sp.; xG-Korrektur +49 Elo; Tempo ×1.00
- **Pafos**: Elo 1580 → 1571; Europapokal (2 Sp.): xG-Residuum -0.66/Sp.; xG-Korrektur -9 Elo
- **Getafe**: Elo 1684 → 1684; Liga (football-data-xg, 11 Sp.): xG 0.70:1.30/Sp., Elo-Erwartung -0.47; Europapokal (2 Sp.): xG-Residuum +0.73/Sp.; xG-Korrektur +0 Elo; Tempo ×0.93
- **Brighton**: Elo 1903 → 1900; Liga (football-data-xg, 9 Sp.): xG 1.91:1.45/Sp., Elo-Erwartung +0.32; Europapokal (2 Sp.): xG-Residuum -1.01/Sp.; xG-Korrektur -3 Elo; Tempo ×1.03
- **FC Lugano**: Elo 1675 → 1666; Liga (matchpulse, 12 Sp.): xG 1.91:1.32/Sp., Elo-Erwartung +0.76; Europapokal (2 Sp.): xG-Residuum -0.24/Sp.; xG-Korrektur -9 Elo; Tempo ×0.98
- **Kauno Žalgiris**: Elo 1384 → 1376; Europapokal (2 Sp.): xG-Residuum -0.58/Sp.; xG-Korrektur -8 Elo
- **Panathinaikos**: Elo 1671 → 1711; Liga (football-data-xg, 9 Sp.): xG 2.24:0.73/Sp., Elo-Erwartung +0.80; Europapokal (2 Sp.): xG-Residuum +1.68/Sp.; xG-Korrektur +40 Elo; Tempo ×1.02
- **CSKA Sofia**: Elo 1515 → 1542; Europapokal (2 Sp.): xG-Residuum +1.88/Sp.; xG-Korrektur +27 Elo
- **Universitatea Craiova**: Elo 1599 → 1597; Europapokal (2 Sp.): xG-Residuum -0.11/Sp.; xG-Korrektur -2 Elo
- **Egnatia Rrogozhinë**: Elo 1432 → 1437; Europapokal (2 Sp.): xG-Residuum +0.40/Sp.; xG-Korrektur +6 Elo
- **St. Truiden**: Elo 1617 → 1618; Liga (matchpulse, 10 Sp.): xG 1.85:1.80/Sp., Elo-Erwartung +0.04; Europapokal (2 Sp.): xG-Residuum +0.04/Sp.; xG-Korrektur +1 Elo; Tempo ×1.04
- **Brann**: Elo 1582 → 1564; Liga (matchpulse, 25 Sp.): xG 1.65:1.72/Sp., Elo-Erwartung +0.30; Europapokal (2 Sp.): xG-Residuum +0.78/Sp.; xG-Korrektur -18 Elo; Tempo ×1.02
- **Riga**: Elo 1499 → 1506; Europapokal (2 Sp.): xG-Residuum +0.47/Sp.; xG-Korrektur +7 Elo
- **FK Jablonec**: Elo 1547 → 1571; Europapokal (2 Sp.): xG-Residuum +1.70/Sp.; xG-Korrektur +24 Elo

</details>

## Schattentest (gespeicherte Vorhersagen vor Anstoß)
- 34 Spiele ausgewertet, Log-Loss 1X2 Modell 1.021
- Gegen Pinnacle (34 Spiele): Modell 1.021 vs. Pinnacle 1.003 (kleiner = besser)
- Value-Wetten: 42, Ergebnis -4.62 Einheiten, ROI -11.0 %
- Kleine Stichproben schwanken stark – erst ab ~150 Spielen aussagekräftig.

## Methode (Kurzfassung)
Elo-Stärke (ClubElo, solange gesperrt eigene Fortschreibung ab letztem ClubElo-Stand) → Tormatrix (Poisson, Dixon-Coles). Torniveau, Steigung und Heimvorteil (getrennt für Heim-Favorit und Heim-Außenseiter) per Maximum Likelihood an Europapokal-Hauptrunden mit Vor-Spiel-Elo geschätzt, Qualifikation ausgeschlossen. xG-Korrektur: 50% des Residuums (xG-Differenz minus Elo-Erwartung) × n/(n+10), max. ±100 Elo. Tempo aus Liga-xG verschiebt nur Über/Unter. Annahmen (Prior, Anteile) sind im Code als Konstanten markiert und werden über den Schattentest überprüft.
