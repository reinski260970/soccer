# Fußball-Backtest nach Quotenbereich (30.09.2026)

Walk-forward-Backtest Bundesliga + 2. Bundesliga, 1X2, ab Saison 2024/25 (wöchentlich neu gefittet,
nur vorher bekannte Spiele). Markt = Pinnacle-Eröffnung (power-de-vigged), CLV gegen Pinnacle-Closing.
Tipps nach Freigaberegel (Quote ≥ 1,03 / p, p = 0,25·Modell + 0,75·Markt).

| Quote | Ausgänge | Modell Ø p | Markt Ø p | Ist-Quote | Tipps | ROI | CLV |
|---|---|---|---|---|---|---|---|
| 1,0–2,0 | 408 | 58,6 % | 60,8 % | 59,6 % | 22 | −11,3 % | −1,6 % |
| 2,0–3,0 | 621 | 40,2 % | 39,8 % | 39,5 % | 58 | −31,0 % | −3,9 % |
| 3,0–4,5 | 1105 | 25,8 % | 25,9 % | 26,3 % | 69 | −2,0 % | −7,0 % |
| 4,5–7,0 | 267 | 19,1 % | 17,7 % | 20,2 % | 24 | +5,7 % | −4,5 % |
| ≥ 7,0 | 116 | 11,7 % | 8,7 % | 5,2 % | 18 | −100 % | −17,2 % |

**Befund**
- Große Außenseiter (≥ 7,0): Modell 11,7 % vs. Markt 8,7 % vs. Realität 5,2 % – das Modell überschätzt
  sie massiv; alle 18 Tipps verloren, CLV −17 %.
- Favoriten werden leicht unterschätzt (58,6 % vs. 60,8 % Markt, 59,6 % real).
- In keinem Quotenbereich schlagen die Tipps die Closing-Line (CLV überall negativ).
- Live bestätigt: 4 abgerechnete Fußball-Freigaben (Nations League), 0-4, 3× negativer CLV.

**Konsequenz**
- Fußball-Freigaben ausgesetzt (`scan.soccer_freeze`), bis `data/validation.json` eine Liga/Marktart
  als validiert führt (Modellgewicht > 0, ≥ 200 Tipps, positiver CLV).
- 10 offene Fußball-Freigaben am 30.09. zurückgezogen (`result = withdrawn`).
- Nations League / Europapokal: kein Backtest mit historischen Quoten möglich → gesperrt.
